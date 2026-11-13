"""GitHub Actions adapter. Inputs travel through env, never shell interpolation."""

import json
import os
from pathlib import Path
import subprocess

from .team import run_checks


def main():
    try:
        mode = os.environ.get("PHOENIX_MODE", "status")
        config = os.environ.get("PHOENIX_CONFIG", "")
        check = os.environ.get("PHOENIX_CHECK", "")
        state = os.environ.get("PHOENIX_STATE", "")
        if mode not in ("status", "refresh") or not config or not check:
            raise ValueError("Provide config and check; mode must be status or explicit refresh")
        if not state:
            runner_temp = os.environ.get("RUNNER_TEMP")
            if not runner_temp:
                raise ValueError("Provide state or RUNNER_TEMP")
            state = str(Path(runner_temp) / "phoenix-team-state")
        result, code = run_checks(config, state, mode, check)
        decision = result["checks"][0]["decision"]["action"]
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result, code, decision = {"team_schema_version": 1, "verdict": "BLOCK",
                                  "checks": [], "error": str(exc)}, 2, "INSPECTION_ERROR"
    try:
        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with Path(output).open("a", encoding="utf-8") as stream:
                stream.write(f"verdict={result['verdict']}\ndecision={decision}\n")
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with Path(summary).open("a", encoding="utf-8") as stream:
                stream.write(f"### Phoenix evidence check\n\n{result['verdict']} / {decision}\n\n"
                             "Local editable evidence only; this is not merge/deploy authorization.\n")
    except OSError:
        result, code = {"team_schema_version": 1, "verdict": "BLOCK", "checks": [],
                        "error": "Could not write CI outputs. Review completed work before retrying."}, 2
    print(json.dumps(result, ensure_ascii=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
