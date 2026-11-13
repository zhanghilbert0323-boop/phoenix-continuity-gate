# Bounded resume cycle / 有界恢复流程实验

Question: after an old result becomes stale and a caller explicitly selects a
new result, do unchanged resumes stay ready? Do failed and timed-out records
cause any automatic command retries in this example?

Run from a current source checkout:

```text
python -B experiments/resume_cycle.py --output NEW-REPORT.json
```

Omit `--output` to print the full JSON report. A named report must be new; existing
files are refused before the experiment runs. The sample Git repository, commands
and records live in a temporary directory and are removed afterward. The report
does not contain their absolute paths, raw command output or complete records.

## Fixed sequence

1. Run a real one-test unittest sample and save A. Inspect A three times without changes.
2. Commit an equivalent code change. A becomes stale.
3. Explicitly run the check once, save B, and have the caller select B. Inspect B
   four times without changes.
4. Negative control: deliberately select A again. It must still be stale. Phoenix
   does not discover or select the latest record on behalf of the caller.
5. Commit a controlled bug. B becomes stale. Explicitly run the sample again and
   save failed result C. Inspect C twice; do not retry it automatically.
6. Explicitly run a sample command that hangs, with a three-second foreground
   timeout. Save T and inspect it twice; do not retry it automatically.

The plan contains 14 inspections and four explicit command attempts. Three
attempts complete a real unittest run; the timeout attempt pauses before unittest.
An append-only counter outside the sample repo observes command starts. Each
inspection records its before/after counter values, so accidental executions are
visible rather than inferred from a PASS result.

The report also checks that the original record files are preserved, new results
do not overwrite A, observed actions match expectations, and the sample worktree
remains clean. It includes source-file hashes and environment information for
reproduction. See `tests/test_resume_cycle.py` for automated regression checks.

## What this does and does not establish

Observed report: [resume-cycle-001.json](results/resume-cycle-001.json), generated
on Windows with Python 3.14.4 on 2026-11-13. All declared checks passed: 14
inspections, four explicit command starts, zero starts during inspections, and
four ready decisions after the caller switched to B. Three completed unittest
runs were observed; the fourth explicit command timed out before unittest.

This is a controlled experiment of Phoenix's evidence API and example policy.
The caller has an explicit refresh schedule; there is no automatic retry scheduler
or persistent latest-record pointer in this experiment. A real integration must
update its selected record correctly and define its own bounded retry behavior.

It is not a reproduction or fix of another agent's reported stale-status loop,
and it does not measure savings against another agent or an always-rerun baseline.
It cannot substitute for independent workflow or customer validation. Documentation
changes still invalidate whole-repository records, and ignored files, environment
changes and test sufficiency remain outside the preview's checks.

中文：这个实验验证「显式切换到 B 后，不变的代码能够继续使用 B」，也验证继续选旧 A
时仍会拦截。它不会替接入方自动找最新记录；更不能据此宣称修好了其他代理的循环问题。
计数器测量的是这个受控流程实际启动命令的次数，不是客户节省工时。
