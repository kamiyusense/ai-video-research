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

    def test_transcript_without_cues_uses_notebook_fulltext(self):
        """2026-10-20 22:42 JST 相棒の方針転換で字幕全文は時刻なしが正になったため、Notebook内YouTube本文を
        字幕全文に使う（T6で「停止」に変えた期待値を、方針転換に合わせて「登録」に戻した）。"""
        c = FakeClient([YT_SOURCE, NOTE_SOURCE])
        res = self.run_live(c, cues=None)
        self.assertEqual(res["status"], "SUCCESS_2_SOURCE_OKF")
        self.assertIn("yt-1", c.fulltext_calls)
        self.assertEqual(res["transcript_acquisition_method"], ing.ACQ_NOTEBOOK_FULLTEXT)
        body = c.add_calls[0][1]
        self.assertIn("## 字幕全文 (取得全量・時刻なし)\n\n動画の文字起こし本文", body)
        self.assertIn(f'acquisition_method: "{ing.ACQ_NOTEBOOK_FULLTEXT}"', body)
        self.assertNotIn("&t=", body)

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
        # 22:42 方針転換後も、字幕本文がどこからも取れなければ書き込み0で停止（状態名を TRANSCRIPT_UNAVAILABLE に変更）
        self.assertEqual(res["status"], "TRANSCRIPT_UNAVAILABLE")
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

    @staticmethod
    def with_published(sources, without=()):
        """偽の本文を付ける：荷札に published_at あり（without に挙げたIDだけ無し）。"""
        out = []
        for s in sources:
            body = 'okf_version: "0.2"\n' + ("" if s["id"].startswith(tuple(without)) else 'published_at: "2026-07-25"\n')
            out.append(dict(s, body=body))
        return out

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
        # T10: 投稿日時の確認が加わったため、偽の本文（published_at入り）を付けて従来の件数とOKを確かめる
        rep = ing.health_check(self.client(self.with_published(real_sources())), self.registry)
        self.assertEqual(rep["registry_ids_missing_in_notebook_count"], 0)
        self.assertEqual(rep["notebook_sources_not_in_registry_count"], 0)
        self.assertEqual(rep["videos_without_transcript_okf_count"], 30)
        self.assertNotIn("pRfC1DILDEM", rep["videos_without_transcript_okf"])
        self.assertEqual(rep["sources_without_published_at_count"], 0)
        self.assertEqual(rep["status"], "OK")

    def test_transcript_without_published_at_is_attention(self):
        """T10: a32a70ec（pRfC1DILDEM の字幕全文OKF）のように荷札に投稿日時が無ければ ATTENTION。"""
        rep = ing.health_check(self.client(self.with_published(real_sources(), without=("a32a70ec",))), self.registry)
        self.assertEqual(rep["status"], "ATTENTION")
        self.assertEqual(rep["sources_without_published_at_count"], 1)
        hit = rep["sources_without_published_at"][0]
        self.assertTrue(hit["source_id"].startswith("a32a70ec"))
        self.assertEqual((hit["kind"], hit["published_at"]), ("transcript_okf", "MISSING"))

    def test_published_at_unknown_is_attention(self):
        srcs = self.with_published(real_sources())
        for s in srcs:
            if s["id"].startswith("af697c8c"):
                s["body"] = 'published_at: "UNKNOWN"\n'
        rep = ing.health_check(self.client(srcs), self.registry)
        self.assertEqual([(h["kind"], h["published_at"]) for h in rep["sources_without_published_at"]],
                         [("research_note", "UNKNOWN")])
        self.assertEqual(rep["status"], "ATTENTION")

    def test_published_at_of_tolerates_notebook_formatting(self):
        self.assertEqual(ing.published_at_of('---\npublished_at: "2026-07-25"\n---'), "2026-07-25")
        self.assertEqual(ing.published_at_of("published at: 2026-07-25"), "2026-07-25")
        self.assertEqual(ing.published_at_of('published_at: ""'), "UNKNOWN")
        self.assertIsNone(ing.published_at_of("- **投稿日時**: 2026-07-25"))

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
            rep = ing.health_check(self.client(self.with_published(real_sources())), self.registry)
        self.assertEqual(rep["status"], "OK")


class TestUserConfirmedSpec20261020(unittest.TestCase):
    """T6: ロードマップv1.2「ユーザー確定仕様」（時刻リンク・投稿日時・URL単体ソース廃止）。"""

    def test_default_transcript_is_untimed_paragraphs(self):
        """T10（22:42 方針転換）: 既定は時刻なし。約1分ごと（発話の切れ目）で段落を分け、発話はそのまま空白でつなぐ。"""
        cues = [(0.0, 1.0, "最初"), (1.2, 2.0, "続き"), (496.9, 500.0, "荷札の話"), (3725.4, 3730.0, "1時間超え")]
        text = ing.build_transcript_text(VID, TITLE, cues, "2026-10-01")["text"]
        self.assertNotIn("&t=", text)
        self.assertIn("## 字幕全文 (取得全量・時刻なし)\n\n最初 続き\n\n荷札の話\n\n1時間超え", text)
        for line in ('published_at: "2026-10-01"', f'logical_id: "youtube:{VID}:transcript"', "cue_count: 4",
                     'acquisition_method: "YOUTUBE_TIMEDTEXT_API"', 'transcript_format: "UNTIMED_PARAGRAPHS"',
                     f'resource: "https://www.youtube.com/watch?v={VID}"'):
            self.assertIn(line, text)

    def test_paragraphs_are_about_one_minute_split_at_utterance_boundaries(self):
        """T10 検品1周目の直し：AGENTS.md と相棒PC作成済み15本の形式（約60秒ごと）に合わせる。"""
        import notebook_auto_ingest as nai
        cues = [(float(t), float(t) + 8.0, f"発話{t}") for t in range(0, 140, 10)]  # 0,10,…,130秒
        paras = nai.cues_to_paragraphs(cues)
        self.assertEqual([p.split(" ")[0] for p in paras], ["発話0", "発話60", "発話120"])
        self.assertEqual([len(p.split(" ")) for p in paras], [6, 6, 2])
        self.assertEqual(" ".join(paras), " ".join(c[2] for c in cues))  # 発話は欠けず、順番も変わらない
        # 沈黙が短くても1分未満なら同じ段落（旧既定の3秒の間では分けない）
        self.assertEqual(len(nai.cues_to_paragraphs([(0.0, 1.0, "a"), (30.0, 31.0, "b"), (59.9, 60.0, "c")])), 1)

    def test_long_paragraph_is_split(self):
        import notebook_auto_ingest as nai
        cues = [(float(i), float(i) + 0.5, "あ" * 100) for i in range(5)]
        paras = nai.cues_to_paragraphs(cues, max_chars=300)
        self.assertEqual([p.count("あ") for p in paras], [300, 200])
        self.assertEqual("".join(paras).replace(" ", ""), "あ" * 500)

    def test_timestamped_option_keeps_time_links(self):
        """時刻つき出力は timestamped=True を明示したときだけ（T6の形式のまま）。"""
        import notebook_auto_ingest as nai
        cues = [(0.0, 1.0, "最初"), (496.9, 500.0, "荷札の話"), (3725.4, 3730.0, "1時間超え")]
        text = nai.build_transcript_okf_content(VID, f"https://www.youtube.com/watch?v={VID}", TITLE, cues=cues,
                                                published_at="2026-10-01", timestamped=True)
        self.assertIn('transcript_format: "TIMESTAMPED_CUES"', text)
        self.assertIn(f"- [00:00:00](https://www.youtube.com/watch?v={VID}&t=0s) 最初", text)
        self.assertIn(f"- [00:08:16](https://www.youtube.com/watch?v={VID}&t=496s) 荷札の話", text)
        self.assertIn(f"- [01:02:05](https://www.youtube.com/watch?v={VID}&t=3725s) 1時間超え", text)

    def test_cue_text_is_not_modified(self):
        raw = "えーと、Q&A は <b>ここ</b>  で…（笑）"
        text = ing.build_transcript_text(VID, TITLE, [(12.0, 13.0, raw)], None)["text"]
        self.assertTrue(text.endswith(f"## 字幕全文 (取得全量・時刻なし)\n\n{raw.strip()}"))

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

    def test_no_cues_in_builder_uses_raw_text_without_halting(self):
        """T10: cueが無くても本文があれば時刻なしの正式な字幕全文にする（TIMESTAMPS_MISSING は廃止）。"""
        import notebook_auto_ingest as nai
        text = nai.build_transcript_okf_content(VID, f"https://www.youtube.com/watch?v={VID}", TITLE, raw_text="本文だけ")
        self.assertNotIn("TIMESTAMPS_MISSING", text)
        self.assertIn('transcript_status: "UNVERIFIED"', text)
        self.assertIn('transcript_format: "RAW_TEXT"', text)
        self.assertIn('published_at: "UNKNOWN"', text)
        self.assertTrue(text.endswith("## 字幕全文 (取得全量・時刻なし)\n\n本文だけ"))

    def test_fetcher_failure_stops_with_zero_writes(self):
        # T10: Notebook内YouTube本文が使えるようになったため、YouTubeソースが無い状況で「どこからも取れない」を確かめる
        c = FakeClient([NOTE_SOURCE])
        res = ing.run_ingest(c, VID, TITLE, NOTE, cues=None, live=True, notebook_id="nb-1",
                             fetch_transcript=lambda vid: {"cues": [], "published_at": "2026-10-01"})
        self.assertEqual(res["status"], "TRANSCRIPT_UNAVAILABLE")
        self.assertEqual(c.add_calls, [])

    def test_youtube_captions_first_then_notebook_fulltext_as_last_resort(self):
        """T10 検品2周目：取得元の順は 渡されたcue → YouTube字幕 → Notebook内YouTube本文（読みにくい版なので最後の手段）。"""
        c = FakeClient([YT_SOURCE, NOTE_SOURCE])
        res = ing.run_ingest(c, VID, TITLE, NOTE, cues=None, live=True, notebook_id="nb-1",
                             fetch_transcript=lambda vid: {"cues": [(0.0, 1.0, "YouTube字幕の発話")], "published_at": "2026-07-25",
                                                           "acquisition_method": ing.ACQ_TRANSCRIPT_API})
        self.assertEqual(res["status"], "SUCCESS_2_SOURCE_OKF")
        body = c.add_calls[0][1]
        self.assertIn("YouTube字幕の発話", body)
        self.assertNotIn("動画の文字起こし本文", body)
        self.assertNotIn("yt-1", c.fulltext_calls)  # YouTube字幕が取れたらNotebook本文は読まない
        self.assertIn(f'acquisition_method: "{ing.ACQ_TRANSCRIPT_API}"', body)
        self.assertIn('published_at: "2026-07-25"', body)

    def test_notebook_fulltext_used_only_when_youtube_captions_fail(self):
        c = FakeClient([YT_SOURCE, NOTE_SOURCE])
        res = ing.run_ingest(c, VID, TITLE, NOTE, cues=None, live=True, notebook_id="nb-1",
                             fetch_transcript=lambda vid: {"cues": [], "published_at": "2026-07-25"})
        self.assertEqual(res["status"], "SUCCESS_2_SOURCE_OKF")
        self.assertEqual(res["transcript_acquisition_method"], ing.ACQ_NOTEBOOK_FULLTEXT)
        body = c.add_calls[0][1]
        self.assertIn("動画の文字起こし本文", body)
        self.assertIn(f'acquisition_method: "{ing.ACQ_NOTEBOOK_FULLTEXT}"', body)
        self.assertIn('published_at: "2026-07-25"', body)

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
            # youtube-transcript-api を使えない状態にして、既存timedtext経路を偽HTTPで通す
            out = ing.fetch_youtube_transcript(VID, sources=(
                (ing.ACQ_TRANSCRIPT_API, mock.Mock(side_effect=ImportError)),
                (ing.ACQ_TIMEDTEXT, ing.fetch_cues_timedtext),
            ))
        self.assertEqual(out["acquisition_method"], ing.ACQ_TIMEDTEXT)
        self.assertIn(ing.ACQ_TRANSCRIPT_API, out["errors"])
        self.assertEqual(out["published_at"], "2026-10-01")
        self.assertEqual([round(c[0]) for c in out["cues"]], [0, 496])
        text = ing.build_transcript_text(VID, TITLE, out["cues"], out["published_at"])["text"]
        self.assertTrue(text.endswith("はじめまして\n\n荷札の話"))  # T10: 時刻なしの段落本文

    def test_fetch_youtube_transcript_without_captions_returns_empty(self):
        def urlopen(req, timeout=None):
            raise OSError("offline")

        fake_api = mock.MagicMock()
        fake_api.YouTubeTranscriptApi.return_value.fetch.side_effect = OSError("offline")
        with mock.patch.object(urllib.request, "urlopen", urlopen), \
                mock.patch.dict(sys.modules, {"youtube_transcript_api": fake_api}):
            out = ing.fetch_youtube_transcript(VID)
        self.assertEqual(out["cues"], [])
        self.assertIsNone(out["published_at"])

    def test_transcript_api_source_is_used_first(self):
        """youtube-transcript-api（偽モジュール）が取れればそれを使い、荷札の取得方法にも記録する。"""
        snippet = mock.Mock(start=496.4, duration=2.0, text="荷札の話")
        fake_api = mock.MagicMock()
        fake_api.YouTubeTranscriptApi.return_value.fetch.return_value = [snippet]
        timedtext = mock.Mock(side_effect=AssertionError("timedtext must not be called"))
        with mock.patch.dict(sys.modules, {"youtube_transcript_api": fake_api}), \
                mock.patch.object(urllib.request, "urlopen", side_effect=OSError("offline")):
            out = ing.fetch_youtube_transcript(VID, sources=(
                (ing.ACQ_TRANSCRIPT_API, ing.fetch_cues_transcript_api),
                (ing.ACQ_TIMEDTEXT, timedtext),
            ))
        self.assertEqual(out["acquisition_method"], ing.ACQ_TRANSCRIPT_API)
        self.assertEqual(out["cues"], [(496.4, 498.4, "荷札の話")])
        fake_api.YouTubeTranscriptApi.return_value.fetch.assert_called_once_with(VID, languages=["ja", "en"])
        c = FakeClient([NOTE_SOURCE])
        res = ing.run_ingest(c, VID, TITLE, NOTE, live=True, notebook_id="nb-1", fetch_transcript=lambda v: out)
        self.assertEqual(res["transcript_acquisition_method"], ing.ACQ_TRANSCRIPT_API)
        body = c.add_calls[0][1]
        self.assertIn(f'acquisition_method: "{ing.ACQ_TRANSCRIPT_API}"', body)
        self.assertTrue(body.endswith("## 字幕全文 (取得全量・時刻なし)\n\n荷札の話"))  # T10: 時刻なし

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

    def test_drive_sync_transcript_records_published_at(self):
        import tempfile
        import notebook_auto_ingest as nai
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "note.md"
            note.write_text("# note\n", encoding="utf-8")
            res = nai.sync_to_drive_notebook_sources(
                VID, f"https://www.youtube.com/watch?v={VID}", TITLE, note,
                target_dir=Path(tmp) / "drive", cues=[{"start": 496.0, "text": "荷札の話"}], published_at="2026-10-01",
            )
            tr = next(Path(f["path"]) for f in res["synced_files"] if f["path"].endswith("_transcript_okf.md"))
            body = tr.read_text(encoding="utf-8")
        self.assertIn('published_at: "2026-10-01"', body)
        self.assertTrue(body.endswith("荷札の話"))  # T10: 時刻なしの段落本文
        self.assertNotIn("&t=", body)

    def test_youtube_url_source_add_is_always_disabled(self):
        import notebook_auto_ingest as nai
        res = nai.add_youtube_source_via_cdp(None, {}, VID, "https://www.youtube.com/watch?v=" + VID)
        self.assertFalse(res["success"])
        self.assertEqual(res["status"], "DISABLED_BY_SPEC")


class TestLinkifyTimestamps(unittest.TestCase):
    """T7: 研究ノートの根拠時刻を再生位置リンクにする（R3）。"""

    def setUp(self):
        import receipt_to_research
        self.lk = receipt_to_research.linkify_timestamps

    def test_mmss_and_hhmmss_become_links_with_seconds(self):
        out = self.lk("要点は08:16と1:02:05", VID)
        self.assertEqual(out, f"要点は[08:16](https://www.youtube.com/watch?v={VID}&t=496s)と"
                              f"[1:02:05](https://www.youtube.com/watch?v={VID}&t=3725s)")

    def test_existing_links_urls_code_frontmatter_and_comments_untouched(self):
        text = (
            '---\ntime: "12:34"\n---\n'
            f"- [08:16](https://www.youtube.com/watch?v={VID}&t=496s) 既存\n"
            "- URL https://example.com/a?t=10:20 と `01:02`\n"
            "<!-- 09:00 -->\n```\n05:00\n```\n"
        )
        self.assertEqual(self.lk(text, VID), text)

    def test_non_time_patterns_and_idempotence(self):
        self.assertEqual(self.lk("比率16:9、番号12:345", VID), "比率16:9、番号12:345")
        once = self.lk("# 03:15 の話\n本文 10:00", VID)
        self.assertEqual(self.lk(once, VID), once)

    def test_notebook_copy_is_linkified_but_github_file_is_not(self):
        note_path = ROOT / "research" / "2026-10-18-pRfC1DILDEM-gemini-notebook.md"
        original = note_path.read_text(encoding="utf-8")
        c = FakeClient([TR_SOURCE])
        ing.run_ingest(c, VID, TITLE, "根拠は 08:16 にある", cues=CUES, live=True, notebook_id="nb-1")
        body = c.add_calls[0][1]
        self.assertIn(f"[08:16](https://www.youtube.com/watch?v={VID}&t=496s)", body)
        self.assertEqual(note_path.read_text(encoding="utf-8"), original)

    def test_drive_sync_linkifies_note_and_writes_no_youtube_source_file(self):
        import tempfile
        import notebook_auto_ingest as nai
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "note.md"
            note.write_text("根拠 08:16\n", encoding="utf-8")
            target = Path(tmp) / "drive"
            res = nai.sync_to_drive_notebook_sources(VID, f"https://www.youtube.com/watch?v={VID}", TITLE, note,
                                                     target_dir=target, cues=CUES)
            names = sorted(p.name for p in target.iterdir())
            md = (target / f"{VID}_research_note.md").read_text(encoding="utf-8")
            self.assertEqual(note.read_text(encoding="utf-8"), "根拠 08:16\n")
        self.assertEqual(names, [f"{VID}_research_note.md", f"{VID}_transcript_okf.md"])
        self.assertEqual(len(res["synced_files"]), 2)
        self.assertIn(f"[08:16](https://www.youtube.com/watch?v={VID}&t=496s)", md)

    def test_python_and_gas_linkify_match(self):
        import subprocess as sp
        samples = [
            "# 08:16 の話\n- [00:10](https://x/y) と https://e.com/?t=10:20 と `01:02`\n- 1:02:05 と 16:9",
            '---\nt: "12:34"\n---\n本文 03:15\n```\n05:00\n```\n<!-- 09:00 --> 59:59',
        ]
        gas = (AUTO_DIR / "cloud_relay_gas.js").as_posix()
        script = ("const g=require(%s);const s=%s;process.stdout.write(JSON.stringify(s.map(t=>g.linkifyTimestamps(t,%s))));"
                  % (json.dumps(gas), json.dumps(samples), json.dumps(VID)))
        js = json.loads(sp.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)
        self.assertEqual(js, [self.lk(t, VID) for t in samples])


if __name__ == "__main__":
    unittest.main()


class TestPipelineNotebookLmPyBackend(unittest.TestCase):
    """T8: URLを貼るだけの通し運転（auto_research_pipeline）に notebooklm-py 登録をつなぐ。"""

    def setUp(self):
        import auto_research_pipeline as arp
        self.arp = arp
        self.net_calls = []

        def _blocked(*args, **kwargs):
            self.net_calls.append(args[:1])
            raise AssertionError(f"テスト中に外部通信が呼ばれました: {args[:1]}")

        for target, name in ((urllib.request, "urlopen"), (socket, "create_connection")):
            p = mock.patch.object(target, name, _blocked)
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(lambda: self.assertEqual(self.net_calls, []))

    def fetch_ok(self, vid):
        return {"cues": CUES, "published_at": "2026-10-01", "acquisition_method": ing.ACQ_TRANSCRIPT_API}

    def note_path(self):
        import tempfile
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = Path(d.name) / "note.md"
        p.write_text(NOTE, encoding="utf-8")
        return p

    def test_new_url_plans_transcript_and_research_note_without_writes(self):
        c = FakeClient([YT_SOURCE])
        res = self.arp.run_notebooklm_py_step(VID, TITLE, self.note_path(), notebook_id="nb-1",
                                              client=c, fetch_transcript=self.fetch_ok)
        self.assertEqual(res["status"], "DRY_RUN_PLAN")
        self.assertEqual(sorted(p["kind"] if isinstance(p, dict) else p for p in res["plan"]),
                         ["research_note", "transcript"])
        self.assertEqual(c.add_calls, [])
        self.assertEqual(res["new_source_ids"], [])

    def test_live_step_returns_status_writes_and_new_source_ids(self):
        c = FakeClient([YT_SOURCE])
        res = self.arp.run_notebooklm_py_step(VID, TITLE, self.note_path(), notebook_id="nb-1", live=True,
                                              client=c, fetch_transcript=self.fetch_ok)
        self.assertEqual(res["status"], "SUCCESS_2_SOURCE_OKF")
        self.assertEqual(res["new_source_ids"], ["new-1", "new-2"])
        self.assertEqual(len(res["writes"]), 2)

    def run_resume(self, client, fetch=None, **kw):
        return self.arp.run_pipeline("https://www.youtube.com/watch?v=pRfC1DILDEM",
                                     notebook_backend="notebooklm-py", notebook_client=client,
                                     fetch_transcript=fetch or self.fetch_ok, **kw)

    def test_already_complete_video_is_no_op(self):
        c = FakeClient(real_sources())
        res = self.run_resume(c, notebook_id="nb-1", notebook_live=True)
        self.assertEqual(res["notebook_ingest"]["status"], "NO_OP")
        self.assertEqual(res["status"], "ALREADY_REGISTERED")
        self.assertEqual(res["notebook_backend"], "notebooklm-py")
        self.assertTrue(res["is_2_source_okf_verified"])
        self.assertEqual(c.add_calls, [])

    def test_auth_expired_halts_with_zero_writes(self):
        c = FakeClient(real_sources(), auth_ok=False)
        res = self.run_resume(c, notebook_id="nb-1", notebook_live=True)
        self.assertEqual(res["status"], "AUTH_EXPIRED_HALT")
        self.assertFalse(res["is_2_source_okf_verified"])
        self.assertEqual(c.add_calls, [])

    def test_captions_unavailable_halts_with_zero_writes(self):
        c = FakeClient([YT_SOURCE])
        res = self.arp.run_pipeline("https://www.youtube.com/watch?v=u3ka_AAb8qE",
                                    notebook_backend="notebooklm-py", notebook_client=c,
                                    notebook_id="nb-1", notebook_live=True,
                                    fetch_transcript=lambda vid: {"cues": [], "published_at": None})
        self.assertEqual(res["status"], "TRANSCRIPT_UNAVAILABLE")
        self.assertEqual(c.add_calls, [])

    def test_live_without_notebook_id_halts(self):
        c = FakeClient([])
        res = self.run_resume(c, notebook_live=True)
        self.assertEqual(res["status"], "LIVE_REQUIRES_NOTEBOOK_ID")
        self.assertEqual(res["notebook_ingest"]["writes"], [])
        self.assertEqual(c.add_calls, [])
        with mock.patch.object(self.arp, "run_pipeline", side_effect=AssertionError("呼ばれてはいけない")), \
                mock.patch("sys.stderr"):
            with self.assertRaises(SystemExit) as cm:
                self.arp.main(["https://www.youtube.com/watch?v=pRfC1DILDEM",
                               "--notebook-backend", "notebooklm-py", "--live"])
            self.assertNotEqual(cm.exception.code, 0)
            with self.assertRaises(SystemExit):
                self.arp.main(["https://www.youtube.com/watch?v=pRfC1DILDEM", "--live",
                               "--notebook-id", "nb-1"])

    def test_live_requires_notebooklm_py_backend_in_api(self):
        with self.assertRaises(ValueError):
            self.arp.run_pipeline("https://www.youtube.com/watch?v=pRfC1DILDEM",
                                  notebook_live=True, notebook_id="nb-1")

    def test_cli_passes_backend_options_to_pipeline(self):
        seen = {}

        def fake_run(*a, **kw):
            seen.update(kw)
            return {"status": "DRY_RUN_PLAN"}

        with mock.patch.object(self.arp, "run_pipeline", fake_run):
            code = self.arp.main(["https://www.youtube.com/watch?v=pRfC1DILDEM",
                                  "--notebook-backend", "notebooklm-py", "--notebook-id", "nb-1"])
        self.assertEqual(code, 0)
        self.assertEqual((seen["notebook_backend"], seen["notebook_id"], seen["notebook_live"]),
                         ("notebooklm-py", "nb-1", False))

    def test_research_note_frontmatter_has_published_at_and_transcript_logical_id(self):
        import receipt_to_research as rtr
        base = {"video_id": "abcdefghijk", "title": "t", "summary_ja": "0:05 から本題", "claims": [],
                "url": "https://www.youtube.com/watch?v=abcdefghijk", "source_scope": "x",
                "notebook_source_id": "UNKNOWN", "notebook_readback": "UNKNOWN", "changes": []}
        for pub, want in (("2026-10-01", '"2026-10-01"'), (None, '"UNKNOWN"')):
            v = dict(base, published_at=pub)
            md = rtr.render(v, "2026-10-20")
            front = md.split("\n---\n", 1)[0]
            self.assertIn(f"published_at: {want}", front)
            self.assertIn('transcript_logical_id: "youtube:abcdefghijk:transcript"', front)


class TestPipelineEndToEndMocked(unittest.TestCase):
    """T9: run_pipeline を手順3〜8まで通す（字幕取得・研究ノート保存・Git・NotebookClient はすべて偽物）。"""

    E2E_VID = "e2eTestVid1"
    E2E_TITLE = "OKFで作るAI知識ベースの設計（E2E）"
    E2E_CUES = [(0.0, 2.0, "こんにちは"), (65.4, 70.0, "OKFは荷札です"), (3725.9, 3730.0, "まとめ")]

    def setUp(self):
        import tempfile
        from datetime import date
        import auto_research_pipeline as arp
        import receipt_to_research as rtr
        self.arp, self.rtr, self.today = arp, rtr, date.today().isoformat()
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.tmp = Path(d.name)
        self.net_calls, self.saved_notes, self.git_calls = [], [], []

        def _blocked(*args, **kwargs):
            self.net_calls.append(args[:1])
            raise AssertionError(f"テスト中に外部通信が呼ばれました: {args[:1]}")

        def _forbidden(name):
            def f(*a, **kw):
                raise AssertionError(f"{name} は呼ばれてはいけない")
            return f

        def fake_save(data, root, **kw):  # 手順4「GitHub保存」の代わり：研究ノートを一時フォルダへ書くだけ
            path = Path(root) / "research" / f"{self.today}-{self.E2E_VID}-gemini-notebook.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rtr.render(data["videos"][0], self.today), encoding="utf-8")
            self.saved_notes.append(path)
            return {"new_records": 1}, [path]

        def fake_catalog(root, write_path):
            Path(write_path).parent.mkdir(parents=True, exist_ok=True)
            Path(write_path).write_text("{}\n", encoding="utf-8")
            return {"total_records": 1, "total_video_records": 1}, None

        def fake_git_out(cmd, **kw):
            self.git_calls.append(cmd)
            return {"branch": arp.DEFAULT_TARGET_BRANCH, "rev-parse": "0" * 40}.get(cmd[1], "")

        player = {"videoDetails": {"videoId": self.E2E_VID, "title": self.E2E_TITLE,
                                   "author": "テスト投稿者", "lengthSeconds": "3730"}}
        self.player_cues = list(self.E2E_CUES)
        patches = [
            (urllib.request, "urlopen", _blocked),
            (socket, "create_connection", _blocked),
            (arp, "ROOT", self.tmp),
            (arp, "SCRATCH_DIR", self.tmp / "scratch"),
            (arp, "verify_target_branch_early", lambda **kw: None),
            (arp.intake_url, "check_url_intake", lambda url, root=None: {"status": "NEW"}),
            (arp.verify_timestamps, "fetch_player", lambda vid: player),
            (arp.verify_timestamps, "fetch_watch_publish_date", lambda vid: "2026-10-01"),
            (arp, "fetch_actual_captions",
             lambda pd: ("ACQUIRED" if self.player_cues else "NOT_ACQUIRED", list(self.player_cues), "ja")),
            (arp, "analyze_with_gemini_api", _forbidden("Gemini API")),
            (arp.receipt_to_research, "process_receipt_data", fake_save),
            (arp.query_research, "build_video_knowledge_catalog", fake_catalog),
            (arp.query_research, "answer_question", lambda q, root=None: {"step2_matched_records": []}),
            (arp.subprocess, "check_output", fake_git_out),
            (arp.subprocess, "check_call", lambda cmd, **kw: self.git_calls.append(cmd) or 0),
            (arp.notebook_auto_ingest, "ingest_and_verify_notebook", _forbidden("CDP登録")),
            (arp.notebook_auto_ingest, "add_youtube_source_via_cdp", _forbidden("URL単体ソース登録")),
        ]
        for target, name, value in patches:
            p = mock.patch.object(target, name, value)
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(lambda: self.assertEqual(self.net_calls, []))

    def fetch_none(self, vid):
        return {"cues": [], "published_at": None}

    def run_e2e(self, client, fetch=None, **kw):
        kw.setdefault("notebook_id", "nb-1")
        kw.setdefault("notebook_live", True)
        res = self.arp.run_pipeline(f"https://www.youtube.com/watch?v={self.E2E_VID}", no_push=True,
                                    notebook_backend="notebooklm-py", notebook_client=client,
                                    fetch_transcript=fetch or self.fetch_none, **kw)
        self.assertFalse([c for c in self.git_calls if "push" in c], "git push は呼ばれてはいけない")
        return res

    def yt(self):
        return {"id": "yt-e2e", "type": "youtube", "title": self.E2E_TITLE}

    def test_adds_only_transcript_and_research_note_okf(self):
        c = FakeClient([self.yt()])
        res = self.run_e2e(c)
        nb = res["notebook_ingest"]
        self.assertEqual(nb["status"], "SUCCESS_2_SOURCE_OKF")
        self.assertEqual(len(c.add_calls), 2)
        self.assertEqual(sorted(t.split("】")[0] + "】" for t, _ in c.add_calls), ["【字幕原文】", "【研究ノート】"])
        self.assertEqual([s for s in c.sources if s["type"] == "youtube"], [self.yt()])  # URL単体の追加0件
        self.assertEqual(nb["new_source_ids"], ["new-1", "new-2"])
        self.assertTrue(res["is_2_source_okf_verified"])
        self.assertEqual(res["notebook_backend"], "notebooklm-py")
        self.assertEqual(len(self.saved_notes), 1)

    def test_both_bodies_have_youtube_url_and_published_at(self):
        c = FakeClient([self.yt()])
        self.run_e2e(c)
        for title, body in c.add_calls:
            self.assertIn(f"https://www.youtube.com/watch?v={self.E2E_VID}", body, title)
            self.assertIn('published_at: "2026-10-01"', body, title)

    def test_transcript_body_is_untimed_paragraphs(self):
        """T9(c) を T10（22:42 方針転換：字幕全文は時刻なしが正）に合わせて書き換え。時刻は研究ノート側のリンクで示す。"""
        c = FakeClient([self.yt()])
        self.run_e2e(c)
        body = next(b for t, b in c.add_calls if t.startswith("【字幕原文】"))
        self.assertNotIn("&t=", body)
        self.assertTrue(body.endswith("## 字幕全文 (取得全量・時刻なし)\n\nこんにちは\n\nOKFは荷札です\n\nまとめ"))
        self.assertIn("cue_count: 3", body)

    def test_already_registered_in_notebook_is_no_op(self):
        tr = {"id": "tr-e2e", "type": "markdown", "title": ing.transcript_title(self.E2E_VID, self.E2E_TITLE)}
        rn = {"id": "rn-e2e", "type": "markdown", "title": ing.research_note_title(self.E2E_VID, self.E2E_TITLE)}
        c = FakeClient([self.yt(), tr, rn])
        res = self.run_e2e(c)
        self.assertEqual(res["notebook_ingest"]["status"], "NO_OP")
        self.assertEqual(c.add_calls, [])
        self.assertTrue(res["is_2_source_okf_verified"])

    def test_untimed_notebook_text_is_registered(self):
        """T9(e) を T10 に合わせて書き換え：時刻つき字幕が無くても、Notebook内YouTube本文（時刻なし）で登録する。"""
        self.player_cues = []
        c = FakeClient([dict(self.yt(), body="ノートブック内の字幕本文")])
        res = self.run_e2e(c)
        self.assertEqual(res["notebook_ingest"]["status"], "SUCCESS_2_SOURCE_OKF")
        body = next(b for t, b in c.add_calls if t.startswith("【字幕原文】"))
        self.assertIn("ノートブック内の字幕本文", body)
        self.assertIn(f'acquisition_method: "{ing.ACQ_NOTEBOOK_FULLTEXT}"', body)
        self.assertIn('published_at: "2026-10-01"', body)

    def test_no_transcript_text_anywhere_stops_without_registration(self):
        self.player_cues = []  # YouTube側・取得関数・Notebook内本文とも0件
        c = FakeClient([self.yt()])
        res = self.run_e2e(c)
        self.assertEqual(res["notebook_ingest"]["status"], "TRANSCRIPT_UNAVAILABLE")
        self.assertEqual(c.add_calls, [])
        self.assertFalse(res["is_2_source_okf_verified"])
        self.assertNotIn(res["status"], ("SUCCESS_2_SOURCE_OKF", "SUCCESS"))


class TestPipelineDryRunNotebookPlan(unittest.TestCase):
    """T9: dry-run でも手順8の notebooklm-py 計画（タイトル・logical_id）を返し、書き込み系は呼ばない。"""

    URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    VID = "dQw4w9WgXcQ"

    def setUp(self):
        import auto_research_pipeline as arp
        self.arp = arp
        self.net_calls = []

        def _blocked(*args, **kwargs):
            self.net_calls.append(args[:1])
            raise AssertionError(f"dry-run中に外部通信が呼ばれました: {args[:1]}")

        for target, name in ((urllib.request, "urlopen"), (socket, "create_connection")):
            p = mock.patch.object(target, name, _blocked)
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(lambda: self.assertEqual(self.net_calls, []))
        scratch = ROOT / "scratch" / f"receipt_{self.VID}.json"
        self.assertFalse(scratch.exists())
        self.addCleanup(lambda: self.assertFalse(scratch.exists()))

    def write_guard(self, client):
        def no_write(*a, **kw):
            raise AssertionError("dry-run中に add_text が呼ばれました")
        client.add_text = no_write
        return client

    def test_dry_run_returns_plan_with_titles_and_logical_ids(self):
        c = self.write_guard(FakeClient([]))
        fetch = lambda vid: {"cues": CUES, "published_at": "2026-10-01"}
        # T10: 棚を読む dry-run では題名・投稿日時を読み取りで取り、計画の題名を本物にする（偽の取得関数）
        meta = lambda vid: {"player_data": {"videoDetails": {"videoId": vid, "title": "本物の動画タイトル"},
                                            "captions": {"must": "be dropped"}},
                            "published_at": "2026-07-25"}
        res = self.arp.run_pipeline(self.URL, dry_run=True, notebook_backend="notebooklm-py",
                                    notebook_id="nb-1", notebook_client=c, fetch_transcript=fetch,
                                    fetch_video_meta=meta)
        self.assertEqual(res["status"], "DRY_RUN_PLAN")
        nb = res["notebook_ingest"]
        self.assertEqual(nb["writes"], [])
        self.assertEqual(nb["published_at"], "2026-07-25")
        self.assertNotIn("captions", str(res["receipt"].get("raw_cues")))
        title = "本物の動画タイトル"
        self.assertEqual(nb["plan_details"], [
            {"kind": "transcript", "title": ing.transcript_title(self.VID, title),
             "logical_id": f"youtube:{self.VID}:transcript"},
            {"kind": "research_note", "title": ing.research_note_title(self.VID, title),
             "logical_id": f"youtube:{self.VID}:research"},
        ])

    def test_dry_run_title_fetch_failure_keeps_placeholder_with_note(self):
        c = self.write_guard(FakeClient([]))

        def broken(vid):
            raise OSError("offline")

        res = self.arp.run_pipeline(self.URL, dry_run=True, notebook_backend="notebooklm-py", notebook_id="nb-1",
                                    notebook_client=c, fetch_video_meta=broken,
                                    fetch_transcript=lambda vid: {"cues": CUES, "published_at": None})
        self.assertEqual(res["status"], "DRY_RUN_PLAN")
        nb = res["notebook_ingest"]
        self.assertEqual(nb["plan_details"][0]["title"], ing.transcript_title(self.VID, f"YouTube Video {self.VID}"))
        self.assertTrue(any("仮名" in n for n in nb["notes"]))

    def test_dry_run_without_notebook_id_is_offline_plan(self):
        res = self.arp.run_pipeline(self.URL, dry_run=True, notebook_backend="notebooklm-py",
                                    fetch_video_meta=lambda vid: self.fail("棚を読まない計画で題名取得は不要"),
                                    fetch_transcript=lambda vid: self.fail("棚を読まない計画で字幕取得は不要"))
        self.assertEqual(res["status"], "DRY_RUN_PLAN_OFFLINE")
        self.assertEqual([p["logical_id"] for p in res["notebook_ingest"]["plan_details"]],
                         [f"youtube:{self.VID}:transcript", f"youtube:{self.VID}:research"])

    def test_dry_run_ignores_live_flag_and_never_writes(self):
        c = self.write_guard(FakeClient([]))
        res = self.arp.run_pipeline(self.URL, dry_run=True, notebook_backend="notebooklm-py",
                                    notebook_id="nb-1", notebook_live=True, notebook_client=c,
                                    fetch_video_meta=lambda vid: {},
                                    fetch_transcript=lambda vid: {"cues": CUES, "published_at": None})
        self.assertEqual(res["status"], "DRY_RUN_PLAN")
        self.assertFalse(res["notebook_ingest"]["live"])

    def test_cdp_dry_run_unchanged(self):
        res = self.arp.run_pipeline(self.URL, dry_run=True)
        self.assertEqual(res["status"], "DRY_RUN_COMPLETE")
        self.assertNotIn("notebook_ingest", res)


class TestUrlSourceMigrationPlan(unittest.TestCase):
    """T10: URL単体ソース15件の移行計画（読み取りのみ。削除の実行コードは無い）。"""

    def client(self, sources, **kw):
        c = FakeClient(sources, **kw)

        def no_write(*a, **k):
            raise AssertionError("migration plan must not write")

        c.add_text = no_write
        return c

    def plan(self, sources=None, **kw):
        return ing.plan_url_source_migration(self.client(sources or real_sources(), **kw), ROOT / "research")

    def test_all_15_url_sources_are_planned_with_video_ids(self):
        rep = self.plan()
        self.assertEqual(rep["status"], "DRY_RUN_MIGRATION_PLAN")
        self.assertEqual(rep["url_source_count"], 15)
        self.assertEqual(rep["video_id_unknown_count"], 0)
        self.assertFalse(rep["deletion_executed"])
        by_vid = {i["video_id"]: i for i in rep["items"]}
        for vid, title in REAL_TITLES.items():
            if vid in by_vid:
                self.assertEqual(by_vid[vid]["youtube_title"], title)
        self.assertIn("t22FELAl-BM", by_vid)  # IDに「-」を含む動画もGitHub研究ノートから特定できる
        self.assertIn("u3ka_AAb8qE", by_vid)  # GitHubに題が無くてもNotebookの「【研究ノート】題 [ID]」から特定

    def test_each_item_lists_existing_order_additions_and_deletion_after_readback(self):
        rep = self.plan()
        u3ka = next(i for i in rep["items"] if i["video_id"] == "u3ka_AAb8qE")
        self.assertIsNone(u3ka["existing"]["transcript_okf"])
        self.assertTrue(u3ka["existing"]["research_note_okf"].startswith("65b634f5"))
        self.assertEqual([o["method"] for o in u3ka["transcript_source_order"]],
                         [ing.ACQ_TRANSCRIPT_API, ing.ACQ_TIMEDTEXT, ing.ACQ_NOTEBOOK_FULLTEXT])
        self.assertEqual(u3ka["to_add"], [{"kind": "transcript", "title": ing.transcript_title("u3ka_AAb8qE", u3ka["youtube_title"]),
                                           "logical_id": "youtube:u3ka_AAb8qE:transcript"}])
        self.assertEqual(u3ka["status"], "ADD_THEN_DELETE")
        self.assertEqual(u3ka["delete_after_readback"], [u3ka["youtube_source_id"]])
        self.assertTrue(any("読み戻し一致を確かめた後だけ" in n for n in u3ka["notes"]))

    def test_existing_transcript_without_published_at_needs_approval(self):
        rep = self.plan()
        rag = next(i for i in rep["items"] if i["video_id"] == "pRfC1DILDEM")
        self.assertTrue(rag["existing"]["transcript_okf"].startswith("a32a70ec"))
        self.assertEqual(rag["existing"]["transcript_published_at"], "MISSING")
        self.assertEqual(rag["to_add"], [])
        self.assertEqual([p["kind"] for p in rag["to_add_pending_approval"]], ["transcript"])
        self.assertTrue(rag["replace_pending_approval"][0].startswith("a32a70ec"))
        self.assertEqual(rag["status"], "ADD_THEN_DELETE")

    def test_transcript_with_published_at_is_ready_and_fulltext_probe_is_reported(self):
        srcs = real_sources()
        for s in srcs:
            if s["id"].startswith("a32a70ec"):
                s["body"] = 'published_at: "2026-07-25"\n'
            if s["id"].startswith("25c0f62e"):  # RAG動画のYouTubeソース
                s["body"] = "本文" * 10
        rep = self.plan(srcs)
        rag = next(i for i in rep["items"] if i["video_id"] == "pRfC1DILDEM")
        self.assertEqual(rag["status"], "READY_TO_DELETE_URL_SOURCE")
        self.assertEqual(rag["delete_after_readback"], ["25c0f62e-99aa-48bc-9486-357a350c76f5"])
        self.assertEqual(rag["transcript_source_order"][-1]["chars"], 20)
        self.assertTrue(rag["transcript_source_order"][-1]["available"])

    def test_unknown_video_id_is_not_scheduled_for_deletion(self):
        srcs = real_sources() + [{"id": "yt-zz", "type": "youtube", "title": "どこにも記録の無い動画"}]
        rep = self.plan(srcs)
        unk = next(i for i in rep["items"] if i["youtube_source_id"] == "yt-zz")
        self.assertEqual((unk["status"], unk["video_id"], unk["delete_after_readback"]), ("VIDEO_ID_UNKNOWN", "UNKNOWN", []))
        self.assertEqual(rep["delete_after_readback_count"], 15)

    def test_auth_expired_reads_nothing(self):
        c = self.client(real_sources(), auth_ok=False)
        with mock.patch.object(c, "list_sources", side_effect=AssertionError("must not list")):
            rep = ing.plan_url_source_migration(c, ROOT / "research")
        self.assertEqual(rep["status"], "AUTH_EXPIRED")

    def test_no_delete_code_and_cli_is_read_only(self):
        self.assertFalse(any("delete" in n.lower() or "remove" in n.lower() for n in dir(ing.NotebookLmCliClient)))
        self.assertFalse(any("delete" in str(v) for v in ing.NotebookLmCliClient.COMMANDS.values()))
        fake = self.client(real_sources())
        with mock.patch.object(ing, "NotebookLmCliClient", return_value=fake), mock.patch("sys.stdout"):
            rc = ing.main(["migrate-plan", "--notebook-id", "nb-1"])
        self.assertEqual(rc, 0)
