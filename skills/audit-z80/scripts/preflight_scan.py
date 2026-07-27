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
    ".sym",
    ".sh",
    ".txt",
    ".bat",
    ".cmd",
    ".cfg",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".def",
    ".z80",
    ".a80",
    ".mac",
    ".bas",
}
TOP_LEVEL_FILES = {"Makefile", "makefile", "build.sh", "build.ps1", "CMakeLists.txt"}
PREFERRED_DIRS = ("src", "asm", "include", "overlay")
ARTIFACT_DIRS = ("build", "out", "obj", "gen", "generated", "dist")
SKIP_DIRS = {".git", ".svn", ".hg", ".venv", "venv", "node_modules", "__pycache__", "third_party", "vendor"}
MAX_BYTES = 2_000_000

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
        r"--sdcccall\s*\d+",
        r"--reserve-regs-iy",
        r"--fno-omit-frame-pointer",
        r"--fomit-frame-pointer",
        r"--opt-code-size",
        r"--max-allocs-per-node",
        r"--peep-asm",
        r"--list\b",
        r"-zorg=\d+",
        r"custom-copt-rules",
    ],
    "calling_conventions": [
        r"__z88dk_callee",
        r"__z88dk_fastcall",
        r"__naked",
        r"__smallc",
        r"__sdcccall\s*\(\s*[01]\s*\)",
    ],
    "interrupts": [
        r"\bim\s+1\b",
        r"\bim\s+2\b",
        r"\bdi\b",
        r"\bei\b",
    ],
    "fixed_address_clues": [
        r"\$4000\b",
        r"\$5800\b",
        r"\$5B[0-9A-Fa-f]{2}",
        r"\$5C[0-9A-Fa-f]{2}",
        r"\$FF58\b",
        r"\boverlay_slot\b",
        r"\bring_buffer\b",
        r"\bprinter buffer\b",
    ],
    "inline_asm": [
        r"__asm\b",
        r"__endasm\b",
        r"#asm\b",
        r"#endasm\b",
    ],
    "firmware_esxdos_divmmc": [
        r"\brst\s+(?:8|\$08|0x08|08h)\b",
        r"\besxDOS\b",
        r"\besxdos\b",
        r"\bdivMMC\b",
        r"\bdot command\b",
        r"\bm_getsetdrv\b",
        r"\bf_open\b",
        r"\bf_read\b",
        r"\bf_write\b",
        r"\bf_close\b",
    ],
    "overlays_banks": [
        r"\boverlay\b",
        r"\bbank(ed|ing)?\b",
        r"\bpaged\b",
        r"\bslot\b",
    ],
    "contention_timing": [
        r"\$40[0-9A-Fa-f]{2}",
        r"\$5[0-7][0-9A-Fa-f]{2}",
        r"\b0x40[0-9A-Fa-f]{2}",
        r"\b0x5[0-7][0-9A-Fa-f]{2}",
        r"\bport\s+\$?fe\b",
        r"\bFRAMES\b",
        r"\bfast\b",
        r"\buart\b",
        r"\baudio\b",
        r"\bbeep\b",
    ],
}


def recognized_dirs(root: Path) -> list[Path]:
    return [root / name for name in (*PREFERRED_DIRS, *ARTIFACT_DIRS) if (root / name).exists()]


def skip_path(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        parts = path.parts
    return any(part in SKIP_DIRS for part in parts)


def text_files(root: Path):
    if root.is_file():
        if root.suffix.lower() in TEXT_EXTS and root.stat().st_size <= MAX_BYTES:
            yield root
        return
    for path in root.rglob("*"):
        if skip_path(path, root) or not path.is_file():
            continue
        if path.name in TOP_LEVEL_FILES or path.suffix.lower() in TEXT_EXTS:
            if path.stat().st_size <= MAX_BYTES:
                yield path


def find_artifacts(root: Path, suffix: str) -> list[Path]:
    return sorted(p for p in root.rglob(f"*{suffix}") if not skip_path(p, root))


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
    files = list(text_files(root))
    recognized = recognized_dirs(root)
    print(f"root: {root}")
    print("dirs_scanned: .")
    print("recognized_dirs: " + (", ".join(str(p.relative_to(root)) for p in recognized) if recognized else "none"))
    print("dirs_skipped: " + ", ".join(sorted(SKIP_DIRS)))
    print(f"text_files_scanned: {len(files)}")
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
