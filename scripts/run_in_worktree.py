#!/usr/bin/env python3
"""Run one command only in a verified disposable Git worktree."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


class GateError(RuntimeError):
    pass


GIT_ROUTE_ENV = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
)


def clean_env(cwd: Path) -> dict[str, str]:
    env = os.environ.copy()
    for name in GIT_ROUTE_ENV:
        env.pop(name, None)
    env.pop("OLDPWD", None)
    env["PWD"] = str(cwd)
    return env


def git_value(root: Path, *arguments: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(root), "rev-parse", *arguments],
        text=True,
        capture_output=True,
        env=clean_env(root),
    )
    if proc.returncode:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise GateError(f"{root}: {detail or 'not a Git worktree'}")
    return proc.stdout.strip()


def worktree_root(path: str, label: str) -> Path:
    try:
        root = Path(path).expanduser().resolve(strict=True)
    except OSError as exc:
        raise GateError(f"{label} path is unavailable: {path}: {exc}") from exc
    if not root.is_dir():
        raise GateError(f"{label} path is not a directory: {root}")
    top = Path(git_value(root, "--show-toplevel")).resolve()
    if top != root:
        raise GateError(f"{label} must be the Git worktree root: {root} != {top}")
    return root


def common_git_dir(root: Path) -> Path:
    value = Path(git_value(root, "--git-common-dir"))
    return (value if value.is_absolute() else root / value).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail closed unless the command target is a distinct worktree."
    )
    parser.add_argument("--primary", required=True, help="Primary Git worktree root")
    parser.add_argument("--worktree", required=True, help="Disposable Git worktree root")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command[:1] == ["--"]:
        args.command = args.command[1:]
    if not args.command:
        parser.error("a command is required after --")
    return args


def main() -> int:
    args = parse_args()
    try:
        primary = worktree_root(args.primary, "primary")
        worktree = worktree_root(args.worktree, "disposable worktree")
        if primary == worktree:
            raise GateError("refusing to run a gate in the primary worktree")
        try:
            worktree.relative_to(primary)
        except ValueError:
            pass
        else:
            raise GateError("disposable worktree must be outside the primary tree")
        if common_git_dir(primary) != common_git_dir(worktree):
            raise GateError("primary and disposable worktree are not from the same repository")
        if git_value(worktree, "--abbrev-ref", "HEAD") != "HEAD":
            raise GateError("disposable worktree must be detached")
        if git_value(primary, "HEAD") != git_value(worktree, "HEAD"):
            raise GateError("primary and disposable worktree must start at the same revision")
        return subprocess.run(
            args.command,
            cwd=str(worktree),
            env=clean_env(worktree),
        ).returncode
    except GateError as exc:
        print(f"gate refused: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"gate failed to start: {exc}", file=sys.stderr)
        return 127


if __name__ == "__main__":
    raise SystemExit(main())
