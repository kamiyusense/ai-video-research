#!/usr/bin/env python3
"""Tests for notebook_auto_ingest.py."""
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
    def test_probe_cdp_connection(self):
        # Should return (bool, str, list/None) without uncaught exception
        ok, msg, tabs = notebook_auto_ingest.probe_cdp_connection(timeout=0.5)
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(msg, str)

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
            
            # Check 2 files created
            files = [Path(f["path"]) for f in res["synced_files"]]
            self.assertTrue(all(f.exists() for f in files))
            self.assertTrue(any(f.name.endswith("_youtube_source.txt") for f in files))
            self.assertTrue(any(f.name.endswith("_research_note.md") for f in files))

    def test_ingest_to_notebook(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            fake_md = tmp_path / "note.md"
            fake_md.write_text("dummy note", encoding="utf-8")

            res = notebook_auto_ingest.ingest_to_notebook(
                video_id="dummy123456",
                video_url="https://www.youtube.com/watch?v=dummy123456",
                video_title="Dummy",
                research_md_path=fake_md,
                drive_dir=tmp_path / "drive_sync",
            )
            self.assertIn("status", res)
            self.assertEqual(res["notebook_id"], notebook_auto_ingest.NOTEBOOK_ID)
            self.assertIn("drive_sync", res)
            self.assertIn("cdp_probe", res)


if __name__ == "__main__":
    unittest.main()
