#!/usr/bin/env python3
"""AI技術研究室 | 自動研究Loop統合パイプライン (auto_research_pipeline.py v2.2).

目的:
YouTube URLを起点とし、事前重複チェック -> 実際のYouTube字幕・メタデータ取得 ->
AI研究/ローカル字幕解析 -> OKF v0.2形式研究ノート生成 -> GitHub正本保存 ->
実際のリモート本文（研究ノート＆registry.json）のSHA-256読み戻し検証 ->
Gemini Notebook自動登録＆実画面Readback検証 -> 自然言語QA実証までを自律実行する。

改善点 (v2.2):
1. [Gemini 3.8 Flash] デフォルトモデルを gemini-3.8-flash に更新。
2. [Notebook実登録＆Readback統合] notebook_auto_ingest v3.0 と連携し、Drive配置＋CDP DOM Readbackを実行。
3. [厳格なSUCCESS判定] 11の必須条件すべてANDのみ完全SUCCESSを認可。1つでも未達なら PARTIAL_* を返却。
4. [registry.json remote readback] git show origin:registry.json によるローカル/リモートSHA-256一致検証。
5. [研究ノート remote readback] git show origin:research/*.md によるローカル/リモートSHA-256一致検証。
6. [部分失敗後の自動レジューム] GitHub登録済み・Notebook未完了時は、Notebook工程だけを安全に再開。
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
AUTO_DIR = Path(__file__).resolve().parent
CONTRACT_PATH = AUTO_DIR / "contract_spec_v1.json"
REGISTRY_PATH = ROOT / "registry.json"
RESEARCH_DIR = ROOT / "research"
CATALOG_PATH = AUTO_DIR / "state" / "video_knowledge_catalog.json"
SCRATCH_DIR = ROOT / "scratch"

# Set UTF-8 encoding safely
try:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(AUTO_DIR))
import intake_url
import verify_timestamps
import receipt_to_research
import query_research
import notebook_auto_ingest

DEFAULT_DRIVE_INBOX = Path("G:/マイドライブ/AI技術研究室_受信トレイ")
DEFAULT_TARGET_BRANCH = "feature/gemini-notebook-research-loop-20261016"
NOTEBOOK_URL = "https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7"
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"


def sanitize_text(text: str, max_len: int, max_newlines: int = 3) -> str:
    """Normalize whitespace and truncate text safely."""
    if not text:
        return ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if max_newlines > 0 and len(lines) > max_newlines:
        lines = lines[:max_newlines]
    res = " ".join(lines) if max_newlines <= 1 else "\n".join(lines)
    if len(res) > max_len:
        res = res[: max_len - 3] + "..."
    return res


def compute_sha256(content: str) -> str:
    """Compute normalized SHA-256 of text string (LF normalized)."""
    normalized = content.replace("\r\n", "\n").encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def verify_target_branch_early(root: Path = ROOT, target_branch: str = DEFAULT_TARGET_BRANCH):
    """Ensure we are in the permitted repository and non-default branch BEFORE any file changes."""
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=root, text=True
        ).strip()
    except Exception as ex:
        raise RuntimeError(f"Gitブランチの確認に失敗しました: {ex}")

    if branch != target_branch:
        raise RuntimeError(
            f"安全エラー: 現在のブランチ '{branch}' は許可された非default作業ブランチ '{target_branch}' ではありません。"
            f"default branch への直接書き込みや未許可ブランチでの操作は禁止されています。"
        )


def fetch_actual_captions(player_data: Dict[str, Any]) -> Tuple[str, List[Tuple[float, float, str]], str]:
    """Fetch and parse actual caption track from YouTube player data."""
    caption_tracks = (
        player_data.get("captions", {})
        .get("playerCaptionsTracklistRenderer", {})
        .get("captionTracks", [])
    )
    if not caption_tracks:
        return "NOT_ACQUIRED", [], ""

    tr = verify_timestamps.pick_track(caption_tracks)
    if not tr or not tr.get("baseUrl"):
        return "NOT_ACQUIRED", [], ""

    try:
        raw_xml = verify_timestamps.http_get(tr["baseUrl"], timeout=25)
        cues = verify_timestamps.parse_caption_xml(raw_xml)
        if cues:
            return "UNVERIFIED", cues, raw_xml[:500]
    except Exception as ex:
        print(f"  - [DEBUG] 字幕取得エラー: {ex}")

    return "NOT_ACQUIRED", [], ""


def analyze_with_gemini_api(
    title: str,
    author: str,
    length_sec: int,
    cues: List[Tuple[float, float, str]],
    api_key: str,
    model_name: str = DEFAULT_GEMINI_MODEL,
) -> Optional[Dict[str, Any]]:
    """Analyze actual caption cues using Google Gemini Flash REST API (defaults to gemini-3.8-flash)."""
    if not api_key:
        return None

    cues_text = []
    step = 1 if len(cues) < 300 else 2
    for start, end, txt in cues[::step]:
        m, s = int(start // 60), int(start % 60)
        cues_text.append(f"[{m:02d}:{s:02d}] {txt}")
    joined_transcript = "\n".join(cues_text[:400])

    prompt = f"""あなたはAI技術研究室の研究員です。以下のYouTube動画の実際の字幕テキストを精査し、客観的な研究成果をJSON形式で出力してください。
動画タイトル: {title}
投稿者: {author}
動画長: {length_sec}秒

【字幕テキスト（抜粋）】
{joined_transcript}

【出力必須スキーマ（JSON）】
{{
  "summary_ja": "動画全体の要約（日本語250文字以内。実際の字幕内容に基づく）",
  "detailed_findings_ja": "技術的要点、中核概念、運用上の注意点、キーワードをまとめた構造化テキスト（2000文字以内、改行20行以内）",
  "chapters": [
    {{
      "title": "章のタイトル（字幕の該当箇所を表す具体的な名称）",
      "start_seconds": 開始秒数(int),
      "end_seconds": 終了秒数(int),
      "summary_ja": "この区間の要約（200文字以内）",
      "timestamp_source": "TIMESTAMPED_CAPTIONS",
      "key_topics": ["キーワード1", "キーワード2"]
    }}
  ],
  "claims": [
    {{
      "text": "動画内の具体的な主張や発言内容（実際の字幕に基づく）",
      "status": "REPORTED_BY_AUTHOR",
      "timestamp_seconds": 発言の開始秒数(int),
      "timestamp_source": "TIMESTAMPED_CAPTIONS",
      "official_url": null
    }}
  ]
}}
※架空の内容や推測の秒数は含めず、字幕に存在する発話・時刻のみを根拠にしてください。
"""

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }
    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidate = data.get("candidates", [{}])[0]
            text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
            return json.loads(text)
    except Exception as ex:
        print(f"  - [WARNING] Gemini API解析呼出に失敗 (ローカル抽出へ移行): {ex}")
        return None


def analyze_with_local_transcript_engine(
    title: str,
    author: str,
    length_sec: int,
    cues: List[Tuple[float, float, str]],
    desc: str,
    desc_chapters: List[int],
) -> Dict[str, Any]:
    """Deterministically extract structured knowledge from real caption text (Non-AI extraction)."""
    if not cues:
        summary_raw = f"{author}による動画「{title}」（字幕未取得: NOT_ACQUIRED）。"
        if desc:
            desc_lines = [l.strip() for l in desc.splitlines() if l.strip() and not l.strip().startswith("http")]
            if desc_lines:
                summary_raw = f"{title}に関する動画（字幕未取得: NOT_ACQUIRED）。概要: " + " / ".join(desc_lines[:2])
        return {
            "summary_ja": sanitize_text(summary_raw, 280, max_newlines=1),
            "detailed_findings_ja": f"【動画基本情報】\n- 投稿者: {author}\n- 動画長: {length_sec}秒\n- 字幕状況: NOT_ACQUIRED（字幕データなし）\n\n【留意事項】\n字幕本文が取得できなかったため、推測での章立て・主張の生成は行っていません。",
            "chapters": [],
            "claims": [],
            "analysis_engine": "METADATA_ONLY",
        }

    total_cues = len(cues)
    num_sections = min(5, max(2, length_sec // 240)) if length_sec > 120 else 1
    chunk_size = total_cues // num_sections if num_sections > 0 else total_cues

    chapters = []
    claims = []
    section_summaries = []

    for i in range(num_sections):
        start_idx = i * chunk_size
        end_idx = min(total_cues, (i + 1) * chunk_size) if i + 1 < num_sections else total_cues
        if start_idx >= end_idx:
            break
        sec_cues = cues[start_idx:end_idx]
        st_sec = int(sec_cues[0][0])
        ed_sec = int(sec_cues[-1][1])
        
        combined_text = " ".join(c[2] for c in sec_cues)
        clean_text = re.sub(r"\s+", " ", combined_text).strip()
        sample_snippet = clean_text[:90] + ("..." if len(clean_text) > 90 else "")
        ch_title = f"区間 {st_sec // 60:02d}:{st_sec % 60:02d}〜{ed_sec // 60:02d}:{ed_sec % 60:02d} 実字幕発話抜粋"
        
        topics = []
        for kw in ["AI", "RAG", "OKF", "Agent", "Claude", "Gemini", "NotebookLM", "自動化", "設計", "検証", "ツール"]:
            if kw.lower() in clean_text.lower():
                topics.append(kw)
        if not topics:
            topics = ["動画発話", "技術解説"]

        chapters.append({
            "title": ch_title,
            "start_seconds": st_sec,
            "end_seconds": ed_sec,
            "summary_ja": sanitize_text(f"実字幕発話抜粋: {sample_snippet}", 280, max_newlines=1),
            "timestamp_source": "TIMESTAMPED_CAPTIONS",
            "key_topics": topics[:6],
        })
        section_summaries.append(f"{st_sec // 60:02d}:{st_sec % 60:02d}〜: {sample_snippet[:60]}")

        if i in (0, num_sections // 2):
            claims.append({
                "text": sanitize_text(f"動画内実発話（{st_sec // 60:02d}:{st_sec % 60:02d}）: 「{sample_snippet[:150]}」", 450, max_newlines=1),
                "status": "REPORTED_BY_AUTHOR",
                "timestamp_seconds": st_sec,
                "timestamp_source": "TIMESTAMPED_CAPTIONS",
                "official_url": None,
            })

    summary_raw = f"{author}による「{title}」。実字幕（{total_cues}行）からローカルテキスト抽出。発話抜粋: " + " / ".join(section_summaries[:2])
    summary_ja = sanitize_text(summary_raw, 280, max_newlines=2)

    findings = [
        f"【動画基本情報】",
        f"- 投稿者: {author} / 動画長: {length_sec}秒",
        f"- 解析方式: ローカル字幕テキスト抽出（非AI要約）",
        f"- 字幕取得状況: UNVERIFIED（実字幕行数: {total_cues}行）",
        f"",
        f"【実字幕からの抽出知見・抜粋】",
    ] + [f"- {s}" for s in section_summaries[:4]] + [
        f"",
        f"【注意点】",
        f"- 本研究ノートはYouTubeから実際に取得した実字幕テキストから決定論的に抽出したものです。AI推論による要約ではありません。",
    ]

    return {
        "summary_ja": summary_ja,
        "detailed_findings_ja": "\n".join(findings[:20]),
        "chapters": chapters,
        "claims": claims,
        "analysis_engine": "LOCAL_TRANSCRIPT_EXTRACTION",
    }


def infer_semantic_related_records(
    video_id: str,
    title: str,
    summary_ja: str,
    detailed_findings_ja: str = "",
    chapters: Optional[List[Dict[str, Any]]] = None,
    claims: Optional[List[Dict[str, Any]]] = None,
    published_at: Optional[str] = None,
    corpus: Optional[Dict[str, Any]] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """台帳全件を対象に、章・タグ・主張・要約の語の重なりから関連動画の候補（CANDIDATE）を出す。

    R6（docs/OKF_KNOWLEDGE_ROADMAP.md）: 固定の数本×単語一致ではなく related_links.infer_candidates を使う。
    根拠にした共通語と両ノートの該当箇所を evidence に入れ、自己リンクは除外し、上限 limit 件。
    CONFIRMED には自動でしない。UPDATES は投稿日時の新旧で向きを決める。
    """
    import related_links

    if corpus is None:
        corpus = related_links.load_corpus(ROOT)
    source = related_links.source_from_fields(
        video_id, title, summary_ja, detailed_findings_ja, chapters, claims, published_at
    )
    return [
        {k: c[k] for k in ("target_id", "relation", "note", "status", "evidence")}
        for c in related_links.infer_candidates(source, corpus, limit=limit)
    ]


def build_research_receipt(
    video_id: str,
    player_data: Dict[str, Any],
    publish_date: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
    gemini_model: str = DEFAULT_GEMINI_MODEL,
    enable_live_gemini: bool = False,
    dry_run: bool = False,
) -> Tuple[Dict[str, Any], str, str]:
    """Synthesize conformant research_receipt_v1 from real metadata & actual caption text.
    
    Returns:
        (receipt_dict, engine_used, model_used)
    """
    vd = player_data.get("videoDetails", {})
    raw_title = vd.get("title", f"YouTube Video {video_id}").strip()
    author = vd.get("author", "Unknown Author").strip()
    length_sec = int(vd.get("lengthSeconds") or 0)
    desc = vd.get("shortDescription", "").strip()

    title = sanitize_text(raw_title, 240, max_newlines=1) or f"YouTube動画研究 {video_id}"
    starts, _ = verify_timestamps.parse_description_chapters(desc)

    # 1. Fetch real captions
    transcript_status, cues, _ = fetch_actual_captions(player_data)
    print(f"  - 字幕取得結果: status={transcript_status}, 実発話ブロック数={len(cues)}")

    # 2. Analyze: Gemini API (Only if enabled, key present, cues present, and NOT dry_run)
    ai_analysis = None
    engine_used = "METADATA_ONLY" if not cues else "LOCAL_TRANSCRIPT_EXTRACTION"
    model_used = "NONE"

    if enable_live_gemini and gemini_api_key and cues and not dry_run:
        print(f"  - Gemini API ({gemini_model}) による字幕内容の研究・要約を実行中 (LIVE承認済み)...")
        ai_analysis = analyze_with_gemini_api(title, author, length_sec, cues, gemini_api_key, model_name=gemini_model)
        if ai_analysis:
            engine_used = "GEMINI_API_LIVE"
            model_used = gemini_model

    if not ai_analysis:
        if dry_run:
            print("  - [DRY RUN] 外部API呼出しを行わず、ローカル字幕解析エンジンを適用します。")
        elif not enable_live_gemini:
            print("  - [INFO] 外部LIVE未指定（--enable-live-geminiなし）: ローカル字幕テキスト抽出エンジンを適用します。")
        elif not gemini_api_key:
            print("  - [WARNING] --enable-live-gemini が指定されましたが GEMINI_API_KEY が未設定です。ローカル字幕解析エンジンにフォールバックします。")
        ai_analysis = analyze_with_local_transcript_engine(title, author, length_sec, cues, desc, starts)
        engine_used = ai_analysis.get("analysis_engine", engine_used)
        model_used = "NONE"

    summary_ja = ai_analysis.get("summary_ja", f"{title}の技術分析。")
    detailed_findings_ja = ai_analysis.get("detailed_findings_ja", "")
    chapters = ai_analysis.get("chapters", [])
    claims = ai_analysis.get("claims", [])

    # Related records: Candidate only, NEVER falsely confirmed
    related_records = infer_semantic_related_records(
        video_id=video_id,
        title=title,
        summary_ja=summary_ja,
        detailed_findings_ja=detailed_findings_ja,
        chapters=chapters,
        claims=claims,
        published_at=publish_date,
    )

    today_str = date.today().isoformat()
    source_scope = f"YouTubeメタデータ（長:{length_sec}s, 投稿:{author}）" + (f", 字幕実発話{len(cues)}件 [{engine_used}]" if cues else f", 字幕なし [{engine_used}]")

    has_real_captions = (len(cues) > 0 and transcript_status != "NOT_ACQUIRED")
    formatted_raw_cues = [{"start": c[0], "end": c[1], "text": c[2]} for c in cues]

    receipt = {
        "schema_version": "research_receipt_v1",
        "notebook_url": NOTEBOOK_URL,
        "checked_at": today_str,
        "notebook_readback": "UNKNOWN",
        "github_dedup_status": "PASS",
        "real_captions_acquired": has_real_captions,
        "raw_cues": formatted_raw_cues,
        "videos": [
            {
                "video_id": video_id,
                "title": title,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "published_at": publish_date if publish_date else "UNKNOWN",
                "summary_ja": summary_ja,
                "source_scope": sanitize_text(source_scope, 175, max_newlines=1),
                "notebook_source_id": "UNKNOWN",
                "notebook_readback": "UNKNOWN",
                "changes": ["NEW"],
                "logical_id": f"youtube:{video_id}:research",
                "transcript_logical_id": f"youtube:{video_id}:transcript",
                "related_transcript_id": f"youtube:{video_id}:transcript",
                "transcript_status": transcript_status,
                "detailed_findings_ja": detailed_findings_ja,
                "chapters": chapters[:25],
                "claims": claims[:12],
                "related_records": related_records[:10],
            }
        ],
    }
    return receipt, engine_used, model_used


def run_notebook_registration_only(
    video_id: str,
    research_md_path: Path,
    video_title: str = "YouTube Video",
    mock_cdp: bool = False,
    mock_sources: Optional[List[str]] = None,
    cues: Optional[List[Any]] = None,
    include_youtube_url: bool = False,
) -> Dict[str, Any]:
    """Resume notebook registration for videos already committed to GitHub."""
    if include_youtube_url:
        raise ValueError("YouTube URL単体ソースの登録は廃止されました（2026-10-20 ユーザー確定仕様）。")
    print(f"\n[RESUME NOTEBOOK INGEST] GitHub登録済み動画 '{video_id}' のNotebook登録状態を確認・再開します。")
    v_url = f"https://www.youtube.com/watch?v={video_id}"

    # If cues not provided, fetch captions to support Transcript OKF source
    if cues is None and not mock_cdp:
        try:
            player_data = verify_timestamps.fetch_player(video_id)
            if player_data:
                _, fetched_cues, _ = fetch_actual_captions(player_data)
                if fetched_cues:
                    cues = fetched_cues
                    print(f"  - [RESUME] 実字幕cuesを取得しました ({len(cues)}件)")
        except Exception as ex:
            print(f"  - [WARNING] 字幕再取得に失敗しました: {ex}")

    # If cues still missing, refuse to falsely complete 2-source OKF
    if not cues and not mock_sources:
        print("  - [WARNING] 実字幕Cueが未取得です。仮資料での完全SUCCESSは遮断されます (PARTIAL_NO_SUBTITLES)。")

    nb_res = notebook_auto_ingest.ingest_and_verify_notebook(
        video_id=video_id,
        video_url=v_url,
        video_title=video_title,
        research_md_path=research_md_path,
        cues=cues,
        mock_cdp=mock_cdp,
        mock_sources=mock_sources,
    )
    return nb_res


def evaluate_final_status(
    real_content_acquired: bool,
    engine_used: str,
    model_used: str,
    research_note_generated: bool,
    github_push_success: bool,
    remote_head_matched: bool,
    remote_research_readback_matched: bool,
    remote_registry_readback_matched: bool,
    notebook_youtube_readback: bool,
    notebook_research_readback: bool,
    qa_verified: bool,
    no_push: bool,
    is_2_source_okf_verified: bool = False,
    notebook_transcript_readback: bool = False,
    independent_sources_distinct: bool = True,
    is_mock: bool = False,
    has_canonical_url: bool = True,
    has_mutual_logical_links: bool = True,
) -> Tuple[str, List[str]]:
    """Strictly evaluate whether execution is a full SUCCESS or PARTIAL/FAILED.
    
    Full SUCCESS_2_SOURCE_OKF requires ALL 11 conditions PLUS 2-Source OKF independence and metadata integrity.
    Anti-false-pass rules:
    - Drive sync alone is NOT sufficient.
    - Chrome tab detection alone is NOT sufficient.
    - Double counting of same item is NOT sufficient.
    - Mock execution is flagged as is_mock=True and BLOCKS SUCCESS_2_SOURCE_OKF.
    - Captionless placeholder is NOT permitted.
    """
    reasons = []

    if is_mock:
        reasons.append("Mockシミュレーション実行のため実機検証未完了 (is_mock=True)")
    if no_push:
        reasons.append("no_pushフラグが指定されているためGitHubリモート未反映")
    if not github_push_success:
        reasons.append("GitHubリモートPush未実行または失敗")
    if not remote_head_matched:
        reasons.append("リモートHEADハッシュ不一致")
    if not remote_research_readback_matched:
        reasons.append("リモート研究ノート本文のSHA-256不一致または取得失敗")
    if not remote_registry_readback_matched:
        reasons.append("リモートregistry.jsonのSHA-256不一致または取得失敗")
    if not real_content_acquired:
        reasons.append("実動画字幕（cue 1件以上）が未取得 (仮資料は不許可)")
    if not has_canonical_url:
        reasons.append("両資料（字幕原文OKF・研究ノートOKF）に元YouTube URLが存在していない")
    if not has_mutual_logical_links:
        reasons.append("両資料（字幕原文OKF・研究ノートOKF）の相互論理リンク（:transcript ↔ :research）が存在していない")
    if engine_used != "GEMINI_API_LIVE":
        reasons.append(f"AIによるLIVE研究要約が未実行 (engine: {engine_used})")
    if model_used != "gemini-3.8-flash":
        reasons.append(f"公式モデル gemini-3.8-flash が未使用 (model: {model_used})")
    if not research_note_generated:
        reasons.append("研究ノートMarkdownが未生成")
    if not notebook_research_readback:
        reasons.append("NotebookLM上の研究ノート追加・読み戻し未完了")
    if not notebook_transcript_readback:
        reasons.append("NotebookLM上の字幕原文OKF独立ソース追加・読み戻し未完了 (1動画2ソースMVP契約未達)")
    if not (is_2_source_okf_verified and independent_sources_distinct):
        reasons.append("NotebookLM上の研究ノートOKFと字幕原文OKFが別々の独立した2要素として実画面立証されていない (同一要素二重カウント排除)")
    if not qa_verified:
        reasons.append("自然言語QA検索による第1位検出未検証")

    if not reasons:
        return "SUCCESS_2_SOURCE_OKF", []

    # Map to specific PARTIAL status
    if is_mock:
        return "PARTIAL_MOCK_VERIFIED", reasons
    if not real_content_acquired:
        return "PARTIAL_NO_SUBTITLES", reasons
    if no_push:
        return "PARTIAL_NO_PUSH", reasons
    if not (has_canonical_url and has_mutual_logical_links):
        return "PARTIAL_METADATA_INCOMPLETE", reasons
    if engine_used == "LOCAL_TRANSCRIPT_EXTRACTION":
        return "PARTIAL_LOCAL_EXTRACTION", reasons
    if not (remote_research_readback_matched and remote_registry_readback_matched):
        return "PARTIAL_READBACK_MISMATCH", reasons
    if not qa_verified:
        return "PARTIAL_QA_MISMATCH", reasons
    if not notebook_research_readback:
        return "PARTIAL_NOTEBOOK_PENDING", reasons
    if not notebook_transcript_readback or not (is_2_source_okf_verified and independent_sources_distinct):
        return "PARTIAL_2_SOURCE_OKF_PENDING", reasons

    return "PARTIAL", reasons



def run_pipeline(
    url: str,
    drive_inbox: Optional[Path] = None,
    dry_run: bool = False,
    no_push: bool = False,
    gemini_api_key: Optional[str] = None,
    gemini_model: str = DEFAULT_GEMINI_MODEL,
    enable_live_gemini: bool = False,
    relay_via_drive: bool = False,
    mock_cdp: bool = False,
    include_youtube_url: bool = False,
    notebook_backend: str = "cdp",
    notebook_id: Optional[str] = None,
    notebook_live: bool = False,
    notebook_client: Any = None,
    fetch_transcript: Any = None,
    fetch_video_meta: Any = None,
    paragraph_anchors: Optional[bool] = None,
) -> Dict[str, Any]:
    """Execute complete automated research pipeline from URL to GitHub commit & verification.

    notebook_backend="notebooklm-py" のときは Notebook 登録を notebooklm_py_ingest.run_ingest で行う
    （既定は計画のみ。書き込みは notebook_live と notebook_id の両方が必要）。
    """
    if include_youtube_url:
        raise ValueError("YouTube URL単体ソースの登録は廃止されました（2026-10-20 ユーザー確定仕様）。")
    if notebook_backend not in NOTEBOOK_BACKENDS:
        raise ValueError(f"notebook_backend は {NOTEBOOK_BACKENDS} のいずれか: {notebook_backend}")
    if notebook_live and notebook_backend != "notebooklm-py":
        raise ValueError("Notebookへの --live 書き込みは notebook_backend='notebooklm-py' のときだけ使えます。")
    if notebook_live and not notebook_id:
        return {"status": "LIVE_REQUIRES_NOTEBOOK_ID", "notebook_ingest": {"status": "LIVE_REQUIRES_NOTEBOOK_ID", "writes": []}}
    py_nb = dict(notebook_id=notebook_id, live=notebook_live, client=notebook_client, fetch_transcript=fetch_transcript,
                 paragraph_anchors=paragraph_anchors)  # None=notebooklm_py_ingest.DEFAULT_PARAGRAPH_ANCHORS
    today_str = date.today().isoformat()
    print("=" * 70)
    print(f"[PIPELINE START] AI技術研究室 完全自動化研究パイプライン 開始 (v2.2, Model: {gemini_model})")
    print(f"入力URL: {url}")
    print("=" * 70)

    # 0. Early repository and branch verification BEFORE ANY FILE CHANGES
    verify_target_branch_early(root=ROOT, target_branch=DEFAULT_TARGET_BRANCH)
    print(f"[0/8] ブランチ検証合格: {DEFAULT_TARGET_BRANCH}")

    # 1. Extract video ID & Check duplication (First line of defense)
    video_id = intake_url.extract_youtube_id(url)
    if not video_id:
        raise ValueError(f"有効なYouTube動画IDを抽出できませんでした: {url}")
    print(f"[1/8] 動画ID抽出成功: {video_id}")

    dedup_res = intake_url.check_url_intake(url, root=ROOT)
    dedup_status = dedup_res.get("status")

    # Resume support: If already registered on GitHub, check if notebook registration needs to be resumed
    if dedup_status == "ALREADY_REGISTERED":
        res_path_str = dedup_res.get("research_path")
        res_path = ROOT / res_path_str if res_path_str else None

        # 1. GitHub研究ノートを再解析しない
        # 2. Gemini APIを再実行しない
        # 3. GitHubへ再Pushしない

        # 4. Check registry.json record using 'records' key (not 'videos')
        reg_data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8")) if REGISTRY_PATH.exists() else {}
        reg_records = reg_data.get("records", [])
        reg_record = next((r for r in reg_records if r.get("video_id") == video_id), {})

        if res_path and res_path.exists() and notebook_backend == "notebooklm-py":
            print(f"\n[ALREADY_REGISTERED] 動画 '{video_id}' のGitHub研究ノートは確認済み。notebooklm-py でNotebookの不足分を確認します...")
            nb_res = run_notebooklm_py_step(
                video_id, dedup_res.get("title") or f"YouTube Video {video_id}", res_path, **py_nb
            )
            return {
                "status": NOTEBOOKLM_PY_RESUME_STATUS.get(nb_res["status"], nb_res["status"]),
                "video_id": video_id,
                "notebook_backend": notebook_backend,
                "notebook_ingest": nb_res,
                "is_2_source_okf_verified": nb_res["status"] in ("SUCCESS_2_SOURCE_OKF", "NO_OP"),
                "details": dedup_res,
            }

        if res_path and res_path.exists():
            print(f"\n[ALREADY_REGISTERED] 動画 '{video_id}' のGitHub研究ノートは確認済みです。Notebook登録状態を実画面から読み戻します...")
            nb_res = run_notebook_registration_only(
                video_id=video_id,
                research_md_path=res_path,
                video_title=dedup_res.get("title", f"YouTube Video {video_id}"),
                mock_cdp=mock_cdp,
                include_youtube_url=include_youtube_url,
            )
            actions = nb_res.get("actions_taken", [])
            is_2_source = nb_res.get("is_2_source_okf_verified", False)
            if nb_res.get("is_full_success") and not actions:
                status_name = "SUCCESS_2_SOURCE_OKF" if is_2_source else "ALREADY_REGISTERED"
                print(f"[NOTEBOOK_ALREADY_CONFIRMED] Notebook実画面に全必要ソースが既に存在することを確認しました ({status_name})。追加処理をスキップし安全停止します。")
                return {
                    "status": status_name,
                    "video_id": video_id,
                    "notebook_ingest": nb_res,
                    "is_2_source_okf_verified": is_2_source,
                    "details": dedup_res,
                }
            elif nb_res.get("is_full_success"):
                status_name = "SUCCESS_2_SOURCE_OKF" if is_2_source else "RESUMED_NOTEBOOK_INGEST"
                print(f"[RESUMED_NOTEBOOK_INGEST] 不足していたNotebookソースの追加と再読み戻しに成功しました ({status_name})。")
                return {
                    "status": status_name,
                    "video_id": video_id,
                    "notebook_ingest": nb_res,
                    "is_2_source_okf_verified": is_2_source,
                    "details": dedup_res,
                }
            else:
                return {
                    "status": "RESUMED_NOTEBOOK_INGEST_PARTIAL",
                    "video_id": video_id,
                    "notebook_ingest": nb_res,
                    "is_2_source_okf_verified": is_2_source,
                    "details": dedup_res,
                }

        print(f"\n[STOP: {dedup_status}] 【登録済み・完全処理済みのため処理を安全停止します】")
        print(f"動画ID: {video_id}")
        print(f"タイトル: {dedup_res.get('title')}")
        print(f"研究ノート: {dedup_res.get('research_path')}")
        return {
            "status": dedup_status,
            "video_id": video_id,
            "details": dedup_res,
        }

    if dedup_status in ("BLOCKED_GITHUB_UNREACHABLE", "HALT", "STATUS_HALT"):
        print(f"\n[STOP: {dedup_status}] 【安全停止判定を尊重して処理を中止します】")
        return {
            "status": dedup_status,
            "video_id": video_id,
            "details": dedup_res,
        }

    # 2. Fetch YouTube metadata & captions
    meta_note = None
    if dry_run and notebook_backend == "notebooklm-py" and notebook_id:
        # 棚を読む dry-run（読み取りのみの通信あり）では、計画の題名を本物にするため題名・投稿日時だけ取る。
        # 字幕トラック情報は捨てて、研究レシート側で字幕を取りに行かない。
        print(f"[2/8] [DRY RUN] YouTubeの題名・投稿日時だけを読み取ります ({video_id})...")
        try:
            meta = (fetch_video_meta or fetch_video_meta_readonly)(video_id) or {}
        except Exception as ex:  # 取れなければ仮の題名で計画を続ける
            meta, meta_note = {}, f"題名の取得に失敗（{type(ex).__name__}）。計画の題名は仮名。"
        details = (meta.get("player_data") or {}).get("videoDetails") or {}
        player_data = {"videoDetails": dict(details, videoId=video_id)}
        publish_date = meta.get("published_at")
        if not details.get("title") and not meta_note:
            meta_note = "題名を取得できなかったため、計画の題名は仮名。"
    elif dry_run:
        # Dry run must be fully offline: no YouTube player/watch/caption requests.
        print(f"[2/8] [DRY RUN] 外部通信を行わず、動画IDのみのメタデータでプレビューします ({video_id})。")
        player_data = {"videoDetails": {"videoId": video_id}}
        publish_date = None
    else:
        print(f"[2/8] YouTubeメタデータ＆字幕本文取得中 ({video_id})...")
        player_data = verify_timestamps.fetch_player(video_id)
        if not player_data or "videoDetails" not in player_data:
            raise RuntimeError(f"YouTubeプレイヤーデータの取得に失敗しました: {video_id}")

        publish_date = verify_timestamps.fetch_watch_publish_date(video_id)
    vd = player_data.get("videoDetails", {})
    print(f"  - タイトル: {vd.get('title')}")
    print(f"  - 投稿者: {vd.get('author')}")
    print(f"  - 動画長: {vd.get('lengthSeconds')} 秒")
    print(f"  - 公開日: {publish_date or 'UNKNOWN'}")

    # 3. Build research receipt conformant to contract_spec_v1
    print(f"[3/8] OKF v0.2形式 研究レシート合成中 (Model: {gemini_model})...")
    key_to_use = gemini_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    receipt, engine_used, model_used = build_research_receipt(
        video_id=video_id,
        player_data=player_data,
        publish_date=publish_date,
        gemini_api_key=key_to_use,
        gemini_model=gemini_model,
        enable_live_gemini=enable_live_gemini,
        dry_run=dry_run,
    )

    if dry_run and notebook_backend == "notebooklm-py":
        # 手順8の計画だけを出す（書き込み0）。--notebook-id が無ければ棚も読まない（DRY_RUN_PLAN_OFFLINE）。
        print("[8/8] [DRY RUN] notebooklm-py でNotebookへの追加予定を確認します（書き込みなし）...")
        receipt_vids = receipt.get("videos") or [{}]
        note_preview = receipt_to_research.render(receipt_vids[0], today_str) if receipt_vids[0] else ""
        nb_res = run_notebooklm_py_step(
            video_id, vd.get("title") or f"YouTube Video {video_id}", None,
            published_at=publish_date, research_note_text=note_preview,
            **dict(py_nb, live=False),
        )
        if meta_note:
            nb_res.setdefault("notes", []).append(meta_note)
        for p in nb_res.get("plan_details", []):
            print(f"  - 追加予定: {p['kind']} / {p['title']} / {p['logical_id']}")
        if "paragraph_anchors" in nb_res:
            print(f"  - 字幕の段落目印（▶HH:MM:SS）: {'ON' if nb_res['paragraph_anchors'] else 'OFF'}")
        print(f"\n[DRY RUN] Notebook計画: {nb_res['status']}。GitHub・Notebook・Driveへの書き込みゼロで終了します。")
        return {
            "status": NOTEBOOKLM_PY_RESUME_STATUS.get(nb_res["status"], nb_res["status"]),
            "video_id": video_id,
            "notebook_backend": notebook_backend,
            "notebook_ingest": nb_res,
            "receipt": receipt,
            "engine_used": engine_used,
            "model_used": model_used,
        }

    if dry_run:
        print("\n[DRY RUN] プレビュー完了。外部・Drive・ローカルファイルへの副作用ゼロで終了します。")
        return {
            "status": "DRY_RUN_COMPLETE",
            "video_id": video_id,
            "receipt": receipt,
            "engine_used": engine_used,
            "model_used": model_used,
        }

    # Save receipt to scratch
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    scratch_receipt_path = SCRATCH_DIR / f"receipt_{video_id}.json"
    scratch_receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  - ローカル受渡し保存: {scratch_receipt_path}")

    # Handling Drive relay mode (Mutually exclusive with direct local Git push)
    drive_saved_path = None
    if relay_via_drive:
        inbox_target = drive_inbox or (DEFAULT_DRIVE_INBOX if DEFAULT_DRIVE_INBOX.exists() else None)
        if not inbox_target or not inbox_target.exists():
            raise RuntimeError(f"Drive中継モード指定ですが受信トレイが存在しません: {inbox_target}")
        drive_receipt_path = inbox_target / f"{video_id}_research_receipt_v1.json"
        drive_receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        drive_saved_path = str(drive_receipt_path)
        print(f"  - [DRIVE_RELAY_MODE] Google Drive受信トレイ配置成功: {drive_saved_path}")
        print("  - 二重保存防止: ローカルGit Pushは行わず、GASリレーの処理を待機します。")
        return {
            "status": "DRIVE_RELAY_DISPATCHED",
            "video_id": video_id,
            "drive_saved": drive_saved_path,
        }

    # 4. Apply receipt to GitHub repository (generate research markdown, update registry)
    print("[4/8] GitHubリポジトリへ研究ノート適用・台帳更新中 (リモート最新走査有効)...")
    summary, touched = receipt_to_research.process_receipt_data(
        data=receipt,
        root=ROOT,
        apply=True,
        allow_updates=True,
        check_remote_branches=True,
        fetch_remote=True,
        allow_stale_remotes=True,
        sync_index=True,
        refresh_existing=True,
    )
    print(f"  - 新規作成数: {summary.get('new_records', 0)}")
    print(f"  - 更新ファイル数: {len(touched)}")
    research_note_generated = summary.get("new_records", 0) > 0 or len(touched) > 0

    # 5. Rebuild knowledge catalog via official query_research API and verify file
    print("[5/8] 知識カタログ再構築中 (video_knowledge_catalog.json)...")
    cat_path = ROOT / "automation" / "gemini-notebook" / "state" / "video_knowledge_catalog.json"
    catalog_res, _ = query_research.build_video_knowledge_catalog(root=ROOT, write_path=cat_path)
    if not cat_path.exists() or cat_path.stat().st_size == 0:
        raise RuntimeError(f"知識カタログの保存に失敗しました: {cat_path}")
    print(f"  - カタログ登録総数: {catalog_res.get('total_records')} (動画数: {catalog_res.get('total_video_records')})")

    # 6. Git commit and push (Safety: non-default branch only)
    current_branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    print(f"[6/8] Gitコミット＆Push実行中 (ブランチ: {current_branch})...")
    files_to_add = ["registry.json", "automation/gemini-notebook/state/video_knowledge_catalog.json"]
    for t in touched:
        rel = str(Path(t).relative_to(ROOT)).replace("\\", "/")
        if rel not in files_to_add:
            files_to_add.append(rel)

    subprocess.check_call(["git", "add"] + files_to_add, cwd=ROOT)
    commit_msg = f"feat(research): auto-ingest video {video_id} via auto research pipeline v2.2"
    subprocess.check_call(["git", "commit", "-m", commit_msg], cwd=ROOT)
    
    commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    print(f"  - ローカルコミット完了: {commit_sha[:7]} ({commit_msg})")

    # Verification flags
    github_push_success = False
    remote_head_matched = False
    remote_research_readback_matched = False
    remote_registry_readback_matched = False
    remote_head = "UNKNOWN"
    research_md_path = f"research/{today_str}-{video_id}-gemini-notebook.md"

    if not no_push:
        subprocess.check_call(["git", "push", "origin", current_branch], cwd=ROOT)
        github_push_success = True
        print(f"  - リモートPush完了: origin/{current_branch}")

        # Real remote readback using git ls-remote
        ls_remote_out = subprocess.check_output(
            ["git", "ls-remote", "origin", f"refs/heads/{current_branch}"],
            cwd=ROOT,
            text=True,
        ).strip()
        if ls_remote_out:
            remote_head = ls_remote_out.split()[0]
        remote_head_matched = (remote_head == commit_sha)
        if not remote_head_matched:
            raise RuntimeError(f"読み戻し不一致エラー: ローカルHEAD({commit_sha[:7]}) と 実際のリモートHEAD({remote_head[:7]}) が一致しません。")
        print(f"  - 実際のリモートHEAD読み戻し確認完了 (Remote HEAD: {remote_head[:7]})")

        # Remote Research Markdown content readback & SHA-256 comparison
        try:
            remote_md_sample = subprocess.check_output(
                ["git", "show", f"origin/{current_branch}:{research_md_path}"],
                cwd=ROOT,
                encoding="utf-8",
                errors="replace",
            )
            local_md_sample = (ROOT / research_md_path).read_text(encoding="utf-8")
            if compute_sha256(remote_md_sample) == compute_sha256(local_md_sample):
                remote_research_readback_matched = True
                print(f"  - リモート研究ノート本文SHA-256一致検証成功: {research_md_path}")
            else:
                print(f"  - [WARNING] リモート研究ノート本文SHA-256不一致")
        except Exception as ex:
            print(f"  - [WARNING] リモート研究ノート本文読み戻し失敗: {ex}")

        # Remote registry.json content readback & SHA-256 comparison
        try:
            remote_reg_sample = subprocess.check_output(
                ["git", "show", f"origin/{current_branch}:registry.json"],
                cwd=ROOT,
                encoding="utf-8",
                errors="replace",
            )
            local_reg_sample = (ROOT / "registry.json").read_text(encoding="utf-8")
            if compute_sha256(remote_reg_sample) == compute_sha256(local_reg_sample):
                remote_registry_readback_matched = True
                print(f"  - リモートregistry.json本文SHA-256一致検証成功")
            else:
                print(f"  - [WARNING] リモートregistry.json本文SHA-256不一致")
        except Exception as ex:
            print(f"  - [WARNING] リモートregistry.json読み戻し失敗: {ex}")

    # 7. QA System self-verification via official answer_question API
    print("[7/8] 自然言語QA検索エンジンでの動作実証中...")
    qa_res = query_research.answer_question(f"{vd.get('title')[:30]} について教えて", root=ROOT)
    matched_records = qa_res.get("step2_matched_records", [])
    top_rec = matched_records[0] if matched_records else {}
    top_vid = top_rec.get("video_id")
    qa_score = top_rec.get("score", 0)

    qa_verified = (top_vid == video_id)
    if qa_verified:
        print(f"  - QA検索第1位スコア検出: {top_vid} (スコア: {qa_score})")
    else:
        print(f"  - [WARNING] QA検索不一致: 期待値 '{video_id}' vs 検出第1位 '{top_vid}' (スコア: {qa_score})")

    # 8. Notebook Auto Ingest & Live Readback
    print("[8/8] Gemini Notebook自動ソース登録・実画面Readback検証中...")
    raw_cues_data = receipt.get("raw_cues", [])
    cues_for_ingest = [(c["start"], c["end"], c["text"]) for c in raw_cues_data] if raw_cues_data else None

    if notebook_backend == "notebooklm-py":
        nb_res = run_notebooklm_py_step(
            video_id, vd.get("title", f"YouTube Video {video_id}"), ROOT / research_md_path,
            cues=cues_for_ingest, published_at=publish_date, **py_nb
        )
        nb_ok = nb_res["status"] in ("SUCCESS_2_SOURCE_OKF", "NO_OP")
        notebook_youtube_readback = False  # URL単体ソースは登録しない（R2）
        notebook_research_readback = nb_ok
        notebook_transcript_readback = nb_ok
        is_2_source_okf_verified = nb_ok
        nb_res.setdefault("independent_sources_distinct", nb_ok)
        nb_res.setdefault("is_mock", False)
    else:
        nb_res = notebook_auto_ingest.ingest_and_verify_notebook(
            video_id=video_id,
            video_url=f"https://www.youtube.com/watch?v={video_id}",
            video_title=vd.get("title", f"YouTube Video {video_id}"),
            research_md_path=ROOT / research_md_path,
            cues=cues_for_ingest,
            mock_cdp=mock_cdp,
            published_at=publish_date,
        )
        nb_rb = nb_res.get("readback", {})
        notebook_youtube_readback = bool(nb_rb.get("youtube_source_found"))
        notebook_research_readback = bool(nb_rb.get("research_note_found"))
        notebook_transcript_readback = bool(nb_rb.get("transcript_source_found"))
        is_2_source_okf_verified = bool(nb_res.get("is_2_source_okf_verified"))

    # Final Strict SUCCESS Evaluation (11 Mandatory Conditions + 2-Source OKF + Metadata Integrity)
    receipt_vids = receipt.get("videos", [])
    first_vid_meta = receipt_vids[0] if receipt_vids else {}
    research_file = ROOT / research_md_path
    rn_text = research_file.read_text(encoding="utf-8") if research_file.exists() else ""
    drive_target = Path(nb_res.get("drive_sync", {}).get("target_dir", ""))
    drive_tr_file = drive_target / f"{video_id}_transcript_okf.md" if drive_target else None
    tr_text = drive_tr_file.read_text(encoding="utf-8") if (drive_tr_file and drive_tr_file.exists()) else ""

    link_check = notebook_auto_ingest.verify_mutual_okf_links(
        research_note_text=rn_text,
        transcript_okf_text=tr_text,
        video_id=video_id,
        video_url=f"https://www.youtube.com/watch?v={video_id}",
    ) if (rn_text and tr_text) else {}

    has_canonical_url = bool(
        link_check.get("urls_match")
        or (first_vid_meta.get("url") and "youtube.com/watch?v=" in first_vid_meta.get("url", ""))
    )
    has_mutual_logical_links = bool(
        link_check.get("mutual_matches")
        or (
            first_vid_meta.get("logical_id")
            and first_vid_meta.get("transcript_logical_id")
            and f"youtube:{video_id}:research" in first_vid_meta.get("logical_id", "")
            and f"youtube:{video_id}:transcript" in first_vid_meta.get("transcript_logical_id", "")
        )
    )

    final_status, fail_reasons = evaluate_final_status(
        real_content_acquired=bool(receipt.get("real_captions_acquired", False)),
        engine_used=engine_used,
        model_used=model_used,
        research_note_generated=research_note_generated,
        github_push_success=github_push_success,
        remote_head_matched=remote_head_matched,
        remote_research_readback_matched=remote_research_readback_matched,
        remote_registry_readback_matched=remote_registry_readback_matched,
        notebook_youtube_readback=notebook_youtube_readback,
        notebook_research_readback=notebook_research_readback,
        qa_verified=qa_verified,
        no_push=no_push,
        is_2_source_okf_verified=is_2_source_okf_verified,
        notebook_transcript_readback=notebook_transcript_readback,
        independent_sources_distinct=bool(nb_res.get("independent_sources_distinct", is_2_source_okf_verified)),
        is_mock=bool(nb_res.get("is_mock", mock_cdp)),
        has_canonical_url=has_canonical_url,
        has_mutual_logical_links=has_mutual_logical_links,
    )

    print("=" * 70)
    print(f"[{final_status}] 完全自動化研究パイプライン 完了")
    print(f"動画ID: {video_id}")
    print(f"コミット: {commit_sha[:7]} (Remote: {remote_head[:7]})")
    print(f"台帳総数: {catalog_res.get('total_video_records')} 本")
    print(f"Notebook用Markdown: {research_md_path}")
    print(f"Drive Notebook同期先: {nb_res.get('drive_sync', {}).get('target_dir')}")
    print(f"2ソースOKF完全立証: {is_2_source_okf_verified}")
    if final_status == "SUCCESS_2_SOURCE_OKF":
        print("状態区分: 正式完成 (SUCCESS_2_SOURCE_OKF) - 研究ノートOKFと字幕原文OKFの2ソース独立実在を完全立証")
    elif final_status == "PARTIAL_2_SOURCE_OKF_PENDING":
        print("状態区分: 暫定状態 (PARTIAL_2_SOURCE_OKF_PENDING) - 旧式（YouTube URL＋研究ノート）のみ確認。正式完成には字幕原文OKFの独立登録が必須")
    else:
        print(f"状態区分: 部分完了・未確認 ({final_status})")
    if fail_reasons:
        print("未達項目・制限事項:")
        for r in fail_reasons:
            print(f"  - {r}")
    print("=" * 70)

    return {
        "status": final_status,
        "video_id": video_id,
        "commit_sha": commit_sha,
        "remote_head": remote_head,
        "total_videos": catalog_res.get("total_video_records"),
        "research_path": research_md_path,
        "drive_saved": drive_saved_path,
        "qa_verified": qa_verified,
        "engine_used": engine_used,
        "model_used": model_used,
        "notebook_backend": notebook_backend,
        "notebook_ingest": nb_res,
        "is_2_source_okf_verified": is_2_source_okf_verified,
        "is_full_success": (final_status == "SUCCESS_2_SOURCE_OKF"),
        "fail_reasons": fail_reasons,
    }


NOTEBOOK_BACKENDS = ("cdp", "notebooklm-py")
# notebooklm-py の結果を、登録済み動画の再開時のパイプライン状態名へ寄せる（それ以外はそのまま返す）
NOTEBOOKLM_PY_RESUME_STATUS = {
    "NO_OP": "ALREADY_REGISTERED",
    "SUCCESS_2_SOURCE_OKF": "SUCCESS_2_SOURCE_OKF",
}


def fetch_video_meta_readonly(video_id: str) -> Dict[str, Any]:
    """YouTubeの題名などと投稿日時を読み取る（書き込みなし）。dry-run の計画表示用。"""
    return {
        "player_data": verify_timestamps.fetch_player(video_id),
        "published_at": verify_timestamps.fetch_watch_publish_date(video_id),
    }


def run_notebooklm_py_step(
    video_id: str,
    video_title: str,
    research_md_path: Optional[Path],
    cues: Optional[List[Any]] = None,
    published_at: Optional[str] = None,
    notebook_id: Optional[str] = None,
    live: bool = False,
    client: Any = None,
    fetch_transcript: Any = None,
    research_note_text: Optional[str] = None,
    paragraph_anchors: Optional[bool] = None,
) -> Dict[str, Any]:
    """notebooklm_py_ingest.run_ingest で字幕取得・不足分の登録・読み戻しを1回で行う。

    client を渡さなければ notebook_id から実CLIクライアントを作る（notebook_id も無ければ未接続の計画のみ）。
    fetch_transcript を渡さなければ実行PCからYouTubeの字幕と投稿日時を取る（youtube-transcript-api→timedtext）。
    字幕全文OKFは約1分ごとの段落本文で、各段落の先頭に時刻目印の1行が付く（paragraph_anchors 既定ON。発話ごとの時刻は入れない）。
    """
    import notebooklm_py_ingest

    if client is None and notebook_id:
        client = notebooklm_py_ingest.NotebookLmCliClient(notebook_id)
    if fetch_transcript is None:
        fetch_transcript = notebooklm_py_ingest.fetch_youtube_transcript
    if research_note_text is not None:
        note_text = research_note_text  # dry-run: 保存前の研究ノート（メモリ上）
    else:
        note_text = research_md_path.read_text(encoding="utf-8") if research_md_path and research_md_path.exists() else ""
    res = notebooklm_py_ingest.run_ingest(
        client,
        video_id=video_id,
        video_title=video_title,
        research_note_text=note_text,
        cues=cues,
        live=live,
        notebook_id=notebook_id,
        published_at=published_at,
        fetch_transcript=fetch_transcript,
        paragraph_anchors=paragraph_anchors,
    )
    res.pop("precheck", None)
    res.pop("postcheck", None)
    res["new_source_ids"] = [w["source_id"] for w in res.get("writes", []) if w.get("source_id")]
    return res


SUCCESS_CLI_STATUSES = (
    "SUCCESS_2_SOURCE_OKF",
    "SUCCESS",  # 後方互換性維持
    "ALREADY_REGISTERED",
    "RESUMED_NOTEBOOK_INGEST",
    "DRY_RUN_COMPLETE",
    "DRIVE_RELAY_DISPATCHED",
    "DRY_RUN_PLAN",  # notebooklm-py: 計画のみ（書き込み0）
    "DRY_RUN_PLAN_OFFLINE",
)


def main(args_list: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AI技術研究室 完全自動化研究パイプライン v2.2")
    parser.add_argument("url", nargs="?", default=None, help="YouTube動画URL (例: https://www.youtube.com/watch?v=...)")
    parser.add_argument("--url", dest="url_opt", default=None, help="YouTube動画URL (オプション形式)")
    parser.add_argument("--drive-inbox", help="Google Drive受信トレイのカスタムパス", default=None)
    parser.add_argument("--dry-run", action="store_true", help="保存・コミット・Push・外部APIをスキップしてプレビュー生成")
    parser.add_argument("--no-push", action="store_true", help="コミットまで行いリモートPushはスキップ")
    parser.add_argument("--gemini-api-key", help="Google Gemini API Key (省略時は環境変数を参照)", default=None)
    parser.add_argument("--gemini-model", help=f"Geminiモデル名 (デフォルト: {DEFAULT_GEMINI_MODEL})", default=DEFAULT_GEMINI_MODEL)
    parser.add_argument("--enable-live-gemini", action="store_true", help="Gemini APIのLIVE実行を明示的に許可する（デフォルトは安全のため無効）")
    parser.add_argument("--relay-via-drive", action="store_true", help="ローカルGit Pushを行わずDrive配置によるGASリレーを優先する")
    parser.add_argument("--mock-cdp", action="store_true", help="テスト用Mock CDPモード")
    parser.add_argument("--include-youtube-url", action="store_true", help="廃止（2026-10-20）：指定するとエラーで停止する")
    parser.add_argument("--notebook-backend", choices=NOTEBOOK_BACKENDS, default="cdp", help="Notebook登録の方式（既定: cdp）")
    parser.add_argument("--notebook-id", help="notebooklm-py で登録するNotebookのID")
    parser.add_argument("--live", action="store_true", help="notebooklm-py でNotebookへ実際に書き込む（--notebook-id 必須）")
    parser.add_argument("--paragraph-anchors", action=argparse.BooleanOptionalAction, default=None,
                        help="字幕の各段落の先頭に時刻目印 ▶HH:MM:SS とURLを付ける（未指定なら notebooklm_py_ingest の既定。現在ON）")
    args = parser.parse_args(args_list)
    if args.live and args.notebook_backend != "notebooklm-py":
        parser.error("--live は --notebook-backend notebooklm-py のときだけ使えます。")
    if args.live and not args.notebook_id:
        parser.error("--live には --notebook-id の明示が必要です。")
    if args.include_youtube_url:
        parser.error("--include-youtube-url は廃止されました。YouTube URL単体ソースは登録しません（2026-10-20 ユーザー確定仕様）。")

    target_url = args.url or args.url_opt
    if not target_url:
        parser.error("YouTube動画URLを指定してください (位置引数または --url)")

    inbox_p = Path(args.drive_inbox) if args.drive_inbox else None
    res = run_pipeline(
        target_url,
        drive_inbox=inbox_p,
        dry_run=args.dry_run,
        no_push=args.no_push,
        gemini_api_key=args.gemini_api_key,
        gemini_model=args.gemini_model,
        enable_live_gemini=args.enable_live_gemini,
        relay_via_drive=args.relay_via_drive,
        mock_cdp=args.mock_cdp,
        include_youtube_url=args.include_youtube_url,
        notebook_backend=args.notebook_backend,
        notebook_id=args.notebook_id,
        notebook_live=args.live,
        paragraph_anchors=args.paragraph_anchors,
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res.get("status") in SUCCESS_CLI_STATUSES else 1


if __name__ == "__main__":
    sys.exit(main())
