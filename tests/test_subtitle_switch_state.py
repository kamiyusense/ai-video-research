"""Offline state/inbox acceptance checks (no GUI, model, or services)."""
import importlib.util
import json
import tempfile
import unittest
from unittest.mock import patch
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "switch_state", ROOT / "automation/subtitle-switch/switch_state.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class StateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.inbox = self.root / "inbox"
        self.inbox.mkdir()
        (self.inbox / "20261027_videos.json").write_text(json.dumps({"videos": [
            {"url": "https://youtu.be/abcdefghijk?t=83", "title": "demo",
             "transcript": "MUST NOT PERSIST"},
            {"url": "https://www.youtube.com/watch?v=abcdefghijk"},
        ]}), encoding="utf-8")

    def inventory(self):
        store = app.Inventory(self.root / "state.json")
        rows, _ = app.read_inbox(self.inbox)
        store.refresh(rows)
        return store

    def test_list_ignores_gdoc_and_isolates_bad_json(self):
        (self.inbox / "ignored.gdoc").write_text("not JSON")
        (self.inbox / "broken.json").write_text("{")
        rows, errors = app.read_inbox(self.inbox)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["url"], "https://www.youtube.com/watch?v=abcdefghijk")
        self.assertEqual(rows[0]["channel"], "")
        self.assertEqual(errors, [{"file": "broken.json", "status": "要確認"}])

    def test_rejected_stays_hidden_after_refresh_restart_and_can_restore(self):
        store = self.inventory()
        store.reject("abcdefghijk", reason="もう知ってる")
        store = self.inventory()
        self.assertEqual(store.visible(), [])
        self.assertEqual(len(store.visible(show_rejected=True)), 1)
        store.reject("abcdefghijk", False)
        self.assertEqual(len(self.inventory().visible()), 1)

    def test_progress_survives_restart(self):
        store = self.inventory()
        store.data["videos"]["abcdefghijk"]["completed_stages"] = ["intake"]
        store.save()
        self.assertEqual(self.inventory().visible()[0]["completed_stages"], ["intake"])

    def test_corrupt_state_stops_without_overwrite(self):
        path = self.root / "state.json"
        path.write_text("broken")
        with self.assertRaises(ValueError):
            app.Inventory(path)
        self.assertEqual(path.read_text(), "broken")

    def test_preferences_names_schema_no_transcript_and_seed_untouched(self):
        store = self.inventory()
        store.reject("abcdefghijk", reason="興味なし")
        document = store.preferences(date(2026, 10, 27))
        folder = self.root / "preferences"
        folder.mkdir()
        seed = folder / "preferences_seed.json"
        seed.write_text('{"interests": []}')
        first = app.write_preferences(folder, document)
        second = app.write_preferences(folder, document)
        self.assertEqual(first.name, "preferences_20261027.json")
        self.assertEqual(second.name, "preferences_20261027_2.json")
        self.assertEqual(json.loads(first.read_text()), document)
        self.assertNotIn("MUST NOT PERSIST", first.read_text())
        self.assertNotIn("MUST NOT PERSIST", store.path.read_text())
        self.assertEqual(seed.read_text(), '{"interests": []}')

    def test_preference_queue_kept_on_destination_failure(self):
        outbox = self.root / "outbox"
        path = app.write_preferences(outbox, self.inventory().preferences())
        destination = self.root / "not_directory"
        destination.write_text("blocked")
        self.assertEqual(app.flush_preferences(outbox, destination), [])
        self.assertTrue(path.exists())
        targets = app.flush_preferences(outbox, self.root / "drive")
        self.assertEqual(len(targets), 1)
        self.assertFalse(path.exists())

    def test_preference_delivery_after_crash_does_not_duplicate(self):
        outbox, drive = self.root / "outbox", self.root / "drive"
        document = self.inventory().preferences()
        queued = app.write_preferences(outbox, document)
        delivered = app.write_preferences(drive, document)
        # Simulate death after destination write but before removing the queue file.
        self.assertEqual(app.flush_preferences(outbox, drive), [delivered])
        self.assertFalse(queued.exists())
        self.assertEqual(len(list(drive.glob("preferences_*.json"))), 1)

    def test_unexpected_preference_json_preserves_queue(self):
        outbox, drive = self.root / "outbox", self.root / "drive"
        queued = app.write_preferences(outbox, self.inventory().preferences())
        drive.mkdir()
        unexpected = drive / "preferences_20261026.json"
        for content in ('[]', 'null', '42', '"text"'):
            with self.subTest(content=content):
                unexpected.write_text(content, encoding="utf-8")
                self.assertEqual(app.flush_preferences(outbox, drive), [])
                self.assertTrue(queued.exists())
                self.assertEqual(unexpected.read_text(), content)
        unexpected.unlink()
        self.assertEqual(len(app.flush_preferences(outbox, drive)), 1)

    def test_cleanup_failure_is_pending_and_next_delivery_does_not_duplicate(self):
        outbox, drive = self.root / "outbox", self.root / "drive"
        queued = app.write_preferences(outbox, self.inventory().preferences())
        with patch.object(Path, "unlink", side_effect=PermissionError("locked")):
            self.assertEqual(app.flush_preferences(outbox, drive), [])
        self.assertTrue(queued.exists())
        self.assertEqual(len(list(drive.glob("preferences_*.json"))), 1)
        self.assertEqual(len(app.flush_preferences(outbox, drive)), 1)
        self.assertFalse(queued.exists())
        self.assertEqual(len(list(drive.glob("preferences_*.json"))), 1)


if __name__ == "__main__":
    unittest.main()
