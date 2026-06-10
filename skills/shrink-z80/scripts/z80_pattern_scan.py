#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

TEXT_EXTS = {".asm", ".s", ".inc", ".c", ".h", ".i", ".opt", ".lst", ".rul"}
PREFERRED_DIRS = ("src", "asm", "include", "overlay")
ASM_EXTS = {".asm", ".s", ".inc", ".opt", ".lst"}
C_EXTS = {".c", ".h", ".i"}


@dataclass
class Hit:
    path: Path
    line_no: int
    text: str
    note: str


PATTERNS: dict[str, tuple[str, str]] = {
    "block-repeat-op": (
        r"\b(ldir|lddr|cpir|cpdr|inir|indr|otir|otdr)\b",
        "block ops may be compact already; count setup cost, BC=0 guard, direction, and helper reuse",
    ),
    "stack-blitter-shape": (
        r"\b(ld\s+sp\s*,|ex\s+\(sp\)\s*,|push\s+(af|bc|de|hl|ix|iy))",
        "stack-copy or stack-temp trick; can be gold for speed/bytes but requires SP and interrupt proof",
    ),
    "indexed-hot-path": (
        r"\b(i[xy][hl]|[,(]\s*i[xy]\s*[+-]|ld\s+i[xy]\s*,|push\s+i[xy]|pop\s+i[xy])",
        "IX/IY prefixes cost bytes; verify ABI, then look for base-register or layout alternatives",
    ),
    "page-local-indexing": (
        r"\b(inc\s+l|dec\s+l|ld\s+h\s*,|ld\s+l\s*,|add\s+a\s*,\s*l)\b",
        "page-local table/screen indexing may replace 16-bit math or 2-byte pointers; prove alignment and page crossings",
    ),
    "timing-pad-or-cycle-equalizer": (
        r"\b(nop|djnz\s+\$|jr\s+\$|defs\s+\d+)\b",
        "possible timing pad; keep as rejected/unsafe unless audio, raster, loader, or I/O cadence is disproven",
    ),
    "dynamic-vector-dispatch": (
        r"\b(jp|call)\s+\((hl|ix|iy)\)",
        "pointer dispatch may indicate bytecode/token interpreter, vector table, or generated code opportunity",
    ),
    "compiled-sprite-shape": (
        r"\b(ld\s+\(hl\)\s*,|add\s+hl\s*,\s*(?:de|bc|sp)|pop\s+(?:af|de))\b",
        "screen writer may be compiled-sprite or stack-table code; check generated draw code, line-skip tables, and clipping fallback",
    ),
    "r-register-rng": (
        r"\bld\s+a\s*,\s*r\b",
        "R register can be a tiny counter/noise source; compare against heavier RNG only if determinism requirements allow it",
    ),
    "self-modifying-or-layout": (
        r"\b(ld\s+\([^)]*[+][^)]*\)\s*,|incbin|org\s+|phase\s+|dephase\s+|defs\s+|defc\s+)",
        "layout/data/code boundary may hide compression, overlays, SMC, or fall-through savings",
    ),
    "screen-anchor": (
        r"(\$|#|0x)(4000|5800|5b00|5c00|5c3a|ff58)\b|\b(16384|22528|23296|23552|23610|65368)\b",
        "fixed Spectrum address; look for screen-layout, attribute, stack-blit, and clipping-zone wins",
    ),
    "runtime-lib-trigger": (
        r"\b(printf|sprintf|snprintf|scanf|malloc|free|memcpy|memset|strcmp|strlen|strcpy|strcat)\s*\(",
        "possible libpull root; prove with map before claiming saving",
    ),
    "zero-load": (
        r"\bld\s+a\s*,\s*0\b|\bld\s+(b|c|d|e|h|l)\s*,\s*0\b",
        "zeroing alternatives may save flags/time only under exact register and flag preconditions",
    ),
    "wide-c-type": (
        r"\b(unsigned\s+int|int|uint16_t|size_t)\s+\w*(flag|state|mode|idx|index|count|len|x|y)\w*\b",
        "wide C scalar may force 16-bit code where byte range may be enough",
    ),
    "power-two-arithmetic": (
        r"([/%]\s*(2|4|8|16|32|64|128|256)\b|\*\s*(3|5|6|7|9|10|12|15|17)\b)",
        "constant arithmetic may become shifts/adds/masks; verify signedness and compiler output",
    ),
}

CALL_RE = re.compile(r"\bcall\s+([A-Za-z_.$?@][\w.$?@]*)", re.IGNORECASE)
RET_RE = re.compile(r"^\s*ret\b", re.IGNORECASE)
EXIT_RE = re.compile(r"^\s*(?:ret|jp\s+[^,;]+|jr\s+[^,;]+)\b", re.IGNORECASE)
LABEL_RE = re.compile(r"^([A-Za-z_.$?@][\w.$?@]*):\s*$")
DIRECTIVE_RE = re.compile(
    r"^\s*(?:public|extern|global|section|module|org|phase|dephase|def[bswcm]|db|dw|ds|defs|equ|include|incbin)\b",
    re.IGNORECASE,
)
LOOP_RE = re.compile(r"\b(for|while)\s*\(", re.IGNORECASE)
STRLEN_RE = re.compile(r"\b(strlen|strcmp|memcpy|memset)\s*\(", re.IGNORECASE)
SWITCH_RE = re.compile(r"\bswitch\s*\(", re.IGNORECASE)
CASE_RE = re.compile(r"\bcase\b")
DB_LONG_RE = re.compile(r"\b(d[bef][bms]?|db|defb)\b\s+(.+)", re.IGNORECASE)


def source_roots(root: Path) -> list[Path]:
    roots = [root / name for name in PREFERRED_DIRS if (root / name).exists()]
    return roots or [root]


def iter_text_files(root: Path):
    for base in source_roots(root):
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_EXTS:
                yield path


def strip_comment(line: str) -> str:
    out = line.split(";", 1)[0]
    out = out.split("//", 1)[0]
    return out.rstrip()


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def add_hit(
    hits: dict[str, list[Hit]], key: str, path: Path, line_no: int, text: str, note: str
) -> None:
    hits[key].append(Hit(path, line_no, text.strip(), note))


def normalise_asm(line: str) -> str | None:
    stripped = " ".join(line.lower().replace("\t", " ").split())
    if not stripped:
        return None
    if LABEL_RE.match(stripped) or DIRECTIVE_RE.match(stripped):
        return None
    return re.sub(r"\b[0-9a-f]+h\b|\$[0-9a-f]+|0x[0-9a-f]+|\b\d+\b", "N", stripped)


def scan_repeated_sequences(
    root: Path,
    path: Path,
    lines: list[str],
    clean: list[str],
    repeated_sequences: dict[tuple[str, ...], list[tuple[Path, int]]],
    repeated_tails: dict[tuple[str, ...], list[tuple[Path, int, str]]],
) -> None:
    insns: list[tuple[int, str]] = []
    current_label = "(file-scope)"
    current_block: list[tuple[int, str]] = []

    def flush_block() -> None:
        if len(current_block) < 3:
            return
        tail = tuple(item[1] for item in current_block[-3:])
        repeated_tails[tail].append((path, current_block[-3][0], current_label))

    for idx, code in enumerate(clean):
        stripped = code.strip()
        label = LABEL_RE.match(stripped)
        if label:
            flush_block()
            current_label = label.group(1)
            current_block = []
            continue
        norm = normalise_asm(code)
        if norm is None:
            continue
        insns.append((idx + 1, norm))
        current_block.append((idx + 1, norm))
        if EXIT_RE.search(stripped):
            flush_block()
            current_block = []

    flush_block()

    for width in (3, 4, 5):
        for idx in range(0, max(0, len(insns) - width + 1)):
            seq = tuple(item[1] for item in insns[idx : idx + width])
            if any(EXIT_RE.search(item) for item in seq[:-1]):
                continue
            repeated_sequences[seq].append((path, insns[idx][0]))


def scan_c_structure(
    path: Path, lines: list[str], clean: list[str], hits: dict[str, list[Hit]]
) -> None:
    for idx, line in enumerate(clean):
        if LOOP_RE.search(line):
            window = "\n".join(clean[idx : min(len(clean), idx + 24)])
            if STRLEN_RE.search(window):
                add_hit(
                    hits,
                    "libcall-in-loop",
                    path,
                    idx + 1,
                    lines[idx],
                    "loop appears to call strlen/strcmp/memcpy/memset; hoist, inline, or specialize if map proves drag",
                )
        if SWITCH_RE.search(line):
            window = "\n".join(clean[idx : min(len(clean), idx + 80)])
            cases = len(CASE_RE.findall(window))
            if cases >= 5:
                add_hit(
                    hits,
                    "large-switch-dispatch",
                    path,
                    idx + 1,
                    lines[idx],
                    f"switch has about {cases} nearby cases; compare cascade, jump table, token table, or computed dispatch",
                )
        if "static const char *" in line and "{" in line:
            add_hit(
                hits,
                "pointer-table-overhead",
                path,
                idx + 1,
                lines[idx],
                "pointer table costs 2 bytes per entry; check packed offsets, token streams, or shared prefix tables",
            )
        if re.search(r"\b(uint8_t|unsigned\s+char|char)\s+\w+\s*:\s*\d+", line):
            add_hit(
                hits,
                "c-bitfield-under-sdcc",
                path,
                idx + 1,
                lines[idx],
                "C bitfields are often larger/slower than manual masks under SDCC; verify generated ASM",
            )


def scan_asm_data(
    path: Path, lines: list[str], clean: list[str], hits: dict[str, list[Hit]]
) -> None:
    for idx, line in enumerate(clean):
        match = DB_LONG_RE.search(line)
        if not match:
            continue
        payload = match.group(2)
        if payload.count(",") >= 15:
            add_hit(
                hits,
                "large-byte-table",
                path,
                idx + 1,
                lines[idx],
                "large byte table: check packing, delta coding, RLE/ZX0, generated table, or screen-layout synthesis",
            )
        if payload.count('"') >= 4:
            add_hit(
                hits,
                "string-fragment-table",
                path,
                idx + 1,
                lines[idx],
                "many string fragments in one db; check token dictionary or shared suffix/prefix table",
            )


def scan_file(
    root: Path,
    path: Path,
    hits: dict[str, list[Hit]],
    calls: Counter[str],
    repeated_sequences: dict[tuple[str, ...], list[tuple[Path, int]]],
    repeated_tails: dict[tuple[str, ...], list[tuple[Path, int, str]]],
) -> None:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return

    compiled = [
        (name, re.compile(pattern, re.IGNORECASE), note)
        for name, (pattern, note) in PATTERNS.items()
    ]
    clean = [strip_comment(line) for line in lines]
    suffix = path.suffix.lower()
    is_asm = suffix in ASM_EXTS
    is_c = suffix in C_EXTS

    for idx, line in enumerate(clean):
        for name, regex, note in compiled:
            if regex.search(line):
                add_hit(hits, name, path, idx + 1, lines[idx], note)
        match = CALL_RE.search(line) if is_asm else None
        if match is not None:
            calls[match.group(1)] += 1
            nxt = idx + 1
            while nxt < len(clean) and not clean[nxt].strip():
                nxt += 1
            if nxt < len(clean) and RET_RE.search(clean[nxt]):
                add_hit(
                    hits,
                    "tail-call-wrapper",
                    path,
                    idx + 1,
                    lines[idx],
                    "`call target; ret` can become `jp target` if ABI permits",
                )

    if is_asm:
        scan_repeated_sequences(
            root, path, lines, clean, repeated_sequences, repeated_tails
        )
        scan_asm_data(path, lines, clean, hits)
    if is_c:
        scan_c_structure(path, lines, clean, hits)


def print_hits(root: Path, hits: dict[str, list[Hit]]) -> None:
    for key in sorted(hits):
        items = hits[key]
        print(f"\n[{key}] count={len(items)}")
        for hit in items[:24]:
            print(f"  {rel(hit.path, root)}:{hit.line_no}: {hit.text}")
        print(f"  note: {items[0].note}")
        if len(items) > 24:
            print(f"  ... {len(items) - 24} more")


def print_repeated_sequences(
    root: Path, repeated_sequences: dict[tuple[str, ...], list[tuple[Path, int]]]
) -> None:
    ranked = sorted(
        (
            (seq, places)
            for seq, places in repeated_sequences.items()
            if len(places) >= 3
        ),
        key=lambda item: (-len(item[0]) * (len(item[1]) - 1), -len(item[1]), item[0]),
    )
    print("\n[repeated-asm-sequences] count=" + str(len(ranked)))
    if not ranked:
        print("  none")
        return
    for seq, places in ranked[:16]:
        gross = len(seq) * (len(places) - 1)
        print(
            f"  approx_gross={gross} insns | repeats={len(places)} | {' / '.join(seq)}"
        )
        for path, line_no in places[:5]:
            print(f"    {rel(path, root)}:{line_no}")
        if len(places) > 5:
            print(f"    ... {len(places) - 5} more")
    print(
        "  note: candidate for factoring, table dispatch, macro split, or suffix merge; count real bytes before proposing"
    )


def print_repeated_tails(
    root: Path, repeated_tails: dict[tuple[str, ...], list[tuple[Path, int, str]]]
) -> None:
    ranked = sorted(
        ((tail, places) for tail, places in repeated_tails.items() if len(places) >= 2),
        key=lambda item: (-(len(item[0]) * (len(item[1]) - 1)), -len(item[1]), item[0]),
    )
    print("\n[repeated-asm-tails] count=" + str(len(ranked)))
    if not ranked:
        print("  none")
        return
    for tail, places in ranked[:16]:
        print(f"  repeats={len(places)} | {' / '.join(tail)}")
        for path, line_no, label in places[:6]:
            print(f"    {rel(path, root)}:{line_no} ({label})")
        if len(places) > 6:
            print(f"    ... {len(places) - 6} more")
    print(
        "  note: suffix merging often beats one-off JP/JR swaps when epilogues repeat"
    )


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    hits: dict[str, list[Hit]] = defaultdict(list)
    calls: Counter[str] = Counter()
    repeated_sequences: dict[tuple[str, ...], list[tuple[Path, int]]] = defaultdict(
        list
    )
    repeated_tails: dict[tuple[str, ...], list[tuple[Path, int, str]]] = defaultdict(
        list
    )
    files = list(iter_text_files(root))
    for path in files:
        scan_file(root, path, hits, calls, repeated_sequences, repeated_tails)

    print(f"root: {root}")
    print(f"files_scanned: {len(files)}")
    print("purpose: shrink candidates only; count bytes and remeasure before accepting")
    print_hits(root, hits)
    print_repeated_sequences(root, repeated_sequences)
    print_repeated_tails(root, repeated_tails)

    repeated = [
        (target, count) for target, count in calls.most_common(40) if count >= 3
    ]
    print("\n[repeated-call-targets] count=" + str(len(repeated)))
    if not repeated:
        print("  none")
    else:
        for target, count in repeated:
            rst_hint = " RST-candidate" if count >= 6 else ""
            print(f"  {target}: {count} calls{rst_hint}")
        print(
            "  note: inspect helper factoring, RST vectors, wrapper collapse, and libpull roots"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
