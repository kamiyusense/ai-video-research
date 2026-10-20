#!/usr/bin/env python3
"""AI技術研究室 | notebooklm-py 経由の「1動画2ソース」自動登録モジュール v0.1.

目的:
docs/OKF_KNOWLEDGE_ROADMAP.md v1.1「1動画2ソースMVP完成契約」に沿って、
字幕原文OKF と 研究ノートOKF を別々のソースとしてNotebookへ登録し、読み戻して確認する。
2026-10-20 にユーザーPCの notebooklm-py 0.8.5 で行った実機作業を再実行可能にしたもの。
既存の notebook_auto_ingest.py（CDP方式）は変更せず、判定・組み立て関数だけ再利用する。

流れ:
1. ログイン点検（auth_check_passive）。失敗なら書き込み0件で AUTH_EXPIRED_HALT。login/refresh は呼ばない。
2. 事前読み戻し（list_sources）→ evaluate_2_source_okf_independence で有無を判定。揃っていれば NO_OP。
3. 足りない方だけ組み立てる（字幕原文は build_transcript_okf_content を再利用）。
4. 既定は dry-run（計画のみ）。live=True かつ notebook_id 指定時だけ add_text する。
5. 書き込み結果が不明（例外・ID無し）でも再送しない。一覧の読み戻しで有無を確認する。
6. 事後読み戻し：完全一致、または Markdown記号・空白を除いた正規化一致で合格。両ソースが別IDであることも確認。

安全:
- クライアントは削除メソッドを持たない。
- このモジュール自体はネットワーク通信を行わない（実機通信は CLI アダプタの subprocess のみ）。
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

AUTO_DIR = Path(__file__).resolve().parent
if str(AUTO_DIR) not in sys.path:
    sys.path.insert(0, str(AUTO_DIR))

from notebook_auto_ingest import (  # noqa: E402
    build_transcript_okf_content,
    evaluate_2_source_okf_independence,
)

ACQ_TIMEDTEXT = "YOUTUBE_TIMEDTEXT_API"
ACQ_NOTEBOOK_YOUTUBE = "NOTEBOOK_YOUTUBE_SOURCE_FULLTEXT"


class NotebookClient(Protocol):
    """Notebook操作の差し替え口。削除系メソッドは意図的に持たない。"""

    def auth_check_passive(self) -> bool: ...

    def list_sources(self) -> List[Dict[str, Any]]: ...  # [{"id": str, "title": str}, ...]

    def get_fulltext(self, source_id: str) -> str: ...

    def add_text(self, title: str, text: str) -> Optional[str]: ...  # 新ソースID（不明ならNone）


class NotebookLmCliClient:
    """notebooklm CLI を subprocess で呼ぶ実機用アダプタ。

    UNVERIFIED: 下記コマンドの正確さは実機未確認。実機で確認済みなのは
    `notebooklm source list --json` と `notebooklm auth check --test --passive` の形だけで、
    ノートブック指定フラグ・fulltext・add-text の書式は推定。実機で使う前に `--help` で照合すること。
    """

    # UNVERIFIED: flags other than the two confirmed forms above are guesses.
    COMMANDS = {
        "auth_check_passive": ["notebooklm", "auth", "check", "--test", "--passive"],
        "list_sources": ["notebooklm", "source", "list", "--json", "--notebook", "{notebook_id}"],
        "get_fulltext": ["notebooklm", "source", "fulltext", "{source_id}", "--json", "--notebook", "{notebook_id}"],
        "add_text": ["notebooklm", "source", "add-text", "--title", "{title}", "--file", "-", "--json", "--notebook", "{notebook_id}"],
    }

    def __init__(self, notebook_id: str, timeout: int = 120):
        if not notebook_id:
            raise ValueError("notebook_id is required")
        self.notebook_id = notebook_id
        self.timeout = timeout

    def _run(self, key: str, stdin: Optional[str] = None, **fmt: str) -> subprocess.CompletedProcess:
        args = [a.format(notebook_id=self.notebook_id, **fmt) for a in self.COMMANDS[key]]
        return subprocess.run(args, input=stdin, capture_output=True, text=True, encoding="utf-8", timeout=self.timeout)

    def auth_check_passive(self) -> bool:
        try:
            return self._run("auth_check_passive").returncode == 0
        except Exception:
            return False

    def list_sources(self) -> List[Dict[str, Any]]:
        cp = self._run("list_sources")
        if cp.returncode != 0:
            raise RuntimeError(f"source list failed (rc={cp.returncode})")
        data = json.loads(cp.stdout)
        rows = data.get("sources", data) if isinstance(data, dict) else data
        return [{"id": str(r.get("id", "")), "title": str(r.get("title", ""))} for r in rows]

    def get_fulltext(self, source_id: str) -> str:
        cp = self._run("get_fulltext", source_id=source_id)
        if cp.returncode != 0:
            raise RuntimeError(f"source fulltext failed (rc={cp.returncode})")
        try:
            data = json.loads(cp.stdout)
            return str(data.get("content") or data.get("text") or "") if isinstance(data, dict) else str(data)
        except json.JSONDecodeError:
            return cp.stdout

    def add_text(self, title: str, text: str) -> Optional[str]:
        cp = self._run("add_text", stdin=text, title=title)
        if cp.returncode != 0:
            raise RuntimeError(f"source add-text failed (rc={cp.returncode})")
        try:
            data = json.loads(cp.stdout)
            sid = data.get("id") if isinstance(data, dict) else None
            return str(sid) if sid else None
        except json.JSONDecodeError:
            return None


# ---------------------------------------------------------------------------
# 判定ヘルパー


def transcript_title(video_id: str, video_title: str) -> str:
    return f"AI_VIDEO_TRANSCRIPT_RAW:{video_id} 【字幕原文】 {video_title}"


def research_note_title(video_id: str) -> str:
    return f"AI_VIDEO_RESEARCH_NOTE:{video_id}"


_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
_MD_LINK_RE = re.compile(r"!?\[([^\]]*)\]\(([^)]*)\)")
_LIST_NUM_RE = re.compile(r"^\s*\d+[.)]\s+", re.M)
_LIST_BULLET_RE = re.compile(r"^\s*[-+]\s+", re.M)
_MD_SYMBOLS_RE = re.compile(r"[#*>`_~|]")
_WS_RE = re.compile(r"\s+")


def normalize_for_readback(text: str) -> str:
    """NotebookLMの表示用整形（Markdown記号・HTMLコメントの除去、改行追加）を吸収する正規化。

    リンク [文字](url) は「文字」と「url」を並べた形に寄せる（文字だけ・URLだけの場合は readback_matches が吸収）。
    """
    s = html.unescape(text or "")
    s = _HTML_COMMENT_RE.sub("", s)
    s = _MD_LINK_RE.sub(lambda m: m.group(1) + m.group(2), s)
    s = _LIST_NUM_RE.sub("", s)
    s = _LIST_BULLET_RE.sub("", s)
    s = _MD_SYMBOLS_RE.sub("", s)
    return _WS_RE.sub("", s)


def readback_matches(expected: str, actual: str) -> Dict[str, Any]:
    """完全一致、または正規化一致で合格。リンクは「文字＋URL」「文字だけ」「URLだけ」のどれが残っても可。"""
    exact = expected == actual
    normalized = exact
    if not exact:
        got = normalize_for_readback(actual)
        variants = (
            expected,
            _MD_LINK_RE.sub(lambda m: m.group(1), expected),
            _MD_LINK_RE.sub(lambda m: m.group(2), expected),
        )
        normalized = any(normalize_for_readback(v) == got for v in variants)
    return {"exact_match": exact, "normalized_match": normalized, "match": normalized}


def classify_sources(sources: List[Dict[str, Any]], video_id: str, video_title: str) -> Dict[str, Any]:
    """既存の evaluate_2_source_okf_independence でソース一覧（タイトル）を判定する。

    has_actual_cues=True で呼ぶ：ここで知りたいのは「字幕原文ソースがあるか」で、
    cue有無の合否は事後読み戻しで別に判定するため。
    """
    items = [
        {"index": i, "text": str(s.get("title", "")), "source_id": s.get("id")}
        for i, s in enumerate(sources)
    ]
    return evaluate_2_source_okf_independence(items, video_id, video_title, has_actual_cues=True)


def build_transcript_text(
    video_id: str,
    video_title: str,
    cues: Optional[List[Any]],
    youtube_fulltext: Optional[str],
) -> Dict[str, Any]:
    url = f"https://www.youtube.com/watch?v={video_id}"
    if cues:
        text = build_transcript_okf_content(video_id, url, video_title, cues=cues)
        method = ACQ_TIMEDTEXT
    else:
        text = build_transcript_okf_content(
            video_id, url, video_title, cues=None, raw_text=youtube_fulltext, status="UNVERIFIED"
        )
        method = ACQ_NOTEBOOK_YOUTUBE
        text = text.replace(f'acquisition_method: "{ACQ_TIMEDTEXT}"', f'acquisition_method: "{method}"', 1)
    return {"text": text, "acquisition_method": method, "cue_count": len(cues) if cues else 0}


# ---------------------------------------------------------------------------
# 本体


def run_ingest(
    client: Optional[NotebookClient],
    video_id: str,
    video_title: str,
    research_note_text: str,
    cues: Optional[List[Any]] = None,
    live: bool = False,
    notebook_id: Optional[str] = None,
) -> Dict[str, Any]:
    """1動画2ソースの不足分を登録する。live=False（既定）では書き込みを一切行わない。"""
    result: Dict[str, Any] = {"video_id": video_id, "live": live, "writes": [], "notes": []}

    if live and not notebook_id:
        result["status"] = "LIVE_REQUIRES_NOTEBOOK_ID"
        return result
    if client is None:
        result["status"] = "DRY_RUN_PLAN_OFFLINE"
        result["plan"] = ["transcript", "research_note"]
        result["notes"].append("Notebook未接続のため、既存ソースの有無は未確認（UNKNOWN）。")
        return result

    if not client.auth_check_passive():
        result["status"] = "AUTH_EXPIRED_HALT"
        return result

    before = client.list_sources()
    pre = classify_sources(before, video_id, video_title)
    result["precheck"] = pre
    need_transcript = not pre["transcript_source_found"]
    need_note = not pre["research_note_found"]

    if not need_transcript and not need_note:
        if pre["transcript_source_id"] == pre["research_note_source_id"]:
            result["status"] = "NEEDS_REVIEW_SAME_SOURCE_ID"
        else:
            result["status"] = "NO_OP"
        return result

    planned: Dict[str, Dict[str, str]] = {}
    if need_transcript:
        yt_text = None
        if not cues and pre["youtube_found"] and pre["youtube_source_id"] != "UNKNOWN":
            yt_text = client.get_fulltext(pre["youtube_source_id"])
        tr = build_transcript_text(video_id, video_title, cues, yt_text)
        result["transcript_acquisition_method"] = tr["acquisition_method"]
        result["transcript_cue_count"] = tr["cue_count"]
        planned["transcript"] = {"title": transcript_title(video_id, video_title), "text": tr["text"]}
    if need_note:
        planned["research_note"] = {"title": research_note_title(video_id), "text": research_note_text}
    result["plan"] = list(planned)

    if not live:
        result["status"] = "DRY_RUN_PLAN"
        return result

    known_ids = {s.get("id") for s in before}
    for kind, p in planned.items():
        entry: Dict[str, Any] = {"kind": kind, "title": p["title"]}
        try:
            entry["source_id"] = client.add_text(p["title"], p["text"])
        except Exception as ex:  # 結果不明：再送しない
            entry["source_id"] = None
            entry["error"] = type(ex).__name__
        if not entry["source_id"]:
            # 再送せず、一覧の読み戻しで追加されたかを確かめる
            found = [s for s in client.list_sources() if s.get("title") == p["title"] and s.get("id") not in known_ids]
            entry["source_id"] = found[0]["id"] if found else None
            entry["result"] = "CONFIRMED_BY_READBACK" if found else "WRITE_RESULT_UNKNOWN"
        else:
            entry["result"] = "ADDED"
        if entry["source_id"]:
            known_ids.add(entry["source_id"])
        result["writes"].append(entry)

    if any(w["result"] == "WRITE_RESULT_UNKNOWN" for w in result["writes"]):
        result["status"] = "WRITE_RESULT_UNKNOWN"
        return result

    # 事後読み戻し
    after = client.list_sources()
    post = classify_sources(after, video_id, video_title)
    result["postcheck"] = post
    checks: Dict[str, Any] = {}
    for w in result["writes"]:
        actual = client.get_fulltext(w["source_id"])
        checks[w["kind"]] = readback_matches(planned[w["kind"]]["text"], actual)
    result["readback"] = checks

    distinct = (
        post["transcript_source_found"]
        and post["research_note_found"]
        and post["transcript_source_id"] != post["research_note_source_id"]
    )
    result["distinct_source_ids"] = bool(distinct)
    if distinct and all(c["match"] for c in checks.values()):
        result["status"] = "SUCCESS_2_SOURCE_OKF"
    else:
        result["status"] = "READBACK_MISMATCH"
    return result


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="notebooklm-py 経由の1動画2ソース登録（既定はdry-run）")
    ap.add_argument("--video-id", required=True)
    ap.add_argument("--video-title", required=True)
    ap.add_argument("--research-md", required=True, type=Path)
    ap.add_argument("--cues-json", type=Path, help="字幕cueのJSON（[[start, dur, text], ...]）。無ければNotebookのYouTubeソース本文を使う")
    ap.add_argument("--notebook-id")
    ap.add_argument("--live", action="store_true", help="実際にNotebookへ書き込む（--notebook-id 必須）")
    args = ap.parse_args(argv)

    if args.live and not args.notebook_id:
        print("--live には --notebook-id の明示が必要です。", file=sys.stderr)
        return 2
    cues = json.loads(args.cues_json.read_text(encoding="utf-8")) if args.cues_json else None
    client = NotebookLmCliClient(args.notebook_id) if args.notebook_id else None
    res = run_ingest(
        client,
        video_id=args.video_id,
        video_title=args.video_title,
        research_note_text=args.research_md.read_text(encoding="utf-8"),
        cues=cues,
        live=args.live,
        notebook_id=args.notebook_id,
    )
    res.pop("precheck", None)
    res.pop("postcheck", None)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res["status"] in ("NO_OP", "SUCCESS_2_SOURCE_OKF", "DRY_RUN_PLAN", "DRY_RUN_PLAN_OFFLINE") else 1


if __name__ == "__main__":
    sys.exit(main())
