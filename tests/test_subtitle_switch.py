#!/usr/bin/env python3
"""Tests for automation/subtitle-switch (字幕保存スイッチ). 画面（tkinter）は起動しない。"""
import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "automation" / "subtitle-switch"


def load_app():
    loader = importlib.machinery.SourceFileLoader("subtitle_switch", str(APP_DIR / "subtitle_switch.pyw"))
    spec = importlib.util.spec_from_loader("subtitle_switch", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


app = load_app()


def make_vault(tmp, transcripts=(), notes=(), registered=()):
    vault = Path(tmp)
    (vault / "transcripts").mkdir()
    (vault / "research").mkdir()
    for vid in transcripts:
        (vault / "transcripts" / f"youtube-{vid}-transcript.md").write_text("x", encoding="utf-8")
    for vid in notes:
        (vault / "research" / f"youtube-{vid}-research.md").write_text("x", encoding="utf-8")
    (vault / "registry.json").write_text(json.dumps([{"video_id": v} for v in registered]), encoding="utf-8")
    return vault


class FakeRunner:
    def __init__(self, codes):
        self.codes = dict(codes)   # target -> (code, log)
        self.calls = []

    def __call__(self, args, on_line):
        self.calls.append(args)
        if args[3].endswith("publish_to_github.ps1"):
            return 0, "読み戻しOK"
        return self.codes.get(args[4], (0, "完了: SUCCESS"))


class ParseTests(unittest.TestCase):
    def test_video_id_forms(self):
        for text in ("https://www.youtube.com/watch?v=u3ka_AAb8qE", "https://youtu.be/u3ka_AAb8qE?t=30",
                     "https://www.youtube.com/shorts/u3ka_AAb8qE", "u3ka_AAb8qE"):
            self.assertEqual(app.video_id(text), "u3ka_AAb8qE")
        self.assertIsNone(app.video_id("https://example.com/"))

    def test_parse_urls_dedupes_and_skips_comments(self):
        text = "\n# memo\nhttps://youtu.be/u3ka_AAb8qE\nhttps://www.youtube.com/watch?v=u3ka_AAb8qE&t=5\nnot a url\nCnkEROU7fZw\n"
        self.assertEqual(app.parse_urls(text), [
            ("https://youtu.be/u3ka_AAb8qE", "u3ka_AAb8qE"), ("not a url", None), ("CnkEROU7fZw", "CnkEROU7fZw")])


class VaultStatusTests(unittest.TestCase):
    def test_waiting_and_finalize(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = make_vault(tmp, transcripts=["aaaaaaaaaaa", "bbbbbbbbbbb", "ccccccccccc"],
                               notes=["bbbbbbbbbbb", "ccccccccccc"], registered=["ccccccccccc"])
            self.assertEqual(app.vault_status(vault), {"waiting": ["aaaaaaaaaaa"], "finalize": ["bbbbbbbbbbb"]})

    def test_missing_vault_is_empty(self):
        self.assertEqual(app.vault_status(Path("/nonexistent-vault")), {"waiting": [], "finalize": []})


class ProcessTests(unittest.TestCase):
    def test_full_run_publishes_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = make_vault(tmp)
            runner, waits = FakeRunner({}), []
            out = app.process("https://youtu.be/aaaaaaaaaaa\nbbbbbbbbbbb", "claude", lambda m: None,
                              vault=vault, runner=runner, sleep=waits.append)
            self.assertEqual([c[-1] for c in runner.calls[:2]], ["claude", "claude"])
            self.assertTrue(all("-NoGitHub" in c for c in runner.calls[:2]))
            self.assertTrue(runner.calls[2][3].endswith("publish_to_github.ps1"))
            self.assertEqual(len(runner.calls), 3)
            self.assertEqual(waits, [app.WAIT_SEC])
            self.assertTrue(out["published"])

    def test_manual_stop_does_not_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = make_vault(tmp)
            runner = FakeRunner({"https://youtu.be/aaaaaaaaaaa": (9, "WAIT_MANUAL: ...")})
            out = app.process("https://youtu.be/aaaaaaaaaaa", "manual", lambda m: None,
                              vault=vault, runner=runner, sleep=lambda s: None)
            self.assertEqual(runner.calls[0][-1], "manual")
            self.assertEqual(len(runner.calls), 1)
            self.assertIsNone(out["published"])
            self.assertEqual(out["results"], [("aaaaaaaaaaa", "研究ノート待ち（手動で頼む）")])

    def test_finalizes_manual_notes_first_even_with_empty_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = make_vault(tmp, transcripts=["bbbbbbbbbbb"], notes=["bbbbbbbbbbb"])
            runner = FakeRunner({})
            out = app.process("", "manual", lambda m: None, vault=vault, runner=runner, sleep=lambda s: None)
            self.assertEqual(runner.calls[0][4], "bbbbbbbbbbb")
            self.assertTrue(runner.calls[1][3].endswith("publish_to_github.ps1"))
            self.assertTrue(out["published"])

    def test_login_failure_aborts_rest(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = make_vault(tmp)
            runner = FakeRunner({"aaaaaaaaaaa": (3, "STOP")})
            out = app.process("aaaaaaaaaaa\nbbbbbbbbbbb", "claude", lambda m: None,
                              vault=vault, runner=runner, sleep=lambda s: None)
            self.assertEqual(len(runner.calls), 1)
            self.assertEqual(out["results"][1], ("bbbbbbbbbbb", "中止（前の失敗が原因）"))

    def test_limit_and_skip_without_wait(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = make_vault(tmp)
            ids = [f"{i:011d}" for i in range(12)]
            runner = FakeRunner({v: (0, "SKIP: この動画は保存済みです") for v in ids})
            waits = []
            app.process("\n".join(ids), "claude", lambda m: None, vault=vault, runner=runner, sleep=waits.append)
            self.assertEqual(len(runner.calls), app.MAX_VIDEOS)   # skips only, no publish
            self.assertEqual(waits, [])


class FileContractTests(unittest.TestCase):
    def test_script_uses_claude_cli_not_agy(self):
        ps1 = (APP_DIR / "research_from_url.ps1").read_text(encoding="utf-8")
        code = "\n".join(l for l in ps1.splitlines() if not l.lstrip().startswith("#"))
        self.assertNotIn("agy", code)
        self.assertIn("& claude -p --model $Model --effort $Effort --permission-mode acceptEdits --tools Read Write Glob Grep", code)
        self.assertIn('[ValidateSet("claude", "manual")][string]$Writer = "claude"', code)
        self.assertIn("exit 9", code)

    def test_template_and_manual_prompt_share_the_okf_rules(self):
        tpl = (APP_DIR / "research_note_prompt_template.md").read_text(encoding="utf-8")
        self.assertIn('created_by: "{CREATED_BY}"', tpl)
        for heading in ("## 独自要約", "## 内容の流れ", "## 重要な知見", "## この研究室への応用", "## 限界・未確認"):
            self.assertIn(heading, tpl)
            self.assertIn(heading, app.MANUAL_PROMPT)
        for key in ('type: "RESEARCH_NOTE"', 'logical_id: "youtube:<VIDEO_ID>:research"',
                    'source_transcript_sha256: "<SHA256>"', 'source_transcript: "youtube:<VIDEO_ID>:transcript"'):
            self.assertIn(key, app.MANUAL_PROMPT)
        self.assertNotIn("{", app.MANUAL_PROMPT)


if __name__ == "__main__":
    unittest.main()
