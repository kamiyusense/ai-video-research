#!/usr/bin/env python3
"""AI技術研究室 | 質問回答・時刻付き動画箇所検索エンジン (`query_research.py` v0.6).

役割:
① ユーザーの自然文質問の意図（概念理解・失敗例/注意点・実装手順・一次資料検証・動画箇所特定）と同義語を解析する。
② GitHub正本の研究記録 (`research/*.md`, `notes/*.md`, `registry.json`, `loop_state.json`) から、
   単なる文字列一致ではなく「質問目的との適合度 × 一次資料の検証強度 × 説明の詳しさ × 確認済み時刻の有無」で
   最適な研究記録・チャプター（動画区間）・検証済み主張をランキング検索する。
③ Gemini Notebook（元資料の図書館）でさらに詳しく参照すべきソースID・動画URLと深掘り質問文を案内する。
④ 既存知識で足りない点（UNKNOWN・未解決課題P006・未調査トピック）を検出し、追加調査候補を提示する。
⑤ 一次資料の確認ステータス (`CONFIRMED_DOC` / `VIDEO_REPORTED` / `UNKNOWN` 等) を区別して根拠付き回答をまとめる。
⑥ **時刻の根拠 (`timestamp_source`) が確認できている場合のみ** YouTube再生位置リンク (`&t=XXs`) を生成し、
   時刻未確認の箇所は推測でリンクを作らず `UNKNOWN` と明示する。
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_PATH = (
    Path(__file__).resolve().parent / "state" / "video_knowledge_catalog.json"
)
DEFAULT_STATE_PATH = Path(__file__).resolve().parent / "state" / "loop_state.json"
DEFAULT_NOTEBOOK_URL = (
    "https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7"
)

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")

# 1.v0.6形式のチャプター行:
# - [02:00〜06:30](https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120s) | **章タイトル** | 要約 | time_source: YOUTUBE_CHAPTER_METADATA | topics: Harness, Hooks
# または
# - UNKNOWN | **章タイトル** | 要約 | time_source: UNKNOWN | topics: NONE
V06_CHAPTER_LINE_RE = re.compile(
    r"^\s*-\s*(?:\[(?P<range_label>[^\]]+)\]\((?P<url>https://www\.youtube\.com/watch\?v=(?P<vid>[A-Za-z0-9_-]{11})&t=(?P<start>\d+)s)\)|(?P<unknown_tok>UNKNOWN))\s*\|\s*\*\*(?P<title>[^*]+)\*\*\s*\|\s*(?P<summary>[^|]+)\|\s*time_source:\s*(?P<ts_source>[A-Z_]+)\s*\|\s*topics:\s*(?P<topics>.+?)\s*$"
)

# 2.v0.5/v0.6形式のClaim行:
# - 主張テキスト | CONFIRMED_DOC | time: [02:05](https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=125s) | official: https://... | time_source: TIMESTAMPED_CAPTIONS
V06_CLAIM_LINE_RE = re.compile(
    r"^\s*-\s*(?P<text>.+?)\s*\|\s*(?P<status>CONFIRMED_DOC|REPORTED_BY_AUTHOR|CONFIRMED_TEST|UNKNOWN|CONTRADICTED)\s*\|\s*time:\s*(?:\[(?P<mmss>\d+:\d{2})\]\((?P<url>https://www\.youtube\.com/watch\?v=(?P<vid>[A-Za-z0-9_-]{11})&t=(?P<sec>\d+)s)\)|UNKNOWN)\s*\|\s*official:\s*(?P<official>[^\s|]+)(?:\s*\|\s*time_source:\s*(?P<ts_source>[A-Z_]+))?\s*$"
)

# 3. 既存研究記録 (lC5jxpYmatE / Vr3JkAT9mo8) のMarkdownテーブル行:
# | V05-01 | [02:02](https://www.youtube.com/watch?v=lC5jxpYmatE&t=122s)〜10:39 | 要約 | 根拠 | 結果 |
# または
# | [03:00](https://www.youtube.com/watch?v=Vr3JkAT9mo8&t=180s)〜04:10 | 内容 | 事実の区別 |
LEGACY_TABLE_ROW_WITH_ID_RE = re.compile(
    r"^\s*\|\s*(?P<seg_id>[A-Za-z0-9_-]+)\s*\|\s*(?:\[(?P<start_mmss>\d{1,2}:\d{2})\]\((?P<url>https://www\.youtube\.com/watch\?v=(?P<vid>[A-Za-z0-9_-]{11})&t=(?P<start_sec>\d+)s)\)|(?P<raw_start_mmss>\d{1,2}:\d{2}))(?:[〜~-](?P<end_mmss>\d{1,2}:\d{2}))?\s*\|\s*(?P<summary>[^|]+)\|\s*(?P<basis>[^|]+)\|\s*(?P<result>[^|]+)\|\s*$"
)
LEGACY_TABLE_ROW_NO_ID_RE = re.compile(
    r"^\s*\|\s*(?:\[(?P<start_mmss>\d{1,2}:\d{2})\]\((?P<url>https://www\.youtube\.com/watch\?v=(?P<vid>[A-Za-z0-9_-]{11})&t=(?P<start_sec>\d+)s)\)|(?P<raw_start_mmss>\d{1,2}:\d{2}))(?:[〜~-](?P<end_mmss>\d{1,2}:\d{2}))?\s*\|\s*(?P<summary>[^|]+)\|\s*(?P<basis>[^|]+)\|\s*$"
)

RELATED_RECORD_LINE_RE = re.compile(
    r"^\s*-\s*`(?P<target_id>[^`]+)`\s*\((?P<relation>[A-Z_]+)\):\s*(?P<note>.+?)\s*$"
)

# 質問の意図分類ルール
INTENT_RULES = {
    "FAILURE_AND_LIMITS": [
        "失敗",
        "問題",
        "注意",
        "限界",
        "デメリット",
        "落とし穴",
        "増やしすぎ",
        "フリーズ",
        "アンチパターン",
        "弱点",
        "だめ",
        "ダメ",
        "批判",
        "矛盾",
        "不正確",
        "誤解",
        "苦労",
        "負担",
    ],
    "CONCEPT_AND_BASICS": [
        "って何",
        "とは",
        "何？",
        "なに？",
        "基本",
        "概要",
        "役割",
        "違い",
        "仕組み",
        "意味",
        "概念",
        "教えて",
        "わかりやすく",
        "分かりやすく",
    ],
    "IMPLEMENTATION_AND_HOWTO": [
        "手順",
        "作り方",
        "設計",
        "実装",
        "やり方",
        "方法",
        "移行",
        "スクリプト",
        "構築",
        "自動化",
        "設定",
        "使い方",
        "どうすれば",
    ],
    "VERIFICATION_AND_OFFICIAL_SPEC": [
        "公式",
        "一次資料",
        "検証",
        "仕様",
        "裏付け",
        "本当に",
        "事実",
        "ドキュメント",
        "証拠",
    ],
    "VIDEO_LOCATOR": [
        "どの動画",
        "動画はどこ",
        "動画は",
        "どこを見れば",
        "どこをみれば",
        "どこ？",
        "何分",
        "箇所",
        "再生",
        "チャプター",
        "タイムスタンプ",
        "時刻",
        "シーン",
        "話していた",
        "説明していた",
    ],
}

# 技術概念の同義語・関連語グループ
SYNONYM_GROUPS = [
    {
        "canonical": "ハーネス (Harness / Hooks)",
        "terms": [
            "ハーネス",
            "harness",
            "hooks",
            "hook",
            "フック",
            "守り・拡張",
            "状態管理",
            "実行前後",
            "ロールバック",
        ],
    },
    {
        "canonical": "スキル設計 (Skill / SKILL.md)",
        "terms": [
            "スキル",
            "skill",
            "skills",
            "skill.md",
            "遅延読み込み",
            "オンデマンド",
            "成果物の必要時参照",
            "増やしすぎ",
            "管理負担",
        ],
    },
    {
        "canonical": "担当制・右腕AI (Specialist / Work)",
        "terms": [
            "担当制",
            "右腕ai",
            "右腕",
            "specialist",
            "specialists",
            "agents.md",
            "memory.md",
            "resources",
            "役割分担",
            "chatgpt work",
        ],
    },
    {
        "canonical": "Computer Use・スクリプト固定化",
        "terms": [
            "computer use",
            "コンピュータユース",
            "画面操作",
            "ブラウザ操作",
            "反復操作",
            "スクリプト",
            "固定化",
            "省力化",
        ],
    },
    {
        "canonical": "課題ドリブン・未解決課題ストック (P006)",
        "terms": [
            "課題ドリブン",
            "課題ストック",
            "未解決課題",
            "p006",
            "できなかった課題",
            "再挑戦",
        ],
    },
    {
        "canonical": "Gemini Notebook (NotebookLM) 連携・知識索引",
        "terms": [
            "notebook",
            "notebooklm",
            "gemini notebook",
            "知識索引",
            "図書館",
            "ソース",
        ],
    },
    {
        "canonical": "Dify・GUIワークフロー比較",
        "terms": [
            "dify",
            "guiワークフロー",
            "ワークフロー",
        ],
    },
    {
        "canonical": "Jev・ブラウザ選択モデル",
        "terms": [
            "jev",
            "特化型判断モデル",
            "ブラウザ選択",
        ],
    },
    {
        "canonical": "Google AI Studio・映像解析",
        "terms": [
            "ai studio",
            "google ai studio",
            "映像解析",
            "フレーム",
            "フリーズ",
        ],
    },
    {
        "canonical": "トークン・利用枠節約・プロンプトキャッシュ (Prompt Caching)",
        "terms": [
            "トークン",
            "利用枠",
            "使用枠",
            "節約",
            "キャッシュ",
            "プロンプトキャッシュ",
            "prompt caching",
            "月12日問題",
            "5時間制限",
            "クォータ",
        ],
    },
    {
        "canonical": "Gemini Notebook Studio・スライド出力・注意点",
        "terms": [
            "studio",
            "スライド",
            "画像データ",
            "文字編集不可",
            "pptx",
            "docx",
            "ブリーフィングドキュメント",
            "インフォグラフィック",
        ],
    },
    {
        "canonical": "AI社員・自律エージェント・並列オーケストレーション",
        "terms": [
            "ai社員",
            "自律エージェント",
            "コーディネーター",
            "サブエージェント",
            "サブスレッド",
            "並列",
            "マスターコンテキスト",
            "自己改善ループ",
            "rsi",
            "dots",
        ],
    },
    {
        "canonical": "Obsidian・ローカル記憶・LLM Wiki連携",
        "terms": [
            "obsidian",
            "vault",
            "llm wiki",
            "ローカル共創",
            "内部リンク",
            "claude.md",
            "memory.md",
        ],
    },
]


def parse_mmss_to_seconds(mmss_str):
    if not mmss_str or not isinstance(mmss_str, str):
        return None
    parts = mmss_str.strip().split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except ValueError:
        return None
    return None


def format_seconds_mmss(sec):
    if sec is None or not isinstance(sec, int) or sec < 0:
        return "UNKNOWN"
    return f"{sec // 60:02d}:{sec % 60:02d}"


def build_verified_youtube_link(video_id, start_seconds, timestamp_source):
    """時刻根拠が確認済み (timestamp_source != 'UNKNOWN') かつ整数秒がある場合のみ再生リンクを返す。"""
    if (
        not video_id
        or not VIDEO_ID_RE.fullmatch(str(video_id))
        or start_seconds is None
        or type(start_seconds) is not int
        or start_seconds < 0
        or not timestamp_source
        or timestamp_source == "UNKNOWN"
    ):
        return None
    return f"https://www.youtube.com/watch?v={video_id}&t={start_seconds}s"


def infer_legacy_timestamp_source(basis_text):
    b = (basis_text or "").lower()
    if "ai studio" in b or "映像" in b or "実演" in b:
        return "VISUAL_FRAME_CHECK"
    if "chapter" in b or "チャプター" in b or "目次" in b:
        return "YOUTUBE_CHAPTER_METADATA"
    if "字幕直接" in b or "deterministic caption" in b:
        return "TIMESTAMPED_CAPTIONS"
    return "UNKNOWN"


def split_markdown_sections(md_text):
    """Markdown本文を見出し (## / ###) ごとの辞書に分割する。"""
    sections = {"_header": []}
    current_heading = "_header"
    for line in md_text.splitlines():
        m = re.match(r"^(#{1,3})\s+(.+?)\s*$", line)
        if m:
            current_heading = m.group(2).strip()
            sections.setdefault(current_heading, [])
        else:
            sections.setdefault(current_heading, []).append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def parse_research_markdown_file(md_path, root=ROOT, registry_entry=None):
    """`research/*.md` または `notes/*.md` を解析し、構造化カタログエントリに変換する。"""
    rel_path = md_path.relative_to(root).as_posix()
    text = md_path.read_text(encoding="utf-8")
    sections = split_markdown_sections(text)

    # タイトル取得
    title = rel_path
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    for meta_line in text.splitlines():
        m_title = re.match(r"^\s*-\s*タイトル[^:：]*[:：]\s*(.+)$", meta_line)
        if m_title:
            title = f"{title}（{m_title.group(1).strip()}）"
            break

    # video_id 取得
    video_id = None
    if registry_entry and registry_entry.get("video_id"):
        video_id = registry_entry["video_id"]
    if not video_id:
        for pat in (
            r"^\s*-\s*video_id:\s*`?([A-Za-z0-9_-]{11})`?\s*$",
            r"^\s*-\s*動画ID:\s*`?([A-Za-z0-9_-]{11})`?\s*$",
            r"^\s*-\s*record_id:\s*`?youtube:([A-Za-z0-9_-]{11})`?\s*$",
        ):
            m = re.search(pat, text, re.MULTILINE)
            if m:
                video_id = m.group(1)
                break
    if not video_id:
        m_fn = re.search(r"\d{4}-\d{2}-\d{2}-([A-Za-z0-9_-]{11})-", rel_path)
        if m_fn:
            video_id = m_fn.group(1)

    canonical_url = (
        f"https://www.youtube.com/watch?v={video_id}" if video_id else None
    )

    # Notebook source ID
    notebook_source_id = "UNKNOWN"
    m_nb = re.search(
        r"^\s*-\s*Gemini Notebook source:\s*(.+?)\s*$", text, re.MULTILINE
    )
    if m_nb:
        notebook_source_id = m_nb.group(1).strip()

    # source_scope
    source_scope = (
        registry_entry.get("source_scope", "") if registry_entry else ""
    )
    if not source_scope:
        for pat in (
            r"^\s*-\s*source_scope:\s*(.+?)\s*$",
            r"^\s*-\s*記録方法:\s*(.+?)\s*$",
            r"^\s*-\s*取得の範囲:\s*(.+?)\s*$",
        ):
            m_sc = re.search(pat, text, re.MULTILINE)
            if m_sc:
                source_scope = m_sc.group(1).strip()
                break

    # 要約セクション
    summary_ja = ""
    for sec_title, sec_body in sections.items():
        if any(
            k in sec_title
            for k in ("独自要約", "結論（独自要約）", "結論", "1. 判断")
        ):
            summary_ja = sec_body.strip()
            break
    delta_summary = ""
    for sec_title, sec_body in sections.items():
        if "差分要約" in sec_title and sec_body.strip():
            delta_summary = sec_body.strip()
            break
    if delta_summary:
        if not summary_ja:
            summary_ja = delta_summary
        elif delta_summary not in summary_ja:
            summary_ja = f"{summary_ja}\n[差分更新要約] {delta_summary}"

    # 詳細技術知識・持ち帰り・失敗例セクション
    detailed_findings_parts = []
    failure_and_limits_parts = []
    official_verification_parts = []

    for sec_title, sec_body in sections.items():
        if not sec_body:
            continue
        if any(
            k in sec_title
            for k in (
                "詳細技術知識",
                "追加・更新された詳細技術知識",
                "研究室への持ち帰り",
                "解釈と研究室への活用",
                "勉強して役立てる",
                "適用評価",
            )
        ):
            detailed_findings_parts.append(f"[{sec_title}]\n{sec_body}")
        if any(
            k in sec_title
            for k in ("既知の条件・失敗例", "既知の限界", "限界", "検証を保留する主張")
        ):
            failure_and_limits_parts.append(f"[{sec_title}]\n{sec_body}")
        if any(
            k in sec_title
            for k in (
                "公式資料との照合",
                "一次資料との照合",
                "主張・一次資料・時刻",
                "追加・更新された主張と検証",
                "独立して確認したこと",
            )
        ):
            official_verification_parts.append(f"[{sec_title}]\n{sec_body}")

    # チャプター・動画区間の抽出 (v0.6形式 + 既存テーブル形式の両対応)
    chapters = []
    claims = []
    related_records = []

    for line in text.splitlines():
        m_ch = V06_CHAPTER_LINE_RE.match(line)
        if m_ch:
            ts_source = m_ch.group("ts_source").strip()
            start_str = m_ch.group("start")
            start_sec = int(start_str) if start_str is not None else None
            range_label = m_ch.group("range_label") or "UNKNOWN"
            end_sec = None
            if "〜" in range_label:
                end_part = range_label.split("〜", 1)[1]
                end_sec = parse_mmss_to_seconds(end_part)
            topics_raw = m_ch.group("topics").strip()
            topics = (
                [t.strip() for t in topics_raw.split(",") if t.strip()]
                if topics_raw and topics_raw != "NONE"
                else []
            )
            vid_for_link = m_ch.group("vid") or video_id
            verified_url = build_verified_youtube_link(
                vid_for_link, start_sec, ts_source
            )
            chapters.append(
                {
                    "segment_id": f"CH-{len(chapters) + 1:02d}",
                    "title": m_ch.group("title").strip(),
                    "summary_ja": m_ch.group("summary").strip(),
                    "start_seconds": start_sec if verified_url else None,
                    "end_seconds": end_sec if verified_url else None,
                    "start_mmss": format_seconds_mmss(start_sec)
                    if verified_url
                    else "UNKNOWN",
                    "end_mmss": format_seconds_mmss(end_sec)
                    if (verified_url and end_sec is not None)
                    else None,
                    "timestamp_source": ts_source,
                    "timestamp_basis": ts_source,
                    "verification_result": "CHAPTER_TIMELINE",
                    "key_topics": topics,
                    "playback_url": verified_url,
                }
            )
            continue

        m_cl = V06_CLAIM_LINE_RE.match(line)
        if m_cl:
            sec_str = m_cl.group("sec")
            sec_val = int(sec_str) if sec_str is not None else None
            ts_source = (
                m_cl.group("ts_source").strip()
                if m_cl.group("ts_source")
                else ("TIMESTAMPED_CAPTIONS" if sec_val is not None else "UNKNOWN")
            )
            vid_for_link = m_cl.group("vid") or video_id
            verified_url = build_verified_youtube_link(
                vid_for_link, sec_val, ts_source
            )
            official_val = m_cl.group("official").strip()
            claims.append(
                {
                    "text": m_cl.group("text").strip(),
                    "status": m_cl.group("status").strip(),
                    "timestamp_seconds": sec_val if verified_url else None,
                    "timestamp_mmss": format_seconds_mmss(sec_val)
                    if verified_url
                    else "UNKNOWN",
                    "timestamp_source": ts_source,
                    "playback_url": verified_url,
                    "official_url": None
                    if official_val == "UNKNOWN"
                    else official_val,
                }
            )
            continue

        m_leg_id = LEGACY_TABLE_ROW_WITH_ID_RE.match(line)
        if m_leg_id:
            start_mmss = m_leg_id.group("start_mmss") or m_leg_id.group("raw_start_mmss")
            start_sec = (
                int(m_leg_id.group("start_sec"))
                if m_leg_id.group("start_sec")
                else parse_mmss_to_seconds(start_mmss)
            )
            end_mmss = m_leg_id.group("end_mmss")
            end_sec = parse_mmss_to_seconds(end_mmss) if end_mmss else None
            basis = m_leg_id.group("basis").strip()
            ts_source = infer_legacy_timestamp_source(basis)
            vid_for_link = m_leg_id.group("vid") or video_id
            verified_url = build_verified_youtube_link(
                vid_for_link, start_sec, ts_source
            )
            summary_txt = m_leg_id.group("summary").strip()
            chapters.append(
                {
                    "segment_id": m_leg_id.group("seg_id").strip(),
                    "title": summary_txt[:60],
                    "summary_ja": summary_txt,
                    "start_seconds": start_sec if verified_url else None,
                    "end_seconds": end_sec if verified_url else None,
                    "start_mmss": start_mmss if verified_url else "UNKNOWN",
                    "end_mmss": end_mmss if (verified_url and end_sec is not None) else None,
                    "timestamp_source": ts_source,
                    "timestamp_basis": basis,
                    "verification_result": m_leg_id.group("result").strip(),
                    "key_topics": [],
                    "playback_url": verified_url,
                }
            )
            continue

        m_leg_noid = LEGACY_TABLE_ROW_NO_ID_RE.match(line)
        if m_leg_noid:
            start_mmss = m_leg_noid.group("start_mmss") or m_leg_noid.group("raw_start_mmss")
            start_sec = (
                int(m_leg_noid.group("start_sec"))
                if m_leg_noid.group("start_sec")
                else parse_mmss_to_seconds(start_mmss)
            )
            end_mmss = m_leg_noid.group("end_mmss")
            end_sec = parse_mmss_to_seconds(end_mmss) if end_mmss else None
            basis = m_leg_noid.group("basis").strip()
            ts_source = infer_legacy_timestamp_source(basis)
            vid_for_link = m_leg_noid.group("vid") or video_id
            verified_url = build_verified_youtube_link(
                vid_for_link, start_sec, ts_source
            )
            summary_txt = m_leg_noid.group("summary").strip()
            chapters.append(
                {
                    "segment_id": f"SEG-{len(chapters) + 1:02d}",
                    "title": summary_txt[:60],
                    "summary_ja": summary_txt,
                    "start_seconds": start_sec if verified_url else None,
                    "end_seconds": end_sec if verified_url else None,
                    "start_mmss": start_mmss if verified_url else "UNKNOWN",
                    "end_mmss": end_mmss if (verified_url and end_sec is not None) else None,
                    "timestamp_source": ts_source,
                    "timestamp_basis": basis,
                    "verification_result": basis,
                    "key_topics": [],
                    "playback_url": verified_url,
                }
            )
            continue

        m_rel = RELATED_RECORD_LINE_RE.match(line)
        if m_rel:
            related_records.append(
                {
                    "target_id": m_rel.group("target_id").strip(),
                    "relation": m_rel.group("relation").strip(),
                    "note": m_rel.group("note").strip(),
                }
            )

    # 既存Markdown内の公式照合番号付きリスト (例: `1. **Claude Code Skills**: https://...`) も抽出
    if not claims and official_verification_parts:
        ov_text = "\n".join(official_verification_parts)
        for m_ov in re.finditer(
            r"^\s*\d+\.\s*\*\*(?P<name>[^*]+)\*\*:\s*(?P<url>https://[^\s]+)\s*\n(?P<bullets>(?:\s+-\s+.+\n?)+)",
            ov_text,
            re.MULTILINE,
        ):
            name = m_ov.group("name").strip()
            u = m_ov.group("url").strip()
            bullets = " / ".join(
                b.strip().lstrip("- ").strip()
                for b in m_ov.group("bullets").strip().splitlines()
            )
            status = (
                "CONFIRMED_DOC"
                if "CONFIRMED_DOC" in bullets
                else ("CONFIRMED_TEST" if "CONFIRMED_TEST" in bullets else "CONFIRMED_DOC")
            )
            claims.append(
                {
                    "text": f"{name}: {bullets}",
                    "status": status,
                    "timestamp_seconds": None,
                    "timestamp_mmss": "UNKNOWN",
                    "timestamp_source": "UNKNOWN",
                    "playback_url": None,
                    "official_url": u,
                }
            )

    return {
        "record_path": rel_path,
        "video_id": video_id,
        "title": title,
        "canonical_url": canonical_url,
        "notebook_source_id": notebook_source_id,
        "source_scope": source_scope,
        "summary_ja": summary_ja,
        "detailed_findings_ja": "\n\n".join(detailed_findings_parts),
        "failure_and_limits_ja": "\n\n".join(failure_and_limits_parts),
        "official_verification_ja": "\n\n".join(official_verification_parts),
        "chapters": chapters,
        "claims": claims,
        "related_records": related_records,
        "full_text_for_index": text,
    }


def build_video_knowledge_catalog(root=ROOT, write_path=None):
    """GitHubリポジトリ内の全研究記録・台帳を走査し、構造化知識・タイムラインカタログを生成する。"""
    registry_path = root / "registry.json"
    reg_by_path = {}
    reg_by_vid = {}
    if registry_path.exists():
        reg = json.loads(registry_path.read_text(encoding="utf-8"))
        for rec in reg.get("records", []):
            if isinstance(rec, dict):
                if rec.get("research_path"):
                    reg_by_path[rec["research_path"]] = rec
                if rec.get("video_id"):
                    reg_by_vid[rec["video_id"]] = rec

    records = []
    for folder_name in ("research", "notes"):
        folder = root / folder_name
        if not folder.exists():
            continue
        for md_file in sorted(folder.rglob("*.md")):
            rel_path = md_file.relative_to(root).as_posix()
            reg_entry = reg_by_path.get(rel_path)
            if not reg_entry:
                m_fn = re.search(r"\d{4}-\d{2}-\d{2}-([A-Za-z0-9_-]{11})-", rel_path)
                if m_fn:
                    reg_entry = reg_by_vid.get(m_fn.group(1))
            parsed = parse_research_markdown_file(
                md_file, root=root, registry_entry=reg_entry
            )
            records.append(parsed)

    state_path = root / "automation" / "gemini-notebook" / "state" / "loop_state.json"
    loop_state = {}
    if state_path.exists():
        try:
            loop_state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            loop_state = {}

    catalog = {
        "schema_version": "video_knowledge_catalog_v1",
        "generated_at": date.today().isoformat(),
        "repository": "kamiyusense/ai-video-research",
        "notebook_url": loop_state.get("notebook_url", DEFAULT_NOTEBOOK_URL),
        "total_records": len(records),
        "total_video_records": sum(1 for r in records if r.get("video_id")),
        "total_verified_chapters": sum(
            sum(1 for ch in r.get("chapters", []) if ch.get("playback_url"))
            for r in records
        ),
        "records": [
            {k: v for k, v in r.items() if k != "full_text_for_index"}
            for r in records
        ],
        "unresolved_backlog_refs": loop_state.get("unresolved_backlog_refs", []),
        "next_topics_queue": loop_state.get("next_topics_queue", []),
        "open_unknowns": loop_state.get("open_unknowns", []),
    }

    if write_path is not None:
        out_p = Path(write_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return catalog, records


def analyze_query_intent(query):
    """① 質問の意図（目的カテゴリ）と対象トピック・同義語を解析する。"""
    q_norm = (query or "").strip()
    q_lower = q_norm.lower()

    detected_intents = []
    for intent_name, triggers in INTENT_RULES.items():
        if any(t.lower() in q_lower for t in triggers):
            detected_intents.append(intent_name)
    if not detected_intents:
        detected_intents.append("CONCEPT_AND_BASICS")

    matched_concepts = []
    expanded_terms = set()
    for grp in SYNONYM_GROUPS:
        if any(t.lower() in q_lower for t in grp["terms"]):
            matched_concepts.append(grp["canonical"])
            for t in grp["terms"]:
                expanded_terms.add(t.lower())

    # 質問文から助詞・疑問詞を除いた主要キーワードも抽出
    stop_phrases = [
        "インストールしたら",
        "インストール",
        "準備しときたい",
        "準備したい",
        "準備すべき",
        "準備",
        "再生位置を",
        "再生位置",
        "について",
        "に関して",
        "って何",
        "とは何",
        "とは",
        "どの動画",
        "どこを見れば",
        "どこをみれば",
        "解説している",
        "解説していた",
        "する動画",
        "動画はどこ",
        "動画と時刻",
        "動画は",
        "動画",
        "時刻",
        "どこ",
        "組み合わせる",
        "組み合わせ",
        "いいですか",
        "いい？",
        "教えて",
        "ください",
        "前に調べた",
        "話していた",
        "説明していた",
        "箇所を",
        "箇所",
        "の動画で",
        "の動画",
        "連携の",
        "連携",
        "完全に",
        "完全",
        "リポジトリ外",
        "リポジトリ",
        "例えば",
        "例：",
        "例:",
        "例",
        "検証済み",
        "確認済み",
        "を",
        "の",
        "で",
        "に",
        "は",
        "が",
        "と",
        "や",
        "？",
        "?",
        "、",
        "。",
    ]
    cleaned_q = re.sub(r"([a-z0-9./_-]+)([^\x00-\x7f]+)", r"\1 \2", q_lower)
    cleaned_q = re.sub(r"([^\x00-\x7f]+)([a-z0-9./_-]+)", r"\1 \2", cleaned_q)
    compound_map = {
        "claude code": "claude__code",
        "gemini notebook": "gemini__notebook",
        "skill creator": "skill__creator",
        "discord mcp": "discord__mcp",
        "playwright mcp": "playwright__mcp",
        "prompt caching": "prompt__caching",
        "youtube to notebooklm": "youtube__to__notebooklm",
        "chatgpt work": "chatgpt__work",
    }
    for k, v in compound_map.items():
        cleaned_q = cleaned_q.replace(k, v)
    for sp in stop_phrases:
        cleaned_q = cleaned_q.replace(sp, " ")
    raw_tokens = []
    explicit_video_ids = []
    for tok in re.split(r"[\s/・,，]+", cleaned_q):
        t_clean = tok.strip().replace("__", " ")
        if t_clean.endswith("する") and len(t_clean) >= 4:
            t_clean = t_clean[:-2]
        if len(t_clean) >= 2 and t_clean not in raw_tokens:
            raw_tokens.append(t_clean)
            if VIDEO_ID_RE.match(t_clean):
                explicit_video_ids.append(t_clean)
    for tok in raw_tokens:
        expanded_terms.add(tok)

    return {
        "original_query": q_norm,
        "intents": detected_intents,
        "matched_concepts": matched_concepts,
        "search_terms": sorted(expanded_terms),
        "raw_tokens": raw_tokens,
        "explicit_video_ids": explicit_video_ids,
    }


GENERIC_QUERY_TOKENS = {
    "技術",
    "方法",
    "機能",
    "手順",
    "概要",
    "詳細",
    "設定",
    "連携",
    "解説",
    "紹介",
    "活用",
    "全体",
    "開発",
    "自動化",
    "作成",
    "確認",
    "検証",
    "比較",
}


def score_text_against_terms(text, terms, raw_tokens):
    if not text:
        return 0, []
    t_lower = text.lower()
    score = 0
    matched = []
    raw_matched_count = 0
    for tok in raw_tokens:
        if tok in t_lower:
            score += 18
            matched.append(tok)
            raw_matched_count += 1
    if raw_matched_count >= 2:
        score += (raw_matched_count - 1) * 15
    for term in terms:
        if term in t_lower and term not in matched:
            score += 10
            matched.append(term)
    return score, matched


def search_github_knowledge(intent_info, parsed_records, top_k=5):
    """② GitHub上の研究記録・目次・検証済み主張を「目的適合度×検証強度×時刻根拠」で検索する。"""
    terms = intent_info["search_terms"]
    raw_tokens = intent_info["raw_tokens"]
    intents = set(intent_info["intents"])

    scored_records = []
    scored_segments = []

    failure_cue_words = (
        "失敗",
        "問題",
        "増やしすぎ",
        "重複",
        "管理負担",
        "限界",
        "注意",
        "不正確",
        "批判",
        "フリーズ",
        "保留",
        "罠",
    )
    concept_cue_words = (
        "役割",
        "説明",
        "とは",
        "仕組み",
        "分離",
        "基本",
        "定義",
        "紹介",
    )
    howto_cue_words = (
        "手順",
        "構築",
        "配置",
        "設計",
        "アーキテクチャ",
        "要素",
        "設定",
        "スクリプト",
        "移行",
        "実装",
        "実践",
    )

    for rec in parsed_records:
        title_score, m1 = score_text_against_terms(rec["title"], terms, raw_tokens)
        sum_score, m2 = score_text_against_terms(rec["summary_ja"], terms, raw_tokens)
        det_score, m3 = score_text_against_terms(
            rec["detailed_findings_ja"], terms, raw_tokens
        )
        fail_score, m4 = score_text_against_terms(
            rec["failure_and_limits_ja"], terms, raw_tokens
        )
        off_score, m5 = score_text_against_terms(
            rec["official_verification_ja"], terms, raw_tokens
        )
        body_score, m6 = score_text_against_terms(
            rec["full_text_for_index"], terms, raw_tokens
        )

        rec_total = (
            title_score * 2.0
            + sum_score * 1.5
            + det_score * 1.4
            + fail_score * 1.4
            + off_score * 1.3
            + body_score * 0.5
        )

        # 質問意図に応じたレコード加点
        if "FAILURE_AND_LIMITS" in intents and rec["failure_and_limits_ja"]:
            rec_total += 25 + fail_score
        if "VERIFICATION_AND_OFFICIAL_SPEC" in intents and rec["official_verification_ja"]:
            rec_total += 25 + off_score
        if "VIDEO_LOCATOR" in intents and rec.get("video_id"):
            rec_total += 20

        is_explicit_vid = bool(
            rec.get("video_id")
            and rec["video_id"].lower() in [v.lower() for v in intent_info.get("explicit_video_ids", [])]
        )
        if is_explicit_vid:
            rec_total += 300

        # チャプター / 区間の個別スコアリング（章タイトル・要約の直接一致をトピックタグより優先）
        best_seg_score_for_rec = 0
        for ch in rec.get("chapters", []):
            ch_title_sum = " ".join([ch.get("title", ""), ch.get("summary_ja", "")])
            ch_topics_str = " ".join(ch.get("key_topics", []))
            ch_text = f"{ch_title_sum} {ch_topics_str}"
            title_seg_score, m_ts = score_text_against_terms(
                ch_title_sum, terms, raw_tokens
            )
            topic_seg_score, m_tp = score_text_against_terms(
                ch_topics_str, terms, raw_tokens
            )
            seg_score = (title_seg_score * 1.5) + (topic_seg_score * 0.4)
            seg_matches = sorted(set(m_ts + m_tp))

            if is_explicit_vid:
                # 動画ID明示指定時は全章（特に検証済み章）を候補として抽出
                seg_score = max(seg_score, 40.0)
                if ch.get("playback_url"):
                    seg_score += 30.0

            # チャプター自身がトピック語に一致している場合のみ意図・時刻ボーナスを付与
            if seg_score > 0:
                if "FAILURE_AND_LIMITS" in intents and any(
                    w in ch_text for w in failure_cue_words
                ):
                    seg_score += 35
                if "CONCEPT_AND_BASICS" in intents and any(
                    w in ch_text for w in concept_cue_words
                ):
                    seg_score += 20
                if "IMPLEMENTATION_AND_HOWTO" in intents and any(
                    w in ch_text for w in howto_cue_words
                ):
                    seg_score += 25
                if "VIDEO_LOCATOR" in intents:
                    seg_score += 20

                # 確認済み再生リンクがある場合は時刻信頼性ボーナス
                if ch.get("playback_url"):
                    seg_score += 25 if "VIDEO_LOCATOR" in intents else 15

                if seg_score > best_seg_score_for_rec:
                    best_seg_score_for_rec = seg_score

                if seg_score >= 20:
                    scored_segments.append(
                        {
                            "score": round(seg_score + (title_score * 0.15), 1),
                            "video_id": rec["video_id"],
                            "video_title": rec["title"],
                            "canonical_url": rec["canonical_url"],
                            "record_path": rec["record_path"],
                            "notebook_source_id": rec["notebook_source_id"],
                            "segment_type": "CHAPTER_SEGMENT",
                            "segment_id": ch["segment_id"],
                            "chapter_title": ch["title"],
                            "summary_ja": ch["summary_ja"],
                            "start_seconds": ch["start_seconds"],
                            "end_seconds": ch["end_seconds"],
                            "start_mmss": ch["start_mmss"],
                            "end_mmss": ch["end_mmss"],
                            "timestamp_source": ch["timestamp_source"],
                            "timestamp_basis": ch["timestamp_basis"],
                            "verification_status": ch["verification_result"],
                            "playback_url": ch["playback_url"],
                            "official_url": None,
                            "matched_terms": sorted(set(seg_matches)),
                        }
                    )

        # Claim（一次資料検証付き主張）の個別スコアリング
        for idx, cl in enumerate(rec.get("claims", []), 1):
            cl_score, cl_matches = score_text_against_terms(
                cl.get("text", ""), terms, raw_tokens
            )
            if cl_score > 0:
                if cl.get("status") in {"CONFIRMED_DOC", "CONFIRMED_TEST"}:
                    cl_score += 25
                elif cl.get("status") == "CONTRADICTED":
                    cl_score += 20
                if "FAILURE_AND_LIMITS" in intents and any(
                    w in cl.get("text", "") for w in failure_cue_words
                ):
                    cl_score += 30
                if cl.get("playback_url"):
                    cl_score += 15
                if cl_score > best_seg_score_for_rec:
                    best_seg_score_for_rec = cl_score

                scored_segments.append(
                    {
                        "score": round(cl_score + (title_score * 0.15), 1),
                        "video_id": rec["video_id"],
                        "video_title": rec["title"],
                        "canonical_url": rec["canonical_url"],
                        "record_path": rec["record_path"],
                        "notebook_source_id": rec["notebook_source_id"],
                        "segment_type": "VERIFIED_CLAIM",
                        "segment_id": f"CLAIM-{idx:02d}",
                        "chapter_title": cl["text"][:60],
                        "summary_ja": cl["text"],
                        "start_seconds": cl["timestamp_seconds"],
                        "end_seconds": None,
                        "start_mmss": cl["timestamp_mmss"],
                        "end_mmss": None,
                        "timestamp_source": cl["timestamp_source"],
                        "timestamp_basis": cl["timestamp_source"],
                        "verification_status": cl["status"],
                        "playback_url": cl["playback_url"],
                        "official_url": cl["official_url"],
                        "matched_terms": sorted(set(cl_matches)),
                    }
                )

        rec_total += best_seg_score_for_rec * 0.8
        all_matched_terms = sorted(set(m1 + m2 + m3 + m4 + m5 + m6))

        # 固有キーワードが存在するクエリで、汎用ストップワードのみに合致した誤検出を除外
        specific_raw_tokens = [tok for tok in raw_tokens if tok not in GENERIC_QUERY_TOKENS]
        if specific_raw_tokens and not is_explicit_vid:
            has_specific_match = any(
                tok in all_matched_terms or any(tok in m for m in all_matched_terms)
                for tok in specific_raw_tokens
            )
            if not has_specific_match:
                rec_total = 0

        if rec_total > 0 and (all_matched_terms or is_explicit_vid):
            chapters_list = rec.get("chapters", [])
            scored_records.append(
                {
                    "score": round(rec_total, 1),
                    "record_path": rec["record_path"],
                    "video_id": rec["video_id"],
                    "title": rec["title"],
                    "canonical_url": rec["canonical_url"],
                    "notebook_source_id": rec["notebook_source_id"],
                    "source_scope": rec["source_scope"],
                    "summary_ja": rec["summary_ja"],
                    "detailed_findings_ja": rec["detailed_findings_ja"],
                    "failure_and_limits_ja": rec["failure_and_limits_ja"],
                    "official_verification_ja": rec["official_verification_ja"],
                    "related_records": rec["related_records"],
                    "matched_terms": all_matched_terms,
                    "chapter_count": len(chapters_list),
                    "verified_chapter_count": sum(
                        1 for c in chapters_list if c.get("playback_url")
                    ),
                }
            )

    scored_records.sort(key=lambda x: (-x["score"], x["record_path"]))
    if scored_records and scored_records[0]["score"] >= 80:
        min_rec_score = scored_records[0]["score"] * 0.22
        scored_records = [r for r in scored_records if r["score"] >= min_rec_score]
    elif scored_records and scored_records[0]["score"] < 60 and not intent_info.get("explicit_video_ids"):
        # 固有クエリにもかかわらず十分な確信度がない（リポジトリ外技術の可能性）場合はゼロ件扱い
        scored_records = []

    if not scored_records:
        scored_segments = []
    else:
        valid_vids = {r.get("video_id") for r in scored_records if r.get("video_id")}
        valid_paths = {r.get("record_path") for r in scored_records if r.get("record_path")}
        scored_segments = [
            s for s in scored_segments
            if s.get("video_id") in valid_vids or s.get("record_path") in valid_paths
        ]

    scored_segments.sort(
        key=lambda x: (
            -x["score"],
            0 if x.get("playback_url") else 1,
            x.get("start_seconds") if x.get("start_seconds") is not None else 999999,
        )
    )
    if scored_segments and scored_segments[0]["score"] >= 45:
        min_seg_score = scored_segments[0]["score"] * 0.30
        scored_segments = [s for s in scored_segments if s["score"] >= min_seg_score]

    max_segs = max(top_k * 2, 6)
    diversified_segments = []
    overflow_segments = []
    per_vid_counts = {}
    for seg in scored_segments:
        vid_key = seg.get("video_id") or seg.get("record_path")
        cnt = per_vid_counts.get(vid_key, 0)
        if cnt < 2:
            diversified_segments.append(seg)
            per_vid_counts[vid_key] = cnt + 1
        else:
            overflow_segments.append(seg)
    final_segments = (diversified_segments + overflow_segments)[:max_segs]

    return scored_records[:top_k], final_segments


def recommend_notebook_lookup(matched_records, intent_info, catalog):
    """③ Gemini Notebook（元資料の図書館）で参照すべき詳細ソースと深掘り質問を生成する。"""
    notebook_sources = []
    seen_vids = set()
    for rec in matched_records:
        vid = rec.get("video_id")
        if vid and vid not in seen_vids:
            seen_vids.add(vid)
            notebook_sources.append(
                {
                    "video_id": vid,
                    "video_title": rec["title"],
                    "youtube_source_url": rec["canonical_url"],
                    "notebook_source_id": rec.get("notebook_source_id") or "UNKNOWN",
                    "recommended_notebook_card_title": f"動画研究カード_{vid}",
                }
            )

    q_orig = intent_info["original_query"]
    followup_prompt = (
        f"Notebook内の対象動画ソース（{', '.join(s['video_id'] for s in notebook_sources) or '登録済みソース'}）"
        f"および総合索引『AI技術研究室_知識索引.md』を参照し、次の質問に対する動画内の具体例・前後の文脈を"
        f"出典ソース名付きで詳しく教えてください：「{q_orig}」\n"
        f"※時刻がソース内で明示されている場合のみ時刻を記載し、不明な場合は推測せず UNKNOWN と記載してください。"
    )

    return {
        "notebook_url": catalog.get("notebook_url", DEFAULT_NOTEBOOK_URL),
        "notebook_master_index": "AI技術研究室_知識索引.md",
        "recommended_sources": notebook_sources,
        "recommended_notebook_prompt": followup_prompt,
    }


def detect_gaps_and_suggest_research(
    intent_info, matched_records, matched_segments, catalog
):
    """④ 既存知識で足りない点（知識ギャップ）を特定し、新しい動画・一次資料の追加調査候補を示す。"""
    verified_segments = [s for s in matched_segments if s.get("playback_url")]
    confirmed_doc_items = [
        s
        for s in matched_segments
        if "CONFIRMED_DOC" in str(s.get("verification_status", ""))
        or "CONFIRMED_TEST" in str(s.get("verification_status", ""))
    ]

    gaps = []
    suggested_queries = []
    q_orig = intent_info["original_query"]
    concepts = intent_info["matched_concepts"]

    if not matched_records:
        coverage_status = "INSUFFICIENT_NEEDS_NEW_RESEARCH"
        gaps.append(
            f"現在のGitHub研究台帳（全{catalog.get('total_records', 0)}件）に「{q_orig}」に直接合致する研究記録が存在しません。"
        )
        suggested_queries.append(
            f"YouTube / 公式ドキュメント新規調査候補: 「{q_orig} 公式ドキュメント アーキテクチャ 実装」"
        )
    else:
        if not verified_segments and "VIDEO_LOCATOR" in intent_info["intents"]:
            coverage_status = "PARTIAL_NO_VERIFIED_TIMESTAMPS"
            gaps.append(
                "関連する文書記録は見つかりましたが、確認済みタイムスタンプ（再生位置リンク）を持つ動画区間がまだ登録されていません。"
            )
        elif not confirmed_doc_items:
            coverage_status = "PARTIAL_VIDEO_REPORTED_NEEDS_PRIMARY_DOC"
            gaps.append(
                "動画内の発言・実演報告（VIDEO_REPORTED）は存在しますが、一部の効果数値や一般化可能性については公式一次資料・実測による裏付け（CONFIRMED_DOC / CONFIRMED_TEST）が未完了です。"
            )
        else:
            coverage_status = "SUFFICIENT_VERIFIED"

        # 既存記録内の「未確認事項・保留事項」から関連するものを抽出
        for rec in matched_records[:2]:
            if rec.get("failure_and_limits_ja"):
                for line in rec["failure_and_limits_ja"].splitlines():
                    if "UNKNOWN" in line or "未検証" in line or "未確認" in line:
                        clean_l = line.strip().lstrip("- ").strip()
                        if clean_l and clean_l not in gaps:
                            gaps.append(f"既存記録({rec['video_id'] or rec['record_path']})の未確認点: {clean_l}")

    if concepts:
        for c in concepts:
            suggested_queries.append(
                f"追加一次資料・動画調査テーマ: 『{c}』の最新公式仕様・具体的な失敗事例と決定論的テスト手法"
            )
    elif raw := intent_info.get("raw_tokens"):
        suggested_queries.append(
            f"追加一次資料・動画調査テーマ: 『{' '.join(raw[:4])}』に関する公式リファレンスと実践動画の収集"
        )

    return {
        "coverage_status": coverage_status,
        "identified_gaps": gaps[:5],
        "suggested_follow_up_research": suggested_queries[:4],
    }


def answer_question(query, root=ROOT, top_k=5):
    """質問回答・時刻付き動画箇所検索の統合パイプライン（①〜⑥）を実行する。"""
    catalog, parsed_records = build_video_knowledge_catalog(root=root)
    intent_info = analyze_query_intent(query)
    matched_records, matched_segments = search_github_knowledge(
        intent_info, parsed_records, top_k=top_k
    )
    notebook_guide = recommend_notebook_lookup(
        matched_records, intent_info, catalog
    )
    gap_analysis = detect_gaps_and_suggest_research(
        intent_info, matched_records, matched_segments, catalog
    )

    return {
        "schema_version": "research_qa_response_v1",
        "query": query,
        "step1_intent_analysis": intent_info,
        "step2_matched_records": matched_records,
        "step3_notebook_lookup": notebook_guide,
        "step4_gap_analysis": gap_analysis,
        "step5_and_6_recommended_video_segments": matched_segments,
    }


def format_qa_response_markdown(qa_res):
    """検索・回答結果（①〜⑥）を人間およびAIアシスタントが読みやすいMarkdown形式で出力する。"""
    intent = qa_res["step1_intent_analysis"]
    records = qa_res["step2_matched_records"]
    nb = qa_res["step3_notebook_lookup"]
    gaps = qa_res["step4_gap_analysis"]
    segments = qa_res["step5_and_6_recommended_video_segments"]

    lines = [
        "# AI技術研究室｜質問回答・時刻付き動画ガイド",
        "",
        f"- **質問**: {qa_res['query']}",
        f"- **① 意図解析 (`intents`)**: `{', '.join(intent['intents'])}`",
        f"- **検出された技術概念**: {', '.join(intent['matched_concepts']) if intent['matched_concepts'] else '（一般キーワード検索）'}",
        f"- **知識カバレッジ判定**: `{gaps['coverage_status']}`",
        "",
        "---",
        "",
        "## ⑤ 根拠付きの回答要約（GitHub正本・一次資料照合結果）",
        "",
    ]

    if not records:
        lines.append(
            "- 現在のGitHub正本（`research/*.md` / `notes/*.md`）に該当トピックの研究記録が見つかりませんでした。下の「④ 追加調査候補」を参照してください。"
        )
    else:
        for idx, rec in enumerate(records[:3], 1):
            vid_label = f"`{rec['video_id']}`" if rec.get("video_id") else "文書研究"
            lines.append(
                f"### {idx}. {rec['title']} ({vid_label} / `{rec['record_path']}`)"
            )
            if rec.get("summary_ja"):
                lines.append(f"- **概要要約**: {rec['summary_ja']}")
            if (
                "FAILURE_AND_LIMITS" in intent["intents"]
                and rec.get("failure_and_limits_ja")
            ):
                lines.append("- **確認されている失敗例・注意点・限界**:")
                for fl_line in rec["failure_and_limits_ja"].splitlines():
                    if fl_line.strip() and not fl_line.strip().startswith("["):
                        lines.append(f"  {fl_line.strip()}")
            elif rec.get("detailed_findings_ja"):
                lines.append("- **詳細技術知識・持ち帰り**:")
                for df_line in rec["detailed_findings_ja"].splitlines()[:8]:
                    if df_line.strip() and not df_line.strip().startswith("["):
                        lines.append(f"  {df_line.strip()}")
            if rec.get("official_verification_ja"):
                lines.append("- **一次資料・公式ドキュメント照合**:")
                for ov_line in rec["official_verification_ja"].splitlines()[:8]:
                    if ov_line.strip() and not ov_line.strip().startswith("["):
                        lines.append(f"  {ov_line.strip()}")
            lines.append("")

    lines += [
        "---",
        "",
        "## ⑥ 該当する動画の章・開始〜終了時刻・再生リンク",
        "",
        "> **時刻の信頼性ルール**: 時刻の根拠（`timestamp_source`）が確認できている区間のみ YouTube 再生リンク（`&t=XXs`）を生成しています。未確認の時刻は推測せず `UNKNOWN` と表示します。",
        "",
    ]

    if not segments:
        lines.append("- 該当する時刻付き動画区間はありません（`UNKNOWN`）。")
    else:
        lines.append(
            "| 優先度 | 動画ID / タイトル | 章・区間ID | 開始〜終了時刻 (再生リンク) | 時刻の確認根拠 (`timestamp_source`) | 検証状態 | 内容要約 |"
        )
        lines.append("|---|---|---|---|---|---|---|")
        for idx, seg in enumerate(segments[:6], 1):
            vid = seg.get("video_id") or "N/A"
            vtitle = seg.get("video_title", "")[:38]
            seg_id = seg.get("segment_id", "")
            start_mmss = seg.get("start_mmss") or "UNKNOWN"
            end_mmss = seg.get("end_mmss")
            time_range = (
                f"{start_mmss}〜{end_mmss}"
                if (start_mmss != "UNKNOWN" and end_mmss)
                else start_mmss
            )
            if seg.get("playback_url") and seg.get("timestamp_source") != "UNKNOWN":
                time_cell = f"[▶ {time_range}]({seg['playback_url']})"
            else:
                normal_url = seg.get("canonical_url") or (
                    f"https://www.youtube.com/watch?v={vid}" if vid != "N/A" else None
                )
                nb_src = seg.get("notebook_source_id") or "UNKNOWN"
                if normal_url:
                    time_cell = (
                        f"UNKNOWN (時刻未確認のため&t=リンク非生成 / "
                        f"[通常動画URL]({normal_url}) + Notebook `{nb_src}` 参照)"
                    )
                else:
                    time_cell = "UNKNOWN (時刻未確認のためリンク生成なし)"
            ts_src = seg.get("timestamp_source") or "UNKNOWN"
            v_status = seg.get("verification_status") or "UNKNOWN"
            summary = seg.get("summary_ja", "").replace("|", "｜")
            if seg.get("official_url"):
                summary += f" ([公式資料]({seg['official_url']}))"
            lines.append(
                f"| #{idx} (score:{seg['score']}) | `{vid}` {vtitle} | `{seg_id}` | {time_cell} | `{ts_src}` | `{v_status}` | {summary} |"
            )

    lines += [
        "",
        "---",
        "",
        "## ③ Gemini Notebook（元資料の図書館）での詳細参照ガイド",
        "",
        f"- **対象Notebook**: {nb['notebook_url']}",
        f"- **Notebook内総合索引**: `{nb['notebook_master_index']}`（※保護対象：削除・無断上書き禁止）",
    ]
    if nb["recommended_sources"]:
        lines.append("- **参照推奨ソース**:")
        for s in nb["recommended_sources"]:
            lines.append(
                f"  - 動画 `{s['video_id']}`: {s['youtube_source_url']} (Notebook source: `{s['notebook_source_id']}` / 研究カード: `{s['recommended_notebook_card_title']}`)"
            )
    lines += [
        "- **Notebookでの深掘り質問プロンプト例**:",
        f"  > {nb['recommended_notebook_prompt']}",
        "",
        "---",
        "",
        "## ④ 既存知識で未確認の点・追加調査候補",
        "",
    ]
    if gaps["identified_gaps"]:
        for g in gaps["identified_gaps"]:
            lines.append(f"- **未確認・課題**: {g}")
    else:
        lines.append("- 主要な一次資料確認と時刻付き区間の特定が完了しています。")

    for sq in gaps["suggested_follow_up_research"]:
        lines.append(f"- **次の調査候補**: {sq}")

    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    parser = argparse.ArgumentParser(
        description="Search GitHub research records & verified video timestamps, and answer natural-language questions."
    )
    parser.add_argument(
        "--query",
        "-q",
        help="Natural-language question (e.g., 'ハーネスって何？どの動画のどこを見ればいい？')",
    )
    parser.add_argument(
        "--build-catalog",
        action="store_true",
        help="Build and write `automation/gemini-notebook/state/video_knowledge_catalog.json`.",
    )
    parser.add_argument(
        "--catalog-path",
        default=str(DEFAULT_CATALOG_PATH),
        help="Output path for video_knowledge_catalog.json.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Maximum number of top records to return.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON response instead of Markdown.",
    )
    args = parser.parse_args(argv)

    if args.build_catalog:
        catalog, _ = build_video_knowledge_catalog(
            root=ROOT, write_path=Path(args.catalog_path)
        )
        if not args.query:
            print(
                json.dumps(
                    {
                        "status": "CATALOG_BUILT",
                        "catalog_path": str(args.catalog_path),
                        "total_records": catalog["total_records"],
                        "total_video_records": catalog["total_video_records"],
                        "total_verified_chapters": catalog["total_verified_chapters"],
                    },
                    ensure_ascii=False,
                )
            )
            return 0

    if not args.query:
        parser.error("Provide --query '...' or --build-catalog")

    qa_res = answer_question(args.query, root=ROOT, top_k=args.top_k)
    if args.json:
        print(json.dumps(qa_res, ensure_ascii=False, indent=2))
    else:
        print(format_qa_response_markdown(qa_res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
