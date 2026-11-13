"""Adapter input failures stop; output files contain only controlled enums."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from phoenix_continuity_gate import ci


class CIAdapterTests(unittest.TestCase):
    def test_missing_or_unknown_inputs_stop_without_running(self):
        for env in ({}, {"PHOENIX_CONFIG": "x", "PHOENIX_CHECK": "unit", "PHOENIX_MODE": "retry"},
                    {"PHOENIX_CONFIG": "x", "PHOENIX_CHECK": "unit"}):
            with patch.dict("os.environ", env, clear=True), patch.object(ci, "run_checks") as run:
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(ci.main(), 2)
                run.assert_not_called()
                self.assertEqual(json.loads(output.getvalue())["verdict"], "BLOCK")

    def test_default_status_uses_private_runner_state_and_exports_enums(self):
        with tempfile.TemporaryDirectory() as temp:
            output, summary = Path(temp) / "output", Path(temp) / "summary"
            env = {"PHOENIX_CONFIG": "reviewed.toml", "PHOENIX_CHECK": "unit", "RUNNER_TEMP": temp,
                   "GITHUB_OUTPUT": str(output), "GITHUB_STEP_SUMMARY": str(summary)}
            value = {"team_schema_version": 1, "verdict": "PASS", "checks": [
                {"decision": {"action": "READY_FOR_NEXT_STEP"}}]}
            with patch.dict("os.environ", env, clear=True), patch.object(ci, "run_checks", return_value=(value, 0)) as run:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(ci.main(), 0)
                run.assert_called_once_with("reviewed.toml", str(Path(temp) / "phoenix-team-state"), "status", "unit")
            self.assertEqual(output.read_text(), "verdict=PASS\ndecision=READY_FOR_NEXT_STEP\n")
            self.assertIn("not merge/deploy authorization", summary.read_text())

    def test_refresh_is_explicit_and_failure_exit_is_preserved(self):
        env = {"PHOENIX_CONFIG": "x", "PHOENIX_CHECK": "unit", "PHOENIX_STATE": "private", "PHOENIX_MODE": "refresh"}
        value = {"verdict": "BLOCK", "checks": [{"decision": {"action": "REVIEW_RECORDED_FAILURE"}}]}
        with patch.dict("os.environ", env, clear=True), patch.object(ci, "run_checks", return_value=(value, 2)) as run:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ci.main(), 2)
            run.assert_called_once_with("x", "private", "refresh", "unit")

    def test_output_write_failure_does_not_retry_command(self):
        with tempfile.TemporaryDirectory() as temp:
            env = {"PHOENIX_CONFIG": "x", "PHOENIX_CHECK": "unit", "PHOENIX_STATE": "private", "PHOENIX_MODE": "refresh",
                   "GITHUB_OUTPUT": str(Path(temp) / "missing" / "output")}
            value = {"verdict": "PASS", "checks": [{"decision": {"action": "READY_FOR_NEXT_STEP"}}]}
            with patch.dict("os.environ", env, clear=True), patch.object(ci, "run_checks", return_value=(value, 0)) as run:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(ci.main(), 2)
                self.assertEqual(run.call_count, 1)
