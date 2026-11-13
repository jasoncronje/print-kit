#!/bin/sh
# Run a print-kit Python script with the first working Python 3.9+ on this machine.
#
#     sh py.sh <script.py> [args...]
#
# Tries $PRINT_KIT_PYTHON, python3, python, then the Windows launcher (py -3), so the same
# command works on macOS, Linux and Windows (Git Bash). Skips two stand-ins that aren't Python:
# macOS's /usr/bin/python3 before the Command Line Tools are installed (running it pops up an
# install dialog), and Windows' python3/python Store aliases (they only print a hint).
# With no Python, the session hook still gets a message telling Claude how to install one;
# anything else exits 127.

works() {
    command -v "$1" >/dev/null 2>&1 || return 1
    if [ "$(command -v "$1")" = /usr/bin/python3 ] && ! xcode-select -p >/dev/null 2>&1; then
        return 1
    fi
    "$@" -c 'import sys; sys.exit(sys.version_info < (3, 9))' >/dev/null 2>&1
}

for cand in "$PRINT_KIT_PYTHON" python3 python; do
    [ -n "$cand" ] && works "$cand" && exec "$cand" "$@"
done
works py -3 && exec py -3 "$@"

case "$1" in
*session_context.py)
    printf '%s\n' '{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "print-kit is installed, but this machine has no Python 3.9+, which its tools need. Before any print-kit work, tell the user and offer to install it. macOS: `xcode-select --install` (a system dialog; about 5 min), or `brew install python` if Homebrew is there. Windows: `winget install -e --id Python.Python.3.13 --scope user`, then restart Claude Code so PATH picks it up. Ubuntu/Debian: the user runs `sudo apt install -y python3` in a terminal. Then run /print-kit:setup."}}'
    exit 0 ;;
esac
echo "print-kit: no Python 3.9+ found (tried python3, python, py -3). Install one, then try again." >&2
exit 127
