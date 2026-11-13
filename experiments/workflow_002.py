"""Exercise real project tests in an isolated copy with controlled changes.

This is a fault-injection experiment, not an observed customer incident.
Run from the project root: python experiments/workflow_002.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from phoenix_continuity_gate.gate import evaluate  # noqa: E402


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True,
        text=True, timeout=30,
    ).stdout.strip()


def run_tests(repo: Path) -> dict:
    command = [sys.executable, "-E", "-s", "-B", "-m", "unittest", "discover", "-s", "tests", "-v"]
    before = git(repo, "rev-parse", "HEAD")
    start = time.monotonic()
    result = subprocess.run(command, cwd=repo, capture_output=True, text=True, timeout=90)
    return {
        "command": ["python", *command[1:]],
        "head_before": before,
        "head_after": git(repo, "rev-parse", "HEAD"),
        "working_tree_after": git(repo, "status", "--porcelain"),
        "exit_code": result.returncode,
        "elapsed_seconds": round(time.monotonic() - start, 3),
        "stdout": result.stdout.replace(str(repo), "<experiment-repo>"),
        "stderr": result.stderr.replace(str(repo), "<experiment-repo>"),
    }


def observe(repo: Path, handoff: dict, name: str, tests: dict | None) -> dict:
    verdict, findings = evaluate(handoff, repo)
    return {"case": name, "gate": verdict, "findings": findings, "test_run": tests}


def experiment() -> dict:
    with tempfile.TemporaryDirectory(prefix="phoenix-workflow-002-") as directory:
        repo = Path(directory)
        for folder in ("phoenix_continuity_gate", "tests"):
            shutil.copytree(ROOT / folder, repo / folder, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for filename in ("README.md", ".gitignore", "start_demo.py", "START_DEMO.cmd"):
            shutil.copy2(ROOT / filename, repo / filename)
        (repo / "experiments").mkdir()
        shutil.copy2(ROOT / "experiments" / "resume_cycle.py", repo / "experiments" / "resume_cycle.py")
        source_hashes = {
            path.relative_to(repo).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(repo.rglob("*")) if path.is_file()
        }
        git(repo, "init", "-q")
        git(repo, "config", "user.name", "Phoenix Controlled Experiment")
        git(repo, "config", "user.email", "experiment@example.invalid")
        git(repo, "config", "core.hooksPath", str(repo / "no-hooks"))
        git(repo, "config", "commit.gpgSign", "false")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "baseline snapshot")
        baseline = git(repo, "rev-parse", "HEAD")
        handoff = {"schema_version": 1, "repo_head": baseline,
                   "tests": {"status": "passed", "git_head": baseline}}

        cases = [observe(repo, handoff, "claim_before_any_test_run", None)]
        cases.append(observe(repo, handoff, "baseline_after_actual_tests", run_tests(repo)))

        with (repo / "README.md").open("a", encoding="utf-8") as stream:
            stream.write("\nControlled experiment: documentation-only change.\n")
        git(repo, "add", "README.md")
        git(repo, "commit", "-qm", "documentation-only change")
        cases.append(observe(repo, handoff, "documentation_changed_old_handoff", run_tests(repo)))

        # Only the disposable copy is modified. The checker above remains the
        # original implementation; the child test run exercises the broken copy.
        with (repo / "phoenix_continuity_gate" / "gate.py").open("a", encoding="utf-8") as stream:
            stream.write("\n\ndef evaluate(handoff, repo):\n"
                         "    return 'PASS', ['Deliberately injected regression.']\n")
        git(repo, "add", "phoenix_continuity_gate/gate.py")
        git(repo, "commit", "-qm", "inject always-pass regression for experiment")
        cases.append(observe(repo, handoff, "code_regression_old_handoff", run_tests(repo)))

        expected = ["PASS", "PASS", "BLOCK", "BLOCK"]
        if [case["gate"] for case in cases] != expected:
            actual = [(case["case"], case["gate"], case["findings"]) for case in cases]
            raise RuntimeError(f"Unexpected Gate verdicts: {actual!r}")
        for case in cases[1:]:
            run = case["test_run"]
            if run["head_before"] != run["head_after"] or run["working_tree_after"]:
                raise RuntimeError("Tests changed the snapshot; this experiment cannot bind results to a clean commit")
        if cases[1]["test_run"]["exit_code"] != 0 or cases[2]["test_run"]["exit_code"] != 0:
            raise RuntimeError("Baseline or documentation-only tests unexpectedly failed")
        if cases[3]["test_run"]["exit_code"] == 0:
            raise RuntimeError("The injected regression was not detected by the test suite")
        if "FAIL: test_new_commit_blocks_stale_handoff" not in cases[3]["test_run"]["stderr"]:
            raise RuntimeError("The regression run failed for an unexpected reason")
        return {"experiment": "workflow-002", "kind": "controlled_fault_injection",
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "python_version": sys.version.split()[0], "git_version": git(repo, "--version"),
                "source_sha256": source_hashes,
                "scope": "Real subprocess test runs on an isolated copy; no customer validation or tamper-proof evidence.",
                "cases": cases}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "experiments" / "results" / "workflow-002.json")
    args = parser.parse_args()
    report = experiment()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for case in report["cases"]:
        test_result = "not run" if case["test_run"] is None else str(case["test_run"]["exit_code"])
        print(f"{case['case']}: gate={case['gate']}; test exit={test_result}")
    print(f"Report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
