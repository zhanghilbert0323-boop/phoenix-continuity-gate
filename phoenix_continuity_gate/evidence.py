"""Local command observations, bound to endpoint snapshots of tracked files.

Records are editable local JSON, not authenticated attestations. Ignored files,
environment state and changes reverted during execution are outside this scope.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import signal
import subprocess
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_LIMIT = 16_384


def _git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "--no-optional-locks", "-C", str(repo), *args],
        capture_output=True, timeout=30,
    )
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", errors="replace").strip() or "Git failed")
    return result.stdout


def repository_root(repo: Path) -> Path:
    return Path(os.fsdecode(_git(repo, "rev-parse", "--show-toplevel")).strip()).resolve()


def snapshot(repo: Path) -> dict[str, Any]:
    root = repository_root(repo)
    head = _git(root, "rev-parse", "HEAD").decode("ascii").strip()
    status = _git(root, "-c", "core.fsmonitor=false", "status", "--porcelain=v1", "--untracked-files=all").decode("utf-8", errors="replace")
    files: dict[str, dict[str, str]] = {}
    for raw_path in _git(root, "ls-files", "-z", "--cached").split(b"\0"):
        if not raw_path:
            continue
        name = os.fsdecode(raw_path)
        path = root / name
        if path.is_symlink():
            digest = hashlib.sha256(os.fsencode(os.readlink(path))).hexdigest()
            kind = "symlink"
        elif path.is_file():
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            kind = "file"
        elif not path.exists():
            digest = hashlib.sha256(b"").hexdigest()
            kind = "missing"
        else:
            raise ValueError(f"Cannot snapshot tracked path {name!r}; submodules and tracked directories are unsupported")
        files[name] = {"kind": kind, "sha256": digest}
    # Catch ordinary modifications that occur while the snapshot is being read.
    if head != _git(root, "rev-parse", "HEAD").decode("ascii").strip():
        raise ValueError("HEAD changed while taking a snapshot")
    if status != _git(root, "-c", "core.fsmonitor=false", "status", "--porcelain=v1", "--untracked-files=all").decode("utf-8", errors="replace"):
        raise ValueError("Working tree changed while taking a snapshot")
    return {"root": str(root), "head": head, "working_tree_status": status, "files": files}


def _tail(stream: Any) -> dict[str, Any]:
    size = stream.seek(0, os.SEEK_END)
    stream.seek(max(0, size - LOG_LIMIT))
    return {"text": stream.read().decode("utf-8", errors="replace"),
            "truncated": size > LOG_LIMIT, "bytes": size}


def _terminate(process: subprocess.Popen) -> str | None:
    """Best effort termination of the foreground process group/tree."""
    error = None
    try:
        if os.name == "nt":
            result = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True, timeout=10,
            )
            if result.returncode and process.poll() is None:
                error = "Process-tree termination failed; attempted direct process termination"
        else:
            os.killpg(process.pid, signal.SIGKILL)
    except (OSError, subprocess.TimeoutExpired) as exc:
        error = f"Process-group termination could not be confirmed: {exc}"
    try:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=10)
    except (OSError, subprocess.TimeoutExpired) as exc:
        error = f"Process termination could not be confirmed: {exc}"
    return error


def _execute(command: list[str], root: Path, timeout: float) -> dict[str, Any]:
    start = time.monotonic()
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
        status, code, error, termination_error = "START_FAILED", None, None, None
        try:
            process = subprocess.Popen(command, cwd=root, stdout=stdout, stderr=stderr,
                                       stdin=subprocess.DEVNULL, shell=False, **options)
        except OSError as exc:
            error = str(exc)
        else:
            try:
                code = process.wait(timeout=timeout)
                status = "SUCCEEDED" if code == 0 else "FAILED"
            except subprocess.TimeoutExpired:
                status = "TIMED_OUT"
                termination_error = _terminate(process)
            except KeyboardInterrupt:
                status = "INTERRUPTED"
                termination_error = _terminate(process)
        return {"status": status, "exit_code": code, "error": error,
                "termination_error": termination_error,
                "elapsed_seconds": round(time.monotonic() - start, 3),
                "stdout": _tail(stdout), "stderr": _tail(stderr)}


def record_command(repo: Path, output: Path, command: list[str], timeout: float = 60) -> dict[str, Any]:
    if not isinstance(command, list) or not command or not command[0] or not all(isinstance(arg, str) and "\0" not in arg for arg in command):
        raise ValueError("Supply an explicit command after --")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Timeout must be a positive finite number")
    root = repository_root(repo)
    output = output.resolve()
    if output.is_relative_to(root):
        raise ValueError("Save the record outside the repository so it does not change the checked snapshot")
    before = snapshot(root)
    if before["working_tree_status"]:
        raise ValueError("Recording requires a clean Git working tree; commit or preserve your changes first")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Reserve a new file before executing. Existing records are never overwritten.
    with output.open("x", encoding="utf-8") as stream:
        started = datetime.now(timezone.utc).isoformat()
        execution = _execute(command, root, timeout)
        after, snapshot_error = None, None
        try:
            after = snapshot(root)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            snapshot_error = str(exc)
        record = {"evidence_schema_version": 1, "kind": "local-command-run",
                  "id": str(uuid.uuid4()), "started_at_utc": started,
                  "finished_at_utc": datetime.now(timezone.utc).isoformat(),
                  "command": command, "timeout_seconds": timeout,
                  "execution": execution, "snapshot_before": before,
                  "snapshot_after": after, "snapshot_error": snapshot_error}
        json.dump(record, stream, indent=2, ensure_ascii=True)
        stream.write("\n")
    return record


def _hex(value: Any, lengths: tuple[int, ...]) -> bool:
    return isinstance(value, str) and len(value) in lengths and all(c in "0123456789abcdef" for c in value)


def _validate_snapshot(value: Any) -> None:
    if not isinstance(value, dict) or not isinstance(value.get("root"), str) or not value["root"]:
        raise ValueError("Invalid snapshot root")
    if not _hex(value.get("head"), (40, 64)) or not isinstance(value.get("working_tree_status"), str):
        raise ValueError("Invalid snapshot HEAD or working-tree state")
    if not isinstance(value.get("files"), dict):
        raise ValueError("Missing tracked-file fingerprints")
    for name, entry in value["files"].items():
        if not isinstance(name, str) or not name or Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("Invalid tracked-file name")
        if not isinstance(entry, dict) or entry.get("kind") not in ("file", "symlink", "missing") or not _hex(entry.get("sha256"), (64,)):
            raise ValueError("Invalid tracked-file fingerprint")


def assess_record(record: Any, repo: Path) -> dict[str, Any]:
    """Inspect data and local files only; never execute the stored command."""
    if not isinstance(record, dict) or type(record.get("evidence_schema_version")) is not int or record["evidence_schema_version"] != 1 or record.get("kind") != "local-command-run":
        raise ValueError("Expected a version-1 local-command-run record")
    command = record.get("command")
    if not isinstance(command, list) or not command or not command[0] or not all(isinstance(arg, str) and "\0" not in arg for arg in command):
        raise ValueError("Invalid command metadata")
    execution = record.get("execution")
    if not isinstance(execution, dict):
        raise ValueError("Missing execution result")
    status, code = execution.get("status"), execution.get("exit_code")
    if status not in ("SUCCEEDED", "FAILED", "TIMED_OUT", "START_FAILED", "INTERRUPTED"):
        raise ValueError("Unknown execution status")
    if status in ("SUCCEEDED", "FAILED"):
        if type(code) is not int or (status == "SUCCEEDED") != (code == 0):
            raise ValueError("Execution status contradicts the exit code")
    elif code is not None:
        raise ValueError("Incomplete execution cannot carry a completed exit code")
    before, after = record.get("snapshot_before"), record.get("snapshot_after")
    _validate_snapshot(before)
    if after is not None:
        _validate_snapshot(after)
    findings = []
    current = snapshot(repo)
    freshness = "MATCH"
    if after is None or record.get("snapshot_error"):
        freshness = "UNKNOWN"
        findings.append("No usable post-execution snapshot was recorded.")
    elif before != after or before["working_tree_status"] or after["working_tree_status"]:
        freshness = "UNSTABLE_DURING_RUN"
        findings.append("Endpoint snapshots differ or contain uncommitted changes; the result is not bound to a stable snapshot.")
    elif Path(before["root"]).resolve() != Path(current["root"]).resolve():
        freshness = "UNKNOWN"
        findings.append("This record belongs to a different repository location.")
    elif before != current:
        freshness = "CHANGED"
        findings.append("HEAD, tracked contents or working-tree state differ from the recorded snapshot.")
    if status != "SUCCEEDED":
        findings.append(f"The recorded command did not succeed: {status}.")
    if execution.get("termination_error"):
        findings.append("Process-tree termination could not be fully confirmed.")
    if status != "SUCCEEDED" or freshness == "CHANGED":
        verdict = "BLOCK"
    elif freshness != "MATCH" or execution.get("termination_error"):
        verdict = "REVIEW"
    else:
        verdict = "PASS"
        findings.append("The record reports exit code 0 and its tracked-file snapshot still matches.")
    return {"verdict": verdict, "execution": status, "freshness": freshness, "findings": findings,
            "scope": "Editable local record; ignored files, environment, background work and changes reverted during execution are not verified. Exit code 0 does not prove test coverage or code correctness."}
