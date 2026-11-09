"""Reproducible tests for the first stale-handoff case."""

import subprocess
import tempfile
import unittest
from pathlib import Path

from phoenix_continuity_gate import evaluate


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


class GateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.name", "Gate Test")
        git(self.repo, "config", "user.email", "gate-test@example.invalid")
        (self.repo / "work.txt").write_text("first version\n", encoding="utf-8")
        git(self.repo, "add", "work.txt")
        git(self.repo, "commit", "-qm", "first")
        self.first_head = git(self.repo, "rev-parse", "HEAD")
        self.handoff = {
            "schema_version": 1,
            "repo_head": self.first_head,
            "tests": {"status": "passed", "git_head": self.first_head},
        }

    def test_matching_clean_commit_passes_limited_consistency_check(self) -> None:
        verdict, findings = evaluate(self.handoff, self.repo)
        self.assertEqual(verdict, "PASS")
        self.assertIn("not independently verified", findings[0])

    def test_new_commit_blocks_stale_handoff(self) -> None:
        (self.repo / "work.txt").write_text("changed after tests\n", encoding="utf-8")
        git(self.repo, "add", "work.txt")
        git(self.repo, "commit", "-qm", "change after handoff")
        verdict, findings = evaluate(self.handoff, self.repo)
        self.assertEqual(verdict, "BLOCK")
        self.assertTrue(any("differs from current HEAD" in item for item in findings))

    def test_uncommitted_change_requires_review(self) -> None:
        (self.repo / "work.txt").write_text("uncommitted change\n", encoding="utf-8")
        verdict, _ = evaluate(self.handoff, self.repo)
        self.assertEqual(verdict, "REVIEW")

    def test_failed_tests_block(self) -> None:
        self.handoff["tests"]["status"] = "failed"
        verdict, _ = evaluate(self.handoff, self.repo)
        self.assertEqual(verdict, "BLOCK")


if __name__ == "__main__":
    unittest.main()
