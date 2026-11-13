"""Named checks bind command identity and never silently share successful state."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_managed as fixtures
from phoenix_continuity_gate.managed import inspect_current, refresh_current
from phoenix_continuity_gate.team import load_project, run_checks


class TeamTests(unittest.TestCase):
    def setUp(self):
        fixtures.ManagedWorkflowTests.setUp(self)
        self.config = self.repo / "phoenix.toml"
        self.write_config()

    def write_config(self, command=None, timeout=30, second=False):
        command = command or ["{python}", "-B", "-c", "print('unit checked')"]
        text = ('config_schema_version = 1\nproject = "sample"\n[checks.unit]\n'
                f'command = {json.dumps(command)}\ntimeout_seconds = {timeout}\n'
                'scope = "tracked-repository"\n')
        if second:
            text += ('\n[checks.lint]\ncommand = ["{python}", "-B", "-c", "raise SystemExit(1)"]\n'
                     'timeout_seconds = 30\nscope = "tracked-repository"\n')
        self.config.write_text(text, encoding="utf-8")
        fixtures.git(self.repo, "add", ".")
        fixtures.git(self.repo, "commit", "-qm", "check configuration")

    def run_team(self, action, name="unit"):
        return run_checks(self.config, self.state, action, name)

    def test_refresh_and_status_bind_check_and_preserve_old_records(self):
        result, code = self.run_team("refresh")
        self.assertEqual((code, result["verdict"]), (0, "PASS"))
        with patch("phoenix_continuity_gate.managed.record_command") as execute:
            self.assertEqual(self.run_team("status")[1], 0)
            execute.assert_not_called()
        project = load_project(self.config)
        selected = project.state_for(self.state, project.checks[0])
        with self.assertRaisesRegex(ValueError, "team interface"):
            inspect_current(self.repo, selected)
        with self.assertRaisesRegex(ValueError, "team interface"):
            refresh_current(self.repo, selected, [sys.executable, "-c", "pass"])
        self.assertEqual(len(list(selected.glob("run-*.json"))), 1)

    def test_command_definition_change_stops_until_explicit_refresh(self):
        self.run_team("refresh")
        self.write_config(command=["{python}", "-B", "-c", "raise SystemExit(1)"])
        result, code = self.run_team("status")
        self.assertEqual(code, 2)
        self.assertIn("definition changed", result["checks"][0]["error"])
        result, code = self.run_team("refresh")
        self.assertEqual(code, 2)
        self.assertEqual(result["checks"][0]["decision"]["action"], "REVIEW_RECORDED_FAILURE")

    def test_timeout_definition_change_also_invalidates_binding(self):
        self.run_team("refresh")
        self.write_config(timeout=31)
        self.assertIn("definition changed", self.run_team("status")[0]["checks"][0]["error"])

    def test_two_checks_are_isolated_and_aggregate_status_does_not_run_either(self):
        self.write_config(second=True)
        self.assertEqual(self.run_team("refresh", "unit")[1], 0)
        self.assertEqual(self.run_team("refresh", "lint")[1], 2)
        with patch("phoenix_continuity_gate.managed.record_command") as execute:
            result, code = self.run_team("status", None)
            execute.assert_not_called()
        self.assertEqual(code, 2)
        actions = {item["check"]: item["decision"]["action"] for item in result["checks"]}
        self.assertEqual(actions, {"unit": "READY_FOR_NEXT_STEP", "lint": "REVIEW_RECORDED_FAILURE"})

    def test_config_and_state_inside_target_are_never_conflated(self):
        with patch("phoenix_continuity_gate.managed.record_command") as execute:
            with self.assertRaisesRegex(ValueError, "outside"):
                run_checks(self.config, self.repo / "bad-state", "refresh", "unit")
            execute.assert_not_called()
        self.assertFalse((self.repo / "bad-state").exists())

    def test_unknown_check_and_refresh_all_are_rejected_before_execution(self):
        with patch("phoenix_continuity_gate.managed.record_command") as execute:
            for name in (None, "missing"):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    self.run_team("refresh", name)
            execute.assert_not_called()

    def test_selected_command_is_checked_even_if_checksum_is_recomputed(self):
        self.run_team("refresh")
        project = load_project(self.config)
        state = project.state_for(self.state, project.checks[0])
        pointer_file = state / "current.json"
        pointer = json.loads(pointer_file.read_text())
        path = state / pointer["record"]
        record = json.loads(path.read_text())
        record["command"] = [sys.executable, "-c", "print('wrong check')"]
        path.write_text(json.dumps(record), encoding="utf-8")
        pointer["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        pointer_file.write_text(json.dumps(pointer), encoding="utf-8")
        self.assertIn("command does not match", self.run_team("status")[0]["checks"][0]["error"])

    def test_invalid_config_variants_and_unknown_keys_stop(self):
        original = self.config.read_text()
        variants = [original.replace("config_schema_version = 1", "config_schema_version = true"),
                    original.replace("config_schema_version = 1", "config_schema_version = 2"),
                    original.replace('project = "sample"', 'project = "../other"'),
                    original.replace("[checks.unit]", '[checks."../escape"]'),
                    original.replace("timeout_seconds = 30", "timeout_seconds = nan"),
                    original.replace("timeout_seconds = 30", "timeout_seconds = true"),
                    original.replace("timeout_seconds = 30", "timeout_seconds = -1"),
                    original.replace("timeout_seconds = 30", "timeout_seconds = 86401"),
                    original.replace("timeout_seconds = 30", "timeout_seconds = " + "9" * 400),
                    original.replace('scope = "tracked-repository"', 'scope = "automatic"'),
                    original.replace('"{python}"', '"{python}/bad"'),
                    original.replace('"print(\'unit checked\')"', '"{python}"'),
                    original + '\nextra = "misspelled option"\n',
                    'config_schema_version = 1\nproject = "sample"\n[checks]\n']
        for text in variants:
            self.config.write_text(text, encoding="utf-8")
            with self.subTest(config=text), self.assertRaises(ValueError):
                load_project(self.config)

    def test_untracked_config_is_rejected_without_running_any_command(self):
        untracked = self.repo / "untracked.toml"
        untracked.write_bytes(self.config.read_bytes())
        with patch("phoenix_continuity_gate.managed.record_command") as execute:
            with self.assertRaisesRegex(ValueError, "must be tracked"):
                run_checks(untracked, self.state, "refresh", "unit")
            execute.assert_not_called()

    def test_same_project_name_at_other_repo_path_gets_different_state(self):
        from dataclasses import replace
        project = load_project(self.config)
        other = replace(project, root=self.base / "other-repo")
        self.assertNotEqual(project.state_for(self.state, project.checks[0]),
                            other.state_for(self.state, project.checks[0]))

    def test_cli_validate_and_missing_state_are_machine_readable(self):
        command = [sys.executable, "-B", "-m", "phoenix_continuity_gate", "team"]
        valid = subprocess.run([*command, "validate", "--config", str(self.config)],
                               capture_output=True, text=True, timeout=30)
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertTrue(json.loads(valid.stdout)["valid"])
        status = subprocess.run([*command, "status", "--config", str(self.config), "--state", str(self.state)],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(status.returncode, 2)
        self.assertEqual(json.loads(status.stdout)["verdict"], "BLOCK")

    def test_cli_refresh_runs_only_the_reviewed_named_command(self):
        command = [sys.executable, "-B", "-m", "phoenix_continuity_gate", "team"]
        result = subprocess.run([*command, "refresh", "--config", str(self.config), "--state", str(self.state),
                                 "--check", "unit"], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["checks"][0]["decision"]["action"], "READY_FOR_NEXT_STEP")

