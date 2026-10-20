#!/usr/bin/env python3
"""AI技術研究室 | 関連動画どうしの相互リンク（R6）の検査・候補生成・関連索引OKF（読み取り専用）.

docs/OKF_KNOWLEDGE_ROADMAP.md R6（2026-10-20 相棒了承「その感じで」）:
- GitHub側の正本は研究ノート荷札の related_records（target_id・relation・status・note・evidence）。
- 自動推定は CANDIDATE 止まり。CONFIRMED は人が根拠（時刻・出典URL）を確かめたものだけ。
- Notebook側は登録済みソースを書き換えられないため、逆リンクは「関連索引OKF」1ソースにまとめ、
  新版追加→読み戻し一致→旧版削除で差し替える（このモジュールは計画を出すだけで、書き込み・削除はしない）。

このモジュールはファイルを書き換えない（研究ノート・registry.json は読むだけ）。外部通信もしない。
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

AUTO_DIR = Path(__file__).resolve().parent
ROOT = AUTO_DIR.parents[1]
if str(AUTO_DIR) not in sys.path:
    sys.path.insert(0, str(AUTO_DIR))

import query_research  # noqa: E402

RELATIONS = ("COMPLEMENTS", "EXTENDS", "UPDATES", "CONTRADICTS", "RESOLVES_BACKLOG")
STATUSES = ("CANDIDATE", "CONFIRMED")
INDEX_LOGICAL_ID = "index:related"
INDEX_TITLE = "【関連索引】AI技術研究室 関連動画リンク一覧"
DEFAULT_CANDIDATE_LIMIT = 5

_TIME_RE = re.compile(r"(?<![0-9])\d{1,2}:\d{2}(?::\d{2})?(?![0-9])")
_URL_RE = re.compile(r"https?://\S+")
_TARGET_RE = re.compile(r"^youtube:([\w-]{11})(?::research)?$")
_PROPOSAL_RE = re.compile(r"^proposal:P?(\d{3})$", re.I)
_PUBLISHED_RE = re.compile(r'^\s*published_at:\s*"?([^"\n]*)"?\s*$', re.M)

# 候補生成で拾う語：英数字語・カタカナ語（3字以上）・漢字語（2字以上）
_TERM_RE = re.compile(r"[A-Za-z][A-Za-z0-9+#.-]*[A-Za-z0-9+#]|[ァ-ヴー]{3,}|[一-龥々]{2,}")
_STOP_TERMS = {
    "unknown", "none", "https", "http", "www", "com", "youtube", "watch", "gemini報告区間",
    "研究", "動画", "技術", "解説", "紹介", "確認", "方法", "機能", "場合", "可能", "必要", "説明", "利用",
    "活用", "使用", "今回", "以下", "以上", "独自", "要約", "報告", "未確認", "字幕", "時刻", "資料",
    # どの動画にも出る一般語（主題を表さない）
    "カード", "実践", "実演", "実務", "要素", "判断", "基準", "定義", "選択", "設計", "手順", "業務", "運用", "設定",
    "連携", "構築", "必須", "配置", "時代", "意味", "登録", "接続", "ステップ", "ポイント", "全機能", "徹底解説",
    "中央", "データ", "学習", "概要", "まとめ", "紹介", "最強", "直結", "判断基準",
}
_UPDATE_CUES = ("新機能", "アップデート", "新バージョン", "刷新", "大幅更新")
# 区分ごとの重み（題名・章名・タグは主題を表すので重く、要約・主張は軽く）
_SECTION_WEIGHT = {"題名": 2.0, "章": 2.0, "タグ": 2.0, "主張": 1.0, "要約": 1.0}
_GENERIC_TAGS = {"AI技術研究室", "動画研究"}


def _clip(text: str, n: int = 40) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text if len(text) <= n else text[: n - 1] + "…"


def _known(value: Any) -> Optional[str]:
    v = str(value or "").strip()
    return v if v and v.upper() != "UNKNOWN" else None


def load_corpus(root: Path = ROOT, registry: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, Any]]:
    """台帳の各動画について研究ノートを読み、候補生成・検査に使う形にまとめる（読み取りのみ）。"""
    root = Path(root)
    if registry is None:
        reg_path = root / "registry.json"
        registry = json.loads(reg_path.read_text(encoding="utf-8")) if reg_path.exists() else {}
    corpus: Dict[str, Dict[str, Any]] = {}
    for rec in registry.get("records", []):
        vid = rec.get("video_id")
        path = root / str(rec.get("research_path") or "")
        if not vid or not path.is_file():
            continue
        parsed = query_research.parse_research_markdown_file(path, root=root, registry_entry=rec)
        raw = path.read_text(encoding="utf-8", errors="replace")
        fm = raw.split("---", 2)[1] if raw.startswith("---") and raw.count("---") >= 2 else ""
        m = _PUBLISHED_RE.search(fm)
        published = _known(m.group(1)) if m else None
        published = published or _known(parsed.get("publication_date"))
        dm = re.match(r"\d{4}-\d{2}-\d{2}", published or "")  # 「2026-08-19 (YouTube一次確認一致)」→ 日付だけ
        published = dm.group(0) if dm else published
        pieces: List[Tuple[str, str]] = [("題名", parsed.get("title") or "")]
        pieces += [("タグ", t) for t in parsed.get("tags") or [] if t not in _GENERIC_TAGS]
        pieces += [("章", c.get("title", "")) for c in parsed.get("chapters") or []]
        for c in parsed.get("chapters") or []:
            pieces += [("タグ", t) for t in c.get("key_topics") or []]
        pieces += [("主張", c.get("text", "")) for c in parsed.get("claims") or []]
        pieces.append(("要約", parsed.get("summary_ja") or ""))
        corpus[vid] = {
            "video_id": vid,
            "title": parsed.get("title") or vid,
            "research_path": str(rec.get("research_path")),
            "published_at": published,
            "related_records": parsed.get("related_records") or [],
            "pieces": [(s, t) for s, t in pieces if str(t).strip()],
        }
    return corpus


def proposal_exists(target_id: str, root: Path = ROOT) -> bool:
    m = _PROPOSAL_RE.match(target_id)
    return bool(m and list((Path(root) / "proposals").glob(f"{m.group(1)}-*.md")))


def target_video_id(target_id: str) -> Optional[str]:
    m = _TARGET_RE.match(str(target_id or "").strip())
    return m.group(1) if m else None


# ---------------------------------------------------------------- 1. 検査

def validate_related_records(corpus: Dict[str, Dict[str, Any]], root: Path = ROOT) -> Dict[str, Any]:
    """研究ノート荷札の related_records を検査する。ファイルは変えない。

    エラー: 宛先が無い・自己リンク・関係ラベル不正・status不正・note無し・evidence無し・
    CONFIRMED なのに evidence に時刻も出典URLも無い。警告: 逆リンクが無い。
    """
    items = []
    for vid, doc in corpus.items():
        for rec in doc["related_records"]:
            tid = str(rec.get("target_id") or "").strip()
            tvid = target_video_id(tid)
            rel, status = str(rec.get("relation") or ""), str(rec.get("status") or "")
            note, ev = str(rec.get("note") or "").strip(), str(rec.get("evidence") or "").strip()
            errors = []
            if tvid == vid:
                errors.append("SELF_LINK")
            elif tvid is None and not proposal_exists(tid, root):
                errors.append("TARGET_NOT_FOUND")
            elif tvid is not None and tvid not in corpus:
                errors.append("TARGET_NOT_FOUND")
            if rel not in RELATIONS:
                errors.append("BAD_RELATION")
            if status not in STATUSES:
                errors.append("BAD_STATUS")
            if not note or note.upper() == "UNKNOWN":
                errors.append("NOTE_MISSING")
            if not ev or ev.upper() == "UNKNOWN":
                errors.append("EVIDENCE_MISSING")
            elif status == "CONFIRMED" and not (_TIME_RE.search(ev) or _URL_RE.search(ev)):
                errors.append("CONFIRMED_WITHOUT_TIME_OR_URL")
            backlink = None
            if tvid and tvid in corpus and tvid != vid:
                backlink = any(target_video_id(r.get("target_id")) == vid for r in corpus[tvid]["related_records"])
            items.append({
                "source": f"youtube:{vid}:research", "target_id": tid, "relation": rel, "status": status,
                "errors": errors, "backlink_present": backlink,
            })
    error_items = [i for i in items if i["errors"]]
    counts = Counter(e for i in items for e in i["errors"])
    return {
        "status": "OK" if not error_items else "ATTENTION",
        "record_count": len(items),
        "notes_with_related_records": sum(1 for d in corpus.values() if d["related_records"]),
        "note_count": len(corpus),
        "error_record_count": len(error_items),
        "error_counts": dict(sorted(counts.items())),
        "confirmed_count": sum(1 for i in items if i["status"] == "CONFIRMED"),
        "confirmed_valid_pairs": sorted({
            tuple(sorted((i["source"], i["target_id"]))) for i in items
            if i["status"] == "CONFIRMED" and not i["errors"] and i["backlink_present"]
        }),
        "missing_backlink_count": sum(1 for i in items if i["backlink_present"] is False),
        "items": items,
    }


# ---------------------------------------------------------------- 2. 候補生成

def _terms(text: str) -> List[str]:
    out = []
    for t in _TERM_RE.findall(str(text or "")):
        t = t.lower() if t.isascii() else t
        if t in _STOP_TERMS or (t.isascii() and len(t) < 3 and t not in ("ai",)):
            continue
        out.append(t)
    return out


def _term_index(doc: Dict[str, Any]) -> Dict[str, Tuple[float, str, str]]:
    """語 → (最大の区分重み, 区分名, 最初に出た箇所)。"""
    idx: Dict[str, Tuple[float, str, str]] = {}
    for section, text in doc["pieces"]:
        w = _SECTION_WEIGHT.get(section, 1.0)
        for t in _terms(text):
            if t not in idx or w > idx[t][0]:
                idx[t] = (w, section, _clip(text))
    return idx


def _doc_freq(indexes: Dict[str, Dict[str, Any]]) -> Counter:
    df: Counter = Counter()
    for idx in indexes.values():
        df.update(idx.keys())
    return df


def infer_candidates(
    source: Dict[str, Any],
    corpus: Dict[str, Dict[str, Any]],
    limit: int = DEFAULT_CANDIDATE_LIMIT,
    min_shared: int = 3,
    max_df_ratio: float = 0.35,
    min_score: float = 6.0,
) -> List[Dict[str, Any]]:
    """台帳全件を対象に、章・タグ・主張・要約の語の重なりから CANDIDATE を出す（CONFIRMED にはしない）。

    多くのノートに出る語（max_df_ratio 超）は主題を表さないので使わない。自己リンクは除外し、上位 limit 件まで。
    UPDATES は投稿日時が新しい側から古い側へ、更新を示す語（新機能・最新など）が新しい側にあるときだけ。
    """
    others = {vid: d for vid, d in corpus.items() if vid != source["video_id"]}
    indexes = {vid: _term_index(d) for vid, d in others.items()}
    src_idx = _term_index(source)
    df = _doc_freq(indexes)
    for t in src_idx:
        df[t] += 1
    n_docs = len(indexes) + 1
    max_df = max(2, int(max_df_ratio * n_docs))
    # 更新を示す語は主題を表す題名・章名・タグにあるときだけ見る（要約・主張の「最新」などは拾わない）
    src_head = " ".join(t for s, t in source["pieces"] if s in ("題名", "章", "タグ"))
    scored = []
    for vid, idx in indexes.items():
        shared = [t for t in src_idx if t in idx and df[t] <= max_df]
        if len(shared) < min_shared:
            continue
        weights = {t: math.log(n_docs / df[t]) * max(src_idx[t][0], idx[t][0]) for t in shared}
        score = sum(weights.values())
        if score < min_score:
            continue
        scored.append((score, vid, sorted(shared, key=lambda t: (-weights[t], t))))
    scored.sort(key=lambda x: (-x[0], x[1]))
    out = []
    for score, vid, shared in scored[:limit]:
        tgt = others[vid]
        top = shared[0]
        s_pub, t_pub = source.get("published_at"), tgt.get("published_at")
        relation = "COMPLEMENTS"
        if s_pub and t_pub and s_pub > t_pub and any(c in src_head for c in _UPDATE_CUES):
            relation = "UPDATES"
        terms = "・".join(shared[:3])
        out.append({
            "target_id": f"youtube:{vid}:research",
            "relation": relation,
            "status": "CANDIDATE",
            "note": f"自動推定の候補（未確認）：共通の主題「{terms}」",
            "evidence": (
                f"共通語: {', '.join(shared[:5])} ／ 本ノート: {src_idx[top][1]}「{src_idx[top][2]}」"
                f" ／ 相手: {indexes[vid][top][1]}「{indexes[vid][top][2]}」"
                + (f" ／ 投稿日時: {s_pub} → {t_pub}" if relation == "UPDATES" else "")
            )[:600],
            "score": round(score, 2),
        })
    return out


def source_from_fields(
    video_id: str,
    title: str,
    summary_ja: str = "",
    detailed_findings_ja: str = "",
    chapters: Optional[List[Dict[str, Any]]] = None,
    claims: Optional[List[Dict[str, Any]]] = None,
    published_at: Optional[str] = None,
) -> Dict[str, Any]:
    """まだ研究ノートになっていない動画（パイプライン途中）の内容を候補生成用の形にする。"""
    pieces: List[Tuple[str, str]] = [("題名", title or "")]
    for c in chapters or []:
        pieces.append(("章", c.get("title", "")))
        pieces += [("タグ", t) for t in c.get("key_topics") or []]
    pieces += [("主張", c.get("text", "")) for c in claims or []]
    pieces += [("要約", summary_ja or ""), ("要約", detailed_findings_ja or "")]
    return {"video_id": video_id, "title": title, "published_at": _known(published_at),
            "related_records": [], "pieces": [(s, t) for s, t in pieces if str(t).strip()]}


def candidates_for_corpus(corpus: Dict[str, Dict[str, Any]], limit: int = DEFAULT_CANDIDATE_LIMIT) -> Dict[str, Any]:
    """台帳の全動画について候補を出す（dry-run。研究ノートは書き換えない）。"""
    rows = []
    for vid in sorted(corpus):
        existing = {target_video_id(r.get("target_id")): r for r in corpus[vid]["related_records"]}
        cands = infer_candidates(corpus[vid], corpus, limit=limit)
        rows.append({
            "video_id": vid,
            "title": corpus[vid]["title"],
            "published_at": corpus[vid]["published_at"] or "UNKNOWN",
            "candidates": [
                dict(c, already_in_note=target_video_id(c["target_id"]) in existing,
                     note_status=(existing.get(target_video_id(c["target_id"])) or {}).get("status"),
                     **({"relation": existing[target_video_id(c["target_id"])].get("relation") or c["relation"]}
                        if target_video_id(c["target_id"]) in existing else {}))
                for c in cands
            ],
        })
    return {
        "status": "DRY_RUN_CANDIDATES",
        "note_count": len(corpus),
        "candidate_count": sum(len(r["candidates"]) for r in rows),
        "new_candidate_count": sum(1 for r in rows for c in r["candidates"] if not c["already_in_note"]),
        "files_modified": False,
        "videos": rows,
    }


# ---------------------------------------------------------------- 3. 関連索引OKF

def build_related_index_okf(
    corpus: Dict[str, Dict[str, Any]],
    root: Path = ROOT,
    generated_at: Optional[str] = None,
    include_auto_candidates: bool = False,
    limit: int = DEFAULT_CANDIDATE_LIMIT,
) -> Dict[str, Any]:
    """関連索引OKF（1ソース）の本文を作る。各動画の published_at・関連先・関連元（逆リンク）・関係・status・理由を並べる。

    研究ノートに登録済みで検査を通った関係だけを載せる。include_auto_candidates=True なら、自動候補を
    「自動推定・未登録」と明記して足す。
    """
    generated_at = generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report = validate_related_records(corpus, root)
    links = []
    for item, (vid, rec) in zip(report["items"], [(v, r) for v, d in corpus.items() for r in d["related_records"]]):
        if item["errors"]:
            continue
        links.append({"source": vid, "target_id": item["target_id"], "relation": item["relation"],
                      "status": item["status"], "note": str(rec.get("note") or ""), "auto": False})
    if include_auto_candidates:
        have = {(l["source"], target_video_id(l["target_id"])) for l in links}
        for vid, doc in corpus.items():
            for c in infer_candidates(doc, corpus, limit=limit):
                if (vid, target_video_id(c["target_id"])) not in have:
                    links.append({"source": vid, "target_id": c["target_id"], "relation": c["relation"],
                                  "status": "CANDIDATE", "note": "（自動推定・未登録）" + c["note"], "auto": True})
    outgoing: Dict[str, List[Dict[str, Any]]] = {}
    incoming: Dict[str, List[Dict[str, Any]]] = {}
    for l in links:
        outgoing.setdefault(l["source"], []).append(l)
        tvid = target_video_id(l["target_id"])
        if tvid:
            incoming.setdefault(tvid, []).append(l)

    order = sorted(corpus, key=lambda v: (corpus[v]["published_at"] is None, "" if corpus[v]["published_at"] is None
                                          else "".join(chr(0x10FFFF - ord(ch)) for ch in corpus[v]["published_at"]), v))
    n_conf = sum(1 for l in links if l["status"] == "CONFIRMED")
    lines = [
        "---",
        'okf_version: "0.2"',
        'type: "RELATED_INDEX"',
        f'title: "{INDEX_TITLE}"',
        f'logical_id: "{INDEX_LOGICAL_ID}"',
        f'generated_at: "{generated_at}"',
        f"video_count: {len(corpus)}",
        f"link_count: {len(links)}",
        f"confirmed_link_count: {n_conf}",
        f"candidate_link_count: {len(links) - n_conf}",
        f"excluded_invalid_count: {report['error_record_count']}",
        'tags:',
        '  - "AI技術研究室"',
        '  - "関連索引"',
        "---",
        "",
        f"# {INDEX_TITLE}",
        "",
        f"ID: {INDEX_LOGICAL_ID}",
        "",
        "- この索引は各研究ノートの `related_records`（GitHubの正本）から作った一覧です。研究ノートの本文は書き換えていません。",
        "- `CONFIRMED` は根拠（時刻・出典）を確認済みの関係、`CANDIDATE` は候補（未確認）です。回答では CANDIDATE を確定事項として扱わないでください。",
        "- 投稿日時の新しい動画が古い主張を改める関係は `UPDATES` です。新しい方を優先し、古い方は当時の情報として区別してください。",
        "",
    ]
    for vid in order:
        d = corpus[vid]
        lines += [f"## {d['title']} [{vid}]", "", f"- 研究ノート: youtube:{vid}:research",
                  f"- 投稿日時: {d['published_at'] or 'UNKNOWN'}"]
        outs, ins = outgoing.get(vid, []), incoming.get(vid, [])
        lines.append("- 関連先:" if outs else "- 関連先: なし")
        lines += [f"  - → {l['target_id']}（{l['relation']}・{l['status']}）{l['note']}" for l in outs]
        lines.append("- 関連元（逆リンク）:" if ins else "- 関連元（逆リンク）: なし")
        lines += [f"  - ← youtube:{l['source']}:research（{l['relation']}・{l['status']}）{l['note']}" for l in ins]
        lines.append("")
    return {
        "title": INDEX_TITLE,
        "logical_id": INDEX_LOGICAL_ID,
        "generated_at": generated_at,
        "video_count": len(corpus),
        "link_count": len(links),
        "confirmed_link_count": n_conf,
        "excluded_invalid_count": report["error_record_count"],
        "text": "\n".join(lines),
    }


def plan_related_index_replacement(client: Any, index: Dict[str, Any]) -> Dict[str, Any]:
    """Notebookの関連索引OKFを差し替える計画（新版追加→読み戻し一致→旧版削除）。書き込み・削除はしない。"""
    plan: Dict[str, Any] = {
        "status": "DRY_RUN_REPLACEMENT_PLAN",
        "title": index["title"],
        "logical_id": index["logical_id"],
        "writes_executed": False,
        "deletion_executed": False,
    }
    old_ids: List[str] = []
    if client is None:
        plan["notes"] = ["Notebook未接続のため、既存の関連索引の有無は未確認（UNKNOWN）。"]
    elif not client.auth_check_passive():
        return {**plan, "status": "AUTH_EXPIRED", "steps": []}
    else:
        old_ids = [str(s.get("id")) for s in client.list_sources()
                   if str(s.get("title", "")).startswith("【関連索引】") or INDEX_LOGICAL_ID in str(s.get("title", ""))]
    plan["existing_index_source_ids"] = old_ids if client is not None else "UNKNOWN"
    plan["steps"] = [
        {"step": 1, "action": "ADD_NEW_VERSION", "title": index["title"], "chars": len(index["text"])},
        {"step": 2, "action": "READBACK_MATCH", "detail": "新版の本文を読み戻し、正規化一致を確かめる"},
        {"step": 3, "action": "DELETE_OLD_VERSION_AFTER_READBACK", "source_ids": old_ids,
         "detail": "手順2で一致したときだけ。削除は相棒の承認後に相棒PCの作業役が行う"},
    ]
    return plan


# ---------------------------------------------------------------- CLI

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="関連動画リンク（R6）の検査・候補・関連索引（読み取り専用・dry-run）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate", help="研究ノート荷札の related_records を検査する")
    c = sub.add_parser("candidates", help="台帳全件について関連候補（CANDIDATE）を出す")
    c.add_argument("--video-id")
    c.add_argument("--limit", type=int, default=DEFAULT_CANDIDATE_LIMIT)
    i = sub.add_parser("index", help="関連索引OKFを組み立て、差し替え計画を出す")
    i.add_argument("--with-candidates", action="store_true", help="自動候補も「自動推定・未登録」として載せる")
    i.add_argument("--notebook-id", help="指定すると既存の関連索引ソースを一覧で探す（読み取りのみ）")
    i.add_argument("--print-text", action="store_true", help="索引本文も出力する")
    args = ap.parse_args(argv)

    corpus = load_corpus(ROOT)
    if args.cmd == "validate":
        rep = validate_related_records(corpus, ROOT)
    elif args.cmd == "candidates":
        rep = candidates_for_corpus(corpus, limit=args.limit)
        if args.video_id:
            rep["videos"] = [v for v in rep["videos"] if v["video_id"] == args.video_id]
    else:
        idx = build_related_index_okf(corpus, ROOT, include_auto_candidates=args.with_candidates)
        client = None
        if args.notebook_id:
            from notebooklm_py_ingest import NotebookLmCliClient
            client = NotebookLmCliClient(args.notebook_id)
        rep = {k: v for k, v in idx.items() if k != "text"}
        rep["replacement_plan"] = plan_related_index_replacement(client, idx)
        if args.print_text:
            rep["text"] = idx["text"]
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
