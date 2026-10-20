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

    def test_real_notes_known_problems_were_repaired(self):
        """T17：根拠なし33件（自己リンク2件を含む）は repair-apply で削除済み。もう残っていないことを見る。"""
        rep = self.check(rl.load_corpus(ROOT))
        self.assertEqual(rep["note_count"], 31)
        self.assertEqual(rep["error_counts"], {})
        self.assertEqual(rep["status"], "OK")


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
        # 9本それぞれが本ノートと固有語（製品名）を3語ずつ共有する。多くの動画に出る語は固有語に数えない（T14）ので、語は1本ずつ別にする
        src = doc(A, "元", pieces=[("題名", " ".join(f"tool{i}x tool{i}y tool{i}z" for i in range(9)))])
        many = [doc(f"M{i:010d}", f"m{i}", pieces=[("題名", f"tool{i}x tool{i}y tool{i}z")]) for i in range(9)]
        filler = [doc(f"F{i:010d}", f"f{i}", pieces=[("題名", f"料理のレシピ{i}")]) for i in range(30)]
        corpus = corpus_of(src, *many, *filler)
        out = rl.infer_candidates(src, corpus, limit=3)
        self.assertEqual(len(out), 3)
        self.assertNotIn(f"youtube:{A}:research", [c["target_id"] for c in out])
        self.assertEqual(len(rl.infer_candidates(src, corpus, limit=20)), 9)
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
        # 既存の確認済みペアは候補の上位3以内に出て、荷札の関係・statusをそのまま見せる
        rag = next(v for v in rep["videos"] if v["video_id"] == "pRfC1DILDEM")
        top3 = [c["target_id"] for c in rag["candidates"][:3]]
        self.assertIn("youtube:u3ka_AAb8qE:research", top3)
        pair = next(c for c in rag["candidates"] if c["target_id"] == "youtube:u3ka_AAb8qE:research")
        self.assertEqual((pair["already_in_note"], pair["note_status"], pair["relation"]), (True, "CONFIRMED", "COMPLEMENTS"))


class TestCandidatePrecision(unittest.TestCase):
    """T14: 汎用語だけ・固有語2語未満・該当箇所が対応しない候補は出さない。回帰の正解セットは registry の実データ."""

    GENERIC = "モデル 自動 操作 画面 ワークフロー エージェント システム 用意 computer"

    def cands(self, src, *others, pad=12):
        filler = [doc(f"P{i:010d}", f"p{i}", pieces=[("題名", f"料理のレシピ{i}")]) for i in range(pad)]
        return rl.infer_candidates(src, corpus_of(src, *others, *filler))

    def test_generic_words_alone_never_make_a_candidate(self):
        a = doc(A, "a", pieces=[("題名", self.GENERIC), ("章", self.GENERIC)])
        b = doc(B, "b", pieces=[("題名", self.GENERIC), ("章", self.GENERIC)])
        self.assertEqual(self.cands(a, b), [])

    def test_big_brand_names_alone_are_not_distinctive(self):
        a = doc(A, "a", pieces=[("題名", "claude gemini openai chatgpt google anthropic")])
        b = doc(B, "b", pieces=[("題名", "claude gemini openai chatgpt google anthropic")])
        self.assertEqual(self.cands(a, b), [])

    def test_fewer_than_two_distinctive_terms_is_not_enough(self):
        # 固有語は playwright の1語だけ。残りは汎用語・大手の名前
        a = doc(A, "a", pieces=[("題名", f"playwright claude openai {self.GENERIC}")])
        b = doc(B, "b", pieces=[("題名", f"playwright claude openai {self.GENERIC}")])
        self.assertEqual(self.cands(a, b), [])
        b2 = doc(B, "b", pieces=[("題名", f"playwright obsidian claude openai")])
        a2 = doc(A, "a", pieces=[("題名", f"playwright obsidian claude openai")])
        self.assertEqual([c["target_id"] for c in self.cands(a2, b2)], [f"youtube:{B}:research"])

    def test_places_must_correspond_heading_to_heading_or_claim_to_claim(self):
        terms = "playwright obsidian agentsmd"
        heading = doc(A, "a", pieces=[("章", terms)])
        claim = doc(B, "b", pieces=[("主張", terms)])
        self.assertEqual(self.cands(heading, claim), [])       # 章と主張：対応しない
        self.assertEqual(self.cands(claim, heading), [])
        summary = doc(C, "c", pieces=[("要約", terms)])
        self.assertEqual(self.cands(heading, summary), [])     # 要約にだけある語は根拠にしない
        claim2 = doc(C, "c", pieces=[("主張", terms)])
        self.assertEqual(len(self.cands(claim, claim2)), 1)    # 主張どうしは対応する
        tag = doc(C, "c", pieces=[("タグ", terms)])
        self.assertEqual(len(self.cands(heading, tag)), 1)     # 見出し（章・題名・タグ）どうしは対応する

    def test_filter_stats_count_every_ordered_pair_and_reason(self):
        a = doc(A, "a", pieces=[("題名", "playwright obsidian agentsmd")])
        b = doc(B, "b", pieces=[("題名", "playwright obsidian agentsmd")])
        c = doc(C, "c", pieces=[("題名", self.GENERIC)])
        stats = rl.candidate_filter_stats(corpus_of(a, b, c, *[doc(f"P{i:010d}", "p", pieces=[("題名", f"料理{i}レシピ")]) for i in range(10)]))
        self.assertEqual(stats["pairs_evaluated"], 13 * 12)
        self.assertEqual(stats["pass"], 2)
        self.assertEqual(sum(stats["rejected"].values()) + stats["pass"], stats["pairs_evaluated"])

    def test_real_registry_golden_pair_is_top3_both_ways_and_weak_example_is_gone(self):
        corpus = rl.load_corpus(ROOT)
        rep = rl.candidates_for_corpus(corpus, limit=30)   # 広い上限でも弱い例が出ないこと
        by = {v["video_id"]: [c["target_id"] for c in v["candidates"]] for v in rep["videos"]}
        self.assertIn("youtube:u3ka_AAb8qE:research", by["pRfC1DILDEM"][:3])
        self.assertIn("youtube:pRfC1DILDEM:research", by["u3ka_AAb8qE"][:3])
        # 弱い例：共通語が「コミュニティ・自動送信・mac・mini・computer・use」の組は出ない
        self.assertNotIn("youtube:NCQZiT0e59g:research", by["JXmk7hmbS3c"])
        self.assertNotIn("youtube:JXmk7hmbS3c:research", by["NCQZiT0e59g"])
        # 件数は T14 前（147件、上限5）より減る
        self.assertLess(rl.candidates_for_corpus(corpus)["candidate_count"], 147)

    def test_cli_summary_lists_top_pairs_with_evidence_and_modifies_nothing(self):
        import io
        from contextlib import redirect_stdout
        before = (ROOT / "registry.json").read_bytes()
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = rl.main(["candidates", "--summary", "--top", "5"])
        out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("【関連動画の候補（自動推定・未確認）】"))
        self.assertIn("人の目での品質確認はまだです", out)
        self.assertEqual(out.count("    根拠: 共通語:"), 5)
        self.assertEqual(sum(1 for ln in out.splitlines() if ln[:3].strip().rstrip(".").isdigit()), 5)
        self.assertNotIn('"files_modified"', out)
        self.assertEqual((ROOT / "registry.json").read_bytes(), before)

    def test_no_remaining_real_candidate_uses_a_generic_word_as_evidence(self):
        corpus = rl.load_corpus(ROOT)
        for v in rl.candidates_for_corpus(corpus)["videos"]:
            for c in v["candidates"]:
                shared = c["evidence"].split(" ／ ")[0].removeprefix("共通語: ").split(", ")
                generic = [t for t in shared if t in rl._GENERIC_TERMS]
                self.assertEqual(generic, [], (v["video_id"], c["target_id"]))
                self.assertGreaterEqual(len(shared), 3)


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

    def test_module_writes_only_inside_repair_apply_and_has_no_delete_code(self):
        src = (ROOT / "automation" / "gemini-notebook" / "related_links.py").read_text(encoding="utf-8")
        for needle in ("add_text(", ".unlink(", "os.remove", "rmtree", "open(", "subprocess"):
            self.assertNotIn(needle, src, needle)
        # 書き込みは repair_apply の中の 2 か所だけ（本番 --write と、dry-run の一時コピー）
        start = src.index("def repair_apply(")
        end = src.index("# ----------------------------------------------------------------", start)
        self.assertEqual(src.count("write_text"), src[start:end].count("write_text"))
        self.assertEqual(src[start:end].count("write_text"), 2)
        self.assertIn("if write:\n        for c in plan[\"changed\"]:\n            (root / c[\"research_path\"]).write_text", src[start:end])

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

    def test_summary_is_a_short_human_readable_list(self):
        corpus = self.corpus()
        plan = rl.repair_plan_for_corpus(corpus, ROOT, limit=3)
        text = rl.format_repair_summary(plan, corpus)
        self.assertIn("対象ノート 1本／削除予定 2件／人の確認 0件", text)
        self.assertIn("✕", text)
        self.assertIn("自己リンク", text)
        self.assertIn("根拠なし", text)
        self.assertIn("＋", text)
        self.assertIn("（同じ宛先）", text)
        self.assertIn("共通語:", text)
        self.assertNotIn("http", text)
        self.assertNotIn("@@", text)   # 差分形式ではなく一覧
        self.assertLess(len(text.splitlines()), 20)

    def test_cli_summary_prints_text_and_modifies_nothing(self):
        import io
        from contextlib import redirect_stdout
        before = (ROOT / "registry.json").read_bytes()
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = rl.main(["repair-plan", "--summary"])
        out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("【related_records 修復計画の一覧"))
        self.assertIn("温存する確定ペア: pRfC1DILDEM ↔ u3ka_AAb8qE", out)
        self.assertNotIn('"files_modified"', out)    # JSONではない
        self.assertEqual((ROOT / "registry.json").read_bytes(), before)

    def test_repair_plan_blocks_network(self):
        with mock.patch.object(urllib.request, "urlopen", side_effect=AssertionError("network")), \
             mock.patch.object(socket, "socket", side_effect=AssertionError("network")):
            rl.repair_plan_for_corpus(self.corpus(), ROOT)


def _write_notes(root, notes):
    (root / "research").mkdir(parents=True, exist_ok=True)
    for vid, text in notes.items():
        (root / "research" / f"{vid}.md").write_text(text, encoding="utf-8")


LEGACY_WITH_SECTION = f"""# ノートA

## 独自要約
本文は変えない。

## 関連する既存研究・課題との接続
- `youtube:{A}` (UPDATES): 自己リンク
- `youtube:{B}` (COMPLEMENTS): 根拠なしのリンク
- `youtube:{C}:research` (COMPLEMENTS): 合格の確定リンク | status: CONFIRMED | evidence: 12:34 の言及

## 限界
最後の節。
"""
LEGACY_NO_SECTION = "# ノートB\n\n## 独自要約\n本文は変えない。\n\n## 限界\n最後の節。\n"
FRONTMATTER_NOTE = f"""---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "ノートC"
related_records:
  - target_id: "youtube:{A}:research"
    relation: "COMPLEMENTS"
    note: "既存の確定"
    status: "CONFIRMED"
    evidence: "01:02"
logical_id: "youtube:{C}:research"
---

# 本文
変えない。
"""
FRONTMATTER_NO_BLOCK = "---\ntype: \"RESEARCH_NOTE\"\ntitle: \"ノートD\"\n---\n\n# 本文\n"


def new_rec(target, relation="COMPLEMENTS", status="CANDIDATE", note="自動推定の候補（未確認）：共通の主題「x」", evidence="共通語: x ／ 本ノート: 章「x」 ／ 相手: 章「x」"):
    return {"target_id": target, "relation": relation, "status": status, "note": note, "evidence": evidence, "direction": "FORWARD"}


class TestRepairApplyEditing(unittest.TestCase):
    """edit_note_text：関連レコード以外は1バイトも変えない（荷札あり・本文だけ・節なしの3種）。"""

    def test_legacy_note_deletes_bad_lines_and_appends_after_the_last_record_line(self):
        removed = {(f"youtube:{A}", "UPDATES", "CANDIDATE"), (f"youtube:{B}", "COMPLEMENTS", "CANDIDATE")}
        out = rl.edit_note_text(LEGACY_WITH_SECTION, removed, [new_rec(f"youtube:{B}:research")])
        self.assertEqual(out, f"""# ノートA

## 独自要約
本文は変えない。

## 関連する既存研究・課題との接続
- `youtube:{C}:research` (COMPLEMENTS): 合格の確定リンク | status: CONFIRMED | evidence: 12:34 の言及
- `youtube:{B}:research` (COMPLEMENTS): 自動推定の候補（未確認）：共通の主題「x」 | status: CANDIDATE | evidence: 共通語: x ／ 本ノート: 章「x」 ／ 相手: 章「x」

## 限界
最後の節。
""")
        self.assertTrue(rl.only_related_records_changed(LEGACY_WITH_SECTION, out))

    def test_legacy_note_without_the_section_gets_it_at_the_end(self):
        out = rl.edit_note_text(LEGACY_NO_SECTION, set(), [new_rec(f"youtube:{A}:research")])
        self.assertTrue(out.startswith(LEGACY_NO_SECTION))
        self.assertEqual(out[len(LEGACY_NO_SECTION):],
                         "\n## 関連する既存研究・課題との接続\n\n- `youtube:" + A + ":research` (COMPLEMENTS): 自動推定の候補（未確認）：共通の主題「x」"
                         " | status: CANDIDATE | evidence: 共通語: x ／ 本ノート: 章「x」 ／ 相手: 章「x」\n")
        self.assertTrue(rl.only_related_records_changed(LEGACY_NO_SECTION, out))

    def test_emptied_section_keeps_its_heading_and_takes_the_new_lines(self):
        text = "# t\n\n## 関連する既存研究・課題との接続\n- `youtube:" + A + "` (COMPLEMENTS): 根拠なし\n\n## 限界\nx\n"
        out = rl.edit_note_text(text, {(f"youtube:{A}", "COMPLEMENTS", "CANDIDATE")}, [new_rec(f"youtube:{B}:research")])
        self.assertEqual(out.splitlines()[2], "## 関連する既存研究・課題との接続")
        self.assertIn(f"`youtube:{B}:research`", out.splitlines()[3] + out.splitlines()[4])
        self.assertTrue(out.endswith("\n## 限界\nx\n"))
        self.assertTrue(rl.only_related_records_changed(text, out))

    def test_frontmatter_note_gets_items_inside_the_related_records_block_only(self):
        out = rl.edit_note_text(FRONTMATTER_NOTE, set(), [new_rec(f"youtube:{B}:research", note="理由", evidence='共通語: "x"')])
        self.assertTrue(rl.only_related_records_changed(FRONTMATTER_NOTE, out))
        data, body = rl.query_research.parse_yaml_frontmatter(out)
        self.assertEqual([r["target_id"] for r in data["related_records"]], [f"youtube:{A}:research", f"youtube:{B}:research"])
        self.assertEqual(data["related_records"][1]["status"], "CANDIDATE")
        self.assertEqual(data["related_records"][1]["evidence"], '共通語: "x"')
        self.assertEqual(data["logical_id"], f"youtube:{C}:research")    # 他の荷札項目は残る
        self.assertEqual(body, "\n# 本文\n変えない。\n")

    def test_frontmatter_without_a_block_gets_one_before_the_closing_line(self):
        out = rl.edit_note_text(FRONTMATTER_NO_BLOCK, set(), [new_rec(f"youtube:{A}:research")])
        data, body = rl.query_research.parse_yaml_frontmatter(out)
        self.assertEqual([r["target_id"] for r in data["related_records"]], [f"youtube:{A}:research"])
        self.assertEqual(data["title"], "ノートD")
        self.assertEqual(body, "\n# 本文\n")

    def test_frontmatter_item_is_removed_by_key_and_other_items_stay(self):
        out = rl.edit_note_text(FRONTMATTER_NOTE, {(f"youtube:{A}:research", "COMPLEMENTS", "CONFIRMED")}, [])
        data, _ = rl.query_research.parse_yaml_frontmatter(out)
        self.assertEqual(data["related_records"], [])
        self.assertEqual(data["logical_id"], f"youtube:{C}:research")
        self.assertTrue(rl.only_related_records_changed(FRONTMATTER_NOTE, out))

    def test_separator_and_newlines_in_text_cannot_break_the_line(self):
        out = rl.edit_note_text(LEGACY_NO_SECTION, set(), [new_rec(f"youtube:{A}:research", note="a | b\nc", evidence="d | e\nf")])
        line = [ln for ln in out.splitlines() if ln.startswith("- `youtube:")][0]
        key = rl._line_record_key(line)
        self.assertEqual(key, (f"youtube:{A}:research", "COMPLEMENTS", "CANDIDATE"))
        self.assertEqual(line.count(" | status: "), 1)
        self.assertEqual(line.count(" | evidence: "), 1)

    def test_a_change_outside_the_records_is_detected(self):
        self.assertFalse(rl.only_related_records_changed(LEGACY_NO_SECTION, LEGACY_NO_SECTION.replace("最後の節", "別の節")))
        self.assertFalse(rl.only_related_records_changed(FRONTMATTER_NOTE, FRONTMATTER_NOTE.replace('type: "RESEARCH_NOTE"', 'type: "OTHER"')))
        self.assertFalse(rl.only_related_records_changed(LEGACY_NO_SECTION, LEGACY_NO_SECTION + "余計な行\n"))


class TestRepairApplyPlan(unittest.TestCase):
    """repair_apply_plan：削除は不合格だけ、追加は CANDIDATE だけ（CONFIRMED は自動で付けない）、逆リンクを足す。"""

    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        shared = [("題名", "NotebookLM と Claude の連携"), ("章", "NotebookLM のソース整理と連携手順"),
                  ("タグ", "NotebookLM"), ("タグ", "連携手順"), ("主張", "ソース整理の自動化")]
        self.corpus = corpus_of(
            doc(A, "a", pieces=shared, related=[
                rec(f"youtube:{A}", relation="UPDATES", evidence=""),
                rec(f"youtube:{B}", evidence=""),
                rec(f"youtube:{C}:research", status="CONFIRMED", evidence="12:34 の言及"),
            ]),
            doc(B, "b", pieces=shared),
            doc(C, "c", pieces=[("題名", "別の話題")], related=[rec(f"youtube:{A}:research", status="CONFIRMED", evidence="01:02")]),
            *[doc(f"N{i:010d}", f"n{i}", pieces=[("題名", f"料理のレシピ{i}")]) for i in range(12)],
        )
        notes = {A: LEGACY_WITH_SECTION, B: LEGACY_NO_SECTION, C: FRONTMATTER_NOTE}
        notes.update({f"N{i:010d}": "# n\n" for i in range(12)})
        _write_notes(self.root, notes)

    def plan(self, **kw):
        return rl.repair_apply_plan(self.corpus, self.root, **kw)

    def test_deletes_only_invalid_records_and_adds_candidates_never_confirmed(self):
        plan = self.plan()
        by = {c["video_id"]: c for c in plan["changed"]}
        self.assertEqual(sorted(by), [A, B])        # C・無関係なノートは変更なし
        self.assertEqual([(r["target_id"], r["reasons"]) for r in by[A]["removed"]],
                         [(f"youtube:{A}", ["SELF_LINK", "EVIDENCE_MISSING"]), (f"youtube:{B}", ["EVIDENCE_MISSING"])])
        self.assertEqual(plan["removed_count"], 2)
        for ch in plan["changed"]:
            for a in ch["added"]:
                self.assertEqual(a["status"], "CANDIDATE")
                self.assertTrue(a["evidence"])
                self.assertNotEqual(rl.target_video_id(a["target_id"]), ch["video_id"])
        self.assertNotIn(f"youtube:{A} ", by[A]["new_text"])
        self.assertIn(f"`youtube:{C}:research` (COMPLEMENTS): 合格の確定リンク | status: CONFIRMED", by[A]["new_text"])   # 温存
        self.assertEqual([a["target_id"] for a in by[A]["added"]], [f"youtube:{B}:research"])
        self.assertTrue(all(c["only_related_records_changed"] for c in plan["changed"]))

    def test_every_added_link_has_its_backlink(self):
        plan = self.plan()
        by = {c["video_id"]: c for c in plan["changed"]}
        # A→B を足したので B→A もある（ここでは B 自身の候補としても出るので、重ねて足さない）
        self.assertEqual([a["target_id"] for a in by[B]["added"]], [f"youtube:{A}:research"])
        self.assertEqual(plan["added_reverse_count"], 0)
        self.assertIn(f"`youtube:{A}:research`", by[B]["new_text"])
        # 片方向の候補しか出ない組は、相手側に CANDIDATE の逆向きを足し、根拠は「本ノート」と「相手」を入れ替える
        corpus = corpus_of(doc(A, "a", related=[rec(f"youtube:{B}:research", evidence="本ノート: 章「x」 ／ 相手: 章「y」")]), doc(B, "b"))
        _write_notes(self.root, {A: "# a\n", B: LEGACY_NO_SECTION})
        (ch,) = rl.repair_apply_plan(corpus, self.root)["changed"]
        (back,) = ch["added"]
        self.assertEqual((ch["video_id"], back["direction"], back["status"]), (B, "REVERSE", "CANDIDATE"))
        self.assertEqual(back["evidence"], "相手ノートの記載: 本ノート: 章「x」 ／ 相手: 章「y」")
        self.assertEqual(rl._swap_viewpoint("共通語: x ／ 本ノート: 章「x」 ／ 相手: 章「y」"), "共通語: x ／ 相手: 章「x」 ／ 本ノート: 章「y」")

    def test_reverse_of_a_kept_record_is_added_as_candidate_not_confirmed(self):
        corpus = corpus_of(doc(A, "a", related=[rec(f"youtube:{B}:research", status="CONFIRMED", evidence="12:34")]), doc(B, "b"))
        _write_notes(self.root, {A: "# a\n", B: LEGACY_NO_SECTION})
        plan = rl.repair_apply_plan(corpus, self.root)
        (ch,) = plan["changed"]
        self.assertEqual(ch["video_id"], B)
        self.assertEqual([(a["target_id"], a["status"], a["direction"]) for a in ch["added"]], [(f"youtube:{A}:research", "CANDIDATE", "REVERSE")])
        self.assertIn("12:34", ch["added"][0]["evidence"])

    def test_confirmed_invalid_record_is_left_for_a_human(self):
        corpus = corpus_of(doc(A, "a", related=[rec(f"youtube:{B}:research", status="CONFIRMED", evidence="雰囲気")]), doc(B, "b"))
        _write_notes(self.root, {A: "# a\n", B: "# b\n"})
        plan = rl.repair_apply_plan(corpus, self.root)
        self.assertEqual(plan["removed_count"], 0)
        self.assertEqual([(n["video_id"], n["reasons"]) for n in plan["needs_human"]], [(A, ["CONFIRMED_WITHOUT_TIME_OR_URL"])])

    def test_the_protected_pair_is_never_touched(self):
        corpus = corpus_of(
            doc(A, "a", related=[rec(f"youtube:{B}:research", status="CONFIRMED", evidence="12:34"), rec(f"youtube:{C}", evidence="")]),
            doc(B, "b", related=[rec(f"youtube:{A}:research", status="CONFIRMED", evidence="https://example.com/x")]), doc(C, "c"))
        _write_notes(self.root, {A: "# a\n", B: "# b\n", C: "# c\n"})
        plan = rl.repair_apply_plan(corpus, self.root)
        self.assertEqual(plan["protected_pairs"], [[f"youtube:{A}:research", f"youtube:{B}:research"]])
        self.assertEqual({r["target_id"] for c in plan["changed"] for r in c["removed"]}, {f"youtube:{C}"})

    def test_plan_is_deterministic(self):
        a, b = self.plan(), self.plan()
        self.assertEqual([c["new_text"] for c in a["changed"]], [c["new_text"] for c in b["changed"]])


class TestRepairApplyOnACopyOfTheRealNotes(unittest.TestCase):
    """実データの写しに対する通し検査（実データの状態に依らない性質だけを見る）。"""

    def copy_root(self):
        import shutil
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        shutil.copytree(ROOT / "research", root / "research")
        shutil.copytree(ROOT / "proposals", root / "proposals")
        shutil.copy2(ROOT / "registry.json", root / "registry.json")
        return root

    @staticmethod
    def snapshot(root):
        return {p.name: p.read_bytes() for p in sorted((root / "research").glob("*.md"))}

    def test_dry_run_writes_nothing_and_reports_the_projected_result(self):
        root = self.copy_root()
        before = self.snapshot(root)
        rep = rl.repair_apply(root, write=False)
        self.assertEqual(rep["status"], "DRY_RUN_REPAIR_APPLY")
        self.assertIs(rep["files_modified"], False)
        self.assertEqual(self.snapshot(root), before)
        self.assertEqual(rep["validate_after"]["error_record_count"], 0)
        self.assertEqual(rep["second_run_changes"], 0)

    def test_write_repairs_everything_changes_only_related_records_and_is_idempotent(self):
        root = self.copy_root()
        before = self.snapshot(root)
        reg_before = (root / "registry.json").read_bytes()
        rep = rl.repair_apply(root, write=True)
        self.assertEqual(rep["status"], "APPLIED")
        after = self.snapshot(root)
        changed = {n for n in before if before[n] != after[n]}
        self.assertEqual(changed, {Path(c["research_path"]).name for c in rep["changed"]})
        for n in before:
            self.assertTrue(rl.only_related_records_changed(before[n].decode("utf-8"), after[n].decode("utf-8")), n)
        self.assertEqual(set(before), set(after))                        # ファイルの増減なし
        self.assertEqual((root / "registry.json").read_bytes(), reg_before)   # registry.json は変えない
        v = rep["validate_after"]
        self.assertEqual((v["status"], v["error_record_count"], v["self_link_count"], v["target_not_found_count"],
                          v["missing_backlink_count"]), ("OK", 0, 0, 0, 0))
        # 確定済みの記録は自動では増えず、合格ペアは残る
        self.assertEqual(v["confirmed_count"], rep["validate_before"]["confirmed_count"])
        self.assertEqual(v["confirmed_valid_pairs"], rep["validate_before"]["confirmed_valid_pairs"])
        # 2回目は変更0件で、ファイルは1バイトも変わらない
        again = rl.repair_apply(root, write=True)
        self.assertEqual(again["notes_changed"], 0)
        self.assertIs(again["files_modified"], False)
        self.assertEqual(self.snapshot(root), after)
        # 追加した記録は全部 CANDIDATE で根拠つき
        corpus = rl.load_corpus(root)
        for c in rep["changed"]:
            for a in c["added"]:
                self.assertEqual(a["status"], "CANDIDATE")
                self.assertTrue(a["evidence"].strip())
                rec_ = next(r for r in corpus[c["video_id"]]["related_records"] if r["target_id"] == a["target_id"])
                self.assertEqual(rec_["status"], "CANDIDATE")

    def test_nothing_is_written_when_a_non_record_line_would_change(self):
        root = self.copy_root()
        before = self.snapshot(root)
        real_edit = rl.edit_note_text

        def bad_edit(text, remove_keys, add_records):
            return real_edit(text, remove_keys, add_records).replace("## 限界", "## 限界（改変）")

        with mock.patch.object(rl, "edit_note_text", bad_edit):
            rep = rl.repair_apply(root, write=True)
        if rep["status"] != "APPLIED":      # 実データ側にすでに変更が無い状態なら、検査が走らず APPLIED(変更0) になる
            self.assertEqual(rep["status"], "BLOCKED_NON_RECORD_DIFF")
            self.assertTrue(rep["blocked_files"])
        self.assertEqual(self.snapshot(root), before)

    def test_blocks_network(self):
        root = self.copy_root()
        with mock.patch.object(urllib.request, "urlopen", side_effect=AssertionError("network")), \
             mock.patch.object(socket, "socket", side_effect=AssertionError("network")):
            rl.repair_apply(root, write=True)

    def test_cli_is_dry_run_unless_write_is_given(self):
        import contextlib
        import io
        root = self.copy_root()
        before = self.snapshot(root)
        with mock.patch.object(rl, "ROOT", root):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(rl.main(["repair-apply", "--print-diff"]), 0)
            out = json.loads(buf.getvalue())
            self.assertEqual(out["status"], "DRY_RUN_REPAIR_APPLY")
            self.assertNotIn("_texts", out)
            self.assertEqual(self.snapshot(root), before)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(rl.main(["repair-apply", "--write"]), 0)
            self.assertEqual(json.loads(buf.getvalue())["status"], "APPLIED")
            self.assertEqual(rl.main.__defaults__, (None,))


class TestRealNotesAfterRepair(unittest.TestCase):
    """T17：自動適用後のリポジトリの研究ノート（実データ）の自己検査。"""

    def test_validate_is_clean_and_registry_is_consistent(self):
        corpus = rl.load_corpus(ROOT)
        rep = rl.validate_related_records(corpus, ROOT)
        self.assertEqual((rep["status"], rep["error_record_count"], rep["missing_backlink_count"]), ("OK", 0, 0))
        self.assertEqual(rep["error_counts"], {})
        self.assertFalse([i for i in rep["items"] if i["errors"]])
        self.assertEqual(rep["confirmed_valid_pairs"], [(f"youtube:pRfC1DILDEM:research", "youtube:u3ka_AAb8qE:research")])
        self.assertEqual(rep["confirmed_count"], 2)         # CONFIRMED は自動で増えていない
        for vid, d in corpus.items():
            for r in d["related_records"]:
                self.assertNotEqual(rl.target_video_id(r["target_id"]), vid)
                self.assertIn(rl.target_video_id(r["target_id"]), corpus)
        # registry.json は related_records を持たない（正本は研究ノート）。台帳の各動画が研究ノートを指している
        reg = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))
        self.assertNotIn("related_records", json.dumps(reg))
        self.assertEqual(sorted(r["video_id"] for r in reg["records"]), sorted(corpus))

    def test_applying_again_changes_nothing(self):
        rep = rl.repair_apply(ROOT, write=False)
        self.assertEqual(rep["notes_changed"], 0)
        self.assertEqual((rep["removed_count"], rep["added_forward_count"], rep["added_reverse_count"]), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
