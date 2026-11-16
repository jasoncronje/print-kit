# Installing print-kit (instructions for the agent)

You are Claude Code, and the user asked you to install print-kit: a plugin for designing
OpenSCAD parts for their 3D printer. Do the whole install in this session. Tell the user in one
line what you're about to do, then work through the steps. Ask only what the steps say to ask.

## 1. Add the plugin

Run these in the shell (they are the same as typing `/plugin ...` in Claude Code):

```bash
claude plugin marketplace add jasoncronje/print-kit
claude plugin install print-kit@print-kit
```

"Already added" or "already installed" is fine: carry on. If `claude` isn't found in the shell,
ask the user to type these two lines into Claude Code themselves, then continue:

```
/plugin marketplace add jasoncronje/print-kit
/plugin install print-kit@print-kit
```

## 2. Find the installed plugin

The plugin's skills only load in a new session, so you will follow its setup guide from disk.
Find the plugin folder (the one holding `skills/`, `tools/` and `scripts/`):

```bash
ls -d ~/.claude/plugins/cache/print-kit/print-kit/*/
```

Call that folder ROOT. More than one: use the newest.

## 3. Run setup now

Read `ROOT/skills/setup/SKILL.md` and follow it from start to finish in this session, in the
folder the user opened. Wherever it says `${CLAUDE_PLUGIN_ROOT}`, use ROOT. Where it points to
another file in the plugin (for example `skills/measure-and-fit/calibration.md`), read that
file from ROOT too.

Setup checks for Python and OpenSCAD and offers to install what's missing (no admin rights),
finds the slicer, asks about the printer one question at a time, writes `print-kit.json`, and
offers an optional calibration print.

## 4. Hand over

When setup is done, tell the user:

- print-kit is installed and set up, and what was written where, in one short list.
- **Restart Claude Code in this folder** so the plugin loads. Until then its commands
  (`/print-kit:setup`) and design rules aren't active.
- After the restart, the example requests from setup's last step.

If a step fails, show the one key error line and what you tried, and point the user to
"Install by hand" in https://github.com/jasoncronje/print-kit#install.
