#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

C_STRING_RE = re.compile(r'"((?:[^"\\]|\\.)+)"')
ASM_STRING_RE = re.compile(r"\b(?:db|defb)\s+\"([^\"]+)\"", re.IGNORECASE)
PREFERRED_DIRS = ("src", "asm", "include", "overlay")


def add_hit(store: dict[str, list[str]], key: str, where: str) -> None:
    if len(key) < 4:
        return
    store[key].append(where)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    hits: dict[str, list[str]] = defaultdict(list)
    bases = [root / name for name in PREFERRED_DIRS if (root / name).exists()]
    if not bases:
        bases = [root]

    for base in bases:
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".c", ".h", ".asm", ".inc", ".s"}:
                continue
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            for lineno, line in enumerate(lines, start=1):
                if line.lstrip().startswith("#include"):
                    continue
                rel = f"{path.relative_to(root)}:{lineno}"
                for match in C_STRING_RE.findall(line):
                    add_hit(hits, match, rel)
                for match in ASM_STRING_RE.findall(line):
                    add_hit(hits, match, rel)

    duplicates = sorted(
        ((literal, places) for literal, places in hits.items() if len(places) > 1),
        key=lambda item: (-len(item[1]), -len(item[0]), item[0]),
    )

    if not duplicates:
        print("none")
        return 0

    for literal, places in duplicates[:40]:
        print(f"{len(places)}x | {literal}")
        for place in places[:8]:
            print(f"  {place}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
