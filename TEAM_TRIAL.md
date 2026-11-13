# First team trial / 第一轮团队试用

This is the fixed dev1 guide. The current configured-check candidate starts at
[V1_CANDIDATE.md](V1_CANDIDATE.md). Keep reporting the actual version you tried.

Fixed version: **0.2.3.dev1**. This is an experimental local developer tool, not a
production safety system or a hosted service. No account, API key, telemetry or
source upload is required. Python 3.11+ and Git must already be available.

## What we want to learn

When an AI coding task resumes, does checking whether its last successful command
still matches the repository help someone decide what to do next? Or does the
team's existing Git/CI/agent workflow already handle this adequately?

Internal tests and controlled demos exist. Independent team value and willingness
to pay have **not** been established. Completing the demo alone is not success.

## A bounded first session

Set a small time budget, for example 15 minutes. This is a suggested limit, not a
promise of setup time. If prerequisites are missing or instructions are confusing,
stop and report that obstacle. No purchase or security-setting change is needed.

1. Download the wheel from the [fixed dev1 release](https://github.com/zhanghilbert0323-boop/phoenix-continuity-gate/releases/tag/v0.2.3-dev1).
   Use [DEV_PREVIEW.md](DEV_PREVIEW.md) to install it in a fresh virtual environment.
   The ZIP includes these instructions and source; it is not a standalone app.
2. Run the installed `phoenix-gate --version`. It must report `0.2.3.dev1`.
   Then run `phoenix-gate demo-record`. Use full virtual-environment executable
   paths if it is not activated; both platform variants are in the install guide.
3. Explain the second demo step in your own words: the *old* command succeeded,
   but its evidence no longer matches. No new failing test ran at that step.
4. If there is time and an appropriate authorized project, try the selected-record
   workflow below. Otherwise report demo/setup feedback without claiming real use.

## One real workflow (optional)

Use a small non-critical Git project you own or are authorized to test, with a
clean committed working tree and no submodules. Do not delete, commit or stash
unrelated work just to satisfy this trial. Use the project's existing trusted
check command; tests themselves may modify files, use credentials or contact
services. Do not run an unfamiliar command or point this trial at production.

Follow [examples/MANAGED_WORKFLOW.md](examples/MANAGED_WORKFLOW.md):

1. Choose a private state directory **outside** the project, dedicated to this
   repository and check definition. Explicitly `refresh` once with its test command.
2. Call `status` without changing the code. The current result should match the
   actual recorded outcome. Repeating status must not rerun the test command.
3. After a normal development change, call `status` again. Record whether the
   stale warning helped or merely repeated information you already had. There is
   no need to inject a bug, change production or manufacture a success story.
4. If you independently decide a new check is appropriate, explicitly `refresh`
   again. The new attempt becomes current, including failures and timeouts.
5. Stop on errors, lock contention or PENDING state; follow the example's recovery
   guidance. Do not add an automatic retry loop to make the trial finish.

READY only describes limited evidence. It does not authorize merge/deploy or prove
that the test suite is sufficient. Whole-repository changes, including docs, can
invalidate a record. Environment/ignored-file changes are outside current checks.
Local JSON and its checksum are editable, not authenticated proof.

## Feedback: one concrete observation is enough

Use the [existing issue form](https://github.com/zhanghilbert0323-boop/phoenix-continuity-gate/issues/new?template=trial-feedback.md)
or reply privately to the person who invited you. No upload is required.

```text
Version / OS / Python / Git:
Setup failed, demo only, or real authorized workflow:
Where I needed help:
How we currently handle old test results:
One actual change and the observed Phoenix decision (redacted):
Did it change my next action, or duplicate existing tools?
Would I use it again? What blocks that?
```

Do not post full records, private source, customer data, credentials, command
arguments or unreviewed logs. Public errors may expose local paths; redact them.
If the tool adds no value or causes needless blocking, that is useful feedback.

## A separate conversation about paid work

A paid pilot would require an identified buyer, one specific workflow, a separately
agreed scope and acceptance criteria. We are not selling guaranteed safety, fixed
time savings, a third-party framework integration or a production SLA. A download,
star, friendly reply or demo completion is not a paid customer.

## 中文速览

先安装固定的 dev1 版本，在独立环境跑演示；有余力再用自己的非关键项目试一次
`refresh → status → 正常改动 → status → 明确刷新`。没有现成 Python/Git、
说明看不懂、现有工具已经够用，都可以直接反馈并停止。第一轮只验证能否独立
使用、结果是否清楚、是否对真实决策有帮助，不要求购买或上传项目。

给潜在试用者的简短介绍（草稿，不会自动发送）：

> 我们做了一个实验性本地工具 Phoenix Continuity Gate，用来检查 AI 编码任务
> 恢复时，之前的命令执行结果是否仍对应当前代码。已有固定开发预览，想请正在
> 使用编码代理的开发者在非关键项目里试一下。它不自动重跑测试，不上传源码。
> 反馈“现有工具已经解决了”也很有价值。你是否遇到过这类证据过时的问题？
