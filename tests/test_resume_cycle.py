"""Exercise a bounded refresh lifecycle, including the caller's stale selection."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "experiments" / "resume_cycle.py"


class ResumeCycleTests(unittest.TestCase):
    def test_explicit_refresh_stops_stale_requests_without_retrying_failures(self):
        spec = importlib.util.spec_from_file_location("resume_cycle_experiment", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = module.run_cycle()
        self.assertTrue(report["passed"], report["checks"])
        self.assertEqual(report["summary"]["inspection_calls"], 14)
        self.assertEqual(report["summary"]["observed_command_starts"], 4)
        self.assertEqual(report["summary"]["command_starts_during_inspections"], 0)
        refreshed = [event for event in report["resume_events"] if event["selected_record"] == "B"
                     and event["stage"] == "unchanged_after_explicit_switch_to_B"]
        self.assertEqual(len(refreshed), 4)
        self.assertTrue(all(event["action"] == "READY_FOR_NEXT_STEP" for event in refreshed))
        control = next(event for event in report["resume_events"] if event["stage"].startswith("negative_control"))
        self.assertEqual(control["action"], "NEEDS_FRESH_EVIDENCE")

    def test_existing_report_is_preserved_before_any_experiment_runs(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "existing.json"
            output.write_text("keep me", encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--output", str(output)],
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep me")
