#!/usr/bin/env python3
"""Tests for auto_research_pipeline.py v2.2."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTO_DIR = ROOT / "automation" / "gemini-notebook"
CONTRACT_PATH = AUTO_DIR / "contract_spec_v1.json"

import sys
sys.path.insert(0, str(AUTO_DIR))
import auto_research_pipeline


class TestAutoResearchPipeline(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

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
        self.assertNotEqual(status, "SUCCESS")
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
        self.assertNotEqual(status, "SUCCESS")
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

    def test_verify_target_branch_early_success(self):
        auto_research_pipeline.verify_target_branch_early(root=ROOT)

    def test_verify_target_branch_early_forbidden(self):
        with self.assertRaises(RuntimeError):
            auto_research_pipeline.verify_target_branch_early(root=ROOT, target_branch="non-existent-branch-xyz")

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

    def test_resume_notebook_ingest_from_already_registered(self):
        """8. GitHub登録済み / Notebook未登録からNotebook工程だけ再開できること。"""
        # u3ka_AAb8qE is already registered on GitHub
        res = auto_research_pipeline.run_pipeline(
            "https://www.youtube.com/watch?v=u3ka_AAb8qE",
            mock_cdp=True,
        )
        self.assertIn(res.get("status"), ("RESUMED_NOTEBOOK_INGEST", "ALREADY_REGISTERED", "SUCCESS_2_SOURCE_OKF"))
        if res.get("status") in ("RESUMED_NOTEBOOK_INGEST", "SUCCESS_2_SOURCE_OKF"):
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


if __name__ == "__main__":
    unittest.main()
