"""A disposable, reproducible demonstration of stale handoff evidence."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from .gate import evaluate


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def run_demo() -> dict[str, object]:
    """Run both sides of the same handoff in a temporary Git repository."""
    with tempfile.TemporaryDirectory(prefix="phoenix-gate-demo-") as directory:
        repo = Path(directory)
        _git(repo, "init", "-q")
        _git(repo, "config", "user.name", "Phoenix Gate Demo")
        _git(repo, "config", "user.email", "phoenix-gate@example.invalid")

        work = repo / "work.txt"
        work.write_text("Version A: tests were reported as passed.\n", encoding="utf-8")
        _git(repo, "add", "work.txt")
        _git(repo, "commit", "-qm", "snapshot A")
        first_head = _git(repo, "rev-parse", "HEAD")

        handoff = {
            "schema_version": 1,
            "repo_head": first_head,
            "tests": {"status": "passed", "git_head": first_head},
        }
        before_verdict, before_findings = evaluate(handoff, repo)

        work.write_text("Version B: code changed after the test claim.\n", encoding="utf-8")
        _git(repo, "add", "work.txt")
        _git(repo, "commit", "-qm", "snapshot B")
        second_head = _git(repo, "rev-parse", "HEAD")
        after_verdict, after_findings = evaluate(handoff, repo)

        return {
            "first_head": first_head,
            "second_head": second_head,
            "before_verdict": before_verdict,
            "before_findings": before_findings,
            "after_verdict": after_verdict,
            "after_findings": after_findings,
        }
