# -*- coding: utf-8 -*-
#
# AutoNote for Notepad++ — © 2026 Himanshu Dadhich.
# Developed by Himanshu Dadhich. Released under the MIT License; see LICENSE.
#
"""
Tests for the parts of autonote that do not need Notepad++.

Run with:  python -m unittest discover -s tests
The Npp module only exists inside the PythonScript plugin, so it is stubbed.
"""
import json
import os
import sys
import tempfile
import types
import unittest

_npp = types.ModuleType("Npp")
_npp.notepad = _npp.editor = None
_npp.NOTIFICATION = types.SimpleNamespace(FILECLOSED=1)
_npp.SCINTILLANOTIFICATION = types.SimpleNamespace(SAVEPOINTLEFT=1)
sys.modules.setdefault("Npp", _npp)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import autonote  # noqa: E402


class NamingTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()

    def name_for(self, tab, text):
        return os.path.basename(autonote.target_path(self.folder, tab, text, "2026-10-04"))

    def test_default_tab_uses_date_and_first_line(self):
        self.assertEqual(self.name_for("new 12", "client call points\nmore"),
                         "2026-10-04 client call points.txt")

    def test_blank_leading_lines_are_skipped(self):
        self.assertEqual(self.name_for("new 1", "\n   \nreal title\n"), "2026-10-04 real title.txt")

    def test_illegal_characters_are_removed(self):
        self.assertEqual(self.name_for("new 1", 'a/b:c*d?"e<f>g|h'), "2026-10-04 a b c d e f g h.txt")

    def test_long_first_line_is_cut_and_has_no_trailing_dot(self):
        name = self.name_for("new 1", "x" * 59 + ". tail")
        self.assertEqual(name, "2026-10-04 " + "x" * 59 + ".txt")

    def test_symbols_only_line_falls_back_to_note(self):
        self.assertEqual(self.name_for("new 1", "???\n***"), "2026-10-04 note.txt")

    def test_renamed_tab_keeps_its_name(self):
        self.assertEqual(self.name_for("Innovative Ideas", "anything"), "Innovative Ideas.txt")

    def test_renamed_tab_keeps_a_real_extension(self):
        self.assertEqual(self.name_for("todo.md", "anything"), "todo.md")

    def test_dot_in_name_is_not_mistaken_for_extension(self):
        self.assertEqual(self.name_for("v1.2 release notes", "x"), "v1.2 release notes.txt")

    def test_existing_file_is_never_overwritten(self):
        open(os.path.join(self.folder, "2026-10-04 same.txt"), "w").close()
        self.assertEqual(self.name_for("new 1", "same"), "2026-10-04 same (2).txt")
        open(os.path.join(self.folder, "2026-10-04 same (2).txt"), "w").close()
        self.assertEqual(self.name_for("new 1", "same"), "2026-10-04 same (3).txt")

    def test_non_latin_first_line_is_kept(self):
        self.assertEqual(self.name_for("new 1", "आज के काम\n"), "2026-10-04 आज के काम.txt")


class PathTests(unittest.TestCase):
    def test_untitled_means_no_absolute_path(self):
        self.assertTrue(autonote.is_untitled("new 3"))
        self.assertFalse(autonote.is_untitled(r"C:\work\a.txt"))

    def test_notes_dir_match_is_case_insensitive_and_exact(self):
        self.assertTrue(autonote.in_notes_dir(r"d:\notepad\a.txt", r"D:\Notepad"))
        self.assertTrue(autonote.in_notes_dir(r"D:\Notepad\sub\a.txt", r"D:\Notepad"))
        self.assertFalse(autonote.in_notes_dir(r"D:\Notepad-old\a.txt", r"D:\Notepad"))
        self.assertFalse(autonote.in_notes_dir(r"D:\Other\a.txt", r"D:\Notepad"))


class ConfigTests(unittest.TestCase):
    def write(self, data):
        path = os.path.join(tempfile.mkdtemp(), "autonote.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle)
        return path

    def test_missing_file_gives_defaults(self):
        self.assertEqual(autonote.load_config(os.path.join(tempfile.mkdtemp(), "none.json")),
                         autonote.DEFAULTS)

    def test_known_keys_override_defaults(self):
        settings = autonote.load_config(self.write({"notes_dir": r"D:\Notes", "tick_seconds": 5}))
        self.assertEqual(settings["notes_dir"], r"D:\Notes")
        self.assertEqual(settings["tick_seconds"], 5)
        self.assertEqual(settings["extension"], ".txt")

    def test_unknown_keys_and_wrong_types_are_ignored(self):
        settings = autonote.load_config(self.write({"bogus": 1, "tick_seconds": "fast"}))
        self.assertNotIn("bogus", settings)
        self.assertEqual(settings["tick_seconds"], autonote.DEFAULTS["tick_seconds"])

    def test_bad_extension_falls_back(self):
        self.assertEqual(autonote.load_config(self.write({"extension": "txt/.."}))["extension"], ".txt")


class EncodingCheckTests(unittest.TestCase):
    TEXT = "price → ₹500 — done…"

    def save(self, encoding):
        path = os.path.join(tempfile.mkdtemp(), "note.txt")
        with open(path, "wb") as handle:
            handle.write(self.TEXT.encode(encoding, errors="replace"))
        return path

    def test_utf8_with_and_without_bom_matches(self):
        self.assertTrue(autonote.saved_text_matches(self.save("utf-8"), self.TEXT))
        self.assertTrue(autonote.saved_text_matches(self.save("utf-8-sig"), self.TEXT))

    def test_utf16_matches(self):
        self.assertTrue(autonote.saved_text_matches(self.save("utf-16"), self.TEXT))

    def test_legacy_codepage_is_flagged(self):
        self.assertFalse(autonote.saved_text_matches(self.save("gbk"), self.TEXT))
        self.assertFalse(autonote.saved_text_matches(self.save("cp1252"), self.TEXT))


if __name__ == "__main__":
    unittest.main()
