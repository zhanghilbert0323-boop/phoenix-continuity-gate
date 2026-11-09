# Phoenix Continuity Gate — experimental v0.1

This is an early prototype for developer feedback, not a production safety
system. It runs locally and does not require an account or upload project data.

For the product architecture and staged plan, see [ROADMAP.md](ROADMAP.md).
For the first experiment and its limitations, see [EXPERIMENT_LOG.md](EXPERIMENT_LOG.md).

This is a local, read-only prototype. It checks whether a handoff's recorded Git
commit and test claim still match the repository being resumed. It does **not**
prove that tests really ran, that the code is correct, or that every external
side effect is safe to repeat.

## The first failure case

Agent A records that tests passed at commit `A`. Someone then commits a change
to produce commit `B`. Agent B must not treat the old test claim as current.
The Gate reports `BLOCK` and explains the mismatch.

## Start here: five-minute demo

You need Python 3 and Git available from a terminal. This version was tested
on Windows with Python 3.14 and Git 2.54; other environments are not yet
verified.

If you received a ZIP file, extract the whole project folder first. On
Windows, open that folder in File Explorer, type `cmd` in the address bar, and
press Enter. This opens Command Prompt in the right directory. Do not
double-click an individual `.py` file.

From this directory, run:

```cmd
python -m phoenix_continuity_gate demo
```

The demo creates a temporary, fictional Git repository. It first shows a
`PASS` when the recorded commit and repository match. It then changes the
repository without updating the handoff and shows `BLOCK` with the conflicting
commit hashes. The temporary repository is deleted when the command ends.
No real tests are run: the demo checks only whether a *recorded claim* has
become stale.

If `python` is not recognized, try `py -m phoenix_continuity_gate demo`. If
`git` is not recognized, install Git before retrying. If the terminal says
`No module named phoenix_continuity_gate`, check that you opened Command
Prompt in the extracted project folder, next to this README.

中文理解：第一次检查时交接记录和代码快照都是 A；第二次代码变成 B，交接记录还写 A，所以不能直接沿用“测试通过”。

## Check your own repository (later)

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

## Scope of this first slice

- Checks the handoff commit against current `HEAD`.
- Rejects a recorded failed test or a passed test tied to another commit.
- Flags uncommitted or untracked files for human review.
- Does not run arbitrary commands from a handoff, read secrets, or contact a server.

Next validation: show this case to developers who have actually resumed an
interrupted agent task. Ask whether this catches a costly failure their current
handoff process misses before adding integrations or a paid team version.

For feedback, please answer: Could you run the demo without help? What does
`BLOCK` mean to you? Have you encountered this failure in a real workflow?
Please do not send private code, credentials, or customer data as feedback.
