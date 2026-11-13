"""Create/change an authorized disposable sample for the actual composite action.

Writes only under RUNNER_TEMP/phoenix-team-ci-fixture; never removes an existing
directory, checks out untrusted branches or prints execution records.
"""

import os
from pathlib import Path
import subprocess
import sys


def main():
    base = Path(os.environ["RUNNER_TEMP"]).resolve()
    repo = base / "phoenix-team-ci-fixture"
    if len(sys.argv) != 2 or sys.argv[1] not in ("create", "change"):
        raise ValueError("Choose create or change")
    if sys.argv[1] == "change":
        if repo.is_symlink() or repo.resolve().parent != base or not (repo / ".git").is_dir():
            raise ValueError("Unexpected fixture location")
        (repo / "sample.txt").write_text("normal sample edit\n", encoding="utf-8")
        return
    repo.mkdir()  # Refuse to reuse an existing directory.
    (repo / "sample.txt").write_text("initial\n", encoding="utf-8")
    (repo / "phoenix.toml").write_text(
        'config_schema_version = 1\nproject = "ci-sample"\n\n[checks.unit]\n'
        'command = ["{python}", "-B", "-c", "assert 2 + 2 == 4"]\n'
        'timeout_seconds = 30\nscope = "tracked-repository"\n', encoding="utf-8")
    for args in (("init", "-q"), ("config", "user.name", "Phoenix CI Fixture"),
                 ("config", "user.email", "ci@example.invalid"),
                 ("config", "commit.gpgSign", "false"),
                 ("config", "core.hooksPath", str(base / "no-fixture-hooks")),
                 ("add", "."), ("commit", "-qm", "sample")):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, timeout=30)
    with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as stream:
        stream.write(f"config={repo / 'phoenix.toml'}\n")


if __name__ == "__main__":
    main()
