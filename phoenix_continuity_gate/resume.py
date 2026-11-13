"""A conservative example policy for consuming version-1 inspection reports.

Decisions describe evidence handling only. No task, test or external operation is
executed, and no decision grants permission to merge or deploy.
"""


def plan_from_report(report, exit_code):
    def decision(action, reason):
        return {"decision_schema_version": 1, "action": action, "reason": reason,
                "evidence_current_and_successful": action == "READY_FOR_NEXT_STEP"}

    def invalid(reason):
        return decision("INSPECTION_ERROR", reason)

    if (not isinstance(report, dict) or type(report.get("report_schema_version")) is not int
            or report["report_schema_version"] != 1):
        return invalid("Missing or unsupported inspection report schema.")
    verdict = report.get("verdict")
    status = report.get("assessment_status")
    execution = report.get("execution")
    freshness = report.get("freshness")
    if (verdict not in ("PASS", "REVIEW", "BLOCK") or type(exit_code) is not int
            or exit_code != {"PASS": 0, "REVIEW": 1, "BLOCK": 2}[verdict]):
        return invalid("Inspection verdict and process exit code are missing or inconsistent.")
    if (not isinstance(report.get("findings"), list)
            or not all(isinstance(item, str) for item in report["findings"])
            or not isinstance(report.get("scope"), str)):
        return invalid("Inspection report is missing its findings or scope.")
    if status == "ERROR":
        error = report.get("error")
        if (verdict != "BLOCK" or execution != "UNKNOWN" or freshness != "UNKNOWN"
                or not isinstance(error, dict) or error.get("code") != "CANNOT_ASSESS"
                or not isinstance(error.get("message"), str)):
            return invalid("Malformed inspection error report.")
        return invalid("Inspection could not assess the record; resolve that error first.")
    if status != "ASSESSED" or report.get("error", "missing") is not None:
        return invalid("Inspection did not produce a completed assessment.")
    if (execution not in ("SUCCEEDED", "FAILED", "TIMED_OUT", "START_FAILED", "INTERRUPTED")
            or freshness not in ("MATCH", "CHANGED", "UNSTABLE_DURING_RUN", "UNKNOWN")):
        return invalid("Unknown execution or freshness state.")
    if execution != "SUCCEEDED":
        if verdict != "BLOCK":
            return invalid("An unsuccessful execution cannot produce PASS or REVIEW.")
        if execution == "FAILED":
            return decision("REVIEW_RECORDED_FAILURE", "The recorded command failed. Examine that result; it does not establish that current code fails.")
        return decision("HUMAN_REVIEW", "The recorded execution timed out, could not start, or was interrupted. Confirm what completed before choosing another action.")
    if freshness == "CHANGED":
        if verdict != "BLOCK":
            return invalid("Changed evidence must be blocked.")
        return decision("NEEDS_FRESH_EVIDENCE", "Old successful evidence is stale. Choose and explicitly run an appropriate check to obtain a new record.")
    if freshness in ("UNKNOWN", "UNSTABLE_DURING_RUN"):
        if verdict != "REVIEW":
            return invalid("Unknown or unstable evidence requires review.")
        return decision("HUMAN_REVIEW", "Evidence cannot be bound to a stable current snapshot.")
    if verdict == "REVIEW":
        return decision("HUMAN_REVIEW", "The inspector requests review despite matching snapshots. Read its findings before proceeding.")
    if verdict != "PASS":
        return invalid("A matching successful record has an unexpected verdict.")
    return decision("READY_FOR_NEXT_STEP", "This limited evidence check passed. Continue only to the workflow's separately defined next step; no operation has been authorized or executed here.")
