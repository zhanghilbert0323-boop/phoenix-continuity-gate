"""Verify an installed wheel from outside the source tree, using a disposable demo.

Run with the isolated environment's Python and -I after pip install .
This script is a developer check, not a customer usage report.
"""

import os
import json
from pathlib import Path
import subprocess
import sys
import sysconfig
import tempfile

import phoenix_continuity_gate
from phoenix_continuity_gate import __version__


def main():
    source = Path(__file__).resolve().parents[1]
    installed = Path(phoenix_continuity_gate.__file__).resolve()
    if installed.is_relative_to(source):
        raise RuntimeError("Package resolved to the source tree; this did not test an installation")
    executable = Path(sysconfig.get_path("scripts")) / ("phoenix-gate.exe" if os.name == "nt" else "phoenix-gate")
    if not executable.is_file():
        raise RuntimeError("Installed console entry point is missing")
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    with tempfile.TemporaryDirectory(prefix="phoenix-installed-") as temp:
        for args, marker in [(["--version"], __version__), (["--help"], "inspect"),
                             (["demo-record"], "CONTENT_CHANGED:")]:
            result = subprocess.run([str(executable), *args], cwd=temp, env=env,
                                    capture_output=True, text=True, timeout=90)
            if result.returncode or marker not in result.stdout:
                raise RuntimeError(f"Installed command failed {args!r}: {result.stdout}\n{result.stderr}")
            if args == ["demo-record"]:
                for state in ("SUCCEEDED | Freshness: MATCH | Gate: PASS",
                              "SUCCEEDED | Freshness: CHANGED | Gate: BLOCK",
                              "FAILED | Freshness: MATCH | Gate: BLOCK"):
                    if state not in result.stdout:
                        raise RuntimeError(f"Installed demo did not report {state}")
            print(f"PASS installed phoenix-gate {' '.join(args)} from unrelated directory")
        repo = Path(temp) / "repo"
        repo.mkdir()
        for args in [("init", "-q"), ("config", "user.name", "Installed CLI Test"),
                     ("config", "user.email", "test@example.invalid"),
                     ("config", "commit.gpgSign", "false"),
                     ("config", "core.hooksPath", str(Path(temp) / "no-hooks"))]:
            subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, timeout=30)
        sample = repo / "sample.txt"
        sample.write_text("initial\n", encoding="utf-8")
        for args in [("add", "."), ("commit", "-qm", "sample")]:
            subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, timeout=30)
        record = Path(temp) / "run.json"
        run = subprocess.run([str(executable), "record", "--repo", str(repo), "--output", str(record),
                              "--", sys.executable, "-B", "-c", "print('installed sample command')"],
                             cwd=temp, env=env, capture_output=True, text=True, timeout=90)
        if run.returncode:
            raise RuntimeError(f"Installed record failed: {run.stdout}\n{run.stderr}")
        for changed, expected_code, expected_freshness in [(False, 0, "MATCH"), (True, 2, "CHANGED")]:
            if changed:
                sample.write_text("normal edit\n", encoding="utf-8")
            check = subprocess.run([str(executable), "inspect", "--repo", str(repo),
                                    "--record", str(record), "--json"],
                                   cwd=temp, env=env, capture_output=True, text=True, timeout=30)
            report = json.loads(check.stdout)
            if (check.returncode != expected_code or check.stderr or report.get("report_schema_version") != 1
                    or report.get("assessment_status") != "ASSESSED"
                    or report.get("freshness") != expected_freshness
                    or report.get("verdict") != ("BLOCK" if changed else "PASS")):
                raise RuntimeError(f"Installed JSON inspection failed: {check.stdout}\n{check.stderr}")
            print(f"PASS installed record/inspect JSON: {report['verdict']} / {expected_freshness}")
            example = subprocess.run([sys.executable, "-I", str(source / "examples" / "resume_task.py"),
                                      "--repo", str(repo), "--record", str(record)],
                                     cwd=temp, env=env, capture_output=True, text=True, timeout=90)
            plan = json.loads(example.stdout)
            expected_action = "NEEDS_FRESH_EVIDENCE" if changed else "READY_FOR_NEXT_STEP"
            if example.returncode != expected_code or example.stderr or plan.get("action") != expected_action:
                raise RuntimeError(f"Resume example failed: {example.stdout}\n{example.stderr}")
            print(f"PASS installed resume example: {expected_action}")
        for args in [("add", "."), ("commit", "-qm", "normal edit")]:
            subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, timeout=30)
        failure_record = Path(temp) / "failed.json"
        failed = subprocess.run([str(executable), "record", "--repo", str(repo), "--output", str(failure_record),
                                 "--", sys.executable, "-B", "-c", "raise SystemExit(1)"],
                                cwd=temp, env=env, capture_output=True, text=True, timeout=90)
        if failed.returncode != 2:
            raise RuntimeError("Sample failed command was not blocked")
        review_record = Path(temp) / "review.json"
        review = subprocess.run([str(executable), "record", "--repo", str(repo), "--output", str(review_record),
                                 "--", sys.executable, "-B", "-c",
                                 "from pathlib import Path; Path('sample.txt').write_text('changed during sample command')"],
                                cwd=temp, env=env, capture_output=True, text=True, timeout=90)
        if review.returncode != 1:
            raise RuntimeError("Unstable sample command did not request review")
        for record_path, expected_action, expected_code in [(failure_record, "REVIEW_RECORDED_FAILURE", 2),
                                                            (review_record, "HUMAN_REVIEW", 1),
                                                            (Path(temp) / "missing.json", "INSPECTION_ERROR", 2)]:
            example = subprocess.run([sys.executable, "-I", str(source / "examples" / "resume_task.py"),
                                      "--repo", str(repo), "--record", str(record_path)],
                                     cwd=temp, env=env, capture_output=True, text=True, timeout=90)
            plan = json.loads(example.stdout)
            if example.returncode != expected_code or example.stderr or plan.get("action") != expected_action:
                raise RuntimeError(f"Resume failure case failed: {example.stdout}\n{example.stderr}")
            print(f"PASS installed resume example: {expected_action}")
    print(f"Installed package: {installed}")
    print("Only disposable sample commands and tests ran. External user workflows remain unverified.")


if __name__ == "__main__":
    main()
