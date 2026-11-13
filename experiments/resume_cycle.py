"""Bounded resume-cycle experiment with real sample tests and explicit refreshes.

This models a caller selecting A, then B. Phoenix does not select a latest record
automatically. No third-party bug or customer workflow is reproduced here.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from phoenix_continuity_gate import __version__
from phoenix_continuity_gate.evidence import assess_record, record_command
from phoenix_continuity_gate.resume import plan_from_report

RUNNER = '''import sys
from pathlib import Path
with Path(sys.argv[1]).open("a", encoding="utf-8") as stream:
    stream.write("attempt\\n")
import time
if "--hang" in sys.argv[2:]:
    time.sleep(30)
import unittest
from arithmetic import add
class Tests(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)
unittest.main(argv=["verify.py"])
'''


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True, timeout=30).stdout.strip()


def run_cycle():
    started = datetime.now(timezone.utc).isoformat()
    events, runs = [], []
    with tempfile.TemporaryDirectory(prefix="phoenix-resume-cycle-") as temp:
        base = Path(temp)
        repo = base / "sample"
        repo.mkdir()
        counter = base / "attempts.txt"
        (repo / "arithmetic.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
        (repo / "verify.py").write_text(RUNNER, encoding="utf-8")
        for args in [("init", "-q"), ("config", "user.name", "Resume Cycle Experiment"),
                     ("config", "user.email", "experiment@example.invalid"),
                     ("config", "commit.gpgSign", "false"),
                     ("config", "core.hooksPath", str(base / "no-hooks"))]:
            git(repo, *args)

        def commit(message):
            git(repo, "add", ".")
            git(repo, "commit", "-qm", message)

        def attempts():
            return len(counter.read_text(encoding="utf-8").splitlines()) if counter.exists() else 0

        records, original_bytes = {}, {}

        def refresh(label, expected_status, hang=False):
            before = attempts()
            path = base / f"record-{label}.json"
            command = [sys.executable, "-B", "verify.py", str(counter)]
            if hang:
                command.append("--hang")
            record = record_command(repo, path, command, timeout=3 if hang else 20)
            records[label] = record
            original_bytes[label] = path.read_bytes()
            execution = record["execution"]
            runs.append({"record": label, "expected_execution": expected_status,
                         "observed_execution": execution["status"],
                         "attempts_before": before, "attempts_after": attempts(),
                         "elapsed_seconds": execution["elapsed_seconds"],
                         "unittest_summary_observed": "Ran 1 test" in execution["stderr"]["text"]})

        def resume(label, stage, expected_action):
            before = attempts()
            result = assess_record(records[label], repo)
            report = {"report_schema_version": 1, "assessment_status": "ASSESSED", **result, "error": None}
            code = {"PASS": 0, "REVIEW": 1, "BLOCK": 2}[result["verdict"]]
            plan = plan_from_report(report, code)
            events.append({"stage": stage, "selected_record": label,
                           "execution": result["execution"], "freshness": result["freshness"],
                           "gate": result["verdict"], "action": plan["action"],
                           "expected_action": expected_action,
                           "attempts_before": before, "attempts_after": attempts()})

        commit("working sample")
        refresh("A", "SUCCEEDED")
        for _ in range(3):
            resume("A", "unchanged_after_A", "READY_FOR_NEXT_STEP")
        (repo / "arithmetic.py").write_text("def add(a, b):\n    return sum([a, b])\n", encoding="utf-8")
        commit("equivalent normal code change")
        resume("A", "A_became_stale", "NEEDS_FRESH_EVIDENCE")
        refresh("B", "SUCCEEDED")
        for _ in range(4):
            resume("B", "unchanged_after_explicit_switch_to_B", "READY_FOR_NEXT_STEP")
        resume("A", "negative_control_caller_still_selects_A", "NEEDS_FRESH_EVIDENCE")
        (repo / "arithmetic.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
        commit("controlled failing change")
        resume("B", "B_became_stale", "NEEDS_FRESH_EVIDENCE")
        refresh("C", "FAILED")
        for _ in range(2):
            resume("C", "recorded_failure_no_retry", "REVIEW_RECORDED_FAILURE")
        refresh("T", "TIMED_OUT", hang=True)
        for _ in range(2):
            resume("T", "recorded_timeout_no_retry", "HUMAN_REVIEW")

        unchanged_records = all((base / f"record-{label}.json").read_bytes() == saved
                                for label, saved in original_bytes.items())
        checks = {
            "all_actions_match": all(event["action"] == event["expected_action"] for event in events),
            "all_execution_results_match": all(run["observed_execution"] == run["expected_execution"] for run in runs),
            "inspection_never_increments_attempt_counter": all(event["attempts_before"] == event["attempts_after"] for event in events),
            "each_explicit_refresh_starts_one_command": all(run["attempts_after"] == run["attempts_before"] + 1 for run in runs),
            "three_completed_unittest_runs_observed": sum(run["unittest_summary_observed"] for run in runs) == 3,
            "old_record_files_preserved": unchanged_records,
            "working_tree_clean": git(repo, "status", "--porcelain") == "",
        }
        summary = {"inspection_calls": len(events), "explicit_command_runs": len(runs),
                   "observed_command_starts": attempts(),
                   "command_starts_during_inspections": sum(event["attempts_after"] - event["attempts_before"] for event in events),
                   "unchanged_resumes_using_B": sum(event["stage"] == "unchanged_after_explicit_switch_to_B" for event in events)}
    files = ["phoenix_continuity_gate/evidence.py", "phoenix_continuity_gate/resume.py", "experiments/resume_cycle.py"]
    return {"experiment_schema_version": 1, "experiment": "bounded-resume-cycle",
            "started_at_utc": started, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "python_version": platform.python_version(), "platform": platform.system(),
            "phoenix_version": __version__,
            "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files},
            "summary": summary, "checks": checks, "passed": all(checks.values()),
            "explicit_refreshes": runs, "resume_events": events,
            "limits": ["Controlled temporary sample, not a reproduction of a third-party bug or customer case.",
                       "The caller explicitly chooses A or B; there is no automatic latest-record selection.",
                       "No measured comparison with another agent or always-rerun policy; no customer savings claimed.",
                       "Ignored files, environment changes and test sufficiency remain outside the check scope."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="New report file; existing files are never overwritten")
    args = parser.parse_args()
    try:
        if args.output:
            with args.output.open("x", encoding="utf-8") as stream:
                result = run_cycle()
                json.dump(result, stream, indent=2, ensure_ascii=True)
                stream.write("\n")
            print(json.dumps({"passed": result["passed"], **result["summary"]}))
        else:
            result = run_cycle()
            print(json.dumps(result, indent=2, ensure_ascii=True))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"Resume-cycle experiment failed: {exc}", file=sys.stderr)
        return 2
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
