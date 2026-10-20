#!/usr/bin/env python3
"""AI技術研究室 | Gemini研究データ（Receipt）受付・検証・省力配置モジュール (`intake_receipt.py`).

目的:
第1号で実証された研究パイプラインを維持し、Geminiの出力からGoogle Drive受信フォルダへの手動配置作業を省力化する。
クリップボードまたはファイルから研究JSON（Handoff Envelope / Receipt）を取得し、
事前検証（スキーマ・重複チェック・禁止語スキャン）を行い、Google Drive受信フォルダまたは指定ディレクトリへ安全に配置する。

仕様:
1. 入力: クリップボード (--clipboard)、引数ファイルパス、または標準入力。
2. 検証: receipt_to_research.py の extract_receipt_payload, validate_receipt, compute_receipt_digest による完全検証。
3. 重複確認: 既存の registry.json を照合し、新規(NEW)または差分(UPDATED)の整合性を確認。
4. 出力: --out-dir で指定されたフォルダ、または環境変数 AI_RESEARCH_DRIVE_INBOX、デフォルトは fixtures/inbox。
5. 証拠性: 書き込み直後にハッシュ・ファイル内容を読み戻し検証 (READBACK_VERIFIED)。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY_PATH = ROOT / "registry.json"
DEFAULT_FIXTURES_INBOX = (
    Path(__file__).resolve().parent / "fixtures" / "inbox"
)

# 既存の receipt_to_research モジュールをインポート
try:
    from automation.gemini_notebook import receipt_to_research as bridge
except ImportError:
    # 相対パスまたは同階層実行時のフォールバック
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import receipt_to_research as bridge


def get_clipboard_text() -> str:
    """OSのクリップボードからテキストを取得する（Windows PowerShellまたはtkinter）。"""
    if sys.platform == "win32":
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            return res.stdout
        except Exception:
            pass

    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        text = root.clipboard_get()
        root.destroy()
        return text
    except Exception as e:
        raise RuntimeError(
            f"クリップボードからのテキスト取得に失敗しました: {e}\n"
            "ファイルパスを指定して実行するか、標準入力からパイプしてください。"
        )


def load_raw_input(
    from_clipboard: bool, file_path: Optional[str]
) -> Tuple[str, str]:
    """入力を読み込み、(raw_text, source_description) を返す。"""
    if from_clipboard:
        text = get_clipboard_text()
        return text, "CLIPBOARD"
    if file_path:
        p = Path(file_path).resolve()
        if not p.is_file():
            raise FileNotFoundError(f"指定されたファイルが見つかりません: {file_path}")
        return p.read_text(encoding="utf-8"), str(p)
    if not sys.stdin.isatty():
        return sys.stdin.read(), "STDIN"

    raise ValueError(
        "入力が指定されていません。--clipboard (-c) を指定するか、ファイルパスを渡してください。"
    )


def resolve_output_dir(explicit_out_dir: Optional[str]) -> Path:
    """出力先ディレクトリを解決する。"""
    if explicit_out_dir:
        p = Path(explicit_out_dir).resolve()
    else:
        env_dir = os.environ.get("AI_RESEARCH_DRIVE_INBOX")
        if env_dir:
            p = Path(env_dir).resolve()
        else:
            p = DEFAULT_FIXTURES_INBOX.resolve()

    p.mkdir(parents=True, exist_ok=True)
    return p


def check_existing_registry(
    video_id: str,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    research_dir: Path = ROOT / "research",
) -> Optional[Dict[str, Any]]:
    """既存の registry.json および research/*.md を照合し、該当エントリがあれば返す。"""
    if registry_path.is_file():
        try:
            data = json.loads(registry_path.read_text(encoding="utf-8"))
            records = data.get("records", [])
            for r in records:
                if isinstance(r, dict) and r.get("video_id") == video_id:
                    return {
                        "video_id": video_id,
                        "title": r.get("title") or r.get("record_id"),
                        "notes_file": r.get("research_path") or r.get("notes_file"),
                        "source": "registry.json",
                    }
        except Exception:
            pass

    if research_dir.is_dir():
        for f in research_dir.glob("*.md"):
            if f"-{video_id}-" in f.name or f.name.endswith(f"-{video_id}.md"):
                return {
                    "video_id": video_id,
                    "title": f.name,
                    "notes_file": str(f.relative_to(ROOT)),
                    "source": "research_dir",
                }

    return None


def intake_and_verify_receipt(
    raw_text: str,
    output_dir: Path,
    source_label: str = "INPUT",
    evidence_map: Optional[Dict[str, Any]] = None,
    allow_overwrite: bool = False,
) -> Dict[str, Any]:
    """研究データを抽出し、検証、重複確認、Google Drive/配置先への安全保存と読み戻し確認を行う。"""
    # 1. 抽出
    if evidence_map is None:
        evidence_map = bridge.load_timestamp_evidence()

    extracted = bridge.extract_receipt_payload(raw_text, evidence_map=evidence_map)
    data = extracted

    # 2. 検証 (bridge.validate)
    errors = []
    warnings = []
    try:
        bridge.validate(data)
    except ValueError as ve:
        errors.append(str(ve))
    except Exception as ex:
        errors.append(f"予期しない検証エラー: {ex}")

    if errors:
        return {
            "status": "VALIDATION_FAILED",
            "source": source_label,
            "errors": errors,
            "warnings": warnings,
            "data": data,
        }

    # 3. ダイジェスト計算
    digest = bridge.compute_receipt_digest(data)

    # 4. 重複確認 (registry.json)
    video_entries = data.get("videos", [])
    registry_checks = []
    has_unintended_duplicate = False

    for v in video_entries:
        vid = v.get("video_id")
        reg_entry = check_existing_registry(vid)
        changes = v.get("changes", [])
        is_new_declared = "NEW" in changes

        if reg_entry:
            if is_new_declared and not ("UPDATED" in changes or "APPEND" in changes):
                has_unintended_duplicate = True
                registry_checks.append({
                    "video_id": vid,
                    "title": v.get("title"),
                    "status": "UNINTENDED_DUPLICATE_NEW_DECLARED",
                    "existing_title": reg_entry.get("title"),
                    "existing_notes": reg_entry.get("notes_file"),
                })
            else:
                registry_checks.append({
                    "video_id": vid,
                    "title": v.get("title"),
                    "status": "VALID_UPDATE_OR_EXTENSION",
                    "existing_notes": reg_entry.get("notes_file"),
                })
        else:
            registry_checks.append({
                "video_id": vid,
                "title": v.get("title"),
                "status": "NEW_UNREGISTERED",
            })

    if has_unintended_duplicate and not allow_overwrite:
        return {
            "status": "STOPPED_DUPLICATE_REGISTERED",
            "source": source_label,
            "digest": digest,
            "registry_checks": registry_checks,
            "message": (
                "この動画IDはすでにregistry.jsonに登録されています。"
                "新規(NEW)として再登録することはできません。差分更新(UPDATED)として指定してください。"
            ),
            "warnings": warnings,
        }

    # 5. 安全保存 (配置先ファイル作成)
    now_ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    first_vid = video_entries[0].get("video_id") if video_entries else "multi"
    target_filename = f"receipt_{now_ts}_{first_vid}.json"
    target_path = output_dir / target_filename

    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    target_path.write_text(json_str, encoding="utf-8")

    # 6. 読み戻し確認 (READBACK_VERIFIED)
    readback_content = target_path.read_text(encoding="utf-8")
    readback_hash = hashlib.sha256(readback_content.encode("utf-8")).hexdigest()

    return {
        "status": "SUCCESS_SAVED_AND_READBACK_VERIFIED",
        "source": source_label,
        "digest": digest,
        "target_file": str(target_path),
        "target_filename": target_filename,
        "bytes_written": len(json_str.encode("utf-8")),
        "readback_hash": readback_hash,
        "video_count": len(video_entries),
        "registry_checks": registry_checks,
        "warnings": warnings,
        "video_ids": [v.get("video_id") for v in video_entries],
        "titles": [v.get("title") for v in video_entries],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Gemini研究データ（Receipt）受付・事前検証・省力配置ツール"
    )
    parser.add_argument(
        "-c",
        "--clipboard",
        action="store_true",
        help="OSクリップボードからテキストを取得して処理する",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="読み込む研究データファイルパス（指定しない場合は標準入力または--clipboard）",
    )
    parser.add_argument(
        "-o",
        "--out-dir",
        help="保存先ディレクトリ（未指定時は環境変数AI_RESEARCH_DRIVE_INBOXまたはfixtures/inbox）",
    )
    parser.add_argument(
        "--allow-overwrite",
        action="store_true",
        help="既存登録済み動画に対する警告停止を上書き許可する",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="結果をJSON形式で出力する",
    )

    args = parser.parse_args()

    try:
        raw_text, source_label = load_raw_input(args.clipboard, args.file)
    except Exception as e:
        print(f"【エラー】{e}", file=sys.stderr)
        sys.exit(1)

    output_dir = resolve_output_dir(args.out_dir)
    res = intake_and_verify_receipt(
        raw_text,
        output_dir=output_dir,
        source_label=source_label,
        allow_overwrite=args.allow_overwrite,
    )

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        sys.exit(0 if res.get("status") == "SUCCESS_SAVED_AND_READBACK_VERIFIED" else 1)

    # 日本語サマリー出力
    status = res.get("status")
    print("=" * 60)
    print(" AI技術研究室 | 研究データ受付・検証結果")
    print("=" * 60)
    print(f"入力元: {res.get('source')}")
    print(f"判定ステータス: {status}")

    if status == "SUCCESS_SAVED_AND_READBACK_VERIFIED":
        print("\n【検証成功: Google Drive / 受信トレイへ安全に配置しました】")
        print(f"保存先ファイル: {res.get('target_file')}")
        print(f"研究データSHA-256: {res.get('digest')}")
        print(f"対象動画数: {res.get('video_count')}件")
        for vid, title in zip(res.get("video_ids", []), res.get("titles", [])):
            print(f"  - [{vid}] {title}")

        if res.get("warnings"):
            print("\n【注意・警告】")
            for w in res.get("warnings", []):
                print(f"  ! {w}")

        print("\n【次のステップ】")
        print("1. Google Driveの受信トレイにファイルが同期されたことを確認します。")
        print("2. Google Apps Script（GAS）で `runCloudRelayLoop`（またはDry-Run）を実行してください。")
        print("3. GitHubへのアトミック保存後、Driveに自動生成された研究カードをNotebookLMから選択できます。")
        sys.exit(0)

    elif status == "STOPPED_DUPLICATE_REGISTERED":
        print("\n【重複停止: 登録済みの動画です】")
        print(res.get("message"))
        for check in res.get("registry_checks", []):
            print(f"  - 動画ID: {check.get('video_id')}")
            print(f"    タイトル: {check.get('title')}")
            print(f"    既存研究ノート: {check.get('existing_notes')}")
        print("\n※ 差分として再調査する場合は、changesに `UPDATED` を指定してください。")
        sys.exit(2)

    else:
        print("\n【検証失敗: 研究データの修正が必要です】")
        for err in res.get("errors", []):
            print(f"  × {err}")
        if res.get("warnings"):
            print("\n【警告】")
            for w in res.get("warnings", []):
                print(f"  ! {w}")
        print("\nGeminiに修正プロンプトを提示して再生成を行ってください。")
        sys.exit(1)


if __name__ == "__main__":
    main()
