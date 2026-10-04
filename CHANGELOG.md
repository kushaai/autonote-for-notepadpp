# Changelog

All notable changes to this project are recorded here. Versions follow
[semantic versioning](https://semver.org/).

## [Unreleased]

### Added

- Demo animation at the top of the README, with the script that renders it
  in `media/`.

## [0.1.0] — 2026-10-04

First public release.

### Added

- Untitled tabs are named and saved into a notes folder as
  `<date> <first line>.txt` once the first line is finished.
- Files in the notes folder are saved again about two seconds after each edit,
  so closing a tab never asks to save.
- Tabs renamed by hand keep their name; existing files are never overwritten.
- Optional `autonote.json` settings: notes folder, timings, name length,
  extension.
- Optional one-time pass that names every untitled tab already open, using the
  date Notepad++ first backed the tab up.
- Warning in the log when a note could not be saved as Unicode.
- Unit tests for naming, settings and the Unicode save check.
