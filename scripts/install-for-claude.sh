#!/usr/bin/env sh
# Link this checkout's skill trees into Claude Code on macOS or Linux, the
# counterpart of install-for-claude.ps1: ~/.claude/skills/<name> -> <repo>/skills/<name>,
# plus ~/.claude/scripts and ~/.claude/tools so the skills' ../../scripts and
# ../../tools references resolve through the links. Nothing is copied; a
# `git pull` is visible to Claude Code at the next session. Existing links are
# replaced; real directories with the same name are reported, never touched.
#
# Usage: sh scripts/install-for-claude.sh [claude-home]   (default: $HOME/.claude)
set -eu
repo=$(cd "$(dirname "$0")/.." && pwd)
claude_home=${1:-$HOME/.claude}

link() { # link <path> <target>
    if [ -e "$1" ] && [ ! -L "$1" ]; then
        echo "    real directory in the way, not touched: $1" >&2
        return
    fi
    ln -sfn "$2" "$1"
    echo "    linked: $1 -> $2"
}

echo "==> z80-skills -> Claude Code (symlinks)"
mkdir -p "$claude_home/skills"
for skill in "$repo"/skills/*/; do
    skill=${skill%/}
    [ -f "$skill/SKILL.md" ] || continue
    link "$claude_home/skills/$(basename "$skill")" "$skill"
done
link "$claude_home/scripts" "$repo/scripts"
link "$claude_home/tools" "$repo/tools"
echo "==> done. Open a new Claude Code session to reload the skill catalog."
