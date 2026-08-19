#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from scan_common import (
    ASM_EXTS, C_EXTS, Hit, LISTING_EXTS, TEXT_EXTS, add_hit, call_targets,
    is_unconditional_exit, parse_byte_payload, print_pattern_hits, print_scope,
    rel_path, resolve_target_scope, source_kind, split_label, strip_line_comment,
    unconditional_call_targets,
)

PATTERNS: dict[str, tuple[str, str]] = {
    "block-repeat-op": (
        r"\b(ldir|lddr|cpir|cpdr|inir|indr|otir|otdr)\b",
        "block ops may be compact already; count setup cost, BC=0 guard, direction, and helper reuse",
    ),
    "indexed-hot-path": (
        r"\b(i[xy][hl]|[,(]\s*i[xy]\s*[+-]|ld\s+i[xy]\s*,|push\s+i[xy]|pop\s+i[xy])",
        "IX/IY prefixes cost bytes; verify ABI, then look for base-register or layout alternatives",
    ),
    "timing-pad-or-cycle-equalizer": (
        r"\b(nop|djnz\s+\$|jr\s+\$|defs\s+\d+)\b",
        "possible timing pad; keep as rejected/unsafe unless audio, raster, loader, or I/O cadence is disproven",
    ),
    "dynamic-vector-dispatch": (
        r"\b(jp|call)\s+\((hl|ix|iy)\)",
        "pointer dispatch may indicate bytecode/token interpreter, vector table, or generated code opportunity",
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
    "sbc-a-mask-source": (
        r"\bsbc\s+a\s*,\s*a\b|\b(?:scf|ccf)\b",
        "carry-derived masks can replace branchy 0/255 materialization only when flags are already the right predicate",
    ),
    "wide-c-type": (
        r"\b(unsigned\s+int|int|uint16_t|size_t)\s+\w*(flag|state|mode|idx|index|count|len|x|y)\w*\b",
        "wide C scalar may force 16-bit code where byte range may be enough",
    ),
    "power-two-arithmetic": (
        r"([/%]\s*(2|4|8|16|32|64|128|256)\b|\*\s*(3|5|6|7|9|10|12|15|17)\b)",
        "constant arithmetic may become shifts/adds/masks; verify signedness and compiler output",
    ),
    "bank-page-io": (
        r"\b(out\s*\(\s*(?:0x)?(?:7ffd|1ffd|243b|253b)\s*\)|nextreg|BANKM|BANK678)\b|\$7ffd|\$1ffd",
        "banking/paging present; split resident vs banked size claims and cold-code move candidates",
    ),
    "z80n-op": (
        r"\b(mul\s+d?e|pixelad|pixeldn|setae|swapnib|mirror|ldirx|ldddx|nextreg)\b",
        "Z80N-only surface; size win only if Next is in target matrix and multi-target gate still holds",
    ),
    "crt-startup-hint": (
        r"\b(-startup=|CRT_ORG_|TAR__|register_sp|__Start|crt0)\b",
        "startup/CRT symbols often dominate map; measure CRT chunks before gameplay micro-edits",
    ),
    "skip-byte-else": (
        r"\.db\s+\$?(?:c2|c3|3e|21|cd)\b|db\s+(?:0x)?(?:c2|c3|3e|21)\b",
        "possible instruction-skip / better-else / overlapping-entry seed; verify flags and swallowed bytes",
    ),
    "conditional-rst-disp": (
        r"\bjr\s+(?:z|nz|c|nc)\s*,\s*\$\s*|\bjr\s+(?:z|nz|c|nc)\s*,\s*-1\b",
        "jr cc,$-1 style may encode conditional rst via $FF displacement; confirm vector ownership",
    ),
}

MULTILINE_PATTERNS: dict[str, tuple[str, str]] = {
    "fallthrough-call-chain": (
        r"call\s+\w+[\s\S]{0,80}?call\s+\w+",
        "adjacent calls may be fallthrough-unroll candidates; count vs counter loop",
    ),
}

# Presence-only seeds (NOT proof of ROM-hole / multi-decoder / ULA next-line).
PRESENCE_PATTERNS: dict[str, tuple[str, str]] = {
    "im2-present": (
        r"\bim\s+2\b|\bld\s+i\s*,",
        "IM2 or I-register load present — candidate only; ROM-hole requires vector page in ROM range + multi-target gate",
    ),
    "decoder-present": (
        r"\b(dzx0|dzx7|zx0|zx7|deexo|aplib|unpletter|megalz|dehrust|unpack|decompress)\w*",
        "decompressor name present — candidate only; multi-decoder needs >=2 families (H26)",
    ),
}

# ULA next-line: require screen anchor OR upde-like (and 7 + inc d/h) nearby.
ULA_SCREEN_ANCHOR_RE = re.compile(
    r"(\$|#|0x)(4000|5800|5b00)|\b(16384|22528|23296)\b|\bupde\b|\bnext_?line\b",
    re.IGNORECASE,
)
ULA_STEP_RE = re.compile(
    r"\b(inc\s+d|inc\s+h|add\s+hl\s*,\s*(?:de|bc)|and\s+7)\b",
    re.IGNORECASE,
)
UPDE_LIKE_RE = re.compile(
    r"inc\s+d[\s\S]{0,120}?and\s+7|and\s+7[\s\S]{0,80}?add\s+a\s*,\s*32",
    re.IGNORECASE,
)

DECODER_FAMILIES = {
    "zx0": re.compile(r"\bdzx0|\bzx0\b", re.I),
    "zx7": re.compile(r"\bdzx7|\bzx7\b", re.I),
    "exo": re.compile(r"\bdeexo\b|\bexomizer\b", re.I),
    "aplib": re.compile(r"\baplib\b", re.I),
    "pletter": re.compile(r"\bunpletter\b|\bpletter\b", re.I),
    "megalz": re.compile(r"\bmegalz\b|\bdec40\b", re.I),
    "hrust": re.compile(r"\bdehrust\b|\bhrust\b|\bunhrum\b", re.I),
}
DECODER_EVIDENCE_EXTS = ASM_EXTS | C_EXTS | LISTING_EXTS | {".map", ".sym"}

IM2_ROM_HOLE_HINT_RE = re.compile(
    r"\bld\s+(?:a|i)\s*,\s*(?:\$39|0x39|39h|57)\b|"
    r"\b(?:org|defw|dw)\s+(?:\$ffff|0xffff|0ffffh|65535)\b|"
    r"\brom[-_ ]?(?:hole|vector)\b|(?:vector.*rom|rom.*vector)",
    re.IGNORECASE,
)

LOW_SIGNAL_PATTERNS: dict[str, tuple[str, str, int]] = {
    "stack_blitter_terms": (
        r"\b(ld\s+sp\s*,|ex\s+\(sp\)\s*,|push\s+(af|bc|de|hl|ix|iy))",
        "stack-copy shape terms are low-signal alone; inspect only when clustered with copy/screen context",
        4,
    ),
    "page_local_terms": (
        r"\b(inc\s+l|dec\s+l|ld\s+h\s*,|ld\s+l\s*,|add\s+a\s*,\s*l)\b",
        "page-local indexing terms are low-signal alone; inspect only when dense in one file/block",
        6,
    ),
    "screen_writer_terms": (
        r"\b(ld\s+\(hl\)\s*,|add\s+hl\s*,\s*(?:de|bc|sp)|pop\s+(?:af|de))\b",
        "screen-writer terms are low-signal alone; combine with anchors/repetition before promoting",
        6,
    ),
}

CALL_RE = re.compile(r"\bcall\s+([A-Za-z_.$?@][\w.$?@]*)", re.IGNORECASE)
RET_RE = re.compile(r"^\s*ret\s*$", re.IGNORECASE)
STACK_TOUCH_RE = re.compile(
    r"^\s*(?:push|pop)\b|\b(?:inc|dec|ld|add)\s+sp\b|\bex\s+\(sp\)", re.IGNORECASE
)
COND_BRANCH_RE = re.compile(r"^\s*(?:jr|jp|call)\s+(z|nz|c|nc|m|p|pe|po)\b", re.IGNORECASE)
DJNZ_RE = re.compile(r"^\s*djnz\b", re.IGNORECASE)
LD_A_ZERO_RE = re.compile(r"^\s*ld\s+a\s*,\s*(?:0|\$00|0x00|00h)\b", re.IGNORECASE)
LD_A_MASK_RE = re.compile(r"^\s*ld\s+a\s*,\s*(?:1|\$01|0x01|01h|255|\$ff|0xff|0ffh)\b", re.IGNORECASE)
IXIY_RE = re.compile(r"\b(?:ix|iy|ixh|ixl|iyh|iyl)\b|[,(]\s*i[xy]\s*[+-]", re.IGNORECASE)
LDI_LIKE_RE = re.compile(r"^\s*(?:ldi|ld\s+a\s*,\s*\(hl\)|ld\s+\(de\)\s*,\s*a|inc\s+(?:hl|de))\b", re.IGNORECASE)
DIRECTIVE_RE = re.compile(
    r"^\s*(?:public|extern|global|section|module|org|phase|dephase|def[bswcm]|db|dw|ds|defs|equ|include|incbin)\b",
    re.IGNORECASE,
)
LOOP_RE = re.compile(r"\b(for|while)\s*\(", re.IGNORECASE)
STRLEN_RE = re.compile(r"\b(strlen|strcmp|memcpy|memset)\s*\(", re.IGNORECASE)
SWITCH_RE = re.compile(r"\bswitch\s*\(", re.IGNORECASE)
CASE_RE = re.compile(r"\bcase\b")
DB_LONG_RE = re.compile(r"\b(d[bef][bms]?|db|defb)\b\s+(.+)", re.IGNORECASE)


def rel(path: Path, root: Path) -> str:
    base = root.parent if root.is_file() else root
    return rel_path(path, base)

def normalise_asm(line: str) -> str | None:
    stripped = " ".join(line.lower().replace("\t", " ").split())
    if not stripped:
        return None
    label, rest = split_label(stripped)
    if label is not None:
        stripped = rest
        if not stripped:
            return None
    if DIRECTIVE_RE.match(stripped):
        return None
    return re.sub(r"\b[0-9a-f]+h\b|\$[0-9a-f]+|0x[0-9a-f]+|\b\d+\b", "N", stripped)


def longest_run(values: list[int]) -> int:
    best = 0
    idx = 0
    while idx < len(values):
        run = 1
        while idx + run < len(values) and values[idx + run] == values[idx]:
            run += 1
        best = max(best, run)
        idx += run
    return best


def scan_repeated_sequences(
    path: Path,
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
        label, rest = split_label(code)
        if label is not None:
            flush_block()
            current_label = label
            current_block = []
            code = rest
            stripped = rest.strip()
            if not stripped:
                continue
        norm = normalise_asm(code)
        if norm is None:
            continue
        insns.append((idx + 1, norm))
        current_block.append((idx + 1, norm))
        if is_unconditional_exit(stripped):
            flush_block()
            current_block = []

    flush_block()

    for width in (3, 4, 5):
        for idx in range(0, max(0, len(insns) - width + 1)):
            seq = tuple(item[1] for item in insns[idx : idx + width])
            if any(is_unconditional_exit(item) for item in seq[:-1]):
                continue
            repeated_sequences[seq].append((path, insns[idx][0]))


def scan_asm_local_shapes(
    path: Path, lines: list[str], clean: list[str], hits: dict[str, list[Hit]]
) -> None:
    current_label = "(file-scope)"
    label_line = 1
    current_block: list[tuple[int, str]] = []
    ldi_like_run: list[int] = []

    def flush_block() -> None:
        nonlocal current_block
        if current_block:
            ixiy_count = sum(1 for _, code in current_block if IXIY_RE.search(code))
            if ("loop" in current_label.lower() or ixiy_count >= 4) and ixiy_count >= 3:
                add_hit(
                    hits,
                    "ixiy-dense-loop",
                    path,
                    label_line,
                    lines[label_line - 1],
                    f"{current_label} has {ixiy_count} IX/IY uses in one block; count prefix bytes and consider HL/DE/base-offset layout",
                )
        current_block = []

    def flush_ldi_like() -> None:
        nonlocal ldi_like_run
        if len(ldi_like_run) >= 8:
            start = ldi_like_run[0]
            add_hit(
                hits,
                "sp-copy-opportunity",
                path,
                start,
                lines[start - 1],
                "long unrolled copy shape; EXPERIMENTAL candidate for SP-as-reader/writer only after DI/SP restore byte count",
            )
        ldi_like_run = []

    for idx, code in enumerate(clean):
        lineno = idx + 1
        stripped = code.strip()
        label, rest = split_label(code)
        if label is not None:
            flush_block()
            flush_ldi_like()
            current_label = label
            label_line = lineno
            stripped = rest.strip()
            if not stripped:
                continue
        if not stripped:
            flush_ldi_like()
            continue
        current_block.append((lineno, stripped))

        if LDI_LIKE_RE.search(stripped):
            ldi_like_run.append(lineno)
        else:
            flush_ldi_like()

        if DJNZ_RE.search(stripped):
            window = "\n".join(clean[max(label_line - 1, idx - 24) : idx])
            if CALL_RE.search(window):
                add_hit(
                    hits,
                    "djnz-loop-with-call-risk",
                    path,
                    lineno,
                    lines[idx],
                    "DJNZ loop window contains CALL; do not rewrite/shrink around B unless callee preserves B/BC",
                )

        if COND_BRANCH_RE.search(stripped):
            window = clean[idx + 1 : min(len(clean), idx + 8)]
            if any(LD_A_ZERO_RE.search(item.strip()) for item in window) and any(
                LD_A_MASK_RE.search(item.strip()) for item in window
            ):
                add_hit(
                    hits,
                    "branchy-boolean-mask",
                    path,
                    lineno,
                    lines[idx],
                    "branch appears to materialize A as 0/1/255; test carry-derived `sbc a,a` or `adc a,0` replacement with flag proof",
                )

    flush_block()
    flush_ldi_like()


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
            values = parse_byte_payload(payload)
            if values and longest_run(values) >= 8:
                add_hit(
                    hits,
                    "rle-run-byte-table",
                    path,
                    idx + 1,
                    lines[idx],
                    "byte table has repeated runs; compare RLE/raw/ZX0 net size including decoder or existing decompressor",
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
    path: Path,
    hits: dict[str, list[Hit]],
    calls: Counter[str],
    repeated_sequences: dict[tuple[str, ...], list[tuple[Path, int]]],
    repeated_tails: dict[tuple[str, ...], list[tuple[Path, int, str]]],
    low_signal: dict[Path, Counter[str]],
    decoder_families: set[str],
) -> None:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return

    compiled = [
        (name, re.compile(pattern, re.IGNORECASE), note)
        for name, (pattern, note) in PATTERNS.items()
    ]
    low_compiled = [
        (name, re.compile(pattern, re.IGNORECASE), threshold)
        for name, (pattern, _note, threshold) in LOW_SIGNAL_PATTERNS.items()
    ]
    clean = [strip_line_comment(line) for line in lines]
    joined = "\n".join(clean)
    suffix = path.suffix.lower()
    is_asm = suffix in ASM_EXTS
    is_c = suffix in C_EXTS

    if is_asm:
        for name, (pattern, note) in MULTILINE_PATTERNS.items():
            for match in re.finditer(pattern, joined, re.IGNORECASE):
                line_no = joined.count("\n", 0, match.start()) + 1
                add_hit(hits, name, path, line_no, lines[line_no - 1], note)

        # Presence seeds (honest names)
        for name, (pattern, note) in PRESENCE_PATTERNS.items():
            for match in re.finditer(pattern, joined, re.IGNORECASE):
                line_no = joined.count("\n", 0, match.start()) + 1
                add_hit(hits, name, path, line_no, lines[line_no - 1], note)

        # ULA next-line only when each step has local screen/upde context.
        for idx, code in enumerate(clean):
            if ULA_STEP_RE.search(code):
                window = "\n".join(clean[max(0, idx - 8) : min(len(clean), idx + 9)])
                if not (ULA_SCREEN_ANCHOR_RE.search(window) or UPDE_LIKE_RE.search(window)):
                    continue
                add_hit(
                    hits,
                    "next-line-ula",
                    path,
                    idx + 1,
                    lines[idx],
                    "ULA-context next-row step seed; compare to gasman upde (15 B) vs Y tables — not proof alone",
                )

        # Promote only when an IM2 instruction has a local explicit ROM-vector hint.
        for idx, code in enumerate(clean):
            if re.search(r"\bim\s+2\b|\bld\s+i\s*,", code, re.I):
                window = "\n".join(clean[max(0, idx - 12) : min(len(clean), idx + 13)])
                if not IM2_ROM_HOLE_HINT_RE.search(window):
                    continue
                add_hit(
                    hits,
                    "im2-rom-hole-candidate",
                    path,
                    idx + 1,
                    lines[idx],
                    "IM2 + ROM/vector-fill hint — still multi-target gated; 128K/Next often break ROM $FF hole",
                )

    # Aggregate only code/link artifacts; do not turn docs/config names into H26 evidence.
    if suffix in DECODER_EVIDENCE_EXTS:
        for fam, rx in DECODER_FAMILIES.items():
            if rx.search(joined):
                decoder_families.add(fam)

    for idx, line in enumerate(clean):
        for name, regex, note in compiled:
            if regex.search(line):
                add_hit(hits, name, path, idx + 1, lines[idx], note)
        if is_asm:
            for name, regex, _threshold in low_compiled:
                if regex.search(line):
                    low_signal[path][name] += 1
        targets = call_targets(line) if is_asm else []
        if targets:
            for target_name in targets:
                calls[target_name] += 1
            uncond_targets = unconditional_call_targets(line)
            nxt = idx + 1
            while nxt < len(clean) and not clean[nxt].strip():
                nxt += 1
            block_start = idx - 1
            while block_start >= 0:
                label, _rest = split_label(clean[block_start])
                if label is not None or is_unconditional_exit(clean[block_start]):
                    break
                block_start -= 1
            stack_touched = any(
                STACK_TOUCH_RE.search(clean[pos]) for pos in range(block_start + 1, idx)
            )
            if uncond_targets and not stack_touched and nxt < len(clean) and RET_RE.search(clean[nxt]):
                add_hit(
                    hits,
                    "tail-call-wrapper",
                    path,
                    idx + 1,
                    lines[idx],
                    "`call target; ret` can become `jp target` if ABI permits",
                )

    if is_asm:
        scan_repeated_sequences(path, clean, repeated_sequences, repeated_tails)
        scan_asm_local_shapes(path, lines, clean, hits)
        scan_asm_data(path, lines, clean, hits)
    if is_c:
        scan_c_structure(path, lines, clean, hits)


def print_low_signal_aggregate(root: Path, low_signal: dict[Path, Counter[str]]) -> None:
    thresholds = {name: cfg[2] for name, cfg in LOW_SIGNAL_PATTERNS.items()}
    notes = {name: cfg[1] for name, cfg in LOW_SIGNAL_PATTERNS.items()}
    rows: list[tuple[Path, dict[str, int]]] = []
    for path, counter in low_signal.items():
        shown = {name: count for name, count in counter.items() if count >= thresholds[name]}
        if shown:
            rows.append((path, shown))
    rows.sort(key=lambda item: (-sum(item[1].values()), rel(item[0], root)))
    print("\n[low-signal-aggregate] count=" + str(len(rows)))
    if not rows:
        print("  none")
        return
    base = root.parent if root.is_file() else root
    for path, counts in rows[:24]:
        joined = " ".join(f"{name}={counts[name]}" for name in sorted(counts))
        print(f"  [{source_kind(path, base)}] {rel(path, root)}: {joined}")
    print("  note: low-signal terms are not findings; promote only with local repetition, screen/copy context, and byte evidence")
    for name in sorted(notes):
        print(f"  {name}: {notes[name]}")


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
        "  note: approx_gross is instruction count, not bytes; candidate for factoring, table dispatch, macro split, or suffix merge; count real bytes before proposing"
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
    low_signal: dict[Path, Counter[str]] = defaultdict(Counter)
    decoder_families: set[str] = set()
    scope = resolve_target_scope(root, TEXT_EXTS)
    files = scope.files
    for path in files:
        scan_file(
            path,
            hits,
            calls,
            repeated_sequences,
            repeated_tails,
            low_signal,
            decoder_families,
        )

    asm_sources = sum(1 for path in files if path.suffix.lower() in ASM_EXTS)
    listings = sum(1 for path in files if path.suffix.lower() in LISTING_EXTS)
    print_scope(scope)
    print(f"files_scanned: {len(files)}")
    print(f"asm_sources_scanned: {asm_sources}")
    print(f"listings_candidates_only: {listings}")
    print("purpose: shrink candidates only; count bytes and remeasure before accepting")

    # H26: multi-decoder only when >=2 distinct families across scope
    if len(decoder_families) >= 2:
        add_hit(
            hits,
            "multi-decoder-smell",
            root if root.is_file() else root,
            1,
            f"families={sorted(decoder_families)}",
            ">=2 decompressor families in scope — delete-all-but-one candidate (H26); single family is decoder-present only",
        )

    print_pattern_hits(root, hits, include_source_kind=True)
    print_low_signal_aggregate(root, low_signal)
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
