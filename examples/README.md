# Example: consult evidence before resuming a task

This example uses the installed development package and its `inspect --json`
interface. It prints a decision; it does not start an agent, rerun a stored test,
merge, deploy or modify the target project. It is not an integration with a named
third-party agent framework.

From a current source checkout, using a Python 3.11+ virtual environment:

```text
python -m pip install .
python examples/resume_task.py --repo "C:\path\to\your\repo" --record "C:\path\to\records\run-001.json"
```

Use the interpreter from the environment in which Phoenix was installed. The
example invokes that same interpreter with `-I -m phoenix_continuity_gate` so
the installation, rather than the checkout's import path, is exercised. You may
copy the example script into another directory after installation.

| Inspector observation | Example action | What a workflow owner must decide |
| --- | --- | --- |
| Successful command, stable matching snapshot, PASS | `READY_FOR_NEXT_STEP` | Enter a separately defined next step. This is not merge or deployment permission. |
| Old successful record, changed snapshot, BLOCK | `NEEDS_FRESH_EVIDENCE` | Choose an appropriate check and explicitly create a new record if needed. |
| Recorded command failed, even if its snapshot is now stale | `REVIEW_RECORDED_FAILURE` | Examine the historical failure. It does not prove current code fails. |
| Unknown or unstable snapshot, incomplete execution, or a REVIEW verdict | `HUMAN_REVIEW` | Read the inspector's findings and resolve the uncertainty. |
| Missing record, unknown report schema, or inconsistent exit code and report | `INSPECTION_ERROR` | Fix the invocation or evidence problem before resuming. |

The output is one JSON object, with `decision_schema_version: 1`, an `action`, a
`reason`, and `evidence_current_and_successful`. The last field is true only for
`READY_FOR_NEXT_STEP`. The exit code remains the inspector's 0, 1 or 2 for valid
reports; malformed responses and invocation failures exit 2. Argument syntax
errors use argparse's ordinary stderr output.

The policy lives in `phoenix_continuity_gate/resume.py` and can be imported by a
Python workflow. It rejects contradictory states and unknown schemas. It does
not authenticate local editable records, inspect test coverage or validate the
workflow's eventual next operation. Run `phoenix-gate inspect ... --json` directly
to see the complete findings and scope behind a decision.

Developer verification: `python -I scripts/check-installed.py` runs the example
from an unrelated directory against disposable fresh, stale, failed, unstable and missing
record cases. This is internal testing, not external user validation.
