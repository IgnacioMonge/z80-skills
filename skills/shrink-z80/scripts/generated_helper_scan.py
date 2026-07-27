#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from scan_common import ASM_EXTS, LISTING_EXTS, branch_targets, map_symbol_is_runtime, rel_path, resolve_target_scope, source_kind, print_scope

SYMBOL_RE = re.compile(r"^(\S+)\s*=\s*\$([0-9A-Fa-f]+)\s*;")
HELPER_RE = re.compile(r"(__mul|__div|__mod|l_(?:mul|mult|div|mod|long)|printf|sprintf|snprintf|scanf|malloc|free|strlen|strcmp|strcpy|strcat|memcpy|memset)", re.IGNORECASE)


def map_helpers(map_path: Path | None) -> set[str]:
    if not map_path or not map_path.exists():
        return set()
    helpers: set[str] = set()
    for line in map_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = SYMBOL_RE.match(line)
        if m and map_symbol_is_runtime(line) and HELPER_RE.search(m.group(1)):
            helpers.add(m.group(1))
    return helpers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", nargs="?", default=".")
    parser.add_argument("map", nargs="?")
    args = parser.parse_args()
    target = Path(args.target).resolve()
    map_path = Path(args.map).resolve() if args.map else None
    scope = resolve_target_scope(target, ASM_EXTS | LISTING_EXTS)
    print_scope(scope)
    helpers = map_helpers(map_path)
    if helpers:
        print(f"map_helpers: {len(helpers)}")
    else:
        print("map_helpers: none_or_no_map")

    hits: dict[str, list[str]] = {}
    for path in scope.files:
        kind = source_kind(path, scope.base)
        text = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for lineno, line in enumerate(text, 1):
            for target_name in branch_targets(line):
                if HELPER_RE.search(target_name) or target_name in helpers:
                    hits.setdefault(target_name, []).append(f"[{kind}] {rel_path(path, scope.base)}:{lineno}: {line.strip()}")

    print("\n[generated_helper_calls]")
    if not hits:
        print("none")
    else:
        for name in sorted(hits):
            in_map = "yes" if name in helpers else "unknown"
            print(f"{name}: in_map={in_map}")
            for row in hits[name][:12]:
                print(f"  {row}")
    print("note: generated/listing hits locate byte evidence; source-level cause still needs map/listing/source correlation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
