"""Small first-run preflight; deliberately parseable by older Python 3 versions."""

import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parent


def check_environment(root):
    """Check prerequisites only. Do not run a demo, install, or change files."""
    if sys.version_info < (3, 11):
        print("ERROR: Python 3.11 or newer is required. Selected: " + sys.version.split()[0])
        return False
    print("Python: " + sys.version.split()[0])
    print("Interpreter: " + sys.executable)
    required = ("__init__.py", "__main__.py", "gate.py", "demo.py", "evidence.py", "evidence_demo.py")
    if any(not (root / "phoenix_continuity_gate" / name).is_file() for name in required):
        print("ERROR: Project files are missing. Extract the complete ZIP, not just this launcher.")
        return False
    git = shutil.which("git")
    if git is None:
        print("ERROR: Git was not found. Install Git yourself and reopen this window.")
        return False
    try:
        result = subprocess.run([git, "--version"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError) as exc:
        print("ERROR: Git could not be started: " + str(exc))
        return False
    if result.returncode != 0 or not result.stdout.strip().startswith("git version "):
        print("ERROR: Git did not return a valid version. Check your Git installation.")
        return False
    print("Git: " + result.stdout.strip())
    return True


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--probe"]:
        if sys.version_info >= (3, 11):
            print("PHOENIX_READY")
            return 0
        return 2
    if args not in ([], ["--check"]):
        print("Usage: start_demo.py [--check]")
        return 2
    if not check_environment(ROOT):
        return 2
    if args == ["--check"]:
        print("Prerequisites found. The demo and tests have NOT run.")
        return 0
    print("Starting real tests in a temporary sample. Please wait...", flush=True)
    # The Windows launcher uses -I; add only this extracted project explicitly.
    sys.path.insert(0, str(ROOT))
    original_args = sys.argv
    original_cwd = Path.cwd()
    try:
        os.chdir(ROOT)
        from phoenix_continuity_gate.__main__ import main as demo_main
        sys.argv = ["phoenix_continuity_gate", "demo-record"]
        result = demo_main()
        if result == 0:
            print("Demo completed: PASS -> BLOCK -> BLOCK -> PASS. The two BLOCKs are expected.")
        return result
    except KeyboardInterrupt:
        print("Demo interrupted. Completion has not been verified.")
        return 130
    except Exception as exc:
        print("ERROR: Demo did not complete: " + type(exc).__name__ + ": " + str(exc))
        return 2
    finally:
        sys.argv = original_args
        sys.path.pop(0)
        os.chdir(original_cwd)


if __name__ == "__main__":
    raise SystemExit(main())
