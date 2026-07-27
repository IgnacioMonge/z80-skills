#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

from scan_common import ASM_EXTS, C_EXTS, SOURCE_EXTS, active_source_lines, branch_targets, read_text_lines, rel_path, resolve_target_scope, source_kind, split_label, print_scope

C_FUNC_HEAD_RE = re.compile(r"^\s*(?:static\s+)?[A-Za-z_][\w\s\*]*\s+([A-Za-z_]\w*)\s*\([^;]*\)\s*(?:\{|$)")
CALLLIKE_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
INDIRECT_RE = re.compile(r"\b(?:jp|call)\s+\((hl|ix|iy)\)|\(\s*\*\s*\w+\s*\)\s*\(", re.IGNORECASE)
PUBLIC_RE = re.compile(r"^\s*(?:public|global|xdef|export)\s+(.+)$", re.IGNORECASE)
ENTRYPOINTS = {"main", "_main", "start", "_start", "crt0", "_crt0", "init", "_init"}


def symbol_aliases(name: str) -> set[str]:
    if name.startswith("_") and len(name) > 1:
        return {name, name[1:]}
    return {name, "_" + name}


def add_ref(refs: Counter[str], name: str) -> None:
    for alias in symbol_aliases(name):
        refs[alias] += 1


def public_symbols(line: str) -> list[str]:
    match = PUBLIC_RE.match(line)
    if not match:
        return []
    names = []
    for item in re.split(r"[,\s]+", match.group(1).strip()):
        if item:
            names.append(item)
    return names


def c_definition_name(lines: list[str], idx: int) -> str | None:
    line = lines[idx]
    stripped = line.strip()
    if stripped.startswith(("if", "while", "for", "switch")):
        return None
    match = C_FUNC_HEAD_RE.match(line)
    if not match:
        return None
    if "{" in line or (idx + 1 < len(lines) and lines[idx + 1].strip().startswith("{")):
        return match.group(1)
    return None


def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    scope = resolve_target_scope(target, SOURCE_EXTS)
    print_scope(scope)
    defined: dict[str, list[str]] = {}
    refs: Counter[str] = Counter()
    indirect: list[str] = []
    exports: list[str] = []
    rooted = set(ENTRYPOINTS)

    file_rows: dict[Path, list[tuple[int, str]]] = {}
    for path in scope.files:
        lines, skipped = read_text_lines(path)
        if skipped:
            continue
        rows = active_source_lines(path, lines)
        file_rows[path] = rows
        text_lines = [line for _, line in rows]
        kind = source_kind(path, scope.base)
        suffix = path.suffix.lower()
        for idx, (lineno, line) in enumerate(rows):
            stripped = line.strip()
            where = f"[{kind}] {rel_path(path, scope.base)}:{lineno}: {stripped}"
            if INDIRECT_RE.search(line):
                indirect.append(where)
            for symbol in public_symbols(line):
                exports.append(where)
                rooted.update(symbol_aliases(symbol))
            if suffix in ASM_EXTS:
                label, _ = split_label(line)
                if label:
                    defined.setdefault(label, []).append(where)
            elif suffix in C_EXTS:
                name = c_definition_name(text_lines, idx)
                if name:
                    defined.setdefault(name, []).append(where)

    for path, rows in file_rows.items():
        suffix = path.suffix.lower()
        text_lines = [line for _, line in rows]
        for idx, (_lineno, line) in enumerate(rows):
            if suffix in ASM_EXTS:
                for target_name in branch_targets(line):
                    add_ref(refs, target_name)
            elif suffix in C_EXTS:
                def_name = c_definition_name(text_lines, idx)
                for name in CALLLIKE_RE.findall(line):
                    if name != def_name:
                        add_ref(refs, name)

    print("\n[symbols_defined]")
    print("none" if not defined else "\n".join(f"{name}: {places[0]}" for name, places in sorted(defined.items())[:200]))
    print("\n[call_targets]")
    called = [(name, count) for name, count in refs.most_common(200) if name in defined]
    print("none" if not called else "\n".join(f"{name}: {count}" for name, count in called))
    print("\n[indirect_dispatch_sites]")
    print("none" if not indirect else "\n".join(indirect[:80]))
    print("\n[public_exports]")
    print("none" if not exports else "\n".join(exports[:80]))
    print("\n[externally_rooted_or_entry_candidates]")
    external = [name for name in sorted(defined) if any(alias in rooted for alias in symbol_aliases(name))]
    print("none" if not external else "\n".join(f"{name}: {defined[name][0]}" for name in external[:120]))
    print("\n[possible_unreferenced_symbols]")
    suspects = [
        name for name in sorted(defined)
        if not name.startswith((".", "__"))
        and not any(refs.get(alias, 0) for alias in symbol_aliases(name))
        and not any(alias in rooted for alias in symbol_aliases(name))
    ]
    print("none" if not suspects else "\n".join(f"{name}: {defined[name][0]}" for name in suspects[:120]))
    print("note: candidate only; indirect dispatch, linker roots, exports, startup labels, and generated references require manual proof")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
