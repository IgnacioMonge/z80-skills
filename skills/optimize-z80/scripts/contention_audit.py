#!/usr/bin/env python3
"""Flag map symbols in likely ZX Spectrum contended ranges."""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

Z88DK = re.compile(
    r"^\s*([A-Za-z0-9_.$]+):([A-Za-z0-9_.$-]+)(?::([^:;]+))?:\s*"
    r"([A-Za-z_.$@?][\w.$@?]*)\s*=\s*\$([0-9A-Fa-f]+)\s*;\s*(.*)$"
)
GENERIC = re.compile(r"^\s*([A-Za-z_.$@?][\w.$@?]*)\s*=\s*\$([0-9A-Fa-f]+)\s*;\s*(.*)$")
PLAIN = re.compile(r"^\s*\$?([0-9A-Fa-f]{4,6})\s+([A-Za-z_.$@?][\w.$@?]*)\b")


def parse_line(line: str):
    m = Z88DK.match(line)
    if m:
        section, module, src, name, hx, meta = m.groups()
        return {"name": name, "addr": int(hx, 16), "section": section.lower(), "module": module, "meta": meta}
    m = GENERIC.match(line)
    if m:
        name, hx, meta = m.groups()
        return {"name": name, "addr": int(hx, 16), "section": "", "module": "", "meta": meta}
    m = PLAIN.match(line)
    if m:
        hx, name = m.groups()
        return {"name": name, "addr": int(hx, 16), "section": "", "module": "", "meta": ""}
    return None


def zone(addr: int, model: str, page: int | None = None) -> str:
    if 0x4000 <= addr <= 0x7FFF:
        return f"contended_{model}"
    if 0x8000 <= addr <= 0xBFFF:
        return f"uncontended_{model}"
    if 0xC000 <= addr <= 0xFFFF:
        if model == "48k":
            return "uncontended_48k"
        if page is None:
            return f"unknown_banked_{model}"
        contended = page in ({1, 3, 5, 7} if model == "128k" else {4, 5, 6, 7})
        return f"{'contended' if contended else 'uncontended'}_{model}"
    return "rom_or_low"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("map")
    ap.add_argument("--model", choices=["48k", "128k", "plus3", "auto"], default="auto")
    ap.add_argument("--page", type=int, choices=range(8), metavar="0..7", help="RAM page mapped at $C000")
    ap.add_argument("--include-uncontended", action="store_true", help="also print uncontended symbols")
    ap.add_argument("--limit", type=int, default=120, help="max printed symbols; use 0 for no limit")
    args = ap.parse_args()
    model = args.model
    if model == "auto" and args.page is not None:
        ap.error("--page requires an explicit --model")
    counts: dict[str, int] = {}
    printed = 0
    truncated = False
    parsed = 0
    for line in Path(args.map).read_text(errors="replace").splitlines():
        row = parse_line(line)
        if not row:
            continue
        parsed += 1
        if str(row.get("meta", "")).startswith("const"):
            continue
        addr = row["addr"]
        z = zone(addr, model, args.page)
        counts[z] = counts.get(z, 0) + 1
        if not z.startswith("contended") and not args.include_uncontended:
            continue
        if args.limit and printed >= args.limit:
            truncated = True
            continue
        extra = []
        if row.get("section"):
            extra.append(row["section"])
        if row.get("module"):
            extra.append(row["module"])
        if row.get("meta"):
            extra.append(row["meta"])
        print(f"${addr:04X} {z:18s} {row['name']} ; {' | '.join(x for x in extra if x)}")
        printed += 1
    print(
        "SUMMARY "
        f"model={model} parsed={parsed} "
        f"contended={counts.get(f'contended_{model}', 0)} "
        f"uncontended={counts.get(f'uncontended_{model}', 0)} "
        f"unknown_banked={counts.get(f'unknown_banked_{model}', 0)} "
        f"rom_or_low={counts.get('rom_or_low', 0)} printed={printed}"
    )
    print("NOTE normal memory map only; pass --page for $C000-$FFFF on banked models")
    if truncated:
        print(f"TRUNCATED at --limit {args.limit}; rerun with --limit 0 for full output")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        try:
            sys.stdout = open(os.devnull, "w")
        except Exception:
            pass
