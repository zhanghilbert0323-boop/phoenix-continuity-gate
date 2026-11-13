"""Version reporting must not inspect a repository or execute a command."""

import contextlib
import io
import unittest
from unittest.mock import patch

from phoenix_continuity_gate import __version__
from phoenix_continuity_gate.__main__ import main


class VersionTests(unittest.TestCase):
    def test_version_exits_successfully_without_project_work(self):
        output = io.StringIO()
        with patch("sys.argv", ["phoenix-gate", "--version"]), \
             patch("phoenix_continuity_gate.__main__.record_command") as execute, \
             patch("phoenix_continuity_gate.__main__.assess_record") as inspect, \
             patch("phoenix_continuity_gate.__main__.evaluate") as check, \
             contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as stopped:
            main()
        self.assertEqual(stopped.exception.code, 0)
        self.assertEqual(output.getvalue().strip(), f"Phoenix Continuity Gate {__version__}")
        execute.assert_not_called()
        inspect.assert_not_called()
        check.assert_not_called()
