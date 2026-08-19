#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

COMMON_SCRIPTS = Path(__file__).resolve().parents[2] / "shrink-z80" / "scripts"
if str(COMMON_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(COMMON_SCRIPTS))

from scan_common import fmt_hex, is_excluded, load_symbol_table  # noqa: E402

IMPORTANT = [
    "__CODE_head", "__CODE_tail", "__CODE_size", "__DATA_head", "__DATA_tail", "__DATA_size",
    "__BSS_head", "__BSS_tail", "__BSS_END_tail", "__BSS_UNINITIALIZED_tail", "CRT_STACK_SIZE",
    "TAR__register_sp", "__register_sp", "CRT_ORG_CODE", "startup",
]
HOT_NAME_RE = re.compile(r"(isr|irq|interrupt|fast|uart|poll|audio|beep|loader|draw|copy|blit|sprite)", re.IGNORECASE)
SYSTEM_NAME_RE = re.compile(r"(rst8|esxdos|divmmc|printer|frames|sysvar|udg|overlay|bank|slot)", re.IGNORECASE)


def parse_args(argv: list[str]) -> tuple[str, Path]:
    sym_base = "auto"
    args = list(argv)
    if args and args[0] == "--sym-base":
        if len(args) < 2 or args[1] not in {"auto", "hex", "decimal"}:
            raise SystemExit("usage: map_summary.py [--sym-base auto|hex|decimal] <mapfile-or-root>")
        sym_base = args[1]
        args = args[2:]
    elif args and args[0].startswith("--sym-base="):
        sym_base = args[0].split("=", 1)[1]
        if sym_base not in {"auto", "hex", "decimal"}:
            raise SystemExit("usage: map_summary.py [--sym-base auto|hex|decimal] <mapfile-or-root>")
        args = args[1:]
    return sym_base, Path(args[0] if args else ".").resolve()


def pick_symbol_file(path: Path) -> tuple[Path, list[Path], str]:
    if path.is_file():
        return path, [path], "explicit file"
    maps = sorted(p for p in path.rglob("*.map") if not is_excluded(p))
    syms = sorted(p for p in path.rglob("*.sym") if not is_excluded(p))
    candidates = maps + syms
    if not candidates:
        raise FileNotFoundError(f"no .map or .sym file found under {path}")
    if len(maps) > 1:
        raise SystemExit("multiple .map files found; pass the intended linked artifact explicitly")
    if len(maps) == 1:
        return maps[0], candidates, "only .map outside skipped dirs"
    if len(syms) > 1:
        raise SystemExit("multiple .sym files found; pass the intended symbol artifact explicitly")
    return syms[0], candidates, "only .sym outside skipped dirs"


def symbol_spans(symbols: dict[str, int]) -> list[tuple[str, int, int]]:
    ordered = sorted((addr, name) for name, addr in symbols.items())
    spans: list[tuple[str, int, int]] = []
    for idx, (addr, name) in enumerate(ordered[:-1]):
        next_addr = ordered[idx + 1][0]
        size = next_addr - addr
        if 0 < size < 0x8000:
            spans.append((name, addr, size))
    return sorted(spans, key=lambda item: item[2], reverse=True)


def first_symbol(symbols: dict[str, int], *names: str) -> int | None:
    for name in names:
        if name in symbols:
            return symbols[name]
    return None


def main() -> int:
    sym_base, target = parse_args(sys.argv[1:])
    symbol_path, candidates, selected_reason = pick_symbol_file(target)
    symbols, formats, bases, duplicates = load_symbol_table(symbol_path, sym_base)
    ambiguous = "ambiguous-plain-numeric" in bases
    print(f"symbol_file: {symbol_path}")
    print(f"selected_reason: {selected_reason}")
    print(f"candidate_files: {len(candidates)}")
    root_for_rel = target if target.is_dir() else target.parent
    for idx, path in enumerate(candidates[:20], start=1):
        try:
            shown = path.relative_to(root_for_rel)
        except ValueError:
            shown = path
        print(f"  {idx}. {shown}")
    if sum(1 for p in candidates if p.suffix.lower() == ".map") > 1:
        print("warning: multiple .map files found; verify selected file is the final linked artifact")
    print("formats: " + (", ".join(f"{k}={v}" for k, v in sorted(formats.items())) or "unrecognized"))
    print("address_base: " + (", ".join(f"{k}={v}" for k, v in sorted(bases.items())) or "unknown"))
    if ambiguous:
        print("warning: plain 4-digit .sym addresses are ambiguous; pass --sym-base hex or --sym-base decimal before treating gaps/regions as proof")
    if len([k for k in bases if k not in {"ambiguous-plain-numeric"}]) > 1:
        print("warning: mixed address bases; verify source format before treating gaps as proof")
    for name, addresses in sorted(duplicates.items()):
        rendered = ", ".join(fmt_hex(address) for address in sorted(addresses))
        print(f"warning: conflicting duplicate symbol {name}: {rendered}; first value retained")
    if not symbols:
        print("warning: no supported symbol lines parsed")
        return 0
    for name in IMPORTANT:
        if name in symbols:
            print(f"{name}: {fmt_hex(symbols[name])}")

    stack_top = first_symbol(symbols, "TAR__register_sp", "__register_sp")
    bss_end = first_symbol(symbols, "__BSS_END_tail", "__BSS_tail")
    if stack_top is not None and bss_end is not None:
        if ambiguous:
            print("stack_gap: unverified (ambiguous plain numeric .sym addresses)")
        else:
            gap = stack_top - bss_end
            print(f"stack_gap: {gap} bytes ({fmt_hex(stack_top)} - {fmt_hex(bss_end)})")

    print("\n[largest_symbol_spans]")
    print("note: approximate; derived from next symbol address, not declared object size")
    spans = symbol_spans(symbols) if not ambiguous else []
    if not spans:
        print("none")
    else:
        for name, addr, size in spans[:30]:
            print(f"{name}: {size} bytes at {fmt_hex(addr)}")

    heavy = sorted(name for name in symbols if re.search(r"(__mul|__div|__mod|printf|sprintf|snprintf|scanf|malloc|free|strlen|strcmp|memcpy|memset)", name))
    print("\n[heavy_symbols]")
    print("\n".join(heavy[:40]) if heavy else "none")

    print("\n[contention_watch_symbols]")
    contented = [(name, addr) for name, addr in sorted(symbols.items(), key=lambda item: item[1]) if 0x4000 <= addr <= 0x7FFF and HOT_NAME_RE.search(name)] if not ambiguous else []
    if not contented:
        print("none")
    else:
        for name, addr in contented[:40]:
            print(f"{name}: {fmt_hex(addr)}")
        print("note: hot/ISR/UART/audio/draw symbols in $4000..$7FFF may gain ULA wait states on 48K Spectrum")

    print("\n[firmware_region_symbols]")
    firmware = [(name, addr) for name, addr in sorted(symbols.items(), key=lambda item: item[1]) if (0x5B00 <= addr <= 0x5CFF) or SYSTEM_NAME_RE.search(name)] if not ambiguous else []
    if not firmware:
        print("none")
    else:
        for name, addr in firmware[:40]:
            region = "printer-buffer" if 0x5B00 <= addr <= 0x5BFF else "sysvars" if 0x5C00 <= addr <= 0x5CFF else "name-clue"
            print(f"{name}: {fmt_hex(addr)} ({region})")
        print("note: verify ROM/esxDOS/divMMC/RST8 interactions before treating these regions as free scratch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
