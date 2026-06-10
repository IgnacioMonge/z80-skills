#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

SYMBOL_RE = re.compile(r"^(\S+)\s*=\s*\$([0-9A-Fa-f]+)\s*;")
HEAVY_RE = re.compile(
    r"(__mul|__div|__mod|printf|sprintf|snprintf|scanf|malloc|free|strlen|strcmp|strcpy|strcat|memcpy|memset)"
)
CALL_RE = re.compile(
    r"\b(printf|sprintf|snprintf|scanf|malloc|free|strlen|strcmp|strcpy|strcat|memcpy|memset)\s*\("
)
ARITH_RE = re.compile(r"(?:=\s*[^;]*[*/%]\s*[^;]+|return\s+[^;]*[*/%]\s*[^;]+|[*/%]=)")
POWER_TWO_RE = re.compile(r"([/%]\s*(?:2|4|8|16|32|64|128|256)\b)")
SMALL_MUL_RE = re.compile(r"(\*\s*(?:3|5|6|7|9|10|12|15|17)\b)")
MEM_CONST_RE = re.compile(r"\b(memcpy|memset)\s*\([^;]*,\s*(\d+)\s*\)")
LOOP_RE = re.compile(r"\b(for|while)\s*\(")
LOOP_LIB_RE = re.compile(r"\b(strlen|strcmp|memcpy|memset)\s*\(")
PREFERRED_DIRS = ("src", "include", "overlay")


def pick_map(root: Path) -> Path | None:
    maps = sorted(
        root.rglob("*.map"), key=lambda item: item.stat().st_mtime, reverse=True
    )
    return maps[0] if maps else None


def load_heavy_symbols(map_path: Path) -> list[str]:
    symbols = []
    for line in map_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = SYMBOL_RE.match(line)
        if match and HEAVY_RE.search(match.group(1)):
            symbols.append(match.group(1))
    return sorted(set(symbols))


def scan_sources(
    root: Path,
) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
    calls: list[str] = []
    arith: list[str] = []
    const_arith: list[str] = []
    small_mem: list[str] = []
    loop_libs: list[str] = []
    bases = [root / name for name in PREFERRED_DIRS if (root / name).exists()]
    if not bases:
        bases = [root]
    for base in bases:
        for path in base.rglob("*.c"):
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            for lineno, line in enumerate(lines, start=1):
                stripped = line.strip()
                if CALL_RE.search(stripped):
                    calls.append(f"{path.relative_to(root)}:{lineno}: {stripped}")
                if (
                    ARITH_RE.search(stripped)
                    and not stripped.startswith(("#", "//"))
                    and "/*" not in stripped
                ):
                    arith.append(f"{path.relative_to(root)}:{lineno}: {stripped}")
                if (
                    POWER_TWO_RE.search(stripped) or SMALL_MUL_RE.search(stripped)
                ) and not stripped.startswith(("#", "//")):
                    const_arith.append(f"{path.relative_to(root)}:{lineno}: {stripped}")
                mem = MEM_CONST_RE.search(stripped)
                if mem and int(mem.group(2)) <= 16:
                    small_mem.append(f"{path.relative_to(root)}:{lineno}: {stripped}")
                if LOOP_RE.search(stripped):
                    window = "\n".join(lines[lineno - 1 : min(len(lines), lineno + 24)])
                    if LOOP_LIB_RE.search(window):
                        loop_libs.append(
                            f"{path.relative_to(root)}:{lineno}: {stripped}"
                        )
    return calls, arith, const_arith, small_mem, loop_libs


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    map_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else pick_map(root)
    print(f"root: {root}")
    print("\n[map_heavy_symbols]")
    if map_path and map_path.exists():
        print(f"map: {map_path}")
        heavy = load_heavy_symbols(map_path)
        if heavy:
            for name in heavy[:60]:
                print(name)
        else:
            print("none")
    else:
        print("no map")

    calls, arith, const_arith, small_mem, loop_libs = scan_sources(root)
    print("\n[c_function_candidates]")
    if calls:
        for item in calls[:60]:
            print(item)
    else:
        print("none")

    print("\n[c_arithmetic_candidates]")
    if arith:
        for item in arith[:80]:
            print(item)
    else:
        print("none")

    print("\n[constant_arithmetic_candidates]")
    if const_arith:
        for item in const_arith[:80]:
            print(item)
        print(
            "note: shifts/adds/masks only if signedness and generated ASM preserve behavior"
        )
    else:
        print("none")

    print("\n[small_mem_helper_candidates]")
    if small_mem:
        for item in small_mem[:80]:
            print(item)
        print(
            "note: tiny memcpy/memset calls often inline smaller than a linked helper, but map must prove helper drag"
        )
    else:
        print("none")

    print("\n[loop_libcall_candidates]")
    if loop_libs:
        for item in loop_libs[:80]:
            print(item)
        print(
            "note: inspect loop body for invariant strlen/strcmp/memcpy/memset and latency spikes"
        )
    else:
        print("none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
