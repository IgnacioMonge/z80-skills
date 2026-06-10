#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

TEXT_EXTS = {
    ".asm",
    ".c",
    ".h",
    ".i",
    ".inc",
    ".lst",
    ".map",
    ".mk",
    ".opt",
    ".ps1",
    ".rul",
    ".s",
    ".sh",
    ".txt",
}
TOP_LEVEL_FILES = {"Makefile", "makefile", "build.sh", "build.ps1"}
PREFERRED_DIRS = ("src", "asm", "include", "overlay")

PATTERNS = {
    "toolchain": [
        r"\bzcc\b",
        r"\bzsdcc\b",
        r"\bsdcc\b",
        r"\bsccz80\b",
        r"\bz80asm\b",
        r"\bz80n\b",
        r"-compiler=sdcc",
        r"-clib=sdcc_iy",
        r"-startup=\d+",
        r"--fomit-frame-pointer",
        r"--opt-code-size",
        r"-zorg=\d+",
        r"custom-copt-rules",
    ],
    "calling_conventions": [
        r"__z88dk_callee",
        r"__z88dk_fastcall",
        r"__naked",
    ],
    "interrupts": [
        r"\bim\s+1\b",
        r"\bim\s+2\b",
        r"\bdi\b",
        r"\bei\b",
    ],
    "fixed_address_clues": [
        r"\$5B[0-9A-Fa-f]{2}",
        r"\$5C[0-9A-Fa-f]{2}",
        r"\$FF58\b",
        r"\boverlay_slot\b",
        r"\bring_buffer\b",
        r"\bprinter buffer\b",
    ],
}


def source_roots(root: Path) -> list[Path]:
    roots = [root / name for name in PREFERRED_DIRS if (root / name).exists()]
    return roots or [root]


def text_files(root: Path):
    for name in TOP_LEVEL_FILES:
        path = root / name
        if path.is_file():
            yield path
    for base in source_roots(root):
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() in TEXT_EXTS:
                yield path


def find_artifacts(root: Path, suffix: str) -> list[Path]:
    return sorted(root.rglob(f"*{suffix}"))


def collect_hits(root: Path, patterns: list[str], limit: int = 8) -> list[str]:
    hits: list[str] = []
    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    for path in text_files(root):
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, start=1):
            if len(line) > 300:
                continue
            if any(regex.search(line) for regex in compiled):
                rel = path.relative_to(root)
                hits.append(f"{rel}:{lineno}: {line.strip()}")
                if len(hits) >= limit:
                    return hits
    return hits


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    print(f"root: {root}")
    for suffix in (".map", ".lst", ".sym", ".opt", ".rul"):
        matches = find_artifacts(root, suffix)
        print(f"{suffix} files: {len(matches)}")
        for path in matches[:5]:
            print(f"  - {path.relative_to(root)}")

    for section, patterns in PATTERNS.items():
        print(f"\n[{section}]")
        hits = collect_hits(root, patterns)
        if not hits:
            print("  none")
            continue
        for hit in hits:
            print(f"  {hit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
