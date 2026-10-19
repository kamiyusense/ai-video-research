#!/usr/bin/env python3
"""AI技術研究室 | 自動研究Loop統合パイプライン (auto_research_pipeline.py v2.0).

目的:
YouTube URLを起点とし、事前重複チェック -> 実際のYouTube字幕・メタデータ取得 ->
AI研究・要約処理 -> OKF v0.2形式研究ノート生成 -> GitHub正本保存 ->
リモート読み戻し検証 -> 自然言語QA実証までを自律実行する。

改善点 (v2.0):
1. [研究・要約] 概要欄整形ではなく、実際の字幕本文（cues）を取得・解析して研究ノートを生成。
2. [正確性] 未取得情報は UNKNOWN / null とし、架空の要約・発言・時刻を生成しない。
3. [Gemini API対応] GEMINI_API_KEY があれば Gemini 1.5/2.0 Flash REST API で高品質解析、
   未設定時はローカル字幕意味解析エンジンで根拠ある抽出を実行。
4. [エラー解消] query_research の正しい公開関数 (build_video_knowledge_catalog, answer_question) を呼出。
5. [Dry-Run] 外部・Drive・ローカルへの副作用を排除。
6. [読み戻し] git ls-remote / origin HEAD による実際のリモート状態検証。
7. [単一責任] ローカルGit Pushを正本保存責任とし、Drive/GASとの二重保存を防止。
"""
from __future__ import annotations

import argparse
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

DEFAULT_DRIVE_INBOX = Path("G:/マイドライブ/AI技術研究室_受信トレイ")
DEFAULT_TARGET_BRANCH = "feature/gemini-notebook-research-loop-20261016"
NOTEBOOK_URL = "https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7"


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


def fetch_actual_captions(player_data: Dict[str, Any]) -> Tuple[str, List[Tuple[float, float, str]], str]:
    """Fetch and parse actual caption track from YouTube player data.
    
    Returns:
        (transcript_status, cues, raw_xml_sample)
    """
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
            # We have real timed cues
            kind = tr.get("kind", "")
            status = "UNVERIFIED"  # Acquired and usable, though not formally human-verified
            return status, cues, raw_xml[:500]
    except Exception as ex:
        print(f"  - [DEBUG] 字幕取得エラー: {ex}")

    return "NOT_ACQUIRED", [], ""


def analyze_with_gemini_api(
    title: str,
    author: str,
    length_sec: int,
    cues: List[Tuple[float, float, str]],
    api_key: str,
) -> Optional[Dict[str, Any]]:
    """Analyze actual caption cues using Google Gemini Flash API via REST."""
    if not api_key:
        return None

    # Construct concise prompt with sampled/indexed transcript
    cues_text = []
    # Sample transcript with timestamps (avoid huge payload, fit in 30k tokens)
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
      "key_topics": ["キーワード1", "キーワード2"]
    }}
  ],
  "claims": [
    {{
      "text": "動画内の具体的な主張や発言内容（実際の字幕に基づく）",
      "status": "REPORTED_BY_AUTHOR",
      "timestamp_seconds": 発言の開始秒数(int)
    }}
  ]
}}
※架空の内容や推測の秒数は含めず、字幕に存在する発話・時刻のみを根拠にしてください。
"""

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
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
        print(f"  - [WARNING] Gemini API解析呼出に失敗 (フォールバックへ移行): {ex}")
        return None


def analyze_with_local_transcript_engine(
    title: str,
    author: str,
    length_sec: int,
    cues: List[Tuple[float, float, str]],
    desc: str,
    desc_chapters: List[int],
) -> Dict[str, Any]:
    """Deterministically analyze real caption text when external API is not configured."""
    if not cues:
        # No cues at all: based on metadata only, no fabricated transcript
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
        }

    # Group cues into sections based on timeline
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
        
        # Combine cue text for this segment
        combined_text = " ".join(c[2] for c in sec_cues)
        clean_text = re.sub(r"\s+", " ", combined_text).strip()
        
        # Extract characteristic sentence snippet
        sample_snippet = clean_text[:90] + ("..." if len(clean_text) > 90 else "")
        ch_title = f"区間 {st_sec // 60:02d}:{st_sec % 60:02d}〜{ed_sec // 60:02d}:{ed_sec % 60:02d} 発話分析"
        
        # Extract topics
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
            "summary_ja": sanitize_text(f"発話内容抜粋: {sample_snippet}", 280, max_newlines=1),
            "timestamp_source": "TIMESTAMPED_CAPTIONS",
            "key_topics": topics[:6],
        })
        section_summaries.append(f"{st_sec // 60:02d}:{st_sec % 60:02d}〜: {sample_snippet[:60]}")

        # Add claim from first and middle sections
        if i in (0, num_sections // 2):
            claims.append({
                "text": sanitize_text(f"動画内発話（{st_sec // 60:02d}:{st_sec % 60:02d}）: 「{sample_snippet[:150]}」", 450, max_newlines=1),
                "status": "REPORTED_BY_AUTHOR",
                "timestamp_seconds": st_sec,
                "timestamp_source": "TIMESTAMPED_CAPTIONS",
                "official_url": None,
            })

    # Build summary from real cues
    all_text = " ".join(c[2] for c in cues)
    summary_raw = f"{author}による技術解説「{title}」。字幕発話データ（全{total_cues}行）から内容を分析。中核発話: " + " / ".join(section_summaries[:2])
    summary_ja = sanitize_text(summary_raw, 280, max_newlines=2)

    findings = [
        f"【動画基本情報】",
        f"- 投稿者: {author} / 動画長: {length_sec}秒",
        f"- 字幕取得状況: UNVERIFIED（実字幕行数: {total_cues}行）",
        f"",
        f"【実字幕からの抽出知見・要約】",
    ] + [f"- {s}" for s in section_summaries[:4]] + [
        f"",
        f"【注意点】",
        f"- 本研究ノートはYouTubeから実際に取得した時間付き字幕テキストに基づき抽出されています。",
    ]

    return {
        "summary_ja": summary_ja,
        "detailed_findings_ja": "\n".join(findings[:20]),
        "chapters": chapters,
        "claims": claims,
    }


def build_research_receipt(
    video_id: str,
    player_data: Dict[str, Any],
    publish_date: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Synthesize conformant research_receipt_v1 from real metadata & actual caption text."""
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

    # 2. Analyze via AI (Gemini Flash API) or fallback to real local transcript engine
    ai_analysis = None
    if gemini_api_key and cues:
        print("  - Gemini API による字幕内容の研究・要約を実行中...")
        ai_analysis = analyze_with_gemini_api(title, author, length_sec, cues, gemini_api_key)

    if not ai_analysis:
        if gemini_api_key:
            print("  - [INFO] Gemini APIの解析がスキップ/失敗したため、ローカル字幕解析エンジンを適用します。")
        else:
            print("  - [INFO] GEMINI_API_KEY 未設定: ローカル字幕意味解析エンジンにより字幕本文を分析します。")
        ai_analysis = analyze_with_local_transcript_engine(title, author, length_sec, cues, desc, starts)

    summary_ja = ai_analysis.get("summary_ja", f"{title}の技術分析。")
    detailed_findings_ja = ai_analysis.get("detailed_findings_ja", "")
    chapters = ai_analysis.get("chapters", [])
    claims = ai_analysis.get("claims", [])

    # Candidate related records (Only candidate / unresolved, NEVER falsely confirmed without evidence)
    related_records = []
    title_and_summary = (title + " " + summary_ja).lower()
    if "okf" in title_and_summary:
        related_records.append({
            "target_id": "youtube:u3ka_AAb8qE",
            "relation": "EXTENDS",
            "note": "OKF知識管理の関連動画候補（内容照合待ち）",
            "status": "CANDIDATE",
            "evidence": "OKFキーワード含有",
        })
    if "rag" in title_and_summary:
        related_records.append({
            "target_id": "youtube:pRfC1DILDEM",
            "relation": "COMPLEMENTS",
            "note": "RAG探索設計の関連動画候補（内容照合待ち）",
            "status": "CANDIDATE",
            "evidence": "RAG技術キーワード含有",
        })

    today_str = date.today().isoformat()
    source_scope = f"YouTubeメタデータ（長:{length_sec}s, 投稿:{author}）" + (f", 字幕実発話{len(cues)}件" if cues else ", 字幕なし")

    receipt = {
        "schema_version": "research_receipt_v1",
        "notebook_url": NOTEBOOK_URL,
        "checked_at": today_str,
        "notebook_readback": "UNKNOWN",
        "github_dedup_status": "PASS",
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
                "transcript_status": transcript_status,
                "detailed_findings_ja": detailed_findings_ja,
                "chapters": chapters[:25],
                "claims": claims[:12],
                "related_records": related_records[:10],
            }
        ],
    }
    return receipt


def run_pipeline(
    url: str,
    drive_inbox: Optional[Path] = None,
    dry_run: bool = False,
    no_push: bool = False,
    gemini_api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute complete automated research pipeline from URL to GitHub commit & verification."""
    today_str = date.today().isoformat()
    print("=" * 70)
    print("[PIPELINE START] AI技術研究室 完全自動化研究パイプライン 開始")
    print(f"入力URL: {url}")
    print("=" * 70)

    # 1. Extract video ID & Check duplication (First line of defense)
    video_id = intake_url.extract_youtube_id(url)
    if not video_id:
        raise ValueError(f"有効なYouTube動画IDを抽出できませんでした: {url}")
    print(f"[1/7] 動画ID抽出成功: {video_id}")

    dedup_res = intake_url.check_url_intake(url, root=ROOT)
    if dedup_res.get("status") == "ALREADY_REGISTERED":
        print("\n[STOP: ALREADY REGISTERED] 【登録済み検知・即時安全停止】")
        print(f"動画ID: {video_id}")
        print(f"タイトル: {dedup_res.get('title')}")
        print(f"要約: {dedup_res.get('summary_ja')}")
        print(f"研究ノート: {dedup_res.get('research_path')}")
        return {
            "status": "ALREADY_REGISTERED",
            "video_id": video_id,
            "details": dedup_res,
        }

    # 2. Fetch YouTube metadata
    print(f"[2/7] YouTubeメタデータ＆字幕本文取得中 ({video_id})...")
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
    print("[3/7] OKF v0.2形式 研究レシート合成中 (字幕・実データに基づくAI研究)...")
    key_to_use = gemini_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    receipt = build_research_receipt(
        video_id=video_id,
        player_data=player_data,
        publish_date=publish_date,
        gemini_api_key=key_to_use,
    )

    if dry_run:
        print("\n[DRY RUN] プレビュー完了。外部への書き込み（Drive/ローカル/Git）を行わずに終了します。")
        return {
            "status": "DRY_RUN_COMPLETE",
            "video_id": video_id,
            "receipt": receipt,
        }

    # Save receipt to scratch
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    scratch_receipt_path = SCRATCH_DIR / f"receipt_{video_id}.json"
    scratch_receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  - ローカル受渡し保存: {scratch_receipt_path}")

    # Optional: Save to Drive inbox if explicitly configured
    drive_saved_path = None
    if drive_inbox and drive_inbox.exists():
        try:
            drive_receipt_path = drive_inbox / f"{video_id}_research_receipt_v1.json"
            drive_receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            drive_saved_path = str(drive_receipt_path)
            print(f"  - Google Drive受信トレイ配置: {drive_saved_path}")
        except Exception as e:
            print(f"  - [WARNING] Google Drive配置スキップ: {e}")

    # 4. Apply receipt to GitHub repository (generate research markdown, update registry)
    print("[4/7] GitHubリポジトリへ研究ノート適用・台帳更新中...")
    summary, touched = receipt_to_research.process_receipt_data(
        data=receipt,
        root=ROOT,
        apply=True,
        allow_updates=True,
        check_remote_branches=False,
        fetch_remote=False,
        allow_stale_remotes=True,
        sync_index=True,
        refresh_existing=True,
    )
    print(f"  - 新規作成数: {summary.get('new_records', 0)}")
    print(f"  - 更新ファイル数: {len(touched)}")

    # 5. Rebuild knowledge catalog via official query_research API
    print("[5/7] 知識カタログ再構築中 (video_knowledge_catalog.json)...")
    catalog_res, _ = query_research.build_video_knowledge_catalog(root=ROOT)
    print(f"  - カタログ登録総数: {catalog_res.get('total_records')} (動画数: {catalog_res.get('total_video_records')})")

    # 6. Git commit and push (Safety: non-default branch only)
    current_branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    if current_branch != DEFAULT_TARGET_BRANCH:
        raise RuntimeError(f"安全エラー: 現在のブランチ '{current_branch}' は許可された非defaultブランチ '{DEFAULT_TARGET_BRANCH}' ではありません。")

    print(f"[6/7] Gitコミット＆Push実行中 (ブランチ: {current_branch})...")
    files_to_add = ["registry.json", "automation/gemini-notebook/state/video_knowledge_catalog.json"]
    for t in touched:
        rel = str(Path(t).relative_to(ROOT)).replace("\\", "/")
        if rel not in files_to_add:
            files_to_add.append(rel)

    subprocess.check_call(["git", "add"] + files_to_add, cwd=ROOT)
    commit_msg = f"feat(research): auto-ingest video {video_id} via auto research pipeline v2"
    subprocess.check_call(["git", "commit", "-m", commit_msg], cwd=ROOT)
    
    commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    print(f"  - ローカルコミット完了: {commit_sha[:7]} ({commit_msg})")

    remote_head = "UNKNOWN"
    if not no_push:
        subprocess.check_call(["git", "push", "origin", current_branch], cwd=ROOT)
        print(f"  - リモートPush完了: origin/{current_branch}")

        # Real remote readback using git ls-remote
        ls_remote_out = subprocess.check_output(
            ["git", "ls-remote", "origin", f"refs/heads/{current_branch}"],
            cwd=ROOT,
            text=True,
        ).strip()
        if ls_remote_out:
            remote_head = ls_remote_out.split()[0]
        if remote_head != commit_sha:
            raise RuntimeError(f"読み戻し不一致エラー: ローカルHEAD({commit_sha[:7]}) と 実際のリモートHEAD({remote_head[:7]}) が一致しません。")
        print(f"  - 実際のリモート読み戻し確認完了 (Remote HEAD: {remote_head[:7]})")

    # 7. QA System self-verification via official answer_question API
    print("[7/7] 自然言語QA検索エンジンでの動作実証中...")
    qa_res = query_research.answer_question(f"{vd.get('title')[:30]} について教えて", root=ROOT)
    top_hit = qa_res.get("ranked_results", [{}])[0] if qa_res.get("ranked_results") else {}
    top_vid = top_hit.get("record_id", "").replace("youtube:", "")
    print(f"  - QA検索第1位スコア検出: {top_vid} (スコア: {top_hit.get('score')})")

    print("=" * 70)
    print("[PIPELINE SUCCESS] 完全自動化研究パイプライン 完走成功！")
    print(f"動画ID: {video_id}")
    print(f"コミット: {commit_sha[:7]} (Remote: {remote_head[:7]})")
    print(f"台帳総数: {catalog_res.get('total_video_records')} 本")
    research_md_path = f"research/{today_str}-{video_id}-gemini-notebook.md"
    print(f"Notebook用Markdown: {research_md_path}")
    print("=" * 70)

    return {
        "status": "SUCCESS",
        "video_id": video_id,
        "commit_sha": commit_sha,
        "remote_head": remote_head,
        "total_videos": catalog_res.get("total_video_records"),
        "research_path": research_md_path,
        "drive_saved": drive_saved_path,
        "qa_verified": top_vid == video_id,
    }


def main():
    parser = argparse.ArgumentParser(description="AI技術研究室 完全自動化研究パイプライン v2.0")
    parser.add_argument("url", help="YouTube動画URL (例: https://www.youtube.com/watch?v=...)")
    parser.add_argument("--drive-inbox", help="Google Drive受信トレイのカスタムパス", default=None)
    parser.add_argument("--dry-run", action="store_true", help="保存・コミット・Pushをスキップしてプレビュー生成")
    parser.add_argument("--no-push", action="store_true", help="コミットまで行いリモートPushはスキップ")
    parser.add_argument("--gemini-api-key", help="Google Gemini API Key (省略時は環境変数 GEMINI_API_KEY を参照)", default=None)
    args = parser.parse_args()

    inbox_p = Path(args.drive_inbox) if args.drive_inbox else None
    res = run_pipeline(
        args.url,
        drive_inbox=inbox_p,
        dry_run=args.dry_run,
        no_push=args.no_push,
        gemini_api_key=args.gemini_api_key,
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res.get("status") in ("SUCCESS", "ALREADY_REGISTERED", "DRY_RUN_COMPLETE") else 1


if __name__ == "__main__":
    sys.exit(main())
