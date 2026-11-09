"""The public demo must exercise the same Gate as normal checks."""

import unittest

from phoenix_continuity_gate.demo import run_demo


class DemoTests(unittest.TestCase):
    def test_one_demo_shows_fresh_then_stale_handoff(self) -> None:
        result = run_demo()
        self.assertNotEqual(result["first_head"], result["second_head"])
        self.assertEqual(result["before_verdict"], "PASS")
        self.assertEqual(result["after_verdict"], "BLOCK")
        self.assertTrue(
            any("differs from current HEAD" in finding for finding in result["after_findings"])
        )


if __name__ == "__main__":
    unittest.main()
