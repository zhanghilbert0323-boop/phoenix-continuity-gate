"""The public execution demo must exercise real tests and recovery."""

import unittest

from phoenix_continuity_gate.evidence_demo import run_evidence_demo


class EvidenceDemoTests(unittest.TestCase):
    def test_real_tests_cover_pass_stale_fail_and_repair(self):
        steps = run_evidence_demo()
        actual = [(s["assessment"]["execution"], s["assessment"]["freshness"],
                   s["assessment"]["verdict"]) for s in steps]
        self.assertEqual(actual, [("SUCCEEDED", "MATCH", "PASS"),
                                  ("SUCCEEDED", "CHANGED", "BLOCK"),
                                  ("FAILED", "MATCH", "BLOCK"),
                                  ("SUCCEEDED", "MATCH", "PASS")])
        self.assertIn("Ran 1 test", steps[0]["record"]["execution"]["stderr"]["text"])
        self.assertIn("AssertionError", steps[2]["record"]["execution"]["stderr"]["text"])
        self.assertNotEqual(steps[0]["record"]["id"], steps[3]["record"]["id"])


if __name__ == "__main__":
    unittest.main()
