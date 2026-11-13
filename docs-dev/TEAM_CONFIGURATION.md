# Configured team checks (1.0 candidate)

This is a local single-machine tool, not a shared cloud service. It maintains
separate evidence for named checks and verifies each check's definition before
accepting a selected result. It never discovers or executes commands from a record.

Create a reviewed, committed `phoenix.toml` inside the target Git repository:

```toml
config_schema_version = 1
project = "my-project"

[checks.unit]
command = ["{python}", "-B", "-m", "unittest", "discover", "-s", "tests", "-v"]
timeout_seconds = 120
scope = "tracked-repository"

[checks.lint]
command = ["my-installed-linter", "src"]
timeout_seconds = 60
scope = "tracked-repository"
```

Replace these commands with the project's existing trusted checks. Configuration
is executable intent: review it like code. `refresh` executes it with the current
user's permissions and inherited environment, without a sandbox. Do not use
production credentials, unknown commands or privileges just for a trial.

## Operations

```text
phoenix-gate team validate --config /path/to/project/phoenix.toml
phoenix-gate team refresh --config /path/to/project/phoenix.toml --state /private/phoenix-state --check unit
phoenix-gate team status --config /path/to/project/phoenix.toml --state /private/phoenix-state --check unit
phoenix-gate team status --config /path/to/project/phoenix.toml --state /private/phoenix-state
```

On Windows, quote paths and use an outside state path such as
`"C:\private\phoenix-state"`. Use the installed virtual environment's full
`phoenix-gate.exe` path if it is not on PATH. `validate` parses the configuration
and locates the repository; it does not run check commands. `status` assesses
one or all configured checks and never runs their commands. `refresh` requires
one explicit check; there is no refresh-all or automatic retry operation.

The config and target must be in a committed, clean repository before recording.
Do not commit or delete unrelated work to satisfy this requirement. Failed checks,
timeouts and unstable snapshots retain their existing separate outcomes.

## Definition and isolation

Only config schema 1 is accepted. Unknown keys are errors, not silently ignored.
Project/check IDs match `[a-z][a-z0-9_-]{0,63}`. Each check requires an explicit
argv list, a finite `timeout_seconds` in `(0, 86400]`, and `scope = "tracked-repository"`.
The only expansion is the exact first argv token `{python}`, replaced by the
Phoenix interpreter. There is no shell, variable or executable-path expansion.
Use an explicit different interpreter path if the target needs another environment.

State is separated by project ID, repository-location hash and check ID, outside
the target repository. The selected record also binds the absolute config path,
project/check identity, resolved argv, timeout and scope. A command or timeout
change cannot inherit an old success. Review it and explicitly refresh that check.
Moving a repository/config or switching Phoenix interpreters can require new
evidence. Other checks still assess the whole repository; config-file edits may
therefore stale them too. Scope does not perform dependency analysis or infer
which tests may be skipped.

An unconfigured `managed` call cannot read or overwrite configured-check state.
The tool checks the stored command against the current definition as well as the
record checksum. These are accidental-mismatch checks, not authenticated attestations.
Anyone able to edit both records and pointers can forge evidence. Ignored files,
environment, credentials, dependency installation and test adequacy are unverified.

## Recovery and local coordination

Each check has a short-lived exclusive `.lock`. Operations on an occupied check
fail immediately. Before a refresh executes anything its pointer becomes PENDING;
failure to record/publish the result cannot silently retain an earlier success.
An explicit refresh after review is required. Failed attempts become current too.

After a killed process, confirm the owner and any child commands have actually
stopped before manually removing only its lock. The recorded PID is a hint, not
proof that a process is the original owner. Do not automatically delete locks,
assume age proves staleness, or blindly rerun a command with external effects.
The tests cover a real child exit during pointer update; they do not guarantee
termination of every possible detached background process or recovery after any
hardware/power failure. See the existing [state details](../examples/MANAGED_WORKFLOW.md).

Do not share one state tree between machines or concurrent checkouts. Git files
are not locked. Another writer can edit files after a check and before the next
step. Status temporarily writes a coordination lock but does not modify the
target or record. Records contain command arguments, logs and local paths: keep
state private and do not upload it as an artifact by default.

## Result contract

`team_schema_version: 1` wraps a project, operation, overall verdict and per-check
results. The overall exit is 0 only when every selected check passes, 1 when
review is required and none block, or 2 when any check blocks or input/state fails.
Individual results keep the existing `workflow_schema_version: 1`, assessment and
decision. Missing records do not disappear from aggregate status; they block it.
See [API_CONTRACT.md](API_CONTRACT.md). No result authorizes merge/deploy.

中文：先把要运行的检查写进并审查配置，再明确执行一个命名检查。之后状态查询
只核验，不重跑。改命令、超时或解释器会使绑定不符，不能沿用旧通过记录；不同
检查分别存储。它是本地协调，不是跨机器共享证据或防伪系统。
