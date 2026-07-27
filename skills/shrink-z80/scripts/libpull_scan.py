#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from scan_common import C_EXTS, TEXT_EXTS, active_source_lines, map_symbol_is_runtime, read_text_lines, rel_path, resolve_scope, resolve_target_scope, print_scope

HELPER_PATTERNS = {
    "sdcc": re.compile(r"(__mul|__div|__mod|printf|sprintf|snprintf|scanf|malloc|free|strlen|strcmp|strcpy|strcat|memcpy|memset)", re.IGNORECASE),
    "sccz80": re.compile(r"(l_(?:mul|mult|div|mod|long)|printf|sprintf|snprintf|scanf|malloc|free|strlen|strcmp|strcpy|strcat|memcpy|memset)", re.IGNORECASE),
    "unknown": re.compile(r"(__mul|__div|__mod|l_(?:mul|mult|div|mod|long)|printf|sprintf|snprintf|scanf|malloc|free|strlen|strcmp|strcpy|strcat|memcpy|memset)", re.IGNORECASE),
}
CALL_RE = re.compile(r"\b(printf|sprintf|snprintf|scanf|malloc|free|strlen|strcmp|strcpy|strcat|memcpy|memset)\s*\(")
ARITH_RE = re.compile(
    r"(?:(?:\b[A-Za-z_]\w*|\d+|\)|\])\s*[*/%]\s*(?:\b[A-Za-z_]\w*|\d+|\(|\[)|[*/%]=)"
)
C_LITERAL_RE = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')
C_TYPE_RE = r"(?:void|char|short|int|long|float|double|[A-Za-z_]\w*_t|struct\s+\w+)"
POINTER_DECL_RE = re.compile(
    r"^\s*(?:(?:static|const|volatile|register|extern)\s+)*(?:(?:signed|unsigned)\s+)?"
    r"(?:struct\s+\w+|[A-Za-z_]\w*)\s+\*+\s*[A-Za-z_]\w*"
)
TYPE_POINTER_RE = re.compile(rf"\b{C_TYPE_RE}\s*\*+|\b(?:const\s+)?(?:[A-Z][A-Za-z0-9_]*|[A-Za-z_]\w*_t)\s*\*+")
CAST_DEREF_RE = re.compile(rf"\(\s*(?:const\s+)?{C_TYPE_RE}\s*\*?\s*\)\s*\*+")
POST_CONDITION_DEREF_RE = re.compile(r"\)\s*\*+\s*(?=[A-Za-z_(])")
UNARY_STAR_RE = re.compile(r"(\b(?:return|else|case)\b|[({=,:;!&|?])\s*\*+\s*(?=[A-Za-z_(])")
LEADING_DEREF_RE = re.compile(r"^\s*\*+\s*(?=[A-Za-z_(])")
POWER_TWO_RE = re.compile(r"([/%]\s*(?:2|4|8|16|32|64|128|256)\b)")
SMALL_MUL_RE = re.compile(r"(\*\s*(?:3|5|6|7|9|10|12|15|17)\b)")
MEM_CONST_RE = re.compile(r"\b(memcpy|memset)\s*\([^;]*,\s*(\d+)\s*\)")
LOOP_RE = re.compile(r"\b(for|while)\s*\(")
LOOP_LIB_RE = re.compile(r"\b(strlen|strcmp|memcpy|memset)\s*\(")
SYMBOL_RE = re.compile(r"^(\S+)\s*=\s*\$([0-9A-Fa-f]+)\s*;")


def detect_backend(target: Path) -> str:
    scope = resolve_scope(target, TEXT_EXTS)
    parts: list[str] = []
    for path in scope.files[:200]:
        lines, skipped = read_text_lines(path)
        if not skipped:
            parts.append("\n".join(lines)[:4000])
    blob = "\n".join(parts).lower()
    if "sccz80" in blob or "-compiler=sccz80" in blob:
        return "sccz80"
    if "sdcc" in blob or "-compiler=sdcc" in blob or "--sdcccall" in blob:
        return "sdcc"
    return "unknown"


def map_candidates(root: Path) -> list[Path]:
    if root.is_file() and root.suffix.lower() == ".map":
        return [root]
    if root.is_dir():
        return sorted(root.rglob("*.map"))
    return []


def choose_map(project: Path, explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit).resolve()
    maps = map_candidates(project)
    return maps[0] if len(maps) == 1 else None


def load_heavy_symbols(map_path: Path, backend: str) -> list[str]:
    regex = HELPER_PATTERNS.get(backend, HELPER_PATTERNS["unknown"])
    symbols: list[str] = []
    for line in map_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = SYMBOL_RE.match(line)
        if match and map_symbol_is_runtime(line) and regex.search(match.group(1)):
            symbols.append(match.group(1))
    return sorted(set(symbols))


def scan_sources(target: Path) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
    scope = resolve_target_scope(target, C_EXTS)
    calls: list[str] = []
    arith: list[str] = []
    const_arith: list[str] = []
    small_mem: list[str] = []
    loop_libs: list[str] = []
    for path in scope.files:
        if path.suffix.lower() == ".h":
            continue
        lines, skipped = read_text_lines(path)
        if skipped:
            continue
        rows = active_source_lines(path, lines)
        active_lines = [line for _, line in rows]
        for idx, (lineno, line) in enumerate(rows):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            where = f"{rel_path(path, scope.base)}:{lineno}: {stripped}"
            arithmetic_line = C_LITERAL_RE.sub("", stripped)
            arithmetic_line = POINTER_DECL_RE.sub("", arithmetic_line, count=1)
            arithmetic_line = CAST_DEREF_RE.sub("", arithmetic_line)
            arithmetic_line = TYPE_POINTER_RE.sub("", arithmetic_line)
            arithmetic_line = POST_CONDITION_DEREF_RE.sub(") ", arithmetic_line)
            arithmetic_line = UNARY_STAR_RE.sub(r"\1 ", arithmetic_line)
            arithmetic_line = LEADING_DEREF_RE.sub("", arithmetic_line)
            if CALL_RE.search(stripped):
                calls.append(where)
            if ARITH_RE.search(arithmetic_line):
                arith.append(where)
            if POWER_TWO_RE.search(arithmetic_line) or SMALL_MUL_RE.search(arithmetic_line):
                const_arith.append(where)
            mem = MEM_CONST_RE.search(stripped)
            if mem and int(mem.group(2)) <= 16:
                small_mem.append(where)
            if LOOP_RE.search(stripped):
                window = "\n".join(active_lines[idx : min(len(active_lines), idx + 24)])
                if LOOP_LIB_RE.search(window):
                    loop_libs.append(where)
    return calls, arith, const_arith, small_mem, loop_libs


def classify_symbol(name: str, backend: str) -> str:
    lower = name.lower()
    if backend == "sccz80":
        return "possible roots: sccz80/z88dk helper; manual confirmation in generated ASM/listing required"
    if any(word in lower for word in ("__mul", "l_mul", "l_mult")):
        return "possible roots: C multiplication candidates"
    if any(word in lower for word in ("__div", "__mod", "l_div", "l_mod")):
        return "possible roots: C division/modulo candidates"
    if any(word in lower for word in ("printf", "sprintf", "snprintf", "scanf")):
        return "possible roots: formatted I/O call candidates"
    if any(word in lower for word in ("memcpy", "memset")):
        return "possible roots: memcpy/memset calls, tiny mem helpers, or loop libcalls"
    if any(word in lower for word in ("strlen", "strcmp", "strcpy", "strcat")):
        return "possible roots: string calls or loop libcalls"
    if any(word in lower for word in ("malloc", "free")):
        return "possible roots: allocator call candidates"
    return "possible roots: inspect map and call sites manually"


def rows_matching(rows: list[str], words: tuple[str, ...]) -> list[str]:
    return [row for row in rows if any(word in row.lower() for word in words)][:8] if words else rows[:8]


def source_roots_for_symbol(name: str, calls, arith, const_arith, small_mem, loop_libs) -> list[tuple[str, list[str]]]:
    lower = name.lower()
    groups: list[tuple[str, list[str]]] = []
    def add(label: str, rows: list[str]) -> None:
        if rows:
            groups.append((label, rows[:8]))
    if any(word in lower for word in ("__mul", "l_mul", "l_mult")):
        add("arithmetic candidates", const_arith + arith)
    if any(word in lower for word in ("__div", "__mod", "l_div", "l_mod")):
        add("division/modulo candidates", const_arith + arith)
    if any(word in lower for word in ("printf", "sprintf", "snprintf")):
        add("formatted-output calls", rows_matching(calls, ("printf", "sprintf", "snprintf")))
    if "scanf" in lower:
        add("formatted-input calls", rows_matching(calls, ("scanf",)))
    if any(word in lower for word in ("memcpy", "memset")):
        add("memory helper calls", rows_matching(calls, ("memcpy", "memset")) + small_mem + rows_matching(loop_libs, ("memcpy", "memset")))
    if any(word in lower for word in ("strlen", "strcmp", "strcpy", "strcat")):
        add("string helper calls", rows_matching(calls, ("strlen", "strcmp", "strcpy", "strcat")) + rows_matching(loop_libs, ("strlen", "strcmp")))
    if any(word in lower for word in ("malloc", "free")):
        add("allocator calls", rows_matching(calls, ("malloc", "free")))
    return groups


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", nargs="?", default=".")
    parser.add_argument("map", nargs="?")
    args = parser.parse_args()
    target = Path(args.target).resolve()
    scope = resolve_target_scope(target, C_EXTS)
    print_scope(scope)
    backend = detect_backend(target)
    print(f"backend: {backend}")
    if backend == "sccz80":
        print("backend_note: sccz80 helper matching is candidate/manual-only; verify with generated ASM/listing before byte claims")

    map_path = choose_map(target, args.map)
    heavy: list[str] = []
    print("\n[map_heavy_symbols]")
    if map_path and map_path.exists():
        print(f"map: {map_path}")
        heavy = load_heavy_symbols(map_path, backend)
        print("none" if not heavy else "\n".join(heavy[:80]))
    else:
        maps = map_candidates(target)
        if len(maps) > 1:
            print("multiple maps found; pass explicit map path")
            for path in maps:
                stat = path.stat()
                print(f"  {path} size={stat.st_size} mtime={int(stat.st_mtime)}")
        else:
            print("no map")

    calls, arith, const_arith, small_mem, loop_libs = scan_sources(target)
    sections = [
        ("c_function_candidates", calls, 80),
        ("c_arithmetic_candidates", arith, 100),
        ("constant_arithmetic_candidates", const_arith, 100),
        ("small_mem_helper_candidates", small_mem, 100),
        ("loop_libcall_candidates", loop_libs, 100),
    ]
    for title, rows, limit in sections:
        print(f"\n[{title}]")
        print("none" if not rows else "\n".join(rows[:limit]))

    print("\n[possible_heavy_symbol_roots]")
    if heavy:
        for name in heavy[:80]:
            print(f"{name}: {classify_symbol(name, backend)}")
            groups = source_roots_for_symbol(name, calls, arith, const_arith, small_mem, loop_libs)
            if not groups:
                print("  source roots: none found by heuristic; inspect generated ASM/map manually")
                continue
            for label, rows in groups:
                print(f"  {label}:")
                for row in rows:
                    print(f"    {row}")
        print("note: correlation is heuristic. Main agent must verify exact helper root in generated ASM/map before claiming libpull deletion.")
    else:
        print("none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
