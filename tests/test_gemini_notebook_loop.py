#!/usr/bin/env python3
"""Comprehensive automated test suite for the Gemini Notebook Research Loop bridge (v0.3).

Verifies:
1. Extraction of `research_receipt_v1` from raw JSON and Gemini Markdown output (fenced code blocks).
2. Canonical YouTube URL normalization (`watch?v=`, `youtu.be/`, `shorts/`, `live/`) and video_id matching.
3. End-to-end processing of NEW video records, `registry.json` updates, and `github_knowledge_index_export.md` generation.
4. Fresh remote branch deduplication (`git fetch --prune origin` before scanning) so stale local refs are never trusted,
   plus safety stop if remote fetch fails.
5. Deep research record deduplication across `registry.json` AND `research/*.md` / `notes/*.md` filenames and markdown bodies
   (both local and remote branches).
6. Protection against `loop_state.json` corruption: refuses to silently reset existing history when JSON or schema is invalid.
7. Explicit separation between GitHub's `github_knowledge_index_export.md` and Gemini Notebook's internal `AI技術研究室_知識索引.md`,
   and strict separation between `github_write_status` and `notebook_sync_status` (`NOT_SYNCED_FROM_GITHUB`).
8. Intentional failure & safety boundary stops (`main` refusal, invalid origin refusal, >300 char summary rejection,
   `notebook_readback != PASS` skip, `METADATA_ONLY` skip).
9. Local & remote Git commit, push, blob SHA readback verification, remote divergence safety stop, and cloud `--payload-env` ingestion.
"""
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "automation" / "gemini-notebook" / "receipt_to_research.py"

spec = importlib.util.spec_from_file_location("receipt_to_research", MODULE_PATH)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def make_sample_receipt(**overrides):
    base = {
        "schema_version": "research_receipt_v1",
        "notebook_url": "https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7",
        "checked_at": "2026-10-17",
        "notebook_readback": "PASS",
        "github_dedup_status": "PASS",
        "videos": [
            {
                "video_id": "dQw4w9WgXcQ",
                "title": "AI Agent Harness Design Patterns 2026",
                "url": "https://youtu.be/dQw4w9WgXcQ?t=45",
                "published_at": "2026-10-12",
                "summary_ja": "ハーネス設計においてモデル呼び出しと状態管理・決定論的検証を分離し、失敗時の再試行を抑制する手法を解説。",
                "source_scope": "Gemini transcript analysis with timestamp verification; visual frames not acquired",
                "claims": [
                    {
                        "text": "ツール実行前後のHooksにより危険なコマンドを決定論的にブロックできる",
                        "status": "CONFIRMED_DOC",
                        "timestamp_seconds": 125,
                        "official_url": "https://code.claude.com/docs/en/hooks",
                    }
                ],
                "notebook_source_id": "src_017_harness",
                "notebook_readback": "PASS",
                "changes": ["NEW"],
            }
        ],
        "next_topics": [
            "ハーネスにおけるツール失敗時の決定論的ロールバック設計",
            "Gemini NotebookのGoogle Drive自動同期と知識索引差分の検証",
        ],
        "unknowns": [
            "Gemini Scheduled ActionsでのNotebookソース追加が完全無人で動作するかは未実証"
        ],
    }
    base.update(overrides)
    return base


class TestGeminiNotebookLoopV03(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tmp_dir.name) / "repo"
        self.remote_bare = Path(self.tmp_dir.name) / "kamiyusense" / "ai-video-research.git"
        self.repo_root.mkdir(parents=True, exist_ok=True)
        self.remote_bare.mkdir(parents=True, exist_ok=True)

        subprocess.run(["git", "init", "--bare", str(self.remote_bare)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.repo_root), "init"], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(self.repo_root), "config", "user.email", "test@example.com"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo_root), "config", "user.name", "Test Runner"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo_root),
                "remote",
                "add",
                "origin",
                self.remote_bare.as_posix(),
            ],
            check=True,
            capture_output=True,
        )

        (self.repo_root / "research").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "notes").mkdir(parents=True, exist_ok=True)
        initial_registry = {
            "schema_version": 1,
            "purpose": "動画IDの重複確認用台帳。",
            "repository": "kamiyusense/ai-video-research",
            "records": [
                {
                    "record_id": "youtube:lC5jxpYmatE",
                    "video_id": "lC5jxpYmatE",
                    "canonical_url": "https://www.youtube.com/watch?v=lC5jxpYmatE",
                    "research_path": "research/2026-10-10-lC5jxpYmatE-ai-techniques.md",
                    "source_scope": "Gemini Spark transcript report",
                    "research_date": "2026-10-10",
                    "status": "RESEARCH_RECORDED; LIVE_NOT_RUN",
                    "evidence": "USER_SUPPLIED_REPORTS",
                }
            ],
        }
        (self.repo_root / "registry.json").write_text(
            json.dumps(initial_registry, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (self.repo_root / "research" / "2026-10-10-lC5jxpYmatE-ai-techniques.md").write_text(
            "# 動画研究05\n\n- video_id: `lC5jxpYmatE`\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "-C", str(self.repo_root), "checkout", "-b", "main"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.repo_root), "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(self.repo_root), "commit", "-m", "Initial commit"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo_root), "push", "origin", "main:main"],
            check=True,
            capture_output=True,
        )

        # Create a parallel remote branch with `ZjUJ-35acaU` in registry.json
        subprocess.run(
            ["git", "-C", str(self.repo_root), "checkout", "-b", "research/video08-mock"],
            check=True,
            capture_output=True,
        )
        remote_reg = json.loads((self.repo_root / "registry.json").read_text(encoding="utf-8"))
        remote_reg["records"].append(
            {
                "record_id": "youtube:ZjUJ-35acaU",
                "video_id": "ZjUJ-35acaU",
                "canonical_url": "https://www.youtube.com/watch?v=ZjUJ-35acaU",
                "research_path": "research/2026-10-10-ZjUJ-35acaU-notebooklm-youtube-extension.md",
                "source_scope": "SPARK_TRANSCRIPT_REPORT",
                "research_date": "2026-10-10",
                "status": "REVIEWED_PARTIAL",
                "evidence": "SPARK_TRANSCRIPT_REPORT",
            }
        )
        (self.repo_root / "registry.json").write_text(
            json.dumps(remote_reg, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "-C", str(self.repo_root), "add", "registry.json"], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(self.repo_root), "commit", "-m", "Add video08 on parallel branch"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo_root),
                "push",
                "origin",
                "research/video08-mock:research/video08-mock",
            ],
            check=True,
            capture_output=True,
        )

        # Switch to working feature branch off main and push initial state
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo_root),
                "checkout",
                "-b",
                "feature/gemini-notebook-research-loop-20261016",
                "main",
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo_root),
                "push",
                "origin",
                "feature/gemini-notebook-research-loop-20261016:feature/gemini-notebook-research-loop-20261016",
            ],
            check=True,
            capture_output=True,
        )

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_01_extract_receipt_from_markdown_and_raw_json(self):
        sample = make_sample_receipt()
        raw_json = json.dumps(sample, ensure_ascii=False, indent=2)
        extracted_direct = bridge.extract_receipt_payload(raw_json)
        self.assertEqual(extracted_direct["schema_version"], "research_receipt_v1")

        markdown_wrapped = (
            "## Gemini Notebook 調査完了報告\n\n"
            "Notebookの既存16ソースを照合し、1件の新規研究を追加しました。\n\n"
            "```json\n"
            + raw_json
            + "\n```\n\n"
            "次回の調査テーマはハーネスのロールバック設計です。"
        )
        extracted_md = bridge.extract_receipt_payload(markdown_wrapped)
        self.assertEqual(extracted_md["videos"][0]["video_id"], "dQw4w9WgXcQ")
        self.assertEqual(
            bridge.compute_receipt_digest(extracted_direct),
            bridge.compute_receipt_digest(extracted_md),
        )

    def test_02_youtube_url_normalization_and_mismatch_rejection(self):
        self.assertEqual(
            bridge.extract_youtube_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120s"),
            "dQw4w9WgXcQ",
        )
        self.assertEqual(
            bridge.extract_youtube_id("https://youtu.be/dQw4w9WgXcQ?si=abc"),
            "dQw4w9WgXcQ",
        )
        self.assertEqual(
            bridge.extract_youtube_id("https://www.youtube.com/shorts/dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )
        self.assertEqual(
            bridge.extract_youtube_id("https://www.youtube.com/live/dQw4w9WgXcQ?feature=share"),
            "dQw4w9WgXcQ",
        )

        bad = make_sample_receipt()
        bad["videos"][0]["url"] = "https://www.youtube.com/watch?v=11111111111"
        with self.assertRaisesRegex(ValueError, "does not match video_id"):
            bridge.validate(bad)

    def test_03_end_to_end_apply_duplicate_prevention_and_index_separation(self):
        receipt = make_sample_receipt()
        buf = io.StringIO()
        with redirect_stdout(buf):
            summary1, _ = bridge.process_receipt_data(
                data=receipt,
                root=self.repo_root,
                apply=True,
                sync_index=True,
            )
        self.assertEqual(summary1["new_records"], 1)
        self.assertEqual(summary1["ids"], ["dQw4w9WgXcQ"])
        self.assertEqual(summary1["remote_dedup_freshness"], "FRESH_FETCHED")
        self.assertEqual(summary1["notebook_sync_status"], "NOT_SYNCED_FROM_GITHUB")
        self.assertEqual(summary1["github_write_status"], "LOCAL_WORKTREE_WRITTEN")

        note_path = self.repo_root / "research" / "2026-10-17-dQw4w9WgXcQ-gemini-notebook.md"
        self.assertTrue(note_path.exists())
        note_text = note_path.read_text(encoding="utf-8")
        self.assertIn("- canonical_url: https://www.youtube.com/watch?v=dQw4w9WgXcQ", note_text)
        self.assertIn("- GitHub-to-Notebook reverse sync: NOT_SYNCED_FROM_GITHUB", note_text)

        # Verify GitHub knowledge index export is created with distinct filename and explicit warning
        export_path = (
            self.repo_root
            / "automation"
            / "gemini-notebook"
            / "state"
            / "github_knowledge_index_export.md"
        )
        self.assertTrue(export_path.exists())
        index_md = export_path.read_text(encoding="utf-8")
        self.assertIn("github_knowledge_index_export.md", index_md)
        self.assertIn("AI技術研究室_知識索引.md", index_md)
        self.assertIn("NOT_SYNCED_FROM_GITHUB", index_md)
        self.assertIn("`dQw4w9WgXcQ`", index_md)
        self.assertIn("`ZjUJ-35acaU`", index_md)

        # Re-processing identical receipt must be idempotent
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            summary2, _ = bridge.process_receipt_data(
                data=receipt,
                root=self.repo_root,
                apply=True,
                sync_index=True,
            )
        self.assertEqual(summary2["new_records"], 0)
        self.assertEqual(summary2["updated_records"], 0)
        self.assertEqual(summary2["skipped"][0]["reason"], "SKIP_DUPLICATE_RECEIPT")

    def test_04_fresh_remote_fetch_and_deep_markdown_deduplication(self):
        # 1. Create a local research markdown file NOT listed in registry.json (`UnregLocal1`)
        (self.repo_root / "notes" / "series-intake.md").write_text(
            "# Series Intake\n\n- `UnregLocal1`: skipped video in notes body\n",
            encoding="utf-8",
        )

        # 2. From a separate clone, push a brand-new remote branch `research/new-remote-unfetched`
        #    containing an unregistered markdown note for video `FreshRemot9` (NOT in local remote refs yet!)
        other_clone = Path(self.tmp_dir.name) / "other_clone_for_branch"
        subprocess.run(
            ["git", "clone", self.remote_bare.as_posix(), str(other_clone)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(other_clone), "config", "user.email", "other@example.com"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(other_clone), "config", "user.name", "Other"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(other_clone), "checkout", "-b", "research/new-remote-unfetched"],
            check=True,
            capture_output=True,
        )
        (other_clone / "research").mkdir(parents=True, exist_ok=True)
        (other_clone / "research" / "2026-10-17-FreshRemot9-preliminary.md").write_text(
            "# Preliminary Research\n\n- video_id: `FreshRemot9`\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "-C", str(other_clone), "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(other_clone), "commit", "-m", "Add unregistered research note on remote"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(other_clone),
                "push",
                "origin",
                "research/new-remote-unfetched:research/new-remote-unfetched",
            ],
            check=True,
            capture_output=True,
        )

        # Confirm `repo_root` does NOT yet have `origin/research/new-remote-unfetched` in local refs
        refs_before = bridge.git(
            "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin/", root=self.repo_root
        )
        self.assertNotIn("origin/research/new-remote-unfetched", refs_before)

        # Now run `process_receipt_data` with `UnregLocal1` and `FreshRemot9`:
        # It must fetch fresh remote refs automatically and deduplicate BOTH videos!
        receipt = make_sample_receipt(
            videos=[
                {
                    "video_id": "UnregLocal1",
                    "title": "Unregistered Local Note Video",
                    "url": "https://www.youtube.com/watch?v=UnregLocal1",
                    "published_at": None,
                    "summary_ja": "ローカルのnotes本文に記載されている動画。",
                    "source_scope": "Transcript",
                    "claims": [],
                    "notebook_source_id": "src_local_note",
                    "notebook_readback": "PASS",
                    "changes": ["NEW"],
                },
                {
                    "video_id": "FreshRemot9",
                    "title": "Fresh Remote Branch Research Video",
                    "url": "https://www.youtube.com/watch?v=FreshRemot9",
                    "published_at": None,
                    "summary_ja": "リモートの新ブランチ上のresearchファイルにのみ存在する動画。",
                    "source_scope": "Transcript",
                    "claims": [],
                    "notebook_source_id": "src_fresh_remote",
                    "notebook_readback": "PASS",
                    "changes": ["NEW"],
                },
            ]
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            summary, _ = bridge.process_receipt_data(
                data=receipt,
                root=self.repo_root,
                apply=True,
                sync_index=True,
            )
        self.assertEqual(summary["remote_dedup_freshness"], "FRESH_FETCHED")
        self.assertEqual(summary["new_records"], 0)
        reasons = {s["video_id"]: s for s in summary["skipped"]}
        self.assertEqual(reasons["UnregLocal1"]["reason"], "SKIP_EXISTING")
        self.assertIn("notes/series-intake.md", reasons["UnregLocal1"]["detected_via"])
        self.assertEqual(reasons["FreshRemot9"]["reason"], "SKIP_EXISTING_REMOTE_BRANCH")
        self.assertIn(
            "origin/research/new-remote-unfetched",
            reasons["FreshRemot9"]["branches"],
        )

    def test_05_corrupted_loop_state_json_refuses_reset(self):
        state_file = (
            self.repo_root / "automation" / "gemini-notebook" / "state" / "loop_state.json"
        )
        state_file.parent.mkdir(parents=True, exist_ok=True)

        # Case A: Invalid JSON syntax
        corrupted_raw = '{"schema_version": "gemini_notebook_loop_state_v1", BROKEN_JSON'
        state_file.write_text(corrupted_raw, encoding="utf-8")
        with self.assertRaises(ValueError) as cm_a:
            bridge.process_receipt_data(make_sample_receipt(), root=self.repo_root, apply=True)
        self.assertIn("Corrupted JSON in loop_state.json", str(cm_a.exception))
        self.assertIn("refusing to reset existing state", str(cm_a.exception))
        # Verify the corrupted file was NOT overwritten
        self.assertEqual(state_file.read_text(encoding="utf-8"), corrupted_raw)

        # Case B: Valid JSON but corrupted schema (`processed_receipts` is not a list)
        bad_schema_raw = json.dumps(
            {
                "schema_version": "gemini_notebook_loop_state_v1",
                "processed_receipts": "CORRUPTED_STRING",
                "next_topics_queue": [],
                "open_unknowns": [],
            }
        )
        state_file.write_text(bad_schema_raw, encoding="utf-8")
        with self.assertRaises(ValueError) as cm_b:
            bridge.process_receipt_data(make_sample_receipt(), root=self.repo_root, apply=True)
        self.assertIn("Corrupted loop_state.json", str(cm_b.exception))
        self.assertIn("'processed_receipts' must be a list", str(cm_b.exception))
        self.assertEqual(state_file.read_text(encoding="utf-8"), bad_schema_raw)

    def test_06_intentional_failures_and_safety_boundaries(self):
        # 1. Refusing write on `main` branch
        subprocess.run(
            ["git", "-C", str(self.repo_root), "checkout", "main"], check=True, capture_output=True
        )
        with self.assertRaisesRegex(ValueError, "Refusing detached/default-branch write"):
            bridge.process_receipt_data(make_sample_receipt(), root=self.repo_root, apply=True)

        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo_root),
                "checkout",
                "feature/gemini-notebook-research-loop-20261016",
            ],
            check=True,
            capture_output=True,
        )

        # 2. Refusing write when origin points to forbidden repository
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo_root),
                "remote",
                "set-url",
                "origin",
                "https://github.com/kamiyusense/multi-ai-council-phase0.git",
            ],
            check=True,
            capture_output=True,
        )
        with self.assertRaisesRegex(ValueError, "Unexpected git origin: refusing write"):
            bridge.process_receipt_data(
                make_sample_receipt(),
                root=self.repo_root,
                apply=True,
                check_remote_branches=False,
            )

        # 3. Refusing stale remotes when `git fetch` fails and `allow_stale_remotes=False`
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo_root),
                "remote",
                "set-url",
                "origin",
                (Path(self.tmp_dir.name) / "nonexistent" / "kamiyusense" / "ai-video-research.git").as_posix(),
            ],
            check=True,
            capture_output=True,
        )
        with self.assertRaisesRegex(
            ValueError, "Failed to fetch fresh remote refs from origin"
        ):
            bridge.process_receipt_data(
                make_sample_receipt(),
                root=self.repo_root,
                apply=True,
                check_remote_branches=True,
                allow_stale_remotes=False,
            )

        # Restore valid origin
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo_root),
                "remote",
                "set-url",
                "origin",
                self.remote_bare.as_posix(),
            ],
            check=True,
            capture_output=True,
        )

    def test_07_git_commit_push_readback_and_divergence_stop(self):
        receipt = make_sample_receipt()
        with redirect_stdout(io.StringIO()):
            _, touched = bridge.process_receipt_data(
                data=receipt,
                root=self.repo_root,
                apply=True,
                sync_index=True,
            )
        git_ev = bridge.verify_and_push_git(
            root=self.repo_root,
            commit_message="test: commit, push to bare origin, and verify remote readback",
            do_push=True,
            touched_paths=touched,
        )
        self.assertTrue(git_ev["committed"])
        self.assertTrue(git_ev["pushed"])
        self.assertTrue(git_ev["readback_verified"])
        self.assertEqual(git_ev["github_write_status"], "PUSHED_AND_READBACK_VERIFIED")
        self.assertEqual(git_ev["notebook_sync_status"], "NOT_SYNCED_FROM_GITHUB")
        self.assertEqual(git_ev["head_sha"], git_ev["remote_head_sha"])

        # Simulate concurrent remote push -> must stop safely without overwriting
        other_clone = Path(self.tmp_dir.name) / "other_clone_diverge"
        subprocess.run(
            [
                "git",
                "clone",
                "-b",
                "feature/gemini-notebook-research-loop-20261016",
                self.remote_bare.as_posix(),
                str(other_clone),
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(other_clone), "config", "user.email", "other@example.com"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(other_clone), "config", "user.name", "Other"],
            check=True,
            capture_output=True,
        )
        (other_clone / "CONCURRENT.md").write_text("concurrent remote change\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(other_clone), "add", "CONCURRENT.md"], check=True, capture_output=True
        )
        subprocess.run(
            ["git", "-C", str(other_clone), "commit", "-m", "Remote concurrent commit"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(other_clone),
                "push",
                "origin",
                "feature/gemini-notebook-research-loop-20261016",
            ],
            check=True,
            capture_output=True,
        )

        receipt2 = make_sample_receipt(
            checked_at="2026-10-19",
            videos=[
                {
                    "video_id": "9bZkp7q19f0",
                    "title": "Second Video Test",
                    "url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
                    "published_at": "2026-10-15",
                    "summary_ja": "リモート競合時の安全停止テスト用データ。",
                    "source_scope": "Transcript",
                    "claims": [],
                    "notebook_source_id": "src_019",
                    "notebook_readback": "PASS",
                    "changes": ["NEW"],
                }
            ],
        )
        with redirect_stdout(io.StringIO()):
            _, touched2 = bridge.process_receipt_data(
                data=receipt2,
                root=self.repo_root,
                apply=True,
                sync_index=True,
            )
        with self.assertRaisesRegex(ValueError, "is ahead by 1 commit"):
            bridge.verify_and_push_git(
                root=self.repo_root,
                commit_message="should stop before overwriting diverged remote",
                do_push=True,
                touched_paths=touched2,
            )

    def test_08_cloud_payload_env_and_inbox_discovery(self):
        # Verify cloud workflow_dispatch / repository_dispatch payload ingestion via --payload-env
        sample_md = "Gemini Cloud Output:\n```json\n" + json.dumps(make_sample_receipt(), ensure_ascii=False) + "\n```"
        os.environ["TEST_CLOUD_RECEIPT_PAYLOAD"] = sample_md
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = bridge.main(["--payload-env", "TEST_CLOUD_RECEIPT_PAYLOAD", "--no-remote-dedup"])
            self.assertEqual(rc, 0)
            out_json = json.loads(buf.getvalue().strip().splitlines()[-1])
            self.assertEqual(out_json["mode"], "PREVIEW")
            self.assertEqual(out_json["new_records"], 1)
            self.assertEqual(out_json["notebook_sync_status"], "NOT_SYNCED_FROM_GITHUB")
        finally:
            os.environ.pop("TEST_CLOUD_RECEIPT_PAYLOAD", None)

    def test_09_python_js_cross_language_contract_and_output_parity(self):
        """Concern A: Verify 100% byte-for-byte parity between Python and GAS (JavaScript) implementations."""
        gas_path = (ROOT / "automation" / "gemini-notebook" / "cloud_relay_gas.js").as_posix()
        contract_path = ROOT / "automation" / "gemini-notebook" / "contract_spec_v1.json"
        contract_json = json.loads(contract_path.read_text(encoding="utf-8"))

        sample_receipt = make_sample_receipt()
        sample_video = sample_receipt["videos"][0]
        registry = json.loads((self.repo_root / "registry.json").read_text(encoding="utf-8"))
        local_map = bridge.collect_local_research_videos(root=self.repo_root)
        remote_map, freshness = bridge.collect_remote_branch_videos(root=self.repo_root)
        loop_state = bridge.default_initial_loop_state()
        loop_state["last_updated"] = "2026-10-17"

        # Verify forbidden key rejection in Python
        bad_forbidden = make_sample_receipt()
        bad_forbidden["videos"][0]["transcript"] = "Full verbatim transcript text not allowed"
        with self.assertRaisesRegex(ValueError, "Forbidden key in receipt payload"):
            bridge.validate(bad_forbidden)

        node_script = f"""
const gas = require({json.dumps(gas_path)});
const sampleReceipt = {json.dumps(sample_receipt, ensure_ascii=False)};
const sampleVideo = {json.dumps(sample_video, ensure_ascii=False)};
const registry = {json.dumps(registry, ensure_ascii=False)};
const localMap = {json.dumps(local_map, ensure_ascii=False)};
const remoteMap = {json.dumps(remote_map, ensure_ascii=False)};
const loopState = {json.dumps(loop_state, ensure_ascii=False)};
const badForbidden = {json.dumps(bad_forbidden, ensure_ascii=False)};

let forbiddenRejected = false;
try {{
  gas.validateReceipt(badForbidden);
}} catch (e) {{
  if (String(e.message).includes("Forbidden key in receipt payload")) {{
    forbiddenRejected = true;
  }}
}}

const out = {{
  contract: gas.CONTRACT_SPEC_V1,
  digest: gas.computeReceiptDigest(sampleReceipt),
  researchMd: gas.renderResearchMarkdown(sampleVideo, sampleReceipt.checked_at),
  deltaMd: gas.renderDeltaSection(sampleVideo, sampleReceipt.checked_at),
  indexMd: gas.renderGitHubKnowledgeIndexExportMd(registry, localMap, remoteMap, loopState, {json.dumps(freshness)}),
  forbiddenRejected: forbiddenRejected,
}};
process.stdout.write(JSON.stringify(out));
"""
        res = subprocess.run(
            ["node", "-e", node_script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        js_out = json.loads(res.stdout)

        self.assertEqual(js_out["contract"], contract_json)
        self.assertTrue(js_out["forbiddenRejected"])
        self.assertEqual(js_out["digest"], bridge.compute_receipt_digest(sample_receipt))
        self.assertEqual(
            js_out["researchMd"],
            bridge.render(sample_video, sample_receipt["checked_at"]),
        )
        self.assertEqual(
            js_out["deltaMd"],
            bridge.render_delta_section(sample_video, sample_receipt["checked_at"]),
        )
        self.assertEqual(
            js_out["indexMd"],
            bridge.render_github_knowledge_index_export_md(
                registry, local_map, remote_map, loop_state, freshness
            ),
        )

    def test_10_gas_mock_atomic_commit_concurrency_conflict_and_drive_self_healing(self):
        """Concerns B, C, D: Test GAS Direct Atomic Commit, LockService, Branch Cache, 422 Conflict, and Drive Self-Healing."""
        gas_path = (ROOT / "automation" / "gemini-notebook" / "cloud_relay_gas.js").as_posix()
        sample_receipt = make_sample_receipt()

        node_test = f"""
const crypto = require("crypto");
const gas = require({json.dumps(gas_path)});
const sampleReceipt = {json.dumps(sample_receipt, ensure_ascii=False)};

// In-memory mock GitHub server + Drive + Docs + Properties + Lock
function createMockEnvironment() {{
  const store = {{}};
  let lockAvailable = true;
  let simulateDriveFailure = false;
  let simulate422Conflict = false;
  let remoteTreeApiCalls = 0;
  let driveDocContent = "OLD_INDEX_CONTENT";
  let driveDocTitle = "GitHub_Knowledge_Index_Export_Mirror";

  const blobs = {{}};
  function putBlob(text) {{
    const sha = crypto.createHash("sha1").update(text, "utf8").digest("hex");
    blobs[sha] = Buffer.from(text, "utf8").toString("base64");
    return sha;
  }}

  const initialRegistry = {{
    schema_version: 1,
    repository: "kamiyusense/ai-video-research",
    records: [{{
      record_id: "youtube:lC5jxpYmatE",
      video_id: "lC5jxpYmatE",
      canonical_url: "https://www.youtube.com/watch?v=lC5jxpYmatE",
      research_path: "research/2026-10-10-lC5jxpYmatE-ai-techniques.md",
      status: "RESEARCH_RECORDED"
    }}]
  }};
  const regSha = putBlob(JSON.stringify(initialRegistry, null, 2) + "\\n");

  const parallelRegistry = JSON.parse(JSON.stringify(initialRegistry));
  parallelRegistry.records.push({{
    record_id: "youtube:ZjUJ-35acaU",
    video_id: "ZjUJ-35acaU",
    canonical_url: "https://www.youtube.com/watch?v=ZjUJ-35acaU",
    research_path: "research/2026-10-10-ZjUJ-35acaU-notebooklm.md",
    status: "REVIEWED_PARTIAL"
  }});
  const parallelRegSha = putBlob(JSON.stringify(parallelRegistry, null, 2) + "\\n");

  const trees = {{
    "tree_initial": [{{ path: "registry.json", type: "blob", sha: regSha }}],
    "tree_parallel": [{{ path: "registry.json", type: "blob", sha: parallelRegSha }}]
  }};
  const commits = {{
    "commit_initial": {{ sha: "commit_initial", tree: {{ sha: "tree_initial" }} }},
    "commit_parallel": {{ sha: "commit_parallel", tree: {{ sha: "tree_parallel" }} }}
  }};
  let targetHeadSha = "commit_initial";

  const inboxFiles = [];

  const scriptProperties = {{
    getProperty: (k) => store[k] || null,
    setProperty: (k, v) => {{ store[k] = String(v); }}
  }};

  const lockService = {{
    getScriptLock: () => ({{
      tryLock: () => lockAvailable,
      releaseLock: () => {{}}
    }})
  }};

  const driveApp = {{
    getFolderById: () => ({{
      getFiles: () => {{
        let idx = 0;
        return {{
          hasNext: () => idx < inboxFiles.length,
          next: () => inboxFiles[idx++]
        }};
      }}
    }})
  }};

  const documentApp = {{
    openById: (id) => {{
      if (id === "EXPORT_DOC_123" && simulateDriveFailure) {{
        throw new Error("Simulated transient Google Docs API outage");
      }}
      const inboxDoc = inboxFiles.find((f) => f.id === id);
      if (inboxDoc) {{
        return {{ getName: () => inboxDoc.name, getBody: () => ({{ getText: () => inboxDoc.text }}) }};
      }}
      return {{
        getName: () => driveDocTitle,
        getBody: () => ({{
          setText: (t) => {{ driveDocContent = t; }}
        }}),
        saveAndClose: () => {{}}
      }};
    }}
  }};

  const urlFetchApp = {{
    fetch: (url, opts) => {{
      const method = (opts.method || "get").toLowerCase();
      const body = opts.payload ? JSON.parse(opts.payload) : null;
      const makeRes = (code, obj) => ({{
        getResponseCode: () => code,
        getContentText: () => (typeof obj === "string" ? obj : JSON.stringify(obj))
      }});

      if (url.includes("/branches?per_page=100")) {{
        return makeRes(200, [
          {{ name: "main", protected: true, commit: {{ sha: "commit_main" }} }},
          {{ name: "feature/gemini-notebook-research-loop-20261016", protected: false, commit: {{ sha: targetHeadSha }} }},
          {{ name: "research/video08-mock", protected: false, commit: {{ sha: "commit_parallel" }} }}
        ]);
      }}
      if (url.includes("/git/commits/") && method === "get") {{
        const cSha = url.split("/git/commits/")[1];
        return makeRes(200, commits[cSha]);
      }}
      if (url.includes("/git/trees/") && method === "get") {{
        const tSha = url.split("/git/trees/")[1].split("?")[0];
        // Issue 3 verification: strictly reject commit SHAs passed to /git/trees/
        if (tSha.startsWith("commit_")) {{
          return makeRes(404, {{ message: "GitHub /git/trees/ requires tree_sha, not commit_sha: " + tSha }});
        }}
        if (tSha === "tree_parallel") {{
          remoteTreeApiCalls += 1;
        }}
        return makeRes(200, {{ sha: tSha, truncated: false, tree: trees[tSha] || [] }});
      }}
      if (url.includes("/git/blobs/") && method === "get") {{
        const bSha = url.split("/git/blobs/")[1];
        return makeRes(200, {{ sha: bSha, content: blobs[bSha], encoding: "base64" }});
      }}
      if (url.endsWith("/git/blobs") && method === "post") {{
        const newSha = putBlob(body.content);
        return makeRes(201, {{ sha: newSha }});
      }}
      if (url.endsWith("/git/trees") && method === "post") {{
        const baseItems = JSON.parse(JSON.stringify(trees[body.base_tree] || []));
        const byPath = {{}};
        baseItems.forEach((it) => {{ byPath[it.path] = it; }});
        body.tree.forEach((it) => {{ byPath[it.path] = {{ path: it.path, type: "blob", sha: it.sha }}; }});
        const newTreeSha = "tree_" + Object.keys(trees).length;
        trees[newTreeSha] = Object.values(byPath);
        return makeRes(201, {{ sha: newTreeSha }});
      }}
      if (url.endsWith("/git/commits") && method === "post") {{
        const newCommitSha = "commit_" + Object.keys(commits).length;
        commits[newCommitSha] = {{ sha: newCommitSha, tree: {{ sha: body.tree }}, parents: body.parents }};
        return makeRes(201, {{ sha: newCommitSha }});
      }}
      if (url.includes("/git/refs/heads/") && method === "patch") {{
        if (simulate422Conflict) {{
          return makeRes(422, {{ message: "Update is not a fast forward" }});
        }}
        targetHeadSha = body.sha;
        return makeRes(200, {{ object: {{ sha: targetHeadSha }} }});
      }}
      if (url.includes("/git/refs/heads/") && method === "get") {{
        return makeRes(200, {{ object: {{ sha: targetHeadSha }} }});
      }}
      return makeRes(404, {{ message: "Not found: " + url }});
    }}
  }};

  store["GITHUB_FINE_GRAINED_PAT"] = "ghp_mock_token";
  store["DRIVE_INBOX_FOLDER_ID"] = "FOLDER_123";
  store["DRIVE_EXPORT_DOC_ID"] = "EXPORT_DOC_123";
  store["TARGET_GITHUB_BRANCH"] = "feature/gemini-notebook-research-loop-20261016";

  return {{
    store,
    inboxFiles,
    setLock: (v) => {{ lockAvailable = v; }},
    setSimulateDriveFailure: (v) => {{ simulateDriveFailure = v; }},
    setSimulate422Conflict: (v) => {{ simulate422Conflict = v; }},
    getRemoteTreeApiCalls: () => remoteTreeApiCalls,
    getDriveDocContent: () => driveDocContent,
    getTargetHeadSha: () => targetHeadSha,
    overrides: {{ scriptProperties, lockService, driveApp, documentApp, urlFetchApp }}
  }};
}}

const env = createMockEnvironment();

// 1. Test LockService contention
env.setLock(false);
const lockRes = gas.relayDriveReceiptsToGitHub(env.overrides);
if (lockRes.status !== "SKIPPED_CONCURRENT_LOCK_HELD") {{
  throw new Error("Expected SKIPPED_CONCURRENT_LOCK_HELD, got " + JSON.stringify(lockRes));
}}
env.setLock(true);

// 2. Test forbidden key rejection + partial Drive failure on valid receipt (Run 1)
const badReceipt = JSON.parse(JSON.stringify(sampleReceipt));
badReceipt.videos[0].raw_transcript = "Forbidden full transcript";
env.inboxFiles.push({{
  id: "DOC_BAD",
  name: "bad_receipt.json",
  getMimeType: () => "text/plain",
  getName: () => "bad_receipt.json",
  getBlob: () => ({{ getDataAsString: () => JSON.stringify(badReceipt) }})
}});
env.inboxFiles.push({{
  id: "DOC_GOOD",
  name: "good_receipt.md",
  getMimeType: () => "application/vnd.google-apps.document",
  getName: () => "good_receipt.md",
  getId: () => "DOC_GOOD",
  text: "```json\\n" + JSON.stringify(sampleReceipt) + "\\n```"
}});

env.setSimulateDriveFailure(true);
const run1 = gas.relayDriveReceiptsToGitHub(env.overrides);
const callsAfterRun1 = env.getRemoteTreeApiCalls();

// 3. Run 2: Drive is now healthy -> must NOT create a duplicate GitHub commit, must reuse GitHub SSOT remote_branch_cache (0 extra remote tree calls), and MUST self-heal Drive export Doc!
env.setSimulateDriveFailure(false);
const headAfterRun1 = env.getTargetHeadSha();
const run2 = gas.relayDriveReceiptsToGitHub(env.overrides);
const callsAfterRun2 = env.getRemoteTreeApiCalls();
const headAfterRun2 = env.getTargetHeadSha();

// 4. Run 3: Simulate 422 branch conflict on a new receipt
const receiptConflict = JSON.parse(JSON.stringify(sampleReceipt));
receiptConflict.checked_at = "2026-10-19";
receiptConflict.videos[0].video_id = "9bZkp7q19f0";
receiptConflict.videos[0].url = "https://www.youtube.com/watch?v=9bZkp7q19f0";
env.inboxFiles.length = 0;
env.inboxFiles.push({{
  id: "DOC_CONFLICT",
  name: "conflict_receipt.json",
  getMimeType: () => "text/plain",
  getName: () => "conflict_receipt.json",
  getBlob: () => ({{ getDataAsString: () => JSON.stringify(receiptConflict) }})
}});
env.setSimulate422Conflict(true);
const run3 = gas.relayDriveReceiptsToGitHub(env.overrides);

process.stdout.write(JSON.stringify({{
  run1,
  run2,
  run3,
  callsAfterRun1,
  callsAfterRun2,
  headAfterRun1,
  headAfterRun2,
  driveContentHealed: env.getDriveDocContent().includes("dQw4w9WgXcQ")
}}));
"""
        res = subprocess.run(
            ["node", "-e", node_test],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        out = json.loads(res.stdout)

        # Verify Run 1 results: bad receipt rejected in memory; good receipt committed atomically; Drive failure recorded as pending
        r1_reports = out["run1"]["relayReport"]
        self.assertEqual(r1_reports[0]["status"], "REJECTED_VALIDATION_BEFORE_GITHUB_WRITE")
        self.assertIn("Forbidden key", r1_reports[0]["error"])
        self.assertEqual(r1_reports[1]["status"], "COMMITTED_AND_READBACK_VERIFIED")
        self.assertEqual(r1_reports[1]["githubWriteStatus"], "PUSHED_AND_READBACK_VERIFIED")
        self.assertEqual(
            r1_reports[1]["driveSyncStatus"],
            "DRIVE_UPDATE_FAILED_WILL_RECONCILE_NEXT_RUN",
        )
        self.assertTrue(r1_reports[1]["securityPosture"]["mainBranchServerProtected"])
        self.assertLess(out["run1"]["scriptPropertyBytesUsed"], 1000)

        # Verify Run 2 results: no duplicate GitHub commit, remote_branch_cache reused from GitHub loop_state.json (0 extra remote tree calls), and Drive Doc self-healed!
        self.assertEqual(out["headAfterRun1"], out["headAfterRun2"])
        self.assertEqual(out["callsAfterRun1"], 1)
        self.assertEqual(out["callsAfterRun2"], 1)
        r2_reports = out["run2"]["relayReport"]
        self.assertEqual(
            r2_reports[1]["status"], "SKIP_DUPLICATE_ALREADY_COMMITTED_ON_GITHUB"
        )
        self.assertEqual(
            out["run2"]["driveReconciliation"]["status"],
            "RECONCILED_FROM_GITHUB_SSOT",
        )
        self.assertTrue(out["driveContentHealed"])

        # Verify Run 3 results: 422 branch conflict halts safely without overwrite or retry
        r3_reports = out["run3"]["relayReport"]
        self.assertEqual(
            r3_reports[0]["status"],
            "STOPPED_ON_BRANCH_CONFLICT_422_NO_OVERWRITE",
        )
        self.assertEqual(r3_reports[0]["httpCode"], 422)

    def test_11_pagination_truncated_tree_partial_scan_continuation_and_value_patterns(self):
        """Issues 1-5: Verify 9KB ScriptProperties bound, /branches pagination, tree.truncated stop, multi-run >25 blob scan continuation, and secret/transcript value pattern rejection."""
        gas_path = (ROOT / "automation" / "gemini-notebook" / "cloud_relay_gas.js").as_posix()
        sample_receipt = make_sample_receipt()

        # 1. Verify value-level secret and transcript pattern rejection in Python
        bad_secret = make_sample_receipt()
        bad_secret["videos"][0]["summary_ja"] = "漏洩トークン ghp_1234567890abcdefghijklmnopqrstuv の混入テスト"
        with self.assertRaisesRegex(ValueError, "Forbidden content pattern \\(GITHUB_TOKEN\\)"):
            bridge.validate(bad_secret)

        bad_srt = make_sample_receipt()
        bad_srt["videos"][0]["claims"][0]["text"] = "00:01:20,000 --> 00:01:25,000 字幕タイムコードの直接転載"
        with self.assertRaisesRegex(ValueError, "Forbidden content pattern \\(SUBTITLE_TIMECODE_BLOCK\\)"):
            bridge.validate(bad_srt)

        bad_newlines = make_sample_receipt()
        bad_newlines["videos"][0]["summary_ja"] = "行1\n行2\n行3\n行4\n行5"
        with self.assertRaisesRegex(ValueError, "Summary contains too many line breaks"):
            bridge.validate(bad_newlines)

        node_test = f"""
const crypto = require("crypto");
const gas = require({json.dumps(gas_path)});
const sampleReceipt = {json.dumps(sample_receipt, ensure_ascii=False)};

// A. Verify value-level pattern rejection in JS
const badSecret = JSON.parse(JSON.stringify(sampleReceipt));
badSecret.videos[0].summary_ja = "漏洩トークン ghp_1234567890abcdefghijklmnopqrstuv の混入テスト";
let jsSecretRejected = false;
try {{ gas.validateReceipt(badSecret); }} catch (e) {{
  if (String(e.message).includes("GITHUB_TOKEN")) jsSecretRejected = true;
}}

const badSrt = JSON.parse(JSON.stringify(sampleReceipt));
badSrt.videos[0].claims[0].text = "00:01:20,000 --> 00:01:25,000 字幕タイムコード";
let jsSrtRejected = false;
try {{ gas.validateReceipt(badSrt); }} catch (e) {{
  if (String(e.message).includes("SUBTITLE_TIMECODE_BLOCK")) jsSrtRejected = true;
}}

const badNewlines = JSON.parse(JSON.stringify(sampleReceipt));
badNewlines.videos[0].summary_ja = "1\\n2\\n3\\n4\\n5";
let jsNewlinesRejected = false;
try {{ gas.validateReceipt(badNewlines); }} catch (e) {{
  if (String(e.message).includes("too many line breaks")) jsNewlinesRejected = true;
}}

// B. Verify saveBoundedRelayState trims oversized state to <= 7500 bytes (well under 9KB)
const propStore = {{}};
const mockProps = {{
  getProperty: (k) => propStore[k] || null,
  setProperty: (k, v) => {{ propStore[k] = String(v); }}
}};
const hugeState = {{
  schemaVersion: "gas_relay_compact_state_v2",
  lastGitHubCommitSha: "a".repeat(40),
  lastDriveSyncedCommitSha: "b".repeat(40),
  pendingDriveSync: false,
  recentNoOpDigests: Array.from({{ length: 120 }}, (_, i) => crypto.createHash("sha256").update("noop_" + i).digest("hex")),
  haltedReceipts: {{}},
  partialScanProgress: {{}}
}};
for (let i = 0; i < 60; i++) {{
  hugeState.haltedReceipts["halted_" + i + "_" + "x".repeat(40)] = {{ haltedAt: "2026-10-17T00:00:00Z", httpCode: 500, status: "ERR_" + "y".repeat(80) }};
}}
const boundedBytes = gas.saveBoundedRelayState(mockProps, hugeState);

// C. Build mock environment for:
//    - 2-page /branches pagination (100 branches on page 1, 1 branch on page 2 containing 30 notes/*.md files)
//    - Multi-run partial scan continuation (Run 1 scans 25 blobs and pauses; Run 2 scans remaining 5 blobs, finds dQw4w9WgXcQ in note_28.md, and deduplicates it!)
//    - Truncated tree error stop when simulateTruncatedTree = true
let simulateTruncatedTree = false;
const blobs = {{}};
function putBlob(text) {{
  const sha = crypto.createHash("sha1").update(text, "utf8").digest("hex");
  blobs[sha] = Buffer.from(text, "utf8").toString("base64");
  return sha;
}}

const initialRegistry = {{
  schema_version: 1,
  repository: "kamiyusense/ai-video-research",
  records: []
}};
const regSha = putBlob(JSON.stringify(initialRegistry, null, 2) + "\\n");

// Create 30 notes/*.md on the page-2 remote branch; note_28.md references dQw4w9WgXcQ
const page2TreeItems = [{{ path: "registry.json", type: "blob", sha: regSha }}];
for (let i = 1; i <= 30; i++) {{
  const num = String(i).padStart(2, "0");
  const vidInNote = i === 28 ? "dQw4w9WgXcQ" : ("DummyVid0" + num);
  const bSha = putBlob("# Note " + num + "\\n\\n- video_id: `" + vidInNote + "`\\n");
  page2TreeItems.push({{ path: "notes/note_" + num + ".md", type: "blob", sha: bSha }});
}}

const trees = {{
  "tree_target": [{{ path: "registry.json", type: "blob", sha: regSha }}],
  "tree_empty_branch": [{{ path: "registry.json", type: "blob", sha: regSha }}],
  "tree_page2": page2TreeItems
}};
const commits = {{
  "commit_target": {{ sha: "commit_target", tree: {{ sha: "tree_target" }} }},
  "commit_empty": {{ sha: "commit_empty", tree: {{ sha: "tree_empty_branch" }} }},
  "commit_page2": {{ sha: "commit_page2", tree: {{ sha: "tree_page2" }} }}
}};

const page1Branches = [
  {{ name: "main", protected: true, commit: {{ sha: "commit_main" }} }},
  {{ name: "feature/gemini-notebook-research-loop-20261016", protected: false, commit: {{ sha: "commit_target" }} }}
];
// Fill page 1 to exactly 100 items using main (forbidden/ignored) so pagination triggers page 2 cleanly
while (page1Branches.length < 100) {{
  page1Branches.push({{ name: "main", protected: true, commit: {{ sha: "commit_main" }} }});
}}
const page2Branches = [
  {{ name: "research/page2-deep-notes", protected: false, commit: {{ sha: "commit_page2" }} }}
];

const store2 = {{
  GITHUB_FINE_GRAINED_PAT: "ghp_mock_token",
  DRIVE_INBOX_FOLDER_ID: "FOLDER_123",
  TARGET_GITHUB_BRANCH: "feature/gemini-notebook-research-loop-20261016"
}};
const props2 = {{
  getProperty: (k) => store2[k] || null,
  setProperty: (k, v) => {{ store2[k] = String(v); }}
}};
const inboxFiles2 = [{{
  id: "DOC_1",
  name: "receipt.json",
  getMimeType: () => "text/plain",
  getName: () => "receipt.json",
  getBlob: () => ({{ getDataAsString: () => JSON.stringify(sampleReceipt) }})
}}];
const driveApp2 = {{
  getFolderById: () => ({{
    getFiles: () => {{
      let idx = 0;
      return {{ hasNext: () => idx < inboxFiles2.length, next: () => inboxFiles2[idx++] }};
    }}
  }})
}};
const lockService2 = {{ getScriptLock: () => ({{ tryLock: () => true, releaseLock: () => {{}} }}) }};

let pagesFetched = [];
const urlFetchApp2 = {{
  fetch: (url, opts) => {{
    const method = (opts.method || "get").toLowerCase();
    const makeRes = (code, obj) => ({{
      getResponseCode: () => code,
      getContentText: () => JSON.stringify(obj)
    }});
    if (url.includes("/branches?per_page=100&page=1")) {{
      pagesFetched.push(1);
      return makeRes(200, page1Branches);
    }}
    if (url.includes("/branches?per_page=100&page=2")) {{
      pagesFetched.push(2);
      return makeRes(200, page2Branches);
    }}
    if (url.includes("/git/commits/") && method === "get") {{
      const cSha = url.split("/git/commits/")[1];
      return makeRes(200, commits[cSha]);
    }}
    if (url.includes("/git/trees/") && method === "get") {{
      const tSha = url.split("/git/trees/")[1].split("?")[0];
      if (tSha.startsWith("commit_")) {{
        return makeRes(404, {{ message: "Expected tree_sha, got commit_sha" }});
      }}
      return makeRes(200, {{ sha: tSha, truncated: simulateTruncatedTree, tree: trees[tSha] || [] }});
    }}
    if (url.includes("/git/blobs/") && method === "get") {{
      const bSha = url.split("/git/blobs/")[1];
      return makeRes(200, {{ sha: bSha, content: blobs[bSha], encoding: "base64" }});
    }}
    return makeRes(404, {{ message: "Unexpected URL: " + url }});
  }}
}};

const overrides2 = {{ scriptProperties: props2, lockService: lockService2, driveApp: driveApp2, urlFetchApp: urlFetchApp2 }};

// Run 1: Should scan first 25 blobs of research/page2-deep-notes and pause with 5 remaining!
const scanRun1 = gas.relayDriveReceiptsToGitHub(overrides2);

// Run 2: Should resume from blob #26, scan the remaining 5 blobs, find dQw4w9WgXcQ in note_28.md, and skip it!
const scanRun2 = gas.relayDriveReceiptsToGitHub(overrides2);

// Run 3: Simulate truncated Git tree -> must throw error refusing incomplete duplicate detection
simulateTruncatedTree = true;
let truncatedError = "";
try {{
  gas.relayDriveReceiptsToGitHub(overrides2);
}} catch (e) {{
  truncatedError = String(e.message || e);
}}

process.stdout.write(JSON.stringify({{
  jsSecretRejected,
  jsSrtRejected,
  jsNewlinesRejected,
  boundedBytes,
  pagesFetched,
  scanRun1,
  scanRun2,
  truncatedError
}}));
"""
        res = subprocess.run(
            ["node", "-e", node_test],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        out = json.loads(res.stdout)

        self.assertTrue(out["jsSecretRejected"])
        self.assertTrue(out["jsSrtRejected"])
        self.assertTrue(out["jsNewlinesRejected"])
        self.assertLessEqual(out["boundedBytes"], 7500)
        self.assertIn(1, out["pagesFetched"])
        self.assertIn(2, out["pagesFetched"])

        # Run 1 paused safely because 5 of the 30 notes/*.md on page 2 were still unscanned
        self.assertEqual(
            out["scanRun1"]["status"],
            "PAUSED_INCOMPLETE_DEDUP_SCAN_CONTINUES_NEXT_RUN",
        )
        self.assertFalse(out["scanRun1"]["dedupScanComplete"])
        self.assertEqual(out["scanRun1"]["remainingUnscannedFiles"], 5)

        # Run 2 resumed, finished the remaining 5 files, and detected dQw4w9WgXcQ in notes/note_28.md on origin/research/page2-deep-notes!
        self.assertEqual(out["scanRun2"]["status"], "COMPLETED")
        self.assertTrue(out["scanRun2"]["dedupScanComplete"])
        r2_rep = out["scanRun2"]["relayReport"][0]
        self.assertEqual(
            r2_rep["status"], "SKIPPED_ALL_VIDEOS_DUPLICATE_OR_UNVERIFIED"
        )
        self.assertEqual(
            r2_rep["skipped"][0]["reason"], "SKIP_EXISTING_REMOTE_BRANCH"
        )
        self.assertIn(
            "origin/research/page2-deep-notes",
            r2_rep["skipped"][0]["branches"],
        )
        self.assertEqual(
            r2_rep["skipped"][0]["detected_via"], "body:notes/note_28.md"
        )

        # Run 3 halted immediately when Git Trees API returned truncated: true
        self.assertIn("is truncated", out["truncatedError"])
        self.assertIn("refusing incomplete duplicate detection", out["truncatedError"])

    def test_12_v06_chapters_detailed_findings_timestamp_provenance_and_qa_search(self):
        """v0.6: Verify chapters, detailed_findings_ja, related_records, timestamp_source provenance, and query_research.py Q&A."""
        gas_path = (ROOT / "automation" / "gemini-notebook" / "cloud_relay_gas.js").as_posix()
        query_mod_path = ROOT / "automation" / "gemini-notebook" / "query_research.py"
        q_spec = importlib.util.spec_from_file_location("query_research", query_mod_path)
        query_mod = importlib.util.module_from_spec(q_spec)
        q_spec.loader.exec_module(query_mod)

        rich_receipt = make_sample_receipt()
        rich_video = rich_receipt["videos"][0]
        rich_video["detailed_findings_ja"] = (
            "1. **ハーネス設計の核心（状態管理と決定論的ガードの分離）**:\n"
            "   - LLMの推論ループに直接ファイル書込みや外部送信を委ねるのではなく、PreToolUse / PostToolUse のHooksで決定論的検証を挟む。\n"
            "2. **スキル設計で起きやすい失敗例と対策**:\n"
            "   - 常設ルールやスキルを無秩序に増やすと、どのスキルを呼ぶべきかのメタデータ選択が衝突し、保守負担が増大する。\n"
            "   - 公式仕様（CONFIRMED_DOC）では `SKILL.md` 本文はオンデマンド遅延ロードされるため、トークン消費の主因は本文全量ではなく説明文の重複にある。\n"
            "3. **再利用手順**:\n"
            "   - 失敗時のリトライ上限（retry=0）とReadback確認をハーネス側で強制する。"
        )
        rich_video["chapters"] = [
            {
                "title": "ハーネスとは何か：モデル推論と状態管理・Hooksの役割分離",
                "start_seconds": 60,
                "end_seconds": 320,
                "summary_ja": "ハーネスの基本概念と、ツール実行前後にHooksを挟んで暴走や誤書込みを防ぐアーキテクチャを解説。",
                "timestamp_source": "YOUTUBE_CHAPTER_METADATA",
                "key_topics": ["ハーネス", "Harness", "Hooks", "状態管理"],
            },
            {
                "title": "スキル設計の失敗例：スキルの増やしすぎ・重複とメタデータ競合",
                "start_seconds": 320,
                "end_seconds": 680,
                "summary_ja": "スキルを無秩序に増やした際に起きる選択ミス・保守破綻の失敗例と、SKILL.md遅延読み込みの正しい仕様を解説。",
                "timestamp_source": "TIMESTAMPED_CAPTIONS",
                "key_topics": ["スキル", "Skill", "失敗例", "SKILL.md"],
            },
            {
                "title": "補足議論：時刻未確認の質疑応答パート",
                "start_seconds": None,
                "end_seconds": None,
                "summary_ja": "Notebookのテキストチャンクから抽出されたが秒単位の時刻根拠が未確認の補足パート。",
                "timestamp_source": "UNKNOWN",
                "key_topics": ["補足", "Q&A"],
            },
        ]
        rich_video["related_records"] = [
            {
                "target_id": "youtube:lC5jxpYmatE",
                "relation": "EXTENDS",
                "note": "動画研究05のHooks・Skill遅延読み込みの検証をハーネス実装パターンへ拡張",
            },
            {
                "target_id": "P006-U03",
                "relation": "RESOLVES_BACKLOG",
                "note": "反復操作を決定論的Hooksとスクリプトへ移行する判断基準を提供",
            },
        ]
        rich_video["claims"][0]["timestamp_source"] = "TIMESTAMPED_CAPTIONS"

        # 1. Validate and check 100% Python/JS output parity on rich v0.6 receipt
        bridge.validate(rich_receipt)
        py_md = bridge.render(rich_video, rich_receipt["checked_at"])
        py_delta_md = bridge.render_delta_section(rich_video, rich_receipt["checked_at"])

        # Verify verified chapter has &t=60s link, while UNKNOWN chapter has NO fake link
        self.assertIn(
            "[01:00〜05:20](https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=60s)",
            py_md,
        )
        self.assertIn(
            "- UNKNOWN | **補足議論：時刻未確認の質疑応答パート**",
            py_md,
        )

        # 2. Verify strict rejection of fabricated timestamps when timestamp_source == "UNKNOWN"
        bad_unknown_chapter = json.loads(json.dumps(rich_receipt))
        bad_unknown_chapter["videos"][0]["chapters"][2]["start_seconds"] = 700
        with self.assertRaisesRegex(
            ValueError,
            "Chapter with UNKNOWN timestamp_source cannot specify start_seconds/end_seconds",
        ):
            bridge.validate(bad_unknown_chapter)

        bad_verified_without_sec = json.loads(json.dumps(rich_receipt))
        bad_verified_without_sec["videos"][0]["chapters"][0]["start_seconds"] = None
        bad_verified_without_sec["videos"][0]["chapters"][0]["end_seconds"] = None
        with self.assertRaisesRegex(
            ValueError,
            "Chapter with verified timestamp_source must specify start_seconds",
        ):
            bridge.validate(bad_verified_without_sec)

        bad_claim_unknown_with_sec = json.loads(json.dumps(rich_receipt))
        bad_claim_unknown_with_sec["videos"][0]["claims"][0]["timestamp_source"] = "UNKNOWN"
        with self.assertRaisesRegex(
            ValueError,
            "Claim with UNKNOWN timestamp_source cannot specify timestamp_seconds",
        ):
            bridge.validate(bad_claim_unknown_with_sec)

        # 3. Verify Node.js (GAS) parity on validation and Markdown rendering
        node_script = f"""
const gas = require({json.dumps(gas_path)});
const richReceipt = {json.dumps(rich_receipt, ensure_ascii=False)};
const richVideo = richReceipt.videos[0];
const badUnknownChapter = {json.dumps(bad_unknown_chapter, ensure_ascii=False)};
const badVerifiedWithoutSec = {json.dumps(bad_verified_without_sec, ensure_ascii=False)};
const badClaimUnknownWithSec = {json.dumps(bad_claim_unknown_with_sec, ensure_ascii=False)};

gas.validateReceipt(richReceipt);

let err1 = false, err2 = false, err3 = false;
try {{ gas.validateReceipt(badUnknownChapter); }} catch (e) {{
  err1 = String(e.message).includes("Chapter with UNKNOWN timestamp_source cannot specify start_seconds/end_seconds");
}}
try {{ gas.validateReceipt(badVerifiedWithoutSec); }} catch (e) {{
  err2 = String(e.message).includes("Chapter with verified timestamp_source must specify start_seconds");
}}
try {{ gas.validateReceipt(badClaimUnknownWithSec); }} catch (e) {{
  err3 = String(e.message).includes("Claim with UNKNOWN timestamp_source cannot specify timestamp_seconds");
}}

process.stdout.write(JSON.stringify({{
  digest: gas.computeReceiptDigest(richReceipt),
  md: gas.renderResearchMarkdown(richVideo, richReceipt.checked_at),
  deltaMd: gas.renderDeltaSection(richVideo, richReceipt.checked_at),
  err1,
  err2,
  err3
}}));
"""
        res = subprocess.run(
            ["node", "-e", node_script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        js_out = json.loads(res.stdout)
        self.assertEqual(js_out["digest"], bridge.compute_receipt_digest(rich_receipt))
        self.assertEqual(js_out["md"], py_md)
        self.assertEqual(js_out["deltaMd"], py_delta_md)
        self.assertTrue(js_out["err1"])
        self.assertTrue(js_out["err2"])
        self.assertTrue(js_out["err3"])

        # 4. Apply rich v0.6 receipt to repo_root and run query_research.py Q&A pipeline
        with redirect_stdout(io.StringIO()):
            bridge.process_receipt_data(
                data=rich_receipt,
                root=self.repo_root,
                apply=True,
                sync_index=True,
            )

        catalog_path = (
            self.repo_root
            / "automation"
            / "gemini-notebook"
            / "state"
            / "video_knowledge_catalog.json"
        )
        catalog, _ = query_mod.build_video_knowledge_catalog(
            root=self.repo_root, write_path=catalog_path
        )
        self.assertTrue(catalog_path.exists())
        self.assertGreaterEqual(catalog["total_verified_chapters"], 2)

        # Q&A Test A: "ハーネスって何？どの動画のどこを見ればいい？"
        qa_harness = query_mod.answer_question(
            "ハーネスって何？どの動画のどこを見ればいい？", root=self.repo_root
        )
        self.assertIn(
            "CONCEPT_AND_BASICS", qa_harness["step1_intent_analysis"]["intents"]
        )
        self.assertIn(
            "VIDEO_LOCATOR", qa_harness["step1_intent_analysis"]["intents"]
        )
        top_seg_h = qa_harness["step5_and_6_recommended_video_segments"][0]
        self.assertEqual(top_seg_h["video_id"], "dQw4w9WgXcQ")
        self.assertIn(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=",
            top_seg_h["playback_url"],
        )

        # Q&A Test B: "前に調べたスキル設計の動画で、失敗例を話していた箇所を教えて"
        qa_skill_fail = query_mod.answer_question(
            "前に調べたスキル設計の動画で、失敗例を話していた箇所を教えて",
            root=self.repo_root,
        )
        self.assertIn(
            "FAILURE_AND_LIMITS", qa_skill_fail["step1_intent_analysis"]["intents"]
        )
        top_seg_s = qa_skill_fail["step5_and_6_recommended_video_segments"][0]
        self.assertEqual(
            top_seg_s["playback_url"],
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=320s",
        )
        self.assertEqual(top_seg_s["timestamp_source"], "TIMESTAMPED_CAPTIONS")
        md_response = query_mod.format_qa_response_markdown(qa_skill_fail)
        self.assertIn(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=320s", md_response
        )

        # Q&A Test C: Unresearched topic gap detection
        qa_gap = query_mod.answer_question(
            "量子暗号コンパイラのゼロ知識証明ベンチマークは？", root=self.repo_root
        )
        self.assertEqual(
            qa_gap["step4_gap_analysis"]["coverage_status"],
            "INSUFFICIENT_NEEDS_NEW_RESEARCH",
        )
        self.assertEqual(len(qa_gap["step2_matched_records"]), 0)

    def test_13_gemini_batch_handoff_normalization_and_remote_branch_consolidation(self):
        """Verify Gemini batch handoff JSON conversion, master index rejection, PART1/PART2 timestamp evidence separation, and remote branch consolidation."""
        # 1. Master index JSON without `videos` array is rejected
        master_index_json = json.dumps(
            {
                "receipt_version": "research_receipt_v1",
                "generated_at": "2026-10-17T10:50:00+09:00",
                "total_videos": 26,
                "split_files": ["PART1.json", "PART2.json"],
                "video_ids": ["sodTFSuV4zY", "ZjUJ-35acaU"],
            },
            ensure_ascii=False,
        )
        with self.assertRaisesRegex(ValueError, "Master index file"):
            bridge.extract_receipt_payload(master_index_json)

        # 2. Arithmetic mismatch in `timeline` (`01:40` != `seconds: 99`) is rejected
        bad_tl_json = json.dumps(
            {
                "receipt_version": "research_receipt_v1",
                "batch_part": "1/2",
                "generated_at": "2026-10-17T10:50:00+09:00",
                "videos": [
                    {
                        "number": "01",
                        "id": "ZgMrRA1Czlc",
                        "title": "Test Video",
                        "url": "https://www.youtube.com/watch?v=ZgMrRA1Czlc",
                        "publish_date": "2026-10-16",
                        "duration": "10:46",
                        "summary": "要約テスト",
                        "timeline": [
                            {
                                "start": "01:40",
                                "end": "02:00",
                                "seconds": 99,
                                "title": "不整合タイムスタンプ",
                                "link": "https://www.youtube.com/watch?v=ZgMrRA1Czlc&t=99s",
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        )
        with self.assertRaisesRegex(ValueError, "Timeline timestamp/seconds/link mismatch"):
            bridge.extract_receipt_payload(bad_tl_json)

        # 3. PART2 research-note-derived batch:
        #    - Uncorroborated/duration-mismatched video (`y2xCGyURl7Q`) gets `timestamp_source: "UNKNOWN"` and `start_seconds: None`
        #    - Remote-branch existing video (`ZjUJ-35acaU` on `origin/research/video08-mock`) gets `changes: ["UPDATED"]` and consolidates onto current branch!
        # First create the remote research markdown file on `origin/research/video08-mock`
        subprocess.run(
            ["git", "-C", str(self.repo_root), "checkout", "research/video08-mock"],
            check=True,
            capture_output=True,
        )
        (self.repo_root / "research" / "2026-10-10-ZjUJ-35acaU-notebooklm-youtube-extension.md").write_text(
            "# 動画08：YouTube to NotebookLM 拡張機能の一括収集（暫定研究）\n\n- video_id: ZjUJ-35acaU\n\n## 結論\n既存の暫定研究結論。\n",
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "-C", str(self.repo_root), "add", "research/2026-10-10-ZjUJ-35acaU-notebooklm-youtube-extension.md"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo_root), "commit", "-m", "Add video08 markdown on remote branch"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo_root), "push", "origin", "research/video08-mock:research/video08-mock"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo_root), "checkout", "feature/gemini-notebook-research-loop-20261016"],
            check=True,
            capture_output=True,
        )

        part2_sample_raw = json.dumps(
            {
                "receipt_version": "research_receipt_v1",
                "batch_part": "2/2",
                "batch_description": "Part 2: 過去調査14本 (No.13〜26)",
                "generated_at": "2026-10-17T10:50:00+09:00",
                "videos": [
                    {
                        "number": "13",
                        "id": "y2xCGyURl7Q",
                        "title": "Gemini 4 Argon一般公開とアーキテクチャ解説",
                        "url": "https://www.youtube.com/watch?v=y2xCGyURl7Q",
                        "channel": "AI技術速報",
                        "publish_date": "2026-10-05",
                        "duration": "24:15",
                        "research_date": "2026-10-16",
                        "summary": "A" * 315,
                        "key_technologies": ["Gemini 4 Argon", "Interactions API"],
                        "timeline": [
                            {
                                "start": "02:15",
                                "end": "05:40",
                                "seconds": 135,
                                "title": "モデルスペック",
                                "link": "https://www.youtube.com/watch?v=y2xCGyURl7Q&t=135s",
                            }
                        ],
                        "official_verification": {
                            "status": "VERIFIED",
                            "details": "Google DeepMind公式発表と一致。",
                        },
                        "constraints_and_notes": "レイテンシ注意。",
                        "future_applications": "非同期リファクタリング。",
                        "unknowns": "内部課金レート。",
                    },
                    {
                        "number": "25",
                        "id": "ZjUJ-35acaU",
                        "title": "【超便利】Google最強AI「NotebookLM」×「YouTube」の拡張機能が神！",
                        "url": "https://www.youtube.com/watch?v=ZjUJ-35acaU",
                        "channel": "mikimiki web スクール",
                        "publish_date": "2026-03-21",
                        "duration": "21:23",
                        "research_date": "2026-10-16",
                        "summary": "YouTube to NotebookLM拡張による一括インポートと6つの実践プロンプトを解説。",
                        "key_technologies": ["YouTube to NotebookLM", "Chrome拡張"],
                        "timeline": [
                            {
                                "start": "12:07",
                                "end": "14:43",
                                "seconds": 727,
                                "title": "ハンズオン④：複数動画横断の共通法則抽出",
                                "link": "https://www.youtube.com/watch?v=ZjUJ-35acaU&t=727s",
                            },
                            {
                                "start": "19:30",
                                "end": "21:23",
                                "seconds": 1170,
                                "title": "まとめ・動画ナレッジの資産化",
                                "link": "https://www.youtube.com/watch?v=ZjUJ-35acaU&t=1170s",
                            },
                        ],
                        "official_verification": {
                            "status": "VERIFIED",
                            "details": "Chrome拡張仕様と一致。",
                        },
                        "constraints_and_notes": "5時間制限注意。",
                        "future_applications": "一括登録と法則抽出。",
                        "unknowns": "拡張作者の保守方針。",
                    },
                ],
            },
            ensure_ascii=False,
        )

        normalized = bridge.extract_receipt_payload(part2_sample_raw)
        bridge.validate(normalized)
        v13 = normalized["videos"][0]
        v25 = normalized["videos"][1]
        self.assertLessEqual(len(v13["summary_ja"]), 300)
        self.assertIn("A" * 315, v13["detailed_findings_ja"])
        # v13 timestamp must be downgraded to UNKNOWN (no guessed playback link)
        self.assertEqual(v13["chapters"][0]["timestamp_source"], "UNKNOWN")
        self.assertIsNone(v13["chapters"][0]["start_seconds"])
        # v25 12:07 (727s) is corroborated by YT chapter 12:06 & GitHub record 727s -> verified!
        # v25 19:30 (1170s) is uncorroborated -> UNKNOWN!
        self.assertEqual(v25["chapters"][0]["start_seconds"], 727)
        self.assertNotEqual(v25["chapters"][0]["timestamp_source"], "UNKNOWN")
        self.assertEqual(v25["chapters"][1]["timestamp_source"], "UNKNOWN")
        self.assertIsNone(v25["chapters"][1]["start_seconds"])

        # Apply normalized PART2 sample and verify remote branch consolidation for ZjUJ-35acaU
        summary, _ = bridge.process_receipt_data(
            data=normalized,
            root=self.repo_root,
            apply=True,
            sync_index=True,
        )
        self.assertEqual(summary["new_records"], 1)
        self.assertEqual(summary["ids"], ["y2xCGyURl7Q"])
        self.assertEqual(summary["updated_records"], 1)
        self.assertEqual(summary["updated_ids"], ["ZjUJ-35acaU"])
        consolidated_md = (
            self.repo_root / "research" / "2026-10-10-ZjUJ-35acaU-notebooklm-youtube-extension.md"
        ).read_text(encoding="utf-8")
        self.assertIn("既存の暫定研究結論。", consolidated_md)
        self.assertIn("## 差分更新 (2026-10-17 / UPDATED)", consolidated_md)
        self.assertIn("https://www.youtube.com/watch?v=ZjUJ-35acaU&t=727s", consolidated_md)
        self.assertNotIn("https://www.youtube.com/watch?v=ZjUJ-35acaU&t=1170s", consolidated_md)


if __name__ == "__main__":
    unittest.main(verbosity=2)



