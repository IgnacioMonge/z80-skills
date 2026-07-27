#!/usr/bin/env python3
"""Parse map files and report approximate hotspots with format warnings."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

Z88DK_RE = re.compile(r"^\s*([A-Za-z_.$@?][\w.$@?]*)\s*=\s*\$([0-9A-Fa-f]+)\s*;\s*([^\n]*)")
GENERIC_RE = re.compile(r"^\s*(?:0x|\$)?([0-9A-Fa-f]{4,6})\s+([A-Za-z_.$@?][\w.$@?]*)\b")


def parse_z88dk(line):
    m = Z88DK_RE.match(line)
    if not m:
        return None
    name, addr_hex, meta = m.groups()
    parts = [p.strip() for p in meta.split(",")]
    kind = parts[0] if len(parts) > 0 else ""
    if kind == "const":
        return None
    return {
        "name": name,
        "addr": int(addr_hex, 16),
        "kind": kind,
        "scope": parts[1] if len(parts) > 1 else "",
        "module": parts[3] if len(parts) > 3 else "",
        "section": parts[4] if len(parts) > 4 else "",
        "src": parts[5] if len(parts) > 5 else "",
        "format": "z88dk",
    }


def parse_generic(line):
    m = GENERIC_RE.match(line)
    if not m:
        return None
    addr_hex, name = m.groups()
    return {"name": name, "addr": int(addr_hex, 16), "kind": "symbol", "scope": "", "module": "", "section": "generic", "src": "", "format": "generic"}


def parse_map(path: Path):
    syms = []
    fmt_counts = {"z88dk": 0, "generic": 0}
    for line in path.read_text(errors="replace").splitlines():
        s = parse_z88dk(line)
        if s:
            fmt_counts["z88dk"] += 1
            syms.append(s)
            continue
        s = parse_generic(line)
        if s:
            fmt_counts["generic"] += 1
            syms.append(s)
    fmt = max(fmt_counts, key=fmt_counts.get) if syms else "unknown"
    return syms, fmt, fmt_counts


def estimate_sizes(syms):
    groups = {}
    for s in syms:
        key = s.get("section") or s.get("module") or "unknown"
        groups.setdefault(key, []).append(s)
    rows = []
    for key, vals in groups.items():
        vals = sorted(vals, key=lambda x: x["addr"])
        for i, s in enumerate(vals[:-1]):
            size = vals[i + 1]["addr"] - s["addr"]
            if 0 < size < 8192:
                r = dict(s)
                r["size_est"] = size
                r["group"] = key
                rows.append(r)
    return sorted(rows, key=lambda r: r["size_est"], reverse=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("map")
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    syms, fmt, counts = parse_map(Path(args.map))
    rows = estimate_sizes(syms)
    payload = {"map": args.map, "format": fmt, "format_counts": counts, "symbols": len(syms), "top": rows[: args.top], "warnings": []}
    if not syms:
        payload["warnings"].append("no symbols parsed; unsupported map format or stripped map")
    if fmt == "generic":
        payload["warnings"].append("generic parser used; section grouping and sizes are approximate")
    payload["warnings"].append("sizes are estimates from adjacent symbols; confirm with lst/sym/build reports")
    if args.json:
        print(json.dumps(payload, indent=2))
        return
    print(f"map: {args.map}")
    print(f"format: {fmt} symbols={len(syms)} counts={counts}")
    for w in payload["warnings"]:
        print(f"warning: {w}")
    for r in rows[: args.top]:
        src = f" {r['src']}" if r.get("src") else ""
        print(f"{r['size_est']:5d}  ${r['addr']:04X}  {r['name']}  [{r.get('group','')}] {r.get('module','')}{src}")


if __name__ == "__main__":
    main()
