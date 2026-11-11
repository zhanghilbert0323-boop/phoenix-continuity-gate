"""Preflight must not confuse prerequisites, demo completion and success."""

import contextlib
import io
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import start_demo


class StartDemoTests(unittest.TestCase):
    def invoke(self, args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = start_demo.main(args)
        return code, output.getvalue()

    def test_probe_requires_supported_python(self):
        with patch.object(start_demo.sys, "version_info", (3, 10)):
            self.assertEqual(self.invoke(["--probe"]), (2, ""))
        code, text = self.invoke(["--probe"])
        self.assertEqual(code, 0)
        self.assertEqual(text.strip(), "PHOENIX_READY")

    def test_old_python_is_explained_before_git_or_demo(self):
        with patch.object(start_demo.sys, "version_info", (3, 10)), patch.object(start_demo.shutil, "which") as which:
            code, text = self.invoke([])
        self.assertEqual(code, 2)
        self.assertIn("Python 3.11", text)
        which.assert_not_called()

    def test_missing_source_files(self):
        with patch.object(Path, "is_file", return_value=False):
            code, text = self.invoke([])
        self.assertEqual(code, 2)
        self.assertIn("Project files are missing", text)

    def test_missing_git_stops_before_demo(self):
        with patch.object(start_demo.shutil, "which", return_value=None):
            code, text = self.invoke([])
        self.assertEqual(code, 2)
        self.assertIn("Git was not found", text)

    def test_silent_or_failed_git_is_not_success(self):
        for returncode, output in ((0, ""), (1, "git version fake")):
            with self.subTest(returncode=returncode), patch.object(start_demo.shutil, "which", return_value="git"), patch.object(start_demo.subprocess, "run", return_value=subprocess.CompletedProcess([], returncode, output, "")):
                code, text = self.invoke(["--check"])
            self.assertEqual(code, 2)
            self.assertIn("valid version", text)

    def test_git_timeout_is_explained(self):
        with patch.object(start_demo.shutil, "which", return_value="git"), patch.object(start_demo.subprocess, "run", side_effect=subprocess.TimeoutExpired("git", 10)):
            code, text = self.invoke([])
        self.assertEqual(code, 2)
        self.assertIn("Git could not be started", text)

    def test_check_does_not_run_demo(self):
        with patch.object(start_demo, "check_environment", return_value=True), patch("phoenix_continuity_gate.__main__.main") as demo:
            code, text = self.invoke(["--check"])
        self.assertEqual(code, 0)
        self.assertIn("have NOT run", text)
        demo.assert_not_called()

    def test_demo_failure_preserves_code_and_restores_process_state(self):
        previous_args = start_demo.sys.argv
        previous_path = list(start_demo.sys.path)
        previous_cwd = Path.cwd()
        with patch.object(start_demo, "check_environment", return_value=True), patch("phoenix_continuity_gate.__main__.main", return_value=2):
            code, text = self.invoke([])
        self.assertEqual(code, 2)
        self.assertNotIn("Demo completed", text)
        self.assertIs(start_demo.sys.argv, previous_args)
        self.assertEqual(start_demo.sys.path, previous_path)
        self.assertEqual(Path.cwd(), previous_cwd)

    def test_unexpected_demo_error_is_not_silent(self):
        with patch.object(start_demo, "check_environment", return_value=True), patch("phoenix_continuity_gate.__main__.main", side_effect=RuntimeError("example error")):
            code, text = self.invoke([])
        self.assertEqual(code, 2)
        self.assertIn("RuntimeError: example error", text)

    def test_unknown_argument_is_rejected(self):
        code, text = self.invoke(["--install"])
        self.assertEqual(code, 2)
        self.assertIn("Usage:", text)
