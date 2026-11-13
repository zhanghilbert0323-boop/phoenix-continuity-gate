"""Example single-workflow evidence selection, not an agent or retry scheduler.

Local state and hashes detect accidental mismatches, not malicious modification.
Use one private state directory per repository/workflow/check definition.
"""

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import uuid

from .evidence import assess_record, record_command, repository_root
from .resume import plan_from_report


def _paths(repo, state):
    root = repository_root(Path(repo))
    state = Path(state).resolve()
    if state == root or root in state.parents:
        raise ValueError("Workflow state must be outside the target repository")
    return root, state


@contextmanager
def _lock(state, create=False):
    if create:
        state.mkdir(parents=True, exist_ok=True)
    lock = state / ".lock"
    # Exclusive creation fails immediately: no waiting and no stale-lock guessing.
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(f"pid={os.getpid()}\n")
    try:
        yield
    finally:
        lock.unlink()


def _write_pointer(state, pointer):
    # Replace only the small pointer. Immutable, uniquely named records remain.
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=state,
                                         prefix=".pointer-", suffix=".tmp", delete=False) as stream:
            name = stream.name
            json.dump(pointer, stream, ensure_ascii=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, state / "current.json")
    finally:
        if name is not None:
            Path(name).unlink(missing_ok=True)


def _read_pointer(root, state, binding=None, allow_binding_change=False):
    path = state / "current.json"
    if path.is_symlink():
        raise ValueError("The current pointer must not be a symlink")
    pointer = json.loads(path.read_text(encoding="utf-8-sig"))
    if (not isinstance(pointer, dict) or type(pointer.get("state_schema_version")) is not int
            or pointer["state_schema_version"] != 1
            or pointer.get("repo") != str(root)
            or pointer.get("status") not in ("PENDING", "COMPLETE")):
        raise ValueError("Unsupported workflow state or repository mismatch")
    stored_binding = pointer.get("binding")
    if stored_binding is not None and (not isinstance(stored_binding, str)
                                      or re.fullmatch(r"[0-9a-f]{64}", stored_binding) is None):
        raise ValueError("Invalid configured-check binding")
    if stored_binding is not None and binding is None:
        raise ValueError("This state belongs to a configured check; use the team interface")
    if not allow_binding_change and stored_binding != binding:
        raise ValueError("Check definition changed; review the config and explicitly refresh this check")
    if pointer["status"] == "COMPLETE":
        if (not isinstance(pointer.get("record"), str)
                or re.fullmatch(r"run-[0-9a-f]{32}\.json", pointer["record"]) is None
                or not isinstance(pointer.get("sha256"), str)
                or re.fullmatch(r"[0-9a-f]{64}", pointer["sha256"]) is None):
            raise ValueError("Invalid selected-record name or digest")
    return pointer


def _inspect_selected(root, state, binding=None, expected_command=None):
    pointer = _read_pointer(root, state, binding)
    if pointer["status"] != "COMPLETE":
        raise ValueError("The last refresh did not complete; review it before explicitly refreshing again")
    path = state / pointer["record"]
    if path.is_symlink():
        raise ValueError("The selected record must not be a symlink")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != pointer["sha256"]:
        raise ValueError("The selected record changed after selection")
    record = json.loads(raw.decode("utf-8-sig"))
    if expected_command is not None and (not isinstance(record, dict) or record.get("command") != expected_command):
        raise ValueError("Selected record command does not match the configured check")
    assessment = assess_record(record, root)
    report = {"report_schema_version": 1, "assessment_status": "ASSESSED",
              **assessment, "error": None}
    code = {"PASS": 0, "REVIEW": 1, "BLOCK": 2}[assessment["verdict"]]
    return {"workflow_schema_version": 1, "assessment": report,
            "decision": plan_from_report(report, code)}, code


def inspect_current(repo, state, *, binding=None, expected_command=None):
    """Read the selected record; never execute its stored command."""
    root, state = _paths(repo, state)
    with _lock(state):
        return _inspect_selected(root, state, binding, expected_command)


def refresh_current(repo, state, argv, timeout=60, *, binding=None):
    """Run exactly one explicitly supplied command and select its result.

    Any failure before final selection leaves PENDING, never the previous PASS.
    Failed and timed-out executions are selected too; there is no success fallback.
    """
    root, state = _paths(repo, state)
    if binding is not None and (not isinstance(binding, str) or re.fullmatch(r"[0-9a-f]{64}", binding) is None):
        raise ValueError("Invalid configured-check binding")
    with _lock(state, create=True):
        current = state / "current.json"
        if current.exists() or current.is_symlink():
            _read_pointer(root, state, binding, allow_binding_change=True)
        pointer = {"state_schema_version": 1, "repo": str(root), "status": "PENDING"}
        if binding is not None:
            pointer["binding"] = binding
        _write_pointer(state, pointer)
        filename = f"run-{uuid.uuid4().hex}.json"
        path = state / filename
        record_command(root, path, argv, timeout)
        pointer.update(status="COMPLETE", record=filename,
                       sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        _write_pointer(state, pointer)
        return _inspect_selected(root, state, binding, argv)


def main():
    parser = argparse.ArgumentParser(description="Example: explicitly refresh or inspect one workflow's current evidence")
    actions = parser.add_subparsers(dest="action", required=True)
    for action in ("status", "refresh"):
        sub = actions.add_parser(action)
        sub.add_argument("--repo", type=Path, required=True)
        sub.add_argument("--state", type=Path, required=True, help="Private directory outside the target repository")
        if action == "refresh":
            sub.add_argument("--timeout", type=float, default=60)
            sub.add_argument("argv", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.action == "refresh" and (not args.argv or args.argv[0] != "--" or len(args.argv) < 2):
        parser.error("refresh requires -- followed by the command you explicitly want to run")
    try:
        if args.action == "refresh":
            result, code = refresh_current(args.repo, args.state, args.argv[1:], args.timeout)
        else:
            result, code = inspect_current(args.repo, args.state)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result = {"workflow_schema_version": 1, "assessment": None,
                  "decision": plan_from_report(None, 2), "error": str(exc)}
        code = 2
    print(json.dumps(result, ensure_ascii=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
