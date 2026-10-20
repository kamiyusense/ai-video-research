#!/usr/bin/env python3
"""Tests for qa_run.py (T20: 質問回答の一括実行。偽クライアントでオフライン、Notebook接続0)."""
import contextlib
import hashlib
import io
import json
import socket
import subprocess
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "automation" / "gemini-notebook"))
import qa_check as qa  # noqa: E402
import qa_run as run  # noqa: E402

VID = "u3ka_AAb8qE"


def tree_hash():
    h = hashlib.sha256()
    for p in sorted([ROOT / "registry.json", *(ROOT / "research").glob("*.md")]):
        h.update(p.name.encode() + p.read_bytes())
    return h.hexdigest()


def good_answer(q):
    """質問の期待どおりの根拠をそろえた回答（qa_check で PASS になる）。"""
    e = q["expect"]
    t = e["time_seconds"]
    url = e["url"] + (f"&t={t}s" if t is not None else "&t=10s")
    clock = qa._mmss(t if t is not None else 10)
    ans = f"字幕原文（{e['transcript_id']}）の [{clock}] {url} が該当し、研究ノート（{e['research_id']}）でも確認できます。"
    if e["related"]:
        r = e["related"][0]
        ans += f"\n関連動画は {r['video_id']} で、{r['relation']} の関係です。"
    return ans


class FakeClient:
    """Notebookの代わり。answers は {質問文: 回答}、無ければ関係ない回答を返す。"""

    def __init__(self, answers=None, auth_ok=True, fail_on=None, auth_lost_after=None):
        self.answers = answers or {}
        self.auth_ok = auth_ok
        self.fail_on = set(fail_on or [])
        self.auth_lost_after = auth_lost_after
        self.asked = []
        self.auth_checks = 0

    def auth_check_passive(self):
        self.auth_checks += 1
        if self.auth_lost_after is not None and len(self.asked) >= self.auth_lost_after:
            return False
        return self.auth_ok

    def ask(self, question):
        self.asked.append(question)
        if question in self.fail_on:
            raise run.AskError("boom")
        return self.answers.get(question, "関係ない回答です")


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.videos = qa.load_videos(ROOT)
        cls.plan_all = qa.plan_for_videos(cls.videos)
        cls.plan_one = qa.plan_for_videos(cls.videos, VID)

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.out = Path(self._tmp.name) / "answers"


class TestAllowlist(unittest.TestCase):
    def test_ask_list_and_auth_check_are_allowed(self):
        c = run.NotebookLmCliAskClient("NB1")
        for key, fmt in (("auth_check_passive", {}), ("ask", {"question": "これは質問"}), ("list_sources", {})):
            self.assertEqual(c.build_args(key, **fmt)[0], "notebooklm")

    def test_commands_outside_the_allowlist_are_refused(self):
        for argv in (["notebooklm", "source", "add", "-", "--type", "text"],
                     ["notebooklm", "source", "delete", "SRC"],
                     ["notebooklm", "auth", "login"],
                     ["notebooklm", "auth", "refresh"],
                     ["notebooklm", "notebook", "create"],
                     ["rm", "-rf", "x"],
                     ["notebooklm"], []):
            with self.assertRaises(run.DisallowedCommand, msg=argv):
                run.ensure_allowed(argv)

    def test_a_forbidden_word_in_the_subcommand_is_refused_even_if_added_to_the_allowlist(self):
        with mock.patch.object(run, "COMMAND_ALLOWLIST", run.COMMAND_ALLOWLIST + (("notebooklm", "source", "add"),)):
            with self.assertRaises(run.DisallowedCommand):
                run.ensure_allowed(["notebooklm", "source", "add", "x"])

    def test_a_question_that_contains_a_write_word_is_still_allowed(self):
        run.ensure_allowed(["notebooklm", "ask", "delete や add の話はどこですか", "--json", "--notebook", "NB"])

    def test_a_tampered_commands_table_is_caught_before_anything_runs(self):
        c = run.NotebookLmCliAskClient("NB1")
        with mock.patch.dict(run.NotebookLmCliAskClient.COMMANDS, {"ask": ["notebooklm", "source", "add", "{question}"]}), \
                mock.patch.object(subprocess, "run", side_effect=AssertionError("subprocess は呼ばれない")):
            with self.assertRaises(run.DisallowedCommand):
                c.ask("質問")

    def test_the_ask_client_has_no_write_methods_and_the_module_never_logs_in(self):
        names = {n for n in dir(run.NotebookLmCliAskClient) if not n.startswith("_")}
        self.assertEqual(names - {"COMMANDS"}, {"build_args", "auth_check_passive", "ask"})
        for key, argv in run.NotebookLmCliAskClient.COMMANDS.items():
            self.assertFalse(set(argv[1:3]) & run.FORBIDDEN_WORDS, key)

    def test_cli_client_runs_ask_and_parses_json_or_plain_text(self):
        c = run.NotebookLmCliAskClient("NB1")
        cp = lambda out, rc=0: subprocess.CompletedProcess([], rc, stdout=out, stderr="")  # noqa: E731
        with mock.patch.object(subprocess, "run", return_value=cp(json.dumps({"answer": "答え"}))) as m:
            self.assertEqual(c.ask("質問"), "答え")
            self.assertEqual(m.call_args.args[0][:2], ["notebooklm", "ask"])
        with mock.patch.object(subprocess, "run", return_value=cp("ただの文章")):
            self.assertEqual(c.ask("質問"), "ただの文章")
        with mock.patch.object(subprocess, "run", return_value=cp("", rc=1)):
            with self.assertRaises(run.AskError):
                c.ask("質問")
        with mock.patch.object(subprocess, "run", side_effect=subprocess.TimeoutExpired("x", 1)):
            with self.assertRaises(run.AskError):
                c.ask("質問")
        with self.assertRaises(run.AskError):
            c.ask("--help")
        with self.assertRaises(ValueError):
            run.NotebookLmCliAskClient("")


class TestDryRun(Base):
    def test_dry_run_lists_all_questions_and_commands_with_zero_connections(self):
        with mock.patch.object(subprocess, "run", side_effect=AssertionError("接続しない")), \
                mock.patch.object(run.NotebookLmCliAskClient, "__init__", side_effect=AssertionError("クライアントを作らない")):
            rep = run.dry_run(self.plan_all)
        self.assertEqual((rep["status"], rep["connections"], rep["files_modified"]), ("DRY_RUN", 0, False))
        self.assertEqual(rep["question_count"], 93)
        self.assertEqual(rep["items"][0]["command"][:2], ["notebooklm", "ask"])
        self.assertIn("<notebook_id>", rep["items"][0]["command"])
        self.assertEqual(rep["items"][0]["command"][2], self.plan_all["questions"][0]["question"])
        self.assertTrue(all("add" not in i["command"][1:3] for i in rep["items"]))
        self.assertIn("UNVERIFIED".lower(), (rep["unverified"] + "unverified").lower())

    def test_limit_and_video_id_narrow_the_questions(self):
        self.assertEqual(run.dry_run(self.plan_all, "NB", limit=5)["question_count"], 5)
        rep = run.dry_run(self.plan_one, "NB")
        self.assertEqual([i["question_id"] for i in rep["items"]], [f"{VID}-Q1", f"{VID}-Q2", f"{VID}-Q3"])
        self.assertIn("NB", rep["items"][0]["command"])

    def test_cli_defaults_to_dry_run_without_touching_anything(self):
        before = tree_hash()
        out = io.StringIO()

        def blocked(*a, **k):
            raise AssertionError("network / subprocess")

        with mock.patch.object(subprocess, "run", blocked), mock.patch.object(urllib.request, "urlopen", blocked), \
                mock.patch.object(socket, "create_connection", blocked), contextlib.redirect_stdout(out):
            rc = run.main([])
            rc2 = run.main(["--video-id", VID, "--limit", "2"])
        self.assertEqual((rc, rc2), (0, 0))
        self.assertEqual(before, tree_hash())
        self.assertEqual(json.loads(out.getvalue().split("\n}\n")[0] + "\n}")["question_count"], 93)


class TestRunQuestions(Base):
    def test_aggregation_counts_verdicts_and_lists_by_video(self):
        qs = self.plan_one["questions"]
        client = FakeClient({qs[0]["question"]: good_answer(qs[0]), qs[1]["question"]: good_answer(qs[1])})
        rep = run.run_questions(self.plan_one, self.videos, client, self.out)
        self.assertEqual(rep["status"], "DONE")
        self.assertEqual((rep["planned"], rep["asked"]), (3, 3))
        self.assertEqual(rep["counts"], {"PASS": 2, "PARTIAL": 0, "FAIL": 1, "ERROR": 0})
        self.assertEqual(rep["by_video"][VID]["questions"], {f"{VID}-Q1": "PASS", f"{VID}-Q2": "PASS", f"{VID}-Q3": "FAIL"})
        self.assertEqual([n["question_id"] for n in rep["not_pass"]], [f"{VID}-Q3"])
        self.assertEqual((rep["notebook_writes"], rep["repo_files_modified"]), (0, False))
        self.assertEqual(client.asked, [q["question"] for q in qs])
        self.assertIn("PASS 2 / PARTIAL 0 / FAIL 1", run.format_summary(rep))

    def test_all_passing_run_over_the_real_93_questions(self):
        client = FakeClient({q["question"]: good_answer(q) for q in self.plan_all["questions"]})
        rep = run.run_questions(self.plan_all, self.videos, client, self.out)
        self.assertEqual(rep["counts"], {"PASS": 93, "PARTIAL": 0, "FAIL": 0, "ERROR": 0})
        self.assertEqual(len(rep["by_video"]), 31)
        self.assertEqual(len(list(self.out.glob("*.txt"))), 93)

    def test_limit_asks_only_the_first_questions(self):
        client = FakeClient()
        rep = run.run_questions(self.plan_all, self.videos, client, self.out, limit=4)
        self.assertEqual((rep["planned"], rep["asked"], len(client.asked)), (4, 4, 4))

    def test_answers_are_saved_only_under_the_out_dir_and_not_in_the_repo(self):
        qs = self.plan_one["questions"]
        run.run_questions(self.plan_one, self.videos, FakeClient({qs[0]["question"]: good_answer(qs[0])}), self.out)
        self.assertEqual(sorted(p.name for p in self.out.iterdir()), [f"{VID}-Q{i}.txt" for i in (1, 2, 3)])
        self.assertIn(VID, (self.out / f"{VID}-Q1.txt").read_text(encoding="utf-8"))
        self.assertFalse((ROOT / "automation" / "gemini-notebook" / f"{VID}-Q1.txt").exists())

    def test_out_dir_inside_the_repo_is_refused_before_any_question(self):
        client = FakeClient()
        for bad in (ROOT, ROOT / "research", ROOT / "automation" / "x" / ".." / "y", Path("research")):
            with mock.patch.object(Path, "cwd", return_value=ROOT):
                with self.assertRaises(ValueError, msg=str(bad)):
                    run.run_questions(self.plan_one, self.videos, client, bad)
        self.assertEqual((client.asked, client.auth_checks), ([], 0))
        self.assertTrue(run.check_out_dir(Path("/tmp/qa_answers")).is_absolute())

    def test_expired_login_at_the_start_stops_with_nothing_written(self):
        client = FakeClient(auth_ok=False)
        rep = run.run_questions(self.plan_one, self.videos, client, self.out)
        self.assertEqual((rep["status"], rep["asked"], rep["notebook_writes"]), ("AUTH_EXPIRED", 0, 0))
        self.assertIn("ログインし直して", rep["user_action"])
        self.assertEqual(client.asked, [])
        self.assertFalse(self.out.exists())

    def test_login_lost_midway_stops_and_keeps_the_answers_so_far(self):
        qs = self.plan_one["questions"]
        client = FakeClient({q["question"]: good_answer(q) for q in qs}, fail_on=[qs[1]["question"]], auth_lost_after=2)
        rep = run.run_questions(self.plan_one, self.videos, client, self.out)
        self.assertEqual((rep["status"], rep["asked"]), ("AUTH_EXPIRED", 1))
        self.assertEqual(rep["counts"]["PASS"], 1)
        self.assertEqual([p.name for p in self.out.iterdir()], [f"{VID}-Q1.txt"])
        self.assertEqual(len(client.asked), 2)          # 失敗した問の後は質問しない

    def test_auth_expired_raised_by_the_client_also_stops(self):
        class Expiring(FakeClient):
            def ask(self, question):
                raise run.AuthExpired("expired")

        rep = run.run_questions(self.plan_one, self.videos, Expiring(), self.out)
        self.assertEqual((rep["status"], rep["asked"]), ("AUTH_EXPIRED", 0))

    def test_a_failed_question_is_an_error_and_the_run_continues(self):
        qs = self.plan_one["questions"]
        client = FakeClient({qs[0]["question"]: good_answer(qs[0])}, fail_on=[qs[1]["question"]])
        rep = run.run_questions(self.plan_one, self.videos, client, self.out)
        self.assertEqual(rep["status"], "DONE")
        self.assertEqual(rep["counts"], {"PASS": 1, "PARTIAL": 0, "FAIL": 1, "ERROR": 1})
        self.assertEqual(rep["by_video"][VID]["questions"][f"{VID}-Q2"], "ERROR")

    def test_repeated_errors_abort_the_run(self):
        client = FakeClient(fail_on=[q["question"] for q in self.plan_all["questions"]])
        rep = run.run_questions(self.plan_all, self.videos, client, self.out)
        self.assertEqual((rep["status"], rep["asked"], rep["counts"]["ERROR"]), ("ABORTED_TOO_MANY_ERRORS", 3, 3))
        self.assertEqual(len(client.asked), 3)


class TestLiveCli(Base):
    def run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = run.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def test_live_requires_notebook_id_and_out_dir(self):
        with mock.patch.object(run, "NotebookLmCliAskClient", side_effect=AssertionError("作らない")):
            self.assertEqual(self.run_cli(["--live"])[0], 2)
            self.assertEqual(self.run_cli(["--live", "--notebook-id", "NB"])[0], 2)
            self.assertEqual(self.run_cli(["--live", "--out-dir", str(self.out)])[0], 2)

    def test_out_dir_in_the_repo_and_unknown_video_are_usage_errors(self):
        with mock.patch.object(run, "NotebookLmCliAskClient", side_effect=AssertionError("作らない")):
            rc, _, err = self.run_cli(["--live", "--notebook-id", "NB", "--out-dir", str(ROOT / "research")])
            self.assertEqual(rc, 2)
            self.assertIn("repo の中", err)
            self.assertEqual(self.run_cli(["--out-dir", str(ROOT)])[0], 2)         # dry-run でも拒否
            self.assertEqual(self.run_cli(["--video-id", "nonexistent"])[0], 2)

    def test_live_with_a_fake_client_prints_the_summary_and_exit_codes_follow_the_status(self):
        qs = self.plan_one["questions"]
        fake = FakeClient({q["question"]: good_answer(q) for q in qs})
        with mock.patch.object(run, "NotebookLmCliAskClient", return_value=fake) as ctor:
            rc, out, _ = self.run_cli(["--live", "--notebook-id", "NB", "--out-dir", str(self.out), "--video-id", VID, "--summary"])
        ctor.assert_called_once_with("NB")
        self.assertEqual(rc, 0)
        self.assertIn("PASS 3 / PARTIAL 0 / FAIL 0 / ERROR 0", out)
        self.assertIn(str(self.out), out)
        with mock.patch.object(run, "NotebookLmCliAskClient", return_value=FakeClient()):
            rc, out, _ = self.run_cli(["--live", "--notebook-id", "NB", "--out-dir", str(self.out / "2"), "--video-id", VID])
        self.assertEqual((rc, json.loads(out)["counts"]["FAIL"]), (1, 3))
        with mock.patch.object(run, "NotebookLmCliAskClient", return_value=FakeClient(auth_ok=False)):
            rc, out, _ = self.run_cli(["--live", "--notebook-id", "NB", "--out-dir", str(self.out / "3"), "--limit", "2"])
        self.assertEqual((rc, json.loads(out)["status"]), (3, "AUTH_EXPIRED"))

    def test_nothing_in_the_repo_changes_and_every_command_in_the_table_is_allowed(self):
        before = tree_hash()
        with mock.patch.object(run, "NotebookLmCliAskClient", return_value=FakeClient()):
            self.run_cli(["--live", "--notebook-id", "NB", "--out-dir", str(self.out), "--limit", "3"])
        self.assertEqual(before, tree_hash())
        for key, argv in run.NotebookLmCliAskClient.COMMANDS.items():
            run.ensure_allowed([a.format(question="q", notebook_id="NB") for a in argv])


if __name__ == "__main__":
    unittest.main()
