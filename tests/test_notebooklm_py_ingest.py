#!/usr/bin/env python3
"""Tests for notebooklm_py_ingest.py (offline, fake client only)."""
import socket
import sys
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
AUTO_DIR = ROOT / "automation" / "gemini-notebook"
sys.path.insert(0, str(AUTO_DIR))
import notebooklm_py_ingest as ing  # noqa: E402

VID = "u3ka_AAb8qE"
TITLE = "OKFで作るAI知識ベースの設計"
NOTE = (
    "# 研究ノート u3ka_AAb8qE\n\n<!-- ID: AI_VIDEO_RESEARCH_NOTE:u3ka_AAb8qE -->\n"
    "## 要点\n1. **OKF** は荷札\n2. > 引用です\n- 参考: [公式](https://example.com/okf)\n"
)
CUES = [(0.0, 2.0, "こんにちは"), (2.0, 3.0, "今日はOKFの話です")]


def notebook_style(text):
    """NotebookLMの表示用整形を真似る：記号・HTMLコメント・リンク記法が消え、改行が足される。"""
    out = ing._HTML_COMMENT_RE.sub("", text)
    out = ing._MD_LINK_RE.sub(lambda m: m.group(1), out)
    out = ing._LIST_NUM_RE.sub("", out)
    out = out.replace("#", "").replace("**", "").replace("> ", "")
    return out.replace("\n", "\n\n")


class FakeClient:
    def __init__(self, sources=None, auth_ok=True, add_raises=False, add_lands=True, mangle=None):
        self.sources = [dict(s) for s in (sources or [])]
        self.bodies = {s["id"]: s.get("body", "") for s in self.sources}
        self.auth_ok = auth_ok
        self.add_raises = add_raises
        self.add_lands = add_lands
        self.mangle = mangle or (lambda t: t)
        self.add_calls = []
        self.auth_calls = 0

    def auth_check_passive(self):
        self.auth_calls += 1
        return self.auth_ok

    def list_sources(self):
        return [{"id": s["id"], "title": s["title"]} for s in self.sources]

    def get_fulltext(self, source_id):
        return self.bodies[source_id]

    def add_text(self, title, text):
        self.add_calls.append((title, text))
        sid = f"new-{len(self.add_calls)}"
        if self.add_lands:
            self.sources.append({"id": sid, "title": title})
            self.bodies[sid] = self.mangle(text)
        if self.add_raises:
            raise TimeoutError("network timeout after send")
        return sid


YT_SOURCE = {"id": "yt-1", "title": TITLE, "body": "動画の文字起こし本文"}
TR_SOURCE = {"id": "tr-1", "title": ing.transcript_title(VID, TITLE)}
NOTE_SOURCE = {"id": "rn-1", "title": ing.research_note_title(VID)}


class TestNotebookLmPyIngest(unittest.TestCase):
    def run_live(self, client, cues=CUES):
        return ing.run_ingest(client, VID, TITLE, NOTE, cues=cues, live=True, notebook_id="nb-1")

    def test_both_present_is_no_op(self):
        c = FakeClient([YT_SOURCE, TR_SOURCE, NOTE_SOURCE])
        res = self.run_live(c)
        self.assertEqual(res["status"], "NO_OP")
        self.assertEqual(c.add_calls, [])

    def test_only_transcript_missing_adds_only_transcript(self):
        c = FakeClient([YT_SOURCE, NOTE_SOURCE])
        res = self.run_live(c)
        self.assertEqual([t for t, _ in c.add_calls], [ing.transcript_title(VID, TITLE)])
        self.assertEqual(res["status"], "SUCCESS_2_SOURCE_OKF")
        self.assertTrue(res["distinct_source_ids"])
        self.assertEqual(res["transcript_acquisition_method"], ing.ACQ_TIMEDTEXT)
        self.assertEqual(res["transcript_cue_count"], 2)

    def test_both_missing_adds_two_distinct_sources(self):
        c = FakeClient([YT_SOURCE], mangle=notebook_style)
        res = self.run_live(c)
        self.assertEqual(len(c.add_calls), 2)
        self.assertEqual(res["status"], "SUCCESS_2_SOURCE_OKF")
        self.assertFalse(res["readback"]["research_note"]["exact_match"])
        self.assertTrue(res["readback"]["research_note"]["normalized_match"])

    def test_auth_expired_halts_without_writes(self):
        c = FakeClient([YT_SOURCE], auth_ok=False)
        res = self.run_live(c)
        self.assertEqual(res["status"], "AUTH_EXPIRED_HALT")
        self.assertEqual(c.add_calls, [])
        self.assertEqual(res["writes"], [])

    def test_default_is_dry_run_without_writes(self):
        c = FakeClient([YT_SOURCE])
        res = ing.run_ingest(c, VID, TITLE, NOTE, cues=CUES)
        self.assertEqual(res["status"], "DRY_RUN_PLAN")
        self.assertEqual(res["plan"], ["transcript", "research_note"])
        self.assertEqual(c.add_calls, [])

    def test_live_requires_notebook_id(self):
        c = FakeClient([YT_SOURCE])
        res = ing.run_ingest(c, VID, TITLE, NOTE, cues=CUES, live=True, notebook_id=None)
        self.assertEqual(res["status"], "LIVE_REQUIRES_NOTEBOOK_ID")
        self.assertEqual(c.add_calls, [])
        self.assertEqual(c.auth_calls, 0)

    def test_cli_live_without_notebook_id_exits(self):
        note = ROOT / "research" / "2026-10-10-BStkW1HTfmk-obsidian-preliminary.md"
        with mock.patch.object(ing.subprocess, "run") as run:
            rc = ing.main(["--video-id", VID, "--video-title", TITLE, "--research-md", str(note), "--live"])
        self.assertEqual(rc, 2)
        run.assert_not_called()

    def test_unknown_write_result_is_not_resent_and_confirmed_by_readback(self):
        c = FakeClient([YT_SOURCE, NOTE_SOURCE], add_raises=True, add_lands=True)
        res = self.run_live(c)
        self.assertEqual(len(c.add_calls), 1)
        self.assertEqual(res["writes"][0]["result"], "CONFIRMED_BY_READBACK")
        self.assertEqual(res["status"], "SUCCESS_2_SOURCE_OKF")

    def test_unknown_write_result_not_landed_stops_as_unknown(self):
        c = FakeClient([YT_SOURCE, NOTE_SOURCE], add_raises=True, add_lands=False)
        res = self.run_live(c)
        self.assertEqual(len(c.add_calls), 1)
        self.assertEqual(res["status"], "WRITE_RESULT_UNKNOWN")

    def test_readback_one_char_missing_fails(self):
        c = FakeClient([YT_SOURCE, TR_SOURCE], mangle=lambda t: notebook_style(t).replace("荷札", "荷", 1))
        res = self.run_live(c)
        self.assertEqual(res["status"], "READBACK_MISMATCH")

    def test_normalized_match_function(self):
        self.assertTrue(ing.readback_matches(NOTE, notebook_style(NOTE))["match"])
        self.assertFalse(ing.readback_matches(NOTE, notebook_style(NOTE).replace("荷札", "荷"))["match"])
        self.assertTrue(ing.readback_matches(NOTE, NOTE)["exact_match"])
        self.assertTrue(ing.readback_matches("a &gt; b", "a > b")["match"])

    def test_transcript_without_cues_uses_notebook_youtube_fulltext(self):
        c = FakeClient([YT_SOURCE, NOTE_SOURCE])
        res = self.run_live(c, cues=None)
        self.assertEqual(res["transcript_acquisition_method"], ing.ACQ_NOTEBOOK_YOUTUBE)
        self.assertEqual(res["transcript_cue_count"], 0)
        text = c.add_calls[0][1]
        self.assertIn(f'acquisition_method: "{ing.ACQ_NOTEBOOK_YOUTUBE}"', text)
        self.assertIn('transcript_status: "UNVERIFIED"', text)
        self.assertIn("cue_count: 0", text)
        self.assertIn("動画の文字起こし本文", text)

    def test_no_delete_capability(self):
        for obj in (ing.NotebookClient, ing.NotebookLmCliClient):
            names = [n.lower() for n in dir(obj)]
            self.assertFalse([n for n in names if "delete" in n or "remove" in n], obj)
        flat = " ".join(" ".join(v) for v in ing.NotebookLmCliClient.COMMANDS.values()).lower()
        self.assertNotIn("delete", flat)
        self.assertNotIn("remove", flat)

    def test_run_is_offline_with_fake_client(self):
        def blocked(*a, **k):
            raise AssertionError("network call")

        c = FakeClient([YT_SOURCE], mangle=notebook_style)
        with mock.patch.object(urllib.request, "urlopen", blocked), \
                mock.patch.object(socket, "create_connection", blocked), \
                mock.patch.object(ing.subprocess, "run", blocked):
            res = self.run_live(c)
        self.assertEqual(res["status"], "SUCCESS_2_SOURCE_OKF")


if __name__ == "__main__":
    unittest.main()
