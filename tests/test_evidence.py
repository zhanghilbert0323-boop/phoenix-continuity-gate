"""Real command runs must not be confused with claims or stale snapshots."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from phoenix_continuity_gate.evidence import assess_record, record_command, LOG_LIMIT


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="phoenix-evidence-test-")
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.repo = self.base / "repo with spaces"
        self.repo.mkdir()
        self.output = self.base / "run.json"
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.name", "Evidence Test")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "commit.gpgSign", "false")
        git(self.repo, "config", "core.hooksPath", str(self.base / "no-hooks"))
        (self.repo / "app.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
        (self.repo / "test_app.py").write_text(
            "import unittest\nfrom app import add\nclass Tests(unittest.TestCase):\n"
            "    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "fixture")

    def run_command(self, code="print('observed')", **kwargs):
        return record_command(self.repo, self.output, [sys.executable, "-B", "-c", code], **kwargs)

    def test_real_unittest_run_and_json_roundtrip(self):
        record = record_command(self.repo, self.output,
                                [sys.executable, "-B", "-m", "unittest", "-v"])
        saved = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(record, saved)
        self.assertIn("Ran 1 test", record["execution"]["stderr"]["text"])
        result = assess_record(saved, self.repo)
        self.assertEqual((result["verdict"], result["execution"], result["freshness"]),
                         ("PASS", "SUCCEEDED", "MATCH"))

    def test_failure_is_recorded_and_blocked(self):
        record = self.run_command("assert 2 + 2 == 5")
        self.assertNotEqual(record["execution"]["exit_code"], 0)
        self.assertIn("AssertionError", record["execution"]["stderr"]["text"])
        self.assertEqual(assess_record(record, self.repo)["verdict"], "BLOCK")

    def test_new_commit_stales_previously_successful_record(self):
        record = self.run_command()
        (self.repo / "app.py").write_text("broken\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "change")
        result = assess_record(record, self.repo)
        self.assertEqual((result["execution"], result["freshness"], result["verdict"]),
                         ("SUCCEEDED", "CHANGED", "BLOCK"))

    def test_changed_bytes_even_when_git_assumes_unchanged(self):
        record = self.run_command()
        git(self.repo, "update-index", "--assume-unchanged", "app.py")
        (self.repo / "app.py").write_text("different contents\n", encoding="utf-8")
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")
        self.assertEqual(assess_record(record, self.repo)["freshness"], "CHANGED")

    def test_successful_command_changing_files_requires_review(self):
        record = self.run_command("from pathlib import Path; Path('app.py').write_text('changed')")
        result = assess_record(record, self.repo)
        self.assertEqual((result["execution"], result["freshness"], result["verdict"]),
                         ("SUCCEEDED", "UNSTABLE_DURING_RUN", "REVIEW"))

    def test_deleted_tracked_file_is_stale(self):
        record = self.run_command()
        (self.repo / "app.py").unlink()
        result = assess_record(record, self.repo)
        self.assertEqual((result["freshness"], result["verdict"]), ("CHANGED", "BLOCK"))

    def test_timeout_is_saved_without_success(self):
        record = self.run_command("import time; time.sleep(30)", timeout=0.1)
        self.assertEqual(record["execution"]["status"], "TIMED_OUT")
        self.assertIsNone(record["execution"]["exit_code"])
        self.assertEqual(assess_record(record, self.repo)["verdict"], "BLOCK")

    def test_missing_executable_is_saved_without_success(self):
        record = record_command(self.repo, self.output, [str(self.base / "missing-program")])
        self.assertEqual(record["execution"]["status"], "START_FAILED")
        self.assertEqual(assess_record(record, self.repo)["verdict"], "BLOCK")

    def test_dirty_repo_is_rejected_before_command_execution(self):
        (self.repo / "untracked.txt").write_text("dirty", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "clean Git"):
            self.run_command("raise RuntimeError('must not run')")
        self.assertFalse(self.output.exists())

    def test_output_inside_repo_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            record_command(self.repo, self.repo / "record.json", [sys.executable, "-c", "pass"])

    def test_existing_record_is_preserved_and_command_not_run(self):
        self.output.write_text("keep this", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            self.run_command("from pathlib import Path; Path('sentinel').touch()")
        self.assertEqual(self.output.read_text(encoding="utf-8"), "keep this")
        self.assertFalse((self.repo / "sentinel").exists())

    def test_inspection_never_executes_stored_command(self):
        record = self.run_command()
        record["command"] = [sys.executable, "-c", "from pathlib import Path; Path('sentinel').touch()"]
        assess_record(record, self.repo)
        self.assertFalse((self.repo / "sentinel").exists())

    def test_contradictory_or_missing_evidence_is_rejected(self):
        record = self.run_command()
        bad = copy.deepcopy(record)
        bad["execution"]["exit_code"] = 1
        with self.assertRaisesRegex(ValueError, "contradicts"):
            assess_record(bad, self.repo)
        with self.assertRaises(ValueError):
            assess_record({"tests": {"status": "passed"}}, self.repo)

    def test_missing_post_snapshot_is_unknown(self):
        record = self.run_command()
        record["snapshot_after"] = None
        record["snapshot_error"] = "simulated observation failure"
        result = assess_record(record, self.repo)
        self.assertEqual((result["freshness"], result["verdict"]), ("UNKNOWN", "REVIEW"))

    def test_log_tail_is_bounded(self):
        record = self.run_command(f"print('x' * {LOG_LIMIT * 2})")
        stdout = record["execution"]["stdout"]
        self.assertTrue(stdout["truncated"])
        self.assertLessEqual(len(stdout["text"]), LOG_LIMIT)

    def test_invalid_timeouts_never_execute(self):
        for timeout in (0, -1, float('inf'), float('nan')):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                self.run_command(timeout=timeout)
        self.assertFalse(self.output.exists())

    def test_cli_roundtrip_stale_record_and_new_record(self):
        project = Path(__file__).resolve().parents[1]

        def cli(*args):
            return subprocess.run([sys.executable, "-m", "phoenix_continuity_gate", *args],
                                  cwd=project, capture_output=True, text=True, timeout=30)

        first = cli("record", "--repo", str(self.repo), "--output", str(self.output),
                    "--", sys.executable, "-B", "-m", "unittest", "-v")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("Execution: SUCCEEDED", first.stdout)
        original_bytes = self.output.read_bytes()
        (self.repo / "README.md").write_text("documentation change", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "docs")
        stale = cli("inspect", "--repo", str(self.repo), "--record", str(self.output))
        self.assertEqual(stale.returncode, 2, stale.stderr)
        self.assertIn("Freshness: CHANGED", stale.stdout)
        next_record = self.base / "next.json"
        fresh = cli("record", "--repo", str(self.repo), "--output", str(next_record),
                    "--", sys.executable, "-B", "-m", "unittest", "-v")
        self.assertEqual(fresh.returncode, 0, fresh.stderr)
        self.assertEqual(self.output.read_bytes(), original_bytes)
        reread = cli("inspect", "--repo", str(self.repo), "--record", str(next_record))
        self.assertEqual(reread.returncode, 0, reread.stderr)
        self.assertIn("Freshness: MATCH", reread.stdout)


if __name__ == "__main__":
    unittest.main()
