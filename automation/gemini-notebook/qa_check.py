#!/usr/bin/env python3
"""AI技術研究室 | 質問回答の確認（ロードマップ T7）を全動画へ広げる道具（読み取りのみ）.

- `plan`  : 研究ノート（research/）1本ごとに、人手なしで「質問3問」と「期待する根拠」を自動生成する。
            質問と期待は研究ノートの題名・章・主張・関連リンク・投稿日だけから作る（字幕全文は使わない＝GitHubにないため）。
- `check` : Notebookの回答テキストを受け取り、次の4点を機械で判定して PASS / PARTIAL / FAIL と理由を返す。
            (a) 字幕原文と研究ノートの両方を根拠に挙げているか（タイトル・ID・`[HH:MM:SS]` 時刻目印のいずれか）
            (b) 時刻リンクまたは動画URLを示しているか（時刻表記と `&t=` の食い違い・台帳にない動画IDも見る）
            (c) 関連動画を述べるとき、関連リンクの関係（COMPLEMENTS など）と矛盾しないか
            (d) 投稿日時・新旧を取り違えていないか
- `--selftest` : 合成した回答（合格例・不合格例）で判定が正しいことを確かめる。ネット・Notebook不要。

このモジュールはファイルを書かない・Notebookにもネットにも触れない（標準出力に出すだけ）。
実機でNotebookに質問を投げて回答を持ってくるのは相棒PC側の作業（NOTEBOOKLM_PY_RUNBOOK.md 手順8）。
判定は「根拠の出し方」の機械検査で、回答の中身の正しさ（意味）は保証しない。CONFIRMED への昇格（AIレビュー）は対象外。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

AUTO_DIR = Path(__file__).resolve().parent
ROOT = AUTO_DIR.parents[1]
if str(AUTO_DIR) not in sys.path:
    sys.path.insert(0, str(AUTO_DIR))

import query_research  # noqa: E402
import related_links  # noqa: E402

PASS, PARTIAL, FAIL, SKIP = "PASS", "PARTIAL", "FAIL", "SKIP"
RELATION_WORDS = {
    "COMPLEMENTS": ("COMPLEMENTS", "補完", "補い合", "補う"),
    "EXTENDS": ("EXTENDS", "発展", "拡張"),
    "UPDATES": ("UPDATES", "更新"),
    "CONTRADICTS": ("CONTRADICTS", "対立", "矛盾"),
}
WINDOW_MARGIN_SEC = 90          # 段落の時刻目印は約60秒ごと。期待する区間の前後にこれだけ余裕を見る
DEFAULT_WINDOW_SEC = 180        # 章の終わりが分からないときの長さ
QUESTIONS_PER_VIDEO = 3

_URL_RE = re.compile(r"https?://(?:www\.)?youtube\.com/watch\?v=([\w-]{11})(?:[&#?][^\s)\]>」』]*?t=(\d+)s?)?|https?://youtu\.be/([\w-]{11})(?:\?t=(\d+)s?)?")
_TIME_RE = re.compile(r"(?<![\d:])(\d{1,3}):([0-5]\d)(?::([0-5]\d))?(?![\d:])")
_DATE_RE = re.compile(r"(?<!\d)(\d{4})[-/年.](\d{1,2})[-/月.](\d{1,2})日?(?!\d)")
_TITLE_PREFIX_RE = re.compile(r"^(?:【[^】]*】\s*)+")
_SENTENCE_SPLIT_RE = re.compile(r"[。\n]+")


# ---------------------------------------------------------------- 資料の読み込み

def _title_head(title: str, n: int = 14) -> str:
    t = _TITLE_PREFIX_RE.sub("", str(title or "")).strip() or str(title or "").strip()
    return re.sub(r"\s+", " ", t)[:n]


def _clip(text: Any, n: int = 40) -> str:
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    return t if len(t) <= n else t[: n - 1] + "…"


def _mmss(sec: int) -> str:
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


def load_videos(root: Path = ROOT) -> Dict[str, Dict[str, Any]]:
    """台帳の各動画について、質問づくり・判定に要るものだけを研究ノートから読む（字幕は読まない）。"""
    root = Path(root)
    registry = json.loads((root / "registry.json").read_text(encoding="utf-8"))
    corpus = related_links.load_corpus(root, registry)
    videos: Dict[str, Dict[str, Any]] = {}
    for rec in registry.get("records", []):
        vid = rec.get("video_id")
        if vid not in corpus:
            continue
        parsed = query_research.parse_research_markdown_file(root / rec["research_path"], root=root, registry_entry=rec)
        chapters = [{"title": c.get("title", ""), "start": c.get("start_seconds"), "end": c.get("end_seconds")}
                    for c in parsed.get("chapters") or []]
        claims = [{"text": c.get("text", ""), "start": _int_or_none(c.get("timestamp_seconds"))} for c in parsed.get("claims") or []]
        videos[vid] = {
            "video_id": vid,
            "title": corpus[vid]["title"],
            "published_at": corpus[vid]["published_at"],
            "chapters": chapters,
            "claims": claims,
            "related": [r for r in corpus[vid]["related_records"]],
        }
    for v in videos.values():   # 題名で動画を見分ける目印は、他の動画の題名に含まれない長さまで伸ばす（先頭が同じ題名があるため）
        v["title_key"] = _unique_title_key(v, videos)
    for v in videos.values():   # 実在する別の動画に向いた記録だけを関連として扱う
        v["related"] = [
            {"target_vid": related_links.target_video_id(r.get("target_id")), "relation": r.get("relation"), "status": r.get("status")}
            for r in v["related"]
            if related_links.target_video_id(r.get("target_id")) in videos and related_links.target_video_id(r.get("target_id")) != v["video_id"]
        ]
    return videos


def _unique_title_key(v: Dict[str, Any], videos: Dict[str, Dict[str, Any]]) -> str:
    full = re.sub(r"\s+", " ", _TITLE_PREFIX_RE.sub("", str(v["title"]))).strip() or str(v["title"])
    others = [str(w["title"]) for k, w in videos.items() if k != v["video_id"]]
    for n in range(14, len(full) + 1):
        if not any(full[:n] in t for t in others):
            return full[:n]
    return full


def _int_or_none(value: Any) -> Optional[int]:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return n if n >= 0 else None


def video_url(vid: str, sec: Optional[int] = None) -> str:
    return f"https://www.youtube.com/watch?v={vid}" + (f"&t={sec}s" if sec is not None else "")


# ---------------------------------------------------------------- 1. plan

def _window(start: Optional[int], end: Optional[int]) -> Optional[List[int]]:
    if start is None:
        return None
    last = end if end is not None and end > start else start + DEFAULT_WINDOW_SEC
    return [max(0, start - WINDOW_MARGIN_SEC), last + WINDOW_MARGIN_SEC]


def _base_expect(v: Dict[str, Any]) -> Dict[str, Any]:
    vid = v["video_id"]
    return {
        "video_id": vid,
        "title_head": v.get("title_key") or _title_head(v["title"]),
        "transcript_id": f"youtube:{vid}:transcript",
        "research_id": f"youtube:{vid}:research",
        "url": video_url(vid),
        "published_at": v["published_at"],
        "time_required": False,
        "time_seconds": None,
        "time_window": None,
        "related": [],
    }


def plan_for_video(v: Dict[str, Any], videos: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """1本につき質問3問：①主張の時刻と元の発言箇所 ②章の時刻 ③関連する別の動画（無ければ投稿日と要点）。"""
    vid, head = v["video_id"], _title_head(v["title"], 30)
    items: List[Dict[str, Any]] = []

    claims = [c for c in v["claims"] if str(c["text"]).strip()]
    claim = next((c for c in claims if c["start"] is not None), claims[0] if claims else None)
    e1 = _base_expect(v)
    e1["time_required"] = True
    if claim:
        e1["time_seconds"] = claim["start"]
        e1["time_window"] = _window(claim["start"], None)
        q1 = f"動画「{head}」の主張『{_clip(claim['text'], 60)}』は、動画のどこで言っていますか？ 時刻のリンクと、元の発言箇所を教えてください。"
        e1["basis"] = f"研究ノートの主張: {_clip(claim['text'], 60)}"
    else:
        q1 = f"動画「{head}」の要点は何ですか？ 動画のどこで言っているか、時刻のリンクつきで教えてください。"
        e1["basis"] = "研究ノートの題名（主張の記載なし）"
    items.append({"id": f"{vid}-Q1", "video_id": vid, "kind": "CLAIM_TIME", "question": q1, "expect": e1})

    chapters = [c for c in v["chapters"] if str(c["title"]).strip()]
    chap = next((c for c in chapters if c["start"] is not None), chapters[0] if chapters else None)
    e2 = _base_expect(v)
    e2["time_required"] = True
    if chap:
        e2["time_seconds"] = chap["start"]
        e2["time_window"] = _window(chap["start"], chap["end"])
        q2 = f"動画「{head}」の『{_clip(chap['title'], 50)}』の話は、動画のどのあたりですか？ 時刻のリンクもつけてください。"
        e2["basis"] = f"研究ノートの章: {_clip(chap['title'], 50)}" + ("" if chap["start"] is not None else "（時刻は未確認＝UNKNOWN）")
    else:
        q2 = f"動画「{head}」のどのあたりで何を話していますか？ 時刻のリンクもつけてください。"
        e2["basis"] = "研究ノートに章の記載なし"
    items.append({"id": f"{vid}-Q2", "video_id": vid, "kind": "CHAPTER_TIME", "question": q2, "expect": e2})

    e3 = _base_expect(v)
    related = [{"target_id": f"youtube:{r['target_vid']}:research", "video_id": r["target_vid"], "relation": r["relation"], "status": r["status"],
                "title_head": videos[r["target_vid"]].get("title_key") or _title_head(videos[r["target_vid"]]["title"]), "published_at": videos[r["target_vid"]]["published_at"]}
               for r in v["related"]]
    if related:
        e3["related"] = related
        e3["basis"] = "研究ノートの related_records: " + "、".join(f"{r['video_id']}({r['relation']}/{r['status']})" for r in related)
        items.append({"id": f"{vid}-Q3", "video_id": vid, "kind": "RELATED", "expect": e3,
                      "question": f"動画「{head}」と関連する別の動画はありますか？ どう関係していて、どちらが新しい（古い）かも教えてください。"})
    else:
        e3["basis"] = "研究ノートの投稿日（関連リンクの記載なし）"
        items.append({"id": f"{vid}-Q3", "video_id": vid, "kind": "POSTED", "expect": e3,
                      "question": f"動画「{head}」はいつ投稿されましたか？ 要点も教えてください。"})
    return items


def plan_for_videos(videos: Dict[str, Dict[str, Any]], video_id: Optional[str] = None) -> Dict[str, Any]:
    vids = [video_id] if video_id else sorted(videos)
    if video_id and video_id not in videos:
        raise KeyError(f"台帳にない動画ID: {video_id}")
    questions = [q for vid in vids for q in plan_for_video(videos[vid], videos)]
    return {
        "status": "QA_PLAN",
        "files_modified": False,
        "note_count": len(vids),
        "question_count": len(questions),
        "by_kind": {k: sum(1 for q in questions if q["kind"] == k) for k in ("CLAIM_TIME", "CHAPTER_TIME", "RELATED", "POSTED")},
        "questions": questions,
    }


def format_plan(plan: Dict[str, Any], videos: Dict[str, Dict[str, Any]]) -> str:
    lines = [
        "【質問回答の確認プラン（自動生成・字幕全文は使っていない）】",
        f"ノート {plan['note_count']}本／質問 {plan['question_count']}問（主張の時刻 {plan['by_kind']['CLAIM_TIME']}・章の時刻 {plan['by_kind']['CHAPTER_TIME']}"
        f"・関連動画 {plan['by_kind']['RELATED']}・投稿日 {plan['by_kind']['POSTED']}）",
        "使い方: 相棒PC側でNotebookに質問を投げ、回答を `qa_check.py check --question-id <ID> --answer <ファイル>` にかける。",
        "",
    ]
    last = None
    for q in plan["questions"]:
        if q["video_id"] != last:
            last = q["video_id"]
            lines.append(f"■ {_clip(videos[last]['title'], 36)} [{last}]  投稿日 {videos[last]['published_at'] or 'UNKNOWN'}")
        e = q["expect"]
        want = ["字幕原文＋研究ノート", "動画URL"]
        if e["time_required"]:
            want.append("時刻リンク" + (f"（{_mmss(e['time_window'][0])}〜{_mmss(e['time_window'][1])}付近）" if e["time_window"] else ""))
        if e["related"]:
            want.append("関連: " + "・".join(f"{r['video_id']} {r['relation']}" for r in e["related"]))
        if q["kind"] == "POSTED":
            want.append(f"投稿日 {e['published_at'] or 'UNKNOWN'}")
        lines.append(f"  {q['id']}  {q['question']}")
        lines.append("      期待: " + " ／ ".join(want) + f"   （基: {e.get('basis', '')}）")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- 2. check

def _urls(text: str) -> List[Tuple[str, Optional[int], int]]:
    out = []
    for m in _URL_RE.finditer(text):
        vid = m.group(1) or m.group(3)
        t = m.group(2) or m.group(4)
        out.append((vid, int(t) if t else None, m.start()))
    return out


def _to_sec(m: "re.Match[str]") -> int:
    a, b, c = int(m.group(1)), int(m.group(2)), m.group(3)
    return a * 3600 + b * 60 + int(c) if c is not None else a * 60 + b


def _mentioned(text: str, v: Dict[str, Any]) -> bool:
    head = v.get("title_key") or _title_head(v["title"], 14)
    return v["video_id"] in text or (len(head) >= 8 and head in text)


def _first_pos(text: str, v: Dict[str, Any]) -> int:
    """text の中で動画 v（ID か題名の目印）が最初に出る位置。無ければ -1。"""
    key = v.get("title_key") or _title_head(v["title"], 14)
    hits = [p for p in (text.find(v["video_id"]), text.find(key) if len(key) >= 8 else -1) if p >= 0]
    return min(hits) if hits else -1


def _transcript_cited(text: str, v: Dict[str, Any], urls: List[Tuple[str, Optional[int], int]]) -> bool:
    vid = v["video_id"]
    if f"youtube:{vid}:transcript" in text or f"AI_VIDEO_TRANSCRIPT_RAW:{vid}" in text:
        return True
    if "【字幕原文】" in text and _mentioned(text, v):
        return True
    if "字幕原文" in text and vid in text:
        return True
    # 字幕の段落先頭の時刻目印 `[HH:MM:SS] <URL>&t=<秒>s` をそのまま引いている
    for u_vid, t, pos in urls:
        if u_vid == vid and t is not None:
            before = text[max(0, pos - 40):pos]
            if re.search(r"(?:\[|▶)?\s*\d{1,3}:[0-5]\d(?::[0-5]\d)?\s*\]?\s*$", before):   # `[HH:MM:SS]`（旧 `▶HH:MM:SS`、記号が落ちた形も）
                return True
    return False


def _research_cited(text: str, v: Dict[str, Any]) -> bool:
    vid = v["video_id"]
    if f"youtube:{vid}:research" in text or f"AI_VIDEO_RESEARCH_NOTE:{vid}" in text:
        return True
    if "【研究ノート】" in text and _mentioned(text, v):
        return True
    if re.search(r"研究ノート|研究カード", text) and _mentioned(text, v):
        return True
    return False


def _result(check: str, level: str, message: str) -> Dict[str, str]:
    return {"check": check, "level": level, "message": message}


def check_sources(text: str, v: Dict[str, Any], urls) -> List[Dict[str, str]]:
    tr, rs = _transcript_cited(text, v, urls), _research_cited(text, v)
    if tr and rs:
        return [_result("a", PASS, "字幕原文と研究ノートの両方を根拠に挙げている")]
    if tr or rs:
        miss = "研究ノート" if tr else "字幕原文"
        return [_result("a", PARTIAL, f"{miss}を根拠に挙げていない（{'字幕原文' if tr else '研究ノート'}だけ）")]
    return [_result("a", FAIL, "字幕原文も研究ノートも根拠に挙げていない（タイトル・ID・[HH:MM:SS] 時刻目印のどれも無い）")]


def check_links(text: str, v: Dict[str, Any], expect: Dict[str, Any], videos: Dict[str, Dict[str, Any]], urls) -> List[Dict[str, str]]:
    res: List[Dict[str, str]] = []
    vid = v["video_id"]
    unknown = sorted({u for u, _, _ in urls if u not in videos})
    if unknown:
        res.append(_result("b", FAIL, "台帳にない動画IDのURLがある: " + ", ".join(unknown)))
    mine = [(t, pos) for u, t, pos in urls if u == vid]
    if not mine:
        res.append(_result("b", FAIL, "この動画のURL（時刻リンクまたは動画URL）が無い"))
        return res
    # 時刻表記と &t= の食い違い（URLの直前40字にある時刻表記と比べる）
    for u, t, pos in urls:
        if t is None or u not in videos:
            continue
        before = text[max(0, pos - 40):pos]
        found = list(_TIME_RE.finditer(before))
        if found and abs(_to_sec(found[-1]) - t) > 1:
            res.append(_result("b", FAIL, f"時刻表記 {found[-1].group(0)} と URL の t={t}s が食い違っている"))
    times = [t for t, _ in mine if t is not None]
    if expect.get("time_required") and not times:
        res.append(_result("b", PARTIAL, "動画URLはあるが時刻リンク（&t=）が無い"))
    elif times and expect.get("time_window"):
        lo, hi = expect["time_window"]
        if not any(lo <= t <= hi for t in times):
            res.append(_result("b", PARTIAL, f"時刻リンク {','.join(_mmss(t) for t in times)} が期待する区間 {_mmss(lo)}〜{_mmss(hi)} から離れている"))
    if not any(r["check"] == "b" for r in res):
        res.append(_result("b", PASS, "時刻リンクを示している" if times else "動画URLを示している"))
    return res


def _lines(text: str) -> List[str]:
    return [s for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]


def _registered_relations(v: Dict[str, Any], w: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = [r for r in v["related"] if r["target_vid"] == w["video_id"]]
    out += [r for r in w["related"] if r["target_vid"] == v["video_id"]]
    return out


def check_related(text: str, v: Dict[str, Any], expect: Dict[str, Any], videos: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
    others = [w for k, w in videos.items() if k != v["video_id"] and _mentioned(text, w)]
    lines = _lines(text)
    # 判定する組：質問の動画 ↔ 回答に出た別の動画（質問の動画は話題なので暗黙）と、回答に出た別の動画どうし（同じ文に両方あるとき）
    pairs = [(v, w, [ln for ln in lines if _mentioned(ln, w)]) for w in others]
    for i, x in enumerate(others):
        for y in others[i + 1:]:
            both = [ln for ln in lines if _mentioned(ln, x) and _mentioned(ln, y)]
            if both:
                pairs.append((x, y, both))
    res: List[Dict[str, str]] = []
    for x, y, pair_lines in pairs:
        registered = _registered_relations(x, y)
        said = {rel for ln in pair_lines for rel, words in RELATION_WORDS.items() if any(w in ln for w in words)}
        asserts_relation = bool(said) or any(re.search(r"関連|関係", ln) for ln in pair_lines)
        label = f"{x['video_id']} ↔ {y['video_id']}"
        if not registered:
            if asserts_relation:
                res.append(_result("c", PARTIAL, f"関連リンクの記載がない組 {label} を関連として述べている"))
            continue
        regs = {r["relation"] for r in registered}
        if said and not (said & regs):
            res.append(_result("c", FAIL, f"{label} の関係が関連リンクと矛盾: 回答 {'/'.join(sorted(said))} ／ 登録 {'/'.join(sorted(regs))}"))
        elif all(r["status"] != "CONFIRMED" for r in registered) and any(re.search(r"確定|CONFIRMED|確実", ln) for ln in pair_lines):
            res.append(_result("c", PARTIAL, f"{label} の関係は CANDIDATE（候補）なのに、確定として述べている"))
    if expect.get("related") and not any(w["video_id"] in {r["video_id"] for r in expect["related"]} for w in others):
        res.append(_result("c", PARTIAL, "関連動画を尋ねる質問なのに、関連リンクにある動画に触れていない"))
    if not res:
        res.append(_result("c", PASS if others else SKIP, "関連動画の述べ方は関連リンクと矛盾しない" if others else "関連動画に触れていないので対象外"))
    return res


_NEWER = ("新しい", "後", "最新", "あと")
_OLDER = ("古い", "前", "先", "以前")


def check_dates(text: str, v: Dict[str, Any], videos: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
    res: List[Dict[str, str]] = []
    judged = 0
    for ln in _lines(text):
        about = [w for w in videos.values() if _mentioned(ln, w)]
        dates = ["-".join((m.group(1), f"{int(m.group(2)):02d}", f"{int(m.group(3)):02d}")) for m in _DATE_RE.finditer(ln)]
        if dates:
            target = about[0] if len(about) == 1 else (v if not about else None)
            if target is not None and target["published_at"]:
                judged += 1
                if target["published_at"][:10] not in dates:
                    res.append(_result("d", FAIL, f"{target['video_id']} の投稿日は {target['published_at']}（回答は {', '.join(dates)}）"))
        if len(about) >= 2 and "より" in ln:
            first, second = sorted(about[:2], key=lambda w: _first_pos(ln, w))
            before = ln.split("より", 1)
            if _first_pos(before[0], first) < 0:
                continue
            after = before[1]
            newer, older = any(x in after for x in _NEWER), any(x in after for x in _OLDER)
            fa, sa = first["published_at"], second["published_at"]
            if (newer != older) and fa and sa and fa[:10] != sa[:10]:
                judged += 1
                first_is_newer = fa[:10] > sa[:10]
                if first_is_newer != newer:
                    res.append(_result("d", FAIL, f"新旧が逆: {first['video_id']}({fa}) は {second['video_id']}({sa}) より{'新しい' if first_is_newer else '古い'}"))
    if not res:
        res.append(_result("d", PASS if judged else SKIP, "投稿日時・新旧は研究ノートと一致" if judged else "投稿日時・新旧に触れていないので対象外"))
    return res


def check_answer(answer: str, item: Dict[str, Any], videos: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """回答1つを、質問項目（plan の1問）の期待に照らして判定する。"""
    expect = item["expect"]
    v = videos[expect["video_id"]]
    text = answer or ""
    urls = _urls(text)
    results = (check_sources(text, v, urls) + check_links(text, v, expect, videos, urls)
               + check_related(text, v, expect, videos) + check_dates(text, v, videos))
    if not text.strip():
        results = [_result("a", FAIL, "回答が空")]
    levels = {r["level"] for r in results}
    verdict = FAIL if FAIL in levels else PARTIAL if PARTIAL in levels else PASS
    per_check = {}
    for c in "abcd":
        ls = [r["level"] for r in results if r["check"] == c]
        per_check[c] = FAIL if FAIL in ls else PARTIAL if PARTIAL in ls else PASS if PASS in ls else SKIP
    return {
        "question_id": item["id"], "video_id": expect["video_id"], "verdict": verdict, "checks": per_check,
        "reasons": [r for r in results if r["level"] in (FAIL, PARTIAL)] or [r for r in results if r["level"] == PASS],
        "files_modified": False,
    }


def format_check(res: Dict[str, Any]) -> str:
    lines = [f"【回答の確認】{res['question_id']} → {res['verdict']}  (a:{res['checks']['a']} b:{res['checks']['b']} c:{res['checks']['c']} d:{res['checks']['d']})"]
    lines += [f"  - [{r['check']}] {r['level']}: {r['message']}" for r in res["reasons"]]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- 3. selftest（合成データ。実データ・ネット・Notebook不要）

def synthetic_videos() -> Dict[str, Dict[str, Any]]:
    a, b, c = "AAAAAAAAAAA", "BBBBBBBBBBB", "CCCCCCCCCCC"
    return {
        a: {"video_id": a, "title": "【研究カード】 OKFの荷札とフロントマター入門", "published_at": "2026-07-25",
            "chapters": [{"title": "荷札（メタデータによる資料識別）", "start": 496, "end": 548}],
            "claims": [{"text": "OKFは資料先頭にYAMLフロントマターを置く", "start": 496}],
            "related": [{"target_vid": b, "relation": "COMPLEMENTS", "status": "CONFIRMED"}, {"target_vid": c, "relation": "UPDATES", "status": "CANDIDATE"}]},
        b: {"video_id": b, "title": "RAG探索設計の基本と検索の流れ", "published_at": "2026-08-20",
            "chapters": [{"title": "検索の流れ", "start": 120, "end": 200}], "claims": [{"text": "検索は段落単位で行う", "start": 130}],
            "related": [{"target_vid": a, "relation": "COMPLEMENTS", "status": "CONFIRMED"}]},
        c: {"video_id": c, "title": "古いOKF解説の記録メモ", "published_at": "2026-06-01",
            "chapters": [], "claims": [], "related": []},
    }


def selftest_cases() -> List[Dict[str, Any]]:
    a, b, c = "AAAAAAAAAAA", "BBBBBBBBBBB", "CCCCCCCCCCC"
    ua = f"https://www.youtube.com/watch?v={a}"
    good = (f"字幕原文（youtube:{a}:transcript）の [00:08:16] {ua}&t=496s では、OKFは資料先頭にYAMLフロントマターを置くと話しています。\n"
            f"研究ノート（youtube:{a}:research）でも荷札の章として同じ箇所が確認済みです。")
    return [
        {"name": "合格：両方の根拠・時刻リンクあり", "question": "Q1", "answer": good, "expect": PASS},
        {"name": "合格：関連動画の関係・新旧が登録どおり",
         "question": "Q3", "expect": PASS,
         "answer": good + f"\n関連動画は {b}（RAG探索設計の基本と検索の流れ）で、COMPLEMENTS（補完）の関係です。{b} は {a} より新しい動画（2026-08-20投稿）です。"},
        {"name": "不合格：字幕原文も研究ノートも根拠に挙げていない", "question": "Q1", "expect": FAIL,
         "answer": f"OKFは資料先頭にYAMLフロントマターを置く話です。{ua}&t=496s"},
        {"name": "一部：研究ノートだけで字幕原文を挙げていない", "question": "Q1", "expect": PARTIAL,
         "answer": f"研究ノート（youtube:{a}:research）によると、OKFは先頭にYAMLを置きます。{ua}&t=496s"},
        {"name": "不合格：動画URLが無い", "question": "Q1", "expect": FAIL,
         "answer": f"字幕原文（youtube:{a}:transcript）と研究ノート（youtube:{a}:research）に8分16秒ごろの話があります。"},
        {"name": "一部：動画URLはあるが時刻リンクが無い", "question": "Q1", "expect": PARTIAL,
         "answer": f"字幕原文（youtube:{a}:transcript）と研究ノート（youtube:{a}:research）に記載。{ua}"},
        {"name": "不合格：時刻表記と &t= が食い違う", "question": "Q1", "expect": FAIL,
         "answer": f"字幕原文（youtube:{a}:transcript）と研究ノート（youtube:{a}:research）。 [00:03:00] {ua}&t=496s"},
        {"name": "不合格：台帳にない動画IDのURL", "question": "Q1", "expect": FAIL,
         "answer": good + "\n参考: https://www.youtube.com/watch?v=ZZZZZZZZZZZ&t=10s"},
        {"name": "一部：時刻リンクが期待する区間から遠い", "question": "Q2", "expect": PARTIAL,
         "answer": f"字幕原文（youtube:{a}:transcript）と研究ノート（youtube:{a}:research）。 [00:50:00] {ua}&t=3000s"},
        {"name": "不合格：関連の関係が登録と矛盾（COMPLEMENTS を対立と述べた）", "question": "Q3", "expect": FAIL,
         "answer": good + f"\n{b}（RAG探索設計の基本と検索の流れ）とは CONTRADICTS（対立）する関係です。"},
        {"name": "一部：CANDIDATE の関係を確定と述べた", "question": "Q3", "expect": PARTIAL,
         "answer": good + f"\n{c}（古いOKF解説の記録メモ）とは UPDATES の関係で、これは確定した関係です。"},
        {"name": "一部：関連リンクにない組を関連として述べた", "question": "Q1", "expect": PARTIAL,
         "answer": good + f"\n{c} と {b} は関連しています。"},
        {"name": "不合格：投稿日時を取り違えた", "question": "Q3", "expect": FAIL,
         "answer": good + f"\n{b}（RAG探索設計の基本と検索の流れ）の投稿日は 2026-05-01 です。"},
        {"name": "不合格：新旧が逆", "question": "Q3", "expect": FAIL,
         "answer": good + f"\n{b} は {a} より古い動画です。"},
        {"name": "一部：関連動画を尋ねる質問なのに触れていない", "question": "Q3", "expect": PARTIAL, "answer": good},
        {"name": "不合格：空の回答", "question": "Q1", "expect": FAIL, "answer": "  \n"},
    ]


def run_selftest() -> Dict[str, Any]:
    videos = synthetic_videos()
    a = "AAAAAAAAAAA"
    plan = {q["id"].split("-")[-1]: q for q in plan_for_video(videos[a], videos)}
    rows = []
    for case in selftest_cases():
        res = check_answer(case["answer"], plan[case["question"]], videos)
        rows.append({"name": case["name"], "expected": case["expect"], "got": res["verdict"], "ok": res["verdict"] == case["expect"],
                     "reasons": [r["message"] for r in res["reasons"]]})
    return {"status": "SELFTEST_OK" if all(r["ok"] for r in rows) else "SELFTEST_FAILED", "case_count": len(rows),
            "failed": [r["name"] for r in rows if not r["ok"]], "cases": rows, "files_modified": False}


# ---------------------------------------------------------------- CLI

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="質問回答の確認の道具（読み取りのみ）：質問プランの自動生成と、回答の根拠の機械判定")
    ap.add_argument("--selftest", action="store_true", help="合成した回答で判定が正しいことを確かめる（ネット・Notebook不要）")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("plan", help="研究ノートごとに質問3問と期待する根拠を作る")
    p.add_argument("--video-id")
    p.add_argument("--summary", action="store_true", help="JSONではなく、人が読める一覧を出す")
    c = sub.add_parser("check", help="Notebookの回答を判定する")
    c.add_argument("--question-id", required=True, help="plan が出した質問ID（例: u3ka_AAb8qE-Q2）")
    c.add_argument("--answer", help="回答テキストのファイル。省略すると標準入力")
    c.add_argument("--json", action="store_true", help="JSONで出す（既定は人が読める形）")
    args = ap.parse_args(argv)

    if args.selftest:
        rep = run_selftest()
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 0 if rep["status"] == "SELFTEST_OK" else 1
    if not args.cmd:
        ap.error("plan / check / --selftest のどれかを指定してください")
    videos = load_videos(ROOT)
    if args.cmd == "plan":
        plan = plan_for_videos(videos, args.video_id)
        print(format_plan(plan, videos), end="") if args.summary else print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    vid = args.question_id.rsplit("-Q", 1)[0]
    if vid not in videos:
        print(f"台帳にない質問ID: {args.question_id}", file=sys.stderr)
        return 2
    item = next((q for q in plan_for_video(videos[vid], videos) if q["id"] == args.question_id), None)
    if item is None:
        print(f"質問IDが見つかりません: {args.question_id}", file=sys.stderr)
        return 2
    answer = Path(args.answer).read_text(encoding="utf-8") if args.answer else sys.stdin.read()
    res = check_answer(answer, item, videos)
    print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else format_check(res), end="")
    return 0 if res["verdict"] == PASS else 1


if __name__ == "__main__":
    sys.exit(main())
