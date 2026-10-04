# -*- coding: utf-8 -*-
#
# AutoNote for Notepad++ — © 2026 Himanshu Dadhich.
# Developed by Himanshu Dadhich. Released under the MIT License; see LICENSE.
#
"""
Auto-names and auto-saves Notepad++ tabs into a notes folder, so a tab never
has to be saved by hand and closing it never asks.

- An untitled tab ("new 12") is saved into the notes folder as
  "<date> <first line>.txt" once its first line looks finished.
- A tab that already lives in the notes folder is saved again a couple of
  seconds after every edit.
- Files that live anywhere else are left alone; Notepad++ handles them as usual.

Runs inside the PythonScript plugin (version 3.x). Load it from the user
startup.py and set PythonScript's initialisation to ATSTARTUP.
Settings are read from autonote.json next to this file; every key is optional.
"""
import datetime
import json
import os
import re
import threading
import time
import traceback

from Npp import notepad, editor, NOTIFICATION, SCINTILLANOTIFICATION

DEFAULTS = {
    # where notes are saved
    "notes_dir": os.path.join(os.path.expanduser("~"), "Documents", "Notepad Notes"),
    # how often the active tab is checked, in seconds
    "tick_seconds": 2,
    # a one-line untitled tab is named after this many seconds
    "name_after_seconds": 10,
    "max_name_chars": 60,
    "extension": ".txt",
    # on first start, also name and save every untitled tab that is already open
    "convert_existing_tabs": False,
}

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "autonote.json")
STATE_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "AutoNote")
LOG_FILE = os.path.join(STATE_DIR, "autonote.log")
CONVERTED_MARKER = os.path.join(STATE_DIR, "existing-tabs-converted.txt")
SNAPSHOT_DIR = os.path.join(os.environ.get("APPDATA", ""), "Notepad++", "backup")
STARTUP_DELAY_SECONDS = 3

_DEFAULT_TAB_NAME = re.compile(r"^new \d+$")
_ILLEGAL_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_SNAPSHOT_DATE = re.compile(r"@(\d{4}-\d{2}-\d{2})_\d{6}$")
_EXTENSION = re.compile(r"^\.[A-Za-z0-9]{1,5}$")
_UNICODE_CODECS = ("utf-8-sig", "utf-16")

config = dict(DEFAULTS)
# bufferID -> time the tab was first seen with unsaved changes
_dirty = {}
_started = False


def _log(message):
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as handle:
            handle.write("%s  %s\n" % (stamp, message))
    except Exception:
        pass  # logging must never break saving


def load_config(path=CONFIG_FILE):
    """Returns DEFAULTS overlaid with the known keys found in the JSON file."""
    settings = dict(DEFAULTS)
    if not os.path.isfile(path):
        return settings
    with open(path, "r", encoding="utf-8-sig") as handle:
        loaded = json.load(handle)
    for key, value in loaded.items():
        if key in DEFAULTS and isinstance(value, type(DEFAULTS[key])):
            settings[key] = value
    settings["notes_dir"] = os.path.abspath(os.path.expandvars(os.path.expanduser(settings["notes_dir"])))
    if not _EXTENSION.match(settings["extension"]):
        settings["extension"] = DEFAULTS["extension"]
    return settings


def is_untitled(name):
    return not os.path.isabs(name)


def in_notes_dir(path, notes_dir):
    root = os.path.normcase(os.path.abspath(notes_dir)) + os.sep
    return os.path.normcase(os.path.abspath(path)).startswith(root)


def clean_name(raw, max_chars):
    name = _ILLEGAL_CHARS.sub(" ", raw)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:max_chars].strip(" .")


def first_line(text, max_chars):
    for line in text.splitlines():
        cleaned = clean_name(line, max_chars)
        if cleaned:
            return cleaned
    return "note"


def target_path(notes_dir, tab_name, text, date, extension=".txt", max_chars=60):
    """Builds a free file path for an untitled tab."""
    if _DEFAULT_TAB_NAME.match(tab_name):
        base, ext = "%s %s" % (date, first_line(text, max_chars)), extension
    else:
        # the tab was renamed by hand: keep that name
        stem, ext = os.path.splitext(tab_name)
        if not _EXTENSION.match(ext):
            stem, ext = tab_name, extension
        base = clean_name(stem, max_chars) or "note"
    path = os.path.join(notes_dir, base + ext)
    counter = 2
    while os.path.exists(path):
        path = os.path.join(notes_dir, "%s (%d)%s" % (base, counter, ext))
        counter += 1
    return path


def saved_text_matches(path, text):
    """True when the file on disk decodes back to the text in the editor.

    A tab set to a legacy codepage (Encoding > Character sets) is written in
    that codepage, which cannot hold every character. This catches that case.
    """
    with open(path, "rb") as handle:
        raw = handle.read()
    for codec in _UNICODE_CODECS:
        try:
            if raw.decode(codec) == text:
                return True
        except UnicodeError:
            continue
    return False


def _snapshot_date(tab_name):
    """Date Notepad++ first snapshotted this untitled tab, or None."""
    newest = None
    try:
        prefix = tab_name + "@"
        for entry in os.listdir(SNAPSHOT_DIR):
            if entry.startswith(prefix):
                match = _SNAPSHOT_DATE.search(entry)
                if match and (newest is None or match.group(1) > newest):
                    newest = match.group(1)
    except Exception:
        pass
    return newest


def _check_saved(path):
    try:
        if not saved_text_matches(path, editor.getText()):
            _log("WARNING %s was not saved as Unicode; some characters may be lost. "
                 "Use Encoding > Convert to UTF-8 on that tab." % os.path.basename(path))
    except Exception:
        _log("could not verify %s\n%s" % (path, traceback.format_exc()))


def _save_active_untitled(date=None):
    """Names and saves the active untitled tab. Returns the path, or None."""
    text = editor.getText()
    if not text.strip():
        return None
    tab_name = notepad.getCurrentFilename()
    if not is_untitled(tab_name):
        return None
    path = target_path(config["notes_dir"], tab_name, text,
                       date or datetime.date.today().isoformat(),
                       config["extension"], config["max_name_chars"])
    os.makedirs(config["notes_dir"], exist_ok=True)
    notepad.saveAs(path)
    if os.path.isfile(path):
        _log("named  %s -> %s" % (tab_name, os.path.basename(path)))
        _check_saved(path)
        return path
    _log("FAILED to save %s as %s" % (tab_name, path))
    return None


def _handle_active(buffer_id, force=False):
    if not editor.getModify():
        _dirty.pop(buffer_id, None)
        return
    name = notepad.getCurrentFilename()
    if is_untitled(name):
        first_seen = _dirty.setdefault(buffer_id, time.time())
        ready = (editor.getLineCount() >= 2
                 or time.time() - first_seen >= config["name_after_seconds"])
        if force or ready:
            _save_active_untitled()
            _dirty.pop(buffer_id, None)
    elif in_notes_dir(name, config["notes_dir"]):
        notepad.save()
        _dirty.pop(buffer_id, None)
    else:
        _dirty.pop(buffer_id, None)


def _handle_background(buffer_id, active_id, open_ids):
    """A tab that was edited and then switched away from before it was saved."""
    _dirty.pop(buffer_id, None)
    if buffer_id not in open_ids:
        return
    name = notepad.getBufferFilename(buffer_id)
    if not is_untitled(name) and not in_notes_dir(name, config["notes_dir"]):
        return
    notepad.activateBufferID(buffer_id)
    try:
        _handle_active(buffer_id, force=True)
    finally:
        notepad.activateBufferID(active_id)


def _tick():
    active_id = notepad.getCurrentBufferID()
    _handle_active(active_id)
    pending = [buffer_id for buffer_id in list(_dirty) if buffer_id != active_id]
    if pending:
        open_ids = set(entry[1] for entry in notepad.getFiles())
        for buffer_id in pending:
            _handle_background(buffer_id, active_id, open_ids)


def _convert_existing_tabs():
    """One-time pass: gives every already-open untitled tab a name."""
    if not config["convert_existing_tabs"] or os.path.exists(CONVERTED_MARKER):
        return
    saved = empty = failed = 0
    seen = set()
    active_id = notepad.getCurrentBufferID()
    try:
        for name, buffer_id, _index, _view in notepad.getFiles():
            if buffer_id in seen or not is_untitled(name):
                continue
            seen.add(buffer_id)
            try:
                notepad.activateBufferID(buffer_id)
                if not editor.getText().strip():
                    empty += 1
                    continue
                date = _snapshot_date(name) or datetime.date.today().isoformat()
                if _save_active_untitled(date=date):
                    saved += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
                _log("convert error on %s\n%s" % (name, traceback.format_exc()))
    finally:
        notepad.activateBufferID(active_id)
    summary = "untitled=%d saved=%d empty=%d failed=%d" % (len(seen), saved, empty, failed)
    _log("existing tabs converted: " + summary)
    if failed == 0:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(CONVERTED_MARKER, "w", encoding="utf-8") as handle:
            handle.write("%s  %s\n" % (datetime.datetime.now().isoformat(), summary))


def _on_dirty(args):
    try:
        _dirty.setdefault(notepad.getCurrentBufferID(), time.time())
    except Exception:
        pass


def _on_closed(args):
    _dirty.pop(args.get("bufferID"), None)


def _run():
    time.sleep(STARTUP_DELAY_SECONDS)
    try:
        _convert_existing_tabs()
    except Exception:
        _log("convert failed\n" + traceback.format_exc())
    errors = 0
    while True:
        try:
            _tick()
            errors = 0
        except Exception:
            errors += 1
            if errors <= 3:
                _log("tick error\n" + traceback.format_exc())
        # back off if something keeps failing, so the editor stays usable
        time.sleep(config["tick_seconds"] if errors < 20 else 30)


def start():
    global _started, config
    if _started:
        return
    _started = True
    try:
        config = load_config()
    except Exception:
        _log("could not read %s, using defaults\n%s" % (CONFIG_FILE, traceback.format_exc()))
    editor.callback(_on_dirty, [SCINTILLANOTIFICATION.SAVEPOINTLEFT])
    notepad.callback(_on_closed, [NOTIFICATION.FILECLOSED])
    worker = threading.Thread(target=_run, name="autonote", daemon=True)
    worker.start()
    _log("started, notes folder = " + config["notes_dir"])
