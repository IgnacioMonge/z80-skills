#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

COMMON_SCRIPTS = Path(__file__).resolve().parents[2] / "shrink-z80" / "scripts"
if str(COMMON_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(COMMON_SCRIPTS))

from scan_common import (  # noqa: E402
    EXCLUDE_DIRS,
    TEXT_EXTS,
    collect_pattern_hits,
    rel_path,
    resolve_scope,
)

PREFERRED_DIRS = ("src", "asm", "include", "overlay")
ARTIFACT_DIRS = ("build", "out", "obj", "gen", "generated", "dist")

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


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    scope = resolve_scope(root, TEXT_EXTS)
    files = scope.files
    recognized = recognized_dirs(root) if root.is_dir() else []
    print(f"root: {root}")
    print("dirs_scanned: .")
    print("recognized_dirs: " + (", ".join(rel_path(p, scope.base) for p in recognized) if recognized else "none"))
    print("dirs_skipped: " + ", ".join(sorted(EXCLUDE_DIRS)))
    print(f"text_files_scanned: {len(files)}")
    for suffix in (".map", ".lst", ".sym", ".opt", ".rul"):
        matches = sorted(path for path in files if path.suffix.lower() == suffix)
        print(f"{suffix} files: {len(matches)}")
        for path in matches[:5]:
            print(f"  - {rel_path(path, scope.base)}")

    for section, patterns in PATTERNS.items():
        print(f"\n[{section}]")
        hits = collect_pattern_hits(files, scope.base, patterns, limit=8)
        if not hits:
            print("  none")
            continue
        for hit in hits:
            print(f"  {hit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
