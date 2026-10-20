#!/usr/bin/env python3
"""Tests for auto_research_pipeline.py v2.2."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Tests must not depend on a real Google Drive mount (G:/マイドライブ exists only on the owner's PC).
import os as _os, tempfile as _tempfile
_DRIVE_TMP = _tempfile.mkdtemp(prefix="ai-research-drive-")
_os.environ.setdefault("AI_RESEARCH_DRIVE_ROOT", _DRIVE_TMP)
AUTO_DIR = ROOT / "automation" / "gemini-notebook"
CONTRACT_PATH = AUTO_DIR / "contract_spec_v1.json"

import sys
sys.path.insert(0, str(AUTO_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import auto_research_pipeline
import branch_pin


class TestAutoResearchPipeline(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        # 実リポジトリの今のブランチ（main でも作業枝でも）には依存しない。許可された作業枝名だけをパイプラインに見せる
        branch_pin.pin_target_branch(self, auto_research_pipeline)

    def test_default_model_is_gemini_3_8_flash(self):
        """1. gemini-3.8-flash が標準モデルであること。"""
        self.assertEqual(auto_research_pipeline.DEFAULT_GEMINI_MODEL, "gemini-3.8-flash")

    def test_evaluate_final_status_full_success(self):
        """All conditions satisfied with 2-Source OKF results in SUCCESS_2_SOURCE_OKF."""
        status, reasons = auto_research_pipeline.evaluate_final_status(
            real_content_acquired=True,
            engine_used="GEMINI_API_LIVE",
            model_used="gemini-3.8-flash",
            research_note_generated=True,
            github_push_success=True,
            remote_head_matched=True,
            remote_research_readback_matched=True,
            remote_registry_readback_matched=True,
            notebook_youtube_readback=True,
            notebook_research_readback=True,
            qa_verified=True,
            no_push=False,
            is_2_source_okf_verified=True,
            notebook_transcript_readback=True,
        )
        self.assertEqual(status, "SUCCESS_2_SOURCE_OKF")
        self.assertEqual(len(reasons), 0)

    def test_evaluate_final_status_partial_when_transcript_missing(self):
        """Only YouTube and Note without Transcript OKF results in PARTIAL_2_SOURCE_OKF_PENDING."""
        status, reasons = auto_research_pipeline.evaluate_final_status(
            real_content_acquired=True,
            engine_used="GEMINI_API_LIVE",
            model_used="gemini-3.8-flash",
            research_note_generated=True,
            github_push_success=True,
            remote_head_matched=True,
            remote_research_readback_matched=True,
            remote_registry_readback_matched=True,
            notebook_youtube_readback=True,
            notebook_research_readback=True,
            qa_verified=True,
            no_push=False,
            is_2_source_okf_verified=False,
            notebook_transcript_readback=False,
        )
        self.assertEqual(status, "PARTIAL_2_SOURCE_OKF_PENDING")
        self.assertTrue(any("字幕原文OKF" in r for r in reasons))

    def test_notebook_unregistered_not_success(self):
        """2. Notebook未登録（研究ノート未確認）ではSUCCESSにならない。"""
        status, reasons = auto_research_pipeline.evaluate_final_status(
            real_content_acquired=True,
            engine_used="GEMINI_API_LIVE",
            model_used="gemini-3.8-flash",
            research_note_generated=True,
            github_push_success=True,
            remote_head_matched=True,
            remote_research_readback_matched=True,
            remote_registry_readback_matched=True,
            notebook_youtube_readback=True,
            notebook_research_readback=False,  # Unregistered Note
            qa_verified=True,
            no_push=False,
            is_2_source_okf_verified=False,
        )
        self.assertNotEqual(status, "SUCCESS_2_SOURCE_OKF")
        self.assertEqual(status, "PARTIAL_NOTEBOOK_PENDING")
        self.assertTrue(any("NotebookLM" in r for r in reasons))

    def test_no_push_not_success(self):
        """3. --no-push ではSUCCESSにならない。"""
        status, reasons = auto_research_pipeline.evaluate_final_status(
            real_content_acquired=True,
            engine_used="GEMINI_API_LIVE",
            model_used="gemini-3.8-flash",
            research_note_generated=True,
            github_push_success=False,
            remote_head_matched=False,
            remote_research_readback_matched=False,
            remote_registry_readback_matched=False,
            notebook_youtube_readback=True,
            notebook_research_readback=True,
            qa_verified=True,
            no_push=True,  # no_push flag
        )
        self.assertNotEqual(status, "SUCCESS_2_SOURCE_OKF")
        self.assertEqual(status, "PARTIAL_NO_PUSH")
        self.assertTrue(any("no_push" in r for r in reasons))

    def test_local_transcript_extraction_not_full_success(self):
        """4. LOCAL_TRANSCRIPT_EXTRACTION では完全SUCCESSにならない。"""
        status, reasons = auto_research_pipeline.evaluate_final_status(
            real_content_acquired=True,
            engine_used="LOCAL_TRANSCRIPT_EXTRACTION",  # Non-AI local extraction
            model_used="NONE",
            research_note_generated=True,
            github_push_success=True,
            remote_head_matched=True,
            remote_research_readback_matched=True,
            remote_registry_readback_matched=True,
            notebook_youtube_readback=True,
            notebook_research_readback=True,
            qa_verified=True,
            no_push=False,
        )
        self.assertNotEqual(status, "SUCCESS_2_SOURCE_OKF")
        self.assertEqual(status, "PARTIAL_LOCAL_EXTRACTION")
        self.assertTrue(any("LIVE" in r for r in reasons))

    def test_registry_remote_readback_failure_not_success(self):
        """5. registry remote readback失敗でSUCCESSにならない。"""
        status, reasons = auto_research_pipeline.evaluate_final_status(
            real_content_acquired=True,
            engine_used="GEMINI_API_LIVE",
            model_used="gemini-3.8-flash",
            research_note_generated=True,
            github_push_success=True,
            remote_head_matched=True,
            remote_research_readback_matched=True,
            remote_registry_readback_matched=False,  # registry readback failed
            notebook_youtube_readback=True,
            notebook_research_readback=True,
            qa_verified=True,
            no_push=False,
            is_2_source_okf_verified=True,
            notebook_transcript_readback=True,
        )
        self.assertNotEqual(status, "SUCCESS_2_SOURCE_OKF")
        self.assertEqual(status, "PARTIAL_READBACK_MISMATCH")
        self.assertTrue(any("registry.json" in r for r in reasons))

    def test_local_transcript_engine_with_cues(self):
        cues = [
            (0.0, 10.0, "こんにちは。AI技術研究室のOKF実践ガイドです。"),
            (10.0, 30.0, "荷札のYAMLフロントマターによりメタデータを標準化します。"),
            (30.0, 60.0, "まとめとして、RAGとOKFの連携運用について解説しました。"),
        ]
        res = auto_research_pipeline.analyze_with_local_transcript_engine(
            title="テストOKF動画",
            author="テスト著者",
            length_sec=60,
            cues=cues,
            desc="概要欄テキスト",
            desc_chapters=[],
        )
        self.assertIn("テスト著者", res["summary_ja"])
        self.assertGreaterEqual(len(res["chapters"]), 1)
        self.assertEqual(res["chapters"][0]["timestamp_source"], "TIMESTAMPED_CAPTIONS")
        self.assertIn("荷札", res["detailed_findings_ja"])
        self.assertEqual(res["analysis_engine"], "LOCAL_TRANSCRIPT_EXTRACTION")

    def test_local_transcript_engine_without_cues(self):
        res = auto_research_pipeline.analyze_with_local_transcript_engine(
            title="字幕なし動画",
            author="テスト著者",
            length_sec=120,
            cues=[],
            desc="概要欄",
            desc_chapters=[],
        )
        self.assertIn("NOT_ACQUIRED", res["summary_ja"])
        self.assertEqual(len(res["chapters"]), 0)
        self.assertEqual(len(res["claims"]), 0)
        self.assertEqual(res["analysis_engine"], "METADATA_ONLY")

    def test_build_research_receipt_schema_compliance(self):
        mock_player = {
            "videoDetails": {
                "title": "テストAI動画: OKF実践ガイド",
                "author": "AI研究者",
                "lengthSeconds": "600",
                "shortDescription": "OKFの荷札設計とRAGの連携について解説します。",
            },
            "captions": {}
        }
        receipt, engine, model = auto_research_pipeline.build_research_receipt(
            video_id="test1234567",
            player_data=mock_player,
            publish_date=None,
        )
        self.assertEqual(receipt["schema_version"], "research_receipt_v1")
        self.assertEqual(len(receipt["videos"]), 1)
        v = receipt["videos"][0]
        self.assertEqual(v["video_id"], "test1234567")
        self.assertEqual(v["published_at"], "UNKNOWN")
        self.assertEqual(v["transcript_status"], "NOT_ACQUIRED")
        self.assertLessEqual(len(v["title"]), 250)
        self.assertLessEqual(len(v["summary_ja"]), 300)
        self.assertLessEqual(len(v["detailed_findings_ja"]), 2500)
        self.assertLessEqual(v["detailed_findings_ja"].count("\n"), 25)
        
        forbidden = set(self.contract.get("forbidden_payload_keys", []))
        for key in v.keys():
            self.assertNotIn(key.lower(), forbidden)

    def test_live_gemini_requires_explicit_flag(self):
        mock_player = {
            "videoDetails": {
                "title": "テストAI動画",
                "author": "AI研究者",
                "lengthSeconds": "60",
                "shortDescription": "概要",
            },
            "captions": {}
        }
        receipt, engine, model = auto_research_pipeline.build_research_receipt(
            video_id="test1234567",
            player_data=mock_player,
            publish_date="2026-10-19",
            gemini_api_key="fake-key-for-test",
            enable_live_gemini=False,
        )
        self.assertEqual(receipt["videos"][0]["video_id"], "test1234567")
        self.assertNotEqual(engine, "GEMINI_API_LIVE")

    def test_dry_run_no_side_effects(self):
        test_scratch = ROOT / "scratch" / "receipt_dQw4w9WgXcQ.json"
        if test_scratch.exists():
            test_scratch.unlink()
        res = auto_research_pipeline.run_pipeline(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            dry_run=True,
            enable_live_gemini=True,
            gemini_api_key="fake_key_must_not_be_called",
        )
        self.assertEqual(res.get("status"), "DRY_RUN_COMPLETE")
        self.assertFalse(test_scratch.exists())

    def test_dry_run_makes_no_network_calls(self):
        """dry-run中は外部通信（urlopen・ソケット接続）が1回も起きないこと。"""
        import socket
        import urllib.request
        from unittest import mock

        calls = []

        def _blocked(*args, **kwargs):
            calls.append(args[:1])
            raise AssertionError(f"dry-run中に外部通信が呼ばれました: {args[:1]}")

        with mock.patch.object(urllib.request, "urlopen", _blocked), \
                mock.patch.object(socket, "create_connection", _blocked):
            res = auto_research_pipeline.run_pipeline(
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                dry_run=True,
                enable_live_gemini=True,
                gemini_api_key="fake_key_must_not_be_called",
            )
        self.assertEqual(res.get("status"), "DRY_RUN_COMPLETE")
        self.assertEqual(calls, [])

    def test_resume_notebook_ingest_from_already_registered(self):
        """8. GitHub登録済み / Notebook未登録からNotebook工程だけ再開できること。"""
        # u3ka_AAb8qE is already registered on GitHub
        res = auto_research_pipeline.run_pipeline(
            "https://www.youtube.com/watch?v=u3ka_AAb8qE",
            mock_cdp=True,
        )
        self.assertIn(res.get("status"), ("RESUMED_NOTEBOOK_INGEST", "ALREADY_REGISTERED", "SUCCESS_2_SOURCE_OKF", "RESUMED_NOTEBOOK_INGEST_PARTIAL"))
        if res.get("status") in ("RESUMED_NOTEBOOK_INGEST", "SUCCESS_2_SOURCE_OKF", "RESUMED_NOTEBOOK_INGEST_PARTIAL"):
            self.assertIn("notebook_ingest", res)

    def test_short_description_only_does_not_satisfy_real_content_acquired(self):
        """shortDescriptionだけでは完全SUCCESSにならず、PARTIAL_NO_SUBTITLESになること。"""
        status, reasons = auto_research_pipeline.evaluate_final_status(
            real_content_acquired=False,  # cues count = 0 or status = NOT_ACQUIRED
            engine_used="GEMINI_API_LIVE",
            model_used="gemini-3.8-flash",
            research_note_generated=True,
            github_push_success=True,
            remote_head_matched=True,
            remote_research_readback_matched=True,
            remote_registry_readback_matched=True,
            notebook_youtube_readback=True,
            notebook_research_readback=True,
            qa_verified=True,
            no_push=False,
            is_2_source_okf_verified=True,
            notebook_transcript_readback=True,
        )
        self.assertNotEqual(status, "SUCCESS_2_SOURCE_OKF")
        self.assertEqual(status, "PARTIAL_NO_SUBTITLES")
        self.assertTrue(any("字幕" in r for r in reasons))

    def test_registry_records_key_used_in_resume(self):
        """registry.jsonのrecordsキーが正しく参照されること。"""
        reg_path = ROOT / "registry.json"
        self.assertTrue(reg_path.exists())
        reg_data = json.loads(reg_path.read_text(encoding="utf-8"))
        self.assertIn("records", reg_data, "registry.json must contain 'records' key")
        self.assertNotIn("videos", reg_data, "registry.json does not use 'videos' at root")

    def test_resume_with_two_sources_does_not_readd(self):
        """ALREADY_REGISTERED時にNotebook2ソース（字幕原文OKF＋研究ノートOKF）存在なら再追加せず完了すること。"""
        res_md = ROOT / "research" / "2026-10-10-lC5jxpYmatE-ai-techniques.md"
        nb_res = auto_research_pipeline.run_notebook_registration_only(
            video_id="lC5jxpYmatE",
            research_md_path=res_md,
            video_title="Test Video",
            mock_cdp=True,
            mock_sources=[
                "https://www.youtube.com/watch?v=lC5jxpYmatE",
                "AI_VIDEO_RESEARCH_NOTE:lC5jxpYmatE",
                "AI_VIDEO_TRANSCRIPT_RAW:lC5jxpYmatE",
            ],
        )
        self.assertTrue(nb_res.get("is_full_success"))
        self.assertEqual(len(nb_res.get("actions_taken", [])), 0, "No actions should be taken when both exist")

    def test_resume_adds_only_missing_source(self):
        """ALREADY_REGISTERED時に字幕原文OKFが不足なら不足側だけ追加されること。"""
        res_md = ROOT / "research" / "2026-10-10-lC5jxpYmatE-ai-techniques.md"
        nb_res = auto_research_pipeline.run_notebook_registration_only(
            video_id="lC5jxpYmatE",
            research_md_path=res_md,
            video_title="Test Video",
            mock_cdp=True,
            mock_sources=[
                "https://www.youtube.com/watch?v=lC5jxpYmatE",
                "AI_VIDEO_RESEARCH_NOTE:lC5jxpYmatE",
            ],  # Transcript OKF is missing
            cues=[{"start": 0.0, "end": 10.0, "text": "AI技術の検証"}],
        )
        self.assertTrue(nb_res.get("is_full_success"))
        self.assertIn("TRANSCRIPT_OKF_INSERTED", nb_res.get("actions_taken", []))
        self.assertNotIn("COPIED_TEXT_NOTE_INSERTED", nb_res.get("actions_taken", []))
        self.assertNotIn("YOUTUBE_URL_INSERTED", nb_res.get("actions_taken", []))

    def test_cli_exit_code_resumed_notebook_ingest_is_zero(self):
        """RESUMED_NOTEBOOK_INGESTはCLI終了コード0を返すこと。"""
        orig_run = auto_research_pipeline.run_pipeline
        try:
            auto_research_pipeline.run_pipeline = lambda *a, **kw: {"status": "RESUMED_NOTEBOOK_INGEST", "is_full_success": True}
            exit_code = auto_research_pipeline.main(["https://www.youtube.com/watch?v=u3ka_AAb8qE"])
            self.assertEqual(exit_code, 0)
        finally:
            auto_research_pipeline.run_pipeline = orig_run

    def test_cli_exit_code_resumed_notebook_ingest_partial_is_nonzero(self):
        """RESUMED_NOTEBOOK_INGEST_PARTIALはCLI終了コード非0(1)を返すこと。"""
        orig_run = auto_research_pipeline.run_pipeline
        try:
            auto_research_pipeline.run_pipeline = lambda *a, **kw: {"status": "RESUMED_NOTEBOOK_INGEST_PARTIAL", "is_full_success": False}
            exit_code = auto_research_pipeline.main(["https://www.youtube.com/watch?v=u3ka_AAb8qE"])
            self.assertEqual(exit_code, 1)
        finally:
            auto_research_pipeline.run_pipeline = orig_run

    def test_okf_research_u3ka_2_source_ingestion_and_readback(self):
        """OKF研究(u3ka_AAb8qE)のソースを既存実装を再利用して字幕原文OKFと研究ノートOKFの必須2ソースにすること。"""
        import notebook_auto_ingest
        res_md = ROOT / "research" / "2026-10-19-u3ka_AAb8qE-gemini-notebook.md"
        self.assertTrue(res_md.exists(), "u3ka_AAb8qE research note must exist")

        # 1. Reuse existing build_transcript_okf_content for Transcript OKF
        cues = [
            {"start": 496.0, "duration": 52.0, "text": "資料冒頭のYAMLフロントマターによる荷札・メタデータ識別原則"},
            {"start": 575.0, "duration": 36.0, "text": "資料間を意味付きリンク（COMPLEMENTS等）で結ぶ双方向参照設計"},
        ]
        tr_text = notebook_auto_ingest.build_transcript_okf_content(
            video_id="u3ka_AAb8qE",
            video_url="https://www.youtube.com/watch?v=u3ka_AAb8qE",
            video_title="【OKF実践】AI時代の知識管理とオープンナレッジフォーマット v0.2",
            cues=cues,
        )
        self.assertIn('logical_id: "youtube:u3ka_AAb8qE:transcript"', tr_text)
        self.assertIn('related_research_id: "youtube:u3ka_AAb8qE:research"', tr_text)
        self.assertIn('<!-- ID: AI_VIDEO_TRANSCRIPT_RAW:u3ka_AAb8qE -->', tr_text)

        # 2. Ingest 2-source OKF using existing pipeline module
        nb_res = auto_research_pipeline.run_notebook_registration_only(
            video_id="u3ka_AAb8qE",
            research_md_path=res_md,
            video_title="【OKF実践】AI時代の知識管理とオープンナレッジフォーマット v0.2",
            mock_cdp=True,
            cues=cues,
        )
        self.assertEqual(nb_res["status"], "SUCCESS_2_SOURCE_OKF")
        self.assertTrue(nb_res["is_full_success"])
        self.assertTrue(nb_res["is_2_source_okf_verified"])
        self.assertTrue(nb_res["readback"]["research_note_found"])
        self.assertTrue(nb_res["readback"]["transcript_source_found"])
        # YouTube URL is NOT registered by default, confirming pure 2-source OKF
        self.assertNotIn("YOUTUBE_URL_INSERTED", nb_res.get("actions_taken", []))

    def test_main_url_argument_positional_and_flag(self):
        """CLI 引数として位置引数と --url オプションの両方が受け入れられること。"""
        from unittest.mock import patch
        # 1. Test dry-run with positional URL
        with patch("auto_research_pipeline.run_pipeline") as mock_run:
            mock_run.return_value = {"status": "DRY_RUN_COMPLETE"}
            code1 = auto_research_pipeline.main(["https://www.youtube.com/watch?v=dQw4w9WgXcQ", "--dry-run"])
            self.assertEqual(code1, 0)
            self.assertEqual(mock_run.call_args[0][0], "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        # 2. Test dry-run with --url flag
        with patch("auto_research_pipeline.run_pipeline") as mock_run:
            mock_run.return_value = {"status": "DRY_RUN_COMPLETE"}
            code2 = auto_research_pipeline.main(["--url", "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "--dry-run"])
            self.assertEqual(code2, 0)
            self.assertEqual(mock_run.call_args[0][0], "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_evaluate_final_status_fails_on_missing_or_mismatched_mutual_links(self):
        """相互論理リンク（:transcript ↔ :research）の欠落・不一致では完全SUCCESSにならないこと。"""
        status, reasons = auto_research_pipeline.evaluate_final_status(
            real_content_acquired=True,
            engine_used="GEMINI_API_LIVE",
            model_used="gemini-3.8-flash",
            research_note_generated=True,
            github_push_success=True,
            remote_head_matched=True,
            remote_research_readback_matched=True,
            remote_registry_readback_matched=True,
            notebook_youtube_readback=True,
            notebook_research_readback=True,
            qa_verified=True,
            no_push=False,
            is_2_source_okf_verified=True,
            notebook_transcript_readback=True,
            has_mutual_logical_links=False,  # 相互リンク欠落
        )
        self.assertNotEqual(status, "SUCCESS_2_SOURCE_OKF")
        self.assertEqual(status, "PARTIAL_METADATA_INCOMPLETE")
        self.assertTrue(any("相互論理リンク" in r for r in reasons))

    def test_evaluate_final_status_fails_on_missing_canonical_url(self):
        """元YouTube URL（canonical_url）の欠落では完全SUCCESSにならないこと。"""
        status, reasons = auto_research_pipeline.evaluate_final_status(
            real_content_acquired=True,
            engine_used="GEMINI_API_LIVE",
            model_used="gemini-3.8-flash",
            research_note_generated=True,
            github_push_success=True,
            remote_head_matched=True,
            remote_research_readback_matched=True,
            remote_registry_readback_matched=True,
            notebook_youtube_readback=True,
            notebook_research_readback=True,
            qa_verified=True,
            no_push=False,
            is_2_source_okf_verified=True,
            notebook_transcript_readback=True,
            has_canonical_url=False,  # 元URL欠落
        )
        self.assertNotEqual(status, "SUCCESS_2_SOURCE_OKF")
        self.assertEqual(status, "PARTIAL_METADATA_INCOMPLETE")
        self.assertTrue(any("元YouTube URL" in r for r in reasons))

    def test_evaluate_final_status_fails_on_sources_not_distinct(self):
        """2ソースが同一要素二重カウント（independent_sources_distinct=False）では完全SUCCESSにならないこと。"""
        status, reasons = auto_research_pipeline.evaluate_final_status(
            real_content_acquired=True,
            engine_used="GEMINI_API_LIVE",
            model_used="gemini-3.8-flash",
            research_note_generated=True,
            github_push_success=True,
            remote_head_matched=True,
            remote_research_readback_matched=True,
            remote_registry_readback_matched=True,
            notebook_youtube_readback=True,
            notebook_research_readback=True,
            qa_verified=True,
            no_push=False,
            is_2_source_okf_verified=True,
            notebook_transcript_readback=True,
            independent_sources_distinct=False,  # 二重カウント・非独立
        )
        self.assertNotEqual(status, "SUCCESS_2_SOURCE_OKF")
        self.assertTrue(any("二重カウント排除" in r for r in reasons))

    def test_rag_and_okf_videos_complements_cross_linking_and_parity(self):
        """RAG動画(pRfC1DILDEM)とOKF動画(u3ka_AAb8qE)の2資料構造、双方向リンク、COMPLEMENTS関係を実証。"""
        import notebook_auto_ingest as nai

        rag_md = ROOT / "research" / "2026-10-18-pRfC1DILDEM-gemini-notebook.md"
        okf_md = ROOT / "research" / "2026-10-19-u3ka_AAb8qE-gemini-notebook.md"
        self.assertTrue(rag_md.exists(), "RAG research note exists")
        self.assertTrue(okf_md.exists(), "OKF research note exists")

        rag_text = rag_md.read_text(encoding="utf-8")
        okf_text = okf_md.read_text(encoding="utf-8")

        # 1. RAG Research Note checks
        self.assertIn('logical_id: "youtube:pRfC1DILDEM:research"', rag_text)
        self.assertIn('transcript_logical_id: "youtube:pRfC1DILDEM:transcript"', rag_text)
        self.assertIn('resource: "https://www.youtube.com/watch?v=pRfC1DILDEM"', rag_text)
        self.assertIn('target_id: "youtube:u3ka_AAb8qE:research"', rag_text)
        self.assertIn('relation: "COMPLEMENTS"', rag_text)
        self.assertIn('status: "CONFIRMED"', rag_text)

        # 2. OKF Research Note checks
        self.assertIn('logical_id: "youtube:u3ka_AAb8qE:research"', okf_text)
        self.assertIn('transcript_logical_id: "youtube:u3ka_AAb8qE:transcript"', okf_text)
        self.assertIn('resource: "https://www.youtube.com/watch?v=u3ka_AAb8qE"', okf_text)
        self.assertIn('target_id: "youtube:pRfC1DILDEM:research"', okf_text)
        self.assertIn('relation: "COMPLEMENTS"', okf_text)
        self.assertIn('status: "CONFIRMED"', okf_text)

        # 3. Generate Transcript OKF for RAG
        rag_tr = nai.build_transcript_okf_content(
            video_id="pRfC1DILDEM",
            video_url="https://www.youtube.com/watch?v=pRfC1DILDEM",
            video_title="【AI中級】RAGのその先。巨大な資料をAIで精度高く取り扱いたい。",
            cues=[{"start": 0.0, "end": 10.0, "text": "RAGの限界と構造"}],
            status="UNVERIFIED",
            related_records=[{
                "target_id": "youtube:u3ka_AAb8qE:research",
                "relation": "COMPLEMENTS",
                "note": "OKFとRAGの相互補完",
                "status": "CONFIRMED",
                "evidence": "13:16過去回言及"
            }]
        )
        self.assertIn('type: "TRANSCRIPT"', rag_tr)
        self.assertIn('logical_id: "youtube:pRfC1DILDEM:transcript"', rag_tr)
        self.assertIn('research_logical_id: "youtube:pRfC1DILDEM:research"', rag_tr)
        self.assertIn('related_research_id: "youtube:pRfC1DILDEM:research"', rag_tr)
        self.assertIn('canonical_url: "https://www.youtube.com/watch?v=pRfC1DILDEM"', rag_tr)
        self.assertIn('target_id: "youtube:u3ka_AAb8qE:research"', rag_tr)

        # 4. Generate Transcript OKF for OKF
        okf_tr = nai.build_transcript_okf_content(
            video_id="u3ka_AAb8qE",
            video_url="https://www.youtube.com/watch?v=u3ka_AAb8qE",
            video_title="【OKF実践】AI時代の知識管理とオープンナレッジフォーマット v0.2",
            cues=[{"start": 496.0, "end": 548.0, "text": "YAMLフロントマターによる荷札"}],
            status="UNVERIFIED",
            related_records=[{
                "target_id": "youtube:pRfC1DILDEM:research",
                "relation": "COMPLEMENTS",
                "note": "RAGとOKFの相互補完",
                "status": "CONFIRMED",
                "evidence": "08:16荷札とpRfC1DILDEM言及"
            }]
        )
        self.assertIn('type: "TRANSCRIPT"', okf_tr)
        self.assertIn('logical_id: "youtube:u3ka_AAb8qE:transcript"', okf_tr)
        self.assertIn('research_logical_id: "youtube:u3ka_AAb8qE:research"', okf_tr)
        self.assertIn('related_research_id: "youtube:u3ka_AAb8qE:research"', okf_tr)
        self.assertIn('canonical_url: "https://www.youtube.com/watch?v=u3ka_AAb8qE"', okf_tr)
        self.assertIn('target_id: "youtube:pRfC1DILDEM:research"', okf_tr)

        # 5. Distinctness: Transcript OKF != Research Note
        self.assertNotEqual(rag_tr, rag_text)
        self.assertNotEqual(okf_tr, okf_text)

    def test_evaluate_2_source_okf_independence_edge_cases(self):
        """2ソースの取り違え、重複カウント、異動画ID混入が正しく弾かれること。"""
        import notebook_auto_ingest as nai

        vid = "pRfC1DILDEM"
        v_title = "RAG Video"

        # (a) 同一要素二重カウント -> False
        items_dup = [{"index": 0, "text": f"AI_VIDEO_RESEARCH_NOTE:{vid} AI_VIDEO_TRANSCRIPT_RAW:{vid}"}]
        res_dup = nai.evaluate_2_source_okf_independence(items_dup, vid, v_title)
        self.assertFalse(res_dup["is_2_source_okf_verified"])

        # (b) 2つとも研究ノート（取り違え/字幕欠落） -> False
        items_two_notes = [
            {"index": 0, "text": f"AI_VIDEO_RESEARCH_NOTE:{vid} part 1"},
            {"index": 1, "text": f"AI_VIDEO_RESEARCH_NOTE:{vid} part 2"},
        ]
        res_two_notes = nai.evaluate_2_source_okf_independence(items_two_notes, vid, v_title)
        self.assertFalse(res_two_notes["is_2_source_okf_verified"])
        self.assertFalse(res_two_notes["transcript_source_found"])

        # (c) 2つとも字幕原文（取り違え/ノート欠落） -> False
        items_two_tr = [
            {"index": 0, "text": f"AI_VIDEO_TRANSCRIPT_RAW:{vid} part 1"},
            {"index": 1, "text": f"AI_VIDEO_TRANSCRIPT_RAW:{vid} part 2"},
        ]
        res_two_tr = nai.evaluate_2_source_okf_independence(items_two_tr, vid, v_title)
        self.assertFalse(res_two_tr["is_2_source_okf_verified"])
        self.assertFalse(res_two_tr["research_note_found"])

        # (d) 異なる動画IDのソース混入（リンク先・対象不一致） -> False
        items_mismatch = [
            {"index": 0, "text": "AI_VIDEO_RESEARCH_NOTE:OTHER_VID_999"},
            {"index": 1, "text": f"AI_VIDEO_TRANSCRIPT_RAW:{vid}"},
        ]
        res_mismatch = nai.evaluate_2_source_okf_independence(items_mismatch, vid, v_title)
        self.assertFalse(res_mismatch["is_2_source_okf_verified"])
        self.assertFalse(res_mismatch["research_note_found"])

    def test_evaluate_final_status_blocks_mock_mode(self):
        """1. Mock成功の遮断: is_mock=True は全条件が揃っていても SUCCESS_2_SOURCE_OKF を遮断すること。"""
        status, reasons = auto_research_pipeline.evaluate_final_status(
            real_content_acquired=True,
            engine_used="GEMINI_API_LIVE",
            model_used="gemini-3.8-flash",
            research_note_generated=True,
            github_push_success=True,
            remote_head_matched=True,
            remote_research_readback_matched=True,
            remote_registry_readback_matched=True,
            notebook_youtube_readback=True,
            notebook_research_readback=True,
            qa_verified=True,
            no_push=False,
            is_2_source_okf_verified=True,
            notebook_transcript_readback=True,
            is_mock=True,  # Mock実行
        )
        self.assertNotEqual(status, "SUCCESS_2_SOURCE_OKF")
        self.assertEqual(status, "PARTIAL_MOCK_VERIFIED")
        self.assertTrue(any("Mockシミュレーション" in r for r in reasons))

    def test_resume_fails_when_captions_missing(self):
        """2. 字幕なしの仮資料を正式成功にしない: Resume経路で字幕Cueが存在しない場合、完全SUCCESSを遮断すること。"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            fake_md = tmp_path / "note.md"
            fake_md.write_text("dummy note", encoding="utf-8")

            nb_res = auto_research_pipeline.run_notebook_registration_only(
                video_id="dummyNoCuesVid",
                research_md_path=fake_md,
                video_title="字幕なしテスト動画",
                mock_cdp=True,
                cues=None,  # 字幕未取得
                mock_sources=["https://www.youtube.com/watch?v=dummyNoCuesVid"],
            )
            self.assertNotEqual(nb_res.get("status"), "SUCCESS_2_SOURCE_OKF")
            self.assertIn(nb_res.get("status"), ("PARTIAL_NO_SUBTITLES", "PARTIAL_2_SOURCE_OKF_PENDING"))
            self.assertFalse(nb_res.get("is_full_success"))
            self.assertFalse(nb_res.get("has_actual_cues"))

    def test_verify_transcript_content_integrity_preserves_unknown_body_status(self):
        """3. 保存本文の検証: ソース一覧DOMの検出のみでは本文完全立証と扱わず、UNKNOWNとして保持すること。"""
        import notebook_auto_ingest as nai

        sample_cues = [
            {"start": 0.0, "end": 5.0, "text": "第1文の実発話"},
            {"start": 5.0, "end": 10.0, "text": "第2文の実発話"},
        ]
        tr_text = nai.build_transcript_okf_content(
            video_id="testVidIntegrity",
            video_url="https://www.youtube.com/watch?v=testVidIntegrity",
            video_title="本文検証テスト",
            cues=sample_cues,
        )
        integrity = nai.verify_transcript_content_integrity(sample_cues, tr_text)
        self.assertTrue(integrity["has_actual_cues"])
        self.assertEqual(integrity["cues_count"], 2)
        self.assertTrue(integrity["cues_fully_contained"])
        self.assertEqual(integrity["body_readback_status"], "UNKNOWN")
        self.assertIn("UNKNOWNとして保持", integrity["body_readback_note"])

        # 字幕なし時
        integrity_empty = nai.verify_transcript_content_integrity([], "")
        self.assertFalse(integrity_empty["has_actual_cues"])
        self.assertEqual(integrity_empty["body_readback_status"], "NOT_ACQUIRED")

    def test_verify_mutual_okf_links_and_clickable_distinction(self):
        """4. 双方のURL・相互リンク検証: 厳格照合および実クリック可能リンク(UNKNOWN)の区別を検証。"""
        import notebook_auto_ingest as nai

        vid = "u3ka_AAb8qE"
        v_url = f"https://www.youtube.com/watch?v={vid}"
        okf_md = ROOT / "research" / "2026-10-19-u3ka_AAb8qE-gemini-notebook.md"
        rn_text = okf_md.read_text(encoding="utf-8")

        tr_text = nai.build_transcript_okf_content(
            video_id=vid,
            video_url=v_url,
            video_title="【OKF実践】",
            cues=[{"start": 496.0, "end": 548.0, "text": "YAMLフロントマターによる荷札"}],
            related_records=[{"target_id": "youtube:pRfC1DILDEM:research", "relation": "COMPLEMENTS", "status": "CONFIRMED"}],
        )

        res = nai.verify_mutual_okf_links(rn_text, tr_text, vid, v_url)
        self.assertTrue(res["is_valid"])
        self.assertTrue(res["mutual_matches"])
        self.assertTrue(res["urls_match"])
        self.assertTrue(res["vids_match"])
        self.assertEqual(res["clickable_link_status"], "UNKNOWN")
        self.assertIn("直接クリック可能リンクは未取得", res["clickable_link_note"])

    def test_rag_and_okf_research_notes_verifications(self):
        """5. RAG・OKF既存2動画の検品: 字幕UNVERIFIEDの保持、出典付きCOMPLEMENTS、UI制限案内の存在を立証。"""
        rag_md = ROOT / "research" / "2026-10-18-pRfC1DILDEM-gemini-notebook.md"
        okf_md = ROOT / "research" / "2026-10-19-u3ka_AAb8qE-gemini-notebook.md"

        rag_text = rag_md.read_text(encoding="utf-8")
        okf_text = okf_md.read_text(encoding="utf-8")

        # 字幕完全性未証明の誠実な保持
        self.assertIn('transcript_status: "UNVERIFIED"', rag_text)
        self.assertIn('transcript_status: "UNVERIFIED"', okf_text)

        # 出典付きCOMPLEMENTS関係
        self.assertIn('target_id: "youtube:u3ka_AAb8qE:research"', rag_text)
        self.assertIn('relation: "COMPLEMENTS"', rag_text)
        self.assertIn('status: "CONFIRMED"', rag_text)
        self.assertIn("13:16", rag_text)

        self.assertIn('target_id: "youtube:pRfC1DILDEM:research"', okf_text)
        self.assertIn('relation: "COMPLEMENTS"', okf_text)
        self.assertIn('status: "CONFIRMED"', okf_text)
        self.assertIn("08:16", okf_text)

        # Notebook UI制限事項の明記
        self.assertIn("NotebookLM UI上ではソース間直接リンクのクリックジャンプができない仕様", rag_text)
        self.assertIn("NotebookLM UI上ではソース間直接リンクのクリックジャンプができない仕様", okf_text)


class TestTargetBranchGuard(unittest.TestCase):
    """安全チェック：許可された非default作業枝以外（main・他の枝・detached HEAD）では、書き込み系は何も始まる前に拒否する。

    実リポジトリの今の枝には依存しない（一時 git リポジトリで枝名を与える）。どの枝でテストを流しても結果が同じになる。
    """

    URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    REFUSED = ("main", "master", "develop", "claude/project-thread-u5xj4e", "feature/other-branch")

    def test_allowed_work_branch_passes(self):
        root = branch_pin.temp_repo_on_branch(self, auto_research_pipeline.DEFAULT_TARGET_BRANCH)
        auto_research_pipeline.verify_target_branch_early(root=root)

    def test_explicit_target_branch_is_honoured(self):
        root = branch_pin.temp_repo_on_branch(self, "feature/some-work")
        auto_research_pipeline.verify_target_branch_early(root=root, target_branch="feature/some-work")
        with self.assertRaises(RuntimeError):
            auto_research_pipeline.verify_target_branch_early(root=root)    # 既定の許可枝ではない

    def test_main_and_every_other_branch_is_refused(self):
        for name in self.REFUSED:
            root = branch_pin.temp_repo_on_branch(self, name)
            with self.assertRaises(RuntimeError, msg=name) as cm:
                auto_research_pipeline.verify_target_branch_early(root=root)
            self.assertIn("default branch", str(cm.exception))
            self.assertIn(name, str(cm.exception))

    def test_detached_head_is_refused(self):
        root = branch_pin.temp_repo_detached(self)
        with self.assertRaises(RuntimeError):
            auto_research_pipeline.verify_target_branch_early(root=root)

    def test_not_a_git_repository_is_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d, self.assertRaises(RuntimeError):
            auto_research_pipeline.verify_target_branch_early(root=Path(d))

    def test_pipeline_on_main_stops_before_any_file_is_touched(self):
        from unittest import mock
        for dry_run in (True, False):
            root = branch_pin.temp_repo_on_branch(self, "main")
            scratch = root / "scratch"
            before = sorted(p.name for p in root.iterdir())
            with mock.patch.object(auto_research_pipeline, "ROOT", root), \
                    mock.patch.object(auto_research_pipeline, "SCRATCH_DIR", scratch), \
                    mock.patch("urllib.request.urlopen", side_effect=AssertionError("network")), \
                    self.assertRaises(RuntimeError) as cm:
                auto_research_pipeline.run_pipeline(self.URL, dry_run=dry_run)
            self.assertIn("default branch", str(cm.exception))
            self.assertEqual(sorted(p.name for p in root.iterdir()), before)
            self.assertFalse(scratch.exists())


if __name__ == "__main__":
    unittest.main()
