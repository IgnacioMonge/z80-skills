#!/usr/bin/env python3
"""Extract a conservative ASM call graph from asm/lst files."""
from __future__ import annotations

import argparse
import os
import sys
import json
import re
from pathlib import Path

LABEL = re.compile(r"^\s*([A-Za-z_.$@?][\w.$@?]*):")
CALL = re.compile(
    r"\b(call|jp)\s+(?:(?:z|nz|c|nc|m|p|pe|po)\s*,\s*)?"
    r"([A-Za-z_.$@?][\w.$@?]*)",
    re.I,
)
EXTS = {".asm", ".s", ".inc", ".lst", ".lis"}
IGNORE_DIRS = {".git", ".hg", ".svn", "__pycache__", "node_modules", ".mex"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--limit", type=int, default=500, help="maximum edges to emit; 0 means unlimited")
    ap.add_argument("--exclude-dir", action="append", default=[], help="extra directory name to skip")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    if not root.exists():
        raise SystemExit(f"root not found: {root}")
    ignore_dirs = IGNORE_DIRS | set(args.exclude_dir or [])
    emit_limit = None if args.limit <= 0 else args.limit
    edges = []
    for p in root.rglob("*"):
        if any(part in ignore_dirs for part in p.parts) or not p.is_file() or p.suffix.lower() not in EXTS:
            continue
        current = None
        for n, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
            m = LABEL.match(line)
            if m:
                current = m.group(1)
            m = CALL.search(line.split(";", 1)[0])
            if m and current:
                edges.append({"file": p.relative_to(root).as_posix(), "line": n, "from": current, "op": m.group(1).lower(), "to": m.group(2)})
    if args.json:
        shown = edges if emit_limit is None else edges[:emit_limit]
        print(json.dumps({"edge_count": len(edges), "truncated": emit_limit is not None and len(edges) > emit_limit, "edges": shown}, indent=2))
        return
    shown = edges if emit_limit is None else edges[:emit_limit]
    for e in shown:
        print(f"{e['file']}:{e['line']} {e['from']} --{e['op']}--> {e['to']}")
    if emit_limit is not None and len(edges) > emit_limit:
        print(f"TRUNCATED {len(edges)-emit_limit} edges")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        pass
