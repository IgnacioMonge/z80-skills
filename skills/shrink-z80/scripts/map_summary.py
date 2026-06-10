#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

SYMBOL_RE = re.compile(r"^(\S+)\s*=\s*\$([0-9A-Fa-f]+)\s*;")
IMPORTANT = [
    "__CODE_head",
    "__CODE_tail",
    "__CODE_size",
    "__DATA_head",
    "__DATA_tail",
    "__DATA_size",
    "__BSS_head",
    "__BSS_tail",
    "__BSS_END_tail",
    "CRT_STACK_SIZE",
    "TAR__register_sp",
    "__register_sp",
]


def pick_map(path: Path) -> Path:
    if path.is_file():
        return path
    maps = sorted(
        path.rglob("*.map"), key=lambda item: item.stat().st_mtime, reverse=True
    )
    if not maps:
        raise FileNotFoundError(f"no .map file found under {path}")
    return maps[0]


def load_symbols(map_path: Path) -> dict[str, int]:
    symbols: dict[str, int] = {}
    for line in map_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = SYMBOL_RE.match(line)
        if match:
            symbols[match.group(1)] = int(match.group(2), 16)
    return symbols


def fmt_hex(value: int | None) -> str:
    return "n/a" if value is None else f"${value:04X}"


def symbol_spans(symbols: dict[str, int]) -> list[tuple[str, int, int]]:
    ordered = sorted((addr, name) for name, addr in symbols.items())
    spans: list[tuple[str, int, int]] = []
    for idx, (addr, name) in enumerate(ordered[:-1]):
        next_addr = ordered[idx + 1][0]
        size = next_addr - addr
        if 0 < size < 0x8000:
            spans.append((name, addr, size))
    return sorted(spans, key=lambda item: item[2], reverse=True)


def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    map_path = pick_map(target)
    symbols = load_symbols(map_path)
    print(f"map: {map_path}")
    for name in IMPORTANT:
        if name in symbols:
            print(f"{name}: {fmt_hex(symbols[name])}")

    stack_top = symbols.get("TAR__register_sp") or symbols.get("__register_sp")
    bss_end = symbols.get("__BSS_END_tail") or symbols.get("__BSS_tail")
    if stack_top is not None and bss_end is not None:
        gap = stack_top - bss_end
        print(f"stack_gap: {gap} bytes ({fmt_hex(stack_top)} - {fmt_hex(bss_end)})")

    print("\n[largest_symbol_spans]")
    spans = symbol_spans(symbols)
    if not spans:
        print("none")
    else:
        for name, addr, size in spans[:30]:
            print(f"{name}: {size} bytes at {fmt_hex(addr)}")

    heavy = sorted(
        name
        for name in symbols
        if re.search(
            r"(__mul|__div|__mod|printf|sprintf|snprintf|scanf|malloc|free|strlen|strcmp|memcpy|memset)",
            name,
        )
    )
    print("\n[heavy_symbols]")
    if not heavy:
        print("none")
    else:
        for name in heavy[:40]:
            print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
