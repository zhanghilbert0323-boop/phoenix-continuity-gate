"""Bounded synthetic snapshot probe; not a customer workload benchmark."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from phoenix_continuity_gate import __version__
from phoenix_continuity_gate.evidence import assess_record, record_command


def probe(files=1000, repeats=5):
    if type(files) is not int or not 1 <= files <= 20000 or type(repeats) is not int or not 1 <= repeats <= 100:
        raise ValueError("Use 1..20000 files and 1..100 inspections")
    with tempfile.TemporaryDirectory(prefix="phoenix-scale-") as directory:
        base = Path(directory)
        repo = base / "repo"
        repo.mkdir()
        content = "x" * 1024
        for index in range(files):
            (repo / f"sample-{index:05d}.txt").write_text(content, encoding="utf-8")
        for args in (("init", "-q"), ("config", "user.name", "Phoenix Scale Probe"),
                     ("config", "user.email", "probe@example.invalid"),
                     ("config", "commit.gpgSign", "false"),
                     ("config", "core.hooksPath", str(base / "no-hooks")),
                     ("add", "."), ("commit", "-qm", "synthetic files")):
            subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, timeout=60)
        counter = base / "starts.txt"
        command = [sys.executable, "-B", "-c",
                   f"from pathlib import Path; p=Path({str(counter)!r}); p.write_text('started')"]
        start = time.perf_counter()
        record = record_command(repo, base / "record.json", command)
        record_seconds = time.perf_counter() - start
        timings, verdicts = [], []
        for _ in range(repeats):
            start = time.perf_counter()
            result = assess_record(record, repo)
            timings.append(time.perf_counter() - start)
            verdicts.append(result["verdict"])
        (repo / "sample-00000.txt").write_text("ordinary edit", encoding="utf-8")
        start = time.perf_counter()
        changed = assess_record(record, repo)
        stale_seconds = time.perf_counter() - start
        passed = all(value == "PASS" for value in verdicts) and changed["verdict"] == "BLOCK"
        return {"experiment": "synthetic-scale-probe", "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "tool_version": __version__, "python": platform.python_version(), "platform": platform.platform(),
                "files": files, "bytes_per_file": 1024, "total_tracked_bytes": files * 1024,
                "inspection_count": repeats, "record_seconds": round(record_seconds, 6),
                "inspection_seconds": [round(value, 6) for value in timings],
                "inspection_median_seconds": round(statistics.median(timings), 6),
                "stale_inspection_seconds": round(stale_seconds, 6),
                "unchanged_verdicts": verdicts, "changed_verdict": changed["verdict"], "passed": passed,
                "scope": "Small synthetic tracked files on one local machine; not a supported-size limit, customer benchmark, cold-cache test or savings claim."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--files", type=int, default=1000)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.output:
            with args.output.open("x", encoding="utf-8") as stream:
                result = probe(args.files, args.repeats)
                json.dump(result, stream, indent=2)
                stream.write("\n")
        else:
            result = probe(args.files, args.repeats)
        print(json.dumps(result))
        return 0 if result["passed"] else 2
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"Probe failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
