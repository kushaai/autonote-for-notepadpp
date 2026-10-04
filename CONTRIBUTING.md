# Contributing

Thanks for helping. This is a small project, so the process is light.

## Reporting a problem

Open an issue with:

- your Notepad++ version and PythonScript version
- what you did, what you expected, what happened
- the relevant lines from `%LOCALAPPDATA%\AutoNote\autonote.log`

Do not paste the text of your notes. File names appear in the log, so remove
any that are private.

## Proposing a change

1. Open an issue first for anything larger than a small fix, so the approach
   can be agreed before you write it.
2. Fork the repo and create a branch: `fix/<short-name>` or `feature/<short-name>`.
3. Keep one change per pull request.
4. Add or update a test in `tests/` when you touch naming, settings or the
   encoding check, and run:

   ```
   python -m unittest discover -s tests
   ```

5. For anything that touches saving, also try it by hand in Notepad++ and say
   in the pull request what you tried.

## Ground rules for the code

- **Never overwrite or delete a user's file.** New notes always get a free
  name; nothing outside the notes folder is saved by the script.
- **Never log note text.** File names only.
- No dependencies beyond the Python standard library and the `Npp` module that
  PythonScript provides.
- Keep logic that does not need Notepad++ in plain functions, so it can be
  tested without the editor.

## License

By contributing you agree that your contribution is released under the MIT
License that covers this project.
