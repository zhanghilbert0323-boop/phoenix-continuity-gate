"""Command-line entry point for the first Phoenix Continuity Gate proof."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .demo import run_demo
from .gate import evaluate


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether a coding-agent handoff is stale.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="Compare handoff claims with a local Git repository")
    check.add_argument("--repo", type=Path, required=True)
    check.add_argument("--handoff", type=Path, required=True)
    subparsers.add_parser("demo", help="Show a fresh handoff and a stale one in a disposable repository")
    args = parser.parse_args()

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
        handoff = json.loads(args.handoff.read_text(encoding="utf-8"))
        if not isinstance(handoff, dict):
            raise ValueError("Handoff JSON must be an object")
        verdict, findings = evaluate(handoff, args.repo)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"BLOCK: {exc}", file=sys.stderr)
        return 2

    print(verdict)
    for finding in findings:
        print(f"- {finding}")
    return {"PASS": 0, "REVIEW": 1, "BLOCK": 2}[verdict]


if __name__ == "__main__":
    raise SystemExit(main())
