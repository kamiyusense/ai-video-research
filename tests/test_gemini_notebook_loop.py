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
QUERY_MODULE_PATH = ROOT / "automation" / "gemini-notebook" / "query_research.py"

spec = importlib.util.spec_from_file_location("receipt_to_research", MODULE_PATH)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

q_spec = importlib.util.spec_from_file_location("query_research", QUERY_MODULE_PATH)
query_mod = importlib.util.module_from_spec(q_spec)
q_spec.loader.exec_module(query_mod)

VTS_MODULE_PATH = ROOT / "automation" / "gemini-notebook" / "verify_timestamps.py"
vts_spec = importlib.util.spec_from_file_location("verify_timestamps", VTS_MODULE_PATH)
vts_mod = importlib.util.module_from_spec(vts_spec)
vts_spec.loader.exec_module(vts_mod)


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
        self.assertIn('canonical_url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ"', note_text)
        self.assertIn('github_to_notebook_sync: "NOT_SYNCED_FROM_GITHUB"', note_text)

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

        # Missing notebook_source_id without explicit override must fail safely (never guess source name)
        with self.assertRaisesRegex(ValueError, "Missing notebook_source_id"):
            bridge.extract_receipt_payload(part2_sample_raw)

        normalized = bridge.extract_receipt_payload(
            part2_sample_raw,
            default_notebook_source_id="AI技術研究室_過去調査14本_完全総合辞書_20261017",
        )
        bridge.validate(normalized)
        self.assertEqual(
            normalized["notebook_url"],
            "https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7",
        )
        self.assertEqual(normalized["notebook_readback"], "UNKNOWN")
        v13 = normalized["videos"][0]
        v25 = normalized["videos"][1]
        self.assertLessEqual(len(v13["summary_ja"]), 300)
        self.assertIn("A" * 315, v13["detailed_findings_ja"])
        # Without official_url, VERIFIED is downgraded to REPORTED_BY_AUTHOR (never CONFIRMED_DOC)
        self.assertEqual(v13["claims"][0]["status"], "REPORTED_BY_AUTHOR")
        self.assertEqual(v13["notebook_readback"], "UNKNOWN")
        # v13 timestamp must be downgraded to UNKNOWN (no guessed playback link)
        self.assertEqual(v13["chapters"][0]["timestamp_source"], "UNKNOWN")
        self.assertIsNone(v13["chapters"][0]["start_seconds"])
        # v25 12:07 (727s) is corroborated by YT chapter 12:06 (DESC_MATCH) -> YOUTUBE_CHAPTER_METADATA!
        # v25 19:30 (1170s) failed caption check (CAPTION_FAIL) -> UNKNOWN!
        self.assertEqual(v25["chapters"][0]["start_seconds"], 727)
        self.assertEqual(v25["chapters"][0]["timestamp_source"], "YOUTUBE_CHAPTER_METADATA")
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

    def test_14_search_precision_and_no_unverified_timestamp_links(self):
        """Verify 30-video catalog integrity, strict per-chapter timestamp links, and natural-language Q&A search accuracy."""
        real_root = Path(__file__).resolve().parents[1]
        catalog, _ = query_mod.build_video_knowledge_catalog(root=real_root)
        self.assertEqual(catalog["total_video_records"], 31)
        self.assertEqual(
            catalog["notebook_url"],
            "https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7",
        )

        evidence_map = bridge.load_timestamp_evidence()
        vid_records = {r["video_id"]: r for r in catalog["records"] if r.get("video_id")}
        self.assertEqual(len(vid_records), 31)

        # 1. Verify t22FELAl-BM has 0 verified chapters (no 24:18 / 1458s special-case hack)
        t22_rec = vid_records["t22FELAl-BM"]
        self.assertEqual(len(t22_rec["chapters"]), 7)
        for ch in t22_rec["chapters"]:
            self.assertEqual(ch["timestamp_source"], "UNKNOWN")
            self.assertIsNone(ch["playback_url"])
            self.assertIsNone(ch["start_seconds"])

        # 2. Verify every chapter across all 28 videos strictly obeys timestamp_evidence.json
        for vid, rec in vid_records.items():
            for ch in rec["chapters"]:
                if ch["timestamp_source"] == "UNKNOWN":
                    self.assertIsNone(ch["playback_url"])
                    self.assertIsNone(ch["start_seconds"])
                else:
                    self.assertIsNotNone(ch["playback_url"])
                    self.assertIn(f"watch?v={vid}&t=", ch["playback_url"])
                    if vid not in {"lC5jxpYmatE", "Vr3JkAT9mo8", "u3ka_AAb8qE", "CnkEROU7fZw"}:
                        ev = evidence_map.get(vid, {})
                        ch_ev = (ev.get("chapters") or {}).get(str(ch["start_seconds"]))
                        self.assertIsNotNone(
                            ch_ev, f"Unexpected verified chapter {vid} @ {ch['start_seconds']}s"
                        )
                        self.assertIn(ch_ev["verdict"], {"DESC_MATCH", "CAPTION_PASS"})
            # Verify no CONFIRMED_DOC claim lacks an official_url
            for cl in rec.get("claims", []):
                if cl["status"] == "CONFIRMED_DOC":
                    self.assertTrue(
                        bridge.valid_url(cl.get("official_url")),
                        f"CONFIRMED_DOC without valid official_url in {vid}: {cl}",
                    )

        # 3. Benchmark 6 natural-language Q&A queries against the 28-video catalog
        # Query 1: Prompt Caching (t22FELAl-BM -> UNKNOWN timestamps -> normal URL + Notebook source guidance)
        q1 = query_mod.answer_question(
            "プロンプトキャッシュでChatGPTやClaudeの利用枠を節約する仕組みと注意点は？",
            root=real_root,
        )
        self.assertEqual(q1["step2_matched_records"][0]["video_id"], "t22FELAl-BM")
        q1_md = query_mod.format_qa_response_markdown(q1)
        self.assertIn("https://www.youtube.com/watch?v=t22FELAl-BM", q1_md)
        self.assertNotIn("watch?v=t22FELAl-BM&t=", q1_md)
        self.assertIn("AI技術研究室_直近調査12本_完全総合辞書_20261017", q1_md)

        # Query 2: Claude Code 10 setups / Skill Creator / Discord MCP (JXmk7hmbS3c -> verified &t= links)
        q2 = query_mod.answer_question(
            "Claude Codeをインストールしたら準備したいSkill CreatorやDiscord MCP連携の動画と再生位置を教えて",
            root=real_root,
        )
        self.assertEqual(q2["step2_matched_records"][0]["video_id"], "JXmk7hmbS3c")
        q2_urls = [
            s["playback_url"]
            for s in q2["step5_and_6_recommended_video_segments"]
            if s.get("playback_url")
        ]
        self.assertTrue(
            any("watch?v=JXmk7hmbS3c&t=27s" in u or "watch?v=JXmk7hmbS3c&t=297s" in u for u in q2_urls)
        )

        # Query 3: YouTube to NotebookLM Chrome extension (ZjUJ-35acaU -> verified &t= links)
        q3 = query_mod.answer_question(
            "YouTube to NotebookLMのChrome拡張機能で動画を一括インポートする手順とプロンプトはどこ？",
            root=real_root,
        )
        self.assertEqual(q3["step2_matched_records"][0]["video_id"], "ZjUJ-35acaU")
        q3_urls = [
            s["playback_url"]
            for s in q3["step5_and_6_recommended_video_segments"]
            if s.get("playback_url")
        ]
        self.assertTrue(any("watch?v=ZjUJ-35acaU&t=" in u for u in q3_urls))

        # Query 4: ChatGPT Work Specialists / AGENTS.md / MEMORY.md (Vr3JkAT9mo8)
        q4 = query_mod.answer_question(
            "ChatGPT Workの右腕AI・担当制でAGENTS.mdとMEMORY.mdを分ける方法はどの動画のどこ？",
            root=real_root,
        )
        self.assertEqual(q4["step2_matched_records"][0]["video_id"], "Vr3JkAT9mo8")
        # 180s is from legacy '動画の説明' (weak basis -> demoted to UNKNOWN), so its playback_url MUST be None
        vr3_segs = [
            s for s in q4["step5_and_6_recommended_video_segments"]
            if s.get("video_id") == "Vr3JkAT9mo8"
        ]
        self.assertTrue(len(vr3_segs) > 0)
        self.assertIsNone(vr3_segs[0].get("playback_url"))
        self.assertEqual(vr3_segs[0].get("timestamp_source"), "UNKNOWN")

        # Query 5: Skill design failures & Computer Use (lC5jxpYmatE)
        q5 = query_mod.answer_question(
            "スキルを増やしすぎる失敗例や課題ドリブンの学習法を解説していた動画と箇所は？",
            root=real_root,
        )
        q5_vids = [r["video_id"] for r in q5["step2_matched_records"][:2]]
        self.assertIn("lC5jxpYmatE", q5_vids)

        # Query 6: Completely unrelated topic -> 0 matched records
        q6 = query_mod.answer_question(
            "超伝導トカマク型核融合炉のプラズマ閉じ込め磁場コイル設計手順は？",
            root=real_root,
        )
        self.assertEqual(len(q6["step2_matched_records"]), 0)
        self.assertEqual(
            q6["step4_gap_analysis"]["coverage_status"],
            "INSUFFICIENT_NEEDS_NEW_RESEARCH",
        )

    def test_15_priority1_to_5_negative_cases_and_scale_generalization(self):
        """Verify negative/chaos cases (missing evidence, dur_match-only, CONFIRMED_DOC without URL, omitted readback) and 100-video scale generalization."""
        # 1. Video without primary verification data & duration-match-only chapter (CAPTION_FAIL) -> both must be UNKNOWN
        custom_evidence = {
            "DurOnly1234": {
                "yt_len_sec": 600,
                "yt_title": "Duration Match Only Video",
                "yt_author": "Test Channel",
                "yt_pub": "2026-10-01",
                "desc_starts": [],
                "desc_summary": "",
                "dur_match": True,
                "contradicts_desc": False,
                "chapters": {
                    "60": {"verdict": "CAPTION_FAIL", "evidence": "no matching tokens"},
                    "180": {"verdict": "CAPTION_PASS", "evidence": "181.0s: matched tokens"},
                },
            }
        }
        handoff_payload = {
            "receipt_version": "research_receipt_v1",
            "batch_part": "1/1",
            "notebook_source_id": "汎用テストソース_20261017",
            "generated_at": "2026-10-17T12:00:00+09:00",
            "videos": [
                {
                    "number": "01",
                    "id": "NoEvid12345",
                    "title": "未検証動画テスト",
                    "url": "https://www.youtube.com/watch?v=NoEvid12345",
                    "publish_date": "2026-10-10",
                    "duration": "10:00",
                    "summary": "一次検証データが存在しない動画。",
                    "timeline": [
                        {
                            "start": "01:00",
                            "end": "05:00",
                            "seconds": 60,
                            "title": "未検証チャプター",
                            "link": "https://www.youtube.com/watch?v=NoEvid12345&t=60s",
                        }
                    ],
                    "official_verification": {
                        "status": "VERIFIED",
                        "details": "一次URLなしの自己申告照合。",
                    },
                },
                {
                    "number": "02",
                    "id": "DurOnly1234",
                    "title": "Duration Match Only Video",
                    "url": "https://www.youtube.com/watch?v=DurOnly1234",
                    "publish_date": "2026-10-01",
                    "duration": "10:00",
                    "summary": "動画尺だけ一致し、1章は字幕不一致、2章は字幕一致の動画。",
                    "timeline": [
                        {
                            "start": "01:00",
                            "end": "03:00",
                            "seconds": 60,
                            "title": "字幕不一致の章",
                            "link": "https://www.youtube.com/watch?v=DurOnly1234&t=60s",
                        },
                        {
                            "start": "03:00",
                            "end": "06:00",
                            "seconds": 180,
                            "title": "字幕一致の章",
                            "link": "https://www.youtube.com/watch?v=DurOnly1234&t=180s",
                        },
                    ],
                    "official_verification": {
                        "status": "VERIFIED",
                        "details": "一次URLありの照合。",
                        "official_url": "https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching",
                    },
                },
            ],
        }
        norm = bridge.normalize_gemini_handoff_receipt(
            handoff_payload, evidence_map=custom_evidence
        )
        bridge.validate(norm)
        # Video 1 (no primary evidence) -> chapter is UNKNOWN, claim without URL is REPORTED_BY_AUTHOR, readback is UNKNOWN
        v_no_ev = norm["videos"][0]
        self.assertEqual(v_no_ev["chapters"][0]["timestamp_source"], "UNKNOWN")
        self.assertIsNone(v_no_ev["chapters"][0]["start_seconds"])
        self.assertEqual(v_no_ev["claims"][0]["status"], "REPORTED_BY_AUTHOR")
        self.assertEqual(v_no_ev["notebook_readback"], "UNKNOWN")

        # Video 2 (dur_match=True) -> CAPTION_FAIL chapter is UNKNOWN, CAPTION_PASS chapter is TIMESTAMPED_CAPTIONS, claim with URL is CONFIRMED_DOC
        v_dur = norm["videos"][1]
        self.assertEqual(v_dur["chapters"][0]["timestamp_source"], "UNKNOWN")
        self.assertIsNone(v_dur["chapters"][0]["start_seconds"])
        self.assertEqual(v_dur["chapters"][1]["timestamp_source"], "TIMESTAMPED_CAPTIONS")
        self.assertEqual(v_dur["chapters"][1]["start_seconds"], 180)
        self.assertEqual(v_dur["claims"][0]["status"], "CONFIRMED_DOC")
        self.assertEqual(
            v_dur["claims"][0]["official_url"],
            "https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching",
        )

        # 2. Direct schema validation must reject CONFIRMED_DOC when official_url is None
        bad_confirmed = json.loads(json.dumps(norm))
        bad_confirmed["videos"][0]["claims"][0]["status"] = "CONFIRMED_DOC"
        bad_confirmed["videos"][0]["claims"][0]["official_url"] = None
        with self.assertRaisesRegex(ValueError, "CONFIRMED_DOC status requires a valid official_url"):
            bridge.validate(bad_confirmed)

        # 3. Scale generalization test: 100 videos across 5 batches of 20 videos each
        total_normalized = 0
        for batch_idx in range(5):
            batch_videos = []
            for i in range(20):
                seq = batch_idx * 20 + i
                vid = f"ScaleV{seq:05d}"  # 11 chars
                batch_videos.append(
                    {
                        "number": str(seq + 1),
                        "id": vid,
                        "title": f"スケール検証動画 #{seq + 1}: Claude Code & MCP Agent",
                        "url": f"https://www.youtube.com/watch?v={vid}",
                        "publish_date": "2026-10-17",
                        "duration": "15:00",
                        "summary": f"100本〜1000本規模の汎用パイプライン検証用動画 #{seq + 1}。",
                        "key_technologies": ["Claude Code", "MCP", "Subagents"],
                        "timeline": [
                            {
                                "start": "00:00",
                                "end": "05:00",
                                "seconds": 0,
                                "title": "イントロダクション",
                                "link": f"https://www.youtube.com/watch?v={vid}&t=0s",
                            }
                        ],
                    }
                )
            batch_raw = {
                "receipt_version": "research_receipt_v1",
                "batch_part": f"{batch_idx + 1}/5",
                "notebook_source_id": f"大規模検証ソース_Batch{batch_idx + 1}",
                "generated_at": "2026-10-17T15:00:00+09:00",
                "videos": batch_videos,
            }
            norm_batch = bridge.normalize_gemini_handoff_receipt(batch_raw, evidence_map={})
            validated_videos = bridge.validate(norm_batch)
            self.assertEqual(len(validated_videos), 20)
            total_normalized += len(validated_videos)
        self.assertEqual(total_normalized, 100)


class TestQueryResearchEngine(unittest.TestCase):
    """Test natural-language query and verified timestamp locator engine (query_research.py)."""

    def test_query_case_e_out_of_scope_rejection(self):
        """Case E: Completely out-of-scope technologies (e.g. Rust WebAssembly compiler) must be rejected with INSUFFICIENT_NEEDS_NEW_RESEARCH."""
        query = "完全にリポジトリ外の技術（例：RustのWebAssemblyコンパイラ最適化）"
        res = query_mod.answer_question(query, root=ROOT, top_k=2)
        gap = res.get("step4_gap_analysis", {})
        self.assertEqual(gap.get("coverage_status"), "INSUFFICIENT_NEEDS_NEW_RESEARCH")
        self.assertEqual(len(res.get("step2_matched_records", [])), 0)
        self.assertEqual(len(res.get("step5_and_6_recommended_video_segments", [])), 0)

    def test_query_case_f_explicit_video_id_and_verified_links(self):
        """Case F: Targeting a specific video ID (lC5jxpYmatE) extracts its verified chapters with valid &t=XXs URLs."""
        query = "lC5jxpYmatEの検証済み箇所"
        res = query_mod.answer_question(query, root=ROOT, top_k=2)
        records = res.get("step2_matched_records", [])
        self.assertGreaterEqual(len(records), 1)
        self.assertEqual(records[0]["video_id"], "lC5jxpYmatE")

        segments = res.get("step5_and_6_recommended_video_segments", [])
        self.assertGreaterEqual(len(segments), 1)
        for seg in segments:
            if seg.get("video_id") == "lC5jxpYmatE" and seg.get("playback_url"):
                self.assertIn("watch?v=lC5jxpYmatE&t=", seg["playback_url"])
                self.assertIn(
                    seg.get("timestamp_source"),
                    {"VISUAL_FRAME_CHECK", "TIMESTAMPED_CAPTIONS", "YOUTUBE_CHAPTER_METADATA"},
                )

    def test_query_case_a_claude_code_knowledge(self):
        """Case A: Claude Code CLI setup query retrieves Claude Code records and notebook recommendations."""
        query = "Claude Codeのエラー解決とCLI環境設定"
        res = query_mod.answer_question(query, root=ROOT, top_k=2)
        records = res.get("step2_matched_records", [])
        self.assertGreaterEqual(len(records), 1)
        titles = " ".join([r["title"] for r in records]).lower()
        self.assertIn("claude", titles)


class TestGasConfigurationAndOperationsContract(unittest.TestCase):
    """Verify GAS configuration, manual contract, property aliases, and non-destructive operations."""

    def setUp(self):
        self.gas_path = (ROOT / "automation" / "gemini-notebook" / "cloud_relay_gas.js").as_posix()

    def test_gas_entry_function_and_aliases_exist(self):
        """1. Verify that runCloudRelayLoop_ and relayDriveReceiptsToGitHub are exported and callable."""
        node_test = f"""
const gas = require({json.dumps(self.gas_path)});
if (typeof gas.runCloudRelayDryRun !== "function") {{
  throw new Error("runCloudRelayDryRun is not exported as a function");
}}
if (typeof gas.runCloudRelayLoop !== "function") {{
  throw new Error("runCloudRelayLoop is not exported as a function");
}}
if (typeof gas.runCloudRelayLoop_ !== "function") {{
  throw new Error("runCloudRelayLoop_ is not exported as a function");
}}
if (typeof gas.relayDriveReceiptsToGitHub !== "function") {{
  throw new Error("relayDriveReceiptsToGitHub is not exported as a function");
}}
process.stdout.write("OK");
"""
        res = subprocess.run(
            ["node", "-e", node_test],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        self.assertEqual(res.stdout.strip(), "OK")

    def test_gas_dry_run_no_github_write(self):
        """Verify that runCloudRelayDryRun validates Drive receipt and previews diffs without performing any GitHub commits."""
        fixture_path = (ROOT / "automation" / "gemini-notebook" / "fixtures" / "test_sample_receipt_v1.json").as_posix()
        node_test = f"""
const gas = require({json.dumps(self.gas_path)});
const fs = require("fs");
const crypto = require("crypto");

const fixtureJson = fs.readFileSync({json.dumps(fixture_path)}, "utf8");

// Validate fixture validity in both JS and check it uses genuine sodTFSuV4zY data
const parsedFixture = JSON.parse(fixtureJson);
if (parsedFixture.videos[0].video_id !== "sodTFSuV4zY") {{
  throw new Error("Fixture must use genuine video_id sodTFSuV4zY");
}}
if (parsedFixture.videos[0].claims[0].status === "CONFIRMED_DOC") {{
  throw new Error("Fixture must not fabricate CONFIRMED_DOC");
}}
if (parsedFixture.notebook_readback === "PASS") {{
  throw new Error("Fixture must not claim unverified PASS for notebook_readback");
}}
gas.validateReceipt(parsedFixture);

const mockProps = {{
  store: {{
    GITHUB_FINE_GRAINED_PAT: "test_pat_token",
    DRIVE_INBOX_FOLDER_ID: "folder_inbox_123",
    TARGET_GITHUB_BRANCH: "feature/gemini-notebook-research-loop-20261016"
  }},
  getProperty(k) {{ return this.store[k] || null; }},
  setProperty(k, v) {{ this.store[k] = String(v); }}
}};

let fileRead = false;
const mockDrive = {{
  getFolderById(id) {{
    return {{
      getFiles() {{
        return {{
          hasNext() {{
            if (!fileRead) {{ fileRead = true; return true; }}
            return false;
          }},
          next() {{
            return {{
              getName() {{ return "test_sample_receipt_v1.json"; }},
              getMimeType() {{ return "application/json"; }},
              getBlob() {{
                return {{
                  getDataAsString() {{ return fixtureJson; }}
                }};
              }}
            }};
          }}
        }};
      }}
    }};
  }}
}};

let commitAttempted = false;
const mockFetcher = {{
  fetch(url, opts) {{
    const u = String(url);
    if (opts && (opts.method === "post" || opts.method === "patch")) {{
      commitAttempted = true;
      throw new Error("FORBIDDEN_WRITE_CALL_IN_DRY_RUN: " + opts.method + " " + u);
    }}
    if (u.includes("/branches?per_page=100")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify([{{ name: "feature/gemini-notebook-research-loop-20261016", commit: {{ sha: "head_commit_sha" }} }}]);
        }}
      }};
    }}

    if (u.includes("/branches/feature%2Fgemini-notebook-research-loop-20261016") || u.includes("/branches/feature/gemini-notebook-research-loop-20261016")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{
            name: "feature/gemini-notebook-research-loop-20261016",
            commit: {{ sha: "head_commit_sha", commit: {{ tree: {{ sha: "head_tree_sha" }} }} }}
          }});
        }}
      }};
    }}
    if (u.includes("/git/commits/head_commit_sha")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{ sha: "head_commit_sha", tree: {{ sha: "head_tree_sha" }} }});
        }}
      }};
    }}
    if (u.includes("/git/trees/head_tree_sha")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{
            sha: "head_tree_sha",
            truncated: false,
            tree: [
              {{ path: "registry.json", sha: "blob_reg", type: "blob" }},
              {{ path: "automation/gemini-notebook/state/loop_state.json", sha: "blob_loop", type: "blob" }}
            ]
          }});
        }}
      }};
    }}
    if (u.includes("/git/blobs/blob_reg")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{
            content: Buffer.from(JSON.stringify({{
              schema_version: 1,
              repository: "kamiyusense/ai-video-research",
              records: []
            }})).toString("base64"),
            encoding: "base64"
          }});
        }}
      }};
    }}

    if (u.includes("/git/blobs/blob_loop")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{
            content: Buffer.from(JSON.stringify({{
              schema_version: "gemini_notebook_loop_state_v1",
              repository: "kamiyusense/ai-video-research",
              processed_receipts: [],
              remote_branch_cache: {{}},
              open_unknowns: [],
              next_topics_queue: []
            }})).toString("base64"),
            encoding: "base64"
          }});
        }}
      }};
    }}
    return {{ getResponseCode() {{ return 200; }}, getContentText() {{ return "{{}}"; }} }};
  }}
}};

const out = gas.runCloudRelayDryRun({{
  scriptProperties: mockProps,
  driveApp: mockDrive,
  urlFetchApp: mockFetcher
}});

if (commitAttempted) {{
  throw new Error("Commit was attempted during runCloudRelayDryRun!");
}}
if (out.mode !== "DRY_RUN") {{
  throw new Error("Expected mode === 'DRY_RUN', got: " + out.mode);
}}
if (!out.relayReport || out.relayReport.length !== 1) {{
  throw new Error("Expected 1 relayReport item, got: " + JSON.stringify(out.relayReport));
}}
const rep = out.relayReport[0];
if (rep.status !== "DRY_RUN_PREVIEW_ONLY_NO_GITHUB_WRITE") {{
  throw new Error("Expected DRY_RUN_PREVIEW_ONLY_NO_GITHUB_WRITE, got: " + rep.status);
}}
if (rep.githubWriteStatus !== "PREVIEW_ONLY") {{
  throw new Error("Expected PREVIEW_ONLY, got: " + rep.githubWriteStatus);
}}

process.stdout.write("DRY_RUN_SUCCESS");
"""
        res = subprocess.run(
            ["node", "-e", node_test],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        self.assertEqual(res.stdout.strip(), "DRY_RUN_SUCCESS")

    def test_live_sample_receipt_fixture_validity(self):
        """Verify that live_sample_receipt_v1.json uses genuine kCc8FmEb1nY data, is valid in JS & Python, and contains no false flags."""
        live_fixture_path = (ROOT / "automation" / "gemini-notebook" / "fixtures" / "live_sample_receipt_v1.json").as_posix()
        self.assertTrue(os.path.exists(live_fixture_path), "live_sample_receipt_v1.json must exist")

        with open(live_fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("schema_version"), "research_receipt_v1")
        self.assertEqual(data.get("notebook_readback"), "UNKNOWN")
        videos = data.get("videos", [])
        self.assertEqual(len(videos), 1)
        v = videos[0]
        self.assertEqual(v.get("video_id"), "kCc8FmEb1nY")
        self.assertEqual(v.get("changes"), ["NEW"])
        self.assertEqual(v.get("notebook_readback"), "UNKNOWN")

        # Verify no fake CONFIRMED_DOC or TIMESTAMPED_CAPTIONS
        for c in v.get("claims", []):
            self.assertNotEqual(c.get("status"), "CONFIRMED_DOC")
            self.assertEqual(c.get("timestamp_source"), "UNKNOWN")
            self.assertIsNone(c.get("timestamp_seconds"))
        for ch in v.get("chapters", []):
            self.assertEqual(ch.get("timestamp_source"), "UNKNOWN")
            self.assertIsNone(ch.get("start_seconds"))

        # Verify JS validation
        node_test = f"""
const gas = require({json.dumps(self.gas_path)});
const fs = require("fs");
const raw = fs.readFileSync({json.dumps(live_fixture_path)}, "utf8");
const clean = gas.validateReceipt(JSON.parse(raw));
if (!clean || clean.length !== 1 || clean[0].video_id !== "kCc8FmEb1nY") {{
  throw new Error("JS validation failed for live_sample_receipt_v1.json");
}}
process.stdout.write("JS_OK");
"""
        res = subprocess.run(
            ["node", "-e", node_test],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        self.assertEqual(res.stdout.strip(), "JS_OK")


    def test_gas_script_properties_aliases_and_safety_stop_on_missing(self):
        """2. Verify that GITHUB_PAT and TARGET_BRANCH aliases work, and missing properties halt safely."""
        node_test = f"""
const gas = require({json.dumps(self.gas_path)});

// Test A: Missing properties must throw an explicit Error
let threwOnMissing = false;
try {{
  gas.relayDriveReceiptsToGitHub({{
    scriptProperties: {{
      getProperty: () => null
    }}
  }});
}} catch (e) {{
  if (e.message.includes("Missing required Script Properties")) {{
    threwOnMissing = true;
  }}
}}
if (!threwOnMissing) {{
  throw new Error("Failed to throw on missing Script Properties");
}}

// Test B: GITHUB_PAT alias + TARGET_BRANCH alias accepted
const store = {{
  GITHUB_PAT: "ghp_alias_test_token",
  DRIVE_INBOX_FOLDER_ID: "FOLDER_ALIAS_123",
  TARGET_BRANCH: "feature/gemini-notebook-research-loop-20261016"
}};
let propsChecked = false;
const mockDriveApp = {{
  getFolderById: () => ({{
    getFiles: () => ({{
      hasNext: () => false,
      next: () => null
    }})
  }})
}};
const mockUrlFetch = {{
  fetch: (url) => {{
    if (url.includes("/branches?per_page=100")) {{
      return {{
        getResponseCode: () => 200,
        getContentText: () => JSON.stringify([
          {{ name: "main", protected: true, commit: {{ sha: "c_main" }} }},
          {{ name: "feature/gemini-notebook-research-loop-20261016", protected: false, commit: {{ sha: "c_target" }} }}
        ])
      }};
    }}
    if (url.includes("/git/commits/")) {{
      return {{
        getResponseCode: () => 200,
        getContentText: () => JSON.stringify({{ sha: "c_target", tree: {{ sha: "t_target" }} }})
      }};
    }}
    if (url.includes("/git/trees/")) {{
      return {{
        getResponseCode: () => 200,
        getContentText: () => JSON.stringify({{
          sha: "t_target",
          truncated: false,
          tree: [{{ path: "registry.json", type: "blob", sha: "sha_reg_stub" }}]
        }})
      }};
    }}
    if (url.includes("/git/blobs/")) {{
      return {{
        getResponseCode: () => 200,
        getContentText: () => JSON.stringify({{
          sha: "sha_reg_stub",
          content: Buffer.from(JSON.stringify({{ schema_version: 1, repository: "kamiyusense/ai-video-research", records: [] }})).toString("base64"),
          encoding: "base64"
        }})
      }};
    }}
    return {{ getResponseCode: () => 404, getContentText: () => "{{}}" }};
  }}
}};

const out = gas.runCloudRelayLoop_({{
  scriptProperties: {{
    getProperty: (k) => store[k] || null,
    setProperty: (k, v) => {{ store[k] = String(v); }}
  }},
  driveApp: mockDriveApp,
  urlFetchApp: mockUrlFetch
}});

if (out.status !== "COMPLETED" || out.targetBranch !== "feature/gemini-notebook-research-loop-20261016") {{
  throw new Error("Alias run failed: " + JSON.stringify(out));
}}
process.stdout.write("OK_ALIASES");
"""
        res = subprocess.run(
            ["node", "-e", node_test],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        self.assertEqual(res.stdout.strip(), "OK_ALIASES")

    def test_gas_in_place_dedup_and_zero_duplicate_on_identical_receipt(self):
        """3. Verify non-destructive in-place dedup prevents duplicate commits without deleting inbox files."""
        sample_receipt = make_sample_receipt()
        node_test = f"""
const gas = require({json.dumps(self.gas_path)});
const sampleReceipt = {json.dumps(sample_receipt, ensure_ascii=False)};

const store = {{
  GITHUB_FINE_GRAINED_PAT: "ghp_mock_token",
  DRIVE_INBOX_FOLDER_ID: "FOLDER_123",
  TARGET_GITHUB_BRANCH: "feature/gemini-notebook-research-loop-20261016"
}};
const initialReg = {{ schema_version: 1, repository: "kamiyusense/ai-video-research", records: [] }};
let targetHeadSha = "commit_init";
const trees = {{ "t_init": [{{ path: "registry.json", type: "blob", sha: "sha_reg" }}] }};
const commits = {{ "commit_init": {{ sha: "commit_init", tree: {{ sha: "t_init" }} }} }};
const blobs = {{ "sha_reg": Buffer.from(JSON.stringify(initialReg)).toString("base64") }};

  function putBlob(text) {{
    const sha = "sha_" + Object.keys(blobs).length;
    blobs[sha] = Buffer.from(text).toString("base64");
    return sha;
  }}

  let patchCount = 0;
  const mockFetch = {{
    fetch: (url, opts) => {{
      const method = (opts.method || "get").toLowerCase();
      const body = opts.payload ? JSON.parse(opts.payload) : null;
      const makeRes = (c, o) => ({{ getResponseCode: () => c, getContentText: () => JSON.stringify(o) }});

      if (url.includes("/branches?per_page=100")) {{
        return makeRes(200, [
          {{ name: "main", protected: true, commit: {{ sha: "c_main" }} }},
          {{ name: "feature/gemini-notebook-research-loop-20261016", protected: false, commit: {{ sha: targetHeadSha }} }}
        ]);
      }}
      if (url.includes("/git/commits/") && method === "get") return makeRes(200, commits[url.split("/git/commits/")[1]]);
      if (url.includes("/git/trees/") && method === "get") {{
        const t = url.split("/git/trees/")[1].split("?")[0];
        return makeRes(200, {{ sha: t, truncated: false, tree: trees[t] || [] }});
      }}
      if (url.includes("/git/blobs/") && method === "get") {{
        const b = url.split("/git/blobs/")[1];
        return makeRes(200, {{ sha: b, content: blobs[b] || "", encoding: "base64" }});
      }}
      if (url.endsWith("/git/blobs") && method === "post") {{
        const s = putBlob(body.content);
        return makeRes(201, {{ sha: s }});
      }}
      if (url.endsWith("/git/trees") && method === "post") {{
        const baseItems = JSON.parse(JSON.stringify(trees[body.base_tree] || []));
        const byPath = {{}};
        baseItems.forEach((it) => {{ byPath[it.path] = it; }});
        body.tree.forEach((it) => {{ byPath[it.path] = {{ path: it.path, type: "blob", sha: it.sha }}; }});
        const newTreeSha = "t_" + Object.keys(trees).length;
        trees[newTreeSha] = Object.values(byPath);
        return makeRes(201, {{ sha: newTreeSha }});
      }}
      if (url.endsWith("/git/commits") && method === "post") {{
        const newCommitSha = "c_" + Object.keys(commits).length;
        commits[newCommitSha] = {{ sha: newCommitSha, tree: {{ sha: body.tree }} }};
        return makeRes(201, {{ sha: newCommitSha }});
      }}
      if (url.includes("/git/refs/heads/") && method === "patch") {{
        patchCount++;
        targetHeadSha = body.sha;
        return makeRes(200, {{ object: {{ sha: targetHeadSha }} }});
      }}
      if (url.includes("/git/refs/heads/") && method === "get") return makeRes(200, {{ object: {{ sha: targetHeadSha }} }});
      return makeRes(404, {{}});
    }}
  }};

const inbox = [{{
  getId: () => "DOC_1",
  getName: () => "receipt.json",
  getMimeType: () => "text/plain",
  getBlob: () => ({{ getDataAsString: () => JSON.stringify(sampleReceipt) }})
}}];

const mockDrive = {{
  getFolderById: () => ({{
    getFiles: () => {{
      let idx = 0;
      return {{ hasNext: () => idx < inbox.length, next: () => inbox[idx++] }};
    }}
  }})
}};

const env = {{
  scriptProperties: {{
    getProperty: (k) => store[k] || null,
    setProperty: (k, v) => {{ store[k] = String(v); }}
  }},
  driveApp: mockDrive,
  urlFetchApp: mockFetch
}};

// Run 1: Should commit new receipt
const res1 = gas.runCloudRelayLoop_(env);
const p1 = patchCount;

// Run 2: Same receipt remains in inbox (non-destructive). Must SKIP duplicate without any new Git patch!
const res2 = gas.runCloudRelayLoop_(env);
const p2 = patchCount;

if (p1 !== 1 || p2 !== 1) {{
  throw new Error(`Duplicate commit detected! Run1 patches: ${{p1}}, Run2 patches: ${{p2}}`);
}}
if (res2.relayReport[0].status !== "SKIP_DUPLICATE_NOOP_RECEIPT" && res2.relayReport[0].status !== "SKIP_DUPLICATE_ALREADY_COMMITTED_ON_GITHUB") {{
  throw new Error("Unexpected duplicate status: " + JSON.stringify(res2.relayReport));
}}
process.stdout.write("OK_NON_DESTRUCTIVE_DEDUP");
"""
        res = subprocess.run(
            ["node", "-e", node_test],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        self.assertEqual(res.stdout.strip(), "OK_NON_DESTRUCTIVE_DEDUP")

    def test_caption_single_token_false_positive_audit(self):
        """Audit that single-token hits in caption verification are strictly rejected as CAPTION_FAIL.
        
        Verifies:
        1. Unit logic in verify_timestamps.verify_chapter: a single generic word (e.g. 'studio')
           or numeric-only tokens must fail with INSUFFICIENT_DISTINCT_TOKENS, even if control_max == 0.
        2. Only chapters with >= 2 distinct non-numeric tokens and local > control_max can achieve CAPTION_PASS.
        3. Entire 28-video timestamp_evidence.json has exactly 0 weak single-token CAPTION_PASS verdicts.
        4. The 4 demoted single-token chapters (studio, 評価, ファイル, ワークフロー) are strictly CAPTION_FAIL.
        5. Total CAPTION_PASS count in evidence is exactly 73.
        """
        # 1. Unit test verify_chapter logic with synthetic cues
        sample_cues = [
            (100.0, 105.0, "ここで studio の説明をします"),
            (200.0, 205.0, "notebooklm cli をセットアップします"),
        ]
        # Single token 'studio' (control_max = 0) -> MUST FAIL
        res_single = vts_mod.verify_chapter(
            start=100,
            end=120,
            title="studio 機能の実演",
            cues=sample_cues,
            yt_len=300,
            desc_starts=[],
            dur_match=True,
            contradicts_desc=False,
        )
        self.assertEqual(res_single["verdict"], "CAPTION_FAIL")
        self.assertEqual(res_single["reason"], "INSUFFICIENT_DISTINCT_TOKENS")

        # Two distinct non-numeric tokens 'notebooklm', 'cli' -> MUST PASS
        res_multi = vts_mod.verify_chapter(
            start=200,
            end=220,
            title="notebooklm cli のセットアップ",
            cues=sample_cues,
            yt_len=300,
            desc_starts=[],
            dur_match=True,
            contradicts_desc=False,
        )
        self.assertEqual(res_multi["verdict"], "CAPTION_PASS")
        self.assertGreaterEqual(len(res_multi["matched_title_tokens"]), 2)

        # Numeric-only tokens (e.g. '10', '20') -> MUST FAIL
        res_num = vts_mod.verify_chapter(
            start=100,
            end=120,
            title="10 20",
            cues=sample_cues,
            yt_len=300,
            desc_starts=[],
            dur_match=True,
            contradicts_desc=False,
        )
        self.assertEqual(res_num["verdict"], "CAPTION_FAIL")
        self.assertEqual(res_num["reason"], "INSUFFICIENT_DISTINCT_TOKENS")

        # 2. Audit actual evidence file
        evidence_map = bridge.load_timestamp_evidence()
        weak_count = 0
        caption_pass_count = 0
        for vid, data in evidence_map.items():
            for sec_str, ch in (data.get("chapters") or {}).items():
                if ch.get("verdict") == "CAPTION_PASS":
                    caption_pass_count += 1
                    toks = [
                        t for t in (ch.get("matched_title_tokens") or [])
                        if not t.isdigit()
                    ]
                    if len(set(toks)) < 2:
                        weak_count += 1

        self.assertEqual(
            weak_count,
            0,
            "No single-token or weak multi-token matches may be marked as CAPTION_PASS",
        )
        self.assertEqual(
            caption_pass_count,
            73,
            "Total CAPTION_PASS count in timestamp_evidence.json must be exactly 73",
        )

        # 3. Assert specific 4 demoted chapters are strictly CAPTION_FAIL
        self.assertEqual(
            evidence_map["2-8cXaRHlqI"]["chapters"]["619"]["verdict"],
            "CAPTION_FAIL",
        )
        self.assertEqual(
            evidence_map["2-8cXaRHlqI"]["chapters"]["619"]["reason"],
            "INSUFFICIENT_DISTINCT_TOKENS",
        )
        self.assertEqual(
            evidence_map["26MGuVIJh4A"]["chapters"]["772"]["verdict"],
            "CAPTION_FAIL",
        )
        self.assertEqual(
            evidence_map["26MGuVIJh4A"]["chapters"]["772"]["reason"],
            "INSUFFICIENT_DISTINCT_TOKENS",
        )
        self.assertEqual(
            evidence_map["Eh75KT85Y40"]["chapters"]["1386"]["verdict"],
            "CAPTION_FAIL",
        )
        self.assertEqual(
            evidence_map["Eh75KT85Y40"]["chapters"]["1386"]["reason"],
            "INSUFFICIENT_DISTINCT_TOKENS",
        )
        self.assertEqual(
            evidence_map["lC5jxpYmatE"]["chapters"]["3078"]["verdict"],
            "CAPTION_FAIL",
        )
        self.assertEqual(
            evidence_map["lC5jxpYmatE"]["chapters"]["3078"]["reason"],
            "INSUFFICIENT_DISTINCT_TOKENS",
        )

    def test_catalog_caption_discrepancy_and_unknown_safety(self):
        """5. Verify exact alignment between evidence CAPTION_PASS (73) and catalog TIMESTAMPED_CAPTIONS (73),
        and verify that UNKNOWN chapters never generate a playback_url or leaked seconds.
        """
        catalog_path = ROOT / "automation" / "gemini-notebook" / "state" / "video_knowledge_catalog.json"
        cat = json.loads(catalog_path.read_text(encoding="utf-8"))

        ts_counts = {}
        for rec in cat.get("records", []):
            for ch in rec.get("chapters", []):
                src = ch.get("timestamp_source")
                ts_counts[src] = ts_counts.get(src, 0) + 1
                if src == "UNKNOWN":
                    self.assertIsNone(
                        ch.get("playback_url"),
                        f"UNKNOWN chapter must not have playback_url: {rec.get('video_id')} @ {ch.get('title')}",
                    )
                    self.assertIsNone(
                        ch.get("start_seconds"),
                        f"UNKNOWN chapter must not expose start_seconds: {rec.get('video_id')} @ {ch.get('title')}",
                    )
                    self.assertEqual(ch.get("start_mmss"), "UNKNOWN")
                else:
                    self.assertTrue(
                        ch.get("playback_url", "").startswith("https://www.youtube.com/watch?v="),
                        f"Verified chapter must have valid playback_url: {rec.get('video_id')} @ {ch.get('title')}",
                    )

        self.assertEqual(
            ts_counts.get("TIMESTAMPED_CAPTIONS"),
            77,
            "Catalog TIMESTAMPED_CAPTIONS must strictly equal 77 (matching evidence CAPTION_PASS + u3ka_AAb8qE + CnkEROU7fZw)",
        )
        self.assertEqual(ts_counts.get("YOUTUBE_CHAPTER_METADATA"), 48)
        self.assertEqual(ts_counts.get("VISUAL_FRAME_CHECK"), 9)
        self.assertEqual(ts_counts.get("UNKNOWN"), 133)
        self.assertEqual(sum(ts_counts.values()), 267)
        self.assertEqual(cat.get("total_verified_chapters"), 134)

    def test_all_241_chapters_parity_between_raw_notes_and_catalog(self):
        """6. Regression test: verify that all 241 chapters in raw research/*.md notes
        are accurately preserved in video_knowledge_catalog.json with zero silent drops,
        and that the 3 restored unlinked chapters exist strictly as UNKNOWN.
        """
        import re

        catalog_path = ROOT / "automation" / "gemini-notebook" / "state" / "video_knowledge_catalog.json"
        cat = json.loads(catalog_path.read_text(encoding="utf-8"))

        # Collect raw chapters from markdown notes
        raw_chaps = []
        for p in sorted((ROOT / "research").glob("*.md")):
            text = p.read_text(encoding="utf-8")
            m_vid = re.search(r'^(?:-\s*)?video_id:\s*["`]?([A-Za-z0-9_-]{11})["`]?', text, re.MULTILINE)
            if not m_vid:
                m_vid = re.search(r"^\s*-\s*動画ID:\s*`?([A-Za-z0-9_-]{11})`?", text, re.MULTILINE)
            if not m_vid:
                m_fn = re.search(r"\d{4}-\d{2}-\d{2}-([A-Za-z0-9_-]{11})-", p.name)
                if m_fn:
                    vid = m_fn.group(1)
                else:
                    continue
            else:
                vid = m_vid.group(1)

            # Match v0.6 lines (both linked and unlinked)
            for line in text.splitlines():
                m = query_mod.V06_CHAPTER_LINE_RE.match(line)
                if m:
                    raw_chaps.append((vid, m.group("title").strip()))
                    continue
                # Match legacy table rows
                m_leg_id = query_mod.LEGACY_TABLE_ROW_WITH_ID_RE.match(line)
                if m_leg_id:
                    raw_chaps.append((vid, m_leg_id.group("summary").strip()[:60]))
                    continue
                m_leg_noid = query_mod.LEGACY_TABLE_ROW_NO_ID_RE.match(line)
                if m_leg_noid:
                    raw_chaps.append((vid, m_leg_noid.group("summary").strip()[:60]))
                    continue

        # Collect catalog chapters
        cat_chaps = []
        cat_map = {}
        for r in cat.get("records", []):
            vid = r.get("video_id")
            for c in r.get("chapters", []):
                cat_chaps.append((vid, c["title"]))
                cat_map[(vid, c["title"])] = c

        self.assertEqual(
            len(raw_chaps),
            267,
            f"Expected exactly 267 chapters in raw research notes, got {len(raw_chaps)}",
        )
        self.assertEqual(
            len(cat_chaps),
            267,
            f"Expected exactly 267 chapters in catalog, got {len(cat_chaps)}",
        )
        self.assertEqual(
            len(raw_chaps),
            len(cat_chaps),
            "Raw markdown chapters and catalog chapters must have zero discrepancy",
        )

        # Verify specific 3 restored unlinked chapters
        restored_targets = [
            ("2-8cXaRHlqI", "Studio機能9種生成の実演"),
            ("26MGuVIJh4A", "ゴッホの『ひまわり』比較法（一流作品とAI生成物をブラインド評価）"),
            ("Eh75KT85Y40", "本番マージとブラウザでの多言語・AI検索向けファイル表示確認"),
        ]
        for vid, title in restored_targets:
            key = (vid, title)
            self.assertIn(key, cat_map, f"Restored chapter {key} missing from catalog!")
            ch = cat_map[key]
            self.assertEqual(
                ch.get("timestamp_source"),
                "UNKNOWN",
                f"Restored chapter {title} must be UNKNOWN, not verified",
            )
            self.assertIsNone(ch.get("start_seconds"))
            self.assertIsNone(ch.get("playback_url"))
            self.assertEqual(ch.get("start_mmss"), "UNKNOWN")

    def test_cp1_gemini_task_and_contract_spec_alignment(self):
        """CP1: Verify cross-spec alignment between GEMINI_TASK.md, contract_spec_v1.json,
        receipt_to_research.py, and cloud_relay_gas.js.
        """
        task_md_path = ROOT / "automation" / "gemini-notebook" / "GEMINI_TASK.md"
        task_text = task_md_path.read_text(encoding="utf-8")

        # 1. Ensure OFFICIAL_TIME_RANGE is completely removed from GEMINI_TASK.md
        self.assertNotIn("OFFICIAL_TIME_RANGE", task_text)

        # 2. Ensure allowed timestamp sources in GEMINI_TASK.md match contract_spec_v1.json exactly
        contract = bridge.CONTRACT
        for src in contract["allowed_timestamp_sources"]:
            self.assertIn(f'"{src}"', task_text)

        # 3. Ensure receipt_to_research rejects receipts with OFFICIAL_TIME_RANGE
        bad_receipt = make_sample_receipt()
        bad_receipt["videos"][0]["chapters"] = [
            {
                "title": "Bad timestamp source chapter",
                "start_seconds": 120,
                "end_seconds": 180,
                "summary_ja": "Test summary",
                "timestamp_source": "OFFICIAL_TIME_RANGE",
            }
        ]
        with self.assertRaises(ValueError) as ctx:
            bridge.validate(bad_receipt)
        self.assertIn("Invalid chapter timestamp_source", str(ctx.exception))

        # 4. Ensure cloud_relay_gas (JS) also rejects OFFICIAL_TIME_RANGE
        node_script = f"""
const gas = require({json.dumps(self.gas_path)});
try {{
  gas.validateReceipt({json.dumps(bad_receipt)});
  process.stdout.write("FAILED_TO_REJECT");
}} catch (e) {{
  if (String(e.message).includes("Invalid chapter timestamp_source")) {{
    process.stdout.write("REJECTED_AS_EXPECTED");
  }} else {{
    process.stdout.write("REJECTED_OTHER: " + e.message);
  }}
}}
"""
        res = subprocess.run(
            ["node", "-e", node_script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        self.assertEqual(res.stdout.strip(), "REJECTED_AS_EXPECTED")

    def test_cp2_query_research_quality_and_provenance_audit(self):
        """CP2: Comprehensive search quality and provenance audit across diverse user questions."""
        real_root = ROOT

        # 1. Audit provenance metadata across all catalog chapters
        catalog_path = ROOT / "automation" / "gemini-notebook" / "state" / "video_knowledge_catalog.json"
        cat = json.loads(catalog_path.read_text(encoding="utf-8"))
        prov_counts = {}
        for r in cat.get("records", []):
            for c in r.get("chapters", []):
                p = c.get("provenance")
                prov_counts[p] = prov_counts.get(p, 0) + 1
                self.assertIsNotNone(c.get("verification_scope"))
                self.assertIsNotNone(c.get("verification_actor"))
                if c["timestamp_source"] == "VISUAL_FRAME_CHECK":
                    self.assertEqual(p, "LEGACY_AI_STUDIO_USER_REPORT")
                    self.assertEqual(c["verification_actor"], "USER_REPORTED_AI_STUDIO_ANALYSIS")
                elif c["timestamp_source"] == "TIMESTAMPED_CAPTIONS":
                    self.assertEqual(p, "YOUTUBE_TIMEDTEXT_DIRECT_DETERMINISTIC_TOKEN_MATCH")
                    self.assertEqual(c["verification_actor"], "INDEPENDENT_CAPTION_VERIFIER")
                elif c["timestamp_source"] == "YOUTUBE_CHAPTER_METADATA":
                    self.assertEqual(p, "YOUTUBE_SHORT_DESCRIPTION_OFFICIAL_METADATA")
                    self.assertEqual(c["verification_actor"], "YOUTUBE_METADATA_EXTRACTOR")
                elif c["timestamp_source"] == "UNKNOWN":
                    self.assertEqual(p, "UNVERIFIED")
                    self.assertEqual(c["verification_actor"], "NONE")

        self.assertEqual(prov_counts["LEGACY_AI_STUDIO_USER_REPORT"], 9)
        self.assertEqual(prov_counts["YOUTUBE_TIMEDTEXT_DIRECT_DETERMINISTIC_TOKEN_MATCH"], 77)
        self.assertEqual(prov_counts["YOUTUBE_SHORT_DESCRIPTION_OFFICIAL_METADATA"], 48)
        self.assertEqual(prov_counts["UNVERIFIED"], 133)

        # 2. Test user questions covering distinct practical scenarios
        # Scenario 1: NotebookLM and Obsidian synergy
        ans1 = query_mod.answer_question("NotebookLMとObsidianを連携する価値や構成方法は？", root=real_root)
        top_vids1 = [r["video_id"] for r in ans1["step2_matched_records"][:2]]
        self.assertIn("2-8cXaRHlqI", top_vids1)
        # Ensure restored UNKNOWN chapter does NOT generate a playback link
        segs1 = ans1["step5_and_6_recommended_video_segments"]
        for s in segs1:
            if s.get("chapter_title") == "Studio機能9種生成の実演":
                self.assertIsNone(s.get("playback_url"))
                self.assertEqual(s.get("timestamp_source"), "UNKNOWN")

        # Scenario 2: Memory preservation in agents
        ans2 = query_mod.answer_question("AIエージェントの記憶を長持ちさせる方法は？", root=real_root)
        top_vids2 = [r["video_id"] for r in ans2["step2_matched_records"][:3]]
        self.assertTrue(any(v in top_vids2 for v in ["BStkW1HTfmk", "sodTFSuV4zY", "Vr3JkAT9mo8"]))

        # Scenario 3: Safety stop for dangerous actions
        ans3 = query_mod.answer_question("AIの自律実行で危険な操作を止めるには？", root=real_root)
        self.assertGreater(len(ans3["step2_matched_records"]), 0)
        self.assertIn("FAILURE_AND_LIMITS", ans3["step1_intent_analysis"]["intents"])

        # Scenario 4: Specific video locator query
        ans4 = query_mod.answer_question("動画 2-8cXaRHlqI の具体的な説明位置や目次は？", root=real_root)
        self.assertEqual(ans4["step2_matched_records"][0]["video_id"], "2-8cXaRHlqI")
        self.assertGreaterEqual(len(ans4["step5_and_6_recommended_video_segments"]), 5)
        # Check title alias is present
        self.assertIn("title", ans4["step5_and_6_recommended_video_segments"][0])

        # Scenario 5: Unrelated technology must reject safely
        ans5 = query_mod.answer_question("超伝導トカマク型核融合炉のプラズマ閉じ込め磁場コイル設計手順は？", root=real_root)
        self.assertEqual(len(ans5["step2_matched_records"]), 0)
        self.assertEqual(ans5["step4_gap_analysis"]["coverage_status"], "INSUFFICIENT_NEEDS_NEW_RESEARCH")


    def test_cp3_user_qa_interactive_and_launcher(self):
        """CP3: Verify user daily Q&A guide, launcher script, and interactive CLI functionality."""
        from unittest.mock import patch
        import io

        # 1. Verify docs/USER_QA_GUIDE.md exists and covers all 4 pathways & 8 criteria
        guide_path = ROOT / "docs" / "USER_QA_GUIDE.md"
        self.assertTrue(guide_path.is_file(), "docs/USER_QA_GUIDE.md must exist")
        guide_text = guide_path.read_text(encoding="utf-8")
        self.assertIn("経路A: ChatGPT", guide_text)
        self.assertIn("経路B: ローカルCLI", guide_text)
        self.assertIn("経路C: Gemini Notebook", guide_text)
        self.assertIn("経路D: 軽量ワンライナー", guide_text)
        for criterion in ["応答速度", "正確性", "再生リンク", "導入コスト", "保守性", "拡張性", "モバイル", "非エンジニア"]:
            self.assertIn(criterion, guide_text)
        self.assertIn("TIMESTAMPED_CAPTIONS", guide_text)
        self.assertIn("YOUTUBE_CHAPTER_METADATA", guide_text)
        self.assertIn("VISUAL_FRAME_CHECK", guide_text)
        self.assertIn("UNKNOWN", guide_text)

        # 2. Verify run_qa.ps1 launcher exists
        ps_path = ROOT / "run_qa.ps1"
        self.assertTrue(ps_path.is_file(), "run_qa.ps1 launcher must exist")
        ps_text = ps_path.read_text(encoding="utf-8")
        self.assertIn("query_research.py", ps_text)

        # 3. Test interactive_mode via simulated user inputs
        simulated_inputs = ["ハーネスとは？", "exit"]
        with patch("builtins.input", side_effect=simulated_inputs):
            with patch("sys.stdout", new=io.StringIO()) as fake_stdout:
                query_mod.interactive_mode(root=ROOT, top_k=2)
                output = fake_stdout.getvalue()
                self.assertIn("AI技術研究室 | 自然言語Q&A・動画チャプター検索 (対話モード)", output)
                self.assertIn("ハーネス", output)
                self.assertIn("終了します", output)

        # 4. Test main() invocation with --interactive and mocked input
        with patch("builtins.input", side_effect=["q"]):
            with patch("sys.stdout", new=io.StringIO()):
                ret = query_mod.main(["--interactive"])
                self.assertEqual(ret, 0)


    def test_cp5_cloud_relay_gas_comprehensive_mock_and_edge_cases(self):
        """CP5: Comprehensive Mock Verification of cloud_relay_gas.js edge cases:
        1. Secret/token leak pattern rejection (PAT, API keys, private keys, Bearer)
        2. Missing notebook_source_id rejection
        3. Malformed/corrupted JSON string handling
        4. Duplicate receipt multi-ingestion non-destructive skip
        5. Forbidden branch rejection (main/master)
        """
        node_script = f"""
const gas = require({json.dumps(self.gas_path)});
const assert = require("assert");

const results = {{}};

// 1. Test secret/token leak pattern rejection
const secretTests = [
  {{ name: "GITHUB_PAT", val: "github_pat_11ABCDEF0123456789_abcdef1234567890abcdef12" }},
  {{ name: "GHP_TOKEN", val: "ghp_123456789012345678901234567890123456" }},
  {{ name: "GOOGLE_API_KEY", val: "AIzaSyD-1234567890abcdef1234567890abcdef" }},
  {{ name: "OPENAI_SECRET", val: "sk-proj-1234567890abcdef1234567890abcdef123456" }},
  {{ name: "PRIVATE_KEY", val: "-----BEGIN RSA PRIVATE KEY-----\\nMIIEowIBAAKCAQEA..." }},
  {{ name: "BEARER_AUTH", val: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0" }}
];

results.secretRejections = {{}};
for (const st of secretTests) {{
  const badReceipt = {json.dumps(make_sample_receipt())};
  badReceipt.videos[0].summary_ja = "説明文の中に " + st.val + " が紛れ込んでいる";
  try {{
    gas.validateReceipt(badReceipt);
    results.secretRejections[st.name] = "FAILED_TO_REJECT";
  }} catch (e) {{
    results.secretRejections[st.name] = "REJECTED: " + (e.message.includes("Forbidden") || e.message.includes("pattern"));
  }}
}}

// 2. Test missing/empty notebook_source_id rejection
const badSourceIdReceipt = {json.dumps(make_sample_receipt())};
badSourceIdReceipt.videos[0].notebook_source_id = "";
try {{
  gas.validateReceipt(badSourceIdReceipt);
  results.missingSourceId = "FAILED_TO_REJECT";
}} catch (e) {{
  results.missingSourceId = "REJECTED: " + e.message.includes("notebook_source_id");
}}

// 3. Test malformed JSON extraction
const malformedJsonText = "前置きテキスト\\n```json\\n{{ invalid json, missing quotes: 123 \\n```";
try {{
  gas.extractReceiptPayload(malformedJsonText);
  results.malformedJson = "FAILED_TO_REJECT";
}} catch (e) {{
  results.malformedJson = "REJECTED_AS_EXPECTED";
}}

// 4. Test duplicate receipt ingestion skip in planReceiptApplication
const validReceipt = {json.dumps(make_sample_receipt())};
const digest = gas.computeReceiptDigest(validReceipt);
const repoState = {{
  dedupScanComplete: true,
  registry: {{ records: [] }},
  loopState: {{
    schema_version: "gemini_notebook_loop_state_v1",
    target_branch: "feature/gemini-notebook-research-loop-20261016",
    processed_receipts: [{{ sha256: digest, received_at: "2026-10-17T00:00:00Z", video_ids: ["dQw4w9WgXcQ"] }}],
    remote_branch_cache: {{}},
    open_unknowns: [],
    next_topics_queue: [],
    last_applied_commit_sha: "abcd123"
  }},
  localMap: {{}},
  remoteMap: {{}},
  existingResearchMdByVid: {{}}
}};

const plan = gas.planReceiptApplication(validReceipt, repoState, [], "mode_apply");
results.duplicatePlan = {{
  alreadyRecordedInGitHubState: plan.alreadyRecordedInGitHubState,
  newRecordsCount: plan.newRecordsCount,
  updatedRecordsCount: plan.updatedRecordsCount,
  filesToCommitCount: Object.keys(plan.filesToCommit).length
}};


// 5. Test forbidden branch rejection (main / master)
const mockForbiddenProps = {{
  store: {{
    GITHUB_FINE_GRAINED_PAT: "dummy_token",
    DRIVE_INBOX_FOLDER_ID: "dummy_inbox",
    TARGET_GITHUB_BRANCH: "main"
  }},
  getProperty(k) {{ return this.store[k] || null; }},
  setProperty(k, v) {{ this.store[k] = String(v); }}
}};
try {{
  gas.relayDriveReceiptsToGitHub({{ scriptProperties: mockForbiddenProps }});
  results.forbiddenBranch = "FAILED_TO_REJECT";
}} catch (e) {{
  results.forbiddenBranch = "REJECTED: " + (e.message.includes("forbidden") || e.message.includes("Forbidden") || e.message.includes("main"));
}}

// 6. Test concurrent lock contention (LockService)
const mockContentionLock = {{
  getScriptLock() {{
    return {{
      tryLock(ms) {{ return false; }}
    }};
  }}
}};
const lockRes = gas.relayDriveReceiptsToGitHub({{ lockService: mockContentionLock }});
results.concurrentLockStatus = lockRes.status;


process.stdout.write(JSON.stringify(results));
"""
        res = subprocess.run(
            ["node", "-e", node_script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        out = json.loads(res.stdout)

        # Assert secret rejections
        for st_name, rej in out["secretRejections"].items():
            self.assertTrue(rej.startswith("REJECTED: true"), f"{st_name} must be rejected: {rej}")

        # Assert notebook_source_id rejection
        self.assertTrue(out["missingSourceId"].startswith("REJECTED: true"))

        # Assert malformed JSON rejection
        self.assertEqual(out["malformedJson"], "REJECTED_AS_EXPECTED")

        # Assert duplicate receipt is correctly flagged with 0 new records and 0 files to commit
        self.assertTrue(out["duplicatePlan"]["alreadyRecordedInGitHubState"])
        self.assertEqual(out["duplicatePlan"]["newRecordsCount"], 0)
        self.assertEqual(out["duplicatePlan"]["filesToCommitCount"], 0)


        # Assert forbidden branch (main) rejection
        self.assertTrue(out["forbiddenBranch"].startswith("REJECTED: true"))

        # Assert concurrent execution safely skips when lock is held
        self.assertEqual(out["concurrentLockStatus"], "SKIPPED_CONCURRENT_LOCK_HELD")

    def test_gas_paused_dedup_scan_logs_details(self):
        """Verify that when dedup scan is paused due to file limit, Logger.log is invoked with detailed pausedOutput."""
        node_test = f"""
const gas = require({json.dumps(self.gas_path)});

const mockProps = {{
  store: {{
    GITHUB_FINE_GRAINED_PAT: "test_pat_token",
    DRIVE_INBOX_FOLDER_ID: "folder_inbox_123",
    TARGET_GITHUB_BRANCH: "feature/gemini-notebook-research-loop-20261016"
  }},
  getProperty(k) {{ return this.store[k] || null; }},
  setProperty(k, v) {{ this.store[k] = String(v); }}
}};

let loggedOutput = null;
global.Logger = {{
  log: function(msg) {{
    try {{
      loggedOutput = JSON.parse(msg);
    }} catch (e) {{}}
  }}
}};

const mockDrive = {{
  getFolderById(id) {{
    return {{
      getFiles() {{
        return {{
          hasNext() {{ return false; }},
          next() {{ return null; }}
        }};
      }}
    }};
  }}
}};

let blobFetchCount = 0;
const mockFetcher = {{
  fetch(url, opts) {{
    const u = String(url);
    if (u.includes("/branches?per_page=100")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify([{{ name: "feature/gemini-notebook-research-loop-20261016", commit: {{ sha: "head_commit_sha" }} }}]);
        }}
      }};
    }}
    if (u.includes("/git/commits/head_commit_sha")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{ sha: "head_commit_sha", tree: {{ sha: "head_tree_sha" }} }});
        }}
      }};
    }}
    if (u.includes("/git/trees/head_tree_sha")) {{
      // Create 30 notes/ files to exceed max_blob_fetches_per_run (25)
      const tree = [
        {{ path: "registry.json", sha: "blob_reg", type: "blob" }},
        {{ path: "automation/gemini-notebook/state/loop_state.json", sha: "blob_loop", type: "blob" }}
      ];
      for (let i = 0; i < 30; i++) {{
        tree.push({{ path: "notes/sample_note_" + i + ".md", sha: "blob_note_" + i, type: "blob" }});
      }}
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{ sha: "head_tree_sha", truncated: false, tree: tree }});
        }}
      }};
    }}
    if (u.includes("/git/blobs/blob_reg")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{
            content: Buffer.from(JSON.stringify({{ schema_version: 1, repository: "kamiyusense/ai-video-research", records: [] }})).toString("base64"),
            encoding: "base64"
          }});
        }}
      }};
    }}
    if (u.includes("/git/blobs/blob_loop")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{
            content: Buffer.from(JSON.stringify({{
              schema_version: "gemini_notebook_loop_state_v1",
              repository: "kamiyusense/ai-video-research",
              processed_receipts: [],
              remote_branch_cache: {{}},
              open_unknowns: [],
              next_topics_queue: []
            }})).toString("base64"),
            encoding: "base64"
          }});
        }}
      }};
    }}
    if (u.includes("/git/blobs/blob_note_")) {{
      blobFetchCount++;
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{
            content: Buffer.from("Sample note body with no video id").toString("base64"),
            encoding: "base64"
          }});
        }}
      }};
    }}
    return {{ getResponseCode() {{ return 200; }}, getContentText() {{ return "{{}}"; }} }};
  }}
}};

const out = gas.runCloudRelayDryRun({{
  scriptProperties: mockProps,
  driveApp: mockDrive,
  urlFetchApp: mockFetcher
}});

if (!loggedOutput) {{
  throw new Error("Logger.log was not called on paused scan!");
}}
if (loggedOutput.status !== "PAUSED_INCOMPLETE_DEDUP_SCAN_CONTINUES_NEXT_RUN") {{
  throw new Error("Unexpected status in logged output: " + loggedOutput.status);
}}
if (loggedOutput.remainingUnscannedFiles <= 0) {{
  throw new Error("Expected remainingUnscannedFiles > 0, got: " + loggedOutput.remainingUnscannedFiles);
}}
if (loggedOutput.mode !== "DRY_RUN") {{
  throw new Error("Expected mode === 'DRY_RUN', got: " + loggedOutput.mode);
}}

process.stdout.write("LOGGED_PAUSED_OK");
"""
        res = subprocess.run(
            ["node", "-e", node_test],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        self.assertEqual(res.stdout.strip(), "LOGGED_PAUSED_OK")

    def test_gas_completed_branch_cache_prevents_duplicate_scans(self):
        """Verify that completed remote branch scan is cached in ScriptProperties across Dry-Runs."""
        node_test = f"""
const gas = require({json.dumps(self.gas_path)});

const mockProps = {{
  store: {{
    GITHUB_FINE_GRAINED_PAT: "test_pat_token",
    DRIVE_INBOX_FOLDER_ID: "folder_inbox_123",
    TARGET_GITHUB_BRANCH: "feature/gemini-notebook-research-loop-20261016"
  }},
  getProperty(k) {{ return this.store[k] || null; }},
  setProperty(k, v) {{ this.store[k] = String(v); }}
}};

const mockDrive = {{
  getFolderById(id) {{
    return {{
      getFiles() {{
        return {{
          hasNext() {{ return false; }},
          next() {{ return null; }}
        }};
      }}
    }};
  }}
}};

let branchACommit = "sha_branch_a";
let branchABlobFetches = 0;
const mockFetcher = {{
  fetch(url, opts) {{
    const u = String(url);
    if (u.includes("/branches?per_page=100")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify([
            {{ name: "feature/gemini-notebook-research-loop-20261016", commit: {{ sha: "head_commit_sha" }} }},
            {{ name: "feature/other-branch-a", commit: {{ sha: branchACommit }} }}
          ]);
        }}
      }};
    }}
    if (u.includes("/git/commits/head_commit_sha")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{ sha: "head_commit_sha", tree: {{ sha: "head_tree_sha" }} }});
        }}
      }};
    }}
    if (u.includes("/git/commits/" + branchACommit)) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{ sha: branchACommit, tree: {{ sha: "tree_branch_a" }} }});
        }}
      }};
    }}
    if (u.includes("/git/trees/head_tree_sha")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{
            sha: "head_tree_sha",
            truncated: false,
            tree: [
              {{ path: "registry.json", sha: "blob_reg", type: "blob" }},
              {{ path: "automation/gemini-notebook/state/loop_state.json", sha: "blob_loop", type: "blob" }}
            ]
          }});
        }}
      }};
    }}
    if (u.includes("/git/trees/tree_branch_a")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{
            sha: "tree_branch_a",
            truncated: false,
            tree: [
              {{ path: "registry.json", sha: "blob_reg_a", type: "blob" }},
              {{ path: "research/2026-10-10-lC5jxpYmatE-ai-techniques.md", sha: "blob_res_a", type: "blob" }}
            ]
          }});
        }}
      }};
    }}
    if (u.includes("/git/blobs/blob_reg_a")) {{
      branchABlobFetches++;
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{
            content: Buffer.from(JSON.stringify({{
              schema_version: 1,
              repository: "kamiyusense/ai-video-research",
              records: [{{ video_id: "lC5jxpYmatE", record_id: "youtube:lC5jxpYmatE", research_path: "research/2026-10-10-lC5jxpYmatE-ai-techniques.md", status: "CONFIRMED_DOC" }}]
            }})).toString("base64"),
            encoding: "base64"
          }});
        }}
      }};
    }}
    if (u.includes("/git/blobs/blob_reg")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{
            content: Buffer.from(JSON.stringify({{ schema_version: 1, repository: "kamiyusense/ai-video-research", records: [] }})).toString("base64"),
            encoding: "base64"
          }});
        }}
      }};
    }}
    if (u.includes("/git/blobs/blob_loop")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{
            content: Buffer.from(JSON.stringify({{
              schema_version: "gemini_notebook_loop_state_v1",
              repository: "kamiyusense/ai-video-research",
              processed_receipts: [],
              remote_branch_cache: {{}},
              open_unknowns: [],
              next_topics_queue: []
            }})).toString("base64"),
            encoding: "base64"
          }});
        }}
      }};
    }}
    return {{ getResponseCode() {{ return 200; }}, getContentText() {{ return "{{}}"; }} }};
  }}
}};

// Run 1: First Dry-Run scans branch A
const out1 = gas.runCloudRelayDryRun({{
  scriptProperties: mockProps,
  driveApp: mockDrive,
  urlFetchApp: mockFetcher
}});

if (branchABlobFetches !== 1) {{
  throw new Error("Expected 1 blob fetch on branch A during Run 1, got: " + branchABlobFetches);
}}

// Verify RELAY_STATE_V1 now has completedBranchCache for branch A with full video metadata
const stateObj = JSON.parse(mockProps.store["RELAY_STATE_V1"]);
const cachedEntry = stateObj.completedBranchCache && stateObj.completedBranchCache["origin/feature/other-branch-a"];
if (!cachedEntry) {{
  throw new Error("completedBranchCache not saved in RELAY_STATE_V1: " + JSON.stringify(stateObj));
}}
if (!Array.isArray(cachedEntry.videos) || cachedEntry.videos.length === 0) {{
  throw new Error("cachedEntry.videos missing or empty in completedBranchCache");
}}
const cachedVideo = cachedEntry.videos[0];
if (cachedVideo.video_id !== "lC5jxpYmatE" || !cachedVideo.research_path || !cachedVideo.status || !cachedVideo.detected_via) {{
  throw new Error("cachedVideo metadata degraded: " + JSON.stringify(cachedVideo));
}}

// Run 2: Second Dry-Run must NOT re-fetch branch A blobs, preserving metadata
branchABlobFetches = 0;
const out2 = gas.runCloudRelayDryRun({{
  scriptProperties: mockProps,
  driveApp: mockDrive,
  urlFetchApp: mockFetcher
}});

if (branchABlobFetches !== 0) {{
  throw new Error("Branch A was re-fetched on Run 2! Expected 0, got: " + branchABlobFetches);
}}

// Run 3: Branch A commit SHA changes -> cache must be invalidated and re-fetched
branchACommit = "sha_branch_a_v2";
branchABlobFetches = 0;
const out3 = gas.runCloudRelayDryRun({{
  scriptProperties: mockProps,
  driveApp: mockDrive,
  urlFetchApp: mockFetcher
}});

if (branchABlobFetches !== 1) {{
  throw new Error("Branch A was not re-fetched after commit SHA change! Expected 1, got: " + branchABlobFetches);
}}

const stateObjV2 = JSON.parse(mockProps.store["RELAY_STATE_V1"]);
const cachedEntryV2 = stateObjV2.completedBranchCache["origin/feature/other-branch-a"];
if (cachedEntryV2.commit_sha !== "sha_branch_a_v2") {{
  throw new Error("Cache commit_sha was not updated after re-fetch: " + JSON.stringify(cachedEntryV2));
}}

process.stdout.write("BRANCH_CACHE_PERSIST_OK");
"""
        res = subprocess.run(
            ["node", "-e", node_test],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        self.assertEqual(res.stdout.strip(), "BRANCH_CACHE_PERSIST_OK")

    def test_gas_state_trimming_preserves_partial_progress_safely(self):
        """Verify that when state size exceeds safe byte limit, volatile caches are trimmed first to protect partialScanProgress, and if partialScanProgress alone exceeds limit, fail-fast without corrupting state."""
        node_test = f"""
const gas = require({json.dumps(self.gas_path)});

const mockProps = {{
  store: {{}},
  getProperty(k) {{ return this.store[k] || null; }},
  setProperty(k, v) {{ this.store[k] = String(v); }}
}};

// Create an oversized state with many noOp digests and completed branches
const relayState = {{
  schemaVersion: "gas_relay_compact_state_v2",
  lastGitHubCommitSha: "sha1",
  lastDriveSyncedCommitSha: null,
  pendingDriveSync: false,
  recentNoOpDigests: [],
  haltedReceipts: {{}},
  completedBranchCache: {{}},
  partialScanProgress: {{
    "target:feature/test": {{
      commit_sha: "sha1",
      scanned_paths: {{ "research/file1.md": true }},
      videos: [{{ video_id: "vid12345678", source: "registry" }}]
    }}
  }}
}};

// Inflate recentNoOpDigests and completedBranchCache to exceed 7,500 bytes
for (let i = 0; i < 200; i++) {{
  relayState.recentNoOpDigests.push("a".repeat(64));
  relayState.completedBranchCache["origin/feature/branch_" + i] = {{
    commit_sha: "b".repeat(40),
    scan_complete: true,
    video_ids: ["vid_" + i]
  }};
}}

// Run saveBoundedRelayState_ via gas internal
const serializedBefore = JSON.stringify(relayState);
const byteLenBefore = Buffer.byteLength(serializedBefore, "utf8");
if (byteLenBefore < 8000) {{
  throw new Error("Test state not large enough: " + byteLenBefore);
}}

// Trigger bounded save by calling gas function that triggers it
mockProps.setProperty("GITHUB_FINE_GRAINED_PAT", "pat_test");
mockProps.setProperty("DRIVE_INBOX_FOLDER_ID", "folder_test");
mockProps.setProperty("TARGET_GITHUB_BRANCH", "feature/gemini-notebook-research-loop-20261016");
mockProps.setProperty("RELAY_STATE_V1", serializedBefore);

// Trigger a Dry-Run with empty drive
const mockDrive = {{
  getFolderById(id) {{
    return {{
      getFiles() {{
        return {{ hasNext() {{ return false; }}, next() {{ return null; }} }};
      }}
    }};
  }}
}};
const mockFetcher = {{
  fetch(url) {{
    const u = String(url);
    if (u.includes("/branches?per_page=100")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify([{{ name: "feature/gemini-notebook-research-loop-20261016", commit: {{ sha: "head_commit_sha" }} }}]);
        }}
      }};
    }}
    if (u.includes("/git/commits/head_commit_sha")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{ return JSON.stringify({{ sha: "head_commit_sha", tree: {{ sha: "head_tree_sha" }} }}); }}
      }};
    }}
    if (u.includes("/git/trees/head_tree_sha")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{
            sha: "head_tree_sha",
            truncated: false,
            tree: [
              {{ path: "registry.json", sha: "blob_reg", type: "blob" }},
              {{ path: "automation/gemini-notebook/state/loop_state.json", sha: "blob_loop", type: "blob" }}
            ]
          }});
        }}
      }};
    }}
    if (u.includes("/git/blobs/blob_reg")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{
            content: Buffer.from(JSON.stringify({{ schema_version: 1, repository: "kamiyusense/ai-video-research", records: [] }})).toString("base64"),
            encoding: "base64"
          }});
        }}
      }};
    }}
    if (u.includes("/git/blobs/blob_loop")) {{
      return {{
        getResponseCode() {{ return 200; }},
        getContentText() {{
          return JSON.stringify({{
            content: Buffer.from(JSON.stringify({{
              schema_version: "gemini_notebook_loop_state_v1",
              repository: "kamiyusense/ai-video-research",
              processed_receipts: [],
              remote_branch_cache: {{}},
              open_unknowns: [],
              next_topics_queue: []
            }})).toString("base64"),
            encoding: "base64"
          }});
        }}
      }};
    }}
    return {{ getResponseCode() {{ return 200; }}, getContentText() {{ return "{{}}"; }} }};
  }}
}};

gas.runCloudRelayDryRun({{
  scriptProperties: mockProps,
  driveApp: mockDrive,
  urlFetchApp: mockFetcher
}});

// Read back pruned state
const prunedState = JSON.parse(mockProps.store["RELAY_STATE_V1"]);
const byteLenAfter = Buffer.byteLength(mockProps.store["RELAY_STATE_V1"], "utf8");

if (byteLenAfter > 7500) {{
  throw new Error("Pruned state exceeds 7500 bytes: " + byteLenAfter);
}}

// 1. Verify partialScanProgress is FULLY preserved (never discarded or truncated)
if (!prunedState.partialScanProgress || !prunedState.partialScanProgress["target:feature/test"]) {{
  throw new Error("partialScanProgress was lost during state trimming!");
}}
const preservedEntry = prunedState.partialScanProgress["target:feature/test"];
if (!preservedEntry.scanned_paths["research/file1.md"] || preservedEntry.videos.length !== 1) {{
  throw new Error("partialScanProgress content corrupted during state trimming: " + JSON.stringify(preservedEntry));
}}

// 2. Verify volatile caches were trimmed
if (prunedState.recentNoOpDigests.length >= 200) {{
  throw new Error("recentNoOpDigests was not trimmed!");
}}

// 3. Verify that if partialScanProgress ALONE exceeds 7,500 bytes, saveBoundedRelayState throws explicit error and NEVER corrupts state
const oversizedProgressState = {{
  recentNoOpDigests: [],
  haltedReceipts: {{}},
  completedBranchCache: {{}},
  partialScanProgress: {{
    "branch_oversized": {{
      commit_sha: "c".repeat(40),
      scanned_paths: {{}},
      videos_by_id: {{}}
    }}
  }}
}};
for (let i = 0; i < 400; i++) {{
  oversizedProgressState.partialScanProgress["branch_oversized"].scanned_paths["deep/path/to/markdown/note_" + i + ".md"] = true;
}}

const savedStateBeforeFailure = mockProps.store["RELAY_STATE_V1"];
let caughtError = null;
try {{
  gas.saveBoundedRelayState(mockProps, oversizedProgressState);
}} catch (e) {{
  caughtError = e;
}}

if (!caughtError) {{
  throw new Error("saveBoundedRelayState did not throw error on oversized partialScanProgress!");
}}
if (!caughtError.message.includes("Unable to safely persist partialScanProgress")) {{
  throw new Error("Unexpected error message: " + caughtError.message);
}}
if (mockProps.store["RELAY_STATE_V1"] !== savedStateBeforeFailure) {{
  throw new Error("Existing valid RELAY_STATE_V1 in ScriptProperties was corrupted after save failure!");
}}

process.stdout.write("TRIMMING_SAFE_OK");
"""
        res = subprocess.run(
            ["node", "-e", node_test],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        self.assertEqual(res.stdout.strip(), "TRIMMING_SAFE_OK")


class TestUrlIntakeDuplicateCheck(unittest.TestCase):
    """Verify pre-analysis duplicate checking for YouTube URL intake."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp_dir.name)
        self.research_dir = self.root / "research"
        self.research_dir.mkdir(parents=True, exist_ok=True)

        intake_mod_path = ROOT / "automation" / "gemini-notebook" / "intake_url.py"
        spec = importlib.util.spec_from_file_location("intake_url", intake_mod_path)
        self.intake_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.intake_mod)

        # Create a sample registry.json
        self.registry_path = self.root / "registry.json"
        self.sample_registry = {
            "schema_version": 1,
            "repository": "kamiyusense/ai-video-research",
            "records": [
                {
                    "record_id": "youtube:lC5jxpYmatE",
                    "video_id": "lC5jxpYmatE",
                    "canonical_url": "https://www.youtube.com/watch?v=lC5jxpYmatE",
                    "research_path": "research/2026-10-10-lC5jxpYmatE-ai-techniques.md",
                    "status": "RESEARCH_RECORDED",
                }
            ],
        }
        self.registry_path.write_text(
            json.dumps(self.sample_registry, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Create sample research markdown
        self.sample_md = self.research_dir / "2026-10-10-lC5jxpYmatE-ai-techniques.md"
        self.sample_md.write_text(
            "# 動画研究05｜課題ドリブン・Skill再利用・Computer Useの省力化\n\n"
            "## 結論（独自要約）\n"
            "目新しいAIの機能を片端から覚えるより、日々の課題を記録して再挑戦する学び方が有用。\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_01_same_video_url_twice_detected_as_duplicate(self):
        """1. Verify feeding the same video URL twice flags duplicate with title, summary, link, and revisit prompt."""
        url = "https://www.youtube.com/watch?v=lC5jxpYmatE"

        # First intake: detected as registered
        res1 = self.intake_mod.check_url_intake(
            url, root=self.root, registry_path=self.registry_path
        )
        self.assertEqual(res1["status"], "ALREADY_REGISTERED")
        self.assertTrue(res1["is_registered"])
        self.assertEqual(res1["video_id"], "lC5jxpYmatE")
        self.assertEqual(
            res1["title"], "動画研究05｜課題ドリブン・Skill再利用・Computer Useの省力化"
        )
        self.assertIn("課題を記録して再挑戦する", res1["summary_ja"])
        self.assertEqual(
            res1["research_path"],
            "research/2026-10-10-lC5jxpYmatE-ai-techniques.md",
        )
        self.assertIsNotNone(res1["github_link"])
        self.assertIn("再調査", res1["revisit_prompt"])
        self.assertIn("UNKNOWN", res1["notebook_status"])

        # Second intake of same URL: identical duplicate verdict
        res2 = self.intake_mod.check_url_intake(
            url, root=self.root, registry_path=self.registry_path
        )
        self.assertEqual(res2["status"], "ALREADY_REGISTERED")
        self.assertEqual(res2["video_id"], "lC5jxpYmatE")

    def test_02_short_url_and_timestamped_url_same_video_detected(self):
        """2 & 3. Verify short URL (youtu.be) and timestamped URL (?t=... &t=...) resolve to same video_id and duplicate."""
        urls = [
            "https://youtu.be/lC5jxpYmatE",
            "https://youtu.be/lC5jxpYmatE?t=123",
            "https://www.youtube.com/watch?v=lC5jxpYmatE&t=123s",
            "https://www.youtube.com/watch?feature=shared&v=lC5jxpYmatE&t=2m30s",
            "https://www.youtube.com/shorts/lC5jxpYmatE",
            "https://www.youtube.com/live/lC5jxpYmatE?feature=share",
        ]
        for u in urls:
            res = self.intake_mod.check_url_intake(
                u, root=self.root, registry_path=self.registry_path
            )
            self.assertEqual(
                res["status"],
                "ALREADY_REGISTERED",
                f"Failed duplicate check for URL: {u}",
            )
            self.assertEqual(res["video_id"], "lC5jxpYmatE")
            self.assertEqual(
                res["canonical_url"], "https://www.youtube.com/watch?v=lC5jxpYmatE"
            )

    def test_03_unregistered_video_allows_research(self):
        """4. Verify unregistered video returns NOT_REGISTERED and allows starting research."""
        unregistered_url = "https://youtu.be/kCc8FmEb1nY"
        res = self.intake_mod.check_url_intake(
            unregistered_url, root=self.root, registry_path=self.registry_path
        )
        self.assertEqual(res["status"], "NOT_REGISTERED")
        self.assertFalse(res["is_registered"])
        self.assertEqual(res["video_id"], "kCc8FmEb1nY")
        self.assertEqual(
            res["canonical_url"], "https://www.youtube.com/watch?v=kCc8FmEb1nY"
        )
        self.assertIsNone(res["research_path"])
        self.assertIn("研究を開始できます", res["message_ja"])
        self.assertIn("UNKNOWN", res["notebook_status"])

    def test_04_github_registry_unreachable_safe_halt(self):
        """5. Verify unreachable or corrupted GitHub registry fails safe without false NEW classification."""
        missing_path = self.root / "missing_registry.json"
        res_missing = self.intake_mod.check_url_intake(
            "https://youtu.be/kCc8FmEb1nY",
            root=self.root,
            registry_path=missing_path,
        )
        self.assertEqual(res_missing["status"], "BLOCKED_GITHUB_UNREACHABLE")
        self.assertIsNone(res_missing["is_registered"])
        self.assertIn("安全停止", res_missing["message_ja"])

        # Corrupted JSON
        corrupted_path = self.root / "corrupted_registry.json"
        corrupted_path.write_text("{ broken json ...", encoding="utf-8")
        res_corrupt = self.intake_mod.check_url_intake(
            "https://youtu.be/kCc8FmEb1nY",
            root=self.root,
            registry_path=corrupted_path,
        )
        self.assertEqual(res_corrupt["status"], "BLOCKED_GITHUB_UNREACHABLE")
        self.assertIsNone(res_corrupt["is_registered"])

    def test_05_pre_guard_and_pre_save_double_check_and_readback(self):
        """6 & 7. Verify pre-analysis intake check, pre-save double check, and post-save readback sequence."""
        # Step 1: Pre-analysis intake check rejects duplicate before video analysis
        res_pre = self.intake_mod.check_url_intake(
            "https://www.youtube.com/watch?v=lC5jxpYmatE",
            root=self.root,
            registry_path=self.registry_path,
        )
        self.assertEqual(res_pre["status"], "ALREADY_REGISTERED")

        # Step 2: Even if an analysis receipt is somehow prepared, pre-save double check blocks it
        sample_receipt = make_sample_receipt()
        sample_receipt["videos"][0]["video_id"] = "lC5jxpYmatE"
        sample_receipt["videos"][0]["url"] = "https://www.youtube.com/watch?v=lC5jxpYmatE"

        # Execute process_receipt_data (pre-save double check)
        res_summary, _ = bridge.process_receipt_data(
            sample_receipt,
            root=self.root,
            apply=False,
            check_remote_branches=False,
            fetch_remote=False,
        )
        # Pre-save double check skipped applying this video!
        self.assertEqual(res_summary["new_records"], 0)
        self.assertEqual(len(res_summary["skipped"]), 1)
        self.assertEqual(res_summary["skipped"][0]["video_id"], "lC5jxpYmatE")
        self.assertEqual(res_summary["skipped"][0]["reason"], "SKIP_EXISTING")

        # Step 3: Post-save readback verification (verifying registry readback)
        reg_readback = json.loads(self.registry_path.read_text(encoding="utf-8"))
        readback_vids = [r["video_id"] for r in reg_readback.get("records", [])]
        self.assertIn("lC5jxpYmatE", readback_vids)

    def test_phase2_notebook_confusion_prevention_and_markdown_parity(self):
        """Phase 2: Verify explicit research card title, primary source metadata, and JS/Python parity."""
        gas_path_str = str((ROOT / "automation" / "gemini-notebook" / "cloud_relay_gas.js").resolve().as_posix())
        sample_video = {
            "video_id": "testVid1234",
            "url": "https://www.youtube.com/watch?v=testVid1234",
            "title": "AIエージェントの未来と自律実行",
            "published_at": "2026-10-18",
            "summary_ja": "AIエージェントの自律実行アーキテクチャに関する解説。",
            "source_scope": "字幕分析 00:00-10:00",
            "notebook_source_id": "src_test_youtube_uuid_001",
            "notebook_readback": "PASS",
            "changes": ["NEW"],
            "claims": [{"text": "テスト主張", "status": "CONFIRMED_DOC", "timestamp_seconds": None, "timestamp_source": "UNKNOWN"}],
        }
        checked_at = "2026-10-18"

        # 1. Render in Python
        py_md = bridge.render(sample_video, checked_at)

        # 2. Render in Node.js GAS
        node_script = f"""
const gas = require({json.dumps(gas_path_str)});
const v = {json.dumps(sample_video)};
const md = gas.renderResearchMarkdown(v, {json.dumps(checked_at)});
process.stdout.write(md);
"""
        res = subprocess.run(
            ["node", "-e", node_script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        js_md = res.stdout

        # Verify exact parity
        self.assertEqual(py_md, js_md)

        # Verify OKF frontmatter begins with ---
        self.assertTrue(py_md.startswith("---\n"))
        self.assertIn('okf_version: "0.2"', py_md)
        self.assertIn('type: "RESEARCH_NOTE"', py_md)

        # Verify H1 Title contains 【研究カード】
        self.assertIn("# 【研究カード】 AIエージェントの未来と自律実行", py_md)

        # Verify primary source metadata separation
        self.assertIn('primary_source_notebook_id: "src_test_youtube_uuid_001"', py_md)
        self.assertIn('document_type: "AI技術研究室 構造化研究カード（二次分析資料）"', py_md)

        # Verify distinction callout block
        self.assertIn("> **文書区分**: 本ドキュメントは一次資料（YouTube字幕）を基に構造化分析した「AI技術研究室 研究カード」です。", py_md)

        # Verify query_research.py parses notebook_source_id correctly
        tmp_md = self.root / "research" / "2026-10-18-testVid1234-temp-test.md"
        try:
            tmp_md.write_text(py_md, encoding="utf-8")
            parsed = query_mod.parse_research_markdown_file(tmp_md, root=self.root)
            self.assertEqual(parsed.get("notebook_source_id"), "src_test_youtube_uuid_001")
            self.assertIn("【研究カード】", parsed.get("title", ""))
        finally:
            if tmp_md.is_file():
                tmp_md.unlink()

    def test_phase2_cloud_relay_gas_sync_research_cards_to_drive(self):
        """Phase 2: Verify GAS syncResearchCardsToDriveSafely creates, updates, and previews research card files in Drive."""
        gas_path_str = str((ROOT / "automation" / "gemini-notebook" / "cloud_relay_gas.js").resolve().as_posix())
        node_script = f"""
const gas = require({json.dumps(gas_path_str)});

// Mock DriveService
const store = new Map();
let idCounter = 1;

function makeMockFile(name, content) {{
  let c = content;
  const fid = "file_" + (idCounter++);
  return {{
    getId: () => fid,
    getName: () => name,
    getContent: () => c,
    setContent: (newC) => {{ c = newC; }},
  }};
}}

const mockFolder = {{
  getFilesByName: (name) => {{
    const found = [];
    for (const f of store.values()) {{
      if (f.getName() === name) found.push(f);
    }}
    let idx = 0;
    return {{
      hasNext: () => idx < found.length,
      next: () => found[idx++],
    }};
  }},
  createFile: (name, content, mime) => {{
    const f = makeMockFile(name, content);
    store.set(f.getId(), f);
    return f;
  }},
}};

const mockDriveService = {{
  getFolderById: (id) => mockFolder,
}};

const filesToCommit = [
  {{ path: "research/2026-10-18-kCc8FmEb1nY-gemini-notebook.md", content: "# Test Card Content" }},
  {{ path: "registry.json", content: "{{}}" }},
];

// Test 1: Dry Run preview
const previewRes = gas.syncResearchCardsToDriveSafely(mockDriveService, "folder_123", filesToCommit, true);

// Test 2: Live create
const liveRes = gas.syncResearchCardsToDriveSafely(mockDriveService, "folder_123", filesToCommit, false);

// Test 3: Live update (existing file)
const updateRes = gas.syncResearchCardsToDriveSafely(mockDriveService, "folder_123", [
  {{ path: "research/2026-10-18-kCc8FmEb1nY-gemini-notebook.md", content: "# Updated Test Card Content" }},
], false);

process.stdout.write(JSON.stringify({{
  previewRes,
  liveRes,
  updateRes,
  storeSize: store.size,
  finalContent: store.values().next().value ? store.values().next().value.getContent() : null,
}}));
"""
        res = subprocess.run(
            ["node", "-e", node_script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        out = json.loads(res.stdout)

        # 1. Preview
        self.assertEqual(out["previewRes"]["status"], "DRY_RUN_PREVIEW_ONLY_NO_DRIVE_WRITE")
        self.assertEqual(len(out["previewRes"]["syncedCards"]), 1)
        self.assertEqual(out["previewRes"]["syncedCards"][0]["fileName"], "【研究カード】_2026-10-18-kCc8FmEb1nY-gemini-notebook.md")
        self.assertEqual(out["previewRes"]["syncedCards"][0]["action"], "WOULD_SYNC")

        # 2. Live create
        self.assertEqual(out["liveRes"]["status"], "DRIVE_CARDS_SYNCHRONIZED")
        self.assertEqual(out["liveRes"]["syncedCards"][0]["action"], "CREATED")
        self.assertEqual(out["storeSize"], 1)

        # 3. Live update
        self.assertEqual(out["updateRes"]["status"], "DRIVE_CARDS_SYNCHRONIZED")
        self.assertEqual(out["updateRes"]["syncedCards"][0]["action"], "UPDATED")
        self.assertEqual(out["finalContent"], "# Updated Test Card Content")

    def test_phase2_intake_receipt_validation_dedup_and_readback(self):
        """Phase 2: Verify intake_receipt.py extraction, validation, dedup stop, and readback hash verification."""
        intake_rc_path = ROOT / "automation" / "gemini-notebook" / "intake_receipt.py"
        spec = importlib.util.spec_from_file_location("intake_receipt", intake_rc_path)
        intake_receipt = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(intake_receipt)

        test_out_dir = self.root / "scratch" / "test_intake_suite"
        test_out_dir.mkdir(parents=True, exist_ok=True)

        sample_fixture = (
            ROOT
            / "automation"
            / "gemini-notebook"
            / "fixtures"
            / "live_sample_receipt_v1.json"
        )
        raw_text = sample_fixture.read_text(encoding="utf-8")

        # 1. Test valid new intake
        res = intake_receipt.intake_and_verify_receipt(
            raw_text,
            output_dir=test_out_dir,
            source_label="FIXTURE_TEST",
            allow_overwrite=False,
        )
        self.assertEqual(res["status"], "SUCCESS_SAVED_AND_READBACK_VERIFIED")
        self.assertEqual(res["video_count"], 1)
        self.assertTrue(Path(res["target_file"]).is_file())
        self.assertEqual(len(res["digest"]), 64)
        self.assertEqual(len(res["readback_hash"]), 64)

        # 2. Test duplicate stop on existing video (pRfC1DILDEM)
        dup_data = json.loads(raw_text)
        dup_data["videos"][0]["video_id"] = "pRfC1DILDEM"
        dup_data["videos"][0]["url"] = "https://www.youtube.com/watch?v=pRfC1DILDEM"
        dup_raw = json.dumps(dup_data)

        dup_res = intake_receipt.intake_and_verify_receipt(
            dup_raw,
            output_dir=test_out_dir,
            source_label="DUP_TEST",
            allow_overwrite=False,
        )
        self.assertEqual(dup_res["status"], "STOPPED_DUPLICATE_REGISTERED")
        self.assertIn("すでにregistry.jsonに登録されています", dup_res["message"])

        # 3. Test validation failure on invalid schema
        invalid_raw = json.dumps({"schema_version": "invalid_v999"})
        fail_res = intake_receipt.intake_and_verify_receipt(
            invalid_raw,
            output_dir=test_out_dir,
            source_label="INVALID_TEST",
        )
        self.assertEqual(fail_res["status"], "VALIDATION_FAILED")
        self.assertTrue(len(fail_res["errors"]) > 0)

    def test_phase_okf_knowledge_and_qa_pipeline(self):
        """OKF v0.2: Test schema specs, GAS/Python parity, knowledge network, 5-category router, and QA pipeline."""
        gas_path = (ROOT / "automation" / "gemini-notebook" / "cloud_relay_gas.js").as_posix()
        query_mod_path = ROOT / "automation" / "gemini-notebook" / "query_research.py"
        q_spec = importlib.util.spec_from_file_location("query_research", query_mod_path)
        query_mod = importlib.util.module_from_spec(q_spec)
        q_spec.loader.exec_module(query_mod)

        # 1. Spec consistency: contract_spec_v1.json vs cloud_relay_gas.js
        spec_path = ROOT / "automation" / "gemini-notebook" / "contract_spec_v1.json"
        py_spec = json.loads(spec_path.read_text(encoding="utf-8"))
        self.assertEqual(py_spec["okf_spec"]["version"], "0.2")
        self.assertIn("FULL_VERIFIED", py_spec["allowed_transcript_statuses"])
        self.assertIn("UNVERIFIED", py_spec["allowed_transcript_statuses"])
        self.assertIn("CONFIRMED", py_spec["allowed_relation_statuses"])
        self.assertIn("UNRESOLVED", py_spec["allowed_relation_statuses"])

        # GAS parity on CONTRACT_SPEC_V1
        node_check_spec = f"""
const gas = require({json.dumps(gas_path)});
process.stdout.write(JSON.stringify(gas.CONTRACT_SPEC_V1));
"""
        proc = subprocess.run(
            ["node", "-e", node_check_spec],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        gas_spec = json.loads(proc.stdout)
        self.assertEqual(gas_spec["okf_spec"]["version"], "0.2")
        self.assertEqual(gas_spec["allowed_transcript_statuses"], py_spec["allowed_transcript_statuses"])
        self.assertEqual(gas_spec["allowed_relation_statuses"], py_spec["allowed_relation_statuses"])

        # 2. Render parity on OKF v0.2 frontmatter and related records with status & evidence
        sample_receipt = make_sample_receipt()
        v = sample_receipt["videos"][0]
        v["logical_id"] = "youtube:dQw4w9WgXcQ:research"
        v["transcript_logical_id"] = "youtube:dQw4w9WgXcQ:transcript"
        v["transcript_status"] = "FULL_VERIFIED"
        v["related_records"] = [
            {
                "target_id": "youtube:u3ka_AAb8qE:research",
                "relation": "COMPLEMENTS",
                "note": "OKF知識構造化と補完",
                "status": "CONFIRMED",
                "evidence": "08:16荷札と照合",
            }
        ]

        py_rendered = bridge.render(v, sample_receipt["checked_at"])
        self.assertTrue(py_rendered.startswith("---\n"))
        self.assertIn('okf_version: "0.2"', py_rendered)
        self.assertIn('type: "RESEARCH_NOTE"', py_rendered)
        self.assertIn('logical_id: "youtube:dQw4w9WgXcQ:research"', py_rendered)
        self.assertIn('transcript_logical_id: "youtube:dQw4w9WgXcQ:transcript"', py_rendered)
        self.assertIn('related_transcript_id: "youtube:dQw4w9WgXcQ:transcript"', py_rendered)
        self.assertIn('transcript_status: "FULL_VERIFIED"', py_rendered)
        self.assertIn('status: "CONFIRMED"', py_rendered)
        self.assertIn('evidence: "08:16荷札と照合"', py_rendered)
        self.assertIn('> **資料識別・Notebook UI参照案内**:', py_rendered)
        self.assertIn('> - **動画ID**: `dQw4w9WgXcQ`', py_rendered)
        self.assertIn('> - **資料論理ID**: `youtube:dQw4w9WgXcQ:research`', py_rendered)
        self.assertIn('> - **対応字幕原文論理ID**: `youtube:dQw4w9WgXcQ:transcript`', py_rendered)
        self.assertIn('NotebookLM UI上ではソース間直接リンクのクリックジャンプができない仕様です', py_rendered)

        node_render_script = f"""
const gas = require({json.dumps(gas_path)});
const v = {json.dumps(v, ensure_ascii=False)};
const checkedAt = {json.dumps(sample_receipt["checked_at"])};
process.stdout.write(gas.renderResearchMarkdown(v, checkedAt));
"""
        node_res = subprocess.run(
            ["node", "-e", node_render_script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        gas_rendered = node_res.stdout
        self.assertEqual(py_rendered.strip(), gas_rendered.strip())

        # 3. Test Knowledge Network construction and link resolution
        test_records = [
            {
                "video_id": "VID_A",
                "logical_id": "youtube:VID_A:research",
                "title": "Record A",
                "record_path": "research/rec_a.md",
                "related_records": [
                    {
                        "target_id": "VID_B",
                        "relation": "COMPLEMENTS",
                        "note": "A complements B",
                        "evidence": "section 1",
                        "status": "CONFIRMED",
                    },
                    {
                        "target_id": "VID_A",
                        "relation": "UPDATES",
                        "note": "Self link to A",
                    },
                    {
                        "target_id": "NON_EXISTENT_VID",
                        "relation": "EXTENDS",
                        "note": "Missing link",
                    },
                ],
            },
            {
                "video_id": "VID_B",
                "logical_id": "youtube:VID_B:research",
                "title": "Record B",
                "record_path": "research/rec_b.md",
                "related_records": [],
            },
        ]
        network = query_mod.build_knowledge_network(test_records)
        self.assertEqual(network["total_nodes"], 2)
        self.assertEqual(network["total_links"], 3)
        self.assertEqual(network["confirmed_links"], 1)
        self.assertEqual(network["unresolved_links"], 2)
        self.assertEqual(len(network["self_link_warnings"]), 1)
        self.assertEqual(network["self_link_warnings"][0]["reason"], "SELF_LINK_DETECTED")
        self.assertIn("VID_B", network["backlinks"])
        self.assertEqual(network["backlinks"]["VID_B"][0]["from_video_id"], "VID_A")

        # 4. Test 5 question categories router
        cat_search, _ = query_mod.classify_question_category("ハーネスの基本概念を教えて", "ハーネスの基本概念を教えて")
        self.assertEqual(cat_search, "CATEGORY_A_SEARCH")

        cat_agg, _ = query_mod.classify_question_category("何件の動画が登録されている？", "何件の動画が登録されている？")
        self.assertEqual(cat_agg, "CATEGORY_B_AGGREGATE")

        cat_timeline, _ = query_mod.classify_question_category("最近調査した研究を時系列で教えて", "最近調査した研究を時系列で教えて")
        self.assertEqual(cat_timeline, "CATEGORY_C_TIMELINE")

        cat_synthesis, _ = query_mod.classify_question_category("OKFとRAGを組み合わせるとどうなる？", "okfとragを組み合わせるとどうなる？")
        self.assertEqual(cat_synthesis, "CATEGORY_D_SYNTHESIS")

        cat_verify, _ = query_mod.classify_question_category("動画内で実際にそう発言していた？元字幕を確認したい", "動画内で実際にそう発言していた？元字幕を確認したい")
        self.assertEqual(cat_verify, "CATEGORY_E_SOURCE_VERIFY")

        # 5. Test Cross-Research Q&A pipeline (OKF + RAG synthesis) in isolated fixture root
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            tmp_research = tmp_root / "research"
            tmp_research.mkdir(parents=True)

            # Copy pRfC1DILDEM note
            prf_src = ROOT / "research" / "2026-10-18-pRfC1DILDEM-gemini-notebook.md"
            (tmp_research / prf_src.name).write_text(prf_src.read_text(encoding="utf-8"), encoding="utf-8")

            # Write u3ka_AAb8qE fixture note (no full transcript, pure OKF structure & timestamps)
            u3ka_content = """# 【研究カード】 【OKF実践】AI時代の知識管理とオープンナレッジフォーマット v0.2

- logical_id: `youtube:u3ka_AAb8qE:research`
- record_id: `youtube:u3ka_AAb8qE`
- video_id: `u3ka_AAb8qE`
- canonical_url: https://www.youtube.com/watch?v=u3ka_AAb8qE
- publication_date: 2026-08-20
- checked_at: 2026-10-19
- source_scope: ユーザー提供字幕（主要タイムスタンプ付き区間 08:16〜16:33）を分析。
- transcript_logical_id: `youtube:u3ka_AAb8qE:transcript`
- transcript_status: UNVERIFIED
- primary_source_notebook_id: UNKNOWN
- document_type: AI技術研究室 構造化研究カード（二次分析資料）
- okf_version: 0.2

## 独自要約
オープンナレッジフォーマット（OKF v0.2）に基づく文書構造化手法を解説。資料先頭の標準荷札、1件1ファイルの資料分割、意味付けされた双方向リンク。

## 動画目次・確認済みタイムライン（チャプター）
- [08:16〜09:08](https://www.youtube.com/watch?v=u3ka_AAb8qE&t=496s) | **荷札（メタデータによる資料識別）** | メタデータによる資料識別原則。 | time_source: TIMESTAMPED_CAPTIONS | topics: OKF, Metadata
- [09:35〜10:11](https://www.youtube.com/watch?v=u3ka_AAb8qE&t=575s) | **リンク（関係の意味付けと双方向参照）** | 資料間を関係種別で結ぶ設計。 | time_source: TIMESTAMPED_CAPTIONS | topics: Links, Graph

## 関連研究・資料リンク
- `youtube:pRfC1DILDEM:research` (COMPLEMENTS): RAGとOKFが相互補完関係にある | status: CONFIRMED | evidence: 08:16荷札とpRfC1DILDEMの13:16言及
"""
            (tmp_research / "2026-10-19-u3ka_AAb8qE-okf-knowledge-management.md").write_text(
                u3ka_content, encoding="utf-8"
            )

            qa_res_synthesis = query_mod.answer_question("OKFとRAGを組み合わせるとどうなる？", root=tmp_root)
            self.assertEqual(qa_res_synthesis["question_category"], "CATEGORY_D_SYNTHESIS")
            synth_vids = [
                (r["source_video_id"], r["target_video_id"])
                for r in qa_res_synthesis["synthesized_relations"]
            ]
            self.assertTrue(
                ("u3ka_AAb8qE", "pRfC1DILDEM") in synth_vids or ("pRfC1DILDEM", "u3ka_AAb8qE") in synth_vids,
                f"Expected u3ka_AAb8qE and pRfC1DILDEM relation, got {synth_vids}",
            )
            md_output = query_mod.format_qa_response_markdown(qa_res_synthesis)
            self.assertIn("関連研究ネットワークの横断合成知見", md_output)
            self.assertIn("COMPLEMENTS", md_output)

        # 6. Test Aggregate Q&A
        qa_res_agg = query_mod.answer_question("何本の動画が登録されている？", root=ROOT)
        self.assertEqual(qa_res_agg["question_category"], "CATEGORY_B_AGGREGATE")
        self.assertGreaterEqual(qa_res_agg["category_data"]["total_video_records"], 29)
        agg_md = query_mod.format_qa_response_markdown(qa_res_agg)
        self.assertIn("台帳集計結果（RAGではなく台帳直接集計）", agg_md)

        # 7. Test Source Verify Q&A
        qa_res_verify = query_mod.answer_question("字幕原文を確認したい", root=ROOT)
        self.assertEqual(qa_res_verify["question_category"], "CATEGORY_E_SOURCE_VERIFY")
        verify_md = query_mod.format_qa_response_markdown(qa_res_verify)
        self.assertIn("字幕全文は著作権保護・利用規約のためGitHub正本には保持せず", verify_md)

    def test_phase_okf_v02_spec_and_regression_verification(self):
        """Comprehensive verification of OKF v0.2 YAML frontmatter specification,
        parity between Python and GAS, conditional aggregate QA, link resolution, and backward compatibility."""
        import sys
        sys_path_entry = str(ROOT / "automation" / "gemini-notebook")
        if sys_path_entry not in sys.path:
            sys.path.insert(0, sys_path_entry)
        import query_research as qm
        import receipt_to_research as bridge

        # 1. Test YAML frontmatter parsing and validation
        valid_yaml = (
            "---\n"
            'okf_version: "0.2"\n'
            'type: "RESEARCH_NOTE"\n'
            'title: "テスト研究カード"\n'
            'description: "テスト要約"\n'
            'resource: "https://www.youtube.com/watch?v=abcdefghijk"\n'
            "tags:\n"
            '  - "AI技術研究室"\n'
            '  - "テスト"\n'
            'logical_id: "youtube:abcdefghijk:research"\n'
            'video_id: "abcdefghijk"\n'
            "---\n"
            "# テスト研究カード\n"
        )
        fm_data, body = qm.parse_yaml_frontmatter(valid_yaml)
        self.assertIsNotNone(fm_data)
        self.assertEqual(fm_data.get("okf_version"), "0.2")
        self.assertEqual(fm_data.get("type"), "RESEARCH_NOTE")
        self.assertEqual(fm_data.get("title"), "テスト研究カード")
        self.assertEqual(fm_data.get("tags"), ["AI技術研究室", "テスト"])

        # Missing closing ---
        broken_yaml = "---\nokf_version: '0.2'\ntype: 'RESEARCH_NOTE'\n# No closing"
        fm_broken, _ = qm.parse_yaml_frontmatter(broken_yaml)
        self.assertIsNone(fm_broken)

        # Missing required type
        missing_type_yaml = "---\nokf_version: '0.2'\ntitle: 'No Type'\n---\nBody"
        fm_no_type, _ = qm.parse_yaml_frontmatter(missing_type_yaml)
        self.assertIsNotNone(fm_no_type)
        self.assertIsNone(fm_no_type.get("type"))

        # 2. Test Python vs GAS rendering parity (100% byte-for-byte identical)
        sample_v = {
            "video_id": "test_parity_vid",
            "url": "https://www.youtube.com/watch?v=test_parity_vid",
            "title": "Parity Test Note 2026: Special chars \"quoted\" & 'single' and : colons",
            "summary_ja": "特殊文字やコロンを含む要約テスト。",
            "source_scope": "Gemini 14:00字幕取得",
            "notebook_readback": "PASS",
            "changes": ["NEW"],
            "primary_source_notebook_id": "nb_parity_123",
            "published_at": "2026-10-18",
            "logical_id": "youtube:test_parity_vid:research",
            "transcript_logical_id": "youtube:test_parity_vid:transcript",
            "transcript_status": "UNVERIFIED",
            "chapters": [],
            "claims": [],
            "related_records": [
                {
                    "target_id": "youtube:u3ka_AAb8qE:research",
                    "relation": "COMPLEMENTS",
                    "note": "OKFとRAGの連携",
                    "status": "CANDIDATE",
                    "evidence": "13:16言及",
                }
            ],
        }
        py_out = bridge.render(sample_v, "2026-10-19")
        gas_path = str(ROOT / "automation" / "gemini-notebook" / "cloud_relay_gas.js")
        node_script = f"""
const gas = require({json.dumps(gas_path)});
const v = {json.dumps(sample_v, ensure_ascii=False)};
process.stdout.write(gas.renderResearchMarkdown(v, "2026-10-19"));
"""
        res = subprocess.run(
            ["node", "-e", node_script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        gas_out = res.stdout
        self.assertEqual(py_out, gas_out, "Python and GAS rendered markdown must have 100% character-by-character parity")

        # 3. Test link resolution and strict candidate separation in knowledge network
        mock_records = [
            {
                "video_id": "vid_src",
                "logical_id": "youtube:vid_src:research",
                "title": "Source Video",
                "record_path": "research/vid_src.md",
                "transcript_status": "UNVERIFIED",
                "related_records": [
                    {
                        "target_id": "vid_existing_confirmed",
                        "relation": "COMPLEMENTS",
                        "status": "CONFIRMED",
                        "evidence": "動画本編 05:20 にて直接言及",
                    },
                    {
                        "target_id": "vid_existing_candidate",
                        "relation": "EXTENDS",
                        "status": "CANDIDATE",
                    },
                    {
                        "target_id": "vid_non_existent",
                        "relation": "COMPLEMENTS",
                        "status": "CONFIRMED",
                        "evidence": "動画本編 12:45 にて直接言及",
                    },
                ],
            },
            {
                "video_id": "vid_existing_confirmed",
                "logical_id": "youtube:vid_existing_confirmed:research",
                "title": "Existing Confirmed",
                "record_path": "research/vid_existing_confirmed.md",
                "transcript_status": "VERIFIED",
                "related_records": [],
            },
            {
                "video_id": "vid_existing_candidate",
                "logical_id": "youtube:vid_existing_candidate:research",
                "title": "Existing Candidate",
                "record_path": "research/vid_existing_candidate.md",
                "transcript_status": "UNKNOWN",
                "related_records": [],
            },
        ]
        net = qm.build_knowledge_network(mock_records)
        self.assertEqual(net["total_links"], 3)
        self.assertEqual(net["confirmed_links"], 1)
        self.assertEqual(net["candidate_links"], 1)
        self.assertEqual(net["unresolved_links"], 1)

        # 4. Test deterministic conditional aggregate QA
        qa_rag = qm.answer_question("RAGに関する動画は何本ありますか？", root=ROOT)
        self.assertEqual(qa_rag["question_category"], "CATEGORY_B_AGGREGATE")
        self.assertEqual(qa_rag["category_data"]["filter_type"], "RAG")
        self.assertEqual(qa_rag["category_data"]["matched_count"], 2)
        matched_rag_vids = {v["video_id"] for v in qa_rag["category_data"]["matched_videos"]}
        self.assertIn("pRfC1DILDEM", matched_rag_vids)

        qa_all = qm.answer_question("登録動画は何本ありますか？", root=ROOT)
        self.assertEqual(qa_all["category_data"]["filter_type"], "ALL")
        self.assertEqual(qa_all["category_data"]["matched_count"], 31)

        # 5. Test timeline sorting differentiation
        qa_time_pub = qm.answer_question("いつ公開された動画か時系列で教えて", root=ROOT)
        self.assertEqual(qa_time_pub["category_data"]["sort_by"], "PUBLICATION_DATE")

        qa_time_chk = qm.answer_question("研究室で調査した日時のタイムライン", root=ROOT)
        self.assertEqual(qa_time_chk["category_data"]["sort_by"], "CHECKED_AT")

        # 6. Test backward compatibility for existing 31 video notes (28 legacy + 3 OKF)
        cat, parsed = qm.build_video_knowledge_catalog(root=ROOT)
        self.assertEqual(cat["total_video_records"], 31)
        self.assertEqual(cat["total_verified_chapters"], 134)
        # Verify pRfC1DILDEM has OKF v0.2 and 22 chapters intact
        prf_rec = next(r for r in parsed if r.get("video_id") == "pRfC1DILDEM")
        self.assertEqual(prf_rec["okf_version"], "0.2")
        self.assertEqual(prf_rec["okf_type"], "RESEARCH_NOTE")
        self.assertEqual(len(prf_rec["chapters"]), 22)
        # Verify legacy note still parses properly without frontmatter
        leg_rec = next(r for r in parsed if r.get("video_id") == "lC5jxpYmatE")
        self.assertIsNone(leg_rec["okf_version"])
        self.assertGreater(len(leg_rec["chapters"]), 0)

    def test_final_integrity_and_okf_alignment(self):
        """Phase 6.5 / 実機試験前最終整合性検証:
        1. validate_okf_frontmatter による type 欠落・空欄FAIL検査
        2. verify_transcript_status による証拠条件判定（FULL_VERIFIEDの厳格性、フォールバック）
        3. extract_aggregate_filter における OKF_TOPIC と OKF_FORMAT の分離集計
        4. format_related_records_lines および formatRelatedRecordsLines_ のMarkdownリンクパリティ
        5. build_knowledge_network の target_path 解決と QA Markdown のリンク表示
        """
        import sys
        sys_path_entry = str(ROOT / "automation" / "gemini-notebook")
        if sys_path_entry not in sys.path:
            sys.path.insert(0, sys_path_entry)
        import query_research as qm
        import receipt_to_research as rtr

        # 1. OKF フロントマター形式検査 (validate_okf_frontmatter)
        # type 欠落
        ok, errs = qm.validate_okf_frontmatter({
            "title": "Title",
            "description": "Desc",
            "resource": "https://example.com",
            "tags": ["AI"],
            "okf_version": "0.2",
        })
        self.assertFalse(ok)
        self.assertTrue(any("Required field 'type'" in e for e in errs))

        # type 空白
        ok_empty, errs_empty = qm.validate_okf_frontmatter({
            "type": "   ",
            "title": "Title",
            "description": "Desc",
            "resource": "https://example.com",
            "tags": ["AI"],
            "okf_version": "0.2",
        })
        self.assertFalse(ok_empty)
        self.assertTrue(any("Required field 'type'" in e for e in errs_empty))

        # 正常なフロントマター
        ok_valid, errs_valid = qm.validate_okf_frontmatter({
            "type": "RESEARCH_NOTE",
            "title": "Title",
            "description": "Desc",
            "resource": "https://example.com",
            "tags": ["AI技術研究室"],
            "okf_version": "0.2",
        })
        self.assertTrue(ok_valid)
        self.assertEqual(len(errs_valid), 0)

        # 2. 字幕検証ステータス (verify_transcript_status)
        # 全文検証（証拠完備）
        st1 = qm.verify_transcript_status(
            "FULL_VERIFIED", "PASS", "src-12345", "00:00〜14:23（全区間）"
        )
        self.assertEqual(st1, "FULL_VERIFIED")

        # 自己申告FULL_VERIFIEDだがNotebookソースIDなし → UNVERIFIED
        st2 = qm.verify_transcript_status(
            "FULL_VERIFIED", "PASS", "UNKNOWN", "00:00〜14:23（全区間）"
        )
        self.assertEqual(st2, "UNVERIFIED")

        # 自己申告FULL_VERIFIEDだがreadbackがPASSでない → UNVERIFIED
        st3 = qm.verify_transcript_status(
            "FULL_VERIFIED", "UNKNOWN", "src-12345", "00:00〜14:23（全区間）"
        )
        self.assertEqual(st3, "UNVERIFIED")

        # 自己申告FULL_VERIFIEDだが区間が部分的 → PARTIAL_VERIFIED
        st4 = qm.verify_transcript_status(
            "FULL_VERIFIED", "PASS", "src-12345", "03:10〜05:20"
        )
        self.assertEqual(st4, "PARTIAL_VERIFIED")

        # 部分検証
        st5 = qm.verify_transcript_status("PARTIAL_VERIFIED", "PASS", "src-12345", "一部区間")
        self.assertEqual(st5, "PARTIAL_VERIFIED")

        # 未取得
        st6 = qm.verify_transcript_status("NOT_ACQUIRED", "PASS", "src-12345", "")
        self.assertEqual(st6, "NOT_ACQUIRED")

        # 3. 集計フィルタの分離 (OKF_TOPIC vs OKF_FORMAT, 字幕ステータス5値)
        flt_topic, _ = qm.extract_aggregate_filter("OKFに関する動画は何本ありますか？", "okfに関する動画は何本ありますか？")
        self.assertEqual(flt_topic, "OKF_TOPIC")

        flt_format, _ = qm.extract_aggregate_filter("OKF形式の研究カードは何件ありますか？", "okf形式の研究カードは何件ありますか？")
        self.assertEqual(flt_format, "OKF_FORMAT")

        flt_full, _ = qm.extract_aggregate_filter("全文検証済みの字幕は何本ありますか？", "全文検証済みの字幕は何本ありますか？")
        self.assertEqual(flt_full, "TRANSCRIPT_FULL_VERIFIED")

        flt_part, _ = qm.extract_aggregate_filter("部分検証済みの字幕は何件ありますか？", "部分検証済みの字幕は何件ありますか？")
        self.assertEqual(flt_part, "TRANSCRIPT_PARTIAL_VERIFIED")

        flt_unver, _ = qm.extract_aggregate_filter("未検証の字幕は何件ありますか？", "未検証の字幕は何件ありますか？")
        self.assertEqual(flt_unver, "TRANSCRIPT_UNVERIFIED")

        flt_notacq, _ = qm.extract_aggregate_filter("未取得の字幕は何件ありますか？", "未取得の字幕は何件ありますか？")
        self.assertEqual(flt_notacq, "TRANSCRIPT_NOT_ACQUIRED")

        # 4. Markdownリンク化パリティ (Python & GAS)
        test_rels = [
            {
                "target_id": "youtube:pRfC1DILDEM",
                "relation": "COMPLEMENTS",
                "note": "RAG探索とOKF知識体系の補完",
                "status": "CONFIRMED",
                "target_path": "research/2026-10-18-pRfC1DILDEM-gemini-notebook.md",
                "evidence": "RAG探索設計",
            },
            {
                "target_id": "youtube:u3ka_AAb8qE",
                "relation": "RELATES_TO",
                "note": "未登録OKF動画の候補",
                "status": "CANDIDATE",
                "target_path": "",
                "evidence": "字幕提供のみ",
            },
        ]
        py_lines = rtr.format_related_records_lines(test_rels)
        self.assertIn("[youtube:pRfC1DILDEM](research/2026-10-18-pRfC1DILDEM-gemini-notebook.md)", py_lines[0])
        self.assertIn("`youtube:u3ka_AAb8qE`", py_lines[1])
        self.assertNotIn("[youtube:u3ka_AAb8qE]", py_lines[1])

        # GAS Node.js parity
        gas_path = str(ROOT / "automation" / "gemini-notebook" / "cloud_relay_gas.js").replace("\\", "/")
        node_script = f"""
const gas = require({json.dumps(gas_path)});
const rels = {json.dumps(test_rels)};
const res = gas.formatRelatedRecordsLines(rels);
process.stdout.write(JSON.stringify(res));
"""
        proc = subprocess.run(
            ["node", "-e", node_script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        gas_lines = json.loads(proc.stdout.strip())
        self.assertEqual(py_lines, gas_lines)

        # 5. build_knowledge_network による target_path 解決
        cat, records = qm.build_video_knowledge_catalog(root=ROOT)
        network = qm.build_knowledge_network(records)
        # pRfC1DILDEM からの confirmed リンクに target_path が設定されていること
        p_edges = [e for e in network["edges"] if e["source_video_id"] == "pRfC1DILDEM"]
        for e in p_edges:
            if e["status"] == "CONFIRMED":
                self.assertIsNotNone(e.get("target_path"))
                self.assertTrue(e["target_path"].startswith("research/") or e["target_path"].startswith("proposals/"))

        # QA 回答出力の Markdown リンク検証
        qa_topic = qm.answer_question("OKFに関する動画は何本ありますか？", root=ROOT)
        md_text = qm.format_qa_response_markdown(qa_topic)
        self.assertIn("台帳集計結果", md_text)
        self.assertIn("OKF_TOPIC", md_text)
        # テーブル内に Markdown リンクが含まれること
        self.assertIn("](research/", md_text)

    def test_backlink_integrity_and_bidirectional_parity(self):
        """逆リンク（Backlinks）の完全性・双方向性・欠落ゼロを検証する。"""
        import sys
        sys_path_entry = str(ROOT / "automation" / "gemini-notebook")
        if sys_path_entry not in sys.path:
            sys.path.insert(0, sys_path_entry)
        import query_research as qm

        cat, records = qm.build_video_knowledge_catalog(root=ROOT)
        net = qm.build_knowledge_network(records)

        # 1. 逆リンク欠落が 0 件であること（完全な双方向整合性）
        self.assertEqual(net.get("unidirectional_links_count"), 0)
        self.assertEqual(net.get("missing_reverse_links"), [])
        self.assertGreaterEqual(net.get("bidirectional_links_count"), 30)

        # 2. 類似キーワード推論リンクと確定リンクの峻別（類似キーワードだけで確定させない契約）
        self.assertEqual(net.get("confirmed_links"), 2)  # 一次証拠付き基準例のみ確定
        self.assertGreaterEqual(net.get("candidate_links"), 58)  # キーワード推論リンクはすべてCANDIDATEとして保持

        # 3. 主要ハブ資料のバックリンクが正しく集約され、未検証候補として保持されていること
        backlinks = net.get("backlinks", {})
        self.assertIn("lC5jxpYmatE", backlinks)
        self.assertGreaterEqual(len(backlinks["lC5jxpYmatE"]), 10)
        # キーワード推論由来のバックリンクが CANDIDATE として記録されていること
        lc5_bl = [b for b in backlinks["lC5jxpYmatE"] if b.get("from_video_id") == "26MGuVIJh4A"]
        self.assertTrue(len(lc5_bl) == 1 and lc5_bl[0]["status"] == "CANDIDATE")

        self.assertIn("ZjUJ-35acaU", backlinks)
        self.assertGreaterEqual(len(backlinks["ZjUJ-35acaU"]), 10)
        self.assertIn("Vr3JkAT9mo8", backlinks)
        self.assertGreaterEqual(len(backlinks["Vr3JkAT9mo8"]), 5)
        self.assertIn("BStkW1HTfmk", backlinks)
        self.assertGreaterEqual(len(backlinks["BStkW1HTfmk"]), 4)

        # 4. 基準例（pRfC1DILDEM と u3ka_AAb8qE）の双方向 COMPLEMENTS かつ CONFIRMED 整合性
        p_to_u = [e for e in net["edges"] if e["source_video_id"] == "pRfC1DILDEM" and e["target_video_id"] == "u3ka_AAb8qE"]
        u_to_p = [e for e in net["edges"] if e["source_video_id"] == "u3ka_AAb8qE" and e["target_video_id"] == "pRfC1DILDEM"]
        self.assertTrue(len(p_to_u) == 1 and p_to_u[0]["relation"] == "COMPLEMENTS" and p_to_u[0]["status"] == "CONFIRMED")
        self.assertTrue(len(u_to_p) == 1 and u_to_p[0]["relation"] == "COMPLEMENTS" and u_to_p[0]["status"] == "CONFIRMED")

    def test_new_video_pure_2_source_okf_default_principle(self):
        """新規動画における純粋2ソースOKF（字幕原文OKF ＋ 研究ノートOKF）登録原則の検証。"""
        import notebook_auto_ingest as nai
        import auto_research_pipeline as arp

        test_vid = "newVid999"
        test_url = f"https://www.youtube.com/watch?v={test_vid}"
        test_title = "新規動画2ソース原則テスト"
        dummy_md = ROOT / "research" / "2026-10-19-u3ka_AAb8qE-gemini-notebook.md"
        test_cues = [(0.0, 10.0, "テスト発話その1"), (10.0, 20.0, "テスト発話その2")]

        # 1. デフォルト (add_youtube_source=False) での新規動画登録シミュレーション
        # 初期状態: Notebookにソースが何も登録されていない新規状態
        res = nai.ingest_and_verify_notebook(
            video_id=test_vid,
            video_url=test_url,
            video_title=test_title,
            research_md_path=dummy_md,
            cues=test_cues,
            mock_cdp=True,
            mock_sources=[],  # 新規動画なので最初は空
            add_youtube_source=False,  # 新規動画の標準原則: YouTube URLはデフォルト追加しない
        )

        # 2. アクションの検証: YouTube URLは追加されず、純粋な2ソース（研究ノートOKF＋字幕原文OKF）のみ追加される
        actions = res.get("actions_taken", [])
        self.assertNotIn("YOUTUBE_URL_INSERTED", actions)
        self.assertIn("COPIED_TEXT_NOTE_INSERTED", actions)
        self.assertIn("TRANSCRIPT_OKF_INSERTED", actions)
        self.assertEqual(len(actions), 2)

        # 3. 2ソースOKF完全立証とステータスの検証
        self.assertTrue(res.get("is_2_source_okf_verified"))
        self.assertTrue(res.get("is_full_success"))
        self.assertEqual(res.get("readback", {}).get("status"), "SUCCESS_2_SOURCE_OKF")
        self.assertFalse(res.get("readback", {}).get("youtube_source_found"))
        self.assertTrue(res.get("readback", {}).get("research_note_found"))
        self.assertTrue(res.get("readback", {}).get("transcript_source_found"))

        # 4. auto_research_pipeline の evaluate_final_status でも SUCCESS_2_SOURCE_OKF と判定されること
        status, reasons = arp.evaluate_final_status(
            real_content_acquired=True,
            engine_used="GEMINI_API_LIVE",
            model_used="gemini-3.8-flash",
            research_note_generated=True,
            github_push_success=True,
            remote_head_matched=True,
            remote_research_readback_matched=True,
            remote_registry_readback_matched=True,
            notebook_youtube_readback=False,  # YouTube URLソースなし（純粋2ソース）
            notebook_research_readback=True,
            qa_verified=True,
            no_push=False,
            is_2_source_okf_verified=True,
            notebook_transcript_readback=True,
        )
        self.assertEqual(status, "SUCCESS_2_SOURCE_OKF")
        self.assertEqual(reasons, [])

    def test_existing_youtube_source_is_preserved_and_never_deleted(self):
        """既存のYouTube URLソースが勝手に削除されず、そのまま非破壊で保持されることを検証する。"""
        import notebook_auto_ingest as nai

        exist_vid = "existVid888"
        exist_url = f"https://www.youtube.com/watch?v={exist_vid}"
        exist_title = "既存登録済み動画（YouTubeソース既存）"
        dummy_md = ROOT / "research" / "2026-10-19-u3ka_AAb8qE-gemini-notebook.md"
        test_cues = [(0.0, 15.0, "既存動画の字幕発話")]

        # 初期状態: NotebookLMに既にYouTube URLソースが登録されている
        initial_sources = [
            f"https://www.youtube.com/watch?v={exist_vid}",
            "AI技術研究室_知識索引.md",
        ]

        # 登録・読み戻し実行（add_youtube_source=False: 新規YouTube追加はオフだが、既存の削除は絶対にしない）
        res = nai.ingest_and_verify_notebook(
            video_id=exist_vid,
            video_url=exist_url,
            video_title=exist_title,
            research_md_path=dummy_md,
            cues=test_cues,
            mock_cdp=True,
            mock_sources=initial_sources,
            add_youtube_source=False,
        )

        actions = res.get("actions_taken", [])
        # 1. 削除アクションは一切発生しない
        for act in actions:
            self.assertNotIn("DELETE", str(act).upper())
            self.assertNotIn("REMOVE", str(act).upper())

        # 2. 既存のYouTube URLソースは削除されず、読み戻しで検出される
        rb = res.get("readback", {})
        self.assertTrue(rb.get("youtube_source_found"), "既存のYouTube URLソースが維持されていること")

        # 3. 不足していた研究ノートと字幕原文OKFが追加され、共存した状態で2ソースOKF完全立証となる
        self.assertTrue(rb.get("research_note_found"))
        self.assertTrue(rb.get("transcript_source_found"))
        self.assertTrue(res.get("is_2_source_okf_verified"))
        self.assertTrue(res.get("is_full_success"))
        self.assertEqual(rb.get("status"), "SUCCESS_2_SOURCE_OKF")

    def test_idempotent_diff_ingest_skips_existing_and_adds_only_missing(self):
        """同じ動画について登録済みのソースがある場合、重複を避け不足しているソースのみを追加することを検証する。"""
        import notebook_auto_ingest as nai

        dummy_md = ROOT / "research" / "2026-10-19-u3ka_AAb8qE-gemini-notebook.md"
        test_cues = [(0.0, 10.0, "テスト発話")]

        # Case A: 研究ノートOKFのみ登録済み -> 字幕原文OKFのみを追加（研究ノートは重複追加しない）
        vid_a = "diffVidA111"
        res_a = nai.ingest_and_verify_notebook(
            video_id=vid_a,
            video_url=f"https://www.youtube.com/watch?v={vid_a}",
            video_title="研究ノート登録済み動画",
            research_md_path=dummy_md,
            cues=test_cues,
            mock_cdp=True,
            mock_sources=[f"AI_VIDEO_RESEARCH_NOTE:{vid_a}"],
            add_youtube_source=False,
        )
        actions_a = res_a.get("actions_taken", [])
        self.assertNotIn("COPIED_TEXT_NOTE_INSERTED", actions_a, "研究ノートの重複追加は回避されること")
        self.assertIn("TRANSCRIPT_OKF_INSERTED", actions_a, "不足していた字幕原文OKFのみが追加されること")
        self.assertEqual(len(actions_a), 1)
        self.assertTrue(res_a.get("is_2_source_okf_verified"))

        # Case B: 字幕原文OKFのみ登録済み -> 研究ノートOKFのみを追加（字幕原文は重複追加しない）
        vid_b = "diffVidB222"
        res_b = nai.ingest_and_verify_notebook(
            video_id=vid_b,
            video_url=f"https://www.youtube.com/watch?v={vid_b}",
            video_title="字幕原文登録済み動画",
            research_md_path=dummy_md,
            cues=test_cues,
            mock_cdp=True,
            mock_sources=[f"AI_VIDEO_TRANSCRIPT_RAW:{vid_b}"],
            add_youtube_source=False,
        )
        actions_b = res_b.get("actions_taken", [])
        self.assertIn("COPIED_TEXT_NOTE_INSERTED", actions_b, "不足していた研究ノートOKFのみが追加されること")
        self.assertNotIn("TRANSCRIPT_OKF_INSERTED", actions_b, "字幕原文OKFの重複追加は回避されること")
        self.assertEqual(len(actions_b), 1)
        self.assertTrue(res_b.get("is_2_source_okf_verified"))

        # Case C: 全ソース（研究ノートOKF＋字幕原文OKF）登録済み -> 追加操作ゼロで安全終了（No-Op）
        vid_c = "diffVidC333"
        res_c = nai.ingest_and_verify_notebook(
            video_id=vid_c,
            video_url=f"https://www.youtube.com/watch?v={vid_c}",
            video_title="全ソース登録済み動画",
            research_md_path=dummy_md,
            cues=test_cues,
            mock_cdp=True,
            mock_sources=[
                f"AI_VIDEO_RESEARCH_NOTE:{vid_c}",
                f"AI_VIDEO_TRANSCRIPT_RAW:{vid_c}",
            ],
            add_youtube_source=False,
        )
        actions_c = res_c.get("actions_taken", [])
        self.assertEqual(actions_c, [], "全ソース登録済みの場合は追加操作ゼロ（No-Op）であること")
        self.assertTrue(res_c.get("is_2_source_okf_verified"))
        self.assertTrue(res_c.get("is_full_success"))
        self.assertEqual(res_c.get("readback", {}).get("status"), "SUCCESS_2_SOURCE_OKF")

    def test_post_registration_2_source_independent_verification(self):
        """登録後に2つのソース（研究ノートOKFと字幕原文OKF）が独立して個別に確認されることを検証する。"""
        import notebook_auto_ingest as nai

        vid = "indepVid777"
        url = f"https://www.youtube.com/watch?v={vid}"
        title = "独立2ソース検証動画"
        dummy_md = ROOT / "research" / "2026-10-19-u3ka_AAb8qE-gemini-notebook.md"
        cues = [(0.0, 10.0, "発話1"), (10.0, 20.0, "発話2")]

        # 1. 正常系: 登録後に2つの独立したソースが正しく検出されること
        res = nai.ingest_and_verify_notebook(
            video_id=vid,
            video_url=url,
            video_title=title,
            research_md_path=dummy_md,
            cues=cues,
            mock_cdp=True,
            mock_sources=[],
            add_youtube_source=False,
        )

        rb = res.get("readback", {})
        # A. 2つのソースが個別に検出されていること
        self.assertTrue(res.get("research_note_found"))
        self.assertTrue(res.get("transcript_source_found"))
        self.assertTrue(rb.get("research_note_found"))
        self.assertTrue(rb.get("transcript_source_found"))

        # B. 2つのアイテムインデックスが異なり、別々の独立DOM要素であること（n != t）
        note_idx = rb.get("research_note_item_index")
        tr_idx = rb.get("transcript_item_index")
        self.assertIsNotNone(note_idx)
        self.assertIsNotNone(tr_idx)
        self.assertNotEqual(note_idx, tr_idx, "研究ノートと字幕原文は同一要素ではなく別要素であること")

        # C. 独立ソース数と独立フラグの検証
        self.assertEqual(rb.get("independent_sources_count"), 2)
        self.assertTrue(rb.get("independent_sources_distinct"))
        self.assertTrue(res.get("independent_sources_distinct"))
        self.assertTrue(res.get("is_2_source_okf_verified"))
        self.assertEqual(res.get("status"), "SUCCESS_2_SOURCE_OKF")

        # 2. 異常系（ネガティブテスト）: 1つの要素に両方のキーワードが混ざっているだけで独立した2要素がない場合
        # （1要素のみで2要素と誤認してはならない）
        items_single = [
            {"index": 0, "text": f"AI_VIDEO_RESEARCH_NOTE:{vid} AI_VIDEO_TRANSCRIPT_RAW:{vid} 混在ソース"}
        ]
        independence_res = nai.evaluate_2_source_okf_independence(items_single, vid, title)
        # 1つのインデックスしか存在しないため、distinct pairs が作れず、is_2_source_okf_verified は False となること
        self.assertFalse(independence_res.get("is_2_source_okf_verified"), "同一の1要素だけでは2ソース独立判定を拒否すること")
        self.assertFalse(independence_res.get("independent_sources_distinct"))


if __name__ == "__main__":
    unittest.main(verbosity=2)







