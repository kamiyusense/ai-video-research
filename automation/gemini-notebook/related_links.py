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
# --- T14: 汎用語の除外（共通語がこれだけの候補を出さないため）。理由別に分けて残す。
# 汎用語は「どの動画の解説でも使う語」で、主題を表さない。ここに入れた語は語の抽出の段階で捨てる。
_GENERIC_TERMS = {
    # 機器・画面・操作まわりの一般語（Mac mini は設置場所の話で、主題ではない）
    "mac", "mini", "computer", "use", "model", "システム", "操作", "用意", "画面", "ブラウザ", "スマホ", "アプリ", "ツール",
    "ファイル", "コード", "ルール", "タスク", "セッション", "アカウント", "プラン", "チャット", "フォーマット", "インポート",
    "テクニック", "サービス", "ソース", "ドキュメント", "ローカル", "フロー", "ユーザー", "コスト", "コンテキスト", "line",
    "max", "web", "ai", "llm",
    # 動作・性質を表す一般語（「自動」「生成」「抽出」はどの動画にも出る）
    "自動", "自動化", "自動生成", "生成", "抽出", "処理", "評価", "比較", "調査", "管理", "蓄積", "投入", "投入時", "導入", "作成",
    "公開", "消費", "拡張", "提唱", "提示", "注意", "調整", "案内", "即座", "全文", "共通", "質問", "問題", "重要", "重要性",
    "結論", "不要", "新規", "知識", "時間", "制限", "限界", "複数", "人間", "日常", "個人", "主要", "文章", "成果物", "完全",
    "進化", "前提", "推論", "思考", "発想", "分解", "ゴール", "合致", "視聴者", "自作", "土台", "一生", "天才", "右腕",
    "完全解説", "録音", "内部", "完全一致", "仕様", "一致", "公式", "リスク", "保管", "参照", "アップデート", "並列", "画像",
    "使用量", "社内", "メイン", "サブ", "個人", "実践例", "セットアップ", "エフォート", "フォーマット", "テンプレート",
    "検証", "正確", "統合", "出力", "仕組", "アーキテクチャ", "ループ", "ソースコード", "レポート", "契約", "利用枠",
    # 候補の一覧を目で見て拾った一般語（どの解説でも使われ、共通していても関連の根拠にならない）
    "ガイド", "エンジニア", "リファレンス", "ノウハウ", "実演解説", "網羅", "言及", "理解", "ナレッジ", "公式仕様", "完全自動化",
    "外部", "分析", "厳密", "役割", "課題", "推奨", "追加", "最大", "最大化", "実証", "開発", "徹底", "権限", "上限", "指示", "対策", "登場",
    "ワークフロー", "エージェント", "トークン", "モデル", "費用", "更新", "仕様変更", "リアルタイム", "レート", "長大", "実装",
    # 動画の最後の宣伝・案内に出る定型語（本編の主題ではない）
    "コミュニティ", "自動送信", "概要欄", "チャンネル登録", "高評価", "プレゼント",
    # 動画の型・語り口（「公式照合報告」など研究ノートの定型文も含む）
    "公式照合報告", "一次", "url", "未添付", "要独立確認", "制約", "注意点", "応用", "今後", "未確認事項", "提示", "完全一致",
}
# 大手の名前は広すぎるので、共通していても「固有語」には数えない（重みも下げる）。
_BROAD_BRANDS = {"claude", "gemini", "google", "openai", "chatgpt", "anthropic", "notebook", "code", "api", "pro", "microsoft", "apple", "github"}
_BROAD_BRAND_WEIGHT = 0.4
_ASCII_NAME_WEIGHT = 1.5    # 製品名・技術名（agents.md, playwright, obsidian など）は日本語の一般名詞より固有性が高い
_HEADING_SECTIONS = {"題名", "章", "タグ"}   # 主題を表す見出しの区分
_CLAIM_SECTIONS = {"主張"}
MIN_DISTINCTIVE_TERMS = 2
# 固有語：製品名・技術名（英数字で、台帳の7本以下にしか出ない語）か、3字以上で台帳の3本以下にしか出ない日本語の語。
# 多くの動画に出る日本語の一般名詞は、汎用語リストに無くても固有語には数えない。
_STRONG_ASCII_MAX_DF = 7
_STRONG_ANY_MAX_DF = 3

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
        if t in _STOP_TERMS or t in _GENERIC_TERMS or (t.isascii() and len(t) < 3):
            continue
        out.append(t)
    return out


def _term_index(doc: Dict[str, Any]) -> Dict[str, Tuple[float, str, str, Dict[str, str]]]:
    """語 → (最大の区分重み, その区分名, その箇所, {出てきた区分: 最初の箇所})。"""
    idx: Dict[str, Tuple[float, str, str, Dict[str, str]]] = {}
    for section, text in doc["pieces"]:
        w = _SECTION_WEIGHT.get(section, 1.0)
        for t in _terms(text):
            if t not in idx:
                idx[t] = (w, section, _clip(text), {section: _clip(text)})
                continue
            best_w, best_sec, best_text, places = idx[t]
            places.setdefault(section, _clip(text))
            if w > best_w:
                idx[t] = (w, section, _clip(text), places)
    return idx


def _doc_freq(indexes: Dict[str, Dict[str, Any]]) -> Counter:
    df: Counter = Counter()
    for idx in indexes.values():
        df.update(idx.keys())
    return df


def _term_weight(term: str) -> float:
    """語の種類による重み：大手の名前は下げ、製品名・技術名（英数字の固有語）は上げる。"""
    if term in _BROAD_BRANDS:
        return _BROAD_BRAND_WEIGHT
    return _ASCII_NAME_WEIGHT if term.isascii() else 1.0


def _is_strong(term: str, doc_freq: int) -> bool:
    """固有語か（製品名・技術名、または台帳でごく少数のノートにしか出ない語）。"""
    if term in _BROAD_BRANDS:
        return False
    if term.isascii():
        return doc_freq <= _STRONG_ASCII_MAX_DF
    # 日本語は短い一般名詞（検索・課題など2字）が多いので、3字以上で、かつごく少数のノートにしか出ない語だけ
    return len(term) >= 3 and doc_freq <= _STRONG_ANY_MAX_DF


def _corresponding_places(src_places: Dict[str, str], tgt_places: Dict[str, str]) -> Optional[Tuple[str, str, str, str]]:
    """両ノートの該当箇所が対応しているか。見出し同士（題名・章・タグ）か、主張同士のとき (本区分, 本箇所, 相手区分, 相手箇所)。"""
    for group in (_HEADING_SECTIONS, _CLAIM_SECTIONS):
        for sec_order in ("章", "題名", "タグ", "主張"):
            if sec_order in group and sec_order in src_places:
                other = next((o for o in ("章", "題名", "タグ", "主張") if o in group and o in tgt_places), None)
                if other:
                    return sec_order, src_places[sec_order], other, tgt_places[other]
    return None


def evaluate_pair(
    src_idx: Dict[str, Any], tgt_idx: Dict[str, Any], df: Counter, n_docs: int,
    min_shared: int = 3, max_df_ratio: float = 0.35, min_score: float = 6.0,
) -> Dict[str, Any]:
    """1組の関連度を評価する。通らない理由を reason に入れる（通れば reason は None）。

    通る条件：共通語が min_shared 語以上／そのうち固有語（_is_strong）が2語以上／
    両ノートの該当箇所が対応している（見出し同士か主張同士）／重み付きスコアが min_score 以上。
    """
    max_df = max(2, int(max_df_ratio * n_docs))
    shared = [t for t in src_idx if t in tgt_idx and df[t] <= max_df]
    if len(shared) < min_shared:
        return {"reason": "TOO_FEW_SHARED_TERMS", "shared": shared}
    distinctive = [t for t in shared if _is_strong(t, df[t])]
    if len(distinctive) < MIN_DISTINCTIVE_TERMS:
        return {"reason": "TOO_FEW_DISTINCTIVE_TERMS", "shared": shared}
    weights = {t: math.log(n_docs / df[t]) * max(src_idx[t][0], tgt_idx[t][0]) * _term_weight(t) for t in shared}
    ranked = sorted(shared, key=lambda t: (-weights[t], t))
    anchor = None
    for t in ranked:
        if t not in distinctive:
            continue
        places = _corresponding_places(src_idx[t][3], tgt_idx[t][3])
        if places:
            anchor = (t, places)
            break
    if anchor is None:
        return {"reason": "NO_SECTION_CORRESPONDENCE", "shared": shared}
    score = sum(weights.values())
    if score < min_score:
        return {"reason": "LOW_SCORE", "shared": shared, "score": score}
    # 表示は固有語を先に並べる
    ordered = [t for t in ranked if t in distinctive] + [t for t in ranked if t not in distinctive]
    return {"reason": None, "shared": ordered, "score": score, "anchor": anchor}


def infer_candidates(
    source: Dict[str, Any],
    corpus: Dict[str, Dict[str, Any]],
    limit: int = DEFAULT_CANDIDATE_LIMIT,
    min_shared: int = 3,
    max_df_ratio: float = 0.35,
    min_score: float = 6.0,
) -> List[Dict[str, Any]]:
    """台帳全件を対象に、章・タグ・主張・要約の語の重なりから CANDIDATE を出す（CONFIRMED にはしない）。

    多くのノートに出る語（max_df_ratio 超）と汎用語は主題を表さないので使わない。固有語が2語以上共通し、
    両ノートの該当箇所が対応している（見出し同士か主張同士）ときだけ出す（evaluate_pair）。自己リンクは除外し、上位 limit 件まで。
    UPDATES は投稿日時が新しい側から古い側へ、更新を示す語（新機能・最新など）が新しい側にあるときだけ。
    """
    others = {vid: d for vid, d in corpus.items() if vid != source["video_id"]}
    indexes = {vid: _term_index(d) for vid, d in others.items()}
    src_idx = _term_index(source)
    df = _doc_freq(indexes)
    for t in src_idx:
        df[t] += 1
    n_docs = len(indexes) + 1
    # 更新を示す語は主題を表す題名・章名・タグにあるときだけ見る（要約・主張の「最新」などは拾わない）
    src_head = " ".join(t for s, t in source["pieces"] if s in ("題名", "章", "タグ"))
    scored = []
    for vid, idx in indexes.items():
        ev = evaluate_pair(src_idx, idx, df, n_docs, min_shared, max_df_ratio, min_score)
        if ev["reason"]:
            continue
        scored.append((ev["score"], vid, ev))
    scored.sort(key=lambda x: (-x[0], x[1]))
    out = []
    for score, vid, ev in scored[:limit]:
        tgt = others[vid]
        shared = ev["shared"]
        s_sec, s_text, t_sec, t_text = ev["anchor"][1]
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
                f"共通語: {', '.join(shared[:5])} ／ 本ノート: {s_sec}「{s_text}」"
                f" ／ 相手: {t_sec}「{t_text}」"
                + (f" ／ 投稿日時: {s_pub} → {t_pub}" if relation == "UPDATES" else "")
            )[:600],
            "score": round(score, 2),
        })
    return out


def candidate_filter_stats(corpus: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """全ての向きつきの組（A→B）を評価して、通った数と通らなかった理由の内訳を数える（件数の前後比較用）。"""
    indexes = {vid: _term_index(d) for vid, d in corpus.items()}
    counts: Counter = Counter()
    for vid, src_idx in indexes.items():
        others = {v: i for v, i in indexes.items() if v != vid}
        df = _doc_freq(others)
        for t in src_idx:
            df[t] += 1
        for oidx in others.values():
            counts[evaluate_pair(src_idx, oidx, df, len(others) + 1)["reason"] or "PASS"] += 1
    return {"pairs_evaluated": sum(counts.values()), "pass": counts.get("PASS", 0),
            "rejected": {k: v for k, v in sorted(counts.items()) if k != "PASS"}}


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


def format_candidate_summary(rep: Dict[str, Any], corpus: Dict[str, Dict[str, Any]], top: int = 20) -> str:
    """候補を、スコアの高い順に1組1行ずつ人が読める形にする（向きの違う同じ組は高い方だけ）。人の確認前の推定。"""
    stats = candidate_filter_stats(corpus)
    best: Dict[frozenset, Tuple[float, str, Dict[str, Any]]] = {}
    for v in rep["videos"]:
        for c in v["candidates"]:
            key = frozenset((v["video_id"], target_video_id(c["target_id"])))
            if key not in best or c["score"] > best[key][0]:
                best[key] = (c["score"], v["video_id"], c)
    ranked = sorted(best.values(), key=lambda x: (-x[0], x[1]))
    lines = [
        "【関連動画の候補（自動推定・未確認）】",
        f"候補 {rep['candidate_count']}件（ノート未登録 {rep['new_candidate_count']}件、1本あたり上限{DEFAULT_CANDIDATE_LIMIT}件）／向きを無視した組 {len(ranked)}組",
        f"評価した向きつきの組 {stats['pairs_evaluated']}件 → 通過 {stats['pass']}件。通らなかった理由: "
        + "・".join(f"{k} {v}" for k, v in stats["rejected"].items()),
        f"以下はスコア上位{min(top, len(ranked))}組。人の目での品質確認はまだです。",
        "",
    ]
    for i, (score, vid, c) in enumerate(ranked[:top], 1):
        tv = target_video_id(c["target_id"])
        a, b = _clip(corpus[vid]["title"], 28), _clip((corpus.get(tv) or {}).get("title") or tv, 28)
        parts = [_clip(x, 46) for x in c["evidence"].split(" ／ ")]
        mark = "（既存ノートに記載あり）" if c.get("already_in_note") else ""
        lines.append(f"{i:>2}. {c['relation']} スコア{score}{mark}")
        lines.append(f"    {a} [{vid}]  ↔  {b} [{tv}]")
        lines.append("    根拠: " + "／".join(parts))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- 2.5 修復計画（差分の提案だけ）

DEFAULT_REPAIR_LIMIT = 3


def _rec_line(mark: str, target_id: str, relation: str, status: str, tail: str = "") -> str:
    return f"{mark} {target_id}  {relation or '-'}  {status or '-'}{('  ' + tail) if tail else ''}"


def repair_plan_for_corpus(
    corpus: Dict[str, Dict[str, Any]], root: Path = ROOT, limit: int = DEFAULT_REPAIR_LIMIT,
) -> Dict[str, Any]:
    """検証に通らない related_records を「削除予定」と「置換候補」の差分として提案する（読み取りのみ）。

    研究ノートのファイルは書き換えない。検証に通る記録（確定済みの合格ペアを含む）は必ず温存する。
    CONFIRMED が不合格のときは自動で消す提案にせず「人の確認」に回す。置換候補は常に CANDIDATE。
    """
    report = validate_related_records(corpus, root)
    protected = {frozenset(pair) for pair in report["confirmed_valid_pairs"]}
    bad_by_video: Dict[str, List[Dict[str, Any]]] = {}
    for item in report["items"]:
        if item["errors"]:
            bad_by_video.setdefault(item["source"].split(":")[1], []).append(item)

    videos = []
    for vid in sorted(corpus):
        doc = corpus[vid]
        bad = bad_by_video.get(vid, [])
        if not bad:
            continue
        bad_keys = {(i["target_id"], i["relation"], i["status"]) for i in bad}
        keep, remove = [], []
        for rec in doc["related_records"]:
            tid = str(rec.get("target_id") or "").strip()
            key = (tid, str(rec.get("relation") or ""), str(rec.get("status") or ""))
            row = {"target_id": tid, "relation": key[1], "status": key[2]}
            if key not in bad_keys or frozenset((f"youtube:{vid}:research", tid)) in protected:
                keep.append(row)
                continue
            item = next(i for i in bad if (i["target_id"], i["relation"], i["status"]) == key)
            action = "NEEDS_HUMAN_CONFIRMED" if key[2] == "CONFIRMED" else "DELETE_PLANNED"
            remove.append(dict(row, reasons=item["errors"], action=action))
        keep_vids = {target_video_id(k["target_id"]) for k in keep}
        removed_vids = {target_video_id(r["target_id"]) for r in remove}
        everyone = infer_candidates(doc, corpus, limit=max(len(corpus), limit))
        picked, seen = [], set()
        for c in everyone:
            tv = target_video_id(c["target_id"])
            if tv in keep_vids or tv in seen:
                continue
            if tv in removed_vids or len(picked) < limit:
                seen.add(tv)
                picked.append(dict(c, same_target_as_removed=tv in removed_vids))
        diff = [f"@@ {doc['research_path']}  related_records ({len(doc['related_records'])}件中 不合格 {len(remove)}件)"]
        diff += [_rec_line("=", k["target_id"], k["relation"], k["status"], "（温存）") for k in keep]
        diff += [_rec_line("-", r["target_id"], r["relation"], r["status"],
                           "[" + ",".join(r["reasons"]) + "]" + (" ※CONFIRMEDなので人の確認" if r["action"] != "DELETE_PLANNED" else ""))
                 for r in remove]
        diff += [_rec_line("+", c["target_id"], c["relation"], "CANDIDATE", "根拠: " + _clip(c["evidence"], 110)) for c in picked]
        videos.append({
            "video_id": vid, "title": doc["title"], "research_path": doc["research_path"],
            "keep": keep, "remove": remove, "replace_candidates": picked, "diff": "\n".join(diff),
        })
    return {
        "status": "DRY_RUN_REPAIR_PLAN",
        "files_modified": False,
        "note_count": len(corpus),
        "notes_to_repair": len(videos),
        "delete_planned_count": sum(1 for v in videos for r in v["remove"] if r["action"] == "DELETE_PLANNED"),
        "needs_human_count": sum(1 for v in videos for r in v["remove"] if r["action"] != "DELETE_PLANNED"),
        "replace_candidate_count": sum(len(v["replace_candidates"]) for v in videos),
        "protected_pairs": sorted(sorted(p) for p in protected),
        "videos": videos,
    }


_REASON_JA = {
    "SELF_LINK": "自己リンク", "TARGET_NOT_FOUND": "宛先なし", "BAD_RELATION": "関係ラベル不正", "BAD_STATUS": "status不正",
    "NOTE_MISSING": "理由なし", "EVIDENCE_MISSING": "根拠なし", "CONFIRMED_WITHOUT_TIME_OR_URL": "確定なのに時刻・URLなし",
}


def format_repair_summary(plan: Dict[str, Any], corpus: Dict[str, Dict[str, Any]]) -> str:
    """repair_plan_for_corpus の結果を、人が読める短い一覧にする（ノートごとの件数と根拠の一文だけ）。"""
    lines = [
        "【related_records 修復計画の一覧（提案だけ・ノートは書き換えません）】",
        f"対象ノート {plan['notes_to_repair']}本／削除予定 {plan['delete_planned_count']}件"
        f"／人の確認 {plan['needs_human_count']}件／置換候補 {plan['replace_candidate_count']}件",
        "温存する確定ペア: " + (" ／ ".join(" ↔ ".join(x.split(":")[1] for x in pair) for pair in plan["protected_pairs"]) or "なし"),
        "凡例: ✕=削除予定 ？=人の確認 ＋=置換候補（常にCANDIDATE。確定ではない）",
        "",
    ]
    for v in sorted(plan["videos"], key=lambda x: (-len(x["remove"]), x["video_id"])):
        lines.append(f"■ {_clip(v['title'], 34)} [{v['video_id']}]  削除予定 {len(v['remove'])}件／置換候補 {len(v['replace_candidates'])}件")
        for r in v["remove"]:
            why = "・".join(_REASON_JA.get(e, e) for e in r["reasons"])
            rt = (corpus.get(target_video_id(r["target_id"]) or "") or {}).get("title")
            lines.append(f"  {'✕' if r['action'] == 'DELETE_PLANNED' else '？'} {_clip(rt, 30) + ' ' if rt else ''}[{r['target_id']}] ({r['relation'] or '-'}) ─ {why}")
        for c in v["replace_candidates"]:
            tv = target_video_id(c["target_id"])
            tt = _clip((corpus.get(tv) or {}).get("title") or tv, 30)
            parts = [_clip(x, 40) for x in c["evidence"].split(" ／ ")]
            same = "（同じ宛先）" if c["same_target_as_removed"] else ""
            lines.append(f"  ＋ {tt} [{tv}] {c['relation']}{same} ─ " + "／".join(parts))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


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
    c.add_argument("--summary", action="store_true", help="JSONではなく、スコア上位の組を根拠の一文つきで人が読める形に出す")
    c.add_argument("--top", type=int, default=20, help="--summary で出す組の数")
    r = sub.add_parser("repair-plan", help="検証に通らない related_records の削除予定と置換候補を差分で出す（書き換えない）")
    r.add_argument("--video-id")
    r.add_argument("--limit", type=int, default=DEFAULT_REPAIR_LIMIT, help="1ノートあたりの置換候補の上限")
    r.add_argument("--print-diff", action="store_true", help="差分を読みやすい文字列でも出す")
    r.add_argument("--summary", action="store_true", help="JSONではなく、ノートごとの件数と根拠の一文だけの人が読める一覧を出す")
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
        if args.summary:
            print(format_candidate_summary(rep, corpus, top=args.top), end="")
            return 0
        if args.video_id:
            rep["videos"] = [v for v in rep["videos"] if v["video_id"] == args.video_id]
    elif args.cmd == "repair-plan":
        rep = repair_plan_for_corpus(corpus, ROOT, limit=args.limit)
        if args.video_id:
            rep["videos"] = [v for v in rep["videos"] if v["video_id"] == args.video_id]
        if args.summary:
            print(format_repair_summary(rep, corpus), end="")
            return 0
        if args.print_diff:
            rep["diff_text"] = "\n\n".join(v["diff"] for v in rep["videos"])
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
