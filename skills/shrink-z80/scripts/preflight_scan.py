#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from scan_common import (
    BINARY_ARTIFACT_EXTS,
    BUILD_EXTS,
    TEXT_EXTS,
    collect_pattern_hits,
    print_scope,
    rel_path,
    resolve_scope,
)

PATTERNS = {
    "build_flags": [
        r"\bzcc\b", r"\bzsdcc\b", r"\bsdcc\b", r"\bsccz80\b", r"-compiler=sdcc", r"-compiler=sccz80",
        r"-clib=sdcc_iy", r"-startup=\d+", r"--sdcccall\s*\d+", r"--reserve-regs-iy",
        r"--max-allocs-per-node", r"--peep-asm", r"--list\b", r"--fomit-frame-pointer",
        r"--opt-code-size", r"-SO\d", r"-zorg=\d+", r"custom-copt-rules",
    ],
    "artifacts_and_rules": [
        r"\.map\b", r"\.lst\b", r"\.lis\b", r"\.sym\b", r"\.opt\b", r"\.rul\b",
        r"\.rel\b", r"\.ihx\b", r"\.lk\b", r"\.noi\b", r"\.mem\b",
        r"CRT_STACK_SIZE", r"z88dk-zx0", r"z88dk-zx7", r"\bzx0\b", r"\bzx7\b",
        r"\blzsa\b", r"\brle\b",
    ],
}
ARTIFACT_EXTS = {".map", ".lst", ".lis", ".sym", ".opt", ".rul", ".rel", ".ihx", ".lk", ".noi", ".mem"}


def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    scope = resolve_scope(target, TEXT_EXTS | BUILD_EXTS)
    print_scope(scope)

    for suffix in sorted(ARTIFACT_EXTS):
        matches = [path for path in scope.files if path.suffix.lower() == suffix]
        print(f"{suffix} files: {len(matches)}")
        for path in matches[:8]:
            print(f"  - {rel_path(path, scope.base)}")

    binary = [path for path in scope.files if path.suffix.lower() in BINARY_ARTIFACT_EXTS]
    print("\n[binary_artifacts]")
    if not binary:
        print("  none")
    else:
        for path in sorted(binary):
            stat = path.stat()
            print(f"  {rel_path(path, scope.base)} size={stat.st_size} mtime={int(stat.st_mtime)}")

    maps = [path for path in scope.files if path.suffix.lower() == ".map"]
    if len(maps) > 1:
        print("\n[map_candidates]")
        for path in sorted(maps):
            stat = path.stat()
            print(f"  {rel_path(path, scope.base)} size={stat.st_size} mtime={int(stat.st_mtime)}")
        print("  note: multiple maps found; main agent must choose one explicitly before byte claims")

    for section, patterns in PATTERNS.items():
        print(f"\n[{section}]")
        hits = collect_pattern_hits(
            scope.files,
            scope.base,
            patterns,
            limit=20,
            excluded_exts=BINARY_ARTIFACT_EXTS,
        )
        if not hits:
            print("  none")
            continue
        for hit in hits:
            print(f"  {hit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
