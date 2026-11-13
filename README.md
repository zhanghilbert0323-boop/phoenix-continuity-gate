# Phoenix Continuity Gate — development preview 0.2.3.dev0

The installable development preview adds `phoenix-gate`, JSON inspection and a
task-resume example. See [DEV_PREVIEW.md](DEV_PREVIEW.md) for wheel installation
without a source build. Release artifacts are on the
[v0.2.3-dev0 release page](https://github.com/zhanghilbert0323-boop/phoenix-continuity-gate/releases/tag/v0.2.3-dev0).
The website's v0.2.2 download remains a separate, older preview.

New on `main` (not in those release artifacts): a
[selected-record workflow example](examples/MANAGED_WORKFLOW.md). Explicit
refreshes select their result, including failures; status checks read it without
rerunning commands. Interrupted updates stop rather than reuse an old success.

Product website (no account required): [Phoenix](https://zhanghilbert0323-boop.github.io/phoenix-continuity-gate/).
The website includes an illustrative demo and a same-site copy of the v0.2.2 ZIP.
Direct language links: [English](https://zhanghilbert0323-boop.github.io/phoenix-continuity-gate/?lang=en)
and [中文](https://zhanghilbert0323-boop.github.io/phoenix-continuity-gate/zh.html?lang=zh).
The first-run guide is also hosted on the same website:
[English](https://zhanghilbert0323-boop.github.io/phoenix-continuity-gate/guide.html) /
[中文](https://zhanghilbert0323-boop.github.io/phoenix-continuity-gate/guide-zh.html).
It includes startup troubleshooting and a copyable feedback outline; no feedback
is transmitted by the website.
The public site's source is `docs/`; check its local resources, language routing
and demo interactions with `node scripts/check-site.mjs`. These checks do not
replace browser layout testing.
GitHub's Tests workflow runs these website checks in its own Node.js 22 job,
including the mirrored release ZIP's checksum. These are source and interaction
logic checks; the separate GitHub Pages deployment is not gated by this job.

Version 0.2.2 includes explanations of changed tracked paths, HEAD and
working-tree status, plus English and Chinese trial guides. Older v0.2.1 ZIPs
remain unchanged. This is an explanation only, not dependency analysis or a
rule for skipping tests.

Download: [v0.2.2 preview](https://github.com/zhanghilbert0323-boop/phoenix-continuity-gate/releases/tag/v0.2.2-preview).

Post-release update on `main`: `inspect` and `check` accept UTF-8 JSON both
with and without a BOM (an invisible prefix added by some Windows editors).
Malformed JSON and non-UTF-8 files are still rejected. The v0.2.2 ZIP does not
include this reading-compatibility fix; verdict rules are unchanged.

Development update: `main` can now be installed as a local Python package with a
`phoenix-gate` console command and `--version`. Its development version is
`0.2.3.dev0`. This is not a PyPI publication or a change to the v0.2.2 download.

## Install the development checkout (optional)

Use a Python 3.11+ virtual environment. From a checkout of the current `main`
branch, install the project with:

```text
python -m pip install .
phoenix-gate --version
phoenix-gate demo-record
```

The build may download setuptools through pip. Phoenix has no third-party
runtime dependencies. The older v0.2.2 ZIP does not contain this packaging setup;
its existing module command and Windows launcher still apply.

After activating the same environment, `phoenix-gate` can run from another
directory; no need to return to the Phoenix source folder. Its arguments and exit
codes are the same as `python -m phoenix_continuity_gate`, for example:

```text
phoenix-gate inspect --repo "C:\path\to\your\repo" --record "C:\path\to\records\run-001.json"
```

This example reads a record; it does not rerun its command. To remove the installed
development package, use `python -m pip uninstall phoenix-continuity-gate` in the
same environment. Developers can verify the actual installation with
`python -I scripts/check-installed.py`: it rejects imports from the source tree
and checks the installed executable from an unrelated temporary directory.

### JSON assessment for scripts and agents (development checkout)

`inspect --json` emits one JSON object on stdout. It performs the same read-only
assessment and uses the same exit codes: PASS `0`, REVIEW `1`, BLOCK or invalid
input `2`. The output does not include stored command arguments or execution logs.

```text
phoenix-gate inspect --repo "C:\path\to\your\repo" --record "C:\path\to\records\run-001.json" --json
```

Example for a successfully assessed, stale record (scope text abbreviated here):

```json
{
  "report_schema_version": 1,
  "assessment_status": "ASSESSED",
  "verdict": "BLOCK",
  "execution": "SUCCEEDED",
  "freshness": "CHANGED",
  "findings": ["HEAD, tracked contents or working-tree state differ from the recorded snapshot."],
  "scope": "Editable local record; limitations apply.",
  "error": null
}
```

If the record cannot be read, parsed or assessed, `assessment_status` is `ERROR`,
`verdict` is `BLOCK`, execution and freshness are `UNKNOWN`, and `error` contains
`code: "CANNOT_ASSESS"` and a message. Missing CLI arguments or invalid CLI syntax
still use argparse's normal stderr output; consumers must handle non-JSON output
as an invocation failure. Check the report schema and assessment status as well
as the exit code. A PASS does not authorize merging or deployment. This interface
is present on current `main`, not in the older v0.2.2 ZIP.

For a runnable consumer, see [the task-resume example](examples/README.md).
It reads this interface, checks schema and exit-code consistency, and prints a
suggested evidence-handling action. It never starts a resumed task or runs a
command from a record. The installed-package CI checks also exercise this example.

For the refresh lifecycle, see the [bounded resume-cycle experiment](experiments/RESUME_CYCLE.md).
Its recorded sample performs 14 inspections and four explicitly requested command
runs, observing zero command starts during inspection. A negative control shows
that a caller still selecting old A remains blocked even after B exists. This is
an internal experiment, not an external agent benchmark or a measured cost saving.

Automated compatibility checks: [GitHub Actions runs](https://github.com/zhanghilbert0323-boop/phoenix-continuity-gate/actions/workflows/tests.yml).
The workflow tests Python 3.11 and 3.14 on Windows and Ubuntu runners after code
changes and pull requests; documentation-only changes are skipped. Windows CMD
integration tests are explicitly skipped on Linux. A green run describes those
runner environments and that commit, not all user machines or customer validation.

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
Independent trial guide: [English](TRIAL.md) / [中文](TRIAL.zh-CN.md).

## The first failure case

Agent A records that tests passed at commit `A`. Someone then commits a change
to produce commit `B`. Agent B must not treat the old test claim as current.
The Gate reports `BLOCK` and explains the mismatch.

## Start here: five-minute demo

You need Python 3.11+ and Git available from a terminal. The published v0.2.1
ZIP was locally tested on Windows with Python 3.14 and Git 2.54. Subsequent
`main` commit `65e59af` passed [four hosted CI jobs](https://github.com/zhanghilbert0323-boop/phoenix-continuity-gate/actions/runs/43232158309):
Windows and Ubuntu, each with Python 3.11 and 3.14. Each Windows job passed
48 tests; each Ubuntu job passed 40 and skipped the 8 Windows-only CMD tests.
All four jobs also ran the public demo. macOS and independent user environments
remain unverified; this CI result does not retroactively test the older ZIP.

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
