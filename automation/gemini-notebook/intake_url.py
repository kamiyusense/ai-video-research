#!/usr/bin/env python3
"""AI技術研究室 | YouTube URL受付・事前重複チェックモジュール (`intake_url.py`).

目的:
ユーザーがYouTube URLを提示した段階で即座に重複を確認し、不要な動画解析・AI使用量を削減する。

仕様:
1. YouTube URL（通常URL、短縮URL、再生時刻指定付き、shorts、live）から11文字の動画IDを抽出する。
2. 動画解析を開始する前に、既存の `registry.json`（および `research/*.md`, `loop_state.json`）を参照する。
3. URLの形式や再生開始時刻が違っても、動画IDが同じなら重複と判定する。
4. 登録済みの場合は研究を開始せず、以下を返す:
   - 登録済みであること (ALREADY_REGISTERED)
   - 動画タイトル
   - 一行要約
   - 研究記録のリンク
   - 再調査するかどうか（再調査の要否プロンプト）
5. 未登録の場合のみ研究を開始可能とする (NOT_REGISTERED)。
6. Gemini Notebookの登録状態は、直接アクセスできない場合は UNKNOWN とし捏造しない。
7. GitHub台帳自体が取得できない場合は、新規と断定せず安全停止 (BLOCKED_GITHUB_UNREACHABLE) する。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY_PATH = ROOT / "registry.json"
DEFAULT_RESEARCH_DIR = ROOT / "research"
DEFAULT_LOOP_STATE_PATH = (
    Path(__file__).resolve().parent / "state" / "loop_state.json"
)

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
YOUTUBE_HOSTS = {
    "www.youtube.com",
    "youtube.com",
    "m.youtube.com",
    "youtu.be",
}
FILENAME_VID_RE = re.compile(
    r"(?:^|[/\\])\d{4}-\d{2}-\d{2}-([A-Za-z0-9_-]{11})-[^/\\]+\.md$"
)


def extract_youtube_id(url_or_id: str) -> Optional[str]:
    """Extract an 11-character YouTube video_id from URL or raw ID."""
    if not isinstance(url_or_id, str):
        return None
    val = url_or_id.strip()
    if not val:
        return None
    if VIDEO_ID_RE.fullmatch(val):
        return val

    # URL parsing
    try:
        u = urlparse(val)
    except Exception:
        return None

    host = (u.hostname or "").lower()
    if host not in YOUTUBE_HOSTS:
        return None

    cand = None
    if host == "youtu.be":
        parts = [p for p in u.path.split("/") if p]
        cand = parts[0] if parts else None
    else:
        if u.path == "/watch":
            qs = parse_qs(u.query)
            cand = qs.get("v", [None])[0]
        else:
            parts = [p for p in u.path.split("/") if p]
            if len(parts) >= 2 and parts[0] in {"shorts", "live", "embed", "v"}:
                cand = parts[1]
            elif len(parts) == 1 and VIDEO_ID_RE.fullmatch(parts[0]):
                cand = parts[0]

    if cand and VIDEO_ID_RE.fullmatch(cand):
        return cand
    return None


def canonical_youtube_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def extract_title_and_summary_from_md(md_path: Path) -> Tuple[Optional[str], Optional[str]]:
    """Extract title and summary from research markdown file."""
    if not md_path.is_file():
        return None, None
    try:
        text = md_path.read_text(encoding="utf-8")
    except Exception:
        return None, None

    title = None
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
        m_t = re.match(r"^-\s*タイトル[（(][^）)]*[）)]\s*:\s*(.+)$", line)
        if m_t:
            title = m_t.group(1).strip()
            break

    summary = None
    m_s = re.search(r"##\s*(?:結論（独自要約）|独自要約|差分要約)\s*\n+([^\n#]+)", text)
    if m_s:
        summary = m_s.group(1).strip()

    return title, summary


def check_url_intake(
    url_or_id: str,
    root: Optional[Path] = None,
    registry_path: Optional[Path] = None,
    research_dir: Optional[Path] = None,
    loop_state_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Perform pre-analysis deduplication intake check for a given YouTube URL or video_id."""
    target_root = Path(root) if root else ROOT
    target_registry = Path(registry_path) if registry_path else (target_root / "registry.json")
    target_research_dir = Path(research_dir) if research_dir else (target_root / "research")
    target_loop_state = (
        Path(loop_state_path)
        if loop_state_path
        else (target_root / "automation" / "gemini-notebook" / "state" / "loop_state.json")
    )

    # 1. Extract video_id
    vid = extract_youtube_id(url_or_id)
    if not vid:
        return {
            "input": url_or_id,
            "video_id": None,
            "canonical_url": None,
            "status": "INVALID_URL",
            "is_registered": False,
            "message_ja": (
                f"指定された入力（`{url_or_id}`）から有効な11文字のYouTube動画IDを抽出できませんでした。"
                "有効なYouTube URL（`https://www.youtube.com/watch?v=...`、`https://youtu.be/...` など）"
                "または11文字の動画IDを指定してください。"
            ),
            "notebook_status": "UNKNOWN (Invalid URL)",
        }

    canonical_url = canonical_youtube_url(vid)

    # 2. Check GitHub registry readability
    if not target_registry.exists() or not target_registry.is_file():
        return {
            "input": url_or_id,
            "video_id": vid,
            "canonical_url": canonical_url,
            "status": "BLOCKED_GITHUB_UNREACHABLE",
            "is_registered": None,
            "message_ja": (
                f"GitHub台帳ファイル（`{target_registry}`）が取得・読み取りできません。"
                "台帳が確認できない場合は新規と断定せず安全停止します。"
            ),
            "notebook_status": "UNKNOWN (GitHub registry unavailable)",
        }

    try:
        reg_data = json.loads(target_registry.read_text(encoding="utf-8"))
    except Exception as e:
        return {
            "input": url_or_id,
            "video_id": vid,
            "canonical_url": canonical_url,
            "status": "BLOCKED_GITHUB_UNREACHABLE",
            "is_registered": None,
            "message_ja": (
                f"GitHub台帳ファイル（`{target_registry}`）のパースに失敗しました: {e}。"
                "台帳の破損が疑われるため、新規と断定せず安全停止します。"
            ),
            "notebook_status": "UNKNOWN (GitHub registry corrupted)",
        }

    # 3. Check registry.json records
    records = reg_data.get("records") or []
    found_record = None
    for r in records:
        if isinstance(r, dict) and r.get("video_id") == vid:
            found_record = r
            break

    # 4. Check research/*.md files on disk
    found_research_file: Optional[Path] = None
    if target_research_dir.is_dir():
        for f in target_research_dir.glob("*.md"):
            m = FILENAME_VID_RE.search(f.name)
            if m and m.group(1) == vid:
                found_research_file = f
                break

    # 5. Check loop_state.json processed_receipts and remote_branch_cache
    remote_branch_matches = []
    if target_loop_state.is_file():
        try:
            ls_data = json.loads(target_loop_state.read_text(encoding="utf-8"))
            rb_cache = ls_data.get("remote_branch_cache") or {}
            for branch, binfo in rb_cache.items():
                if isinstance(binfo, dict):
                    vids = [
                        v.get("video_id") if isinstance(v, dict) else v
                        for v in binfo.get("videos", [])
                    ] + binfo.get("video_ids", [])
                    if vid in vids:
                        remote_branch_matches.append(branch)
        except Exception:
            pass

    is_registered = bool(found_record or found_research_file or remote_branch_matches)

    if is_registered:
        # Determine research path
        res_path_str = ""
        if found_record and found_record.get("research_path"):
            res_path_str = found_record["research_path"]
        elif found_research_file:
            try:
                res_path_str = str(found_research_file.relative_to(target_root)).replace("\\", "/")
            except Exception:
                res_path_str = str(found_research_file).replace("\\", "/")

        # Resolve markdown file on disk to extract title & summary
        md_file = None
        if found_research_file and found_research_file.is_file():
            md_file = found_research_file
        elif res_path_str:
            cand_p = target_root / res_path_str
            if cand_p.is_file():
                md_file = cand_p

        title = None
        summary_ja = None
        if md_file:
            title, summary_ja = extract_title_and_summary_from_md(md_file)

        if not title:
            title = (
                (found_record.get("title") if found_record else None)
                or f"動画研究 ({vid})"
            )
        if not summary_ja:
            summary_ja = (
                (found_record.get("summary_ja") if found_record else None)
                or (found_record.get("source_scope") if found_record else None)
                or "既存の研究台帳に登録されています。"
            )

        repo_name = reg_data.get("repository", "kamiyusense/ai-video-research")
        branch_name = "feature/gemini-notebook-research-loop-20261016"
        github_link = f"https://github.com/{repo_name}/blob/{branch_name}/{res_path_str}" if res_path_str else None

        detection_details = []
        if found_record:
            detection_details.append("registry.json")
        if found_research_file:
            detection_details.append(f"research/{found_research_file.name}")
        if remote_branch_matches:
            detection_details.append(f"remote_branches: {', '.join(remote_branch_matches)}")

        msg_lines = [
            f"### 🛑 【登録済み・重複検知】 動画解析をスキップしました",
            f"",
            f"- **判定**: 登録済み (`ALREADY_REGISTERED`)",
            f"- **動画ID**: `{vid}`",
            f"- **動画URL**: {canonical_url}",
            f"- **検出元**: {', '.join(detection_details)}",
            f"- **動画タイトル**: {title}",
            f"- **一行要約**: {summary_ja}",
            f"- **研究記録リンク**: [`{res_path_str}`]({github_link})" if github_link else f"- **研究記録**: `{res_path_str}`",
            f"",
            f"#### ❓ 再調査しますか？",
            f"この動画はすでに研究台帳・正本に保存されているため、新規調査は不要です。",
            f"重要な公式仕様変更、新機能発表による影響、または未確認タイムスタンプの補足がある場合のみ、",
            f"「**差分更新（UPDATED）として再調査**」と明示して指示してください。",
        ]

        return {
            "input": url_or_id,
            "video_id": vid,
            "canonical_url": canonical_url,
            "status": "ALREADY_REGISTERED",
            "is_registered": True,
            "title": title,
            "summary_ja": summary_ja,
            "research_path": res_path_str,
            "github_link": github_link,
            "detection_sources": detection_details,
            "revisit_prompt": (
                "この動画はすでに研究記録が存在します。重要な仕様更新や未確認タイムスタンプの補足がある場合のみ、"
                "差分更新（UPDATED）として再調査してください。"
            ),
            "notebook_status": "UNKNOWN (Notebook requires manual verification or authorized Gemini session)",
            "message_ja": "\n".join(msg_lines),
        }

    # Not registered (NEW)
    msg_lines = [
        f"### 🟢 【未登録・新規動画】 研究を開始できます",
        f"",
        f"- **判定**: 未登録 (`NOT_REGISTERED`)",
        f"- **動画ID**: `{vid}`",
        f"- **動画URL**: {canonical_url}",
        f"- **台帳確認**: `registry.json` および `research/*.md` に存在しませんでした。",
        f"- **Gemini Notebook確認**: `UNKNOWN` (外部Notebookの直接照合は未実施。公式経路で確認してください)",
        f"",
        f"#### 次のステップ",
        f"1. **Gemini Notebookへの投入**: 上記URLをGemini Notebookのソースに登録し、`GEMINI_TASK.md` の指示に従って章立て・時刻根拠・詳細技術ノートを作成します。",
        f"2. **レシート保存**: 出力された `research_receipt_v1` JSONをGoogle Driveの受信フォルダへ配置し、GASリレーでGitHubへ自動保存します。",
        f"3. **保存直前ガード**: 保存直前にも全ブランチ横断の重複チェックが自動実行され、二重保存を防止します。",
    ]

    return {
        "input": url_or_id,
        "video_id": vid,
        "canonical_url": canonical_url,
        "status": "NOT_REGISTERED",
        "is_registered": False,
        "title": None,
        "summary_ja": None,
        "research_path": None,
        "github_link": None,
        "detection_sources": [],
        "revisit_prompt": None,
        "notebook_status": "UNKNOWN (Notebook requires manual verification or authorized Gemini session)",
        "message_ja": "\n".join(msg_lines),
    }


def main():
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    parser = argparse.ArgumentParser(
        description="YouTube URL受付・事前重複チェックCLI (AI技術研究室)"
    )
    parser.add_argument("url", help="YouTube URL or 11-char video ID")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--root", type=Path, default=None, help="Repository root path")
    parser.add_argument("--registry", type=Path, default=None, help="registry.json path")
    args = parser.parse_args()

    result = check_url_intake(args.url, root=args.root, registry_path=args.registry)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["message_ja"])

    if result["status"] == "BLOCKED_GITHUB_UNREACHABLE":
        sys.exit(2)
    elif result["status"] == "INVALID_URL":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
