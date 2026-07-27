#!/usr/bin/env python3
"""Read-only structural scanner for Z80/Spectrum optimization opportunities."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

STATIC_C_FUNC = re.compile(
    r"(?m)^\s*static\s+(?!const\b)(?:[\w_]+\s+|\*|\s)+?"
    r"([A-Za-z_]\w*)\s*\([^;]*\)\s*(?:[A-Za-z_]\w*\s*)*\{"
)

PATTERNS = [
    ("asm_tail_call", re.compile(r"\bcall\s+([\w.$@?]+)\s*(?:;[^\n]*)?\n\s*ret\b", re.I), "SAFE", "call+ret can often become jp"),
    ("asm_block_repeat", re.compile(r"\b(ldir|otir|cpir|inir|indr|otdr)\b", re.I), "MEDIUM", "block repeat may be size-good but not speed-best"),
    ("asm_block_single", re.compile(r"\b(ldi|ldd|cpi|cpd|ini|ind|outi|outd)\b", re.I), "CHECK", "single-step block op; compare setup cost versus loop alternatives"),
    ("asm_index_regs", re.compile(r"\b(?:ix|iy)(?:[+-]|\s*\+|\s*\-|\b)", re.I), "CHECK", "IX/IY access costs prefix bytes/t-states"),
    ("asm_undoc_index_halves", re.compile(r"\b(ixh|ixl|iyh|iyl)\b", re.I), "DANGEROUS", "undocumented index-half usage"),
    ("asm_shadow_regs", re.compile(r"\bexx\b|\bex\s+af\s*,\s*af'", re.I), "MEDIUM", "alternate-register usage; audit ISR ownership"),
    ("asm_sp_blit_dense", re.compile(r"(?:\bld\s+sp,|\bpush\s+(?:af|bc|de|hl)|\bpop\s+(?:af|bc|de|hl)|\bexx\b)(?:[^\n]*\n){0,12}(?:\bpush\s+(?:af|bc|de|hl)|\bpop\s+(?:af|bc|de|hl)).*(?:\n.*(?:\bpush\s+(?:af|bc|de|hl)|\bpop\s+(?:af|bc|de|hl))){2,}", re.I), "DANGEROUS", "dense SP/PUSH/POP block: possible stack blit or risk"),
    ("asm_di_ei_region", re.compile(r"\bdi\b(?:[^\n]*\n){0,40}.*\bei\b", re.I), "CHECK", "interrupt-disabled region; inspect timing/safety"),
    ("asm_smc_marker", re.compile(r"\$\+1|\$\+2|\bld\s*\([^)]*\+1\)|\bld\s*\([^)]*\+2\)", re.I), "MEDIUM", "possible self-modifying immediate"),
    ("asm_manual_copy", re.compile(r"ld\s+a,\s*\(hl\)\s*\n\s*ld\s*\(de\),\s*a\s*\n\s*inc\s+hl\s*\n\s*inc\s+de", re.I), "MEDIUM", "manual byte copy may be LDI/unroll candidate"),
    ("asm_loop_ram_state", re.compile(r"ld\s+(bc|de|hl),\s*\([^)]*\)(?:[^\n]*\n){1,12}.*ld\s*\([^)]*\),\s*\1(?:[^\n]*\n){0,8}.*\b(djnz|jr\s+nz|jp\s+nz)\b", re.I), "MEDIUM", "loop spills state to RAM inside body"),
    ("asm_border_beeper", re.compile(r"\bout\s*\(\s*(?:0xfe|\$fe|254)\s*\)", re.I), "CHECK", "border/beeper write; timing-sensitive on Spectrum"),
    ("asm_ay_ports", re.compile(r"\b(?:0xfffd|\$fffd|65533|0xbffd|\$bffd|49149)\b", re.I), "CHECK", "possible AY register/data port activity"),
    ("asm_floating_bus", re.compile(r"\bin\s+a\s*,\s*\(\s*(?:0xff|\$ff|255)\s*\)", re.I), "DANGEROUS", "possible floating-bus read"),
    ("c_libpull_string", re.compile(r"\b(strlen|strcmp|strcpy|strncpy|memcmp|memcpy|memmove|sprintf|printf)\s*\("), "CHECK", "may pull library or duplicate helpers; check map before swapping helpers"),
    ("c_fixed_compare", re.compile(r"\bstrcmp\s*\(\s*[^,\n]+,\s*[^)\n]+\)\s*==\s*0"), "CHECK", "fixed-buffer compare candidate only after length/NUL/link-size proof"),
    ("c_strncpy_terminator", re.compile(r"\bstrncpy\s*\([^;]+;\s*(?:[^\n]*\n){0,2}\s*[^;]+=\s*'\\0'\s*;"), "CHECK", "bounded-copy candidate; verify semantics and whether strncpy remains linked"),
    ("c_wide_math", re.compile(r"\b(uint32_t|int32_t|long)\b"), "CHECK", "wide math can pull heavy helpers"),
    ("c_fastcall", re.compile(r"__z88dk_fastcall|__fastcall|__FASTCALL__", re.I), "CHECK", "fastcall marker; confirm ABI and generated code"),
    ("c_callee", re.compile(r"__z88dk_callee|__CALLEE__", re.I), "CHECK", "callee marker; confirm stack cleanup expectations"),
    ("c_sdcccall", re.compile(r"__sdcccall\s*\("), "CHECK", "explicit sdcc calling convention in use"),
    ("c_naked", re.compile(r"__naked\b", re.I), "MEDIUM", "naked function; prologue/epilogue is fully manual"),
    ("c_pragma_output", re.compile(r"#pragma\s+output\b", re.I), "INFO", "z88dk pragma output present; inspect toolchain-related size choices"),
    ("c_loop_scan", re.compile(r"\bfor\s*\([^;]+;[^;]+;[^)]*\)|\bwhile\s*\("), "INFO", "hot loops may merit map/listing check"),
]

EXTS = {".c", ".h", ".asm", ".s", ".inc", ".lst", ".lis"}
IGNORE_DIRS = {".git", ".hg", ".svn", "__pycache__", "node_modules"}


def is_ignored(path: Path, root: Path, ignore_dirs: set[str]) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        parts = path.parts
    return any(part in ignore_dirs for part in parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--limit-per-pattern", type=int, default=25)
    ap.add_argument("--limit-total", type=int, default=400)
    ap.add_argument("--exclude-dir", action="append", default=[], help="extra directory name to skip")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    ignore_dirs = IGNORE_DIRS | set(args.exclude_dir or [])
    total = 0
    counts = {name: 0 for name, *_ in PATTERNS}
    truncated = set()
    for p in root.rglob("*"):
        if total >= args.limit_total:
            break
        if is_ignored(p, root, ignore_dirs) or not p.is_file() or p.suffix.lower() not in EXTS:
            continue
        text = p.read_text(errors="replace")
        for name, rx, lane, note in PATTERNS:
            if counts[name] >= args.limit_per_pattern:
                truncated.add(name)
                continue
            for m in rx.finditer(text):
                if counts[name] >= args.limit_per_pattern or total >= args.limit_total:
                    truncated.add(name)
                    break
                line = text.count("\n", 0, m.start()) + 1
                rel = p.relative_to(root).as_posix()
                snippet = " ".join(text[m.start():m.end()].split())[:120]
                print(f"{lane:9s} {name:18s} {rel}:{line}: {snippet} -- {note}")
                counts[name] += 1
                total += 1
    unused_count = 0
    if total < args.limit_total:
        for p in root.rglob("*.c"):
            if is_ignored(p, root, ignore_dirs) or not p.is_file():
                continue
            text = p.read_text(errors="replace")
            for m in STATIC_C_FUNC.finditer(text):
                name = m.group(1)
                if len(re.findall(r"\b" + re.escape(name) + r"\b", text)) != 1:
                    continue
                if unused_count >= args.limit_per_pattern or total >= args.limit_total:
                    truncated.add("c_unused_static_fn")
                    break
                line = text.count("\n", 0, m.start()) + 1
                rel = p.relative_to(root).as_posix()
                print(f"SAFE      c_unused_static_fn {rel}:{line}: {name} -- static function appears only at its definition")
                unused_count += 1
                total += 1
    if truncated:
        print("TRUNCATED patterns: " + ", ".join(sorted(truncated)))
    if total >= args.limit_total:
        print(f"TRUNCATED total at {args.limit_total}")


if __name__ == "__main__":
    main()
