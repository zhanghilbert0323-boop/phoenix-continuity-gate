"""Minimal evidence checks for a coding-agent handoff."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or "Git command failed")
    return result.stdout.strip()


def evaluate(handoff: dict[str, Any], repo: Path) -> tuple[str, list[str]]:
    """Return a limited verdict and human-readable reasons; never modify repo."""
    if handoff.get("schema_version") != 1:
        raise ValueError("handoff.schema_version must be 1")

    recorded_head = handoff.get("repo_head")
    if not isinstance(recorded_head, str) or not recorded_head:
        raise ValueError("handoff.repo_head must be a non-empty Git commit hash")

    current_head = _git(repo, "rev-parse", "HEAD")
    status = _git(repo, "status", "--porcelain")
    findings: list[tuple[str, str]] = []

    if recorded_head != current_head:
        findings.append(
            ("BLOCK", f"Handoff commit {recorded_head} differs from current HEAD {current_head}.")
        )

    tests = handoff.get("tests")
    if not isinstance(tests, dict):
        findings.append(("REVIEW", "No test claim was supplied; test status is unknown."))
    elif tests.get("status") == "failed":
        findings.append(("BLOCK", "Handoff records failed tests."))
    elif tests.get("status") == "passed":
        test_head = tests.get("git_head")
        if not isinstance(test_head, str) or not test_head:
            findings.append(("REVIEW", "Passed-test claim has no associated commit hash."))
        elif test_head != current_head:
            findings.append(
                ("BLOCK", f"Passed-test claim applies to {test_head}, not current HEAD {current_head}.")
            )
    else:
        findings.append(("REVIEW", "Tests are not recorded as passed; test status is unknown."))

    if status:
        findings.append(("REVIEW", "Working tree has uncommitted or untracked files; recorded tests may not cover them."))

    if any(level == "BLOCK" for level, _ in findings):
        verdict = "BLOCK"
    elif findings:
        verdict = "REVIEW"
    else:
        verdict = "PASS"
        findings.append(
            ("PASS", "Recorded hashes match a clean HEAD; the test claim itself was not independently verified.")
        )

    return verdict, [message for _, message in findings]
