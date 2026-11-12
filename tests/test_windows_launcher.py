"""Exercise the public Windows launcher without changing installed software."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == "nt", "Windows CMD launcher integration tests")
class WindowsLauncherTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="phoenix-launcher-test-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.project = self.base / "trial with spaces & (parentheses) ! 中文"
        self.project.mkdir()
        self.outside = self.base / "unrelated working directory"
        self.outside.mkdir()
        self.launcher = self.project / "START_DEMO.cmd"
        shutil.copyfile(PROJECT_ROOT / "START_DEMO.cmd", self.launcher)
        self.bootstrap = self.project / "start_demo.py"

    def copy_real_bootstrap(self):
        shutil.copyfile(PROJECT_ROOT / "start_demo.py", self.bootstrap)
        shutil.copytree(
            PROJECT_ROOT / "phoenix_continuity_gate",
            self.project / "phoenix_continuity_gate",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )

    def write_stub(self, source):
        self.bootstrap.write_text(textwrap.dedent(source), encoding="utf-8")

    def run_launcher(self, *arguments):
        # Use an explicit Windows command line: Python's generic argv quoting
        # escapes embedded quotes for C runtimes, not CMD's /S /C parser.
        cmd = Path(os.environ["SystemRoot"]) / "System32" / "cmd.exe"
        command = '"{}" /d /s /c ""{}" {}"'.format(
            cmd, self.launcher, " ".join(arguments)
        )
        environment = os.environ.copy()
        paths = [str(Path(sys.executable).parent)]
        git = shutil.which("git")
        if git:
            paths.append(str(Path(git).parent))
        paths.extend([str(cmd.parent), str(cmd.parent.parent)])
        # This affects this test subprocess only, never the user's PATH.
        environment["PATH"] = os.pathsep.join(paths)
        return subprocess.run(
            command,
            executable=str(cmd),
            cwd=self.outside,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )

    def test_check_works_from_special_character_path_and_unrelated_cwd(self):
        self.copy_real_bootstrap()
        result = self.run_launcher("--check", "--no-pause")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("Step 1:", result.stdout)

    def test_default_runs_actual_demo_once_without_pause(self):
        self.copy_real_bootstrap()
        result = self.run_launcher("--no-pause")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Step 1:", result.stdout)
        self.assertIn("Step 4:", result.stdout)
        self.assertEqual(result.stdout.count("Gate: PASS"), 2, result.stdout)
        self.assertEqual(result.stdout.count("Gate: BLOCK"), 2, result.stdout)
        self.assertIn('CONTENT_CHANGED: "arithmetic.py"', result.stdout)

    def test_missing_bootstrap_is_a_visible_failure(self):
        result = self.run_launcher("--check", "--no-pause")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("start_demo.py", result.stdout)

    def test_nonzero_bootstrap_status_is_preserved(self):
        self.write_stub('''
            import sys
            if "--probe" in sys.argv:
                print("PHOENIX_READY")
                raise SystemExit(0)
            print("EXPECTED_BOOTSTRAP_FAILURE")
            raise SystemExit(37)
        ''')
        result = self.run_launcher("--check", "--no-pause")
        self.assertIn("EXPECTED_BOOTSTRAP_FAILURE", result.stdout)
        self.assertEqual(result.returncode, 37, result.stdout)

    def test_zero_exit_without_probe_output_is_not_accepted(self):
        self.write_stub('''
            import sys
            if "--probe" in sys.argv:
                raise SystemExit(0)
            print("SILENT_PROBE_WAS_WRONGLY_ACCEPTED")
            raise SystemExit(0)
        ''')
        result = self.run_launcher("--check", "--no-pause")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("SILENT_PROBE_WAS_WRONGLY_ACCEPTED", result.stdout)

    def test_selected_interpreter_is_reused_and_check_is_forwarded(self):
        self.write_stub('''
            import json
            import sys
            from pathlib import Path
            root = Path(__file__).resolve().parent
            if "--probe" in sys.argv:
                (root / "probe.json").write_text(
                    json.dumps({"executable": sys.executable}), encoding="utf-8")
                print("PHOENIX_READY")
                raise SystemExit(0)
            (root / "run.json").write_text(json.dumps({
                "executable": sys.executable,
                "arguments": sys.argv[1:],
                "isolated": sys.flags.isolated,
                "no_bytecode": sys.flags.dont_write_bytecode,
            }), encoding="utf-8")
        ''')
        result = self.run_launcher("--check", "--no-pause")
        self.assertEqual(result.returncode, 0, result.stdout)
        probe = json.loads((self.project / "probe.json").read_text(encoding="utf-8"))
        run = json.loads((self.project / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(run["executable"], probe["executable"])
        self.assertTrue(Path(run["executable"]).is_absolute())
        self.assertIn("--check", run["arguments"])
        self.assertEqual(run["isolated"], 1)
        self.assertEqual(run["no_bytecode"], 1)

    def test_check_is_respected_when_no_pause_comes_first(self):
        self.write_stub('''
            import sys
            if "--probe" in sys.argv:
                print("PHOENIX_READY")
                raise SystemExit(0)
            if sys.argv[1:] == ["--check"]:
                print("CHECK_ONLY_REQUEST_RESPECTED")
                raise SystemExit(0)
            print("ERROR_REQUESTED_PREFLIGHT_BUT_STARTED_DEMO")
            raise SystemExit(31)
        ''')
        result = self.run_launcher("--no-pause", "--check")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("CHECK_ONLY_REQUEST_RESPECTED", result.stdout)
        self.assertNotIn("ERROR_REQUESTED_PREFLIGHT_BUT_STARTED_DEMO", result.stdout)

    def test_unknown_option_is_rejected_before_running_bootstrap(self):
        self.write_stub('''
            import sys
            if "--probe" in sys.argv:
                print("PHOENIX_READY")
                raise SystemExit(0)
            print("ERROR_UNKNOWN_ARGUMENT_WAS_IGNORED")
        ''')
        result = self.run_launcher("--no-pause", "--not-a-real-option")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("ERROR_UNKNOWN_ARGUMENT_WAS_IGNORED", result.stdout)


if __name__ == "__main__":
    unittest.main()
