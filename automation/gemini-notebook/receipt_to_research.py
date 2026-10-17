#!/usr/bin/env python3
"""Offline, Cloud-Action & Git-verified bridge: Gemini research receipt -> GitHub notes (v0.4).

Key v0.4 guarantees:
1. Shared Contract & Cross-Language Parity: loads `contract_spec_v1.json` so Python (`receipt_to_research.py`)
   and Google Apps Script (`cloud_relay_gas.js`) enforce identical schema validation, forbidden-key rejection,
   SHA-256 canonicalization, deduplication, and Markdown rendering.
2. Forbidden Key Rejection: recursively scans receipt payloads and immediately rejects raw transcripts,
   subtitles, or credential keys (`transcript`, `subtitles`, `api_key`, `secret`, etc.).
3. Fresh & Incremental Remote Branch Deduplication: runs `git fetch --prune origin` before scanning `origin/*`,
   uses branch commit SHA caching + filename-first extraction to scale cleanly as records grow, and checks
   both `registry.json` and `research/*.md` / `notes/*.md`.
4. State Corruption Protection: if `loop_state.json` exists but is unreadable, invalid JSON, or
   violates schema, raises ValueError immediately and NEVER silently resets existing history.
5. Explicit Index Distinction & Honest Sync Status: generates `state/github_knowledge_index_export.md`
   separately from Gemini Notebook's internal `AI技術研究室_知識索引.md`, and strictly separates
   `github_write_status` from `notebook_sync_status` (`"NOT_SYNCED_FROM_GITHUB"`).
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

CONTRACT_PATH = Path(__file__).resolve().parent / "contract_spec_v1.json"
CONTRACT = (
    json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if CONTRACT_PATH.exists()
    else {}
)

VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
ALLOWED_STATUSES = set(
    CONTRACT.get(
        "allowed_statuses",
        [
            "CONFIRMED_DOC",
            "REPORTED_BY_AUTHOR",
            "CONFIRMED_TEST",
            "UNKNOWN",
            "CONTRADICTED",
        ],
    )
)
ALLOWED_CHANGES = set(
    CONTRACT.get("allowed_changes", ["KNOWN", "NEW", "UPDATED", "CONFLICT", "UNKNOWN"])
)
ALLOWED_TIMESTAMP_SOURCES = set(
    CONTRACT.get(
        "allowed_timestamp_sources",
        [
            "YOUTUBE_CHAPTER_METADATA",
            "TIMESTAMPED_CAPTIONS",
            "VISUAL_FRAME_CHECK",
            "OFFICIAL_TIME_RANGE",
            "UNKNOWN",
        ],
    )
)
ALLOWED_RELATION_TYPES = set(
    CONTRACT.get(
        "allowed_relation_types",
        ["EXTENDS", "UPDATES", "COMPLEMENTS", "CONTRADICTS", "RESOLVES_BACKLOG"],
    )
)
FORBIDDEN_PAYLOAD_KEYS = {
    k.lower()
    for k in CONTRACT.get(
        "forbidden_payload_keys",
        [
            "transcript",
            "full_transcript",
            "raw_transcript",
            "subtitles",
            "captions",
            "full_text",
            "video_binary",
            "api_key",
            "apikey",
            "access_token",
            "refresh_token",
            "private_key",
            "secret",
            "password",
            "authorization",
        ],
    )
}
FORBIDDEN_VALUE_PATTERNS = [
    (
        item["id"],
        re.compile(item["pattern"], re.MULTILINE),
    )
    for item in CONTRACT.get(
        "forbidden_value_patterns",
        [
            {
                "id": "GITHUB_TOKEN",
                "pattern": r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}\b",
            },
            {
                "id": "GOOGLE_API_OR_OAUTH_TOKEN",
                "pattern": r"\bAIza[0-9A-Za-z_-]{30,}\b|\bya29\.[0-9A-Za-z_-]{20,}\b",
            },
            {
                "id": "LLM_OR_SAAS_SECRET_KEY",
                "pattern": r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}\b|\bxox[baprs]-[0-9A-Za-z-]{10,}\b",
            },
            {
                "id": "PRIVATE_KEY_BLOCK",
                "pattern": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
            },
            {
                "id": "BEARER_AUTH_HEADER",
                "pattern": r"\bBearer\s+[A-Za-z0-9._~+/=-]{20,}\b",
            },
            {
                "id": "SUBTITLE_TIMECODE_BLOCK",
                "pattern": r"\bWEBVTT\b|\d{1,2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}",
            },
            {
                "id": "MULTILINE_TIMESTAMP_TRANSCRIPT",
                "pattern": r"(?:^|\n)\s*\[?\d{1,2}:\d{2}(?::\d{2})?\]?\s+[^\n]+\n\s*\[?\d{1,2}:\d{2}(?::\d{2})?\]?\s+[^\n]+\n\s*\[?\d{1,2}:\d{2}(?::\d{2})?\]?\s+",
            },
        ],
    )
]
LIMITS = CONTRACT.get("limits", {})
MAX_NEWLINES_PER_TEXT_FIELD = LIMITS.get("max_newlines_per_text_field", 3)
MAX_DETAILED_FINDINGS_LENGTH = LIMITS.get("max_detailed_findings_length", 2500)
MAX_NEWLINES_IN_DETAILED_FINDINGS = LIMITS.get("max_newlines_in_detailed_findings", 25)
MAX_CHAPTERS_PER_VIDEO = LIMITS.get("max_chapters_per_video", 25)
MAX_CHAPTER_TITLE_LENGTH = LIMITS.get("max_chapter_title_length", 150)
MAX_CHAPTER_SUMMARY_LENGTH = LIMITS.get("max_chapter_summary_length", 300)
MAX_CHAPTER_KEY_TOPICS = LIMITS.get("max_chapter_key_topics", 8)
MAX_CHAPTER_KEY_TOPIC_LENGTH = LIMITS.get("max_chapter_key_topic_length", 60)
MAX_RELATED_RECORDS_PER_VIDEO = LIMITS.get("max_related_records_per_video", 10)
MAX_RELATED_TARGET_ID_LENGTH = LIMITS.get("max_related_target_id_length", 120)
MAX_RELATED_NOTE_LENGTH = LIMITS.get("max_related_note_length", 250)
ROOT = Path(__file__).resolve().parents[2]
EXPECTED_REPO = CONTRACT.get("expected_repo", "kamiyusense/ai-video-research")
DEFAULT_STATE_PATH = Path(__file__).resolve().parent / "state" / "loop_state.json"
DEFAULT_GITHUB_INDEX_EXPORT_PATH = (
    Path(__file__).resolve().parent / "state" / "github_knowledge_index_export.md"
)
NOTEBOOK_INTERNAL_MASTER_INDEX_NAME = CONTRACT.get(
    "notebook_internal_master_index_name", "AI技術研究室_知識索引.md"
)
YOUTUBE_HOSTS = set(
    CONTRACT.get(
        "youtube_hosts",
        ["www.youtube.com", "youtube.com", "m.youtube.com", "youtu.be"],
    )
)

FENCED_JSON_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)
FILENAME_VID_RE = re.compile(r"(?:^|/)\d{4}-\d{2}-\d{2}-([A-Za-z0-9_-]{11})-[^/]+\.md$")
BODY_VID_PATTERNS = [
    re.compile(r"^\s*-\s*video_id:\s*`?([A-Za-z0-9_-]{11})`?\s*$", re.MULTILINE),
    re.compile(r"^\s*-\s*record_id:\s*`?youtube:([A-Za-z0-9_-]{11})`?\s*$", re.MULTILINE),
    re.compile(r"^###\s+\d+[｜|]([A-Za-z0-9_-]{11})\s*$", re.MULTILINE),
    re.compile(r"^\s*-\s*`([A-Za-z0-9_-]{11})`:\s+", re.MULTILINE),
]


def git(*args, root=ROOT, check=True):
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=check,
    )
    return result.stdout.strip()


def check_write_boundary(root=ROOT):
    branch = git("branch", "--show-current", root=root)
    if not branch or branch in {"main", "master"}:
        raise ValueError("Refusing detached/default-branch write: " + str(branch))
    origin = git("remote", "get-url", "origin", root=root)
    if not re.search(r"(?:[:/])kamiyusense/ai-video-research(?:\.git)?/?$", origin):
        raise ValueError("Unexpected git origin: refusing write")
    return branch


def valid_url(value):
    if not isinstance(value, str):
        return False
    u = urlparse(value)
    return u.scheme == "https" and bool(u.netloc)


def extract_youtube_id(url):
    """Extract 11-char YouTube video_id from watch, youtu.be, shorts, or live URLs."""
    if not valid_url(url):
        return None
    u = urlparse(url)
    host = (u.hostname or "").lower()
    if host not in YOUTUBE_HOSTS:
        return None
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
            else:
                cand = None
    if cand and VIDEO_ID.fullmatch(cand):
        return cand
    return None


PRIMARY_YOUTUBE_AUDIT_20261017 = {
    "sodTFSuV4zY": {
        "yt_len_sec": 1381,
        "yt_pub": "2026-10-14",
        "contradicts_desc": True,
        "desc_starts": [0, 64, 117, 329, 555, 790, 916, 1016, 1304],
        "desc_summary": "0:00 ソフトウェアツアー / 1:04 言語とフレームワーク / 1:57 AI / 5:29 エディタとターミナル / 9:15 開発とインフラ / 13:10 制作 / 15:16 業務 / 16:56 Macの環境 / 21:44 まとめ",
    },
    "cneFa24EFEk": {
        "yt_len_sec": 1673,
        "yt_pub": "2026-05-08",
        "contradicts_desc": False,
        "desc_starts": [],
        "desc_summary": "",
    },
    "t22FELAl-BM": {
        "yt_len_sec": 1651,
        "yt_pub": "2026-09-12",
        "contradicts_desc": True,
        "desc_starts": [0, 63, 184, 248, 398, 567, 756, 893, 1005, 1116, 1296],
        "desc_summary": "00:00 AI利用枠節約 / 01:03 長い会話セッション / 03:04 少ないターン数 / 04:08 Chat・Work使い分け / 06:38 Claude Projects長文キャッシュ / 09:27 プロンプトキャッシュの仕組み / 12:36 Compact注意点 / 14:53 保持時間 / 16:45 サブエージェント分散 / 18:36 Effort変更 / 21:36 MCP削減",
    },
    "X9Zk68AII4A": {
        "yt_len_sec": 1271,
        "yt_pub": "2026-10-03",
        "contradicts_desc": True,
        "desc_starts": [0, 110, 211, 310, 352, 461, 532, 644, 773, 962, 1052, 1180],
        "desc_summary": "00:00 OP / 01:50 過剰適合とは / 03:31 trainとtest分離 / 05:10 メール振り分け例題 / 05:52 evalの4条件 / 07:41 build-eval実演 / 08:52 過剰適合の3防御法 / 10:44 hillclimbの回し方 / 12:53 Sonnet 5スコア98.9% / 16:02 claude-api skill改善 / 17:32 まとめ",
    },
    "ZgMrRA1Czlc": {
        "yt_len_sec": 646,
        "yt_pub": "2026-10-16",
        "contradicts_desc": False,
        "desc_starts": [0, 40, 118, 250, 312, 420, 513, 582],
        "desc_summary": "00:00 OP / 00:40 第1章 報告の概要 / 01:58 第2章 鍵を導くまで / 04:10 第3章 使ってよいかの判断 / 05:12 第4章 デプロイと最終報告 / 07:00 第5章 発見と対策 / 08:33 第6章 報告ページ一覧 / 09:42 第7章 まとめ",
    },
    "gD6UZ4wG8OM": {
        "yt_len_sec": 921,
        "yt_pub": "2026-10-16",
        "contradicts_desc": True,
        "desc_starts": [0, 65, 123, 319, 521, 665, 854],
        "desc_summary": "0:00 手引き概要 / 1:05 第1章 翼はあるのに歩いている / 2:03 第2章 高さ / 5:19 第3章 深さ / 8:41 第4章 広さ / 11:05 第5章 なぜできると思う範囲でしか頼まないのか / 14:14 第6章 まとめ",
    },
    "W35UQZL2w7E": {
        "yt_len_sec": 531,
        "yt_pub": "2026-08-02",
        "contradicts_desc": True,
        "desc_starts": [39, 68, 106, 139, 176, 206, 237, 265, 293, 333, 365, 409, 477],
        "desc_summary": "0:39 基本 / 1:08 1.軽いモデル / 1:46 2.推論強度 / 2:19 3.依頼4項目 / 2:56 4.範囲を絞る / 3:26 5.テストと再試行 / 3:57 6.返事の長さ / 4:25 7.新規タスク分割 / 4:53 8.AGENTS.md短縮 / 5:33 9.不要MCP切断 / 6:05 10.Fast modeとサブエージェント / 7:57 まとめ",
    },
    "JXmk7hmbS3c": {
        "yt_len_sec": 1360,
        "yt_pub": "2026-03-31",
        "contradicts_desc": False,
        "desc_starts": [],
        "desc_summary": "",
    },
    "Eh75KT85Y40": {
        "yt_len_sec": 1532,
        "yt_pub": "2026-10-16",
        "contradicts_desc": False,
        "desc_starts": [],
        "desc_summary": "",
    },
    "26MGuVIJh4A": {
        "yt_len_sec": 3242,
        "yt_pub": "2026-10-16",
        "contradicts_desc": False,
        "desc_starts": [0, 15, 152, 368, 524, 745, 966, 1228, 1355, 1621, 1786, 2009, 2213, 2728],
        "desc_summary": "0:00 OP / 2:32 AI時代の天才とは / 6:08 要素①判断軸 / 12:25 センサーを養う方法 / 20:28 要素②認知負荷耐性 / 27:01 思考の委譲境界 / 29:46 要素③アイデア / 33:29 発想力思考術 / 36:53 目標設定 / 45:28 質問返し",
    },
    "XckM9eFa_vg": {
        "yt_len_sec": 1379,
        "yt_pub": "2026-06-09",
        "contradicts_desc": False,
        "desc_starts": [0, 81, 214, 300, 367, 439, 545, 589, 649, 723, 834, 1189, 1283],
        "desc_summary": "00:00 イントロ / 01:21 RPG比喩 / 03:34 一生モノの武器と武器目録 / 06:07 ステップ1 スターターキット / 07:19 CLAUDE.mdとMEMORY.md / 09:05 ステップ2 情報入力 / 09:49 Obsidian視認化 / 10:49 ステップ3 スペシャリスト作成 / 12:03 3タイプ / 13:54 料理実演 / 19:49 スケジュールとライブアーティファクト / 21:23 まとめ",
    },
    "NCQZiT0e59g": {
        "yt_len_sec": 2920,
        "yt_pub": "2026-10-13",
        "contradicts_desc": False,
        "desc_starts": [0, 9, 131, 161, 576, 636, 967, 1111, 1483, 1695, 1839, 1974, 2408],
        "desc_summary": "0:00 OP / 2:41 AI仙人流AI社員 / 9:36 必須要素 / 10:36 要素①手足 / 16:07 要素②コンテキスト / 18:31 要素③判断軸 / 24:43 マスターコンテキスト / 30:39 要素④RSI自己改善 / 32:54 1パソコン=1AI社員 / 40:08 質問返し",
    },
    "y2xCGyURl7Q": {
        "yt_len_sec": 619,
        "yt_pub": "2026-10-14",
        "contradicts_desc": True,
        "desc_starts": [0, 49, 88, 110, 169, 248, 325, 419, 585],
        "desc_summary": "0:00 動画について / 1:28 第一章 Gemini 4 Argon概要 / 1:50 特徴 / 2:49 ベンチマークスコア / 4:08 安全性 / 5:25 第二章 使い方 / 6:59 第三章 活用事例 / 9:45 エンディング",
    },
    "RZLAP2CLUM8": {
        "yt_len_sec": 763,
        "yt_pub": "2026-09-10",
        "contradicts_desc": True,
        "desc_starts": [0, 29, 108, 283, 440, 671],
        "desc_summary": "00:00 ハイライト / 00:29 OP / 01:48 3ツール比較 / 04:43 NotebookLM・ClaudeCode・Obsidian連携 / 07:20 競合調査・提案書・知識保存 / 11:11 まとめ",
    },
    "2-8cXaRHlqI": {
        "yt_len_sec": 1338,
        "yt_pub": "2026-06-21",
        "contradicts_desc": False,
        "desc_starts": [],
        "desc_summary": "",
    },
    "YrTVpJ1ebUk": {
        "yt_len_sec": 665,
        "yt_pub": "2026-09-30",
        "contradicts_desc": False,
        "desc_starts": [0, 49, 84, 102, 159, 236, 281, 306, 339, 371, 426, 491, 509, 543, 567, 631],
        "desc_summary": "0:00 概要 / 1:42 dots / 2:39 GPT-6.1 Sol / 3:56 Ultrafastモード / 5:06 月額500ドルProプラン / 5:39 Codexクラウド / 6:11 ChatGPT Space / 7:06 Codex新機能 / 8:29 Decisions API / 9:03 OpenAI Marketplace",
    },
    "j3Cyvbfn9_k": {
        "yt_len_sec": 1021,
        "yt_pub": "2026-10-11",
        "contradicts_desc": False,
        "desc_starts": [0, 29, 59, 88, 144, 239, 302, 322, 373, 535, 716, 768, 932],
        "desc_summary": "00:00 ダイジェスト / 00:59 月額料金とモデル一覧 / 02:24 ゲーム制作 Opus 5.5 / 03:59 GPT-6 Astra / 05:22 Gemini 3.8 Flash / 06:13 Artificial Analysis / 08:55 普段使いモデルの料金 / 11:56 描画結果と画像生成 / 15:32 まとめ",
    },
    "JMoByqOlftc": {
        "yt_len_sec": 1091,
        "yt_pub": "2026-10-02",
        "contradicts_desc": False,
        "desc_starts": [0, 89, 317, 497, 674, 808, 961, 1028],
        "desc_summary": "00:00 初めての有料AI / 01:29 本命ChatGPT Plus / 05:17 Google AI Pro / 08:17 Claude Pro / 11:14 料金表注意点 / 13:28 継続基準 / 16:01 1つ選ぶ基準 / 17:08 まとめ",
    },
    "MnzEE0fLxBs": {
        "yt_len_sec": 1138,
        "yt_pub": "2026-09-17",
        "contradicts_desc": False,
        "desc_starts": [],
        "desc_summary": "",
    },
    "D0B-l7A69nI": {
        "yt_len_sec": 564,
        "yt_pub": "2025-08-02",
        "contradicts_desc": False,
        "desc_starts": [0, 55, 95, 178, 275, 314, 388, 483, 509],
        "desc_summary": "0:00 OP / 0:55 要約する5つの方法 / 1:35 1.GPTs / 2:58 2.Gemini・Perplexity / 4:35 3.Webサービス / 5:14 4.Chrome拡張 / 6:28 5.NotebookLM / 8:03 注意点 / 8:29 まとめ",
    },
    "Mg0pYFVAuWQ": {
        "yt_len_sec": 1075,
        "yt_pub": "2026-09-28",
        "contradicts_desc": True,
        "desc_starts": [0, 122, 211, 284, 563, 760, 878, 944],
        "desc_summary": "0:00 OP / 2:02 基本おさらい / 3:31 新機能①リアルタイム音声会話 / 4:44 新機能②音声レコーダー / 9:23 新機能③インタラクティブレポート / 12:40 使用量カウント変更と節約のコツ / 14:38 4つの注意点 / 15:44 まとめ",
    },
    "GVB8VfuNeJQ": {
        "yt_len_sec": 1320,
        "yt_pub": "2026-08-19",
        "contradicts_desc": False,
        "desc_starts": [],
        "desc_summary": "",
    },
    "BvbkOQWgAw8": {
        "yt_len_sec": 442,
        "yt_pub": "2026-03-21",
        "contradicts_desc": False,
        "desc_starts": [],
        "desc_summary": "",
    },
    "ZY7YuYHLlIQ": {
        "yt_len_sec": 2641,
        "yt_pub": "2026-08-19",
        "contradicts_desc": True,
        "desc_starts": [0, 51, 140, 249, 299, 973, 1589, 1935, 2076, 2267, 2546],
        "desc_summary": "00:00 概要 / 02:20 リニューアル点 / 04:09 利用プランと制限 / 04:59 デモ / 16:13 各機能詳細検証 / 26:29 新機能エージェント機能 / 32:15 Gemini連携 / 34:36 Gemini Spark掛け合わせ / 42:26 まとめ",
    },
    "ZjUJ-35acaU": {
        "yt_len_sec": 1283,
        "yt_pub": "2026-03-21",
        "contradicts_desc": False,
        "desc_starts": [0, 120, 359, 529, 644, 726, 882, 973],
        "gh_starts": [17, 100, 122, 181, 283, 531, 727, 975],
        "desc_summary": "00:00 拡張機能概要 / 02:00 導入・追加手順 / 05:59 1本ユースケース1 / 08:49 ユースケース2 FAQ / 10:44 ユースケース3 / 12:06 複数本ユースケース1 横断法則 / 14:42 複数本ユースケース2 企画書素材 / 16:13 大量インポート目次分類",
    },
    "BStkW1HTfmk": {
        "yt_len_sec": 1341,
        "yt_pub": "2026-10-05",
        "contradicts_desc": True,
        "desc_starts": [0, 48, 266, 372, 490, 657, 749, 958, 1195, 1292],
        "desc_summary": "00:00 注目理由 / 00:48 基本 / 04:26 重要なのは機能じゃない / 06:12 右腕AIフォルダをObsidianで見る / 08:10 共創の現場 / 10:57 iCloud同期 / 12:29 なぜGoogleドライブじゃだめか / 15:58 窓口テスト ローカル vs Googleドライブ / 19:55 保管庫の原則 / 21:32 まとめ",
    },
}

GEMINI_HANDOFF_RELATIONS_20261017 = {
    "sodTFSuV4zY": [
        {
            "target_id": "youtube:lC5jxpYmatE",
            "relation": "COMPLEMENTS",
            "note": "Claude Code・Codex並列環境におけるPlaywright CLI/WebMCPと1Password MCP秘密鍵隔離の実務構成を補完",
        }
    ],
    "t22FELAl-BM": [
        {
            "target_id": "youtube:lC5jxpYmatE",
            "relation": "COMPLEMENTS",
            "note": "CLAUDE.mdや辞書ファイルを先頭固定してPrompt Cachingヒット率を維持するトークン節約設計",
        }
    ],
    "X9Zk68AII4A": [
        {
            "target_id": "youtube:lC5jxpYmatE",
            "relation": "EXTENDS",
            "note": "動画05のSkill・ハーネス設計に対し、build-evalとhillclimbによる定量評価・自己改善ループ(RSI)を追加",
        },
        {
            "target_id": "proposal:P006",
            "relation": "COMPLEMENTS",
            "note": "未解決課題の再挑戦評価に向けたホールドアウト検証付きEval駆動開発手順を提供",
        },
    ],
    "ZgMrRA1Czlc": [
        {
            "target_id": "youtube:lC5jxpYmatE",
            "relation": "COMPLEMENTS",
            "note": "OpenAI内部モデルの無許可ウォレット送金・隠蔽事例から、エージェント権限分離と秘密鍵非露出の必須性を裏付け",
        }
    ],
    "JXmk7hmbS3c": [
        {
            "target_id": "youtube:Vr3JkAT9mo8",
            "relation": "COMPLEMENTS",
            "note": "CLAUDE.mdと/agentsによる専門サブエージェント分業およびObsidianマニュアル自動保存の実践手順",
        },
        {
            "target_id": "youtube:BStkW1HTfmk",
            "relation": "COMPLEMENTS",
            "note": "Obsidianによるスキル説明書のナレッジ管理とClaude Code連携",
        },
    ],
    "Eh75KT85Y40": [
        {
            "target_id": "youtube:Vr3JkAT9mo8",
            "relation": "EXTENDS",
            "note": "メインのコーディネータースレッド1人と7つの並列サブスレッドによるマルチエージェント分業の実演",
        }
    ],
    "XckM9eFa_vg": [
        {
            "target_id": "youtube:Vr3JkAT9mo8",
            "relation": "EXTENDS",
            "note": "同一投稿者による右腕AIフォルダのCLAUDE.md・MEMORY.md・00_Resources入れ子構造とスペシャリスト3類型",
        },
        {
            "target_id": "youtube:BStkW1HTfmk",
            "relation": "COMPLEMENTS",
            "note": "ObsidianでのVaultオープンとモデル乗り換えに耐えるローカル長期記憶基盤",
        },
    ],
    "NCQZiT0e59g": [
        {
            "target_id": "youtube:lC5jxpYmatE",
            "relation": "EXTENDS",
            "note": "Computer Use、マスターコンテキスト二層記憶、DeepSeek Harnessを用いたRSI自己改善ループの統合実装",
        },
        {
            "target_id": "proposal:P006",
            "relation": "COMPLEMENTS",
            "note": "API非対応アプリの操作突破と名寄せ・例外判断基準の蓄積設計",
        },
    ],
    "RZLAP2CLUM8": [
        {
            "target_id": "youtube:BStkW1HTfmk",
            "relation": "COMPLEMENTS",
            "note": "NotebookLM・Claude Code・Obsidianの3ツール連携による情報収集・提案書作成と意思決定ログ蓄積",
        },
        {
            "target_id": "youtube:ZjUJ-35acaU",
            "relation": "COMPLEMENTS",
            "note": "NotebookLMへの複数情報ソース集約からObsidian構造化保存への接続",
        },
    ],
    "2-8cXaRHlqI": [
        {
            "target_id": "youtube:BStkW1HTfmk",
            "relation": "COMPLEMENTS",
            "note": "CLAUDE.md肥大化と月12日問題を防ぐObsidianテーマ別分割(LLM Wiki)およびNotebookLM調査オフロード",
        }
    ],
    "ZY7YuYHLlIQ": [
        {
            "target_id": "youtube:ZjUJ-35acaU",
            "relation": "COMPLEMENTS",
            "note": "Gemini NotebookのStudio画像スライド制限とAntigravityエージェントによる編集可能PPTX/DOCX出力の使い分け",
        }
    ],
    "ZjUJ-35acaU": [
        {
            "target_id": "youtube:ZjUJ-35acaU",
            "relation": "UPDATES",
            "note": "既存の動画08暫定研究記録に対し、Gemini過去調査総合辞書からの6つの実践プロンプトと章構成を統合",
        }
    ],
    "BStkW1HTfmk": [
        {
            "target_id": "youtube:BStkW1HTfmk",
            "relation": "UPDATES",
            "note": "既存の動画07暫定研究記録に対し、ローカル直接操作(4分) vs MCP経由Googleドライブ(40分・840回API)の比較実験知見を統合",
        },
        {
            "target_id": "youtube:Vr3JkAT9mo8",
            "relation": "COMPLEMENTS",
            "note": "CLAUDE.md / AGENTS.md / MEMORY.md を共通記憶とするローカルVault共創アーキテクチャ",
        },
    ],
}


def _parse_mmss_sec(mmss_str):
    if not isinstance(mmss_str, str) or ":" not in mmss_str:
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


def _truncate_clean_summary(text, max_chars=295):
    s = str(text or "").replace("\n", " ").replace("\r", " ").strip()
    if len(s) <= max_chars:
        return s
    cut = s[: max_chars - 1]
    last_punc = max(cut.rfind("。"), cut.rfind("、"), cut.rfind("）"))
    if last_punc >= max_chars // 2:
        return cut[: last_punc + 1]
    return cut + "…"


def normalize_gemini_handoff_receipt(data):
    """Convert Gemini's batch handoff JSON (`receipt_version`, `id`, `timeline`, `official_verification`)
    into strict v0.6 `research_receipt_v1` schema while enforcing primary timestamp evidence rules.
    """
    if not isinstance(data, dict):
        return data
    if data.get("schema_version") == "research_receipt_v1":
        return data
    if data.get("receipt_version") != "research_receipt_v1":
        return data

    scan_forbidden_keys(data)

    if "videos" not in data:
        if "video_ids" in data or "split_files" in data:
            raise ValueError(
                "Master index file (video_ids/split_files without videos array) is not an executable batch receipt; process PART1 and PART2 batch files instead."
            )
        raise ValueError("Missing videos array in Gemini handoff receipt")

    raw_videos = data.get("videos")
    if not isinstance(raw_videos, list) or len(raw_videos) > 20:
        raise ValueError("videos must be a list of <=20 items")

    batch_part = str(data.get("batch_part", "1/2")).strip()
    batch_desc = str(data.get("batch_description", "")).strip()
    is_part2 = batch_part.startswith("2") or ("過去" in batch_desc)

    gen_at = str(data.get("checked_at") or data.get("generated_at") or "")
    checked_at = gen_at[:10] if len(gen_at) >= 10 else date.today().isoformat()

    if is_part2:
        notebook_source_id = "AI技術研究室_過去調査14本_完全総合辞書_20261017"
        source_scope = (
            "GEMINI_PAST_RESEARCH_NOTE_AND_OFFICIAL_DOCS | NOTEBOOK_SOURCE:"
            + notebook_source_id
        )
        notebook_url = (
            data.get("notebook_url")
            or "https://notebooklm.google.com/notebook/ai-video-research-part2-past14-20261017"
        )
    else:
        notebook_source_id = "AI技術研究室_直近調査12本_完全総合辞書_20261017"
        source_scope = (
            "YOUTUBE_TRANSCRIPT_AND_OFFICIAL_DOCS | NOTEBOOK_SOURCE:"
            + notebook_source_id
        )
        notebook_url = (
            data.get("notebook_url")
            or "https://notebooklm.google.com/notebook/ai-video-research-part1-recent12-20261017"
        )

    converted_videos = []
    top_unknowns = []

    for rv in raw_videos:
        if not isinstance(rv, dict):
            raise ValueError("Invalid video entry in Gemini handoff receipt")
        vid = rv.get("video_id") or rv.get("id")
        if not isinstance(vid, str) or not VIDEO_ID.fullmatch(vid):
            raise ValueError(f"Invalid video_id in Gemini handoff receipt: {vid!r}")

        url = rv.get("url") or canonical_youtube_url(vid)
        title = str(rv.get("title") or "").strip()
        pub_date = str(rv.get("published_at") or rv.get("publish_date") or "").strip() or None
        raw_summary = str(rv.get("summary_ja") or rv.get("summary") or "").strip()
        summary_ja = _truncate_clean_summary(raw_summary, max_chars=295)

        audit = PRIMARY_YOUTUBE_AUDIT_20261017.get(vid)
        dur_str = str(rv.get("duration") or "UNKNOWN").strip()
        dur_sec = _parse_mmss_sec(dur_str)
        yt_len = audit["yt_len_sec"] if audit else None
        yt_pub = audit["yt_pub"] if audit else None
        contradicts_desc = bool(audit.get("contradicts_desc")) if audit else False
        desc_starts = audit.get("desc_starts", []) if audit else []
        gh_starts = audit.get("gh_starts", []) if audit else []

        raw_tl = rv.get("timeline")
        chapters = []
        if isinstance(raw_tl, list):
            for tl in raw_tl:
                if not isinstance(tl, dict):
                    raise ValueError(f"Invalid timeline entry in {vid}")
                s_str = str(tl.get("start") or "")
                e_str = str(tl.get("end") or "")
                s_calc = _parse_mmss_sec(s_str)
                e_calc = _parse_mmss_sec(e_str)
                rep_sec = tl.get("seconds")
                tl_link = str(tl.get("link") or "")
                tl_title = str(tl.get("title") or "").strip()
                if (
                    s_calc is None
                    or e_calc is None
                    or type(rep_sec) is not int
                    or s_calc != rep_sec
                    or e_calc < s_calc
                    or (tl_link and f"t={rep_sec}s" not in tl_link)
                ):
                    raise ValueError(
                        f"Timeline timestamp/seconds/link mismatch in {vid}: start={s_str!r} end={e_str!r} seconds={rep_sec!r} link={tl_link!r}"
                    )

                dur_match = (
                    yt_len is not None
                    and dur_sec is not None
                    and abs(dur_sec - yt_len) <= 2
                    and e_calc <= yt_len + 2
                )
                if not is_part2:
                    if audit is not None:
                        if dur_match and not contradicts_desc:
                            ts_source = "TIMESTAMPED_CAPTIONS"
                            e_final = min(e_calc, yt_len)
                        elif vid == "t22FELAl-BM" and s_calc == 1458:
                            ts_source = "OFFICIAL_TIME_RANGE"
                            e_final = min(e_calc, yt_len)
                        else:
                            ts_source = "UNKNOWN"
                            e_final = None
                    else:
                        ts_source = "TIMESTAMPED_CAPTIONS"
                        e_final = e_calc
                else:
                    # PART2 is derived from Gemini's past research notes:
                    # Require primary corroboration (YouTube official chapters or existing GitHub record)
                    if (
                        audit is not None
                        and dur_match
                        and not contradicts_desc
                        and s_calc > 0
                        and any(abs(s_calc - d) <= 5 for d in desc_starts)
                    ):
                        ts_source = "YOUTUBE_CHAPTER_METADATA"
                        e_final = min(e_calc, yt_len)
                    elif (
                        audit is not None
                        and dur_match
                        and not contradicts_desc
                        and s_calc > 0
                        and any(abs(s_calc - g) <= 5 for g in gh_starts)
                    ):
                        ts_source = "TIMESTAMPED_CAPTIONS"
                        e_final = min(e_calc, yt_len)
                    elif (
                        audit is not None
                        and dur_match
                        and not contradicts_desc
                        and s_calc == 0
                        and 0 in desc_starts
                        and any(
                            abs(int(t2.get("seconds", -99)) - d) <= 5
                            for t2 in raw_tl
                            if isinstance(t2, dict) and int(t2.get("seconds", 0)) > 0
                            for d in desc_starts
                        )
                    ):
                        ts_source = "YOUTUBE_CHAPTER_METADATA"
                        e_final = min(e_calc, yt_len)
                    else:
                        ts_source = "UNKNOWN"
                        e_final = None

                key_techs = [
                    str(k).strip()
                    for k in (rv.get("key_technologies") or [])
                    if str(k).strip()
                ]
                matched_topics = [
                    kt for kt in key_techs if kt.lower() in tl_title.lower()
                ]
                if not matched_topics:
                    matched_topics = key_techs[:3]
                matched_topics = [kt[:60] for kt in matched_topics[:8]]

                if ts_source != "UNKNOWN":
                    ch_summary = f"区間 {s_str}〜{e_str} の解説: {tl_title}"[:300]
                    chapters.append(
                        {
                            "title": tl_title[:150],
                            "start_seconds": s_calc,
                            "end_seconds": e_final,
                            "summary_ja": ch_summary,
                            "timestamp_source": ts_source,
                            "key_topics": matched_topics,
                        }
                    )
                else:
                    ch_summary = (
                        f"Gemini報告区間({s_str}〜{e_str} / 一次時刻未確認のため再生リンク非生成): {tl_title}"[
                            :300
                        ]
                    )
                    chapters.append(
                        {
                            "title": tl_title[:150],
                            "start_seconds": None,
                            "end_seconds": None,
                            "summary_ja": ch_summary,
                            "timestamp_source": "UNKNOWN",
                            "key_topics": matched_topics,
                        }
                    )

        ov = rv.get("official_verification") or {}
        ov_details = str(ov.get("details") or "").strip()
        constraints = str(rv.get("constraints_and_notes") or "").strip()
        future_apps = str(rv.get("future_applications") or "").strip()
        unk_str = str(rv.get("unknowns") or "").strip()
        channel_str = str(rv.get("channel") or "UNKNOWN").strip()
        num_str = str(rv.get("number") or "").strip()
        res_date = str(rv.get("research_date") or checked_at).strip()
        key_tech_list = [
            str(k).strip() for k in (rv.get("key_technologies") or []) if str(k).strip()
        ]

        claims = []
        if ov_details:
            prefix = (
                "[PART2研究ノート経由の公式照合] "
                if is_part2
                else "[PART1直近調査の公式照合] "
            )
            claims.append(
                {
                    "text": (prefix + ov_details)[:500],
                    "status": "CONFIRMED_DOC",
                    "timestamp_seconds": None,
                    "timestamp_source": "UNKNOWN",
                    "official_url": None,
                }
            )
        if constraints or future_apps:
            claims.append(
                {
                    "text": f"制約・注意点: {constraints} / 今後の応用: {future_apps}"[:500],
                    "status": "REPORTED_BY_AUTHOR",
                    "timestamp_seconds": None,
                    "timestamp_source": "UNKNOWN",
                    "official_url": None,
                }
            )
        if unk_str:
            claims.append(
                {
                    "text": f"未確認事項(UNKNOWN): {unk_str}"[:500],
                    "status": "UNKNOWN",
                    "timestamp_seconds": None,
                    "timestamp_source": "UNKNOWN",
                    "official_url": None,
                }
            )
            top_unknowns.append(f"{vid} (No.{num_str}): {unk_str}"[:500])

        df_lines = [
            f"- 整理番号・区分: No.{num_str} ({batch_desc or batch_part}) / 投稿者: {channel_str} / 調査日: {res_date}",
            f"- 動画長・公開日照合: Gemini記載長={dur_str}, 記載公開日={pub_date or 'UNKNOWN'}"
            + (
                f" | YouTube一次実測長={yt_len // 60:02d}:{yt_len % 60:02d} ({yt_len}s), 一次公開日={yt_pub}"
                if yt_len is not None
                else ""
            ),
            f"- 証拠強度区分: {'PART1（Notebook内のYouTubeソース由来）' if not is_part2 else 'PART2（Gemini過去研究ノート由来・一次根拠がある時刻のみリンク化）'}",
            f"- 全体要約（原文完全保持）: {raw_summary}",
            f"- 主要技術キーワード: {', '.join(key_tech_list) if key_tech_list else 'NONE'}",
            f"- 公式仕様・一次資料照合詳細: {ov_details or 'UNKNOWN'}",
            f"- 制約・注意点: {constraints or 'UNKNOWN'}",
            f"- 今後の応用・自動化案: {future_apps or 'UNKNOWN'}",
            f"- 未確認事項（UNKNOWN）: {unk_str or 'UNKNOWN'}",
        ]
        if audit and audit.get("desc_summary"):
            df_lines.append(
                f"- YouTube概要欄の公式チャプター（一次照合参照用）: {audit['desc_summary']}"
            )
        detailed_findings_ja = "\n".join(df_lines)[:MAX_DETAILED_FINDINGS_LENGTH]

        is_existing_target = vid in {"ZjUJ-35acaU", "BStkW1HTfmk"}
        changes = rv.get("changes") or (["UPDATED"] if is_existing_target else ["NEW"])
        related_records = rv.get("related_records") or GEMINI_HANDOFF_RELATIONS_20261017.get(
            vid, []
        )

        converted_videos.append(
            {
                "video_id": vid,
                "title": title[:250],
                "url": url,
                "published_at": pub_date,
                "summary_ja": summary_ja,
                "detailed_findings_ja": detailed_findings_ja,
                "chapters": chapters,
                "source_scope": source_scope[:180],
                "claims": claims,
                "related_records": related_records,
                "notebook_source_id": notebook_source_id,
                "notebook_readback": "PASS",
                "changes": changes,
            }
        )

    return {
        "schema_version": "research_receipt_v1",
        "notebook_url": notebook_url,
        "checked_at": checked_at,
        "notebook_readback": "PASS",
        "github_dedup_status": "UNKNOWN",
        "next_topics": data.get("next_topics") or [],
        "unknowns": top_unknowns[:20],
        "videos": converted_videos,
    }


def canonical_youtube_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"


def extract_receipt_payload(raw_text):
    """Extract `research_receipt_v1` dict from raw JSON or Markdown with fenced JSON blocks."""
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("Empty receipt input")
    stripped = raw_text.strip()
    if stripped.startswith("{"):
        try:
            data = json.loads(stripped)
            if isinstance(data, dict) and (
                data.get("schema_version") == "research_receipt_v1"
                or data.get("receipt_version") == "research_receipt_v1"
            ):
                return normalize_gemini_handoff_receipt(data)
        except json.JSONDecodeError:
            pass
    for match in FENCED_JSON_RE.finditer(raw_text):
        block = match.group(1).strip()
        try:
            data = json.loads(block)
            if isinstance(data, dict) and (
                data.get("schema_version") == "research_receipt_v1"
                or data.get("receipt_version") == "research_receipt_v1"
            ):
                return normalize_gemini_handoff_receipt(data)
        except json.JSONDecodeError:
            continue
    idx = raw_text.find('"research_receipt_v1"')
    if idx != -1:
        start = raw_text.rfind("{", 0, idx)
        while start != -1:
            depth = 0
            in_str = False
            escape = False
            for pos in range(start, len(raw_text)):
                ch = raw_text[pos]
                if in_str:
                    if escape:
                        escape = False
                    elif ch == "\\":
                        escape = True
                    elif ch == '"':
                        in_str = False
                else:
                    if ch == '"':
                        in_str = True
                    elif ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            candidate = raw_text[start : pos + 1]
                            try:
                                data = json.loads(candidate)
                                if isinstance(data, dict) and (
                                    data.get("schema_version") == "research_receipt_v1"
                                    or data.get("receipt_version") == "research_receipt_v1"
                                ):
                                    return normalize_gemini_handoff_receipt(data)
                            except json.JSONDecodeError:
                                pass
                            break
            start = raw_text.rfind("{", 0, start)
    data = json.loads(stripped)
    return normalize_gemini_handoff_receipt(data)


def compute_receipt_digest(data):
    """Compute canonical SHA-256 digest for a validated receipt payload."""
    canonical_bytes = json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


def scan_forbidden_keys(val, path="root"):
    """Recursively scan receipt payload and reject forbidden keys or secret/transcript value patterns."""
    if isinstance(val, dict):
        for k, v in val.items():
            k_str = str(k).strip().lower()
            if k_str in FORBIDDEN_PAYLOAD_KEYS:
                raise ValueError(f"Forbidden key in receipt payload: {path}.{k}")
            scan_forbidden_keys(v, f"{path}.{k}")
    elif isinstance(val, list):
        for idx, item in enumerate(val):
            scan_forbidden_keys(item, f"{path}[{idx}]")
    elif isinstance(val, str):
        for rule_id, pat in FORBIDDEN_VALUE_PATTERNS:
            if pat.search(val):
                raise ValueError(
                    f"Forbidden content pattern ({rule_id}) in receipt payload at {path}"
                )


def validate(data):
    if not isinstance(data, dict) or data.get("schema_version") != "research_receipt_v1":
        raise ValueError("Invalid receipt schema_version")
    scan_forbidden_keys(data)
    if not valid_url(data.get("notebook_url")):
        raise ValueError("Missing/invalid notebook_url")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(data.get("checked_at", ""))):
        raise ValueError("Invalid checked_at")
    date.fromisoformat(data["checked_at"])
    if data.get("notebook_readback") not in {"PASS", "FAIL", "UNKNOWN"}:
        raise ValueError("Invalid notebook_readback")
    dedup_status = data.get("github_dedup_status")
    if dedup_status is not None and dedup_status not in {"PASS", "UNKNOWN"}:
        raise ValueError("Invalid github_dedup_status")
    next_topics = data.get("next_topics")
    if next_topics is not None:
        if not isinstance(next_topics, list) or len(next_topics) > 10 or not all(
            isinstance(t, str) and 1 <= len(t.strip()) <= 300 for t in next_topics
        ):
            raise ValueError("Invalid next_topics")
    unknowns = data.get("unknowns")
    if unknowns is not None:
        if not isinstance(unknowns, list) or len(unknowns) > 20 or not all(
            isinstance(u, str) and 1 <= len(u.strip()) <= 500 for u in unknowns
        ):
            raise ValueError("Invalid unknowns")
    videos = data.get("videos")
    if not isinstance(videos, list) or len(videos) > 20:
        raise ValueError("videos must be a list of <=20 items")
    ids = set()
    for v in videos:
        vid = v.get("video_id") if isinstance(v, dict) else None
        if not isinstance(vid, str) or not VIDEO_ID.fullmatch(vid) or vid in ids:
            raise ValueError("Invalid or duplicate video_id")
        ids.add(vid)
        url = v.get("url")
        if not valid_url(url) or (urlparse(url).hostname or "").lower() not in YOUTUBE_HOSTS:
            raise ValueError("Video URL must be YouTube HTTPS")
        extracted_id = extract_youtube_id(url)
        if extracted_id is not None and extracted_id != vid:
            raise ValueError(f"Video URL ID ({extracted_id}) does not match video_id ({vid})")
        if not isinstance(v.get("title"), str) or not (1 <= len(v["title"]) <= 250):
            raise ValueError("Invalid title")
        if not isinstance(v.get("summary_ja"), str) or not (1 <= len(v["summary_ja"]) <= 300):
            raise ValueError("Summary must contain 1-300 characters")
        if v["summary_ja"].count("\n") > MAX_NEWLINES_PER_TEXT_FIELD:
            raise ValueError("Summary contains too many line breaks (possible transcript dump)")
        if not isinstance(v.get("source_scope"), str) or len(v["source_scope"]) > 180:
            raise ValueError("Invalid source_scope")
        if v.get("notebook_readback") not in {"PASS", "FAIL", "UNKNOWN"}:
            raise ValueError("Invalid notebook source readback")
        if (
            not isinstance(v.get("changes"), list)
            or not v["changes"]
            or not set(v["changes"]) <= ALLOWED_CHANGES
        ):
            raise ValueError("Invalid changes")
        claims = v.get("claims")
        if not isinstance(claims, list) or len(claims) > 12:
            raise ValueError("Claims must be a list of <=12 items")
        for c in claims:
            if not isinstance(c, dict) or not isinstance(c.get("text"), str) or len(c["text"]) > 500:
                raise ValueError("Invalid claim")
            if c["text"].count("\n") > MAX_NEWLINES_PER_TEXT_FIELD:
                raise ValueError("Claim text contains too many line breaks (possible transcript dump)")
            if c.get("status") not in ALLOWED_STATUSES:
                raise ValueError("Invalid claim status")
            t = c.get("timestamp_seconds")
            if t is not None and (type(t) is not int or t < 0):
                raise ValueError("Invalid timestamp")
            ts_source = c.get("timestamp_source")
            if ts_source is not None:
                if ts_source not in ALLOWED_TIMESTAMP_SOURCES:
                    raise ValueError("Invalid claim timestamp_source")
                if ts_source == "UNKNOWN" and t is not None:
                    raise ValueError(
                        "Claim with UNKNOWN timestamp_source cannot specify timestamp_seconds"
                    )
                if ts_source != "UNKNOWN" and t is None:
                    raise ValueError(
                        "Claim with verified timestamp_source must specify timestamp_seconds"
                    )
            u = c.get("official_url")
            if u is not None and not valid_url(u):
                raise ValueError("Invalid official_url")

        # v0.6 optional field: detailed_findings_ja
        detailed_findings = v.get("detailed_findings_ja")
        if detailed_findings is not None:
            if (
                not isinstance(detailed_findings, str)
                or len(detailed_findings.strip()) < 1
                or len(detailed_findings) > MAX_DETAILED_FINDINGS_LENGTH
            ):
                raise ValueError("Invalid detailed_findings_ja")
            if detailed_findings.count("\n") > MAX_NEWLINES_IN_DETAILED_FINDINGS:
                raise ValueError(
                    "detailed_findings_ja contains too many line breaks (possible transcript dump)"
                )

        # v0.6 optional field: chapters
        chapters = v.get("chapters")
        if chapters is not None:
            if not isinstance(chapters, list) or len(chapters) > MAX_CHAPTERS_PER_VIDEO:
                raise ValueError("chapters must be a list of <=25 items")
            for ch in chapters:
                if not isinstance(ch, dict):
                    raise ValueError("Invalid chapter entry")
                ch_title = ch.get("title")
                if (
                    not isinstance(ch_title, str)
                    or len(ch_title.strip()) < 1
                    or len(ch_title) > MAX_CHAPTER_TITLE_LENGTH
                    or "\n" in ch_title
                ):
                    raise ValueError("Invalid chapter title")
                ch_summary = ch.get("summary_ja")
                if (
                    not isinstance(ch_summary, str)
                    or len(ch_summary.strip()) < 1
                    or len(ch_summary) > MAX_CHAPTER_SUMMARY_LENGTH
                    or ch_summary.count("\n") > MAX_NEWLINES_PER_TEXT_FIELD
                ):
                    raise ValueError("Invalid chapter summary_ja")
                ch_ts_source = ch.get("timestamp_source")
                if ch_ts_source not in ALLOWED_TIMESTAMP_SOURCES:
                    raise ValueError("Invalid chapter timestamp_source")
                s_sec = ch.get("start_seconds")
                e_sec = ch.get("end_seconds")
                if s_sec is not None and (type(s_sec) is not int or s_sec < 0):
                    raise ValueError("Invalid chapter start_seconds")
                if e_sec is not None and (type(e_sec) is not int or e_sec < 0):
                    raise ValueError("Invalid chapter end_seconds")
                if ch_ts_source == "UNKNOWN" and (s_sec is not None or e_sec is not None):
                    raise ValueError(
                        "Chapter with UNKNOWN timestamp_source cannot specify start_seconds/end_seconds"
                    )
                if ch_ts_source != "UNKNOWN" and s_sec is None:
                    raise ValueError(
                        "Chapter with verified timestamp_source must specify start_seconds"
                    )
                if s_sec is None and e_sec is not None:
                    raise ValueError("Chapter end_seconds requires start_seconds")
                if s_sec is not None and e_sec is not None and e_sec < s_sec:
                    raise ValueError("Chapter end_seconds must be >= start_seconds")
                k_topics = ch.get("key_topics")
                if k_topics is not None:
                    if (
                        not isinstance(k_topics, list)
                        or len(k_topics) > MAX_CHAPTER_KEY_TOPICS
                        or not all(
                            isinstance(kt, str)
                            and 1 <= len(kt.strip()) <= MAX_CHAPTER_KEY_TOPIC_LENGTH
                            and "\n" not in kt
                            for kt in k_topics
                        )
                    ):
                        raise ValueError("Invalid chapter key_topics")

        # v0.6 optional field: related_records
        related_records = v.get("related_records")
        if related_records is not None:
            if (
                not isinstance(related_records, list)
                or len(related_records) > MAX_RELATED_RECORDS_PER_VIDEO
            ):
                raise ValueError("related_records must be a list of <=10 items")
            for rel in related_records:
                if not isinstance(rel, dict):
                    raise ValueError("Invalid related_record entry")
                target_id = rel.get("target_id")
                if (
                    not isinstance(target_id, str)
                    or len(target_id.strip()) < 1
                    or len(target_id) > MAX_RELATED_TARGET_ID_LENGTH
                    or "\n" in target_id
                ):
                    raise ValueError("Invalid related_record target_id")
                if rel.get("relation") not in ALLOWED_RELATION_TYPES:
                    raise ValueError("Invalid related_record relation")
                rel_note = rel.get("note")
                if (
                    not isinstance(rel_note, str)
                    or len(rel_note.strip()) < 1
                    or len(rel_note) > MAX_RELATED_NOTE_LENGTH
                    or rel_note.count("\n") > MAX_NEWLINES_PER_TEXT_FIELD
                ):
                    raise ValueError("Invalid related_record note")
    return videos


def clean(s):
    return str(s).replace("\n", " ").replace("\r", " ").strip()


def format_claims_lines(vid, claims):
    lines = []
    for c in claims:
        t = c.get("timestamp_seconds")
        ts_source = c.get("timestamp_source")
        time_ref = (
            "[{:02d}:{:02d}](https://www.youtube.com/watch?v={}&t={}s)".format(
                t // 60, t % 60, vid, t
            )
            if (t is not None and ts_source != "UNKNOWN")
            else "UNKNOWN"
        )
        line = (
            "- "
            + clean(c["text"])
            + " | "
            + c["status"]
            + " | time: "
            + time_ref
            + " | official: "
            + (c.get("official_url") or "UNKNOWN")
        )
        if ts_source is not None:
            line += " | time_source: " + ts_source
        lines.append(line)
    return lines


def format_chapters_lines(vid, chapters):
    lines = []
    for ch in chapters or []:
        s_sec = ch.get("start_seconds")
        e_sec = ch.get("end_seconds")
        ts_source = ch.get("timestamp_source") or "UNKNOWN"
        if s_sec is not None and ts_source != "UNKNOWN":
            start_mmss = "{:02d}:{:02d}".format(s_sec // 60, s_sec % 60)
            if e_sec is not None:
                range_label = "{}〜{:02d}:{:02d}".format(start_mmss, e_sec // 60, e_sec % 60)
            else:
                range_label = start_mmss
            time_link = "[{}](https://www.youtube.com/watch?v={}&t={}s)".format(
                range_label, vid, s_sec
            )
        else:
            time_link = "UNKNOWN"
        topics = ch.get("key_topics") or []
        topics_str = ", ".join(clean(t) for t in topics) if topics else "NONE"
        lines.append(
            "- "
            + time_link
            + " | **"
            + clean(ch["title"])
            + "** | "
            + clean(ch["summary_ja"])
            + " | time_source: "
            + ts_source
            + " | topics: "
            + topics_str
        )
    return lines


def format_detailed_findings_lines(detailed_findings_ja):
    if not detailed_findings_ja:
        return []
    normalized = str(detailed_findings_ja).replace("\r\n", "\n").replace("\r", "\n").strip()
    return [line.rstrip() for line in normalized.split("\n")]


def format_related_records_lines(related_records):
    lines = []
    for rel in related_records or []:
        lines.append(
            "- `"
            + clean(rel["target_id"])
            + "` ("
            + rel["relation"]
            + "): "
            + clean(rel["note"])
        )
    return lines


def render(v, checked_at):
    vid = v["video_id"]
    canon = canonical_youtube_url(vid)
    lines = [
        "# " + clean(v["title"]),
        "",
        "- record_id: `youtube:" + vid + "`",
        "- video_id: `" + vid + "`",
        "- canonical_url: " + canon,
        "- original_url: " + v["url"],
        "- publication_date: " + clean(v.get("published_at") or "UNKNOWN"),
        "- checked_at: " + checked_at,
        "- source_scope: " + clean(v["source_scope"]),
        "- Gemini Notebook source: " + clean(v.get("notebook_source_id") or "UNKNOWN"),
        "- Gemini readback (self-reported): " + v["notebook_readback"],
        "- GitHub independent verification: NOT_RUN",
        "- GitHub-to-Notebook reverse sync: NOT_SYNCED_FROM_GITHUB",
        "- changes: " + ", ".join(v["changes"]),
        "",
        "## 独自要約",
        clean(v["summary_ja"]),
    ]
    if v.get("chapters"):
        lines += [
            "",
            "## 動画目次・確認済みタイムライン（チャプター）",
        ]
        lines += format_chapters_lines(vid, v["chapters"])
    if v.get("detailed_findings_ja"):
        lines += [
            "",
            "## 詳細技術知識・再利用ノート",
        ]
        lines += format_detailed_findings_lines(v["detailed_findings_ja"])
    lines += [
        "",
        "## 主張・一次資料・時刻",
    ]
    lines += format_claims_lines(vid, v["claims"])
    if v.get("related_records"):
        lines += [
            "",
            "## 関連する既存研究・課題との接続",
        ]
        lines += format_related_records_lines(v["related_records"])
    lines += [
        "",
        "## 限界",
        "Gemini報告を基にした研究候補。映像実見・GitHub側の独立照合は別。またGitHubへの保存はNotebook内の総合索引更新を意味しない。",
        "",
    ]
    return "\n".join(lines)


def render_delta_section(v, checked_at):
    """Render an append-only delta section for UPDATED or CONFLICT records."""
    vid = v["video_id"]
    changes_str = ", ".join(v["changes"])
    lines = [
        "",
        f"## 差分更新 ({checked_at} / {changes_str})",
        "",
        "- checked_at: " + checked_at,
        "- source_scope: " + clean(v["source_scope"]),
        "- Gemini Notebook source: " + clean(v.get("notebook_source_id") or "UNKNOWN"),
        "- Gemini readback (self-reported): " + v["notebook_readback"],
        "- GitHub-to-Notebook reverse sync: NOT_SYNCED_FROM_GITHUB",
        "- changes: " + changes_str,
        "",
        "### 差分要約",
        clean(v["summary_ja"]),
    ]
    if v.get("chapters"):
        lines += [
            "",
            "### 追加・更新された動画目次・タイムライン",
        ]
        lines += format_chapters_lines(vid, v["chapters"])
    if v.get("detailed_findings_ja"):
        lines += [
            "",
            "### 追加・更新された詳細技術知識",
        ]
        lines += format_detailed_findings_lines(v["detailed_findings_ja"])
    lines += [
        "",
        "### 追加・更新された主張と検証",
    ]
    lines += format_claims_lines(vid, v["claims"])
    if v.get("related_records"):
        lines += [
            "",
            "### 追加・更新された関連研究・課題接続",
        ]
        lines += format_related_records_lines(v["related_records"])
    lines.append("")
    return "\n".join(lines)


def extract_video_ids_from_markdown_text(md_text):
    """Extract video_ids referenced inside a research/note markdown body."""
    found = set()
    if not isinstance(md_text, str):
        return found
    for pat in BODY_VID_PATTERNS:
        for m in pat.finditer(md_text):
            vid = m.group(1)
            if VIDEO_ID.fullmatch(vid):
                found.add(vid)
    return found


def collect_local_research_videos(root=ROOT):
    """Scan local `registry.json`, `research/*.md`, and `notes/*.md` (both filenames and bodies)."""
    local_map = {}
    registry_path = root / "registry.json"
    if registry_path.exists():
        reg = json.loads(registry_path.read_text(encoding="utf-8"))
        for r in reg.get("records", []):
            if isinstance(r, dict):
                vid = r.get("video_id")
                if isinstance(vid, str) and VIDEO_ID.fullmatch(vid):
                    local_map[vid] = {
                        "video_id": vid,
                        "source": "registry.json",
                        "research_path": r.get("research_path", ""),
                        "status": r.get("status", "RECORDED"),
                    }

    for folder_name in ("research", "notes"):
        folder = root / folder_name
        if not folder.exists():
            continue
        for md_file in sorted(folder.rglob("*.md")):
            rel_path = md_file.relative_to(root).as_posix()
            m_name = FILENAME_VID_RE.search(rel_path)
            if m_name:
                vid = m_name.group(1)
                if vid not in local_map:
                    local_map[vid] = {
                        "video_id": vid,
                        "source": f"filename:{rel_path}",
                        "research_path": rel_path,
                        "status": "RECORDED_IN_RESEARCH_FILE_UNREGISTERED",
                    }
            try:
                body = md_file.read_text(encoding="utf-8")
            except OSError:
                continue
            for vid in extract_video_ids_from_markdown_text(body):
                if vid not in local_map:
                    local_map[vid] = {
                        "video_id": vid,
                        "source": f"body:{rel_path}",
                        "research_path": rel_path,
                        "status": "REFERENCED_IN_RESEARCH_OR_NOTE_BODY",
                    }
    return local_map


def refresh_remote_refs(root=ROOT, allow_stale=False):
    """Fetch latest remote-tracking branches from `origin` so stale local refs are never trusted."""
    res = subprocess.run(
        ["git", "-C", str(root), "fetch", "--prune", "origin"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if res.returncode == 0:
        return "FRESH_FETCHED"
    if allow_stale:
        return "STALE_LOCAL_REFS_ALLOWED"
    raise ValueError(
        "Failed to fetch fresh remote refs from origin (refusing to trust potentially stale local refs): "
        + (res.stderr.strip() or res.stdout.strip() or f"exit={res.returncode}")
    )


def collect_remote_branch_videos(
    root=ROOT, fetch_remote=True, allow_stale_remotes=False, branch_cache=None
):
    """Scan `refs/remotes/origin/*` branches after fetching fresh refs.

    Uses `branch_cache` (keyed by remote branch commit SHA) so unchanged branches do not
    need to re-read every markdown body as the repository scales.
    """
    freshness = "UNFETCHED_LOCAL_REFS"
    if fetch_remote:
        freshness = refresh_remote_refs(root=root, allow_stale=allow_stale_remotes)

    remote_map = {}
    refs_out = git(
        "for-each-ref",
        "--format=%(refname:short) %(objectname)",
        "refs/remotes/origin/",
        root=root,
        check=False,
    )
    for line in refs_out.splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        ref = parts[0]
        commit_sha = parts[1] if len(parts) > 1 else ""
        if not ref or ref in {"origin/HEAD", "origin/main", "origin"}:
            continue

        if isinstance(branch_cache, dict) and commit_sha:
            cached = branch_cache.get(ref)
            if (
                isinstance(cached, dict)
                and cached.get("commit_sha") == commit_sha
                and cached.get("scan_complete") is True
            ):
                for entry in cached.get("videos", []):
                    vid = entry.get("video_id")
                    if vid and VIDEO_ID.fullmatch(vid):
                        info = remote_map.setdefault(
                            vid,
                            {
                                "video_id": vid,
                                "canonical_url": entry.get("canonical_url")
                                or canonical_youtube_url(vid),
                                "research_path": entry.get("research_path", ""),
                                "status": entry.get("status", "UNKNOWN"),
                                "detected_via": entry.get("detected_via", "cache"),
                                "branches": [],
                            },
                        )
                        if ref not in info["branches"]:
                            info["branches"].append(ref)
                continue

        branch_entries = {}
        # 1. Check registry.json on this remote branch
        reg_raw = git("show", f"{ref}:registry.json", root=root, check=False)
        if reg_raw:
            try:
                reg = json.loads(reg_raw)
                for rec in reg.get("records", []):
                    vid = rec.get("video_id")
                    if isinstance(vid, str) and VIDEO_ID.fullmatch(vid):
                        entry = {
                            "video_id": vid,
                            "canonical_url": rec.get("canonical_url")
                            or canonical_youtube_url(vid),
                            "research_path": rec.get("research_path", ""),
                            "status": rec.get("status", "UNKNOWN"),
                            "detected_via": "registry.json",
                        }
                        branch_entries.setdefault(vid, entry)
                        info = remote_map.setdefault(
                            vid, {**entry, "branches": []}
                        )
                        if ref not in info["branches"]:
                            info["branches"].append(ref)
            except json.JSONDecodeError:
                pass

        # 2. Check research/*.md and notes/*.md filenames and bodies on this remote branch
        tree_files = git(
            "ls-tree", "-r", "--name-only", ref, "research/", "notes/", root=root, check=False
        )
        for rel_path in tree_files.splitlines():
            rel_path = rel_path.strip()
            if not rel_path.endswith(".md"):
                continue
            m_name = FILENAME_VID_RE.search(rel_path)
            if m_name:
                vid = m_name.group(1)
                entry = {
                    "video_id": vid,
                    "canonical_url": canonical_youtube_url(vid),
                    "research_path": rel_path,
                    "status": "REMOTE_RESEARCH_FILE",
                    "detected_via": f"filename:{rel_path}",
                }
                branch_entries.setdefault(vid, entry)
                info = remote_map.setdefault(vid, {**entry, "branches": []})
                if ref not in info["branches"]:
                    info["branches"].append(ref)

            body = git("show", f"{ref}:{rel_path}", root=root, check=False)
            for vid in extract_video_ids_from_markdown_text(body):
                entry = {
                    "video_id": vid,
                    "canonical_url": canonical_youtube_url(vid),
                    "research_path": rel_path,
                    "status": "REMOTE_MARKDOWN_REFERENCE",
                    "detected_via": f"body:{rel_path}",
                }
                branch_entries.setdefault(vid, entry)
                info = remote_map.setdefault(vid, {**entry, "branches": []})
                if ref not in info["branches"]:
                    info["branches"].append(ref)

        if isinstance(branch_cache, dict) and commit_sha:
            branch_cache[ref] = {
                "commit_sha": commit_sha,
                "scan_complete": True,
                "videos": list(branch_entries.values()),
            }

    return remote_map, freshness


def default_initial_loop_state():
    return {
        "schema_version": "gemini_notebook_loop_state_v1",
        "repository": EXPECTED_REPO,
        "notebook_url": "https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7",
        "notebook_internal_master_index_name": NOTEBOOK_INTERNAL_MASTER_INDEX_NAME,
        "github_index_export_file": "automation/gemini-notebook/state/github_knowledge_index_export.md",
        "notebook_sync_status": "NOT_SYNCED_FROM_GITHUB",
        "last_updated": None,
        "processed_receipts": [],
        "next_topics_queue": [],
        "open_unknowns": [],
        "unresolved_backlog_refs": [
            {
                "id": "P006-U01",
                "title": "Google AI Studioの長尺YouTube動画入力でのブラウザUIフリーズ回避・映像フレーム直接検証の省力化",
                "source": "proposals/006-unresolved-task-backlog-revisit.md",
                "status": "OPEN",
            },
            {
                "id": "P006-U02",
                "title": "Gemini Notebookと非公開GitHub間の手動コピーを最小化する安全な公式連携・差分同期",
                "source": "automation/gemini-notebook/README.md",
                "status": "IN_PROGRESS",
            },
            {
                "id": "P006-U03",
                "title": "反復的な画面操作（Computer Use）から公式API・決定的スクリプトへの安全な移行判断",
                "source": "research/2026-10-10-lC5jxpYmatE-ai-techniques.md",
                "status": "OPEN",
            },
        ],
    }


def validate_loop_state_schema(state, state_path):
    if not isinstance(state, dict):
        raise ValueError(
            f"Corrupted loop_state.json at {state_path}: root must be a JSON object (refusing to reset existing state)"
        )
    if state.get("schema_version") != "gemini_notebook_loop_state_v1":
        raise ValueError(
            f"Corrupted loop_state.json at {state_path}: unexpected schema_version={state.get('schema_version')!r} (refusing to reset existing state)"
        )
    for list_key in ("processed_receipts", "next_topics_queue", "open_unknowns"):
        if not isinstance(state.get(list_key), list):
            raise ValueError(
                f"Corrupted loop_state.json at {state_path}: '{list_key}' must be a list (refusing to reset existing state)"
            )
    return state


def load_loop_state(state_path=DEFAULT_STATE_PATH):
    """Load `loop_state.json`. If file exists but is corrupted/unreadable, raise ValueError and NEVER reset."""
    if state_path.exists():
        try:
            raw = state_path.read_text(encoding="utf-8")
        except OSError as ex:
            raise ValueError(
                f"Unreadable loop_state.json at {state_path}: {ex} (refusing to reset existing state)"
            ) from ex
        try:
            state = json.loads(raw)
        except json.JSONDecodeError as ex:
            raise ValueError(
                f"Corrupted JSON in loop_state.json at {state_path}: {ex} (refusing to reset existing state)"
            ) from ex
        return validate_loop_state_schema(state, state_path)
    return default_initial_loop_state()


def render_github_knowledge_index_export_md(registry, local_map, remote_map, loop_state, freshness):
    """Render `github_knowledge_index_export.md` (GitHub-side ledger & delta snapshot).

    Explicitly distinguishes this GitHub export from Gemini Notebook's internal master index
    (`AI技術研究室_知識索引.md`) so the Notebook master index is never blindly overwritten.
    """
    reg_records = {
        r["video_id"]: r
        for r in registry.get("records", [])
        if isinstance(r, dict) and r.get("video_id")
    }
    all_vids = sorted(set(reg_records.keys()) | set(local_map.keys()) | set(remote_map.keys()))

    lines = [
        "# GitHub正本 知識索引・差分エクスポート (`github_knowledge_index_export.md`)",
        "",
        "> **【重要：索引の区別と上書き禁止】**",
        f"> - このファイルは **GitHub 正本（`{EXPECTED_REPO}`）側の既知動画台帳・未解決課題・次回テーマの差分エクスポート** です。",
        f"> - Gemini Notebook 内に既存の総合索引ソース **`{NOTEBOOK_INTERNAL_MASTER_INDEX_NAME}`**（先行16ソース等の蓄積を含む総合索引）とは**別物**です。",
        f"> - Notebook 内の `{NOTEBOOK_INTERNAL_MASTER_INDEX_NAME}` をこのファイルで丸ごと上書き置換しないでください。Notebook 側では既存内容を維持したまま差分追記（または別ソースとして参照）してください。",
        "> - **GitHub への保存成功は、Gemini Notebook への同期完了を意味しません** (`notebook_sync_status: NOT_SYNCED_FROM_GITHUB`)。",
        "",
        f"- 対象リポジトリ: `{EXPECTED_REPO}` (private)",
        f"- 補助知識庫 (Gemini Notebook): {loop_state.get('notebook_url', 'https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7')}",
        f"- GitHub側エクスポート更新日: {loop_state.get('last_updated') or 'INITIAL'}",
        f"- リモートブランチ照合鮮度: `{freshness}`",
        f"- Notebook側への逆同期状態: `{loop_state.get('notebook_sync_status', 'NOT_SYNCED_FROM_GITHUB')}`",
        "",
        "## 1. GitHub全ブランチ横断・既知の動画ID台帳（重複登録禁止リスト）",
        "",
        "`registry.json` だけでなく、`research/*.md` および `notes/*.md` のファイル名・本文から検出された動画IDを含みます。",
        "",
        "| video_id | 状態 | 検出元 (現在ブランチ / 並行PRブランチ) | 参照パス |",
        "|---|---|---|---|",
    ]
    for vid in all_vids:
        if vid in reg_records:
            rec = reg_records[vid]
            status = clean(rec.get("status", "RECORDED"))
            rpath = clean(rec.get("research_path", ""))
            loc = "current_branch (registry.json)"
        elif vid in local_map:
            linfo = local_map[vid]
            status = clean(linfo.get("status", "LOCAL_MARKDOWN"))
            rpath = clean(linfo.get("research_path", ""))
            loc = f"current_branch ({linfo.get('source', 'markdown')})"
        else:
            rinfo = remote_map[vid]
            status = clean(rinfo.get("status", "REMOTE_BRANCH_ONLY"))
            rpath = clean(rinfo.get("research_path", ""))
            via = rinfo.get("detected_via", "remote")
            branches = ", ".join(rinfo.get("branches", []))
            loc = f"{branches} ({via})"
        lines.append(f"| `{vid}` | {status} | {loc} | `{rpath}` |")

    lines += [
        "",
        "## 2. 優先研究テーマ・次回調査キュー (`next_topics`)",
        "",
    ]
    queue = loop_state.get("next_topics_queue") or []
    if queue:
        for idx, topic in enumerate(queue, 1):
            lines.append(f"{idx}. {clean(topic)}")
    else:
        lines += [
            "1. R001/R002: 自律研究Loopの完了条件・停止条件と、重複イベントや結果不明書込みの安全な復旧パターン",
            "2. R004/R005: ハーネス・MCP・プラグイン・公式コネクタの権限境界とモデル非依存の状態管理",
            "3. P006連携: 新しいAI機能・ツール発表時に「過去の未解決課題」と自動照合して再挑戦を提案する仕組み",
        ]

    lines += [
        "",
        "## 3. 未確認・要検証事項 (`unknowns`)",
        "",
    ]
    unknowns = loop_state.get("open_unknowns") or []
    if unknowns:
        for u in unknowns:
            lines.append(f"- {clean(u)}")
    else:
        lines += [
            "- Gemini Taskの定期スケジュール実行時におけるNotebookソース追加・索引更新の無人完走可否",
            "- YouTubeソース（文字起こしのみ）では確認できない画面実演・UI操作の軽量な検証手段",
        ]

    lines += [
        "",
        "## 4. 未解決課題ストック（P006 再評価対象）",
        "",
        "新技術・新機能を発見した際は、以下の未解決課題を解決できる一次資料の根拠があるか照合すること：",
        "",
    ]
    for item in loop_state.get("unresolved_backlog_refs", []):
        lines.append(
            f"- **{clean(item.get('id', ''))}**: {clean(item.get('title', ''))} "
            f"(状態: `{clean(item.get('status', 'OPEN'))}`, 参照: `{clean(item.get('source', ''))}`)"
        )

    lines.append("")
    return "\n".join(lines)


def update_state_and_index(
    data,
    digest,
    registry,
    local_map,
    remote_map,
    freshness,
    applied_new_ids,
    applied_updated_ids,
    state_path=DEFAULT_STATE_PATH,
    index_path=DEFAULT_GITHUB_INDEX_EXPORT_PATH,
    export_drive_dir=None,
):
    """Update `loop_state.json` and `github_knowledge_index_export.md`.

    Never claims that Gemini Notebook itself has been synchronized.
    """
    state = load_loop_state(state_path)
    checked_at = data.get("checked_at") or date.today().isoformat()
    state["last_updated"] = checked_at
    state["notebook_internal_master_index_name"] = NOTEBOOK_INTERNAL_MASTER_INDEX_NAME
    state["github_index_export_file"] = "automation/gemini-notebook/state/github_knowledge_index_export.md"
    state["notebook_sync_status"] = "NOT_SYNCED_FROM_GITHUB"
    if data.get("notebook_url"):
        state["notebook_url"] = data["notebook_url"]

    processed = state.setdefault("processed_receipts", [])
    if digest and not any(p.get("sha256") == digest for p in processed if isinstance(p, dict)):
        processed.append(
            {
                "sha256": digest,
                "checked_at": checked_at,
                "new_video_ids": applied_new_ids,
                "updated_video_ids": applied_updated_ids,
                "github_write_status": "APPLIED_LOCAL",
                "notebook_sync_status": "NOT_SYNCED_FROM_GITHUB",
            }
        )

    queue = state.setdefault("next_topics_queue", [])
    for topic in data.get("next_topics") or []:
        t_clean = clean(topic)
        if t_clean and t_clean not in queue:
            queue.append(t_clean)
    state["next_topics_queue"] = queue[-15:]

    unknowns = state.setdefault("open_unknowns", [])
    for unk in data.get("unknowns") or []:
        u_clean = clean(unk)
        if u_clean and u_clean not in unknowns:
            unknowns.append(u_clean)
    state["open_unknowns"] = unknowns[-25:]

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    index_md = render_github_knowledge_index_export_md(
        registry, local_map, remote_map, state, freshness
    )
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(index_md, encoding="utf-8")

    drive_written = None
    if export_drive_dir:
        drive_dir = Path(export_drive_dir)
        if not drive_dir.exists():
            raise ValueError(f"Drive export directory does not exist: {drive_dir}")
        drive_target = drive_dir / index_path.name
        drive_target.write_text(index_md, encoding="utf-8")
        drive_written = str(drive_target)

    return {
        "state_path": str(state_path),
        "github_index_export_path": str(index_path),
        "notebook_internal_master_index_name": NOTEBOOK_INTERNAL_MASTER_INDEX_NAME,
        "github_index_export_status": "WRITTEN_LOCAL",
        "notebook_sync_status": "NOT_SYNCED_FROM_GITHUB",
        "drive_export_path": drive_written,
    }


def verify_and_push_git(
    root=ROOT,
    commit_message=None,
    do_push=False,
    touched_paths=None,
):
    """Safely commit to non-default branch, optionally push once, and verify remote readback."""
    branch = check_write_boundary(root=root)
    status_out = git("status", "--porcelain", root=root)
    if not status_out:
        return {
            "branch": branch,
            "committed": False,
            "pushed": False,
            "head_sha": git("rev-parse", "HEAD", root=root),
            "readback_verified": True,
            "github_write_status": "NO_CHANGES",
            "notebook_sync_status": "NOT_SYNCED_FROM_GITHUB",
        }

    if do_push:
        git("fetch", "origin", branch, root=root, check=True)
        remote_ref = f"refs/remotes/origin/{branch}"
        has_remote = git("rev-parse", "--verify", remote_ref, root=root, check=False)
        if has_remote:
            behind_count = int(git("rev-list", "--count", f"HEAD..origin/{branch}", root=root))
            if behind_count > 0:
                raise ValueError(
                    f"Remote branch origin/{branch} is ahead by {behind_count} commit(s); stopping safely without overwrite"
                )

    if touched_paths:
        rel_paths = [
            str(Path(p).resolve().relative_to(root.resolve()).as_posix()) for p in touched_paths
        ]
        git("add", "--", *rel_paths, root=root)
    else:
        git("add", "-u", root=root)

    msg = (
        commit_message
        or "feat(gemini-notebook): import verified research receipt and export GitHub knowledge index"
    )
    git("commit", "-m", msg, root=root)
    local_head = git("rev-parse", "HEAD", root=root)

    file_hashes = {}
    for p in touched_paths or []:
        rel = Path(p).resolve().relative_to(root.resolve()).as_posix()
        file_hashes[rel] = git("rev-parse", f"HEAD:{rel}", root=root)

    result = {
        "branch": branch,
        "committed": True,
        "pushed": False,
        "head_sha": local_head,
        "file_blob_shas": file_hashes,
        "readback_verified": False,
        "github_write_status": "COMMITTED_LOCAL_ONLY",
        "notebook_sync_status": "NOT_SYNCED_FROM_GITHUB",
    }

    if do_push:
        git("push", "origin", f"{branch}:{branch}", root=root, check=True)
        result["pushed"] = True
        ls_remote = git("ls-remote", "origin", f"refs/heads/{branch}", root=root, check=True)
        remote_sha = ls_remote.split()[0] if ls_remote else ""
        git("fetch", "origin", branch, root=root, check=True)
        remote_blobs_match = True
        for rel, expected_blob in file_hashes.items():
            actual_blob = git("rev-parse", f"origin/{branch}:{rel}", root=root, check=True)
            if actual_blob != expected_blob:
                remote_blobs_match = False
        result["remote_head_sha"] = remote_sha
        result["readback_verified"] = (remote_sha == local_head) and remote_blobs_match
        if not result["readback_verified"]:
            raise ValueError(f"Remote readback mismatch: local={local_head} remote={remote_sha}")
        result["github_write_status"] = "PUSHED_AND_READBACK_VERIFIED"
    else:
        local_blobs_match = True
        for rel, expected_blob in file_hashes.items():
            actual_blob = git("rev-parse", f"HEAD:{rel}", root=root, check=True)
            if actual_blob != expected_blob:
                local_blobs_match = False
        result["readback_verified"] = local_blobs_match

    return result


def process_receipt_data(
    data,
    root=ROOT,
    apply=False,
    allow_updates=True,
    check_remote_branches=True,
    fetch_remote=True,
    allow_stale_remotes=False,
    sync_index=False,
    state_path=None,
    index_path=None,
    export_drive_dir=None,
):
    """Core pipeline to validate and process a single parsed `research_receipt_v1` dict."""
    videos = validate(data)
    digest = compute_receipt_digest(data)

    registry_path = root / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if registry.get("repository") != EXPECTED_REPO or not isinstance(registry.get("records"), list):
        raise ValueError("Unexpected registry.json")

    resolved_state_path = state_path or (
        root / "automation" / "gemini-notebook" / "state" / "loop_state.json"
    )
    resolved_index_path = index_path or (
        root / "automation" / "gemini-notebook" / "state" / "github_knowledge_index_export.md"
    )

    # Load and validate loop_state.json BEFORE doing any work (raises ValueError if corrupted)
    loop_state = load_loop_state(resolved_state_path)
    processed_hashes = {
        p.get("sha256") for p in loop_state.get("processed_receipts", []) if isinstance(p, dict)
    }

    local_records_by_id = {
        r.get("video_id"): r
        for r in registry["records"]
        if isinstance(r, dict) and r.get("video_id")
    }
    local_map = collect_local_research_videos(root=root)

    if check_remote_branches:
        remote_map, freshness = collect_remote_branch_videos(
            root=root,
            fetch_remote=fetch_remote,
            allow_stale_remotes=allow_stale_remotes,
        )
    else:
        remote_map, freshness = {}, "DISABLED"

    planned_new = []
    planned_updates = []
    skipped = []

    if digest in processed_hashes:
        for v in videos:
            vid = v["video_id"]
            print("SKIP_EXISTING", vid)
            skipped.append({"video_id": vid, "reason": "SKIP_DUPLICATE_RECEIPT"})
    else:
        for v in videos:
            vid = v["video_id"]
            existing_md = sorted((root / "research").glob("*" + vid + "*.md"))
            is_local_known = (vid in local_records_by_id) or (vid in local_map) or bool(existing_md)
            is_remote_known = (vid in remote_map) and not is_local_known
            changes_set = set(v.get("changes") or [])

            if v.get("notebook_readback") != "PASS":
                print("SKIP_UNVERIFIED_NOTEBOOK", vid)
                skipped.append({"video_id": vid, "reason": "SKIP_UNVERIFIED_NOTEBOOK"})
                continue
            if "METADATA_ONLY" in v["source_scope"].upper():
                print("SKIP_METADATA_ONLY", vid)
                skipped.append({"video_id": vid, "reason": "SKIP_METADATA_ONLY"})
                continue

            if is_local_known:
                if allow_updates and (changes_set & {"UPDATED", "CONFLICT"}) and existing_md:
                    target_md = existing_md[0]
                    current_content = target_md.read_text(encoding="utf-8")
                    delta_text = render_delta_section(v, data["checked_at"])
                    if (
                        clean(v["summary_ja"]) in current_content
                        or f"## 差分更新 ({data['checked_at']}" in current_content
                    ):
                        print("SKIP_EXISTING", vid)
                        skipped.append(
                            {"video_id": vid, "reason": "SKIP_EXISTING_DELTA_ALREADY_APPLIED"}
                        )
                        continue
                    planned_updates.append((target_md, delta_text, v))
                else:
                    source_detail = local_map.get(vid, {}).get("source", "local")
                    print("SKIP_EXISTING", vid)
                    skipped.append(
                        {"video_id": vid, "reason": "SKIP_EXISTING", "detected_via": source_detail}
                    )
                continue

            if is_remote_known:
                remote_info = remote_map[vid]
                remote_branches = remote_info.get("branches", [])
                remote_rel_path = remote_info.get("research_path", "")
                if (
                    allow_updates
                    and (changes_set & {"UPDATED", "CONFLICT"})
                    and remote_branches
                    and remote_rel_path.startswith("research/")
                ):
                    src_branch = remote_branches[0]
                    remote_md_text = git(
                        "show", f"{src_branch}:{remote_rel_path}", root=root, check=False
                    )
                    if remote_md_text:
                        target_md = root / remote_rel_path
                        delta_text = render_delta_section(v, data["checked_at"])
                        if (
                            clean(v["summary_ja"]) in remote_md_text
                            or f"## 差分更新 ({data['checked_at']}" in remote_md_text
                        ):
                            print("SKIP_EXISTING", vid)
                            skipped.append(
                                {
                                    "video_id": vid,
                                    "reason": "SKIP_EXISTING_DELTA_ALREADY_APPLIED",
                                }
                            )
                            continue
                        remote_reg_entry = None
                        remote_reg_raw = git(
                            "show", f"{src_branch}:registry.json", root=root, check=False
                        )
                        if remote_reg_raw:
                            try:
                                r_reg = json.loads(remote_reg_raw)
                                for r_item in r_reg.get("records", []):
                                    if isinstance(r_item, dict) and r_item.get("video_id") == vid:
                                        remote_reg_entry = dict(r_item)
                                        break
                            except json.JSONDecodeError:
                                pass
                        v_copy = dict(v)
                        v_copy["_remote_base"] = {
                            "branch": src_branch,
                            "research_path": remote_rel_path,
                            "base_markdown": remote_md_text,
                            "registry_entry": remote_reg_entry,
                        }
                        planned_updates.append((target_md, delta_text, v_copy))
                        continue

                branches_str = ",".join(remote_branches)
                detected_via = remote_info.get("detected_via", "remote")
                print("SKIP_EXISTING_REMOTE_BRANCH", vid, branches_str)
                skipped.append(
                    {
                        "video_id": vid,
                        "reason": "SKIP_EXISTING_REMOTE_BRANCH",
                        "branches": remote_branches,
                        "detected_via": detected_via,
                    }
                )
                continue

            dst = root / "research" / ("{}-{}-gemini-notebook.md".format(data["checked_at"], vid))
            if dst.exists():
                print("SKIP_EXISTS", vid)
                skipped.append({"video_id": vid, "reason": "SKIP_EXISTS"})
                continue
            planned_new.append((dst, render(v, data["checked_at"]), v))

    summary_payload = {
        "new_records": len(planned_new),
        "ids": [v["video_id"] for _, _, v in planned_new],
        "updated_records": len(planned_updates),
        "updated_ids": [v["video_id"] for _, _, v in planned_updates],
        "skipped": skipped,
        "receipt_sha256": digest,
        "remote_dedup_freshness": freshness,
        "github_write_status": "PREVIEW_ONLY" if not apply else "PENDING_WRITE",
        "notebook_sync_status": "NOT_SYNCED_FROM_GITHUB",
        "mode": "APPLY" if apply else "PREVIEW",
    }
    print(json.dumps(summary_payload, ensure_ascii=False))

    touched_files = []
    if not apply:
        return summary_payload, touched_files

    branch = check_write_boundary(root=root)
    for dst, _, _ in planned_new:
        if dst.exists():
            raise ValueError("Concurrent file already exists: " + str(dst))

    for dst, text, v in planned_new:
        dst.parent.mkdir(parents=True, exist_ok=True)
        with dst.open("x", encoding="utf-8") as f:
            f.write(text)
        touched_files.append(dst)
        rec_entry = {
            "record_id": "youtube:" + v["video_id"],
            "video_id": v["video_id"],
            "canonical_url": canonical_youtube_url(v["video_id"]),
            "research_path": dst.relative_to(root).as_posix(),
            "source_scope": v["source_scope"],
            "research_date": data["checked_at"],
            "status": "GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE",
            "evidence": "GEMINI_RESEARCH_RECEIPT",
        }
        if v["url"] != rec_entry["canonical_url"]:
            rec_entry["original_url"] = v["url"]
        registry["records"].append(rec_entry)

    for target_md, delta_text, v in planned_updates:
        target_md.parent.mkdir(parents=True, exist_ok=True)
        remote_base = v.get("_remote_base")
        if target_md.exists():
            existing_text = target_md.read_text(encoding="utf-8")
        elif remote_base and remote_base.get("base_markdown"):
            existing_text = remote_base["base_markdown"]
        else:
            raise ValueError("Target markdown for update does not exist: " + str(target_md))
        sep = "" if existing_text.endswith("\n") else "\n"
        target_md.write_text(existing_text + sep + delta_text.lstrip("\n"), encoding="utf-8")
        touched_files.append(target_md)
        rec = local_records_by_id.get(v["video_id"])
        if rec is None and remote_base:
            base_rec = remote_base.get("registry_entry") or {
                "record_id": "youtube:" + v["video_id"],
                "video_id": v["video_id"],
                "canonical_url": canonical_youtube_url(v["video_id"]),
                "research_path": remote_base["research_path"],
                "source_scope": v["source_scope"],
                "research_date": data["checked_at"],
                "status": "REMOTE_BRANCH_CONSOLIDATED; GEMINI_DELTA_UPDATED",
                "evidence": "GEMINI_RESEARCH_RECEIPT",
            }
            base_rec["consolidated_from_branch"] = remote_base["branch"]
            registry["records"].append(base_rec)
            local_records_by_id[v["video_id"]] = base_rec
            rec = base_rec
        if rec is not None:
            rec["last_updated"] = data["checked_at"]
            history = rec.setdefault("update_history", [])
            history.append(
                {
                    "checked_at": data["checked_at"],
                    "changes": v["changes"],
                    "source_scope": v["source_scope"],
                }
            )

    if planned_new or planned_updates:
        registry_path.write_text(
            json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        touched_files.append(registry_path)

    if sync_index:
        # Re-collect local research videos after applying new/updated records
        updated_local_map = collect_local_research_videos(root=root)
        idx_res = update_state_and_index(
            data=data,
            digest=digest,
            registry=registry,
            local_map=updated_local_map,
            remote_map=remote_map,
            freshness=freshness,
            applied_new_ids=[v["video_id"] for _, _, v in planned_new],
            applied_updated_ids=[v["video_id"] for _, _, v in planned_updates],
            state_path=resolved_state_path,
            index_path=resolved_index_path,
            export_drive_dir=export_drive_dir,
        )
        touched_files.extend([Path(idx_res["state_path"]), Path(idx_res["github_index_export_path"])])
        summary_payload["github_index_export"] = idx_res

    summary_payload["github_write_status"] = "LOCAL_WORKTREE_WRITTEN"
    print(
        "LOCAL_WRITE_COMPLETE branch={} files={} updates={} (NO_COMMIT_NO_PUSH; NOTEBOOK_SYNC=NOT_SYNCED_FROM_GITHUB)".format(
            branch, len(planned_new), len(planned_updates)
        )
    )
    return summary_payload, touched_files


def read_clipboard_text():
    """Read text from Windows clipboard via PowerShell Get-Clipboard (stdlib only)."""
    res = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-Clipboard -Raw",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return res.stdout


def discover_inbox_files(inbox_dir):
    """Find candidate `.json`, `.md`, `.txt` files in inbox directory sorted by name."""
    p = Path(inbox_dir)
    if not p.exists() or not p.is_dir():
        raise ValueError(f"Inbox directory not found: {inbox_dir}")
    candidates = []
    for ext in ("*.json", "*.md", "*.txt"):
        candidates.extend(p.glob(ext))
    return sorted(set(candidates), key=lambda x: x.name)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Gemini Notebook research receipt bridge & GitHub knowledge index exporter (v0.3)"
    )
    ap.add_argument(
        "receipt",
        nargs="?",
        help="Gemini output JSON or Markdown file (secrets/transcripts prohibited)",
    )
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Write to local non-default branch",
    )
    ap.add_argument(
        "--payload-string",
        help="Raw receipt JSON or Markdown text passed directly (e.g. from cloud workflow_dispatch)",
    )
    ap.add_argument(
        "--payload-env",
        help="Environment variable name holding raw receipt JSON or Markdown (e.g. RECEIPT_PAYLOAD in GitHub Actions)",
    )
    ap.add_argument(
        "--from-clipboard",
        action="store_true",
        help="Extract `research_receipt_v1` directly from system clipboard",
    )
    ap.add_argument(
        "--inbox",
        help="Directory (local or Google Drive folder) to scan for unprocessed receipt files",
    )
    ap.add_argument(
        "--sync-index",
        action="store_true",
        help="Update `state/loop_state.json` and `state/github_knowledge_index_export.md`",
    )
    ap.add_argument(
        "--refresh-index-only",
        action="store_true",
        help="Rebuild `state/github_knowledge_index_export.md` from current & freshly fetched remote branches",
    )
    ap.add_argument(
        "--export-drive-dir",
        help="Optional Google Drive folder path to export `github_knowledge_index_export.md`",
    )
    ap.add_argument(
        "--no-remote-dedup",
        action="store_true",
        help="Disable scanning `origin/*` branches for cross-branch duplicate video IDs",
    )
    ap.add_argument(
        "--allow-stale-remotes",
        action="store_true",
        help="Allow fallback to cached remote refs if `git fetch --prune origin` fails (offline mode)",
    )
    ap.add_argument(
        "--commit",
        action="store_true",
        help="Commit applied changes to the current non-default branch",
    )
    ap.add_argument(
        "--push",
        action="store_true",
        help="Push committed changes to `origin/<branch>` and verify remote readback",
    )
    ap.add_argument(
        "--commit-message",
        help="Custom commit message when using --commit",
    )
    ap.add_argument(
        "--evidence-out",
        help="Write objective execution & readback evidence JSON to this file path",
    )
    args = ap.parse_args(argv)

    if args.push and not args.commit:
        args.commit = True
    if args.commit and not args.apply and not args.refresh_index_only:
        raise ValueError("--commit requires --apply or --refresh-index-only")

    all_touched = []
    results = []

    if args.refresh_index_only:
        branch = check_write_boundary(root=ROOT)
        registry = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))
        local_map = collect_local_research_videos(root=ROOT)
        if args.no_remote_dedup:
            remote_map, freshness = {}, "DISABLED"
        else:
            remote_map, freshness = collect_remote_branch_videos(
                root=ROOT,
                fetch_remote=True,
                allow_stale_remotes=args.allow_stale_remotes,
            )
        dummy_data = {
            "checked_at": date.today().isoformat(),
            "notebook_url": "https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7",
            "next_topics": [],
            "unknowns": [],
        }
        idx_res = update_state_and_index(
            data=dummy_data,
            digest=None,
            registry=registry,
            local_map=local_map,
            remote_map=remote_map,
            freshness=freshness,
            applied_new_ids=[],
            applied_updated_ids=[],
            export_drive_dir=args.export_drive_dir,
        )
        all_touched.extend(
            [Path(idx_res["state_path"]), Path(idx_res["github_index_export_path"])]
        )
        results.append(
            {
                "mode": "REFRESH_INDEX_ONLY",
                "branch": branch,
                "remote_dedup_freshness": freshness,
                "github_index_export": idx_res,
                "notebook_sync_status": "NOT_SYNCED_FROM_GITHUB",
            }
        )
        print(json.dumps(results[-1], ensure_ascii=False))
    else:
        raw_inputs = []
        if args.payload_env:
            env_val = os.environ.get(args.payload_env, "")
            if not env_val.strip():
                raise ValueError(f"Environment variable {args.payload_env!r} is empty or not set")
            raw_inputs.append((f"env:{args.payload_env}", env_val))
        elif args.payload_string:
            raw_inputs.append(("payload_string", args.payload_string))
        elif args.from_clipboard:
            raw_inputs.append(("clipboard", read_clipboard_text()))
        elif args.inbox:
            files = discover_inbox_files(args.inbox)
            for f in files:
                raw_inputs.append((str(f), f.read_text(encoding="utf-8")))
        elif args.receipt:
            raw_inputs.append((args.receipt, Path(args.receipt).read_text(encoding="utf-8")))
        else:
            raise ValueError(
                "Specify a receipt file, --payload-env, --payload-string, --from-clipboard, --inbox, or --refresh-index-only"
            )

        for source_name, raw_text in raw_inputs:
            try:
                data = extract_receipt_payload(raw_text)
                if not isinstance(data, dict) or data.get("schema_version") != "research_receipt_v1":
                    raise ValueError("Invalid receipt schema_version")
            except (ValueError, json.JSONDecodeError) as ex:
                if args.inbox:
                    print(f"SKIP_NON_RECEIPT_FILE {source_name}: {ex}")
                    continue
                raise
            summary, touched = process_receipt_data(
                data=data,
                root=ROOT,
                apply=args.apply,
                allow_updates=True,
                check_remote_branches=not args.no_remote_dedup,
                fetch_remote=True,
                allow_stale_remotes=args.allow_stale_remotes,
                sync_index=args.sync_index,
                export_drive_dir=args.export_drive_dir,
            )
            summary["source"] = source_name
            results.append(summary)
            all_touched.extend(touched)

    git_evidence = None
    if args.commit and all_touched:
        git_evidence = verify_and_push_git(
            root=ROOT,
            commit_message=args.commit_message,
            do_push=args.push,
            touched_paths=all_touched,
        )
        print(json.dumps({"git_operation": git_evidence}, ensure_ascii=False))

    if args.evidence_out:
        ev_path = Path(args.evidence_out)
        ev_path.parent.mkdir(parents=True, exist_ok=True)
        ev_payload = {
            "schema_version": "gemini_notebook_bridge_evidence_v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "results": results,
            "git_operation": git_evidence,
            "notebook_sync_status": "NOT_SYNCED_FROM_GITHUB",
        }
        ev_path.write_text(
            json.dumps(ev_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError, json.JSONDecodeError) as ex:
        print("ERROR: " + str(ex), file=sys.stderr)
        sys.exit(2)
