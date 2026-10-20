#!/usr/bin/env python3
"""Tests for notebooklm_py_ingest.py (offline, fake client only)."""
import json
import socket
import sys
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "notebook_sources_20261020.json"
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
        self.fulltext_calls = []

    def auth_check_passive(self):
        self.auth_calls += 1
        return self.auth_ok

    def list_sources(self):
        return [{"id": s["id"], "type": s.get("type", ""), "title": s["title"]} for s in self.sources]

    def get_fulltext(self, source_id):
        self.fulltext_calls.append(source_id)
        return self.bodies.get(source_id, "")

    def add_text(self, title, text):
        self.add_calls.append((title, text))
        sid = f"new-{len(self.add_calls)}"
        if self.add_lands:
            self.sources.append({"id": sid, "type": "text", "title": title})
            self.bodies[sid] = self.mangle(text)
        if self.add_raises:
            raise TimeoutError("network timeout after send")
        return sid


YT_SOURCE = {"id": "yt-1", "type": "youtube", "title": TITLE, "body": "動画の文字起こし本文"}
TR_SOURCE = {"id": "tr-1", "type": "markdown", "title": ing.transcript_title(VID, TITLE)}
NOTE_SOURCE = {"id": "rn-1", "type": "markdown", "title": ing.research_note_title(VID, TITLE)}


def real_sources():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["sources"]


REAL_TITLES = {
    "pRfC1DILDEM": "【AI中級】RAGのその先。巨大な資料をAIで精度高く取り扱いたい。",
    "u3ka_AAb8qE": "AIが資料整理する新ルールOKFをサクッと理解する",
    "sodTFSuV4zY": "デスクツアーならぬソフトウェアツアー！AIエンジニアが仕事で使ってるアプリ・サービスを一式紹介",
    "YrTVpJ1ebUk": "2026年10月AI最新ニュースと3社比較",
}


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

    def test_transcript_without_cues_halts_instead_of_notebook_fulltext(self):
        """2026-10-20 ユーザー確定仕様で、Notebook内YouTube本文（時刻なし）へのフォールバックは廃止。
        旧テスト（フォールバックで登録できること）は意味が逆転したため、停止すること・書き込み0に期待値を更新。"""
        c = FakeClient([YT_SOURCE, NOTE_SOURCE])
        res = self.run_live(c, cues=None)
        self.assertEqual(res["status"], "TRANSCRIPT_TIMESTAMPS_UNAVAILABLE")
        self.assertEqual(c.add_calls, [])
        self.assertNotIn("yt-1", c.fulltext_calls)

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


class TestRealNotebookTitles(unittest.TestCase):
    """2026-10-20 の実Notebook一覧（id/type/titleのみ）での回帰テスト。"""

    def plan(self, vid, cues=CUES):
        c = FakeClient(real_sources())
        res = ing.run_ingest(c, vid, REAL_TITLES[vid], NOTE, cues=cues)
        self.assertEqual(c.add_calls, [])
        return res

    def test_pRfC1DILDEM_all_three_found_no_op(self):
        res = self.plan("pRfC1DILDEM")
        self.assertEqual(res["status"], "NO_OP")
        pre = res["precheck"]
        self.assertTrue(pre["youtube_source_id"].startswith("25c0f62e"))
        self.assertTrue(pre["transcript_source_id"].startswith("a32a70ec"))
        self.assertTrue(pre["research_note_source_id"].startswith("af697c8c"))

    def test_u3ka_AAb8qE_plans_transcript_only(self):
        # 2026-10-20 仕様で時刻なしフォールバックを廃止したため、時刻つきcueを渡す形に更新
        res = self.plan("u3ka_AAb8qE")
        self.assertEqual(res["status"], "DRY_RUN_PLAN")
        self.assertEqual(res["plan"], ["transcript"])
        self.assertTrue(res["precheck"]["research_note_source_id"].startswith("65b634f5"))
        self.assertTrue(res["precheck"]["youtube_source_id"].startswith("d1fef625"))
        self.assertEqual(res["transcript_acquisition_method"], ing.ACQ_TIMEDTEXT)

    def test_sodTFSuV4zY_plans_transcript_only_and_ignores_markdown_as_youtube(self):
        res = self.plan("sodTFSuV4zY")
        self.assertEqual(res["status"], "DRY_RUN_PLAN")
        self.assertEqual(res["plan"], ["transcript"])
        pre = res["precheck"]
        self.assertTrue(pre["research_note_source_id"].startswith("9d2e470f"))
        self.assertNotEqual(pre["youtube_source_id"], pre["research_note_source_id"])
        if pre["youtube_source_id"]:
            self.assertTrue(pre["youtube_source_id"].startswith("2a738296"))

    def test_YrTVpJ1ebUk_combined_note_detected(self):
        res = self.plan("YrTVpJ1ebUk")
        self.assertTrue(res["precheck"]["research_note_source_id"].startswith("cedf6421"))
        self.assertEqual(res["plan"], ["transcript"])

    def test_every_registry_research_note_is_detected(self):
        """registry.json に実IDが記録された研究ノートは、すべて検出されること（二重登録の防止）。"""
        reg = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))
        sources = real_sources()
        checked = 0
        for r in reg["records"]:
            sid = (r.get("notebook_sources") or {}).get("research_note")
            if not sid or not any(s["id"] == sid for s in sources):
                continue
            pre = ing.classify_sources(sources, r["video_id"], "", FakeClient(sources))
            self.assertEqual(pre["research_note_source_id"], sid, r["video_id"])
            checked += 1
        self.assertGreater(checked, 0)

    def test_new_titles_are_detected_by_classifier(self):
        srcs = [
            {"id": "a", "type": "text", "title": ing.transcript_title(VID, TITLE)},
            {"id": "b", "type": "text", "title": ing.research_note_title(VID, TITLE)},
        ]
        pre = ing.classify_sources(srcs, VID, TITLE)
        self.assertEqual((pre["transcript_source_id"], pre["research_note_source_id"]), ("a", "b"))

    def test_unknown_markdown_resolved_by_okf_tag_in_body(self):
        srcs = [{"id": "m1", "type": "markdown", "title": f"memo_{VID}.md",
                 "body": f'---\ntype: "TRANSCRIPT"\nlogical_id: "youtube:{VID}:transcript"\n---\n'}]
        c = FakeClient(srcs)
        pre = ing.classify_sources(c.list_sources(), VID, TITLE, c)
        self.assertEqual(pre["transcript_source_id"], "m1")
        self.assertFalse(pre["ambiguous"])

    def test_unresolvable_sources_halt_without_writes(self):
        srcs = [YT_SOURCE, {"id": "m1", "type": "markdown", "title": f"memo_{VID}.md", "body": "なにかのメモ"}]
        c = FakeClient(srcs)
        res = ing.run_ingest(c, VID, TITLE, NOTE, cues=CUES, live=True, notebook_id="nb-1")
        self.assertEqual(res["status"], "AMBIGUOUS_EXISTING_SOURCES")
        self.assertEqual(c.add_calls, [])

    def test_duplicate_notes_resolved_by_body_or_halt(self):
        n2 = {"id": "rn-2", "type": "markdown", "title": f"動画研究_{VID}_old.md",
              "body": f'logical_id: "youtube:{VID}:research"'}
        c = FakeClient([YT_SOURCE, dict(NOTE_SOURCE, body="本文に荷札なし"), n2, TR_SOURCE])
        res = ing.run_ingest(c, VID, TITLE, NOTE, cues=CUES, live=True, notebook_id="nb-1")
        self.assertEqual(res["status"], "NO_OP")
        self.assertEqual(res["precheck"]["research_note_source_id"], "rn-2")
        n2["body"] = "荷札なし"
        c = FakeClient([YT_SOURCE, NOTE_SOURCE, n2, TR_SOURCE])
        res = ing.run_ingest(c, VID, TITLE, NOTE, cues=CUES, live=True, notebook_id="nb-1")
        self.assertEqual(res["status"], "AMBIGUOUS_EXISTING_SOURCES")
        self.assertEqual(c.add_calls, [])

    def test_no_cues_and_no_youtube_source_halts(self):
        c = FakeClient([NOTE_SOURCE])
        res = ing.run_ingest(c, VID, TITLE, NOTE, cues=None, live=True, notebook_id="nb-1")
        # 2026-10-20 仕様：時刻つき字幕が無ければ（YouTubeソースの有無に関係なく）この状態で停止
        self.assertEqual(res["status"], "TRANSCRIPT_TIMESTAMPS_UNAVAILABLE")
        self.assertEqual(c.add_calls, [])


class TestCliAdapterAddText(unittest.TestCase):
    """T5: 実CLI（notebooklm-py 0.8.5）の `source add - --type text` に合わせたアダプタ。"""

    def fake_run(self, stdout, rc=0):
        calls = []

        def run(args, **kw):
            calls.append({"args": args, **kw})
            return ing.subprocess.CompletedProcess(args, rc, stdout=stdout, stderr="")

        return run, calls

    def test_add_text_args_stdin_and_nested_id(self):
        run, calls = self.fake_run(json.dumps({"source": {"id": "src-123", "title": "t"}}))
        c = ing.NotebookLmCliClient("nb-1", add_timeout=777)
        with mock.patch.object(ing.subprocess, "run", run):
            sid = c.add_text("【字幕原文】題 [abc]", "本文\n2行目")
        self.assertEqual(sid, "src-123")
        self.assertEqual(calls[0]["args"], [
            "notebooklm", "source", "add", "-", "--type", "text",
            "--title", "【字幕原文】題 [abc]", "--json", "--notebook", "nb-1",
        ])
        self.assertEqual(calls[0]["input"], "本文\n2行目")
        self.assertEqual(calls[0]["timeout"], 777)

    def test_add_text_default_timeout_is_long(self):
        run, calls = self.fake_run(json.dumps({"source": {"id": "x"}}))
        with mock.patch.object(ing.subprocess, "run", run):
            ing.NotebookLmCliClient("nb-1").add_text("t", "b")
        self.assertGreaterEqual(calls[0]["timeout"], 600)

    def test_add_text_flat_id_fallback(self):
        run, _ = self.fake_run(json.dumps({"id": "flat-1"}))
        with mock.patch.object(ing.subprocess, "run", run):
            self.assertEqual(ing.NotebookLmCliClient("nb-1").add_text("t", "b"), "flat-1")

    def test_add_text_without_id_returns_none(self):
        for out in (json.dumps({"source": {}}), "not json", json.dumps([1])):
            run, _ = self.fake_run(out)
            with mock.patch.object(ing.subprocess, "run", run):
                self.assertIsNone(ing.NotebookLmCliClient("nb-1").add_text("t", "b"))

    def test_add_without_id_goes_to_readback_not_resend(self):
        """CLIがIDを返さない → 再送せず一覧で確認（入っていれば CONFIRMED_BY_READBACK）。"""
        title = ing.transcript_title(VID, TITLE)
        state = {"listed": [
            {"id": "yt-1", "type": "youtube", "title": TITLE},
            {"id": "rn-1", "type": "markdown", "title": ing.research_note_title(VID, TITLE)},
        ]}
        add_calls = []

        def run(args, **kw):
            sub = args[1:3]
            if args[1] == "auth":
                return ing.subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            if sub == ["source", "list"]:
                return ing.subprocess.CompletedProcess(args, 0, stdout=json.dumps({"sources": state["listed"]}), stderr="")
            if sub == ["source", "add"]:
                add_calls.append(kw["input"])
                state["listed"] = state["listed"] + [{"id": "tr-new", "type": "text", "title": title}]
                state["body"] = kw["input"]
                return ing.subprocess.CompletedProcess(args, 0, stdout="{}", stderr="")
            if sub == ["source", "fulltext"]:
                body = state.get("body", "") if args[3] == "tr-new" else "動画の文字起こし本文"
                return ing.subprocess.CompletedProcess(args, 0, stdout=json.dumps({"content": body}), stderr="")
            raise AssertionError(args)

        c = ing.NotebookLmCliClient("nb-1")
        with mock.patch.object(ing.subprocess, "run", run):
            # 2026-10-20 仕様で時刻なしフォールバックを廃止したため cues を渡す形に更新
            res = ing.run_ingest(c, VID, TITLE, NOTE, cues=CUES, live=True, notebook_id="nb-1")
        self.assertEqual(len(add_calls), 1)
        self.assertEqual(res["writes"][0]["result"], "CONFIRMED_BY_READBACK")
        self.assertEqual(res["writes"][0]["source_id"], "tr-new")
        self.assertEqual(res["status"], "SUCCESS_2_SOURCE_OKF")

    def test_add_timeout_is_unknown_and_not_resent(self):
        add_calls = []

        def run(args, **kw):
            if args[1] == "auth":
                return ing.subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            if args[1:3] == ["source", "list"]:
                return ing.subprocess.CompletedProcess(args, 0, stdout=json.dumps({"sources": [
                    {"id": "rn-1", "type": "markdown", "title": ing.research_note_title(VID, TITLE)}]}), stderr="")
            if args[1:3] == ["source", "add"]:
                add_calls.append(1)
                raise ing.subprocess.TimeoutExpired(args, kw["timeout"])
            raise AssertionError(args)

        with mock.patch.object(ing.subprocess, "run", run):
            res = ing.run_ingest(ing.NotebookLmCliClient("nb-1"), VID, TITLE, NOTE, cues=CUES, live=True, notebook_id="nb-1")
        self.assertEqual(add_calls, [1])
        self.assertEqual(res["status"], "WRITE_RESULT_UNKNOWN")


class TestHealthCheck(unittest.TestCase):
    """T3: 読み取り専用のNotebook健康診断。"""

    def setUp(self):
        self.registry = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))

    def client(self, sources, **kw):
        c = FakeClient(sources, **kw)

        def no_write(*a, **k):
            raise AssertionError("health check must not write")

        c.add_text = no_write
        return c

    def test_auth_expired_stops_without_reading_or_writing(self):
        c = self.client(real_sources(), auth_ok=False)
        with mock.patch.object(c, "list_sources", side_effect=AssertionError("must not list")):
            rep = ing.health_check(c, self.registry)
        self.assertEqual(rep["status"], "AUTH_EXPIRED")
        self.assertIn("ログイン", rep["user_action"])
        self.assertEqual(c.add_calls, [])

    def test_cli_auth_expired_exits_nonzero(self):
        with mock.patch.object(ing.NotebookLmCliClient, "auth_check_passive", return_value=False), \
                mock.patch.object(ing.NotebookLmCliClient, "list_sources", side_effect=AssertionError), \
                mock.patch.object(ing.NotebookLmCliClient, "add_text", side_effect=AssertionError):
            rc = ing.main(["health", "--notebook-id", "nb-1"])
        self.assertNotEqual(rc, 0)

    def test_current_fixture_counts(self):
        rep = ing.health_check(self.client(real_sources()), self.registry)
        self.assertEqual(rep["registry_ids_missing_in_notebook_count"], 0)
        self.assertEqual(rep["notebook_sources_not_in_registry_count"], 0)
        self.assertEqual(rep["videos_without_transcript_okf_count"], 30)
        self.assertNotIn("pRfC1DILDEM", rep["videos_without_transcript_okf"])
        self.assertEqual(rep["status"], "OK")

    def test_one_id_removed_reports_one_missing(self):
        srcs = [s for s in real_sources() if not s["id"].startswith("65b634f5")]
        rep = ing.health_check(self.client(srcs), self.registry)
        self.assertEqual(rep["registry_ids_missing_in_notebook_count"], 1)
        self.assertEqual(rep["registry_ids_missing_in_notebook"][0]["video_id"], "u3ka_AAb8qE")
        self.assertEqual(rep["status"], "ATTENTION")

    def test_unregistered_note_in_notebook_is_reported(self):
        srcs = real_sources() + [{"id": "x-1", "type": "text", "title": "【研究ノート】新しい動画 [abcdefghijk]"}]
        rep = ing.health_check(self.client(srcs), self.registry)
        self.assertEqual(rep["notebook_sources_not_in_registry_count"], 1)
        self.assertEqual(rep["notebook_sources_not_in_registry"][0]["kind"], "research_note")

    def test_health_is_offline(self):
        def blocked(*a, **k):
            raise AssertionError("network call")

        with mock.patch.object(urllib.request, "urlopen", blocked), \
                mock.patch.object(socket, "create_connection", blocked), \
                mock.patch.object(ing.subprocess, "run", blocked):
            rep = ing.health_check(self.client(real_sources()), self.registry)
        self.assertEqual(rep["status"], "OK")


class TestUserConfirmedSpec20261020(unittest.TestCase):
    """T6: ロードマップv1.2「ユーザー確定仕様」（時刻リンク・投稿日時・URL単体ソース廃止）。"""

    def test_cue_line_has_time_link_with_truncated_seconds(self):
        cues = [(0.0, 1.0, "最初"), (496.9, 500.0, "荷札の話"), (3725.4, 3730.0, "1時間超え")]
        text = ing.build_transcript_text(VID, TITLE, cues, "2026-10-01")["text"]
        self.assertIn(f"- [00:00:00](https://www.youtube.com/watch?v={VID}&t=0s) 最初", text)
        self.assertIn(f"- [00:08:16](https://www.youtube.com/watch?v={VID}&t=496s) 荷札の話", text)
        self.assertIn(f"- [01:02:05](https://www.youtube.com/watch?v={VID}&t=3725s) 1時間超え", text)

    def test_cue_text_is_not_modified(self):
        raw = "えーと、Q&A は <b>ここ</b>  で…（笑）"
        text = ing.build_transcript_text(VID, TITLE, [(12.0, 13.0, raw)], None)["text"]
        self.assertIn(f"&t=12s) {raw}", text)

    def test_published_at_recorded_in_both_okfs(self):
        c = FakeClient([])
        res = ing.run_ingest(c, VID, TITLE, NOTE, cues=CUES, live=True, notebook_id="nb-1", published_at="2026-10-01")
        bodies = dict((t.split("】")[0], b) for t, b in c.add_calls)
        self.assertIn('published_at: "2026-10-01"', bodies["【字幕原文"])
        self.assertIn('published_at: "2026-10-01"', bodies["【研究ノート"])
        self.assertEqual(res["published_at"], "2026-10-01")

    def test_published_at_unknown_when_not_available(self):
        c = FakeClient([])
        ing.run_ingest(c, VID, TITLE, NOTE, cues=CUES, live=True, notebook_id="nb-1",
                       fetch_transcript=lambda vid: {"cues": [], "published_at": None})
        for _, body in c.add_calls:
            self.assertIn('published_at: "UNKNOWN"', body)

    def test_research_note_published_at_added_once_to_frontmatter(self):
        note = '---\ntype: "RESEARCH_NOTE"\n---\n# 本文\n'
        out = ing.ensure_published_at(note, "2026-10-01")
        self.assertTrue(out.startswith('---\ntype: "RESEARCH_NOTE"\npublished_at: "2026-10-01"\n---\n'))
        self.assertTrue(out.endswith("# 本文\n"))
        self.assertEqual(ing.ensure_published_at(out, "2027-01-01"), out)
        self.assertIn('published_at: "UNKNOWN"', ing.ensure_published_at("# 荷札なし", None))

    def test_no_cues_in_builder_marks_timestamps_missing(self):
        import notebook_auto_ingest as nai
        text = nai.build_transcript_okf_content(VID, f"https://www.youtube.com/watch?v={VID}", TITLE, raw_text="本文だけ")
        self.assertIn('transcript_status: "TIMESTAMPS_MISSING"', text)
        self.assertIn('published_at: "UNKNOWN"', text)

    def test_fetcher_failure_stops_with_zero_writes(self):
        c = FakeClient([YT_SOURCE, NOTE_SOURCE])
        res = ing.run_ingest(c, VID, TITLE, NOTE, cues=None, live=True, notebook_id="nb-1",
                             fetch_transcript=lambda vid: {"cues": [], "published_at": "2026-10-01"})
        self.assertEqual(res["status"], "TRANSCRIPT_TIMESTAMPS_UNAVAILABLE")
        self.assertEqual(c.add_calls, [])

    def fake_youtube_http(self, caption_xml, watch_html):
        """urlopen を偽のYouTube応答に差し替える（player JSON / 字幕XML / watchページ）。"""
        player = {"videoDetails": {"videoId": VID}, "captions": {"playerCaptionsTracklistRenderer": {
            "captionTracks": [{"baseUrl": "https://www.youtube.com/api/timedtext?v=x", "languageCode": "ja"}]}}}

        class Resp:
            def __init__(self, body):
                self.body = body.encode("utf-8")

            def read(self):
                return self.body

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def urlopen(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            if "youtubei/v1/player" in url:
                return Resp(json.dumps(player))
            if "timedtext" in url:
                return Resp(caption_xml)
            if "watch?v=" in url:
                return Resp(watch_html)
            raise AssertionError(url)

        return urlopen

    def test_fetch_youtube_transcript_with_fake_http(self):
        xml = '<timedtext><body><p t="0" d="1500">はじめまして</p><p t="496000" d="2000">荷札の話</p></body></timedtext>'
        html_page = '..."publishDate":"2026-10-01T09:00:00-07:00"...'
        with mock.patch.object(urllib.request, "urlopen", self.fake_youtube_http(xml, html_page)), \
                mock.patch.object(socket, "create_connection", side_effect=AssertionError("real network")):
            out = ing.fetch_youtube_transcript(VID)
        self.assertEqual(out["published_at"], "2026-10-01")
        self.assertEqual([round(c[0]) for c in out["cues"]], [0, 496])
        text = ing.build_transcript_text(VID, TITLE, out["cues"], out["published_at"])["text"]
        self.assertIn(f"&t=496s) 荷札の話", text)

    def test_fetch_youtube_transcript_without_captions_returns_empty(self):
        def urlopen(req, timeout=None):
            raise OSError("offline")

        with mock.patch.object(urllib.request, "urlopen", urlopen):
            out = ing.fetch_youtube_transcript(VID)
        self.assertEqual(out["cues"], [])
        self.assertIsNone(out["published_at"])

    def test_include_youtube_url_is_rejected(self):
        import auto_research_pipeline as arp
        import notebook_auto_ingest as nai
        for mod, argv in ((arp, ["https://www.youtube.com/watch?v=" + VID, "--include-youtube-url"]),
                          (nai, [VID, "--include-youtube-url"])):
            with mock.patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
                mod.main(argv)
            self.assertNotEqual(cm.exception.code, 0)
        with self.assertRaises(ValueError):
            arp.run_pipeline("https://www.youtube.com/watch?v=" + VID, include_youtube_url=True)
        with self.assertRaises(ValueError):
            arp.run_notebook_registration_only(VID, ROOT / "README.md", include_youtube_url=True)
        with self.assertRaises(ValueError):
            nai.ingest_and_verify_notebook(VID, "u", "t", ROOT / "README.md", mock_cdp=True, add_youtube_source=True)

    def test_youtube_url_source_add_is_always_disabled(self):
        import notebook_auto_ingest as nai
        res = nai.add_youtube_source_via_cdp(None, {}, VID, "https://www.youtube.com/watch?v=" + VID)
        self.assertFalse(res["success"])
        self.assertEqual(res["status"], "DISABLED_BY_SPEC")


if __name__ == "__main__":
    unittest.main()
