#!/usr/bin/env python3
"""Rank structural size winners from a linked z88dk map and its binaries.

Reads one resident map plus its CODE binary and, optionally, the overlay or
bank binaries linked against it. Prints candidate families that historically
dominate real savings, each already above a materiality threshold:

  [mass]          largest modules and routines (where to look)
  [overlay_only]  resident routines referenced only from one overlay (move them)
  [unreferenced]  resident routines with no 16-bit reference and no fall-through
  [abi_cleanup]   callees whose callers pop stack arguments (callee/fastcall)
  [frame_idioms]  repeated SDCC frame/boolean idioms (one shared helper or rule)

Everything is a candidate: references are counted as any little-endian 16-bit
occurrence of the address, so tables, pointer loads and calls all count and
the move/dead lists err towards keeping code.
"""
from __future__ import annotations

import argparse
import collections
import re
from pathlib import Path

MAP_RE = re.compile(
    r"^(\S+)\s+= \$([0-9A-Fa-f]+) ; addr, \w+, \S*, (\S*), (\S*), (.*)$"
)
LOCAL_PREFIXES = ("l_", "i_", "__str_", "___str_")
CODE_SECTION_HINTS = ("code", "rodata")
# 5-byte epilogue / 8-byte inline prologue / 7-byte booleanization (SDCC).
IDIOMS = (
    ("ld sp,ix; pop ix; ret", bytes.fromhex("ddf9dde1c9"), 3, 5),
    ("push ix; ld ix,0; add ix,sp", bytes.fromhex("dde5dd210000dd39"), 3, 11),
    ("jr nz,+4; ld a,1; jr +1; xor a", bytes.fromhex("20043e011801af"), 5, 0),
    ("jr z,+4; ld a,1; jr +1; xor a", bytes.fromhex("28043e011801af"), 5, 0),
)
CLEANUP = {0xF1: 2, 0xC1: 2, 0xD1: 2, 0xE1: 2, 0x33: 1}  # pop af/bc/de/hl, inc sp
CALLS = {0xCD, 0xC4, 0xCC, 0xD4, 0xDC, 0xE4, 0xEC, 0xF4, 0xFC}
JUMPS = {0xC3, 0xC2, 0xCA, 0xD2, 0xDA, 0xE2, 0xEA, 0xF2, 0xFA}
LOAD16 = {0x01, 0x11, 0x21, 0x31}  # ld bc/de/hl/sp,nn
RELATIVE = {0x10, 0x18, 0x20, 0x28, 0x30, 0x38}  # djnz/jr


def load_map(path: Path) -> list[tuple[int, str, str, str]]:
    """Return sorted (addr, name, module, section) for addr symbols."""
    rows: dict[int, tuple[int, str, str, str]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = MAP_RE.match(line)
        if not m:
            continue
        name, addr, module, section = m.group(1), int(m.group(2), 16), m.group(3), m.group(4)
        if not section.startswith(CODE_SECTION_HINTS):
            continue
        if addr not in rows or rows[addr][1].startswith(LOCAL_PREFIXES):
            rows[addr] = (addr, name, module, section)
    return sorted(rows.values())


def bss_head(path: Path) -> int | None:
    """__BSS_head: defc aliases into BSS keep their source's code section."""
    m = re.search(r"^__BSS_head\s+= \$([0-9A-Fa-f]+) ; const",
                  path.read_text(encoding="utf-8", errors="replace"), re.M)
    return int(m.group(1), 16) if m else None


def routines(symbols, origin: int, end: int) -> list[tuple[int, int, str, str]]:
    """(start, size, name, module) with local labels folded into the owner."""
    starts = [s for s in symbols if origin <= s[0] < end]
    out: list[list] = []
    for i, (addr, name, module, _section) in enumerate(starts):
        nxt = starts[i + 1][0] if i + 1 < len(starts) else end
        if name.startswith(LOCAL_PREFIXES) and out and out[-1][3] == module:
            out[-1][1] = nxt - out[-1][0]
            continue
        out.append([addr, nxt - addr, name, module])
    return [tuple(r) for r in out]


def word_hits(blob: bytes, value: int) -> list[int]:
    needle = bytes((value & 0xFF, value >> 8))
    hits, at = [], blob.find(needle)
    while at >= 0:
        hits.append(at)
        at = blob.find(needle, at + 1)
    return hits


def strong_refs(blob: bytes, origin: int | None) -> dict[int, list[int]]:
    """target -> offsets of call/jp/ld rr,nn (and jr/djnz when origin is known)."""
    refs: dict[int, list[int]] = collections.defaultdict(list)
    for i in range(len(blob) - 2):
        op = blob[i]
        if op in CALLS or op in JUMPS or op in LOAD16:
            refs[blob[i + 1] | (blob[i + 2] << 8)].append(i)
        elif op in (0xDD, 0xFD) and blob[i + 1] == 0x21 and i + 3 < len(blob):
            refs[blob[i + 2] | (blob[i + 3] << 8)].append(i)
        elif origin is not None and op in RELATIVE:
            disp = blob[i + 1] - 256 if blob[i + 1] > 127 else blob[i + 1]
            refs[origin + i + 2 + disp].append(i)
    return refs


def falls_through(code: bytes, offset: int) -> bool:
    """True unless the bytes before offset end in ret, jp nn, jr e or jp (hl)."""
    if offset <= 0:
        return False
    if code[offset - 1] in (0xC9, 0xE9):
        return False
    if offset >= 3 and code[offset - 3] == 0xC3:
        return False
    if offset >= 2 and code[offset - 2] == 0x18:
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--map", type=Path, required=True, help="resident linker map")
    ap.add_argument("--bin", type=Path, required=True, help="resident CODE binary")
    ap.add_argument("--origin", type=lambda v: int(v, 0), required=True, help="load address of --bin")
    ap.add_argument("--overlay", action="append", default=[], metavar="NAME=PATH",
                    help="overlay/bank binary linked against the resident map (repeatable)")
    ap.add_argument("--min-bytes", type=int, default=30, help="materiality threshold (default 30)")
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()

    code = args.bin.read_bytes()
    end = args.origin + len(code)
    bss = bss_head(args.map)
    if bss is not None and args.origin < bss < end:
        end = bss
    symbols = load_map(args.map)
    rts = routines(symbols, args.origin, end)
    overlays = {}
    for spec in args.overlay:
        name, _, path = spec.partition("=")
        overlays[name or Path(path).stem] = Path(path).read_bytes()

    print(f"[pressure]\nresident {args.origin:#06x}..{end:#06x} = {len(code)} B; "
          f"threshold {args.min_bytes} B; overlays {len(overlays)}")

    by_module = collections.Counter()
    for _a, size, _n, module in rts:
        by_module[module] += size
    print("\n[mass]")
    for module, size in by_module.most_common(args.top):
        print(f"  module {size:6d} B  {module}")
    for addr, size, name, module in sorted(rts, key=lambda r: -r[1])[: args.top]:
        print(f"  routine {size:5d} B  {name} ({module}) @{addr:#06x}")

    res_refs = strong_refs(code, args.origin)
    ovl_refs = {k: strong_refs(v, None) for k, v in overlays.items()}
    owner_starts = [r[0] for r in rts]

    def owner(offset: int) -> int:
        lo, hi = 0, len(owner_starts) - 1
        addr = args.origin + offset
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if owner_starts[mid] <= addr:
                lo = mid
            else:
                hi = mid - 1
        return owner_starts[lo]

    info = {}
    for addr, size, name, module in rts:
        own = range(addr - args.origin, addr - args.origin + size)
        callers = {owner(o) for o in res_refs.get(addr, []) if o not in own}
        users = {k: len(r.get(addr, [])) for k, r in ovl_refs.items() if r.get(addr)}
        weak = len([h for h in word_hits(code, addr) if h not in own]) - len(
            [o for o in res_refs.get(addr, []) if o not in own])
        info[addr] = (size, name, module, callers, users, weak)

    moves: dict[int, tuple[str, str]] = {}
    for addr, (size, name, module, callers, users, weak) in info.items():
        if not callers and len(users) == 1:
            moves[addr] = (next(iter(users)), "")
    changed = True
    while changed:  # resident helpers whose every caller moves to the same overlay
        changed = False
        for addr, (size, name, module, callers, users, weak) in info.items():
            if addr in moves or not callers or not callers <= set(moves):
                continue
            targets = {moves[c][0] for c in callers} | set(users)
            if len(targets) == 1:
                via = ",".join(info[c][1] for c in sorted(callers))
                moves[addr] = (targets.pop(), f" with {via}")
                changed = True
    groups = collections.defaultdict(list)
    for addr, (ovl, via) in moves.items():
        groups[ovl].append((info[addr][0], info[addr][1], info[addr][2], via, info[addr][5]))
    print("\n[overlay_only]  move into that overlay if it has room; verify C/ASM callers")
    shown = 0
    for ovl, items in sorted(groups.items(), key=lambda kv: -sum(i[0] for i in kv[1])):
        total = sum(i[0] for i in items)
        if total < args.min_bytes:
            continue
        print(f"  -> {ovl}: {total} B")
        for size, name, module, via, weak in sorted(items, reverse=True):
            caution = f" [weak refs {weak}: check tables]" if weak > 0 else ""
            print(f"     {size:5d} B  {name} ({module}){via}{caution}")
        shown += 1
    if not shown:
        print("  none" + ("" if overlays else " (no --overlay given)"))

    dead = [(s, n, m) for a, (s, n, m, callers, users, weak) in info.items()
            if s >= args.min_bytes and not callers and not users and weak <= 0
            and not falls_through(code, a - args.origin)]
    print("\n[unreferenced]  no reference anywhere and no fall-through; check indirect use")
    for size, name, module in sorted(dead, reverse=True)[: args.top]:
        print(f"  {size:5d} B  {name} ({module})")
    if not dead:
        print("  none")

    starts = {addr: name for addr, _s, name, _m in rts}
    cleanup = collections.defaultdict(lambda: [0, 0])
    for blob in [code, *overlays.values()]:
        for i in range(len(blob) - 3):
            if blob[i] not in CALLS:
                continue
            target = blob[i + 1] | (blob[i + 2] << 8)
            if target not in starts:
                continue
            j, cost = i + 3, 0
            while j < len(blob) and blob[j] in CLEANUP and cost < 12:
                cost += 1
                j += 1
            if cost:
                cleanup[target][0] += 1
                cleanup[target][1] += cost
    ranked = sorted(cleanup.items(), key=lambda kv: -kv[1][1])
    total = sum(v[1] for _k, v in ranked)
    print(f"\n[abi_cleanup]  caller-side stack cleanup {total} B in all; callee/fastcall removes it per site")
    for target, (sites, cost) in ranked[: args.top]:
        if cost < args.min_bytes // 3:
            break
        print(f"  {cost:4d} B over {sites:3d} sites  {starts[target]}")

    print("\n[frame_idioms]  one helper + one peephole rule; resident and overlays")
    for label, pattern, call_len, helper in IDIOMS:
        counts = {"resident": code.count(pattern)}
        counts.update({k: v.count(pattern) for k, v in overlays.items()})
        n = sum(counts.values())
        if not n:
            continue
        gain = n * (len(pattern) - call_len) - helper
        note = "" if helper else " (needs flag liveness; estimate only)"
        print(f"  {n:4d} x {label:34s} resident {counts['resident']:3d}  net ~{gain} B{note}")
    print("\nnote: candidates only; confirm with sources, a build, and every target's limits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
