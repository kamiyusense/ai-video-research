#!/usr/bin/env python3
"""Tests for auto_research_pipeline.py."""
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

    def test_extract_key_topics(self):
        text = "OKFとRAGを用いたGemini Notebook自動化エージェント設計"
        topics = auto_research_pipeline.extract_key_topics_from_text(text)
        self.assertIn("OKF", topics)
        self.assertIn("RAG", topics)
        self.assertIn("Gemini", topics)

    def test_build_research_receipt_schema_compliance(self):
        mock_player = {
            "videoDetails": {
                "title": "テストAI動画: OKF実践ガイド",
                "author": "AI研究者",
                "lengthSeconds": "600",
                "shortDescription": "OKFの荷札設計とRAGの連携について解説します。\n公式仕様を参照。",
            },
            "captions": {
                "playerCaptionsTracklistRenderer": {
                    "captionTracks": [{"languageCode": "ja"}]
                }
            }
        }
        receipt = auto_research_pipeline.build_research_receipt(
            video_id="test1234567",
            player_data=mock_player,
            publish_date="2026-10-19",
        )
        self.assertEqual(receipt["schema_version"], "research_receipt_v1")
        self.assertEqual(len(receipt["videos"]), 1)
        v = receipt["videos"][0]
        self.assertEqual(v["video_id"], "test1234567")
        self.assertEqual(v["transcript_status"], "UNVERIFIED")
        self.assertLessEqual(len(v["title"]), 250)
        self.assertLessEqual(len(v["summary_ja"]), 300)
        self.assertLessEqual(len(v["detailed_findings_ja"]), 2500)
        self.assertLessEqual(v["detailed_findings_ja"].count("\n"), 25)
        self.assertLessEqual(len(v["chapters"]), 25)
        
        # Check forbidden keys
        forbidden = set(self.contract.get("forbidden_payload_keys", []))
        for key in v.keys():
            self.assertNotIn(key.lower(), forbidden)

    def test_duplicate_prevention_on_pipeline(self):
        res = auto_research_pipeline.run_pipeline("https://www.youtube.com/watch?v=u3ka_AAb8qE")
        self.assertEqual(res.get("status"), "ALREADY_REGISTERED")
        self.assertEqual(res.get("video_id"), "u3ka_AAb8qE")


if __name__ == "__main__":
    unittest.main()
