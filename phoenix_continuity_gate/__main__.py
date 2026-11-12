"""Command-line entry point for the first Phoenix Continuity Gate proof."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .demo import run_demo
from .gate import evaluate
from .evidence import assess_record, record_command
from .evidence_demo import run_evidence_demo


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether a coding-agent handoff is stale.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="Compare handoff claims with a local Git repository")
    check.add_argument("--repo", type=Path, required=True)
    check.add_argument("--handoff", type=Path, required=True)
    subparsers.add_parser("demo", help="Show a fresh handoff and a stale one in a disposable repository")
    subparsers.add_parser("demo-record", help="Run real tests in a disposable project: pass, stale, fail, repair")
    record = subparsers.add_parser("record", help="Explicitly execute a command and save a new local record")
    record.add_argument("--repo", type=Path, required=True)
    record.add_argument("--output", type=Path, required=True, help="New JSON file outside the repository")
    record.add_argument("--timeout", type=float, default=60, help="Foreground command timeout in seconds (default: 60)")
    record.add_argument("argv", nargs=argparse.REMAINDER, help="-- followed by an executable and its arguments")
    inspect = subparsers.add_parser("inspect", help="Read an execution record and compare current files; runs no stored command")
    inspect.add_argument("--repo", type=Path, required=True)
    inspect.add_argument("--record", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "demo-record":
        try:
            steps = run_evidence_demo()
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            print(f"Execution demo failed: {exc}", file=sys.stderr)
            return 2
        for index, step in enumerate(steps, 1):
            result = step["assessment"]
            print(f"Step {index}: {step['name']}")
            print(f"  Execution: {result['execution']} | Freshness: {result['freshness']} | Gate: {result['verdict']}")
            if result["freshness"] in ("CHANGED", "UNSTABLE_DURING_RUN"):
                for finding in result["findings"]:
                    print(f"  Why: {finding}")
        print("Real unittest commands ran in a temporary project. Sample files and records were removed.")
        print("Scope: local observations, not authenticated proof or a guarantee of correctness.")
        expected = [("SUCCEEDED", "MATCH", "PASS"), ("SUCCEEDED", "CHANGED", "BLOCK"),
                    ("FAILED", "MATCH", "BLOCK"), ("SUCCEEDED", "MATCH", "PASS")]
        actual = [(s["assessment"]["execution"], s["assessment"]["freshness"], s["assessment"]["verdict"]) for s in steps]
        return 0 if actual == expected else 2

    if args.command in ("record", "inspect"):
        try:
            if args.command == "record":
                if not args.argv or args.argv[0] != "--":
                    parser.error("Put -- before the command you explicitly want to execute")
                evidence = record_command(args.repo, args.output, args.argv[1:], args.timeout)
                print(f"Record: {args.output.resolve()}")
            else:
                evidence = json.loads(args.record.read_text(encoding="utf-8-sig"))
            result = assess_record(evidence, args.repo)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            print(f"Cannot assess execution evidence: {exc}", file=sys.stderr)
            return 2
        print(f"Execution: {result['execution']}")
        print(f"Freshness: {result['freshness']}")
        print(f"Gate: {result['verdict']}")
        for finding in result["findings"]:
            print(f"- {finding}")
        print(f"Scope: {result['scope']}")
        return {"PASS": 0, "REVIEW": 1, "BLOCK": 2}[result["verdict"]]

    if args.command == "demo":
        try:
            result = run_demo()
        except (OSError, subprocess.CalledProcessError, ValueError) as exc:
            print(f"Demo failed: {exc}", file=sys.stderr)
            return 2
        print("Step 1: Handoff and repository both refer to snapshot A")
        print(f"  Git HEAD: {str(result['first_head'])[:12]}")
        print(f"  Gate: {result['before_verdict']}")
        print("Step 2: Repository changes to snapshot B; handoff still refers to A")
        print(f"  Git HEAD: {str(result['second_head'])[:12]}")
        print(f"  Gate: {result['after_verdict']}")
        for finding in result["after_findings"]:
            print(f"  Why: {finding}")
        print("Scope: this checks recorded consistency, not whether tests actually ran.")
        return 0 if (result["before_verdict"], result["after_verdict"]) == ("PASS", "BLOCK") else 2

    try:
        handoff = json.loads(args.handoff.read_text(encoding="utf-8-sig"))
        if not isinstance(handoff, dict):
            raise ValueError("Handoff JSON must be an object")
        verdict, findings = evaluate(handoff, args.repo)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"BLOCK: {exc}", file=sys.stderr)
        return 2

    print(verdict)
    print("Execution: UNKNOWN (handoff claim only; no execution record inspected)")
    for finding in findings:
        print(f"- {finding}")
    return {"PASS": 0, "REVIEW": 1, "BLOCK": 2}[verdict]


if __name__ == "__main__":
    raise SystemExit(main())
