# Phoenix Continuity Gate — experimental v0.2.1 preview

This is an early prototype for developer feedback, not a production safety
system. It runs locally and does not require an account or upload project data.

For the product architecture and staged plan, see [ROADMAP.md](ROADMAP.md).
For the first experiment and its limitations, see [EXPERIMENT_LOG.md](EXPERIMENT_LOG.md).

This local prototype checks whether a handoff or an execution record still matches
the repository being resumed. `check` and `inspect` read records and project state.
The new `record` command explicitly executes a command you supply and saves its
observed exit result with tracked-file fingerprints. Executing tests can change
files or have other effects: choose a command you intend to run.

An old handoff's claim alone does not prove tests ran. An execution record is
editable local JSON, not authenticated proof. Neither guarantees code correctness
or the safety of repeating an external operation.

中文入门：[QUICKSTART.zh-CN.md](QUICKSTART.zh-CN.md)。
Independent trial guide / 外部试用与反馈：[TRIAL.zh-CN.md](TRIAL.zh-CN.md).

## The first failure case

Agent A records that tests passed at commit `A`. Someone then commits a change
to produce commit `B`. Agent B must not treat the old test claim as current.
The Gate reports `BLOCK` and explains the mismatch.

## Start here: five-minute demo

You need Python 3.11+ and Git available from a terminal. This version was tested
on Windows with Python 3.14 and Git 2.54; other environments are not yet
verified.

If you received a ZIP file, extract the whole project folder first. On
Windows, you can double-click `START_DEMO.cmd`: it checks installed Python and
Git, runs the temporary demo, then pauses so errors do not disappear. It does not
install dependencies or change global settings. `START_DEMO.cmd --check` checks
prerequisites only; add `--no-pause` for automation. Discovery lists installed
runtimes and probes concrete executables, skipping WindowsApps aliases. An
empty successful command result is not accepted as a working interpreter.

Alternatively, open that folder in File Explorer, type `cmd` in the address bar, and
press Enter. This opens Command Prompt in the right directory. Do not
double-click an individual `.py` file.

From this directory, run:

```cmd
python -m phoenix_continuity_gate demo-record
```

This creates a temporary sample project and really runs a small unittest suite:

1. Working code: `SUCCEEDED / MATCH / PASS`.
2. Changed code, inspect the old record: `SUCCEEDED / CHANGED / BLOCK`.
3. Run tests on the deliberately broken code: `FAILED / MATCH / BLOCK`.
4. Repair the code and make a new record: `SUCCEEDED / MATCH / PASS`.

The second row still says `SUCCEEDED` because it describes the OLD execution,
not the current code. The third row's `MATCH` describes the snapshot, not success.
The sample repository and its records are removed when the demo finishes.

If `python` is not recognized, try `py -m phoenix_continuity_gate demo-record`. If
`git` is not recognized, install Git before retrying. If the terminal says
`No module named phoenix_continuity_gate`, check that you opened Command
Prompt in the extracted project folder, next to this README.

## Record and inspect a command on your own repository

Use a clean, committed Git working tree. Save a new record **outside** that
repository. Existing record files are never overwritten. Replace the example
test command with the command your project actually uses; `--` separates it
from Phoenix's options.

```cmd
python -m phoenix_continuity_gate record --repo "C:\path\to\your\repo" --output "C:\path\to\records\run-001.json" --timeout 60 -- python -B -m unittest discover -s tests -v
python -m phoenix_continuity_gate inspect --repo "C:\path\to\your\repo" --record "C:\path\to\records\run-001.json"
```

`record` runs the supplied executable without implicitly requesting a shell,
with the repository root as its working directory and no interactive stdin.
It saves the command, exit result, timestamps, tracked-file SHA-256 fingerprints
and the last 16 KiB of each output stream. The output can contain private data;
review a record before sharing it.

`inspect` never executes the command stored in JSON. It shows execution outcome
separately from freshness. A clean matching snapshot and a recorded successful
command yield limited `PASS`; stale evidence or an unsuccessful command yields
`BLOCK`; unknown or unstable snapshots yield `REVIEW` when the command succeeded.
Exit codes are `0`, `2` and `1`, respectively. Invalid input also exits `2`.

Limits of the preview:

- A successful exit code does not establish how many tests ran, test quality,
  or code correctness. A command that runs no tests can still exit zero.
- Files ignored by Git, environment/dependency changes, submodule contents and
  background work are not verified. Submodules are currently unsupported.
- Snapshots compare tracked contents at the endpoints. They are not atomic and
  cannot establish that files stayed unchanged for every instant of execution.
  Symbolic links bind the link target text, not the external target's contents.
- Records are local, editable and associated with their original repository
  location. They do not resist a person fabricating or modifying the JSON.
- Timeout and interruption attempt to terminate the process group/tree. Escaped
  or detached background processes are outside the completion guarantee.

## Original v0.1 demo: claims only

```cmd
python -m phoenix_continuity_gate demo
```

This original demo shows `PASS` then `BLOCK` for recorded Git consistency.
It does not run tests. The new execution demo above is a separate command.

## Inspect an old handoff (claims only)

Create a JSON file outside your repository (or commit it before running):

```json
{
  "schema_version": 1,
  "repo_head": "PASTE_THE_FULL_GIT_COMMIT_HASH_HERE",
  "tests": {
    "status": "passed",
    "git_head": "PASTE_THE_SAME_FULL_GIT_COMMIT_HASH_HERE"
  }
}
```

Then run from this project's directory:

```powershell
python -m phoenix_continuity_gate check --repo C:\path\to\your\repo --handoff C:\path\to\handoff.json
python -m unittest discover -s tests -v
```

Get a repository's current hash with `git rev-parse HEAD`. If you commit a new
change without updating the handoff, the next check should report `BLOCK`.

Exit codes: `0` = recorded evidence is consistent; `1` = human review needed;
`2` = blocked or invalid input. A `PASS` means only that these limited checks
passed. It is **not** permission to deploy, merge, pay, or repeat an external
operation.

## Scope of the original handoff check

- Checks the handoff commit against current `HEAD`.
- Rejects a recorded failed test or a passed test tied to another commit.
- Flags uncommitted or untracked files for human review.
- Does not run commands from a handoff or contact a server.

Next validation: show this case to developers who have actually resumed an
interrupted agent task. Ask whether this catches a costly failure their current
handoff process misses before adding integrations or a paid team version.

For feedback, please answer: Could you run the demo without help? What does
`BLOCK` mean to you? Have you encountered this failure in a real workflow?
Please do not send private code, credentials, or customer data as feedback.

## Developer experiment: actual test runs

```cmd
python experiments/workflow_002.py
```

This optional experiment copies this project's source and tests into a temporary
Git repository. It runs the real test suite, commits a documentation change, and
then deliberately introduces a regression in that disposable copy. The regression
is expected to fail the copied tests. The experiment succeeds only when its
expected results are observed. It writes a JSON report under `experiments/results/`.

This is a controlled experiment, not a customer incident. It demonstrates that
the current Gate checks old records while actual test execution is a separate
source of evidence. See [the experiment findings](VALIDATION_002.md).
