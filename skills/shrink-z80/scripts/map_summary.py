#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from scan_common import fmt_hex, load_symbol_table

IMPORTANT = [
    "__CODE_head",
    "__CODE_tail",
    "__CODE_END_tail",
    "__CODE_size",
    "__DATA_head",
    "__DATA_tail",
    "__DATA_END_tail",
    "__DATA_size",
    "__BSS_head",
    "__BSS_tail",
    "__BSS_END_tail",
    "CRT_STACK_SIZE",
    "TAR__register_sp",
    "__register_sp",
]
SECTIONS = ("CODE", "DATA", "BSS")
HEAVY_RE = re.compile(
    r"(__mul|__div|__mod|l_(?:mul|mult|div|mod|long)|printf|sprintf|snprintf|scanf|"
    r"malloc|free|strlen|strcmp|memcpy|memset)"
)
CRT_RE = re.compile(
    r"(^__Start$|^_main$|crt0|__crt|CRT_|startup|register_sp|__heap|"
    r"malloc|free|printf|sprintf|snprintf|scanf|fputc|fgetc|fputs|fgets|"
    r"fopen|fclose|exit|atexit|errno|stdin|stdout|stderr|__stdio|"
    r"__prin|__scan|__calloc|__realloc|__strdup)",
    re.IGNORECASE,
)
BANK_RE = re.compile(
    r"(bank|page|overlay|mmu|__BANK|BANK_|_banked|far_|__far)",
    re.IGNORECASE,
)
SPAN_SENTINEL_RE = re.compile(
    r"^(__[A-Z0-9_]+_(head|tail|size)|__BSS_END_tail|CRT_STACK_SIZE|"
    r"TAR__register_sp|__register_sp)$"
)

# Classic Spectrum flat RAM pressure zones (heuristic triage only).
# 0x0000-0x3FFF: ROM window / special
# 0x4000-0x5AFF: display file + attrs
# 0x5B00-0xFFFF: typical resident program RAM on 48K
ZONE_ROM = (0x0000, 0x4000, "rom_window")
ZONE_SCREEN = (0x4000, 0x5B00, "screen_ula")
ZONE_RESIDENT = (0x5B00, 0xC000, "resident_ram")
ZONE_PAGED_SLOT = (0xC000, 0x10000, "paged_slot_or_high_ram")


def map_candidates(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() == ".map" else []
    return sorted(path.rglob("*.map"))


def section_tail(symbols: dict[str, int], name: str) -> int | None:
    tail = symbols.get(f"__{name}_tail")
    end_tail = symbols.get(f"__{name}_END_tail")
    if end_tail is not None and (tail is None or end_tail > tail):
        return end_tail
    return tail


def section_summary(symbols: dict[str, int]) -> list[str]:
    rows: list[str] = []
    for name in SECTIONS:
        head = symbols.get(f"__{name}_head")
        tail = section_tail(symbols, name)
        derived = tail - head if head is not None and tail is not None else None
        explicit = symbols.get(f"__{name}_size")
        size = derived if derived is not None else explicit
        if head is not None or tail is not None or size is not None:
            rows.append(
                f"{name}: head={fmt_hex(head)} tail={fmt_hex(tail)} "
                f"size={size if size is not None else 'n/a'}"
            )
    return rows


def section_bounds(symbols: dict[str, int]) -> list[tuple[str, int, int]]:
    bounds: list[tuple[str, int, int]] = []
    for name in SECTIONS:
        head = symbols.get(f"__{name}_head")
        tail = section_tail(symbols, name)
        if head is not None and tail is not None and tail > head:
            bounds.append((name, head, tail))
    return bounds


def bank_sections(symbols: dict[str, int]) -> list[tuple[str, int, int, int]]:
    """Named bank/overlay sections with explicit head/tail markers."""
    rows: list[tuple[str, int, int, int]] = []
    for symbol, head in symbols.items():
        match = re.match(r"^__(.+)_head$", symbol, re.IGNORECASE)
        if not match:
            continue
        name = match.group(1)
        if not BANK_RE.search(name):
            continue
        tails = [
            symbols.get(f"__{name}_tail"),
            symbols.get(f"__{name}_END_tail"),
        ]
        tail = max((value for value in tails if value is not None), default=None)
        if tail is not None and tail >= head:
            rows.append((name, head, tail, tail - head))
    return sorted(rows, key=lambda item: (item[1], item[0].lower()))


def span_limit(addr: int, bounds: list[tuple[str, int, int]]) -> int | None:
    if not bounds:
        return None
    for _, head, tail in bounds:
        if head <= addr < tail:
            return tail
    return -1


def symbol_spans(symbols: dict[str, int]) -> list[tuple[str, int, int]]:
    ordered = sorted((addr, name) for name, addr in symbols.items())
    bounds = section_bounds(symbols)
    spans: list[tuple[str, int, int]] = []
    for idx, (addr, name) in enumerate(ordered[:-1]):
        if SPAN_SENTINEL_RE.match(name):
            continue
        limit = span_limit(addr, bounds)
        if limit == -1:
            continue
        next_addr = ordered[idx + 1][0]
        if limit is not None and next_addr > limit:
            next_addr = limit
        size = next_addr - addr
        if 0 < size < 0x8000:
            spans.append((name, addr, size))
    return sorted(spans, key=lambda item: item[2], reverse=True)


def zone_name(addr: int) -> str:
    for lo, hi, name in (ZONE_ROM, ZONE_SCREEN, ZONE_RESIDENT, ZONE_PAGED_SLOT):
        if lo <= addr < hi:
            return name
    return "other"


def print_resident_banked(symbols: dict[str, int], spans: list[tuple[str, int, int]]) -> None:
    print("\n[resident_vs_banked_heuristic]")
    print(
        "note: flat 48K triage only. $C000-$FFFF is paged_slot_or_high_ram "
        "(NOT automatic resident). Use [target_row] + --all matrix; banked/Next need section names."
    )
    zone_bytes = {"rom_window": 0, "screen_ula": 0, "resident_ram": 0, "paged_slot_or_high_ram": 0, "other": 0}
    zone_count = {k: 0 for k in zone_bytes}
    for _, addr, size in spans:
        z = zone_name(addr)
        zone_bytes[z] = zone_bytes.get(z, 0) + size
        zone_count[z] = zone_count.get(z, 0) + 1

    for z in ("rom_window", "screen_ula", "resident_ram", "paged_slot_or_high_ram", "other"):
        print(f"  {z}: span_sum≈{zone_bytes[z]} bytes across {zone_count[z]} symbols")

    bank_syms = sorted(n for n in symbols if BANK_RE.search(n))
    print(f"  bank_like_symbol_names: {len(bank_syms)}")
    if bank_syms:
        for name in bank_syms[:40]:
            print(f"    {name}: {fmt_hex(symbols[name])}")
        if len(bank_syms) > 40:
            print(f"    ... {len(bank_syms) - 40} more")

    named_sections = bank_sections(symbols)
    print(f"  bank_sections_with_bounds: {len(named_sections)}")
    for name, head, tail, size in named_sections[:40]:
        print(f"    {name}: head={fmt_hex(head)} tail={fmt_hex(tail)} size={size}")
    if len(named_sections) > 40:
        print(f"    ... {len(named_sections) - 40} more")
    if named_sections:
        print(
            "  bank_section_payload_sum: "
            f"{sum(size for _, _, _, size in named_sections)} "
            "(mechanical sum; overlapping aliases may double-count)"
        )

    # Section placement summary
    for sec in SECTIONS:
        head = symbols.get(f"__{sec}_head")
        if head is not None:
            print(f"  section_{sec}_zone: {zone_name(head)} at {fmt_hex(head)}")


def print_crt_drag(symbols: dict[str, int], spans: list[tuple[str, int, int]]) -> None:
    print("\n[crt_startup_drag]")
    print(
        "note: CRT/stdio/heap symbols and large spans near startup — "
        "measure before micro-shrinking gameplay; spans are triage only"
    )
    crt_names = sorted(n for n in symbols if CRT_RE.search(n))
    if not crt_names:
        print("  crt_like_symbols: none")
    else:
        print(f"  crt_like_symbols: {len(crt_names)}")
        for name in crt_names[:50]:
            print(f"    {name}: {fmt_hex(symbols[name])}")
        if len(crt_names) > 50:
            print(f"    ... {len(crt_names) - 50} more")

    crt_spans = [(n, a, s) for n, a, s in spans if CRT_RE.search(n)]
    crt_spans.sort(key=lambda x: x[2], reverse=True)
    print("  top_crt_like_spans:")
    if not crt_spans:
        print("    none")
    else:
        for name, addr, size in crt_spans[:15]:
            print(f"    {name}: span={size} at {fmt_hex(addr)}")

    # crude CRT tax: sum of top CRT-like spans (overlapping risk → ESTIMADO only)
    tax = sum(s for _, _, s in crt_spans[:20])
    print(f"  crude_crt_span_tax_top20: ≈{tax} bytes (ESTIMADO, may overlap)")



def collect_target_row(map_path: Path, symbols: dict[str, int]) -> dict[str, object]:
    """One mechanical row for multi-target matrix (triage, not proof)."""
    code_head = symbols.get("__CODE_head")
    code_tail = section_tail(symbols, "CODE")
    code_size = None
    if code_head is not None and code_tail is not None:
        code_size = code_tail - code_head
    elif "__CODE_size" in symbols:
        code_size = symbols["__CODE_size"]
    bss_end = symbols.get("__BSS_END_tail")
    if bss_end is None:
        bss_end = symbols.get("__BSS_tail")
    stack_top = symbols.get("TAR__register_sp")
    if stack_top is None:
        stack_top = symbols.get("__register_sp")
    gap = None
    if stack_top is not None and bss_end is not None:
        gap = stack_top - bss_end
    bankish = sum(1 for n in symbols if BANK_RE.search(n))
    named_banks = bank_sections(symbols)
    bank_payload = sum(size for _, _, _, size in named_banks)
    bank_max = max((size for _, _, _, size in named_banks), default=0)
    # Heuristic: CODE head in $C000+ likely bank window
    code_zone = zone_name(code_head) if code_head is not None else "unknown"
    return {
        "map": str(map_path),
        "target_id": map_path.stem,
        "code_size": code_size,
        "code_zone": code_zone,
        "bss_end": bss_end,
        "stack_top": stack_top,
        "stack_gap": gap,
        "bank_like_symbols": bankish,
        "bank_sections": len(named_banks),
        "bank_payload": bank_payload,
        "bank_max": bank_max,
    }


def print_target_row(row: dict[str, object]) -> None:
    print("\n[target_row]")
    print(f"  target_id: {row['target_id']}")
    print(f"  map: {row['map']}")
    print(f"  code_size: {row['code_size'] if row['code_size'] is not None else 'n/a'}")
    print(f"  code_zone: {row['code_zone']}")
    print(f"  bss_end: {fmt_hex(row['bss_end'] if isinstance(row['bss_end'], int) else None)}")
    print(f"  stack_top: {fmt_hex(row['stack_top'] if isinstance(row['stack_top'], int) else None)}")
    print(f"  stack_gap: {row['stack_gap'] if row['stack_gap'] is not None else 'n/a'}")
    print(f"  bank_like_symbols: {row['bank_like_symbols']}")
    print(f"  bank_sections: {row['bank_sections']}")
    print(f"  bank_payload: {row['bank_payload']}")
    print(f"  bank_max: {row['bank_max']}")
    print(
        "  note: ceilings/floors are project policy — this row only reports measured markers; "
        "paged_slot code_zone must not be treated as exclusive 48K resident without bank proof"
    )


def print_multi_map_matrix(rows: list[dict[str, object]]) -> None:
    print("\n[multi_map_matrix]")
    if len(rows) < 2:
        print("  note: need --all with >=2 maps for matrix compare")
        return
    print("  target_id | code_size | code_zone | stack_gap | bank_sections | bank_payload | bank_max")
    for row in rows:
        print(
            f"  {row['target_id']} | {row['code_size']} | {row['code_zone']} | "
            f"{row['stack_gap']} | {row['bank_sections']} | {row['bank_payload']} | "
            f"{row['bank_max']}"
        )
    print(
        "  note: mechanical multi-target triage — apply project resident ceiling and "
        "stack-gap floor per row; reject candidates that fail any target"
    )

def print_one(map_path: Path) -> dict[str, object]:
    symbols = load_symbol_table(map_path)[0]
    print(f"map: {map_path}")
    try:
        st = map_path.stat()
        print(f"map_mtime: {int(st.st_mtime)} size={st.st_size}")
    except OSError:
        pass
    if not symbols:
        print(
            "warning: no z88dk-style symbols parsed; exact section/symbol sizes "
            "unavailable for this map dialect"
        )
    for name in IMPORTANT:
        if name in symbols:
            print(f"{name}: {fmt_hex(symbols[name])}")

    print("\n[section_summary]")
    rows = section_summary(symbols)
    print("none" if not rows else "\n".join(rows))

    stack_top = symbols.get("TAR__register_sp")
    if stack_top is None:
        stack_top = symbols.get("__register_sp")
    bss_end = symbols.get("__BSS_END_tail")
    if bss_end is None:
        bss_end = symbols.get("__BSS_tail")
    if stack_top is not None and bss_end is not None:
        gap = stack_top - bss_end
        print(f"\nstack_gap: {gap} bytes ({fmt_hex(stack_top)} - {fmt_hex(bss_end)})")

    print("\n[address_spans_not_exact_symbol_sizes]")
    print(
        "note: span is section-bounded when CODE/DATA/BSS markers exist, but still "
        "not a proven function/object size; use as triage only"
    )
    spans = symbol_spans(symbols)
    print(
        "none"
        if not spans
        else "\n".join(
            f"{name}: span={size} bytes at {fmt_hex(addr)}"
            for name, addr, size in spans[:30]
        )
    )

    heavy = sorted(name for name in symbols if HEAVY_RE.search(name))
    print("\n[heavy_symbols]")
    print("none" if not heavy else "\n".join(heavy[:60]))

    print_resident_banked(symbols, spans)
    print_crt_drag(symbols, spans)
    row = collect_target_row(map_path, symbols)
    print_target_row(row)
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", nargs="?", default=".")
    parser.add_argument("--all", action="store_true", help="summarize every map under target")
    args = parser.parse_args()
    target = Path(args.target).resolve()
    maps = map_candidates(target)
    if not maps:
        print(f"error: no .map file found under {target}")
        return 2
    if len(maps) > 1 and not args.all and not target.is_file():
        print("error: multiple .map files found; pass an explicit map path or --all")
        print("[map_candidates]")
        for path in maps:
            stat = path.stat()
            print(f"  {path} size={stat.st_size} mtime={int(stat.st_mtime)}")
        return 2
    rows: list[dict[str, object]] = []
    for idx, map_path in enumerate(maps):
        if idx:
            print("\n---")
        row = print_one(map_path)
        if row:
            rows.append(row)
    if len(rows) >= 2:
        print_multi_map_matrix(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
