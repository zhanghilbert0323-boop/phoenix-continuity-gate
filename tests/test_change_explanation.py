"""Explanations describe observed changes without weakening gate decisions."""

import copy
import unittest

from phoenix_continuity_gate.evidence import describe_changes


class ChangeExplanationTests(unittest.TestCase):
    def setUp(self):
        self.before = {"root": "example", "head": "a" * 40,
                       "working_tree_status": "", "files": {
                           "app.py": {"kind": "file", "sha256": "b" * 64}}}
        self.after = copy.deepcopy(self.before)

    def describe(self):
        return "\n".join(describe_changes(self.before, self.after))

    def test_content_change_names_file_without_showing_contents(self):
        self.after["files"]["app.py"]["sha256"] = "c" * 64
        text = self.describe()
        self.assertIn('CONTENT_CHANGED: "app.py"', text)
        self.assertNotIn("c" * 64, text)
        self.assertIn("do not identify which tests", text)

    def test_empty_commit_is_not_presented_as_a_file_change(self):
        self.after["head"] = "d" * 40
        text = self.describe()
        self.assertIn("HEAD changed:", text)
        self.assertIn("Tracked-file differences: 0", text)

    def test_added_removed_and_missing_are_distinct(self):
        self.after["files"]["new.py"] = self.after["files"].pop("app.py")
        text = self.describe()
        self.assertIn('ADDED_TO_TRACKED_SET: "new.py"', text)
        self.assertIn('REMOVED_FROM_TRACKED_SET: "app.py"', text)
        self.after = copy.deepcopy(self.before)
        self.after["files"]["app.py"]["kind"] = "missing"
        self.assertIn('MISSING_ON_DISK: "app.py"', self.describe())

    def test_file_type_change_is_explicit(self):
        self.after["files"]["app.py"]["kind"] = "symlink"
        self.assertIn('TYPE_CHANGED: "app.py"', self.describe())

    def test_untracked_file_is_shown_as_status_not_hashed_content(self):
        self.after["working_tree_status"] = "?? notes.txt\n"
        text = self.describe()
        self.assertIn('Compared: "?? notes.txt"', text)
        self.assertIn("Tracked-file differences: 0", text)
        self.assertNotIn("CONTENT_CHANGED", text)

    def test_lists_are_bounded_and_truncation_is_explicit(self):
        for i in range(25):
            self.after["files"][f"extra-{i:02}.py"] = {"kind": "file", "sha256": "b" * 64}
        self.after["working_tree_status"] = "".join(f"?? other-{i}\n" for i in range(25))
        text = self.describe()
        self.assertEqual(text.count("ADDED_TO_TRACKED_SET:"), 20)
        self.assertIn("5 more tracked-file differences omitted", text)
        self.assertIn("5 more compared entries omitted", text)

    def test_paths_are_escaped_and_snapshots_are_not_modified(self):
        name = "line\nbreak\x1b[31m.py"
        self.after["files"][name] = {"kind": "file", "sha256": "b" * 64}
        saved = copy.deepcopy(self.after)
        text = self.describe()
        self.assertNotIn("\x1b", text)
        self.assertIn(r"line\nbreak\u001b[31m.py", text)
        self.assertEqual(saved, self.after)


if __name__ == "__main__":
    unittest.main()
