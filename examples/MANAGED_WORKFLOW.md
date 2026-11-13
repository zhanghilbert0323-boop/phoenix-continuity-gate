# One workflow, one selected record / 自动维护当前证据的接入示例

This example is included in 0.2.3.dev1. The older 0.2.3.dev0 release artifacts do
**not** contain it. Install the dev1 wheel using [DEV_PREVIEW.md](../DEV_PREVIEW.md),
or install a current checkout into a Python 3.11+ virtual environment with
`python -m pip install .`.
It has no additional runtime dependencies, account or API requirement.

## Two explicit operations

- `refresh`: run exactly one command supplied by the caller, save a uniquely
  named record, and select that attempt as current. Failed or timed-out attempts
  become current too; the example never falls back to an earlier success.
- `status`: read the selected record and inspect the current repository. It does
  not execute stored commands, refresh evidence, start an agent or retry anything.

Choose a **private state directory outside the target repository**, dedicated to
one workflow/check definition. Do not share it between different tests or tasks.
The example does not infer which check is sufficient. If you change the intended
check, choose a separate state directory and explicitly refresh it first.

For example, after replacing the paths and selecting an appropriate command:

```text
python -m phoenix_continuity_gate.managed refresh --repo "C:\work\my-project" --state "C:\work\private-evidence\my-project-unittest" -- python -B -m unittest discover -s tests -v
python -m phoenix_continuity_gate.managed status --repo "C:\work\my-project" --state "C:\work\private-evidence\my-project-unittest"
```

The target must be a committed, clean Git repository before recording. `python`
after `--` is the executable explicitly chosen for the target project; use that
project's full interpreter path if it needs a different environment. The example
runs argv directly, not through a shell. It never obtains commands from a record.

Repeat `status` after resuming work. After a change makes evidence stale, review
the change, choose the appropriate check, then explicitly call `refresh` again.
There is no automatic `status -> refresh` loop. No example command merges,
deploys or starts a subsequent task.

## Consume the result

Each valid invocation prints one JSON object:

```json
{
  "workflow_schema_version": 1,
  "assessment": {"report_schema_version": 1, "assessment_status": "ASSESSED", "...": "full inspection report"},
  "decision": {"decision_schema_version": 1, "action": "READY_FOR_NEXT_STEP", "reason": "...", "evidence_current_and_successful": true}
}
```

This is an abbreviated illustration, not literal output. Actions and verdicts
use the [same policy as the record-based example](README.md). Exit codes remain
0 (PASS), 1 (REVIEW), or 2 (BLOCK/invocation or state error). On a state error,
`assessment` is null, `decision.action` is `INSPECTION_ERROR`, and `error` describes
the problem. Argument syntax errors use ordinary argparse stderr, not JSON.
Consumers must check the exit code, schema, assessment and decision together;
unknown output must stop the workflow. READY is not permission to merge/deploy.

Python callers can use `refresh_current(repo, state, argv, timeout=60)` and
`inspect_current(repo, state)` from `phoenix_continuity_gate.managed`. They return
`(result, exit_code)` and raise errors for invalid state. Neither API starts a
resumed task. Only `refresh_current` executes the explicitly supplied command.

## State and failure handling

The directory contains `current.json`, immutable `run-<uuid>.json` records and a
short-lived `.lock`. The pointer binds a repository path and record SHA-256. It
is updated with a same-directory temporary file and atomic replacement. Old
records are retained; no automatic pruning or latest-by-timestamp search occurs.

Before an explicit refresh starts, the pointer changes to `PENDING`. If recording
or pointer publication fails, subsequent status checks stop instead of consulting
the old successful record. Review the failure and any completed command before
explicitly refreshing again. A rejected recording precondition can also leave
PENDING; it does not mean a command necessarily started.

Operations use exclusive lock creation and fail immediately if another operation
holds the lock. Even `status` needs write access to the private state directory
to create/remove this coordination lock; it does not edit the record or target
repository. Ordinary exceptions release it. A killed process may leave `.lock`;
there is no automatic stale-lock deletion. Confirm the owning operation and any
child processes have stopped before manually removing only that lock. Then review
PENDING and decide whether to explicitly refresh. Do not delete records to hide a
failed run or run two writers against a shared/network state directory.

This is a single-machine example, not a distributed transaction or production
coordinator. Repository files are not locked; a concurrent edit after a check
can invalidate it before the next action. Atomic replacement does not guarantee
durability after every hardware/power failure. A checksum is not authentication:
someone able to edit both files can forge state. Records contain command arguments,
logs and local paths; keep them private. Ignored files, environment, dependency
changes and test coverage retain the inspector's existing limitations.

中文：`refresh` 是你明确要求跑一次检查，并自动把这次结果设为当前证据；
`status` 只读证据并对照当前代码，不会偷偷跑测试。新检查失败或超时也会成为
当前结果，不能退回旧的通过记录。更新中断会停止并要求排查。状态目录必须在
目标仓库之外，一个工作流/检查定义用一个目录。它不是通用代理插件，也不是
客户已经部署的证明；这是可安装、可复现的最小接入示例。
