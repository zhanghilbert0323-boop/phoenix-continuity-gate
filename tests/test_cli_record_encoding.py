"""Windows editors may save otherwise valid JSON with a UTF-8 BOM."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from phoenix_continuity_gate.__main__ import main


class RecordEncodingTests(unittest.TestCase):
    def test_inspect_accepts_utf8_with_and_without_bom_without_execution(self):
        for encoding in ("utf-8", "utf-8-sig"):
            with self.subTest(encoding=encoding), tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "record.json"
                payload = {"note": "中文", "command": ["never-run-this"]}
                path.write_text(json.dumps(payload, ensure_ascii=False), encoding=encoding)
                result = {"execution": "SUCCEEDED", "freshness": "MATCH",
                          "verdict": "PASS", "findings": [], "scope": "test fixture"}
                with patch("sys.argv", ["phoenix", "inspect", "--repo", temp,
                                        "--record", str(path)]), \
                     patch("phoenix_continuity_gate.__main__.assess_record", return_value=result) as assess, \
                     patch("phoenix_continuity_gate.__main__.record_command") as execute, \
                     contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(main(), 0)
                    assess.assert_called_once_with(payload, Path(temp))
                    execute.assert_not_called()

    def test_check_accepts_utf8_with_and_without_bom(self):
        for encoding in ("utf-8", "utf-8-sig"):
            with self.subTest(encoding=encoding), tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "handoff.json"
                payload = {"schema_version": 1, "note": "中文"}
                path.write_text(json.dumps(payload, ensure_ascii=False), encoding=encoding)
                with patch("sys.argv", ["phoenix", "check", "--repo", temp,
                                        "--handoff", str(path)]), \
                     patch("phoenix_continuity_gate.__main__.evaluate", return_value=("REVIEW", [])) as evaluate, \
                     contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(), 1)
                    evaluate.assert_called_once_with(payload, Path(temp))

    def test_malformed_or_non_utf8_records_remain_rejected(self):
        for command, option, assessor in (("inspect", "--record", "assess_record"),
                                          ("check", "--handoff", "evaluate")):
            for data in (b"\xef\xbb\xbf{broken", b"\xff\xfe{}"):
                with self.subTest(command=command, data=data), tempfile.TemporaryDirectory() as temp:
                    path = Path(temp) / "invalid.json"
                    path.write_bytes(data)
                    with patch("sys.argv", ["phoenix", command, "--repo", temp, option, str(path)]), \
                         patch("phoenix_continuity_gate.__main__." + assessor) as assess, \
                         patch("phoenix_continuity_gate.__main__.record_command") as execute, \
                         contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        self.assertEqual(main(), 2)
                        assess.assert_not_called()
                        execute.assert_not_called()
