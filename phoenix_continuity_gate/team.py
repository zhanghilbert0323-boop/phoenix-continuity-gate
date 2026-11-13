"""Versioned local team-check configuration. No implicit refreshes or uploads."""

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib

from .evidence import repository_root
from .managed import inspect_current, refresh_current
from .resume import plan_from_report


ID = re.compile(r"[a-z][a-z0-9_-]{0,63}")


@dataclass(frozen=True)
class Check:
    name: str
    command: tuple[str, ...]
    timeout: float
    scope: str = "tracked-repository"

    def argv(self):
        # Only this exact executable token is expanded. No shell or env expansion.
        return [sys.executable if index == 0 and value == "{python}" else value
                for index, value in enumerate(self.command)]


@dataclass(frozen=True)
class Project:
    root: Path
    config: Path
    project: str
    checks: tuple[Check, ...]

    def binding(self, check):
        definition = {"config_schema_version": 1, "project": self.project,
                      "config": str(self.config), "check": check.name,
                      "command": check.argv(), "timeout": check.timeout, "scope": check.scope}
        return hashlib.sha256(json.dumps(definition, sort_keys=True, separators=(",", ":"),
                                         ensure_ascii=True).encode("utf-8")).hexdigest()

    def state_for(self, state_root, check):
        base = Path(state_root).resolve()
        if base == self.root or self.root in base.parents:
            raise ValueError("Team state must be outside the target repository")
        key = hashlib.sha256(str(self.root).encode("utf-8")).hexdigest()
        return base / f"{self.project}-{key}" / check.name


def load_project(path):
    path = Path(path).resolve()
    data = tomllib.loads(path.read_text(encoding="utf-8-sig"))
    if (set(data) != {"config_schema_version", "project", "checks"}
            or type(data.get("config_schema_version")) is not int or data["config_schema_version"] != 1
            or not isinstance(data.get("project"), str) or ID.fullmatch(data["project"]) is None
            or not isinstance(data.get("checks"), dict) or not data["checks"]):
        raise ValueError("Expected config schema 1, a project ID and at least one named check; unknown keys are rejected")
    root = repository_root(path.parent)
    if not path.is_relative_to(root):
        raise ValueError("Config must be inside the target Git repository")
    tracked = subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", "--",
                              path.relative_to(root).as_posix()], capture_output=True, timeout=30)
    if tracked.returncode:
        raise ValueError("Config must be tracked in the target repository; do not auto-commit unrelated work")
    checks = []
    for name, value in sorted(data["checks"].items()):
        if not isinstance(name, str) or ID.fullmatch(name) is None or not isinstance(value, dict):
            raise ValueError("Invalid check ID or definition")
        if set(value) != {"command", "timeout_seconds", "scope"}:
            raise ValueError(f"Check {name}: command, timeout_seconds and scope are required; unknown keys are rejected")
        command, timeout = value["command"], value["timeout_seconds"]
        if (not isinstance(command, list) or not command or not command[0]
                or not all(isinstance(part, str) and "\0" not in part for part in command)
                or any("{python}" in part for part in command[1:])
                or ("{python}" in command[0] and command[0] != "{python}")):
            raise ValueError(f"Check {name}: command must be an explicit argv list; only argv[0] may be exactly {{python}}")
        if type(timeout) not in (int, float) or not 0 < timeout <= 86400:
            raise ValueError(f"Check {name}: timeout_seconds must be finite, positive and no more than 86400")
        if value["scope"] != "tracked-repository":
            raise ValueError(f"Check {name}: only tracked-repository scope is supported")
        checks.append(Check(name, tuple(command), float(timeout)))
    return Project(root, path, data["project"], tuple(checks))


def error_result(message):
    return {"workflow_schema_version": 1, "assessment": None,
            "decision": plan_from_report(None, 2), "error": str(message)}


def run_checks(config, state_root, action, name=None):
    if action not in ("status", "refresh"):
        raise ValueError("Unknown team action")
    project = load_project(config)
    selected = [check for check in project.checks if name is None or check.name == name]
    if not selected or (action == "refresh" and name is None):
        raise ValueError("Choose one existing --check for an explicit refresh")
    # Resolve every state path before doing any I/O or starting a command.
    states = [(check, project.state_for(state_root, check)) for check in selected]
    results, exit_code = [], 0
    for check, state in states:
        try:
            if action == "refresh":
                result, code = refresh_current(project.root, state, check.argv(), check.timeout,
                                               binding=project.binding(check))
            else:
                result, code = inspect_current(project.root, state, binding=project.binding(check),
                                               expected_command=check.argv())
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            result, code = error_result(exc), 2
        results.append({"check": check.name, **result})
        exit_code = max(exit_code, code)
    return {"team_schema_version": 1, "project": project.project, "operation": action,
            "verdict": {0: "PASS", 1: "REVIEW", 2: "BLOCK"}[exit_code], "checks": results}, exit_code


def main(argv=None):
    parser = argparse.ArgumentParser(description="Configured local team checks; only refresh executes a command")
    actions = parser.add_subparsers(dest="action", required=True)
    validate = actions.add_parser("validate", help="Validate config only; execute nothing")
    validate.add_argument("--config", type=Path, required=True)
    for action in ("status", "refresh"):
        sub = actions.add_parser(action)
        sub.add_argument("--config", type=Path, required=True)
        sub.add_argument("--state", type=Path, required=True)
        sub.add_argument("--check", required=action == "refresh")
    args = parser.parse_args(argv)
    try:
        if args.action == "validate":
            project = load_project(args.config)
            result, code = {"team_schema_version": 1, "operation": "validate", "valid": True,
                            "project": project.project, "checks": [check.name for check in project.checks]}, 0
        else:
            result, code = run_checks(args.config, args.state, args.action, args.check)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result, code = {"team_schema_version": 1, "operation": args.action, "verdict": "BLOCK",
                        "checks": [], "error": str(exc)}, 2
        if args.action == "validate":
            result["valid"] = False
    print(json.dumps(result, ensure_ascii=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
