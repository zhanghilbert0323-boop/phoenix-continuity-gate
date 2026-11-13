"""The example resume policy must preserve distinctions and reject contradictions."""

import unittest

from phoenix_continuity_gate.resume import plan_from_report


def report(execution="SUCCEEDED", freshness="MATCH", verdict="PASS", **extra):
    return {"report_schema_version": 1, "assessment_status": "ASSESSED",
            "execution": execution, "freshness": freshness, "verdict": verdict,
            "findings": [], "scope": "test fixture", "error": None, **extra}


class ResumePolicyTests(unittest.TestCase):
    def test_only_successful_matching_evidence_is_ready(self):
        plan = plan_from_report(report(), 0)
        self.assertEqual(plan["action"], "READY_FOR_NEXT_STEP")
        self.assertTrue(plan["evidence_current_and_successful"])

    def test_stale_success_needs_new_evidence(self):
        plan = plan_from_report(report(freshness="CHANGED", verdict="BLOCK"), 2)
        self.assertEqual(plan["action"], "NEEDS_FRESH_EVIDENCE")
        self.assertFalse(plan["evidence_current_and_successful"])

    def test_failure_is_not_relabelled_as_stale_success(self):
        for freshness in ("MATCH", "CHANGED", "UNKNOWN"):
            with self.subTest(freshness=freshness):
                plan = plan_from_report(report(execution="FAILED", freshness=freshness, verdict="BLOCK"), 2)
                self.assertEqual(plan["action"], "REVIEW_RECORDED_FAILURE")
                self.assertFalse(plan["evidence_current_and_successful"])

    def test_incomplete_execution_and_review_require_a_person(self):
        cases = [(report(execution=status, verdict="BLOCK"), 2) for status in ("TIMED_OUT", "START_FAILED", "INTERRUPTED")]
        cases += [(report(freshness=freshness, verdict="REVIEW"), 1) for freshness in ("MATCH", "UNKNOWN", "UNSTABLE_DURING_RUN")]
        for value, code in cases:
            with self.subTest(value=value):
                self.assertEqual(plan_from_report(value, code)["action"], "HUMAN_REVIEW")

    def test_errors_and_malformed_or_unknown_reports_stop(self):
        cases = [None, [], {}, report(report_schema_version=2), report(report_schema_version=True),
                 report(assessment_status="PENDING"), report(error={"code": "unexpected"}),
                 report(findings="not a list"), report(scope=None), report(execution="invented"),
                 report(freshness="invented")]
        error = report(execution="UNKNOWN", freshness="UNKNOWN", verdict="BLOCK",
                       assessment_status="ERROR", error={"code": "CANNOT_ASSESS", "message": "missing record"})
        cases.append(error)
        for value in cases:
            with self.subTest(value=value):
                plan = plan_from_report(value, 2 if value is error else 0)
                self.assertEqual(plan["action"], "INSPECTION_ERROR")
                self.assertFalse(plan["evidence_current_and_successful"])

    def test_exit_codes_and_verdict_state_contradictions_stop(self):
        cases = [(report(), 2), (report(), True), (report(execution="FAILED"), 0),
                 (report(freshness="CHANGED"), 0), (report(freshness="UNKNOWN"), 0),
                 (report(verdict="BLOCK"), 2), (report(freshness="CHANGED", verdict="REVIEW"), 1)]
        for value, code in cases:
            with self.subTest(value=value, code=code):
                self.assertEqual(plan_from_report(value, code)["action"], "INSPECTION_ERROR")
