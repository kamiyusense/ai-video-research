#!/usr/bin/env python3
"""AI技術研究室 | Gemini Notebook 自動登録モジュール (notebook_auto_ingest.py).

目的:
対象Notebook（e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7）に対し、
元YouTube動画と独自研究ノートの2資料を自動登録するための実装・検証を行う。

アプローチ:
1. [Google Drive専用同期フォルダ連携 (正式・実用経路)]
   ローカルマウントされた Google Drive (G:/マイドライブ) 上の専用フォルダ
   「AI技術研究室_Notebookソース」へ、研究ノートMarkdownとYouTube動画参照ファイルを自動同期配置。
   NotebookLMの公式機能「Google Driveからソースを追加」と直結させる。
2. [Chrome DevTools Protocol (CDP) 自動化プローブ]
   ローカル稼働中のChromeに対し、リモートデバッグポート（127.0.0.1:9222）経由での
   NotebookLMタブ接続・DOM自動操作の可能性を実測プローブ。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
AUTO_DIR = Path(__file__).resolve().parent

NOTEBOOK_ID = "e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7"
NOTEBOOK_URL = f"https://gemini.google.com/notebook/{NOTEBOOK_ID}"
DEFAULT_DRIVE_ROOT = Path("G:/マイドライブ")
DEFAULT_NOTEBOOK_SOURCES_DIR = DEFAULT_DRIVE_ROOT / "AI技術研究室_Notebookソース"
CDP_ENDPOINT = "http://127.0.0.1:9222/json"


def probe_cdp_connection(timeout: float = 2.0) -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
    """Probe if Chrome is running with remote debugging port 9222 enabled."""
    try:
        req = urllib.request.Request(CDP_ENDPOINT)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            tabs = json.loads(resp.read().decode("utf-8"))
            return True, "CDP_CONNECTED", tabs
    except urllib.error.URLError as ex:
        return False, f"CDP_CONNECTION_REFUSED: Chrome is not launched with --remote-debugging-port=9222 ({ex.reason})", None
    except Exception as ex:
        return False, f"CDP_ERROR: {ex}", None


def sync_to_drive_notebook_sources(
    video_id: str,
    video_url: str,
    video_title: str,
    research_md_path: Path,
    target_dir: Path = DEFAULT_NOTEBOOK_SOURCES_DIR,
) -> Dict[str, Any]:
    """Place the 2 sources (YouTube reference & Research Markdown) into Drive Notebook Sources folder."""
    if not target_dir.parent.exists():
        return {
            "status": "DRIVE_ROOT_NOT_FOUND",
            "message": f"Google Driveマウントパス '{target_dir.parent}' が見つかりません。",
            "synced_files": [],
        }

    target_dir.mkdir(parents=True, exist_ok=True)

    # 1. Source 1: YouTube video reference text & shortcut
    yt_file = target_dir / f"{video_id}_youtube_source.txt"
    yt_content = (
        f"【YouTube元動画資料】\n"
        f"動画ID: {video_id}\n"
        f"タイトル: {video_title}\n"
        f"URL: {video_url}\n"
        f"登録日時: {datetime.now(timezone.utc).isoformat()}\n"
        f"※NotebookLMでYouTubeソースとして追加する場合は、上記URLを直接「YouTube」ソース欄へ投入してください。\n"
    )
    yt_file.write_text(yt_content, encoding="utf-8")

    # 2. Source 2: Research Markdown file
    md_file = target_dir / f"{video_id}_research_note.md"
    if research_md_path.exists():
        md_content = research_md_path.read_text(encoding="utf-8")
        md_file.write_text(md_content, encoding="utf-8")
    else:
        md_content = f"# 研究ノート {video_id}\nURL: {video_url}\n"
        md_file.write_text(md_content, encoding="utf-8")

    # Calculate hashes
    yt_sha = hashlib.sha256(yt_file.read_bytes()).hexdigest()
    md_sha = hashlib.sha256(md_file.read_bytes()).hexdigest()

    return {
        "status": "DRIVE_SYNC_SUCCESS",
        "target_dir": str(target_dir),
        "synced_files": [
            {
                "kind": "YOUTUBE_SOURCE_REF",
                "path": str(yt_file),
                "sha256": yt_sha,
                "size_bytes": yt_file.stat().st_size,
            },
            {
                "kind": "RESEARCH_NOTE_MARKDOWN",
                "path": str(md_file),
                "sha256": md_sha,
                "size_bytes": md_file.stat().st_size,
            },
        ],
    }


def ingest_to_notebook(
    video_id: str,
    video_url: str,
    video_title: str,
    research_md_path: Path,
    try_cdp: bool = True,
    drive_dir: Path = DEFAULT_NOTEBOOK_SOURCES_DIR,
) -> Dict[str, Any]:
    """Execute automated notebook ingestion workflow and return comprehensive status."""
    print("=" * 60)
    print("AI技術研究室 | Gemini Notebook 自動ソース登録処理")
    print(f"対象Notebook: {NOTEBOOK_URL}")
    print(f"動画ID: {video_id}")
    print("=" * 60)

    # 1. Drive Sync (Guaranteed deterministic channel)
    drive_res = sync_to_drive_notebook_sources(
        video_id=video_id,
        video_url=video_url,
        video_title=video_title,
        research_md_path=research_md_path,
        target_dir=drive_dir,
    )
    print(f"[1/2] Google Drive同期フォルダ連携: {drive_res.get('status')}")
    if drive_res.get("status") == "DRIVE_SYNC_SUCCESS":
        for sf in drive_res.get("synced_files", []):
            print(f"  - 配置完了: {sf['kind']} -> {sf['path']} ({sf['size_bytes']} bytes)")

    # 2. CDP Probe (Live browser automation capability check)
    cdp_ok, cdp_msg, tabs = probe_cdp_connection()
    print(f"[2/2] Chrome CDPブラウザ自動化プローブ: {'SUCCESS' if cdp_ok else 'UNAVAILABLE'}")
    print(f"  - 詳細: {cdp_msg}")

    notebook_tab_found = False
    if cdp_ok and tabs:
        for t in tabs:
            tab_url = t.get("url", "")
            if NOTEBOOK_ID in tab_url or "notebook" in tab_url:
                notebook_tab_found = True
                print(f"  - NotebookLMタブを検出: {t.get('title')} ({tab_url})")

    overall_status = "PARTIAL_DRIVE_SYNCED"
    if drive_res.get("status") == "DRIVE_SYNC_SUCCESS":
        if cdp_ok and notebook_tab_found:
            overall_status = "CDP_TAB_ACTIVE"
        else:
            overall_status = "DRIVE_SYNCED_AWAITING_NOTEBOOK_IMPORT"

    return {
        "status": overall_status,
        "notebook_id": NOTEBOOK_ID,
        "notebook_url": NOTEBOOK_URL,
        "drive_sync": drive_res,
        "cdp_probe": {
            "available": cdp_ok,
            "message": cdp_msg,
            "notebook_tab_found": notebook_tab_found,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Gemini Notebook 自動登録モジュール")
    parser.add_argument("video_id", help="登録対象のYouTube動画ID")
    parser.add_argument("--url", help="YouTube動画URL", default=None)
    parser.add_argument("--title", help="動画タイトル", default="YouTube動画")
    parser.add_argument("--research-md", help="研究ノートMarkdownファイルのパス", default=None)
    parser.add_argument("--drive-dir", help="Drive同期先フォルダ", default=str(DEFAULT_NOTEBOOK_SOURCES_DIR))
    args = parser.parse_args()

    v_url = args.url or f"https://www.youtube.com/watch?v={args.video_id}"
    md_p = Path(args.research_md) if args.research_md else Path(f"research/{args.video_id}.md")
    res = ingest_to_notebook(
        video_id=args.video_id,
        video_url=v_url,
        video_title=args.title,
        research_md_path=md_p,
        drive_dir=Path(args.drive_dir),
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
