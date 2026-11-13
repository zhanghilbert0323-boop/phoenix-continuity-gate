# 1.0 candidate / 1.0 候选版

Package version: **1.0.0rc1**. GitHub tag: **v1.0.0-rc1**. This is a release
candidate, not a claim that a paid team product has passed independent acceptance.
See [V1_READINESS.md](V1_READINESS.md) for remaining evidence gates.

## What is in the candidate?

- Local explicit command records, tracked-repository snapshots and JSON inspection.
- Reviewed TOML configuration, named check isolation, command/timeout/scope binding.
- `team validate`, `team refresh --check NAME` and `team status` without implicit retries.
- A same-job GitHub Actions composite adapter and a reviewable consumer workflow.
- Interface, upgrade/rollback, failure recovery, trial and service-boundary docs.
- MIT-licensed core; integration, customization and time-limited support can be
  separately agreed. The core does not require payment, an account or activation.

Supported candidate target: one local machine/job, Python 3.11+, Git, ordinary
committed clean repositories without submodules. Hosted verification targets
Windows/Ubuntu with Python 3.11/3.14. Consult the fixed commit's actual CI result;
macOS, network-shared state, cross-machine/cross-job receipt reuse and detached
background work are not supported claims. This does not authenticate editable
records, validate test adequacy, observe environment changes or authorize deployment.

## Download/install

[Fixed candidate release](https://github.com/zhanghilbert0323-boop/phoenix-continuity-gate/releases/tag/v1.0.0-rc1)

The ZIP contains source, LICENSE, tests, config, action metadata, examples and docs.
The wheel contains the Python package and license; it requires existing Python
and Git, not a bundled standalone runtime. It has no third-party Python runtime
dependencies. Check download consistency with SHA256SUMS.txt; that is not an
independent signature or trust proof. Prior release attachments are unchanged.

Windows CMD, from a fresh working directory:

```cmd
python -m venv .venv
.venv\Scripts\python.exe -m pip install --no-index --no-deps "C:\downloads\phoenix_continuity_gate-1.0.0rc1-py3-none-any.whl"
.venv\Scripts\phoenix-gate.exe --version
.venv\Scripts\phoenix-gate.exe demo-record
```

Linux (macOS syntax is similar but not a tested platform claim):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --no-index --no-deps /downloads/phoenix_continuity_gate-1.0.0rc1-py3-none-any.whl
.venv/bin/phoenix-gate --version
.venv/bin/phoenix-gate demo-record
```

Do not reuse a previous environment/state root for candidate acceptance. From a
source checkout `python -m pip install .` is also possible; it may download build
dependencies. `python -I scripts/check-installed.py` verifies that installation
from outside the source import path, using disposable sample projects only.

## First real workflow

Use a non-critical authorized project with a trusted existing check. Review and
track a config following [TEAM_CONFIGURATION.md](docs-dev/TEAM_CONFIGURATION.md).
There is a self-use `phoenix.toml` in this repository; do not copy its command
blindly into a different project. Then, with the installed executable:

```text
phoenix-gate team validate --config /your/project/phoenix.toml
phoenix-gate team refresh --config /your/project/phoenix.toml --state /private/phoenix-state-rc1 --check unit
phoenix-gate team status --config /your/project/phoenix.toml --state /private/phoenix-state-rc1
```

The first refresh explicitly executes a reviewed command. Status runs no command.
One failed/missing check blocks aggregate status. After a normal code change,
observe the warning and decide whether another explicit check is warranted.
Never retry automatically just to turn a gate green. No cleanup, reset, commit
or environment weakening is required to finish a trial; stop and report friction.

See [GitHub Actions](docs-dev/GITHUB_ACTIONS.md) for the same-job adapter, and
[API_CONTRACT.md](docs-dev/API_CONTRACT.md) before consuming JSON or upgrading.

## External feedback and commercial boundary

Report version/OS, where help was needed, one redacted real workflow observation,
your existing alternative, and whether Phoenix changed the next action. Do not
send complete records, private code, credentials, customer data or unreviewed logs.
Use the [existing feedback form](https://github.com/zhanghilbert0323-boop/phoenix-continuity-gate/issues/new?template=trial-feedback.md)
or reply privately. Demo completion is not evidence of paid value.

[COMMERCIAL.md](COMMERCIAL.md) explains MIT core versus proposed scoped services.
No fixed price, SLA, buyer or payment is implied by this release. Independent
workflow acceptance and a concrete authorized purchase remain external work.

中文：候选版已把“能跑的核心”推进到命名配置、真实接入和可维护接口。先独立
安装、跑演示，再选择授权的非关键项目验证。1.0rc1 不是正式成熟商用版，不能
把内部测试当作客户验收。MIT 核心免费，接入/定制/限期支持按另行约定交付。
