"""The example selects the latest explicit attempt, never an old successful one."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from phoenix_continuity_gate.managed import inspect_current, refresh_current


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True, timeout=30).stdout.strip()


class ManagedWorkflowTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="phoenix-managed-")
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.repo = self.base / "repo with spaces"
        self.repo.mkdir()
        self.state = self.base / "private state"
        self.counter = self.base / "starts.txt"
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.name", "Workflow Test")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "commit.gpgSign", "false")
        git(self.repo, "config", "core.hooksPath", str(self.base / "no-hooks"))
        (self.repo / "sample.txt").write_text("A", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "initial")

    def refresh(self, code="pass", **kwargs):
        code = (f"from pathlib import Path; p=Path({str(self.counter)!r}); "
                "p.write_text(p.read_text()+'x' if p.exists() else 'x'); " + code)
        return refresh_current(self.repo, self.state, [sys.executable, "-B", "-c", code], **kwargs)

    def action(self):
        return inspect_current(self.repo, self.state)[0]["decision"]["action"]

    def test_refresh_selects_B_and_status_never_executes(self):
        self.refresh()
        first = (self.state / "current.json").read_bytes()
        for _ in range(3):
            self.assertEqual(self.action(), "READY_FOR_NEXT_STEP")
        (self.repo / "sample.txt").write_text("B", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "change")
        self.assertEqual(self.action(), "NEEDS_FRESH_EVIDENCE")
        self.refresh()
        self.assertNotEqual(first, (self.state / "current.json").read_bytes())
        for _ in range(4):
            self.assertEqual(self.action(), "READY_FOR_NEXT_STEP")
        self.assertEqual(self.counter.read_text(), "xx")
        self.assertEqual(len(list(self.state.glob("run-*.json"))), 2)

    def test_failed_attempt_replaces_prior_success(self):
        self.refresh()
        self.refresh("raise SystemExit(1)")
        self.assertEqual(self.action(), "REVIEW_RECORDED_FAILURE")
        self.assertEqual(self.counter.read_text(), "xx")

    def test_timed_out_attempt_replaces_prior_success(self):
        self.refresh()
        self.refresh("import time; time.sleep(30)", timeout=0.2)
        self.assertEqual(self.action(), "HUMAN_REVIEW")
        self.assertEqual(len(list(self.state.glob("run-*.json"))), 2)

    def test_interrupted_update_blocks_old_success_and_allows_explicit_recovery(self):
        self.refresh()
        with patch("phoenix_continuity_gate.managed.record_command", side_effect=OSError("interrupted")):
            with self.assertRaises(OSError):
                self.refresh()
        with self.assertRaisesRegex(ValueError, "did not complete"):
            self.action()
        self.assertFalse((self.state / ".lock").exists())
        self.refresh()
        self.assertEqual(self.action(), "READY_FOR_NEXT_STEP")
        self.assertEqual(self.counter.read_text(), "xx")

    def test_busy_store_blocks_read_and_refresh_without_execution(self):
        self.refresh()
        (self.state / ".lock").write_text("another process", encoding="utf-8")
        for operation in (self.action, self.refresh):
            with self.subTest(operation=operation), self.assertRaises(FileExistsError):
                operation()
        self.assertEqual(self.counter.read_text(), "x")
        self.assertEqual((self.state / ".lock").read_text(), "another process")

    def test_record_changes_and_missing_record_do_not_fallback(self):
        self.refresh()
        pointer = json.loads((self.state / "current.json").read_text())
        record = self.state / pointer["record"]
        record.write_bytes(record.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "changed after selection"):
            self.action()
        record.unlink()
        with self.assertRaises(FileNotFoundError):
            self.action()

    def test_bad_pointer_schema_path_and_repository_are_rejected(self):
        self.refresh()
        path = self.state / "current.json"
        original = json.loads(path.read_text())
        for updates in ({"state_schema_version": True}, {"state_schema_version": 2},
                        {"record": "../outside.json"}, {"repo": "other"}, {"sha256": "bad"}):
            path.write_text(json.dumps({**original, **updates}), encoding="utf-8")
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                self.action()
        self.assertEqual(self.counter.read_text(), "x")

    def test_reuse_for_different_repo_preserves_selection(self):
        self.refresh()
        before = (self.state / "current.json").read_bytes()
        with patch("phoenix_continuity_gate.managed.repository_root", return_value=self.base / "different"):
            with self.assertRaisesRegex(ValueError, "repository mismatch"):
                self.refresh()
        self.assertEqual((self.state / "current.json").read_bytes(), before)
        self.assertEqual(self.counter.read_text(), "x")

    def test_state_inside_repo_and_missing_selection_stop(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            refresh_current(self.repo, self.repo / "state", [sys.executable, "-c", "pass"])
        self.assertFalse((self.repo / "state").exists())
        with self.assertRaises(FileNotFoundError):
            self.action()
        self.assertFalse(self.state.exists())

    def test_failed_pointer_publication_does_not_retain_old_success(self):
        self.refresh()
        from phoenix_continuity_gate.managed import _write_pointer

        def fail_complete(state, pointer):
            if pointer["status"] == "COMPLETE":
                raise OSError("simulated publication failure")
            _write_pointer(state, pointer)

        with patch("phoenix_continuity_gate.managed._write_pointer", side_effect=fail_complete):
            with self.assertRaises(OSError):
                self.refresh()
        with self.assertRaisesRegex(ValueError, "did not complete"):
            self.action()
        self.assertEqual(self.counter.read_text(), "xx")
        self.assertEqual(len(list(self.state.glob("run-*.json"))), 2)

    def test_cli_status_missing_state_emits_stop_json(self):
        result = subprocess.run([sys.executable, "-B", "-m", "phoenix_continuity_gate.managed",
                                 "status", "--repo", str(self.repo), "--state", str(self.state)],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["decision"]["action"], "INSPECTION_ERROR")
        self.assertEqual(result.stderr, "")

    def test_cli_refresh_then_status_with_normal_option_order(self):
        command = [sys.executable, "-B", "-m", "phoenix_continuity_gate.managed"]
        options = ["--repo", str(self.repo), "--state", str(self.state)]
        refresh = subprocess.run([*command, "refresh", *options, "--", sys.executable, "-B", "-c", "pass"],
                                 capture_output=True, text=True, timeout=30)
        status = subprocess.run([*command, "status", *options], capture_output=True, text=True, timeout=30)
        for result in (refresh, status):
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(json.loads(result.stdout)["decision"]["action"], "READY_FOR_NEXT_STEP")
            self.assertEqual(result.stderr, "")
