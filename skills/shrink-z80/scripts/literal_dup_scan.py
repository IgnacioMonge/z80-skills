#!/usr/bin/env python3
from __future__ import annotations

import ast
import re
import sys
from collections import defaultdict
from pathlib import Path

from scan_common import ASM_EXTS, C_EXTS, LISTING_EXTS, TEXT_EXTS, active_source_lines, parse_byte_payload, read_text_lines, rel_path, resolve_target_scope, source_kind, print_scope

C_STRING_RE = re.compile(r'"((?:[^"\\]|\\.)+)"')
ASM_STRING_RE = re.compile(r"\b(?:db|defb)\s+\"([^\"]+)\"", re.IGNORECASE)
ASM_BYTES_RE = re.compile(r"\b(?:db|defb|\.byte)\b\s+(.+)", re.IGNORECASE)

def decode_c_string(raw: str) -> str:
    try:
        value = ast.literal_eval('"' + raw + '"')
        return value if isinstance(value, str) else raw
    except Exception:
        return raw


def add_hit(store: dict[str, list[tuple[str, str]]], key: str, kind: str, where: str) -> None:
    if len(key) >= 4:
        store[key].append((kind, where))


def run_stats(values: list[int]) -> tuple[int, int, int]:
    runs = 0
    run_bytes = 0
    longest = 0
    idx = 0
    while idx < len(values):
        run = 1
        while idx + run < len(values) and values[idx + run] == values[idx] and run < 255:
            run += 1
        if run >= 3:
            runs += 1
            run_bytes += run
            longest = max(longest, run)
        idx += run
    return runs, run_bytes, longest


def print_duplicates(title: str, rows: list[tuple[str, list[tuple[str, str]]]]) -> None:
    print(f"\n[{title}]")
    if not rows:
        print("none")
        return
    for literal, places in rows[:40]:
        print(f"{len(places)}x | {literal}")
        for kind, place in places[:8]:
            print(f"  [{kind}] {place}")


def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    scope = resolve_target_scope(target, TEXT_EXTS)
    hits: dict[str, list[tuple[str, str]]] = defaultdict(list)
    rle_candidates: list[tuple[int, int, int, int, str, str, str]] = []
    print_scope(scope)

    for path in scope.files:
        kind = source_kind(path, scope.base)
        suffix = path.suffix.lower()
        lines, skipped = read_text_lines(path)
        if skipped:
            continue
        for lineno, line in active_source_lines(path, lines):
            if line.lstrip().startswith("#include"):
                continue
            rel = f"{rel_path(path, scope.base)}:{lineno}"
            if suffix in C_EXTS:
                for match in C_STRING_RE.findall(line):
                    add_hit(hits, decode_c_string(match), kind, rel)
            if suffix in ASM_EXTS | LISTING_EXTS:
                for match in ASM_STRING_RE.findall(line):
                    add_hit(hits, match, kind, rel)
            byte_match = ASM_BYTES_RE.search(line)
            if byte_match:
                values = parse_byte_payload(byte_match.group(1))
                if len(values) >= 16:
                    runs, run_bytes, longest = run_stats(values)
                    if runs:
                        preview = ",".join(f"${value:02X}" for value in values[:12])
                        if len(values) > 12:
                            preview += ",..."
                        rle_candidates.append((len(values), runs, run_bytes, longest, kind, rel, preview))

    duplicate_rows = [(lit, places) for lit, places in hits.items() if len(places) > 1]
    duplicate_rows.sort(key=lambda item: (-len(item[1]), -len(item[0]), item[0]))
    source_dups = [(lit, places) for lit, places in duplicate_rows if sum(1 for kind, _ in places if kind == "source") > 1]
    generated_dups = [(lit, places) for lit, places in duplicate_rows if any(kind in {"generated_asm", "listing", "build_artifact", "dist"} for kind, _ in places)]
    mixed_echoes = [(lit, places) for lit, places in duplicate_rows if any(kind == "source" for kind, _ in places) and any(kind != "source" for kind, _ in places)]

    print_duplicates("source_duplicate_literals", source_dups)
    print_duplicates("generated_duplicate_literals_candidates_only", generated_dups)
    print_duplicates("mixed_source_generated_echoes", mixed_echoes)
    print("note: do not count duplicates between source and generated/listing as savings; C comments and #if 0 blocks are stripped before textual literal scanning")

    print("\n[rle_byte_table_candidates]")
    if not rle_candidates:
        print("none")
    else:
        rle_candidates.sort(key=lambda item: (-item[2], -item[3], item[5]))
        for raw, runs, run_bytes, longest, kind, where, preview in rle_candidates[:40]:
            print(f"[{kind}] {where}: raw={raw}B runs={runs} run_bytes={run_bytes} longest_run={longest} exact_codec_required | {preview}")
        print("note: no net saving is claimed here; count a concrete codec, decoder/setup/workspace bytes, and existing decoder reuse before accepting")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
