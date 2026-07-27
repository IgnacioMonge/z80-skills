#!/usr/bin/env python3
"""Approximate static Z80 T-state scan for asm/listing snippets.

This is not a profiler. It reports single-pass totals and flags repeated or
conditional instructions that require manual counts/direction. Contention and
data-dependent loops need manual review.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

SIMPLE = {
    "nop": 4,
    "jr": 12,
    "djnz": 13,
    "call": 17,
    "exx": 4,
    "ldi": 16,
    "ldd": 16,
    "cpi": 16,
    "cpd": 16,
    "outi": 16,
    "outd": 16,
    "ini": 16,
    "ind": 16,
    "rlca": 4,
    "rrca": 4,
    "rla": 4,
    "rra": 4,
    "di": 4,
    "ei": 4,
    "halt": 4,
    "rst": 11,
}
REPEAT = {"ldir", "lddr", "cpir", "cpdr", "otir", "otdr", "inir", "indr"}
R8 = {"a", "b", "c", "d", "e", "h", "l"}
R16 = {"bc", "de", "hl", "sp"}
IDX = {"ix", "iy"}
CONDITIONS = {"nz", "z", "nc", "c", "po", "pe", "p", "m"}
LABEL_RE = re.compile(r"^\s*[A-Za-z_.$@?][\w.$@?]*:\s*")


def clean(line):
    line = line.split(";", 1)[0]
    line = LABEL_RE.sub("", line).strip().lower()
    if not line:
        return None
    parts = re.split(r"\s+", line, maxsplit=1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def split_args(args):
    parts = [p.strip().lower() for p in args.split(",")]
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], ",".join(parts[1:]).strip()


def is_idx_mem(x):
    return "(ix" in x or "(iy" in x


def is_hl_mem(x):
    return "(hl)" in x


def is_mem(x):
    return "(" in x and ")" in x

def estimate_ld(dst, src):
    if (dst == "a" and src in {"i", "r"}) or (src == "a" and dst in {"i", "r"}):
        return 9
    if dst in R8 and src in R8:
        return 4
    if dst in R8 and src.isdigit():
        return 7
    if dst == "sp" and src == "hl":
        return 6
    if dst == "sp" and src in IDX:
        return 10
    if dst in R16 and src:
        return (16 if dst == "hl" else 20) if is_mem(src) else 10
    if src in R16 and is_mem(dst):
        return 16 if src == "hl" else 20
    if dst in IDX and src:
        return 20 if is_mem(src) else 14
    if src in IDX and is_mem(dst):
        return 20
    if dst in R8 and is_hl_mem(src):
        return 7
    if is_hl_mem(dst) and src in R8:
        return 7
    if dst in R8 and is_idx_mem(src):
        return 19
    if is_idx_mem(dst) and src in R8:
        return 19
    if is_hl_mem(dst) and src:
        return 10
    if is_idx_mem(dst) and src:
        return 19
    if dst == "a" and src in {"(bc)", "(de)"}:
        return 7
    if src == "a" and dst in {"(bc)", "(de)"}:
        return 7
    if dst == "a" and is_mem(src):
        return 13
    if src == "a" and is_mem(dst):
        return 13
    if dst == "hl" and is_mem(src):
        return 16
    if src == "hl" and is_mem(dst):
        return 16
    if dst in IDX and is_mem(src):
        return 20
    if src in IDX and is_mem(dst):
        return 20
    if is_mem(dst) or is_mem(src):
        return 13
    return 7

def estimate(op, args):
    dst, src = split_args(args)
    if op == "jp":
        if dst == "(hl)":
            return 4
        if dst in {"(ix)", "(iy)"}:
            return 8
        return 10
    if op in REPEAT:
        return 16
    if op in {"push", "pop"}:
        if dst in IDX:
            return 15 if op == "push" else 14
        return 11 if op == "push" else 10
    if op == "ret":
        return 11 if dst in CONDITIONS else 10
    if op in SIMPLE:
        return SIMPLE[op]
    if op == "ld":
        return estimate_ld(dst, src)
    if op in {"inc", "dec"}:
        if dst in R8:
            return 4
        if dst in R16 or dst in IDX:
            return 6 if dst in R16 else 10
        if is_hl_mem(dst):
            return 11
        if is_idx_mem(dst):
            return 23
        return 4
    if op in {"add", "adc", "sbc"}:
        if dst == "hl":
            return 11 if op == "add" else 15
        if dst in IDX:
            return 15
        if is_idx_mem(src) or is_hl_mem(src):
            return 7 if is_hl_mem(src) else 19
        if src and src not in R8:
            return 7
        return 4
    if op in {"and", "or", "xor", "cp", "sub"}:
        operand = src or dst
        if is_hl_mem(operand):
            return 7
        if is_idx_mem(operand):
            return 19
        return 4 if operand in R8 else 7
    if op == "bit":
        if is_hl_mem(args):
            return 12
        if is_idx_mem(args):
            return 20
        return 8
    if op in {"set", "res", "rl", "rr", "sla", "sra", "srl"}:
        if is_hl_mem(args):
            return 15
        if is_idx_mem(args):
            return 23
        return 8
    if op == "ex":
        if args.strip().lower() in {"de,hl", "af,af'"}:
            return 4
        if "(sp)" in args:
            return 23 if any(x in args for x in ("ix", "iy")) else 19
        return 4
    if op in {"in", "out"}:
        return 12 if "(c)" in args.lower() else 11
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--top-window", type=int, default=12)
    args = ap.parse_args()
    path = Path(args.file)
    rows = []
    manual_markers = []
    total = 0
    unknown = 0
    for n, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        parsed = clean(line)
        if not parsed:
            continue
        op, rest = parsed
        branch_head, _ = split_args(rest)
        t = estimate(op, rest)
        if op in REPEAT:
            manual_markers.append((n, f"{line.strip()} ; total=21*(iterations-1)+16"))
        elif op == "djnz" or (
            op in {"jr", "jp", "call", "ret"} and branch_head in CONDITIONS
        ):
            manual_markers.append((n, f"{line.strip()} ; direction/count required"))
        if t is None:
            unknown += 1
            continue
        rows.append((n, t, line.strip()))
        total += t
    print(f"file: {path}")
    print(f"estimated_static_tstates_single_pass: {total}")
    print(f"estimated_instructions: {len(rows)} unknown_ops: {unknown}")
    if unknown:
        print("warning: total excludes unknown opcodes")
    if manual_markers:
        print("manual_timing_markers:")
        for n, src in manual_markers[:20]:
            print(f"  line {n}: {src}")
    if rows:
        w = max(1, args.top_window)
        windows = []
        for i in range(0, max(1, len(rows) - w + 1)):
            s = sum(r[1] for r in rows[i:i+w])
            windows.append((s, rows[i][0], rows[min(i+w-1, len(rows)-1)][0]))
        for s, a, b in sorted(windows, reverse=True)[:10]:
            print(f"hot_window {s:5d}T lines {a}-{b}")
    print("note: single-pass estimate only; multiply marked loops manually and account for contention, branch direction, and windows crossing labels")


if __name__ == "__main__":
    main()
