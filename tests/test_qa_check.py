#!/usr/bin/env python3
"""Tests for qa_check.py (T19: 質問回答の確認を全動画へ広げる道具。オフライン・読み取りのみ)."""
import contextlib
import hashlib
import io
import json
import socket
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "automation" / "gemini-notebook"))
import qa_check as qa  # noqa: E402

A, B, C = "AAAAAAAAAAA", "BBBBBBBBBBB", "CCCCCCCCCCC"
UA = f"https://www.youtube.com/watch?v={A}"


def tree_hash():
    h = hashlib.sha256()
    for p in sorted([ROOT / "registry.json", *(ROOT / "research").glob("*.md")]):
        h.update(p.name.encode() + p.read_bytes())
    return h.hexdigest()


class TestSelftest(unittest.TestCase):
    def test_selftest_cases_are_all_judged_as_expected(self):
        rep = qa.run_selftest()
        self.assertEqual(rep["failed"], [])
        self.assertEqual(rep["status"], "SELFTEST_OK")
        self.assertGreaterEqual(rep["case_count"], 15)
        self.assertEqual({c["expected"] for c in rep["cases"]}, {qa.PASS, qa.PARTIAL, qa.FAIL})   # 3 種類の判定を全部試している

    def test_selftest_cli_exits_zero_and_needs_no_repository_data(self):
        buf = io.StringIO()
        with mock.patch.object(qa, "load_videos", side_effect=AssertionError("実データは読まない")), contextlib.redirect_stdout(buf):
            self.assertEqual(qa.main(["--selftest"]), 0)
        self.assertEqual(json.loads(buf.getvalue())["status"], "SELFTEST_OK")


class TestCheckRules(unittest.TestCase):
    """合成データで (a)〜(d) を1つずつ確かめる。"""

    def setUp(self):
        self.videos = qa.synthetic_videos()
        self.plan = {q["id"].split("-")[-1]: q for q in qa.plan_for_video(self.videos[A], self.videos)}
        self.good = (f"字幕原文（youtube:{A}:transcript）の [00:08:16] {UA}&t=496s で話しています。\n"
                     f"研究ノート（youtube:{A}:research）にも同じ箇所があります。")

    def verdict(self, answer, q="Q1"):
        return qa.check_answer(answer, self.plan[q], self.videos)

    def test_a_sources(self):
        self.assertEqual(self.verdict(self.good)["checks"]["a"], qa.PASS)
        self.assertEqual(self.verdict(f"研究ノート（youtube:{A}:research） {UA}&t=496s")["checks"]["a"], qa.PARTIAL)
        self.assertEqual(self.verdict(f"字幕原文（youtube:{A}:transcript） {UA}&t=496s")["checks"]["a"], qa.PARTIAL)
        self.assertEqual(self.verdict(f"{UA}&t=496s")["checks"]["a"], qa.FAIL)

    def test_a_transcript_can_be_cited_by_title_id_or_time_anchor(self):
        title = "OKFの荷札とフロントマター入門"
        by_title = f"【字幕原文】{title}［{A}］と研究ノート「{title}」 {UA}&t=496s"
        self.assertEqual(self.verdict(by_title)["checks"]["a"], qa.PASS)
        by_id = f"AI_VIDEO_TRANSCRIPT_RAW:{A} と AI_VIDEO_RESEARCH_NOTE:{A} {UA}&t=496s"
        self.assertEqual(self.verdict(by_id)["checks"]["a"], qa.PASS)
        by_anchor = f"[00:08:16] {UA}&t=496s に該当。研究ノート（youtube:{A}:research）も参照。"
        self.assertEqual(self.verdict(by_anchor)["checks"]["a"], qa.PASS)
        old_anchor = f"▶00:08:16 {UA}&t=496s に該当。研究ノート（youtube:{A}:research）も参照。"
        self.assertEqual(self.verdict(old_anchor)["checks"]["a"], qa.PASS)

    def test_b_links(self):
        self.assertEqual(self.verdict(self.good)["checks"]["b"], qa.PASS)
        no_t = self.good.replace("&t=496s", "")
        self.assertEqual(self.verdict(no_t)["checks"]["b"], qa.PARTIAL)
        self.assertEqual(self.verdict(self.good.replace(UA + "&t=496s", "どこか"))["checks"]["b"], qa.FAIL)
        self.assertEqual(self.verdict(self.good + "\nhttps://youtu.be/ZZZZZZZZZZZ?t=5")["checks"]["b"], qa.FAIL)    # 台帳にないID
        self.assertEqual(self.verdict(self.good.replace("[00:08:16]", "[00:01:00]"))["checks"]["b"], qa.FAIL)    # 時刻表記が食い違う
        far = self.good.replace("[00:08:16]", "[01:00:00]").replace("t=496s", "t=3600s")
        self.assertEqual(self.verdict(far)["checks"]["b"], qa.PARTIAL)                                           # 期待する区間から遠い

    def test_b_window_allows_the_one_minute_paragraph_error(self):
        lo, hi = self.plan["Q2"]["expect"]["time_window"]
        self.assertEqual((lo, hi), (496 - qa.WINDOW_MARGIN_SEC, 548 + qa.WINDOW_MARGIN_SEC))
        inside = f"字幕原文（youtube:{A}:transcript）と研究ノート（youtube:{A}:research） [00:07:30] {UA}&t=450s"
        self.assertEqual(self.verdict(inside, "Q2")["verdict"], qa.PASS)

    def test_c_related(self):
        ok = self.good + f"\n{B} とは COMPLEMENTS（補完）の関係です。"
        self.assertEqual(self.verdict(ok, "Q3")["checks"]["c"], qa.PASS)
        self.assertEqual(self.verdict(self.good + f"\n{B} とは EXTENDS（発展）の関係です。", "Q3")["checks"]["c"], qa.FAIL)
        self.assertEqual(self.verdict(self.good + f"\n{C} は UPDATES ですが確定です。", "Q3")["checks"]["c"], qa.PARTIAL)
        self.assertEqual(self.verdict(self.good + f"\n{B} と {C} は関連しています。", "Q3")["checks"]["c"], qa.PARTIAL)   # 登録のない組
        self.assertEqual(self.verdict(self.good)["checks"]["c"], qa.SKIP)             # 関連に触れない質問では対象外
        self.assertEqual(self.verdict(self.good, "Q3")["checks"]["c"], qa.PARTIAL)    # 関連を尋ねたのに触れていない

    def test_c_relation_is_symmetric_and_status_is_respected(self):
        # B 側の記載（B → A, COMPLEMENTS）だけがある組でも、A から見て同じ関係として扱う
        videos = qa.synthetic_videos()
        videos[A]["related"] = []
        plan = {q["id"].split("-")[-1]: q for q in qa.plan_for_video(videos[A], videos)}
        res = qa.check_answer(self.good + f"\n{B} とは UPDATES の関係です。", plan["Q3"], videos)
        self.assertEqual(res["checks"]["c"], qa.FAIL)

    def test_d_dates(self):
        base = self.good + f"\n{B}（RAG探索設計の基本と検索の流れ）は COMPLEMENTS（補完）です。"
        self.assertEqual(self.verdict(base + f"\n{B} の投稿日は 2026-08-20 です。", "Q3")["checks"]["d"], qa.PASS)
        self.assertEqual(self.verdict(base + f"\n{B} の投稿日は 2026/08/21 です。", "Q3")["checks"]["d"], qa.FAIL)
        self.assertEqual(self.verdict(base + f"\n{B} は {A} より新しいです。", "Q3")["checks"]["d"], qa.PASS)
        self.assertEqual(self.verdict(base + f"\n{B} は {A} より古いです。", "Q3")["checks"]["d"], qa.FAIL)
        self.assertEqual(self.verdict(base + f"\n{A} は {B} より古い動画です。", "Q3")["checks"]["d"], qa.PASS)
        self.assertEqual(self.verdict(self.good)["checks"]["d"], qa.SKIP)

    def test_d_date_without_naming_a_video_is_about_the_asked_video(self):
        self.assertEqual(self.verdict(self.good + "\n投稿日は2026年7月25日です。")["checks"]["d"], qa.PASS)
        self.assertEqual(self.verdict(self.good + "\n投稿日は2026年7月26日です。")["checks"]["d"], qa.FAIL)

    def test_empty_answer_fails_and_verdict_is_the_worst_check(self):
        self.assertEqual(self.verdict("")["verdict"], qa.FAIL)
        worst = self.verdict(self.good + f"\n{B} は {A} より古いです。", "Q3")
        self.assertEqual(worst["verdict"], qa.FAIL)
        self.assertTrue(any(r["check"] == "d" for r in worst["reasons"]))

    def test_check_never_writes(self):
        with mock.patch.object(Path, "write_text", side_effect=AssertionError("write")), \
                mock.patch.object(Path, "write_bytes", side_effect=AssertionError("write")):
            self.verdict(self.good)


class TestPlanOnRealNotes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.videos = qa.load_videos(ROOT)
        cls.plan = qa.plan_for_videos(cls.videos)

    def test_three_questions_for_each_of_the_31_notes(self):
        self.assertEqual((self.plan["note_count"], self.plan["question_count"]), (31, 93))
        ids = [q["id"] for q in self.plan["questions"]]
        self.assertEqual(len(ids), len(set(ids)))
        for vid in self.videos:
            self.assertEqual([q["id"] for q in self.plan["questions"] if q["video_id"] == vid], [f"{vid}-Q1", f"{vid}-Q2", f"{vid}-Q3"])
        self.assertIs(self.plan["files_modified"], False)

    def test_each_question_carries_its_expected_evidence(self):
        for q in self.plan["questions"]:
            e = q["expect"]
            self.assertTrue(q["question"].strip())
            self.assertEqual((e["transcript_id"], e["research_id"]), (f"youtube:{q['video_id']}:transcript", f"youtube:{q['video_id']}:research"))
            self.assertEqual(e["url"], f"https://www.youtube.com/watch?v={q['video_id']}")
            # 投稿日が研究ノートに無い動画もある（実データで4本）。その場合は None のまま渡し、日付ルールは掛けない
            self.assertIn("published_at", e)
            self.assertTrue(e["published_at"] is None or len(e["published_at"]) >= 10)
            if q["kind"] in ("CLAIM_TIME", "CHAPTER_TIME"):
                self.assertTrue(e["time_required"])
            if e["time_window"]:
                self.assertLess(e["time_window"][0], e["time_window"][1])
                self.assertEqual(e["time_window"][0], max(0, e["time_seconds"] - qa.WINDOW_MARGIN_SEC))
            if q["kind"] == "RELATED":
                self.assertTrue(e["related"])
                for r in e["related"]:
                    self.assertIn(r["relation"], qa.RELATION_WORDS | {"RESOLVES_BACKLOG": ()})
                    self.assertIn(r["video_id"], self.videos)
                    self.assertNotEqual(r["video_id"], q["video_id"])

    def test_the_golden_pair_expects_a_confirmed_complements_link_both_ways(self):
        for src, dst in (("pRfC1DILDEM", "u3ka_AAb8qE"), ("u3ka_AAb8qE", "pRfC1DILDEM")):
            q3 = next(q for q in self.plan["questions"] if q["id"] == f"{src}-Q3")
            rel = [r for r in q3["expect"]["related"] if r["video_id"] == dst]
            self.assertEqual([(r["relation"], r["status"]) for r in rel], [("COMPLEMENTS", "CONFIRMED")])

    def test_the_real_chapter_time_is_expected_for_u3ka(self):
        q2 = next(q for q in self.plan["questions"] if q["id"] == "u3ka_AAb8qE-Q2")
        self.assertEqual(q2["expect"]["time_seconds"], 496)           # 荷札の章 08:16〜09:08
        self.assertEqual(q2["expect"]["time_window"], [496 - qa.WINDOW_MARGIN_SEC, 548 + qa.WINDOW_MARGIN_SEC])

    def test_plan_is_deterministic_and_never_uses_transcript_text(self):
        self.assertEqual(self.plan, qa.plan_for_videos(qa.load_videos(ROOT)))
        src = (ROOT / "automation" / "gemini-notebook" / "qa_check.py").read_text(encoding="utf-8")
        for needle in ("get_fulltext", "list_sources", "notebooklm", "subprocess", "urlopen", "open(", "write_text", "write_bytes"):
            self.assertNotIn(needle, src, needle)

    def test_title_keys_tell_every_video_apart(self):
        keys = {v["video_id"]: v["title_key"] for v in self.videos.values()}
        for vid, key in keys.items():
            self.assertGreaterEqual(len(key), 8)
            for other, v in self.videos.items():
                if other != vid:
                    self.assertNotIn(key, v["title"], (vid, other))

    def test_answers_built_from_the_expectation_pass_and_broken_ones_do_not(self):
        for q in self.plan["questions"]:
            e, vid = q["expect"], q["video_id"]
            t = e["time_seconds"]
            url = e["url"] + (f"&t={t}s" if t is not None else "&t=10s")
            clock = qa._mmss(t if t is not None else 10)
            answer = (f"字幕原文（{e['transcript_id']}）の [{clock}] {url} が該当し、研究ノート（{e['research_id']}）でも確認できます。")
            if e["related"]:
                r = e["related"][0]
                answer += f"\n関連動画は {r['video_id']} で、{r['relation']} の関係です。"
            res = qa.check_answer(answer, q, self.videos)
            self.assertEqual(res["verdict"], qa.PASS, (q["id"], res["reasons"]))
            # 根拠を消す／URLを消す／関係を取り違える と、どれも PASS ではなくなる
            self.assertNotEqual(qa.check_answer(answer.replace(e["transcript_id"], "").replace(e["research_id"], "").replace(clock, "").replace(url, "x"), q, self.videos)["verdict"], qa.PASS)
            self.assertEqual(qa.check_answer(answer.replace(url, "どこか").replace(clock, ""), q, self.videos)["checks"]["b"], qa.FAIL)
            if e["related"]:
                wrong = "CONTRADICTS" if e["related"][0]["relation"] != "CONTRADICTS" else "EXTENDS"
                bad = answer.replace(e["related"][0]["relation"], wrong)
                self.assertEqual(qa.check_answer(bad, q, self.videos)["checks"]["c"], qa.FAIL, q["id"])


class TestCli(unittest.TestCase):
    def run_cli(self, argv, stdin=None):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            if stdin is not None:
                with mock.patch.object(sys, "stdin", io.StringIO(stdin)):
                    rc = qa.main(argv)
            else:
                rc = qa.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def test_plan_json_and_summary_and_single_video(self):
        rc, out, _ = self.run_cli(["plan", "--video-id", "u3ka_AAb8qE"])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out)["question_count"], 3)
        rc, out, _ = self.run_cli(["plan", "--summary"])
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("【質問回答の確認プラン"))
        self.assertIn("ノート 31本／質問 93問", out)
        self.assertIn("u3ka_AAb8qE-Q2", out)

    def test_check_reads_a_file_or_stdin_and_exit_code_follows_the_verdict(self):
        vid = "u3ka_AAb8qE"
        url = f"https://www.youtube.com/watch?v={vid}&t=496s"
        good = f"字幕原文（youtube:{vid}:transcript）の [00:08:16] {url} が該当。研究ノート（youtube:{vid}:research）も参照。"
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "answer.txt"
            f.write_text(good, encoding="utf-8")
            rc, out, _ = self.run_cli(["check", "--question-id", f"{vid}-Q2", "--answer", str(f)])
            self.assertEqual(rc, 0)
            self.assertIn("→ PASS", out)
        rc, out, _ = self.run_cli(["check", "--question-id", f"{vid}-Q2", "--json"], stdin="関係ない回答です")
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["verdict"], qa.FAIL)

    def test_unknown_question_id_is_an_error(self):
        for qid in ("nonexistent-Q1", "u3ka_AAb8qE-Q9"):
            rc, _, err = self.run_cli(["check", "--question-id", qid], stdin="x")
            self.assertEqual(rc, 2)
            self.assertIn(qid, err)

    def test_no_command_is_an_error_and_everything_is_read_only_and_offline(self):
        before = tree_hash()

        def blocked(*a, **k):
            raise AssertionError("network")

        with mock.patch.object(urllib.request, "urlopen", blocked), mock.patch.object(socket, "create_connection", blocked), \
                mock.patch.object(socket, "socket", blocked):
            self.run_cli(["plan", "--summary"])
            self.run_cli(["--selftest"])
            self.run_cli(["check", "--question-id", "u3ka_AAb8qE-Q1"], stdin="x")
            with self.assertRaises(SystemExit):
                self.run_cli([])
        self.assertEqual(before, tree_hash())


if __name__ == "__main__":
    unittest.main()
