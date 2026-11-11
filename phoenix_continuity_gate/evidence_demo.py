"""A disposable end-to-end example with real unittest execution."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from .evidence import assess_record, record_command


def run_evidence_demo() -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="phoenix-record-demo-") as directory:
        base = Path(directory)
        repo = base / "sample project"
        repo.mkdir()

        def git(*args: str) -> None:
            subprocess.run(["git", "-C", str(repo), *args], check=True,
                           capture_output=True, text=True, timeout=30)

        git("init", "-q")
        git("config", "user.name", "Phoenix Execution Demo")
        git("config", "user.email", "demo@example.invalid")
        git("config", "commit.gpgSign", "false")
        git("config", "core.hooksPath", str(base / "no-hooks"))
        source = repo / "arithmetic.py"
        source.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
        (repo / "test_arithmetic.py").write_text(
            "import unittest\nfrom arithmetic import add\nclass Tests(unittest.TestCase):\n"
            "    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n", encoding="utf-8")
        git("add", ".")
        git("commit", "-qm", "working arithmetic")
        command = [sys.executable, "-E", "-s", "-B", "-m", "unittest", "-v"]
        first = record_command(repo, base / "first.json", command)
        steps = [{"name": "Run a real test on working code", "record": first,
                  "assessment": assess_record(first, repo)}]

        source.write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
        git("add", "arithmetic.py")
        git("commit", "-qm", "deliberately break addition")
        steps.append({"name": "Code changed; inspect the OLD record without running tests",
                      "record": first, "assessment": assess_record(first, repo)})
        failed = record_command(repo, base / "failed.json", command)
        steps.append({"name": "Run the test again on the changed code", "record": failed,
                      "assessment": assess_record(failed, repo)})

        source.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
        git("add", "arithmetic.py")
        git("commit", "-qm", "repair addition")
        repaired = record_command(repo, base / "repaired.json", command)
        steps.append({"name": "Repair the code and record a new test run", "record": repaired,
                      "assessment": assess_record(repaired, repo)})
        return steps
