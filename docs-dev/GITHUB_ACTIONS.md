# Same-job GitHub Actions integration

The root `action.yml` is a composite action. It uses an already installed Python
3.11+ / Phoenix package and Git; it does not install anything itself. It is not
published to Marketplace, not a hosted service, and not a cross-run CI attestation
system. The adapter does not grant merge/deploy permission.

Start with the [reviewable workflow example](../examples/github-actions/phoenix-evidence.yml).
The target project and fixed Phoenix source are checked out into **sibling Git
repositories**, not one inside the other. Otherwise tool installation/untracked
files could dirty the target snapshot. Source installation may download build
dependencies; alternatively install the matching verified wheel offline first.
Use the same Python environment for installation and the action invocation.

Review the consumer's config and test prerequisites before enabling `refresh`.
The candidate tag is a fixed release; replace it with the release's full tested
commit SHA for a production pin. Do not track an automatically moving `main`.

| Input | Meaning |
| --- | --- |
| `config` | Required path to a reviewed config inside the target Git repository |
| `check` | Required existing check ID; one check per invocation |
| `mode` | `status` by default; `refresh` explicitly executes the configured command once |
| `state` | Optional private outside state root; defaults to `RUNNER_TEMP/phoenix-team-state` |

Inputs are passed as environment variables into a constant Python invocation,
not substituted into shell source. Runtime validation rejects missing inputs or
unknown modes. Configured commands still execute arbitrary reviewed code with
runner permissions; this is not a sandbox or a defense against malicious tests.
Use read-only minimum permissions, no unnecessary secrets and no privileged
`pull_request_target` workflow for untrusted code. Do not upload raw records as
artifacts or restore evidence caches from untrusted branches.

The adapter exports controlled `verdict` and `decision` outputs and writes a short
job summary. It exits with the gate's code: 0 PASS, 1 REVIEW, 2 BLOCK/error. REVIEW
also stops a normal step. Structured stdout contains findings, not raw command
logs/argv; findings and errors can contain paths. Check log visibility before use.
If writing outputs fails after refresh, review the completed attempt instead of
blindly retrying. A caller can explicitly choose a risky workflow policy such as
`continue-on-error`; Phoenix cannot prevent that override. Do not use it for a
real blocking gate. Our own negative-control CI uses it only to assert that a
deliberately stale disposable fixture actually fails.

## State lifetime and limits

The refresh and status steps operate in one job on one unchanged repository
location. The state is ephemeral with that runner. Nothing restores a prior job's
success, remote CI logs, another machine's receipt or a downloaded artifact.
Absolute path and interpreter binding are deliberate. After an edit, explicitly
review whether a new check is needed; the action never refreshes automatically.

The project's Tests workflow runs the actual composite action on Windows and
Ubuntu with Python 3.11/3.14: create a disposable committed fixture, refresh once,
inspect PASS, make a normal edit, then assert status fails with
NEEDS_FRESH_EVIDENCE. Those hosted results validate our fixture integration, not
an independent customer's deployment. See the matching candidate commit's CI.

中文：这是同一个 job 内的接入，不是从上次 CI 恢复测试凭证。默认只检查；
`mode: refresh` 才明确执行一次。目标仓库与工具仓库并排放置，状态在 runner
临时目录。遇到失败会停止，不自动修复或重试，也不代表已经允许合并/部署。
