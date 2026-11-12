# Independent trial: does Phoenix add anything to your workflow?

This is an experimental local tool, not a production safety system. Completing
the demo is not evidence of customer demand. Negative results are useful.

## Choose the version first

- [v0.2.2 preview ZIP](https://github.com/zhanghilbert0323-boop/phoenix-continuity-gate/releases/download/v0.2.2-preview/phoenix-continuity-gate-v0.2.2-preview.zip):
  fixed downloadable version with the Windows launcher, changed-path explanations
  and this guide.
- Older v0.2.1 ZIPs do **not** include changed-path explanations. Keep reporting
  the version you actually tried; there is no need to repeat completed feedback.
- If using a `main` Git checkout, report `git rev-parse HEAD` so we can identify it.

Requirements: Python 3.11+ and Git. No account, API key or cloud upload is needed.
Do not install dependencies or disable security settings just to complete a trial
if you are uncomfortable doing so; report the startup obstacle instead.

## Trial A: disposable demo

Extract the entire ZIP. On Windows, double-click `START_DEMO.cmd` in the extracted
folder. Alternatively, open a terminal in the folder containing this README and run:

```text
python -B -m phoenix_continuity_gate demo-record
```

The command creates and removes a temporary sample repository, executes its
small test suite and shows these four expected states:

| Step | Execution | Freshness | Gate | Meaning |
| --- | --- | --- | --- | --- |
| 1 | SUCCEEDED | MATCH | PASS | Recorded success matches the sample snapshot. |
| 2 | SUCCEEDED | CHANGED | BLOCK | The OLD successful run no longer covers the snapshot. No new test ran at this step. |
| 3 | FAILED | MATCH | BLOCK | A new run actually failed on the changed sample. |
| 4 | SUCCEEDED | MATCH | PASS | Repair and a fresh run restore a matching success record. |

If startup fails, stop and send the redacted error. Do not repeatedly retry
commands you do not understand. We want to learn whether setup works unaided.

## Trial B: one normal change in your own project (optional)

Use only a small project you own or are explicitly authorized to test. It must
have a clean committed Git working tree and no submodules. Do not delete or
commit unrelated work to satisfy this prerequisite.

1. Identify the project's existing trusted test command. Phoenix executes it;
   tests may write files or contact services. Do not copy an unfamiliar command.
2. From the Phoenix folder, use `record` as documented in the
   [README](README.md#record-and-inspect-a-command-on-your-own-repository).
   Replace all example paths and the example test command. Choose a new output
   filename in an existing directory **outside** the target repository.
3. Use `inspect` against that record. It reads state; it does not run the stored
   command. A PASS means only that the reported successful exit and snapshots match.
4. After your next ordinary development change, inspect the same old record.
   Did it identify something you would otherwise have missed? Or just repeat
   what Git or CI already told you? Do not manufacture a bug for this trial.
5. When you actually need a new test result, explicitly run `record` again with
   a new filename. Preserve the old record. Report whether this added friction.

A documentation-only change can also invalidate a record. BLOCK does not mean
the new code is broken or that every test needs rerunning. Changed-path output
does not infer test dependencies or authorize skipping tests. Ignored files,
environment changes and test quality are outside the preview's checks. Local
records are editable, not authenticated evidence.

## Send a small observation, not your project

Use the [trial issue form](https://github.com/zhanghilbert0323-boop/phoenix-continuity-gate/issues/new?template=trial-feedback.md)
or reply where the maintainer invited you. This short format is enough:

```text
Version / commit:
OS + Python + Git:
Demo only, real project, or could not start:
Needed help at:
Expected / observed (redacted):
My existing way to handle stale test results:
What Phoenix changed about my next action, if anything:
Would I use it again? Why / why not?
```

Do not attach complete execution JSON, private source, customer information,
credentials or sensitive command arguments. Logs can contain secrets; manually
review and redact any excerpt before posting. No upload is required to use Phoenix.

## What happens after feedback?

- Startup failure: fix setup before expanding functionality.
- Confusing output: improve the explanation before adding integrations.
- Existing Git/CI workflow already suffices: record that result, not a success story.
- Concrete benefit in an authorized workflow: investigate frequency, missed cases
  and integration effort before proposing more work.
- A paid pilot requires a separately agreed scope, acceptance criteria and a
  buyer with payment authority. A star, demo run or friendly reply is not a sale.
