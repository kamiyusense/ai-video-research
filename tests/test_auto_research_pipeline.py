#!/usr/bin/env python3
"""Tests for auto_research_pipeline.py v2.1."""
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

    def test_sanitize_text(self):
        raw = "Line 1\n\nLine 2\nLine 3\nLine 4\nLine 5"
        res = auto_research_pipeline.sanitize_text(raw, max_len=50, max_newlines=2)
        self.assertLessEqual(len(res), 50)
        self.assertLessEqual(res.count("\n"), 2)

    def test_verify_target_branch_early_success(self):
        # On current branch, it should not raise
        auto_research_pipeline.verify_target_branch_early(root=ROOT)

    def test_verify_target_branch_early_forbidden(self):
        # When target is different, it must raise RuntimeError
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
        receipt = auto_research_pipeline.build_research_receipt(
            video_id="test1234567",
            player_data=mock_player,
            publish_date=None,  # Unknown
        )
        self.assertEqual(receipt["schema_version"], "research_receipt_v1")
        self.assertEqual(len(receipt["videos"]), 1)
        v = receipt["videos"][0]
        self.assertEqual(v["video_id"], "test1234567")
        self.assertEqual(v["published_at"], "UNKNOWN")  # Honesty: never faked
        self.assertEqual(v["transcript_status"], "NOT_ACQUIRED")
        self.assertLessEqual(len(v["title"]), 250)
        self.assertLessEqual(len(v["summary_ja"]), 300)
        self.assertLessEqual(len(v["detailed_findings_ja"]), 2500)
        self.assertLessEqual(v["detailed_findings_ja"].count("\n"), 25)
        
        # Check forbidden keys
        forbidden = set(self.contract.get("forbidden_payload_keys", []))
        for key in v.keys():
            self.assertNotIn(key.lower(), forbidden)

    def test_live_gemini_requires_explicit_flag(self):
        # Even with API key, without enable_live_gemini=True, it should fallback to local engine
        mock_player = {
            "videoDetails": {
                "title": "テストAI動画",
                "author": "AI研究者",
                "lengthSeconds": "60",
                "shortDescription": "概要",
            },
            "captions": {}
        }
        receipt = auto_research_pipeline.build_research_receipt(
            video_id="test1234567",
            player_data=mock_player,
            publish_date="2026-10-19",
            gemini_api_key="fake-key-for-test",
            enable_live_gemini=False,  # Not explicitly enabled
        )
        # Should succeed using local fallback without network call
        self.assertEqual(receipt["videos"][0]["video_id"], "test1234567")

    def test_duplicate_prevention_on_pipeline(self):
        res = auto_research_pipeline.run_pipeline("https://www.youtube.com/watch?v=u3ka_AAb8qE")
        self.assertEqual(res.get("status"), "ALREADY_REGISTERED")
        self.assertEqual(res.get("video_id"), "u3ka_AAb8qE")

    def test_dry_run_no_side_effects(self):
        test_scratch = ROOT / "scratch" / "receipt_dQw4w9WgXcQ.json"
        if test_scratch.exists():
            test_scratch.unlink()
        res = auto_research_pipeline.run_pipeline(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            dry_run=True,
            enable_live_gemini=True,  # Even if requested, dry_run must prevent API call & file write
            gemini_api_key="fake_key_must_not_be_called",
        )
        self.assertEqual(res.get("status"), "DRY_RUN_COMPLETE")
        self.assertFalse(test_scratch.exists(), "Dry-run must not create scratch receipt file")


if __name__ == "__main__":
    unittest.main()
