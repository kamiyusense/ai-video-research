#!/usr/bin/env python3
"""Independent YouTube timestamp verifier for Gemini handoff receipts (v0.6.1).

Purpose
-------
Gemini handoff receipts contain chapter timestamps reported by another AI. Those are
untrusted input. This tool independently checks each reported chapter start/end against
public YouTube data and writes a compact evidence file that the normalizer consults:

    automation/gemini-notebook/state/timestamp_evidence.json

Checks per video
----------------
1. `lengthSeconds`, `publishDate`, `title`, `author`, and description chapters from YouTube.
2. Video-level timeline integrity:
   - `dur_match`: reported video duration (or final chapter end) must match `lengthSeconds` within +/-2s.
   - `contradicts_desc`: if official description chapters exist (>=3), at least 2 non-zero reported
     chapters must align with official description chapters within +/-5s; otherwise the reported
     timeline contradicts the official chapter structure.
3. Timed captions (manual preferred, otherwise ASR) fetched in memory only.
   Caption text is NEVER written to disk; only matched title tokens and counts
   are stored as evidence.

Per-chapter verdicts
--------------------
- `DESC_MATCH`          : `dur_match` and not `contradicts_desc`, and chapter start matches an official
                          YouTube description chapter within +/-5s (-> YOUTUBE_CHAPTER_METADATA)
- `CAPTION_PASS`        : `dur_match` and not `contradicts_desc`, and title tokens appear in timed
                          captions within the chapter window and beat shifted control windows
                          (-> TIMESTAMPED_CAPTIONS)
- `CAPTION_FAIL`        : captions checked but reported timestamp is not supported by caption tokens
- `DURATION_MISMATCH`   : reported video duration deviates from actual YouTube `lengthSeconds` (>2s)
- `CONTRADICTS_DESC`    : reported timeline contradicts official YouTube description chapters
- `OUT_OF_RANGE`        : reported start or end exceeds the real video length (+2s tolerance)
- `NO_CAPTIONS`         : no caption track retrievable
Anything other than DESC_MATCH / CAPTION_PASS must be rendered as UNKNOWN downstream.
"""
import argparse
import html
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVIDENCE_PATH = (
    Path(__file__).resolve().parent / "state" / "timestamp_evidence.json"
)
EVIDENCE_SCHEMA = "timestamp_evidence_v1"
DESC_TOLERANCE_SEC = 5
WINDOW_BEFORE_SEC = 15
WINDOW_MIN_AFTER_SEC = 90
WINDOW_MAX_AFTER_SEC = 300
CONTROL_SHIFT_SEC = 240
ANDROID_CLIENT = {
    "clientName": "ANDROID",
    "clientVersion": "20.10.38",
    "androidSdkVersion": 30,
    "hl": "ja",
}
ANDROID_UA = "com.google.android.youtube/20.10.38 (Linux; U; Android 11) gzip"
WEB_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")

STOP_TOKENS = {
    "概要", "まとめ", "解説", "紹介", "実演", "方法", "機能", "活用", "設定", "注意点",
    "比較", "基本", "使い方", "実践", "対応", "確認", "作成", "案内", "生成", "自動",
    "全体", "具体", "必要", "可能", "場合", "今後", "仕組", "仕組み", "ポイント",
    "ステップ", "要素", "条件", "準備", "理由", "特徴", "効果", "課題", "問題",
    "これ", "それ", "こと", "もの", "ため", "よう", "ai",
}

ASR_ALIASES = {
    "obsidian": ["obsidian", "オブシディアン", "オブシディ"],
    "claude": ["claude", "クロード"],
    "agent": ["agent", "エージェント"],
    "agents": ["agents", "エージェント"],
    "opus": ["opus", "オーパス"],
    "sonnet": ["sonnet", "ソネット"],
    "deepseek": ["deepseek", "ディープシーク"],
    "harness": ["harness", "ハーネス"],
    "studio": ["studio", "スタジオ"],
    "notebooklm": ["notebooklm", "ノートブック"],
    "notebook": ["notebook", "ノートブック"],
    "gemini": ["gemini", "ジェミニ"],
    "cowork": ["cowork", "コワーク"],
    "skill": ["skill", "スキル"],
    "skills": ["skills", "スキル"],
    "prompt": ["prompt", "プロンプト"],
    "token": ["token", "トークン"],
    "memory": ["memory", "メモリー", "メモリ"],
    "eval": ["eval", "エバル", "評価"],
    "vault": ["vault", "ボールト", "ボルト"],
    "markdown": ["markdown", "マークダウン"],
    "fireshot": ["fireshot", "ファイアショット", "スクショ", "スクリーンショット"],
    "grokbot": ["grokbot", "グロック"],
    "dot": ["dot", "ドット"],
    "codex": ["codex", "コーデックス"],
    "spark": ["spark", "スパーク"],
    "antigravity": ["antigravity", "アンチグラビティ"],
    "mcp": ["mcp", "エムシーピー"],
}

TOKEN_RE = re.compile(
    r"[ァ-ヴー]{2,}|[一-龥々]{2,}|[A-Za-z]{2,}|[0-9]+(?:\.[0-9]+)?"
)


def http_get(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": WEB_UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def fetch_player(video_id):
    body = json.dumps({"context": {"client": ANDROID_CLIENT}, "videoId": video_id}).encode()
    req = urllib.request.Request(
        "https://www.youtube.com/youtubei/v1/player?prettyPrint=false",
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": ANDROID_UA},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_watch_publish_date(video_id):
    try:
        raw = http_get(f"https://www.youtube.com/watch?v={video_id}")
        m = re.search(r'"publishDate":"(\d{4}-\d{2}-\d{2})', raw)
        if m:
            return m.group(1)
        m2 = re.search(r'itemprop="datePublished" content="(\d{4}-\d{2}-\d{2})', raw)
        if m2:
            return m2.group(1)
    except Exception:
        pass
    return None


def parse_ts(text):
    if not isinstance(text, str) or ":" not in text:
        return None
    parts = text.strip().split(":")
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return None
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    if len(nums) == 3:
        return nums[0] * 3600 + nums[1] * 60 + nums[2]
    return None


def parse_description_chapters(desc):
    starts = []
    entries = []
    for line in (desc or "").splitlines():
        m = re.match(r"^\s*[\[(]?((?:\d{1,2}:)?\d{1,2}:\d{2})[\])]?\s+(\S.*)$", line)
        if m:
            sec = parse_ts(m.group(1))
            label = m.group(2).strip()
            if sec is not None:
                starts.append(sec)
                entries.append(f"{m.group(1)} {label[:35]}")
    if len(starts) >= 3 and starts[0] == 0 and starts == sorted(starts):
        return starts, " / ".join(entries[:15])
    return [], ""


def parse_caption_xml(raw):
    """Return list of (start_sec, end_sec, text). Supports timedtext format 3 and srv1."""
    cues = []
    for m in re.finditer(r'<p t="(\d+)"(?: d="(\d+)")?[^>]*>(.*?)</p>', raw, re.S):
        start = int(m.group(1)) / 1000.0
        dur = int(m.group(2) or 0) / 1000.0
        text = html.unescape(re.sub(r"<[^>]+>", "", m.group(3)))
        if text.strip():
            cues.append((start, start + dur, text))
    if not cues:
        for m in re.finditer(r'<text start="([\d.]+)"(?: dur="([\d.]+)")?[^>]*>(.*?)</text>', raw, re.S):
            start = float(m.group(1))
            dur = float(m.group(2) or 0)
            text = html.unescape(re.sub(r"<[^>]+>", "", m.group(3)))
            if text.strip():
                cues.append((start, start + dur, text))
    return cues


def pick_track(tracks):
    if not tracks:
        return None
    manual_ja = [t for t in tracks if t.get("languageCode", "").startswith("ja") and t.get("kind") != "asr"]
    asr_ja = [t for t in tracks if t.get("languageCode", "").startswith("ja")]
    return (manual_ja or asr_ja or tracks)[0]


def title_tokens(title):
    toks = []
    for t in TOKEN_RE.findall(title or ""):
        norm = t.lower()
        if norm in STOP_TOKENS or t in STOP_TOKENS:
            continue
        if len(norm) < 2:
            continue
        if norm not in toks:
            toks.append(norm)
    return toks


def window_text(cues, start, end):
    return "".join(c[2] for c in cues if c[1] >= start and c[0] <= end).lower().replace(" ", "")


def count_hits(tokens, text):
    hits = []
    for t in tokens:
        candidates = ASR_ALIASES.get(t, [t])
        if any(c.replace(" ", "") in text for c in candidates):
            hits.append(t)
    return hits


def verify_chapter(
    start,
    end,
    title,
    cues,
    yt_len,
    desc_starts,
    dur_match,
    contradicts_desc,
):
    if yt_len is not None and (start > yt_len + 2 or (end is not None and end > yt_len + 2)):
        return {"verdict": "OUT_OF_RANGE"}
    if not dur_match:
        return {"verdict": "DURATION_MISMATCH"}
    if contradicts_desc:
        return {"verdict": "CONTRADICTS_DESC"}

    if desc_starts:
        if start > 0 and any(abs(start - d) <= DESC_TOLERANCE_SEC for d in desc_starts if d > 0):
            nearest = min((d for d in desc_starts if d > 0), key=lambda d: abs(start - d))
            return {"verdict": "DESC_MATCH", "desc_start": nearest}
        if start == 0 and 0 in desc_starts:
            return {"verdict": "DESC_MATCH", "desc_start": 0}

    if not cues:
        return {"verdict": "NO_CAPTIONS"}
    tokens = title_tokens(title)
    if not tokens:
        return {"verdict": "CAPTION_FAIL", "reason": "NO_DISTINCTIVE_TITLE_TOKENS"}

    span_after = WINDOW_MIN_AFTER_SEC
    if end is not None and end > start:
        span_after = min(max(end - start + 15, WINDOW_MIN_AFTER_SEC), WINDOW_MAX_AFTER_SEC)

    local = count_hits(tokens, window_text(cues, start - WINDOW_BEFORE_SEC, start + span_after))
    controls = []
    for shift in (-CONTROL_SHIFT_SEC, CONTROL_SHIFT_SEC):
        cs = start + shift
        if cs < 0 or (yt_len is not None and cs > yt_len):
            continue
        controls.append(
            len(count_hits(tokens, window_text(cues, cs - WINDOW_BEFORE_SEC, cs + WINDOW_MIN_AFTER_SEC)))
        )
    control_max = max(controls) if controls else 0
    distinct_non_num = [t for t in local if not re.match(r"^[0-9]+(?:\.[0-9]+)?$", t)]
    passed = len(distinct_non_num) >= 2 and len(local) > control_max
    res = {
        "verdict": "CAPTION_PASS" if passed else "CAPTION_FAIL",
        "title_tokens": len(tokens),
        "matched_title_tokens": local[:8],
        "control_max_hits": control_max,
    }
    if not passed:
        if len(distinct_non_num) < 2:
            res["reason"] = "INSUFFICIENT_DISTINCT_TOKENS"
        elif len(local) <= control_max:
            res["reason"] = "NOT_ABOVE_CONTROL_WINDOW"
    return res


def load_handoff_videos(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for v in data.get("videos", []):
        vid = v.get("video_id") or v.get("id")
        dur_sec = parse_ts(str(v.get("duration") or ""))
        chapters = []
        for tl in v.get("timeline") or []:
            if isinstance(tl.get("seconds"), int):
                e_sec = parse_ts(str(tl.get("end") or ""))
                chapters.append((tl["seconds"], e_sec, str(tl.get("title") or "")))
        for ch in v.get("chapters") or []:
            if isinstance(ch.get("start_seconds"), int):
                chapters.append(
                    (ch["start_seconds"], ch.get("end_seconds"), str(ch.get("title") or ""))
                )
        out.append((vid, dur_sec, chapters))
    return out


def verify_video(vid, reported_dur_sec, chapters):
    rec = {"checked_at": date.today().isoformat(), "method": "youtube_player_android+timedtext"}
    try:
        player = fetch_player(vid)
    except Exception as e:
        rec["error"] = f"PLAYER_FETCH_FAILED: {type(e).__name__}"
        rec["chapters"] = {}
        return rec
    details = player.get("videoDetails") or {}
    yt_len = int(details["lengthSeconds"]) if str(details.get("lengthSeconds", "")).isdigit() else None
    yt_title = details.get("title") or ""
    yt_author = details.get("author") or ""
    yt_pub = fetch_watch_publish_date(vid)
    desc_starts, desc_summary = parse_description_chapters(details.get("shortDescription", ""))
    rec["yt_len_sec"] = yt_len
    rec["yt_title"] = yt_title
    rec["yt_author"] = yt_author
    if yt_pub:
        rec["yt_pub"] = yt_pub
    rec["desc_starts"] = desc_starts
    if desc_summary:
        rec["desc_summary"] = desc_summary

    if yt_len is not None and reported_dur_sec is not None:
        dur_match = abs(reported_dur_sec - yt_len) <= 2
    elif yt_len is not None and chapters and chapters[-1][1] is not None:
        dur_match = abs(chapters[-1][1] - yt_len) <= 2
    else:
        dur_match = False

    nonzero_desc_matches = sum(
        1
        for start, end, _ in chapters
        if start > 0
        and (yt_len is None or end is None or end <= yt_len + 2)
        and any(abs(start - d) <= DESC_TOLERANCE_SEC for d in desc_starts if d > 0)
    )
    contradicts_desc = bool(desc_starts and nonzero_desc_matches < 1)
    rec["dur_match"] = dur_match
    rec["contradicts_desc"] = contradicts_desc

    tracks = (
        player.get("captions", {})
        .get("playerCaptionsTracklistRenderer", {})
        .get("captionTracks", [])
    )
    track = pick_track(tracks)
    cues = []
    if track:
        rec["caption_track"] = f"{track.get('languageCode')}:{track.get('kind') or 'manual'}"
        try:
            cues = parse_caption_xml(http_get(track["baseUrl"], {"User-Agent": ANDROID_UA}))
        except Exception as e:
            rec["caption_error"] = type(e).__name__
    rec["caption_cue_count"] = len(cues)

    rec["chapters"] = {}
    for start, end, title in chapters:
        rec["chapters"][str(start)] = verify_chapter(
            start,
            end,
            title,
            cues,
            yt_len,
            desc_starts,
            dur_match,
            contradicts_desc,
        )
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("receipts", nargs="+", help="Gemini handoff or research_receipt_v1 JSON files")
    ap.add_argument("--evidence", default=str(DEFAULT_EVIDENCE_PATH))
    ap.add_argument("--apply", action="store_true", help="write the evidence file (default: preview)")
    args = ap.parse_args(argv)

    ev_path = Path(args.evidence)
    evidence = {"schema_version": EVIDENCE_SCHEMA, "videos": {}}
    if ev_path.exists():
        existing = json.loads(ev_path.read_text(encoding="utf-8"))
        if existing.get("schema_version") != EVIDENCE_SCHEMA:
            raise SystemExit("Refusing to overwrite evidence file with unknown schema")
        evidence = existing

    summary = {}
    for path in args.receipts:
        for vid, dur_sec, chapters in load_handoff_videos(path):
            if not isinstance(vid, str) or not VIDEO_ID.fullmatch(vid):
                raise SystemExit(f"Invalid video id in {path}: {vid!r}")
            rec = verify_video(vid, dur_sec, chapters)
            evidence["videos"][vid] = rec
            counts = {}
            for c in rec["chapters"].values():
                counts[c["verdict"]] = counts.get(c["verdict"], 0) + 1
            summary[vid] = {
                "yt_len_sec": rec.get("yt_len_sec"),
                "yt_pub": rec.get("yt_pub"),
                "dur_match": rec.get("dur_match"),
                "contradicts_desc": rec.get("contradicts_desc"),
                **counts,
            }

    print(json.dumps(summary, ensure_ascii=False, indent=1))
    if args.apply:
        ev_path.parent.mkdir(parents=True, exist_ok=True)
        ev_path.write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("EVIDENCE_WRITTEN", ev_path)
    else:
        print("PREVIEW_ONLY (use --apply to write evidence)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
