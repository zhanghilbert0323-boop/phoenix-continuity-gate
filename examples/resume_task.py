"""Read Phoenix's installed JSON interface and print an example resume decision.

Use the environment in which the development package is installed. This example
never executes test commands from records or starts a resumed task.
"""

import argparse
import json
import math
from pathlib import Path
import subprocess
import sys

from phoenix_continuity_gate.resume import plan_from_report


def main():
    parser = argparse.ArgumentParser(description="Example evidence decision before resuming a coding task")
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=90)
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("Timeout must be a positive finite number")
    try:
        process = subprocess.run([sys.executable, "-I", "-m", "phoenix_continuity_gate", "inspect",
                                  "--repo", str(args.repo), "--record", str(args.record), "--json"],
                                 capture_output=True, text=True, timeout=args.timeout)
        report = json.loads(process.stdout)
        plan = plan_from_report(report, process.returncode)
        code = process.returncode if process.returncode in (0, 1, 2) else 2
    except (OSError, ValueError, subprocess.SubprocessError):
        plan, code = plan_from_report(None, 2), 2
    if plan["action"] == "INSPECTION_ERROR":
        code = 2
    print(json.dumps(plan, ensure_ascii=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
