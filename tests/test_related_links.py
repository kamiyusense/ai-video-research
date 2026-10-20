#!/usr/bin/env python3
"""Tests for related_links.py (R6: 関連動画リンクの検査・候補生成・関連索引OKF。オフライン・読み取りのみ)."""
import hashlib
import json
import socket
import sys
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "automation" / "gemini-notebook"))
import related_links as rl  # noqa: E402


def doc(vid, title, published="2026-08-01", related=None, pieces=None):
    return {
        "video_id": vid, "title": title, "research_path": f"research/{vid}.md", "published_at": published,
        "related_records": related or [],
        "pieces": pieces or [("題名", title)],
    }


def rec(target, relation="COMPLEMENTS", status="CANDIDATE", note="関係の理由", evidence="12:34 の言及"):
    return {"target_id": target, "relation": relation, "status": status, "note": note, "evidence": evidence}


def corpus_of(*docs):
    return {d["video_id"]: d for d in docs}


A, B, C = "AAAAAAAAAAA", "BBBBBBBBBBB", "CCCCCCCCCCC"


class TestValidator(unittest.TestCase):
    def check(self, corpus):
        return rl.validate_related_records(corpus, ROOT)

    def errors(self, rep):
        return [i["errors"] for i in rep["items"]]

    def test_valid_confirmed_pair_with_backlink(self):
        c = corpus_of(doc(A, "a", related=[rec(f"youtube:{B}:research", status="CONFIRMED")]),
                      doc(B, "b", related=[rec(f"youtube:{A}:research", status="CONFIRMED", evidence="https://example.com/doc")]))
        rep = self.check(c)
        self.assertEqual(rep["status"], "OK")
        self.assertEqual(self.errors(rep), [[], []])
        self.assertEqual(rep["confirmed_valid_pairs"], [(f"youtube:{A}:research", f"youtube:{B}:research")])
        self.assertEqual(rep["missing_backlink_count"], 0)

    def test_each_rule_is_reported(self):
        c = corpus_of(
            doc(A, "a", related=[
                rec(f"youtube:{A}:research"),                              # 自己リンク
                rec("youtube:ZZZZZZZZZZZ:research"),                       # 宛先なし
                rec(f"youtube:{B}:research", relation="RELATED"),          # 関係ラベル不正
                rec(f"youtube:{B}:research", status="MAYBE"),              # status不正
                rec(f"youtube:{B}:research", note=""),                     # note無し
                rec(f"youtube:{B}:research", evidence="UNKNOWN"),          # evidence無し
                rec(f"youtube:{B}:research", status="CONFIRMED", evidence="雰囲気が似ている"),  # 時刻もURLも無いCONFIRMED
                rec("proposal:P999"),                                      # 存在しない提案
                rec("proposal:P006"),                                      # 存在する提案
            ]),
            doc(B, "b"),
        )
        rep = self.check(c)
        self.assertEqual(self.errors(rep), [
            ["SELF_LINK"], ["TARGET_NOT_FOUND"], ["BAD_RELATION"], ["BAD_STATUS"], ["NOTE_MISSING"],
            ["EVIDENCE_MISSING"], ["CONFIRMED_WITHOUT_TIME_OR_URL"], ["TARGET_NOT_FOUND"], [],
        ])
        self.assertEqual(rep["status"], "ATTENTION")
        self.assertEqual(rep["error_record_count"], 8)

    def test_missing_backlink_is_reported_but_not_an_error(self):
        c = corpus_of(doc(A, "a", related=[rec(f"youtube:{B}:research")]), doc(B, "b"))
        rep = self.check(c)
        self.assertEqual(rep["status"], "OK")
        self.assertEqual(rep["missing_backlink_count"], 1)
        self.assertIs(rep["items"][0]["backlink_present"], False)
        self.assertEqual(rep["confirmed_valid_pairs"], [])

    def test_both_target_id_forms_are_accepted(self):
        c = corpus_of(doc(A, "a", related=[rec(f"youtube:{B}")]), doc(B, "b"))
        self.assertEqual(self.check(c)["status"], "OK")

    def test_existing_rag_okf_pair_passes_on_the_real_notes(self):
        rep = self.check(rl.load_corpus(ROOT))
        pair = (f"youtube:pRfC1DILDEM:research", f"youtube:u3ka_AAb8qE:research")
        self.assertIn(pair, rep["confirmed_valid_pairs"])
        mine = [i for i in rep["items"] if {i["source"], i["target_id"]} == set(pair)]
        self.assertEqual(len(mine), 2)
        for i in mine:
            self.assertEqual((i["errors"], i["status"], i["relation"], i["backlink_present"]), ([], "CONFIRMED", "COMPLEMENTS", True))
        self.assertEqual(rep["confirmed_count"], 2)

    def test_real_notes_known_problems_are_visible(self):
        rep = self.check(rl.load_corpus(ROOT))
        self.assertEqual(rep["note_count"], 31)
        self.assertGreater(rep["error_counts"].get("EVIDENCE_MISSING", 0), 0)  # evidence が無い既存候補が多い
        self.assertEqual(rep["error_counts"].get("SELF_LINK"), 2)               # ZjUJ-35acaU / BStkW1HTfmk の自己リンク


class TestCandidates(unittest.TestCase):
    def setUp(self):
        self.src = doc(A, "OKFの荷札", pieces=[
            ("題名", "OKFの荷札とYAMLフロントマター"), ("章", "荷札のメタデータ原則"), ("タグ", "ナレッジフォーマット"),
        ])
        self.close = doc(B, "荷札の運用", "2026-07-01", pieces=[
            ("題名", "荷札のメタデータ運用"), ("章", "荷札のメタデータ原則を現場へ"), ("タグ", "ナレッジフォーマット"),
        ])
        self.noise = [doc(f"N{i:010d}", f"無関係{i}", pieces=[("題名", f"料理のレシピ{i}")]) for i in range(8)]

    def corpus(self):
        return corpus_of(self.src, self.close, *self.noise)

    def test_overlap_yields_candidate_with_evidence_and_never_confirmed(self):
        out = rl.infer_candidates(self.src, self.corpus())
        self.assertEqual([c["target_id"] for c in out], [f"youtube:{B}:research"])
        c = out[0]
        self.assertEqual((c["status"], c["relation"]), ("CANDIDATE", "COMPLEMENTS"))
        self.assertIn("荷札", c["evidence"])
        self.assertIn("本ノート:", c["evidence"])
        self.assertIn("相手:", c["evidence"])
        self.assertTrue(c["note"].startswith("自動推定の候補（未確認）"))

    def test_self_link_is_excluded_and_limit_applies(self):
        many = [doc(f"M{i:010d}", f"荷札{i}", pieces=[("題名", "荷札のメタデータ原則とフロントマター運用"), ("章", "ナレッジフォーマット")])
                for i in range(9)]
        filler = [doc(f"F{i:010d}", f"f{i}", pieces=[("題名", f"料理のレシピ{i}")]) for i in range(30)]
        corpus = corpus_of(self.src, *many, *filler)
        out = rl.infer_candidates(self.src, corpus, limit=3)
        self.assertEqual(len(out), 3)
        self.assertNotIn(f"youtube:{A}:research", [c["target_id"] for c in out])
        # 自分自身のコピーが台帳にあっても自己リンクにならない
        self.assertNotIn(f"youtube:{A}:research", [c["target_id"] for c in rl.infer_candidates(self.src, corpus_of(self.src, self.close))])

    def test_no_overlap_means_no_candidate(self):
        lone = doc("L0000000000", "料理", pieces=[("題名", "完全に別の話題のスープ")])
        self.assertEqual(rl.infer_candidates(lone, self.corpus()), [])

    def test_words_found_in_most_notes_are_not_evidence(self):
        common = [doc(f"K{i:010d}", f"共通{i}", pieces=[("題名", f"荷札と標準化{i}")]) for i in range(10)]
        src = doc(A, "x", pieces=[("題名", "荷札と標準化の話"), ("章", "標準化")])
        out = rl.infer_candidates(src, corpus_of(src, *common))
        self.assertEqual(out, [])

    def test_updates_direction_follows_published_at_and_needs_update_wording(self):
        new = doc(A, "新機能", "2026-09-01", pieces=[("題名", "荷札のメタデータ運用の新機能アップデート"), ("章", "荷札のメタデータ原則"), ("タグ", "ナレッジフォーマット")])
        old = doc(B, "旧", "2026-07-01", pieces=[("題名", "荷札のメタデータ運用"), ("章", "荷札のメタデータ原則"), ("タグ", "ナレッジフォーマット")])
        pad = self.noise
        self.assertEqual(rl.infer_candidates(new, corpus_of(new, old, *pad))[0]["relation"], "UPDATES")
        self.assertIn("2026-09-01 → 2026-07-01", rl.infer_candidates(new, corpus_of(new, old, *pad))[0]["evidence"])
        # 古い側から新しい側へは UPDATES にしない
        self.assertEqual(rl.infer_candidates(old, corpus_of(new, old, *pad))[0]["relation"], "COMPLEMENTS")
        # 日付が分からなければ UPDATES にしない
        new["published_at"] = None
        self.assertEqual(rl.infer_candidates(new, corpus_of(new, old, *pad))[0]["relation"], "COMPLEMENTS")

    def test_whole_registry_dry_run_is_read_only_and_never_confirms(self):
        paths = sorted((ROOT / "research").glob("*.md")) + [ROOT / "registry.json"]
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

        def blocked(*a, **k):
            raise AssertionError("network call")

        with mock.patch.object(urllib.request, "urlopen", blocked), mock.patch.object(socket, "create_connection", blocked):
            corpus = rl.load_corpus(ROOT)
            rep = rl.candidates_for_corpus(corpus)
            wide = rl.candidates_for_corpus(corpus, limit=10)
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
        self.assertFalse(rep["files_modified"])
        self.assertEqual(rep["note_count"], 31)
        self.assertGreater(rep["candidate_count"], 31)
        for v in rep["videos"]:
            self.assertLessEqual(len(v["candidates"]), rl.DEFAULT_CANDIDATE_LIMIT)
            for c in v["candidates"]:
                self.assertEqual(c["status"], "CANDIDATE")
                self.assertNotEqual(target := rl.target_video_id(c["target_id"]), v["video_id"], target)
                self.assertTrue(c["evidence"].startswith("共通語:"))
        # 既存の確認済みペアは候補にも出て、荷札の関係・statusをそのまま見せる
        rag = next(v for v in wide["videos"] if v["video_id"] == "pRfC1DILDEM")  # 上位5件には入らないので、広めの上限で見る
        pair = next(c for c in rag["candidates"] if c["target_id"] == "youtube:u3ka_AAb8qE:research")
        self.assertEqual((pair["already_in_note"], pair["note_status"], pair["relation"]), (True, "CONFIRMED", "COMPLEMENTS"))


class TestRelatedIndexOkf(unittest.TestCase):
    def build(self, **kw):
        c = corpus_of(
            doc(A, "新しい動画", "2026-09-01", related=[rec(f"youtube:{B}:research", "UPDATES", "CANDIDATE", "仕様が変わった")]),
            doc(B, "古い動画", "2026-07-01", related=[rec(f"youtube:{A}:research", "COMPLEMENTS", "CONFIRMED", "補い合う", "08:16 の言及")]),
            doc(C, "日付不明", None, related=[rec("youtube:ZZZZZZZZZZZ:research")]),
        )
        return c, rl.build_related_index_okf(c, ROOT, generated_at="2026-10-20T00:00:00Z", **kw)

    def test_frontmatter_and_counts(self):
        _, idx = self.build()
        text = idx["text"]
        for line in ('type: "RELATED_INDEX"', 'logical_id: "index:related"', 'generated_at: "2026-10-20T00:00:00Z"',
                     "video_count: 3", "link_count: 2", "confirmed_link_count: 1", "candidate_link_count: 1", "excluded_invalid_count: 1"):
            self.assertIn(line, text)
        self.assertEqual(idx["logical_id"], "index:related")
        self.assertIn("ID: index:related", text)  # Notebookの読み戻しで荷札が消えても見える1行

    def test_each_video_lists_published_at_targets_sources_relation_status_and_reason(self):
        _, idx = self.build()
        text = idx["text"]
        self.assertIn(f"## 新しい動画 [{A}]", text)
        self.assertIn("- 投稿日時: 2026-09-01", text)
        self.assertIn(f"  - → youtube:{B}:research（UPDATES・CANDIDATE）仕様が変わった", text)
        self.assertIn(f"  - ← youtube:{B}:research（COMPLEMENTS・CONFIRMED）補い合う", text.split(f"## 新しい動画 [{A}]")[1].split("## ")[0])
        self.assertIn("- 投稿日時: UNKNOWN", text)
        self.assertNotIn("ZZZZZZZZZZZ", text)  # 検査を通らない関係は載せない

    def test_newest_video_first_and_unknown_date_last(self):
        _, idx = self.build()
        heads = [l for l in idx["text"].splitlines() if l.startswith("## ")]
        self.assertEqual([h.split("[")[1].rstrip("]") for h in heads], [A, B, C])

    def test_auto_candidates_are_marked_not_registered(self):
        c = corpus_of(
            doc(A, "a", pieces=[("題名", "荷札のメタデータ運用"), ("章", "荷札のメタデータ原則"), ("タグ", "ナレッジフォーマット")]),
            doc(B, "b", pieces=[("題名", "荷札のメタデータ原則を現場へ"), ("章", "荷札のメタデータ運用"), ("タグ", "ナレッジフォーマット")]),
            *[doc(f"N{i:010d}", f"n{i}", pieces=[("題名", f"料理のレシピ{i}")]) for i in range(8)],
        )
        plain = rl.build_related_index_okf(c, ROOT, generated_at="g")
        self.assertEqual(plain["link_count"], 0)
        withc = rl.build_related_index_okf(c, ROOT, generated_at="g", include_auto_candidates=True)
        self.assertGreater(withc["link_count"], 0)
        self.assertIn("（自動推定・未登録）", withc["text"])

    def test_replacement_plan_adds_reads_back_then_deletes_only_after_readback_and_writes_nothing(self):
        _, idx = self.build()

        class Client:
            def __init__(self, auth=True):
                self.auth, self.calls = auth, []

            def auth_check_passive(self):
                return self.auth

            def list_sources(self):
                return [{"id": "old-1", "type": "markdown", "title": "【関連索引】AI技術研究室 関連動画リンク一覧"},
                        {"id": "x", "type": "markdown", "title": "【研究ノート】別 [AAAAAAAAAAA]"}]

            def add_text(self, *a):
                raise AssertionError("must not write")

            def delete(self, *a):
                raise AssertionError("must not delete")

        plan = rl.plan_related_index_replacement(Client(), idx)
        self.assertEqual(plan["status"], "DRY_RUN_REPLACEMENT_PLAN")
        self.assertEqual(plan["existing_index_source_ids"], ["old-1"])
        self.assertEqual([s["action"] for s in plan["steps"]], ["ADD_NEW_VERSION", "READBACK_MATCH", "DELETE_OLD_VERSION_AFTER_READBACK"])
        self.assertEqual(plan["steps"][2]["source_ids"], ["old-1"])
        self.assertFalse(plan["writes_executed"] or plan["deletion_executed"])
        self.assertEqual(rl.plan_related_index_replacement(Client(auth=False), idx)["status"], "AUTH_EXPIRED")
        offline = rl.plan_related_index_replacement(None, idx)
        self.assertEqual(offline["existing_index_source_ids"], "UNKNOWN")

    def test_module_has_no_write_or_delete_code(self):
        src = (ROOT / "automation" / "gemini-notebook" / "related_links.py").read_text(encoding="utf-8")
        for needle in ("write_text", "add_text(", ".unlink(", "os.remove", "rmtree", "open(", "subprocess"):
            self.assertNotIn(needle, src, needle)

    def test_cli_runs_on_real_registry_without_changing_files(self):
        import io
        import contextlib
        before = hashlib.sha256((ROOT / "registry.json").read_bytes()).hexdigest()
        for argv in (["validate"], ["candidates", "--video-id", "u3ka_AAb8qE"], ["index", "--with-candidates"]):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(rl.main(argv), 0)
            out = json.loads(buf.getvalue())
            self.assertIsInstance(out, dict)
        self.assertEqual(before, hashlib.sha256((ROOT / "registry.json").read_bytes()).hexdigest())


class TestRepairPlan(unittest.TestCase):
    """検証に通らない related_records の削除予定・置換候補を差分として出すだけ（ファイルは書き換えない）。"""

    def corpus(self):
        shared = [("題名", "NotebookLM と Claude の連携"), ("章", "NotebookLM のソース整理と連携手順"),
                  ("タグ", "NotebookLM"), ("タグ", "連携手順"), ("主張", "ソース整理の自動化")]
        return corpus_of(
            doc(A, "a", pieces=shared, related=[
                rec(f"youtube:{A}"),                                   # 自己リンク
                rec(f"youtube:{B}", evidence=""),                      # 根拠なし（置換候補と同じ宛先）
                rec(f"youtube:{C}:research", status="CONFIRMED", evidence="12:34"),   # 合格のCONFIRMED（温存）
            ]),
            doc(B, "b", pieces=shared, related=[rec(f"youtube:{A}:research")]),
            doc(C, "c", pieces=[("題名", "別の話題")], related=[rec(f"youtube:{A}:research", status="CONFIRMED", evidence="01:02")]),
            *[doc(f"N{i:010d}", f"n{i}", pieces=[("題名", f"料理のレシピ{i}")]) for i in range(12)],
        )

    def test_removes_only_invalid_records_and_keeps_valid_ones(self):
        plan = rl.repair_plan_for_corpus(self.corpus(), ROOT, limit=3)
        self.assertEqual(plan["status"], "DRY_RUN_REPAIR_PLAN")
        self.assertIs(plan["files_modified"], False)
        self.assertEqual([v["video_id"] for v in plan["videos"]], [A])  # B・C・無関係なノートは不合格なし
        v = plan["videos"][0]
        self.assertEqual([(r["target_id"], r["reasons"], r["action"]) for r in v["remove"]], [
            (f"youtube:{A}", ["SELF_LINK"], "DELETE_PLANNED"),
            (f"youtube:{B}", ["EVIDENCE_MISSING"], "DELETE_PLANNED"),
        ])
        self.assertEqual([k["target_id"] for k in v["keep"]], [f"youtube:{C}:research"])
        self.assertEqual(plan["delete_planned_count"], 2)

    def test_replacements_are_candidate_with_evidence_and_never_self(self):
        v = rl.repair_plan_for_corpus(self.corpus(), ROOT, limit=3)["videos"][0]
        self.assertTrue(v["replace_candidates"])
        for c in v["replace_candidates"]:
            self.assertEqual(c["status"], "CANDIDATE")
            self.assertTrue(c["evidence"].startswith("共通語:"))
            self.assertNotEqual(rl.target_video_id(c["target_id"]), A)
            self.assertNotEqual(rl.target_video_id(c["target_id"]), C)   # 温存した宛先は重ねない
        same = [c for c in v["replace_candidates"] if c["same_target_as_removed"]]
        self.assertEqual([rl.target_video_id(c["target_id"]) for c in same], [B])
        self.assertIn("- youtube:" + B, v["diff"])
        self.assertIn("+ youtube:" + B + ":research", v["diff"])
        self.assertIn("= youtube:" + C + ":research", v["diff"])

    def test_confirmed_invalid_record_goes_to_a_human_not_auto_delete(self):
        c = corpus_of(doc(A, "a", related=[rec(f"youtube:{B}:research", status="CONFIRMED", evidence="雰囲気が似ている")]), doc(B, "b"))
        plan = rl.repair_plan_for_corpus(c, ROOT)
        r = plan["videos"][0]["remove"][0]
        self.assertEqual((r["action"], r["reasons"]), ("NEEDS_HUMAN_CONFIRMED", ["CONFIRMED_WITHOUT_TIME_OR_URL"]))
        self.assertEqual((plan["delete_planned_count"], plan["needs_human_count"]), (0, 1))

    def test_valid_confirmed_pair_is_protected_even_when_a_sibling_record_is_bad(self):
        c = corpus_of(
            doc(A, "a", related=[rec(f"youtube:{B}:research", status="CONFIRMED", evidence="https://example.com/x"),
                                 rec(f"youtube:{C}:research", evidence="")]),
            doc(B, "b", related=[rec(f"youtube:{A}:research", status="CONFIRMED", evidence="03:21")]),
            doc(C, "c"),
        )
        plan = rl.repair_plan_for_corpus(c, ROOT)
        self.assertEqual(plan["protected_pairs"], [[f"youtube:{A}:research", f"youtube:{B}:research"]])
        v = plan["videos"][0]
        self.assertEqual([r["target_id"] for r in v["remove"]], [f"youtube:{C}:research"])
        self.assertEqual([k["target_id"] for k in v["keep"]], [f"youtube:{B}:research"])

    def test_real_registry_keeps_the_golden_pair_and_modifies_nothing(self):
        before = (ROOT / "registry.json").read_bytes()
        corpus = rl.load_corpus(ROOT)
        plan = rl.repair_plan_for_corpus(corpus, ROOT)
        self.assertEqual(plan["protected_pairs"], [["youtube:pRfC1DILDEM:research", "youtube:u3ka_AAb8qE:research"]])
        touched = {v["video_id"] for v in plan["videos"]}
        self.assertTrue(touched.isdisjoint({"pRfC1DILDEM", "u3ka_AAb8qE"}))
        self.assertEqual(plan["delete_planned_count"] + plan["needs_human_count"],
                         rl.validate_related_records(corpus, ROOT)["error_record_count"])
        self.assertEqual((ROOT / "registry.json").read_bytes(), before)

    def test_repair_plan_blocks_network(self):
        with mock.patch.object(urllib.request, "urlopen", side_effect=AssertionError("network")), \
             mock.patch.object(socket, "socket", side_effect=AssertionError("network")):
            rl.repair_plan_for_corpus(self.corpus(), ROOT)


if __name__ == "__main__":
    unittest.main()
