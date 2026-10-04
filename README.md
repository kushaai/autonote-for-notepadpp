# AutoNote for Notepad++

Stop saving notes by hand. AutoNote gives every new Notepad++ tab a file name
and keeps it saved, so closing a tab never asks "Save file?" and nothing is
lost when you forget.

It is a small script for the [PythonScript](https://github.com/bruderstein/PythonScript)
plugin. It is not affiliated with or endorsed by the Notepad++ project.

## Contents

- [What it does](#what-it-does)
- [Requirements](#requirements)
- [Install](#install)
- [Using it day to day](#using-it-day-to-day)
- [Naming convention](#naming-convention)
- [Converting tabs you already have open](#converting-tabs-you-already-have-open)
- [Syncing notes to the cloud](#syncing-notes-to-the-cloud)
- [Settings](#settings)
- [Troubleshooting](#troubleshooting)
- [Known limitations](#known-limitations)
- [Uninstall](#uninstall)
- [Tests](#tests)
- [Contributing](#contributing)
- [Author](#author)
- [License](#license)

## What it does

- **Names new tabs for you.** Type in an untitled tab (`new 12`) and it is saved
  into your notes folder as `<date> <first line>.txt`, for example
  `2026-10-04 client call points.txt`.
- **Keeps notes saved.** Any file in the notes folder is saved again about two
  seconds after each edit.
- **Leaves everything else alone.** Files outside the notes folder behave
  exactly as they did before.
- **Works with any cloud drive.** Point the notes folder at a folder synced by
  Google Drive, OneDrive, Dropbox or similar, and your notes are online without
  a sign-in inside Notepad++.

## Requirements

- Windows, Notepad++ 8.x
- PythonScript plugin **3.x** (the Python 3 line). Version 2.x will not work.

Developed on Notepad++ 8.9.2 (64-bit) with PythonScript 3.0.27.

## Install

1. **Install PythonScript 3.x.** In Notepad++ open **Plugins > Plugins Admin**,
   search for "Python Script" and install it. If it offers an older 2.x build,
   take 3.x from the
   [PythonScript releases page](https://github.com/bruderstein/PythonScript/releases)
   instead.
2. **Copy two files** from this repo, `autonote.py` and `startup.py`, into the
   PythonScript user scripts folder. Paste this into the File Explorer address
   bar to open it (create the folder if it does not exist):

   ```
   %APPDATA%\Notepad++\plugins\config\PythonScript\scripts
   ```

   If you already have a `startup.py` there, do not replace it. Add these two
   lines to the end of yours:

   ```python
   import autonote
   autonote.start()
   ```
3. **Turn on start-up loading.** In Notepad++ open
   **Plugins > Python Script > Configuration** and set **Initialisation** to
   `ATSTARTUP`. Without this the script only loads when you run something from
   the Python Script menu.
4. **Restart Notepad++.**

Notes are saved to `Documents\Notepad Notes` unless you choose another folder
in [Settings](#settings).

### Check that it works

1. Press `Ctrl+N` for a new tab.
2. Type a line, press Enter, type a second line.
3. Within two or three seconds the tab title changes from `new 1` to something
   like `2026-10-04 your first line.txt`.
4. Close the tab. Notepad++ does not ask to save, and the file is in your
   notes folder.

If the title does not change, see [Troubleshooting](#troubleshooting).

## Using it day to day

There is nothing to operate. Use Notepad++ the way you already do.

| You want to | Do this |
|---|---|
| Start a note | `Ctrl+N` and type. The first line becomes the file name. |
| Close a note | Close the tab. It is already saved, so there is no prompt. |
| Rename a note | Right-click the tab > **Rename** (or **File > Rename**). Auto-save carries on under the new name. Rename from inside Notepad++, not from File Explorer, while the tab is open. |
| Choose the name yourself before it is saved | Right-click the untitled tab > **Rename** before typing. AutoNote keeps your name instead of using the first line. |
| Organise notes into subfolders | Move files into subfolders of the notes folder. Files in subfolders are auto-saved too. |
| Put an existing file under auto-save | **File > Save As** into the notes folder. |
| Keep a file out of auto-save | Save it anywhere outside the notes folder. AutoNote never saves files outside it. |
| Find an old note | Open the notes folder. Names start with the date, so sorting by name is sorting by date. |

What AutoNote does not touch:

- **Empty tabs.** An untitled tab with no text is never saved.
- **Files outside the notes folder.** Code, configs and anything else you open
  keep the normal Notepad++ behaviour, including the save prompt.

## Naming convention

A new note is named:

```
<date> <first line><extension>
```

for example `2026-10-04 client call points.txt`.

### The parts

| Part | Rule |
|---|---|
| Date | `YYYY-MM-DD`, the day the note was named, in your local time. For tabs converted from an older session it is the day Notepad++ first backed that tab up (see [converting](#converting-tabs-you-already-have-open)). |
| First line | The first line of the note that still has text after cleaning. Blank lines above it are skipped. |
| Extension | `.txt`, or the `extension` setting. |

### How the first line is cleaned

1. Characters Windows does not allow in file names, `\ / : * ? " < > |`, and
   control characters such as tabs, are each replaced by a space.
2. Runs of spaces are collapsed to one, and spaces at both ends are removed.
3. The result is cut to 60 characters (the `max_name_chars` setting).
4. Dots and spaces left at the end are removed.
5. If nothing is left, for example a line of only `???`, the next line is
   tried. If no line gives a name, the word `note` is used.

Letters in any script are kept, so a first line in Hindi, Chinese or Arabic
becomes the file name as written.

### When the name is chosen

A tab is named at the first of these:

- it has a second line (you pressed Enter after the first line), or
- it has been unsaved for 10 seconds (the `name_after_seconds` setting), or
- you switch to another tab.

The wait exists so the name is not taken from a half-typed first line.

A name is chosen **once**. Changing the first line later does not rename the
file; rename it yourself from inside Notepad++ if you want a different name.

### Tabs you renamed yourself

If an untitled tab no longer has a default name like `new 12`, because you
renamed it, AutoNote uses your name and adds no date.

- `Innovative Ideas` becomes `Innovative Ideas.txt`.
- A name that ends in a real extension keeps it: `todo.md` stays `todo.md`.
  An extension here means a dot followed by 1 to 5 letters or digits.
- A dot inside a name is not mistaken for an extension:
  `v1.2 release notes` becomes `v1.2 release notes.txt`.

### Name clashes

An existing file is never overwritten. If the name is taken, a number is added:

```
2026-10-04 meeting.txt
2026-10-04 meeting (2).txt
2026-10-04 meeting (3).txt
```

### Examples

| Tab | Text starts with | File name |
|---|---|---|
| `new 12` | `client call points` | `2026-10-04 client call points.txt` |
| `new 3` | two blank lines, then `real title` | `2026-10-04 real title.txt` |
| `new 7` | `fix: a/b test?` | `2026-10-04 fix a b test.txt` |
| `new 8` | `???` then `***` | `2026-10-04 note.txt` |
| `new 9` | `आज के काम` | `2026-10-04 आज के काम.txt` |
| `Innovative Ideas` | anything | `Innovative Ideas.txt` |
| `todo.md` | anything | `todo.md` |

## Converting tabs you already have open

Many people keep dozens of unsaved `new N` tabs open for months. AutoNote can
name and save all of them in one pass. This is **off by default** because it
renames every untitled tab at once.

### Before you start

- **Make a backup.** Close Notepad++ and copy the whole folder
  `%APPDATA%\Notepad++` somewhere safe. It holds your open tabs and their
  unsaved text. With the copy you can go back to exactly where you were.
- Check that **Settings > Preferences > Backup > Enable session snapshot and
  periodic backup** is on. It is on by default, and it is how Notepad++ keeps
  unsaved tabs between restarts. AutoNote also reads the tab dates from it.

### Steps

1. In the scripts folder (`%APPDATA%\Notepad++\plugins\config\PythonScript\scripts`),
   create `autonote.json`, or edit it if you have one, so it contains:

   ```json
   {
     "convert_existing_tabs": true
   }
   ```

   Add `"notes_dir"` as well if you want a folder other than the default.
2. Restart Notepad++.
3. Wait and do not type. A few seconds after start-up, Notepad++ flips through
   the untitled tabs one by one while each is saved. About 300 tabs take
   roughly a minute.
4. When it stops, every untitled tab that had text now shows a file name, and
   the files are in the notes folder.

### What happens to each tab

| Tab | Result |
|---|---|
| Untitled, with text | Saved as `<date> <first line>.txt`, where the date is the day Notepad++ first backed the tab up. If that date cannot be found, today's date is used. |
| Untitled, renamed by you | Saved under your name, with no date. |
| Untitled, empty or only spaces | Left as it is. |
| A file that already has a path | Not touched, even if it has unsaved changes. |

### Checking the result

Open `%LOCALAPPDATA%\AutoNote\autonote.log`. The pass ends with one line:

```
existing tabs converted: untitled=287 saved=287 empty=0 failed=0
```

- `saved` is the number of files created. It should equal `untitled` minus `empty`.
- `failed` should be `0`. If it is not, the lines above it say which tabs failed
  and why, and the pass runs again at the next start for the tabs still untitled.
- A line starting with `WARNING` names a note that was not saved as Unicode.
  See [Known limitations](#known-limitations).

### It runs only once

After a pass with no failures, AutoNote writes
`%LOCALAPPDATA%\AutoNote\existing-tabs-converted.txt` and never repeats the
pass, even if the setting stays `true`. To run it again on purpose, delete that
file and restart Notepad++.

### Going back

1. Close Notepad++.
2. Replace `%APPDATA%\Notepad++` with the copy you made.
3. Make sure `convert_existing_tabs` is `false` in `autonote.json`, so the pass
   does not run again.
4. Start Notepad++. Your tabs are untitled again.

The files created in the notes folder stay there; delete them yourself if you
do not want them.

## Syncing notes to the cloud

AutoNote only writes files to a folder. Any sync app that watches that folder
puts your notes online.

- **Google Drive for desktop:** tray icon > gear > **Preferences** >
  **My Computer** > **Add folder**, choose the notes folder, tick
  **Sync with Google Drive**.
- **OneDrive, Dropbox and similar:** set `notes_dir` to a folder inside the
  synced folder, for example `C:\Users\you\OneDrive\Notes`.

Prefer a notes folder on a normal local disk that the sync app mirrors, over a
virtual drive letter created by the sync app. A virtual drive is not there
until the sync app has started, and saving fails if Notepad++ starts first.

## Settings

Copy `autonote.example.json` to the scripts folder as `autonote.json` and edit
it. Every key is optional; leave out the ones you do not want to change.

| Key | Default | Meaning |
|---|---|---|
| `notes_dir` | `Documents\Notepad Notes` | Folder notes are saved in. `~` and `%VARS%` are expanded. Created if missing. |
| `tick_seconds` | `2` | How often the active tab is checked. |
| `name_after_seconds` | `10` | A tab with only one line is named after this long. |
| `max_name_chars` | `60` | Longest first-line text used in a file name. |
| `extension` | `.txt` | Extension for new notes: a dot and 1 to 5 letters or digits. |
| `convert_existing_tabs` | `false` | Name and save every untitled tab already open. Runs once. |

In JSON a backslash is written twice: `"notes_dir": "D:\\Notes"`.

Restart Notepad++ after changing settings. A key with the wrong type, such as
text where a number is expected, is ignored and the default is used. If the
file is not valid JSON, all defaults are used and the log says so.

## Troubleshooting

**The tab title never changes.**

- Check **Plugins > Python Script > Configuration > Initialisation** is
  `ATSTARTUP`, then restart Notepad++.
- Check both `autonote.py` and `startup.py` are in the user scripts folder, not
  in the plugin's own `scripts` folder under `Program Files`.
- Open `%LOCALAPPDATA%\AutoNote\autonote.log`. A line `started, notes folder = ...`
  appears on every start. If the file or that line is missing, the script did
  not load: open **Plugins > Python Script > Show Console** and read the error.
- If the console banner says Python 2.7, PythonScript 2.x is installed.
  Install 3.x.

**Notes are going to the wrong folder.** The folder in use is on the `started`
line of the log. If it is not the one in `autonote.json`, the file is not valid
JSON (often a single backslash in the path) and defaults were used.

**Notepad++ still asked me to save.** A tab with only one line, closed within
`name_after_seconds` of typing, has not been named yet. Lower that setting if
this happens often.

**A note shows wrong characters after saving.** See the codepage note below.

## Known limitations

- Close a one-line tab within a few seconds of typing and Notepad++ may still
  ask to save once.
- A tab set to a legacy codepage (**Encoding > Character sets**) is written in
  that codepage, which cannot hold every character. AutoNote cannot prevent
  this, but it logs a `WARNING` line naming the file. Use
  **Encoding > Convert to UTF-8** on that tab.
- New notes get one extension, so a tab holding JSON or SQL loses its syntax
  highlighting once it is saved as `.txt`. Set the language again from the
  **Language** menu, or rename the file with the right extension.
- A tab edited and left within two seconds is saved by briefly switching to it
  and back, which shows as a quick flicker.
- Portable Notepad++ installs keep their config next to `notepad++.exe`, so
  the scripts folder is there instead of under `%APPDATA%`.

## Log

`%LOCALAPPDATA%\AutoNote\autonote.log` records each file that was named, plus
any warnings or errors. It contains file names, never note text. It is not
inside the notes folder, so it is not synced.

## Uninstall

1. Delete `autonote.py`, and `autonote.json` if you made one, from the scripts
   folder.
2. Delete `startup.py` from the same folder, or remove the two AutoNote lines
   from it if it holds other things.
3. Restart Notepad++.

Your notes stay where they are. They are ordinary text files.

## Tests

The naming, settings and encoding checks run without Notepad++:

```
python -m unittest discover -s tests
```

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Author

Created and maintained by **Himanshu Dadhich**, published under
[Kusha AI](https://github.com/kushaai).

## License

MIT. See [LICENSE](LICENSE).
