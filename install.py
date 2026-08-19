#!/usr/bin/env python3
"""Put claude-usage on your PATH and print it on every new shell.

Two ways in, same result:

    ./install.py                                    from a checkout
    curl -fsSL <raw>/install.py | python3           no checkout, so it clones first

Every step is idempotent: rerunning this updates an existing install instead of
duplicating it.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/anteloio/claude-usage.git"
COMMAND = "claude-usage"

CLONE_DIR = Path(os.environ.get("CLAUDE_USAGE_DIR", Path.home() / ".local/share/claude-usage"))
BIN_DIR = Path.home() / ".local/bin"
TARGET = BIN_DIR / COMMAND
ZSHRC = Path.home() / ".zshrc"

# Sentinels, so a rerun can find its own block and replace it.
BEGIN = f"# {COMMAND} >>> plan usage on every new shell, served from cache"
END = f"# {COMMAND} <<<"
HOOK = f"""
{BEGIN}
alias cu='{COMMAND}'
if [[ -o interactive ]] && command -v {COMMAND} >/dev/null; then
  {COMMAND}
fi
{END}
"""


def git(*args):
    subprocess.run(["git", *args], check=True)


def find_checkout():
    """The repo this script sits in, or None when piped from curl (argv[0] is then "-")."""
    script = Path(sys.argv[0])
    if not script.is_file():
        return None
    repo = script.resolve().parent
    return repo if (repo / COMMAND).is_file() else None


def clone_or_update():
    """Fetch the repo ourselves, since there is nothing on disk to install from."""
    if (CLONE_DIR / ".git").is_dir():
        git("-C", str(CLONE_DIR), "pull", "--ff-only", "--quiet")
        print(f"updated {CLONE_DIR}")
    else:
        CLONE_DIR.parent.mkdir(parents=True, exist_ok=True)
        git("clone", "--quiet", "--depth", "1", REPO_URL, str(CLONE_DIR))
        print(f"cloned into {CLONE_DIR}")
    return CLONE_DIR


def link_command(source):
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    command = source / COMMAND
    command.chmod(0o755)
    if TARGET.is_symlink() or TARGET.exists():
        TARGET.unlink()
    TARGET.symlink_to(command)
    print(f"linked {TARGET} -> {command}")

    if str(BIN_DIR) not in os.environ.get("PATH", "").split(os.pathsep):
        print(f"warning: {BIN_DIR} is not on your PATH")


def find_old_hook(rc):
    """The block a previous run wrote, sentinels or - before those existed - up to its `fi`."""
    between_sentinels = rf"\n?{re.escape(BEGIN)}.*?{re.escape(END)}\n?"
    up_to_fi = rf"\n?# {re.escape(COMMAND)}:.*?\nfi\n?"
    return re.search(between_sentinels, rc, re.DOTALL) or re.search(up_to_fi, rc, re.DOTALL)


def add_shell_hook():
    rc = ZSHRC.read_text() if ZSHRC.is_file() else ""
    old = find_old_hook(rc)

    if old and old.group() == HOOK:
        print(f"shell hook already current in {ZSHRC}")
        return

    ZSHRC.write_text(rc[: old.start()] + HOOK + rc[old.end() :] if old else rc + HOOK)
    print(f"{'replaced the outdated' if old else 'added the'} shell hook in {ZSHRC}")


def main():
    source = find_checkout() or clone_or_update()
    link_command(source)
    add_shell_hook()
    print()
    subprocess.run([str(TARGET)])


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as err:
        sys.exit(f"{COMMAND}: {' '.join(err.cmd)} failed")
