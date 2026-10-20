#!/usr/bin/env python3
"""AI技術研究室 | notebooklm-py 経由の「1動画2ソース」自動登録モジュール v0.1.

目的:
docs/OKF_KNOWLEDGE_ROADMAP.md v1.1「1動画2ソースMVP完成契約」に沿って、
字幕原文OKF と 研究ノートOKF を別々のソースとしてNotebookへ登録し、読み戻して確認する。
2026-10-20 にユーザーPCの notebooklm-py 0.8.5 で行った実機作業を再実行可能にしたもの。
既存の notebook_auto_ingest.py（CDP方式）は変更せず、字幕原文OKFの組み立て関数だけ再利用する。
（CDP用の evaluate_2_source_okf_independence は実Notebookのタイトル形式を拾えないため使わない。2026-10-20 検品T2）

流れ:
1. ログイン点検（auth_check_passive）。失敗なら書き込み0件で AUTH_EXPIRED_HALT。login/refresh は呼ばない。
2. 事前読み戻し（list_sources）→ classify_sources で種類（type）とタイトルから有無を判定。
   タイトルで決めきれなければ本文の荷札（type / logical_id）を読み、それでも曖昧なら書き込み0で
   AMBIGUOUS_EXISTING_SOURCES。揃っていれば NO_OP。
3. 足りない方だけ組み立てる（字幕原文は build_transcript_okf_content を再利用）。
   2026-10-20 22:42 JST 相棒の方針転換（docs/OKF_KNOWLEDGE_ROADMAP.md R3）: 字幕全文は時刻なしを正とし、
   発話を段落にまとめた本文にする（場面の時刻リンクは研究ノート側）。字幕の取得元は
   渡されたcue → Notebook内YouTubeソースの本文（fulltext）→ YouTube字幕（youtube-transcript-api→timedtext）の順。
   どれも取れなければ書き込み0で TRANSCRIPT_UNAVAILABLE。両OKFに published_at を記録する。
4. 既定は dry-run（計画のみ）。live=True かつ notebook_id 指定時だけ add_text する。
5. 書き込み結果が不明（例外・ID無し）でも再送しない。一覧の読み戻しで有無を確認する。
6. 事後読み戻し：完全一致、または Markdown記号・空白を除いた正規化一致で合格。両ソースが別IDであることも確認。

安全:
- クライアントは削除メソッドを持たない。
- 外部通信は CLI アダプタの subprocess と、CLI実行時の YouTube 字幕・投稿日時の取得（fetch_youtube_transcript）だけ。
  run_ingest は fetch_transcript を渡されない限り通信しない。
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol

AUTO_DIR = Path(__file__).resolve().parent
ROOT = AUTO_DIR.parents[1]
REGISTRY_PATH = ROOT / "registry.json"
if str(AUTO_DIR) not in sys.path:
    sys.path.insert(0, str(AUTO_DIR))

from notebook_auto_ingest import build_transcript_okf_content  # noqa: E402
from receipt_to_research import linkify_timestamps  # noqa: E402

ACQ_TIMEDTEXT = "YOUTUBE_TIMEDTEXT_API"
ACQ_TRANSCRIPT_API = "YOUTUBE_TRANSCRIPT_API"
ACQ_NOTEBOOK_FULLTEXT = "NOTEBOOK_YOUTUBE_SOURCE_FULLTEXT"


class NotebookClient(Protocol):
    """Notebook操作の差し替え口。削除系メソッドは意図的に持たない。"""

    def auth_check_passive(self) -> bool: ...

    def list_sources(self) -> List[Dict[str, Any]]: ...  # [{"id": str, "type": str, "title": str}, ...]

    def get_fulltext(self, source_id: str) -> str: ...

    def add_text(self, title: str, text: str) -> Optional[str]: ...  # 新ソースID（不明ならNone）


class NotebookLmCliClient:
    """notebooklm CLI を subprocess で呼ぶ実機用アダプタ。

    コマンドの形は notebooklm-py 0.8.5 の実CLIで照合済み（2026-10-20 検品ループ記録7）。
    auth / list / fulltext は実機dry-runで動作確認済み。add は実機調査（同記録）で判明した形で、
    書き込みの実行は未確認（UNVERIFIED）。本文は標準入力で渡す（`--type text` のときだけ `-` が使える）。
    """

    COMMANDS = {
        "auth_check_passive": ["notebooklm", "auth", "check", "--test", "--passive"],
        "list_sources": ["notebooklm", "source", "list", "--json", "--notebook", "{notebook_id}"],
        "get_fulltext": ["notebooklm", "source", "fulltext", "{source_id}", "--json", "--notebook", "{notebook_id}"],
        "add_text": ["notebooklm", "source", "add", "-", "--type", "text", "--title", "{title}", "--json", "--notebook", "{notebook_id}"],
    }

    def __init__(self, notebook_id: str, timeout: int = 120, add_timeout: int = 600):
        if not notebook_id:
            raise ValueError("notebook_id is required")
        self.notebook_id = notebook_id
        self.timeout = timeout
        self.add_timeout = add_timeout

    def _run(
        self, key: str, stdin: Optional[str] = None, timeout: Optional[int] = None, **fmt: str
    ) -> subprocess.CompletedProcess:
        args = [a.format(notebook_id=self.notebook_id, **fmt) for a in self.COMMANDS[key]]
        return subprocess.run(
            args, input=stdin, capture_output=True, text=True, encoding="utf-8", timeout=timeout or self.timeout
        )

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
        return [
            {"id": str(r.get("id", "")), "type": str(r.get("type", "")).lower(), "title": str(r.get("title", ""))}
            for r in rows
        ]

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
        cp = self._run("add_text", stdin=text, timeout=self.add_timeout, title=title)
        if cp.returncode != 0:
            raise RuntimeError(f"source add failed (rc={cp.returncode})")
        try:
            data = json.loads(cp.stdout)
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
            return None
        src = data.get("source")
        sid = (src.get("id") if isinstance(src, dict) else None) or data.get("id")
        return str(sid) if sid else None


# ---------------------------------------------------------------------------
# 判定ヘルパー


SHORT_TITLE_MAX = 40


def _short_title(video_title: str) -> str:
    t = " ".join((video_title or "").split())
    return t if len(t) <= SHORT_TITLE_MAX else t[:SHORT_TITLE_MAX].rstrip() + "…"


def transcript_title(video_id: str, video_title: str) -> str:
    return f"【字幕原文】{_short_title(video_title)} [{video_id}]"


def research_note_title(video_id: str, video_title: str) -> str:
    return f"【研究ノート】{_short_title(video_title)} [{video_id}]"


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


def _title_kind(title: str, video_id: str) -> Optional[str]:
    """実Notebookのタイトル形式（2026-10-20 一覧）から種類を決める。決めきれなければ None。"""
    bracket = f"[{video_id}]"
    if (
        (title.startswith("【字幕原文】") and bracket in title)
        or f"AI_VIDEO_TRANSCRIPT_RAW:{video_id}" in title
        or f"youtube:{video_id}:transcript" in title
    ):
        return "transcript"
    if (
        (title.startswith("【研究ノート】") and bracket in title)
        or (title.startswith(("動画研究_", "研究動画_")) and video_id in title)
        or f"AI_VIDEO_RESEARCH_NOTE:{video_id}" in title
        or f"youtube:{video_id}:research" in title
    ):
        return "research_note"
    return None


def _body_kind(body: str, video_id: str) -> Optional[str]:
    """本文の荷札（logical_id / type）から種類を決める。関連リンクの記載に引っ張られないよう行頭の項目だけ見る。"""
    vid = re.escape(video_id)
    m = re.search(rf'^\s*logical_id:\s*"?youtube:{vid}:(transcript|research)"?\s*$', body or "", re.M)
    if m:
        return "transcript" if m.group(1) == "transcript" else "research_note"
    if video_id in (body or "") and re.search(r'^\s*type:\s*"?TRANSCRIPT"?\s*$', body or "", re.M):
        return "transcript"
    return None


def _same_title(a: str, b: str) -> bool:
    na, nb = normalize_for_readback(a), normalize_for_readback(b)
    return bool(na) and bool(nb) and (na == nb or na in nb or nb in na)


def classify_sources(
    sources: List[Dict[str, Any]],
    video_id: str,
    video_title: str,
    client: Optional[NotebookClient] = None,
) -> Dict[str, Any]:
    """ソース一覧を YouTube / 字幕原文OKF / 研究ノートOKF に振り分ける。

    - YouTube は type=="youtube" かつタイトル一致のものだけ（IDを含むmarkdownをYouTube扱いしない）。
    - 字幕原文・研究ノートは youtube 以外の type からタイトル形式で判定。
    - 種類不明（IDを含むがタイトル形式に合わない）や同じ種類が複数ある場合は、client があれば本文の荷札で判定。
    - それでも決めきれなければ ambiguous=True。
    """
    youtube = [s for s in sources if s.get("type") == "youtube" and _same_title(str(s.get("title", "")), video_title)]
    kinds: Dict[str, List[Dict[str, Any]]] = {"transcript": [], "research_note": []}
    unknown: List[Dict[str, Any]] = []
    for s in sources:
        if s.get("type") == "youtube":
            continue
        title = str(s.get("title", ""))
        k = _title_kind(title, video_id)
        if k:
            kinds[k].append(s)
        elif video_id in title:
            unknown.append(s)

    reasons: List[str] = []
    # (source, タイトル上の種類 or None)。同じ種類が複数あるものは本文の荷札で絞り込む
    to_inspect = [(s, None) for s in unknown]
    for k, cands in kinds.items():
        if len(cands) > 1:
            to_inspect.extend((s, k) for s in cands)
            kinds[k] = []
    if to_inspect:
        if client is None:
            reasons.append("タイトルで決めきれないソースがあるが、本文を読めない")
        else:
            unresolved: List[tuple] = []
            for s, title_k in to_inspect:
                k = _body_kind(client.get_fulltext(s["id"]), video_id)
                if k:
                    kinds[k].append(s)
                else:
                    unresolved.append((s, title_k))
            for s, title_k in unresolved:
                # タイトル上同じ種類の重複で、別の1件が荷札で確定したなら、それを正とする
                if title_k and len(kinds[title_k]) == 1:
                    continue
                reasons.append(f"種類不明: {s.get('title')}")
    for k, cands in kinds.items():
        if len(cands) > 1:
            reasons.append(f"{k} の候補が複数: " + ", ".join(str(c.get("title")) for c in cands))
    if len(youtube) > 1:
        reasons.append("YouTubeソースの候補が複数")

    def _one(cands: List[Dict[str, Any]]) -> Optional[str]:
        return str(cands[0]["id"]) if len(cands) == 1 else None

    return {
        "youtube_source_id": _one(youtube),
        "transcript_source_id": _one(kinds["transcript"]),
        "research_note_source_id": _one(kinds["research_note"]),
        "ambiguous": bool(reasons),
        "ambiguous_reasons": reasons,
    }


def build_transcript_text(
    video_id: str,
    video_title: str,
    cues: Optional[List[Any]],
    published_at: Optional[str],
    acquisition_method: str = ACQ_TIMEDTEXT,
    raw_text: Optional[str] = None,
) -> Dict[str, Any]:
    """字幕全文OKF（既定は時刻なしの段落本文）。cue が無ければ raw_text（Notebook内YouTubeソースの本文など）を使う。"""
    url = f"https://www.youtube.com/watch?v={video_id}"
    text = build_transcript_okf_content(
        video_id, url, video_title, cues=cues or None, raw_text=None if cues else raw_text,
        published_at=published_at, acquisition_method=acquisition_method,
    )
    return {"text": text, "acquisition_method": acquisition_method, "cue_count": len(cues or [])}


def ensure_published_at(research_note_text: str, published_at: Optional[str]) -> str:
    """研究ノートの荷札に published_at が無ければ1行足す（既にあれば変えない）。"""
    value = str(published_at).strip() if published_at and str(published_at).strip() else "UNKNOWN"
    line = f'published_at: "{value}"'
    text = research_note_text or ""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            if re.search(r"^\s*published_at:", parts[1], re.M):
                return text
            fm = parts[1].rstrip("\n") + "\n" + line + "\n"
            return "---" + fm + "---" + parts[2]
    return "---\n" + line + "\n---\n" + text


def fetch_cues_transcript_api(video_id: str, languages: tuple = ("ja", "en")) -> List[Any]:
    """youtube-transcript-api で時刻つき字幕を取る（未インストールなら ImportError）。

    相棒PCで 1.2.2 により pRfC1DILDEM 275 cue・u3ka_AAb8qE 381 cue の取得を確認済み（検品ループ記録 T6）。
    `YouTubeTranscriptApi().fetch(...)` の呼び方は 1.x 系のもの。
    """
    from youtube_transcript_api import YouTubeTranscriptApi

    fetched = YouTubeTranscriptApi().fetch(video_id, languages=list(languages))
    return [(float(c.start), float(c.start) + float(c.duration), c.text) for c in fetched]


def fetch_cues_timedtext(video_id: str) -> List[Any]:
    """既存の取得関数（YouTube player API → timedtext）で時刻つき字幕を取る。"""
    import auto_research_pipeline
    import verify_timestamps

    player = verify_timestamps.fetch_player(video_id)
    if not player:
        return []
    _, cues, _ = auto_research_pipeline.fetch_actual_captions(player)
    return list(cues or [])


CUE_SOURCES = (
    (ACQ_TRANSCRIPT_API, fetch_cues_transcript_api),
    (ACQ_TIMEDTEXT, fetch_cues_timedtext),
)


def fetch_youtube_transcript(video_id: str, sources=None) -> Dict[str, Any]:
    """実行PCから YouTube の時刻つき字幕と投稿日時を取る。失敗は空で返す。

    字幕は sources を順に試し、最初に cue が取れたものを使う（既定: youtube-transcript-api → 既存timedtext）。
    """
    import verify_timestamps

    out: Dict[str, Any] = {"cues": [], "published_at": None, "acquisition_method": None, "errors": {}}
    for method, fn in (CUE_SOURCES if sources is None else sources):
        try:
            cues = fn(video_id)
        except Exception as ex:
            out["errors"][method] = type(ex).__name__
            continue
        if cues:
            out["cues"] = list(cues)
            out["acquisition_method"] = method
            break
    try:
        out["published_at"] = verify_timestamps.fetch_watch_publish_date(video_id)
    except Exception:
        pass
    return out


# ---------------------------------------------------------------------------
# 本体


PLAN_LOGICAL_SUFFIX = {"transcript": "transcript", "research_note": "research"}


def plan_details(video_id: str, video_title: str, kinds: List[str]) -> List[Dict[str, str]]:
    """追加予定ソースの種類・タイトル・logical_id（計画の表示用。本文は含めない）。"""
    titles = {"transcript": transcript_title, "research_note": research_note_title}
    return [
        {"kind": k, "title": titles[k](video_id, video_title), "logical_id": f"youtube:{video_id}:{PLAN_LOGICAL_SUFFIX[k]}"}
        for k in kinds
    ]


def run_ingest(
    client: Optional[NotebookClient],
    video_id: str,
    video_title: str,
    research_note_text: str,
    cues: Optional[List[Any]] = None,
    live: bool = False,
    notebook_id: Optional[str] = None,
    published_at: Optional[str] = None,
    fetch_transcript: Optional[Callable[[str], Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """1動画2ソースの不足分を登録する。live=False（既定）では書き込みを一切行わない。

    cues / published_at が無く fetch_transcript があれば、それで時刻つき字幕と投稿日時を取る。
    """
    result: Dict[str, Any] = {"video_id": video_id, "live": live, "writes": [], "notes": []}

    if live and not notebook_id:
        result["status"] = "LIVE_REQUIRES_NOTEBOOK_ID"
        return result
    if client is None:
        result["status"] = "DRY_RUN_PLAN_OFFLINE"
        result["plan"] = ["transcript", "research_note"]
        result["plan_details"] = plan_details(video_id, video_title, result["plan"])
        result["notes"].append("Notebook未接続のため、既存ソースの有無は未確認（UNKNOWN）。")
        return result

    if not client.auth_check_passive():
        result["status"] = "AUTH_EXPIRED_HALT"
        return result

    before = client.list_sources()
    pre = classify_sources(before, video_id, video_title, client)
    result["precheck"] = pre
    if pre["ambiguous"]:
        result["status"] = "AMBIGUOUS_EXISTING_SOURCES"
        return result
    need_transcript = pre["transcript_source_id"] is None
    need_note = pre["research_note_source_id"] is None

    if not need_transcript and not need_note:
        result["status"] = "NO_OP"
        return result

    acquisition_method = ACQ_TIMEDTEXT
    raw_text: Optional[str] = None
    if need_transcript and not cues and pre.get("youtube_source_id"):
        # 既存動画：Notebook内YouTubeソースの本文（時刻なし）を字幕全文に使う（22:42 方針転換で正式扱い）
        raw_text = (client.get_fulltext(pre["youtube_source_id"]) or "").strip() or None
        if raw_text:
            acquisition_method = ACQ_NOTEBOOK_FULLTEXT
    if fetch_transcript and ((need_transcript and not cues and not raw_text) or not published_at):
        fetched = fetch_transcript(video_id) or {}
        if need_transcript and not cues and not raw_text:
            cues = fetched.get("cues") or None
            acquisition_method = fetched.get("acquisition_method") or ACQ_TIMEDTEXT
        if not published_at:
            published_at = fetched.get("published_at")
    result["published_at"] = published_at or "UNKNOWN"

    planned: Dict[str, Dict[str, str]] = {}
    if need_transcript:
        if not cues and not raw_text:
            result["status"] = "TRANSCRIPT_UNAVAILABLE"
            result["notes"].append("字幕全文を取得できなかった（Notebook内YouTubeソース本文・YouTube字幕とも無し）ため、何も書き込まずに停止。")
            return result
        tr = build_transcript_text(video_id, video_title, cues, published_at, acquisition_method, raw_text=raw_text)
        result["transcript_acquisition_method"] = tr["acquisition_method"]
        result["transcript_cue_count"] = tr["cue_count"]
        planned["transcript"] = {"title": transcript_title(video_id, video_title), "text": tr["text"]}
    if need_note:
        planned["research_note"] = {
            "title": research_note_title(video_id, video_title),
            # Notebook側のコピーだけ根拠時刻をリンク化する（GitHubの研究ノートは書き換えない）
            "text": linkify_timestamps(ensure_published_at(research_note_text, published_at), video_id),
        }
    result["plan"] = list(planned)
    result["plan_details"] = plan_details(video_id, video_title, result["plan"])

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
    post = classify_sources(after, video_id, video_title, client)
    result["postcheck"] = post
    checks: Dict[str, Any] = {}
    for w in result["writes"]:
        actual = client.get_fulltext(w["source_id"])
        checks[w["kind"]] = readback_matches(planned[w["kind"]]["text"], actual)
    result["readback"] = checks

    distinct = (
        not post["ambiguous"]
        and post["transcript_source_id"] is not None
        and post["research_note_source_id"] is not None
        and post["transcript_source_id"] != post["research_note_source_id"]
    )
    result["distinct_source_ids"] = bool(distinct)
    if distinct and all(c["match"] for c in checks.values()):
        result["status"] = "SUCCESS_2_SOURCE_OKF"
    else:
        result["status"] = "READBACK_MISMATCH"
    return result


# ---------------------------------------------------------------------------
# 健康診断（読み取り専用）

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
_NOTE_TITLE_RE = re.compile(r"^(【研究ノート】|動画研究_|研究動画_)|AI_VIDEO_RESEARCH_NOTE:|youtube:[\w-]{11}:research")
_TRANSCRIPT_TITLE_RE = re.compile(r"^【字幕原文】|AI_VIDEO_TRANSCRIPT_RAW:|youtube:[\w-]{11}:transcript")
REGISTRY_SOURCE_KEYS = ("research_note", "transcript_okf", "youtube_url_source")


def health_check(client: NotebookClient, registry: Dict[str, Any]) -> Dict[str, Any]:
    """Notebookと台帳 registry.json の notebook_sources を照合する。書き込み系は一切呼ばない。"""
    if not client.auth_check_passive():
        return {
            "status": "AUTH_EXPIRED",
            "user_action": "相棒のPCでNotebookLMにログインし直してください（このツールはログインを自動で行いません）。",
        }

    sources = client.list_sources()
    notebook_ids = {str(s.get("id")) for s in sources}
    records = registry.get("records", [])

    registry_ids: Dict[str, Dict[str, str]] = {}
    for r in records:
        ns = r.get("notebook_sources") or {}
        for key in REGISTRY_SOURCE_KEYS:
            sid = str(ns.get(key) or "")
            if _UUID_RE.match(sid):
                registry_ids.setdefault(sid, {"video_id": r.get("video_id"), "kind": key})

    missing = [
        {"source_id": sid, **meta} for sid, meta in registry_ids.items() if sid not in notebook_ids
    ]

    unregistered = []
    for s in sources:
        if s.get("type") == "youtube" or str(s.get("id")) in registry_ids:
            continue
        title = str(s.get("title", ""))
        kind = (
            "transcript_okf" if _TRANSCRIPT_TITLE_RE.search(title)
            else "research_note" if _NOTE_TITLE_RE.search(title)
            else None
        )
        if kind:
            unregistered.append({"source_id": s.get("id"), "kind": kind, "title": title})

    transcript_missing = []
    for r in records:
        sid = str((r.get("notebook_sources") or {}).get("transcript_okf") or "")
        if not (_UUID_RE.match(sid) and sid in notebook_ids):
            transcript_missing.append(r.get("video_id"))

    # 字幕全文・研究ノートの荷札に投稿日時が無い（UNKNOWN含む）ものを数える（R4。本文の読み取りのみ）
    published_missing = []
    for s in sources:
        if s.get("type") == "youtube":
            continue
        title = str(s.get("title", ""))
        meta = registry_ids.get(str(s.get("id")), {})
        kind = (
            "transcript_okf" if meta.get("kind") == "transcript_okf" or _TRANSCRIPT_TITLE_RE.search(title)
            else "research_note" if meta.get("kind") == "research_note" or _NOTE_TITLE_RE.search(title)
            else None
        )
        if not kind:
            continue
        value = published_at_of(client.get_fulltext(str(s.get("id"))))
        if value in (None, "UNKNOWN"):
            published_missing.append({"source_id": s.get("id"), "kind": kind, "title": title, "published_at": value or "MISSING"})

    return {
        "status": "OK" if not missing and not unregistered and not published_missing else "ATTENTION",
        "notebook_source_count": len(sources),
        "registry_record_count": len(records),
        "registry_ids_missing_in_notebook": missing,
        "registry_ids_missing_in_notebook_count": len(missing),
        "notebook_sources_not_in_registry": unregistered,
        "notebook_sources_not_in_registry_count": len(unregistered),
        "videos_without_transcript_okf": transcript_missing,
        "videos_without_transcript_okf_count": len(transcript_missing),
        "sources_without_published_at": published_missing,
        "sources_without_published_at_count": len(published_missing),
    }


_PUBLISHED_AT_RE = re.compile(r'^\s*published[_ ]?at\s*[:：]\s*"?([^"\n]*?)"?\s*$', re.M | re.I)


def published_at_of(body: Optional[str]) -> Optional[str]:
    """本文の荷札の published_at 値（無ければ None、空・UNKNOWN は "UNKNOWN"）。"""
    m = _PUBLISHED_AT_RE.search(body or "")
    if not m:
        return None
    value = m.group(1).strip()
    return "UNKNOWN" if not value or value.upper() == "UNKNOWN" else value


_RESEARCH_FILE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-([\w-]{11})-")
_ID_IN_TITLE_RE = re.compile(r"\[([\w-]{11})\]\s*$")


def resolve_video_id(youtube_title: str, sources: List[Dict[str, Any]], research_dir: Path) -> Optional[str]:
    """YouTubeソースのタイトルから動画IDを探す（Notebook内の「【…】題 [ID]」→ GitHub研究ノートの本文の順）。"""
    for s in sources:
        title = str(s.get("title", ""))
        m = _ID_IN_TITLE_RE.search(title)
        if s.get("type") != "youtube" and m and title.startswith(("【研究ノート】", "【字幕原文】")):
            if _same_title(title, youtube_title) or youtube_title.startswith(_short_title(title.split("】", 1)[1].rsplit("[", 1)[0].strip())):
                return m.group(1)
    hits = set()
    for path in sorted(Path(research_dir).glob("*.md")):
        m = _RESEARCH_FILE_RE.match(path.name)
        if m and youtube_title in path.read_text(encoding="utf-8", errors="replace"):
            hits.add(m.group(1))
    return hits.pop() if len(hits) == 1 else None


def plan_url_source_migration(
    client: NotebookClient,
    research_dir: Path = ROOT / "research",
) -> Dict[str, Any]:
    """URL単体ソース（type=youtube）を字幕全文OKFへ移す計画を返す。読み取りのみで、追加も削除もしない。

    2026-10-20 22:42 JST 相棒の判断: 先に各動画の字幕全文OKF（時刻なし・published_at入り）を登録し、
    読み戻しで一致を確かめてから、URLソースを削除してよい。このツールは削除の実行コードを持たない。
    """
    if not client.auth_check_passive():
        return {"status": "AUTH_EXPIRED", "user_action": "相棒のPCでNotebookLMにログインし直してください。", "items": []}
    sources = client.list_sources()
    items = []
    for yt in [s for s in sources if s.get("type") == "youtube"]:
        title = str(yt.get("title", ""))
        vid = resolve_video_id(title, sources, research_dir)
        item: Dict[str, Any] = {"youtube_source_id": yt.get("id"), "youtube_title": title, "video_id": vid or "UNKNOWN"}
        fulltext = (client.get_fulltext(str(yt.get("id"))) or "").strip()
        item["transcript_source_order"] = [
            {"method": ACQ_NOTEBOOK_FULLTEXT, "source_id": yt.get("id"), "available": bool(fulltext), "chars": len(fulltext)},
            {"method": ACQ_TRANSCRIPT_API, "available": "UNKNOWN（実行PCで取得して確認）"},
        ]
        if not vid:
            item.update(status="VIDEO_ID_UNKNOWN", existing={}, to_add=[], delete_after_readback=[],
                        notes=["動画IDを特定できないため計画から外す（削除もしない）。"])
            items.append(item)
            continue
        pre = classify_sources(sources, vid, title, client)
        tr_id, rn_id = pre["transcript_source_id"], pre["research_note_source_id"]
        tr_pub = published_at_of(client.get_fulltext(tr_id)) if tr_id else None
        item["existing"] = {
            "transcript_okf": tr_id, "transcript_published_at": (tr_pub or "MISSING") if tr_id else None,
            "research_note_okf": rn_id,
        }
        to_add = []
        if not tr_id:
            to_add.append("transcript")
        if not rn_id:
            to_add.append("research_note")
        item["to_add"] = plan_details(vid, title, to_add)
        item["notes"] = []
        if pre["ambiguous"]:
            item["status"] = "AMBIGUOUS_EXISTING_SOURCES"
            item["delete_after_readback"] = []
            item["notes"].extend(pre["ambiguous_reasons"])
        elif tr_id and tr_pub not in (None, "UNKNOWN"):
            item["status"] = "READY_TO_DELETE_URL_SOURCE"
            item["delete_after_readback"] = [yt.get("id")]
            item["notes"].append("字幕全文OKF（published_at入り）が既にある。削除前にその本文の読み戻し一致をもう一度確かめる。")
        else:
            item["status"] = "ADD_THEN_DELETE"
            item["delete_after_readback"] = [yt.get("id")]
            if tr_id:
                item["to_add_pending_approval"] = plan_details(vid, title, ["transcript"])
                item["replace_pending_approval"] = [tr_id]
                item["notes"].append(f"既存の字幕全文OKF {tr_id} に published_at が無い。入り版の追加・置き換え（{tr_id} の削除）は相棒の承認待ち。")
            item["notes"].append("URLソースの削除は、追加した字幕全文OKFの読み戻し一致を確かめた後だけ（その前は削除しない）。")
        items.append(item)
    return {
        "status": "DRY_RUN_MIGRATION_PLAN",
        "url_source_count": len(items),
        "video_id_unknown_count": sum(1 for i in items if i["video_id"] == "UNKNOWN"),
        "delete_after_readback_count": sum(len(i["delete_after_readback"]) for i in items),
        "deletion_executed": False,
        "items": items,
    }


def main_health(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(prog="notebooklm_py_ingest.py health", description="Notebook健康診断（読み取り専用）")
    ap.add_argument("--notebook-id", required=True)
    ap.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    args = ap.parse_args(argv)
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    rep = health_check(NotebookLmCliClient(args.notebook_id), registry)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0 if rep["status"] == "OK" else (3 if rep["status"] == "AUTH_EXPIRED" else 1)


def main_migrate_plan(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(prog="notebooklm_py_ingest.py migrate-plan",
                                 description="URL単体ソースの移行計画（読み取りのみ・削除しない）")
    ap.add_argument("--notebook-id", required=True)
    ap.add_argument("--research-dir", type=Path, default=ROOT / "research")
    args = ap.parse_args(argv)
    rep = plan_url_source_migration(NotebookLmCliClient(args.notebook_id), args.research_dir)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 3 if rep["status"] == "AUTH_EXPIRED" else 0


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["health"]:
        return main_health(argv[1:])
    if argv[:1] == ["migrate-plan"]:
        return main_migrate_plan(argv[1:])
    ap = argparse.ArgumentParser(description="notebooklm-py 経由の1動画2ソース登録（既定はdry-run）")
    ap.add_argument("--video-id", required=True)
    ap.add_argument("--video-title", required=True)
    ap.add_argument("--research-md", required=True, type=Path)
    ap.add_argument("--cues-json", type=Path, help="字幕cueのJSON（[[start, end, text], ...]）。無ければNotebook内YouTubeソース本文→YouTube字幕の順に取る")
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
        fetch_transcript=fetch_youtube_transcript,
    )
    res.pop("precheck", None)
    res.pop("postcheck", None)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res["status"] in ("NO_OP", "SUCCESS_2_SOURCE_OKF", "DRY_RUN_PLAN", "DRY_RUN_PLAN_OFFLINE") else 1


if __name__ == "__main__":
    sys.exit(main())
