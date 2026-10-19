#!/usr/bin/env python3
"""Tests for notebook_auto_ingest.py v3.0."""
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTO_DIR = ROOT / "automation" / "gemini-notebook"

import sys
sys.path.insert(0, str(AUTO_DIR))
import notebook_auto_ingest


class TestNotebookAutoIngest(unittest.TestCase):
    def test_cdp_port_probe(self):
        client = notebook_auto_ingest.CDPClient()
        is_open = client.is_port_open(timeout=0.2)
        self.assertIsInstance(is_open, bool)

    def test_sync_to_drive_notebook_sources(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            fake_research_md = tmp_path / "fake_research.md"
            fake_research_md.write_text("# Fake Research Note\n", encoding="utf-8")

            res = notebook_auto_ingest.sync_to_drive_notebook_sources(
                video_id="testVid1234",
                video_url="https://www.youtube.com/watch?v=testVid1234",
                video_title="テスト動画",
                research_md_path=fake_research_md,
                target_dir=tmp_path / "sync_target",
            )
            self.assertEqual(res["status"], "DRIVE_SYNC_SUCCESS")
            self.assertEqual(len(res["synced_files"]), 2)
            
            files = [Path(f["path"]) for f in res["synced_files"]]
            self.assertTrue(all(f.exists() for f in files))
            self.assertTrue(any(f.name.endswith("_youtube_source.txt") for f in files))
            self.assertTrue(any(f.name.endswith("_research_note.md") for f in files))

    def test_ingest_and_verify_readback_pass(self):
        """Mock mode: Both YouTube and Research Note present results in is_full_success=True."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            fake_md = tmp_path / "note.md"
            fake_md.write_text("dummy note", encoding="utf-8")

            res = notebook_auto_ingest.ingest_and_verify_notebook(
                video_id="dummy123456",
                video_url="https://www.youtube.com/watch?v=dummy123456",
                video_title="Dummy Video",
                research_md_path=fake_md,
                mock_cdp=True,
                mock_sources=["dummy123456", "研究ノート_dummy123456"],
                drive_dir=tmp_path / "drive_sync",
            )
            self.assertEqual(res["status"], "NOTEBOOK_REGISTRATION_VERIFIED")
            self.assertTrue(res["is_full_success"])
            self.assertTrue(res["readback"]["youtube_source_found"])
            self.assertTrue(res["readback"]["research_note_found"])

    def test_ingest_and_verify_readback_fail(self):
        """Mock mode: Missing YouTube or Note results in is_full_success=False."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            fake_md = tmp_path / "note.md"
            fake_md.write_text("dummy note", encoding="utf-8")

            res = notebook_auto_ingest.ingest_and_verify_notebook(
                video_id="dummy123456",
                video_url="https://www.youtube.com/watch?v=dummy123456",
                video_title="Dummy Video",
                research_md_path=fake_md,
                mock_cdp=True,
                mock_sources=["unrelated_source_item"],  # Missing target sources
                drive_dir=tmp_path / "drive_sync",
            )
            self.assertNotEqual(res["status"], "NOTEBOOK_REGISTRATION_VERIFIED")
            self.assertFalse(res["is_full_success"])
            self.assertFalse(res["readback"]["youtube_source_found"])
            self.assertFalse(res["readback"]["research_note_found"])

    def test_chrome_binary_finder(self):
        # find_chrome_binary should return str or None
        chrome_bin = notebook_auto_ingest.find_chrome_binary()
        if chrome_bin:
            self.assertTrue(Path(chrome_bin).is_file())


if __name__ == "__main__":
    unittest.main()
