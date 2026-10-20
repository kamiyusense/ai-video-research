"""Tests must not depend on which branch the real checkout is on (main, a work branch, detached HEAD in CI...).

The pipeline's safety check (`verify_target_branch_early`) refuses to run unless the current branch is the one allowed
work branch. These helpers give the check a branch name through a patched `git branch --show-current` or through a
throw-away git repository, so the real repository's branch is never read and the check itself stays as strict as before.
"""
import os
import subprocess
import tempfile
from pathlib import Path
from unittest import mock

_REAL_CHECK_OUTPUT = subprocess.check_output


def _is_show_current(cmd):
    return list(cmd)[:3] == ["git", "branch", "--show-current"]


def pin_branch_name(testcase, branch):
    """For the length of one test, make `git branch --show-current` answer `branch`. Every other command runs for real."""

    def check_output(cmd, *args, **kwargs):
        if _is_show_current(cmd):
            return branch + "\n"
        return _REAL_CHECK_OUTPUT(cmd, *args, **kwargs)

    patcher = mock.patch.object(subprocess, "check_output", check_output)
    patcher.start()
    testcase.addCleanup(patcher.stop)


def pin_target_branch(testcase, arp):
    """Make the pipeline see the one allowed work branch (arp.DEFAULT_TARGET_BRANCH) without checking out anything."""
    pin_branch_name(testcase, arp.DEFAULT_TARGET_BRANCH)


def temp_repo_on_branch(testcase, branch):
    """A throw-away git repository whose current branch is `branch` (no commits needed). Returns its path."""
    tmp = tempfile.TemporaryDirectory()
    testcase.addCleanup(tmp.cleanup)
    root = Path(tmp.name)
    subprocess.run(["git", "init", "-q", "-b", branch], cwd=root, check=True)
    return root


def temp_repo_detached(testcase):
    """A throw-away git repository with a detached HEAD (`git branch --show-current` prints nothing)."""
    root = temp_repo_on_branch(testcase, "scratch")
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@example.invalid", "PATH": os.environ.get("PATH", "")}
    subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "x"], cwd=root, check=True, env=env)
    subprocess.run(["git", "checkout", "-q", "--detach"], cwd=root, check=True)
    return root
