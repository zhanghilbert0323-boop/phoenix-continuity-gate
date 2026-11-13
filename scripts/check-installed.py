"""Verify an installed wheel from outside the source tree, using a disposable demo.

Run with the isolated environment's Python and -I after pip install .
This script is a developer check, not a customer usage report.
"""

import os
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
    print(f"Installed package: {installed}")
    print("Only disposable sample tests ran. External user workflows remain unverified.")


if __name__ == "__main__":
    main()
