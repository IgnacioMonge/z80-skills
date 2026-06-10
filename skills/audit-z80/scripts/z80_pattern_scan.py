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
        "prove BC=0 behavior, overlap direction, post-state, flags, and interrupt assumptions",
    ),
    "shadow-register-use": (
        r"\b(exx|ex\s+af\s*,\s*af')\b",
        "prove alternate-register convention across ISR, ROM, and every C/ASM boundary",
    ),
    "stack-pointer-trick": (
        r"\b(ld\s+sp\s*,|ex\s+\(sp\)\s*,|push\s+(af|bc|de|hl|ix|iy))",
        "check stack restoration, DI span, interrupt model, and caller stack assumptions",
    ),
    "self-modifying-or-layout": (
        r"\b(ld\s+\([^)]*[+][^)]*\)\s*,|incbin|org\s+|phase\s+|dephase\s+|defs\s+|defc\s+)",
        "possible layout, overlay, or self-modifying dependency; verify RAM/code placement and relocation",
    ),
    "indexed-hot-path": (
        r"\b(i[xy][hl]|[,(]\s*i[xy]\s*[+-]|ld\s+i[xy]\s*,|push\s+i[xy]|pop\s+i[xy])",
        "IX/IY indexed code is prefix-heavy and ABI-sensitive; verify frame-pointer/reserved-register contract",
    ),
    "page-local-indexing": (
        r"\b(inc\s+l|dec\s+l|ld\s+h\s*,|ld\s+l\s*,|add\s+a\s*,\s*l)\b",
        "page-local table/screen indexing; prove 256-byte alignment and no row/table page crossing",
    ),
    "timing-pad-or-cycle-equalizer": (
        r"\b(nop|djnz\s+\$|jr\s+\$|defs\s+\d+)\b",
        "possible cycle padding for audio, raster, loader, VDP/ULA wait, or benchmark timing; identify timing contract before changing",
    ),
    "dynamic-vector-dispatch": (
        r"\b(jp|call)\s+\((hl|ix|iy)\)",
        "dynamic dispatch or generated-code jump; prove target table, bank lifetime, and ABI/register contract",
    ),
    "smc-opcode-patch": (
        r"\bld\s+\([^)]*(?:line|skip|patch|opcode|jump|call|jp|jr)[^)]*\)\s*,",
        "looks like opcode/table patching; prove RAM residency, relocation, interrupts, and restore path",
    ),
    "interrupt-control": (
        r"\b(di|ei|im\s+[012]|halt|reti|retn)\b",
        "check DI/EI balance, IM setup, HALT wakeup, ISR return type, and shared-state protection",
    ),
    "port-io": (
        r"\b(in|out)\s*(?:a\s*,)?\(",
        "verify port decode, timing, border/AY/UART/esxDOS side effects, and register preservation",
    ),
    "screen-or-rom-anchor": (
        r"(\$|#|0x)(4000|5800|5b00|5c00|5c3a|5c78|ff58|ffff)\b|\b(16384|22528|23296|23552|23610|23672|65368|65535)\b",
        "fixed Spectrum address; prove model, aliasing, firmware/esxDOS interaction, and 48K/128K/Next contract",
    ),
    "i-or-r-register": (
        r"\bld\s+a\s*,\s*[ir]\b|\bld\s+[ir]\s*,\s*a\b",
        "I/R register behavior can expose interrupt flip-flop, refresh-register, or entropy assumptions",
    ),
    "next-only-or-undocumented": (
        r"\b(nextreg|mul\s+de|swapnib|mirror|pixeldn|pixeldm|setae|ldix|lddx|ldirx|lddrx|sll)\b|\b(ixh|ixl|iyh|iyl)\b",
        "target-specific or undocumented opcode; reject for plain 48K unless preflight proves support",
    ),
    "expensive-c-runtime-trigger": (
        r"\b(printf|sprintf|snprintf|scanf|malloc|free|memcpy|memset|strcmp|strlen|strcpy|strcat)\s*\(",
        "library call may be valid but audit clobbers, stack, latency, and linked footprint",
    ),
    "mutable-string-literal": (
        r"\bchar\s*\*\s+\w+\s*=\s*\"|=\s*\(char\s*\*\)\s*\"",
        "string literal passed through mutable char pointer; verify no write-through corrupts code/data",
    ),
}

CALL_RE = re.compile(r"\bcall\s+([A-Za-z_.$?@][\w.$?@]*)", re.IGNORECASE)
RET_RE = re.compile(r"^\s*ret[imn]?\b", re.IGNORECASE)
UNCOND_EXIT_RE = re.compile(
    r"^\s*(?:ret[imn]?|jp\s+[^,;]+|jr\s+[^,;]+)\b", re.IGNORECASE
)
DI_RE = re.compile(r"\bdi\b", re.IGNORECASE)
EI_RE = re.compile(r"\bei\b", re.IGNORECASE)
HALT_RE = re.compile(r"\bhalt\b", re.IGNORECASE)
EXX_RE = re.compile(r"\bexx\b", re.IGNORECASE)
EX_AF_RE = re.compile(r"\bex\s+af\s*,\s*af'\b", re.IGNORECASE)
PUSH_RE = re.compile(r"^\s*push\s+(af|bc|de|hl|ix|iy)\b", re.IGNORECASE)
POP_RE = re.compile(r"^\s*pop\s+(af|bc|de|hl|ix|iy)\b", re.IGNORECASE)
LD_SP_RE = re.compile(r"^\s*ld\s+sp\s*,", re.IGNORECASE)
RESTORE_SP_RE = re.compile(
    r"^\s*(?:ld\s+sp\s*,\s*\([^)]*\)|ld\s+sp\s*,\s*(?:hl|ix|iy)|pop\s+sp)\b",
    re.IGNORECASE,
)
COND_BRANCH_RE = re.compile(
    r"^\s*(?:jr|jp|call|ret)\s+(z|nz|c|nc|m|p|pe|po)\b", re.IGNORECASE
)
CARRY_BRANCH_RE = re.compile(r"^\s*(?:jr|jp|call|ret)\s+(c|nc)\b", re.IGNORECASE)
FLAG_NEUTRAL_RE = re.compile(
    r"^\s*(?:ld|ex|exx|push|pop|di|ei|im|nop)\b", re.IGNORECASE
)
INC_DEC_RE = re.compile(r"^\s*(?:inc|dec)\s+", re.IGNORECASE)
BLOCK_RE = re.compile(r"\b(ldir|lddr|cpir|cpdr|inir|indr|otir|otdr)\b", re.IGNORECASE)
LD_BC_ZERO_RE = re.compile(r"\bld\s+bc\s*,\s*(?:0|\$0|#0|0x0)\b", re.IGNORECASE)
LABEL_RE = re.compile(r"^([A-Za-z_.$?@][\w.$?@]*):\s*$")
LOOP_RE = re.compile(r"\b(for|while)\s*\(", re.IGNORECASE)
STRLEN_RE = re.compile(r"\bstrlen\s*\(", re.IGNORECASE)
ARRAY_DECL_RE = re.compile(r"\b(?:uint8_t|char|unsigned\s+char)\s+(\w+)\s*\[(\d+)\]")
ARRAY_WRITE_RE = re.compile(r"\b(\w+)\s*\[[^]]+\]\s*=")


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


def label_name(line: str) -> str | None:
    match = LABEL_RE.match(line.strip())
    return match.group(1) if match else None


def scan_asm_structure(
    root: Path,
    path: Path,
    lines: list[str],
    clean: list[str],
    hits: dict[str, list[Hit]],
) -> None:
    current_label = "(file-scope)"
    label_line = 1
    stack_delta = 0
    di_line: int | None = None
    exx_parity = 0
    exaf_parity = 0
    sp_hijack_line: int | None = None
    previous_code: tuple[int, str] | None = None

    def reset_state(name: str, lineno: int) -> None:
        nonlocal \
            current_label, \
            label_line, \
            stack_delta, \
            di_line, \
            exx_parity, \
            exaf_parity, \
            sp_hijack_line, \
            previous_code
        current_label = name
        label_line = lineno
        stack_delta = 0
        di_line = None
        exx_parity = 0
        exaf_parity = 0
        sp_hijack_line = None
        previous_code = None

    for idx, code in enumerate(clean):
        lineno = idx + 1
        stripped = code.strip()
        if not stripped:
            continue

        label = label_name(stripped)
        if label is not None:
            reset_state(label, lineno)
            continue

        if DI_RE.search(stripped):
            di_line = lineno
        if EI_RE.search(stripped):
            di_line = None
        if di_line is not None and HALT_RE.search(stripped):
            add_hit(
                hits,
                "halt-while-di-active",
                path,
                lineno,
                lines[idx],
                f"HALT appears after DI in {current_label}; prove an EI or interrupt source can wake it",
            )
        if di_line is not None and lineno - di_line > 64:
            add_hit(
                hits,
                "long-di-span",
                path,
                di_line,
                lines[di_line - 1],
                f"DI span in {current_label} exceeds 64 scanned code lines before EI",
            )
            di_line = None

        if PUSH_RE.search(stripped):
            stack_delta += 2
        if POP_RE.search(stripped):
            stack_delta -= 2
        if EXX_RE.search(stripped):
            exx_parity ^= 1
        if EX_AF_RE.search(stripped):
            exaf_parity ^= 1
        if LD_SP_RE.search(stripped):
            sp_hijack_line = lineno
        if RESTORE_SP_RE.search(stripped):
            sp_hijack_line = None

        if previous_code is not None:
            prev_lineno, prev = previous_code
            if COND_BRANCH_RE.search(stripped) and FLAG_NEUTRAL_RE.search(prev):
                add_hit(
                    hits,
                    "stale-flag-branch",
                    path,
                    lineno,
                    lines[idx],
                    f"conditional branch follows flag-neutral instruction at line {prev_lineno}; prove flags intentionally come from earlier code",
                )
            if CARRY_BRANCH_RE.search(stripped) and INC_DEC_RE.search(prev):
                add_hit(
                    hits,
                    "carry-after-inc-dec",
                    path,
                    lineno,
                    lines[idx],
                    f"carry branch follows INC/DEC at line {prev_lineno}; INC/DEC do not update carry",
                )

        if BLOCK_RE.search(stripped):
            window = "\n".join(clean[max(0, idx - 6) : idx])
            if LD_BC_ZERO_RE.search(window):
                add_hit(
                    hits,
                    "block-op-bc-zero",
                    path,
                    lineno,
                    lines[idx],
                    "block repeat follows an apparent BC=0 setup; on Z80 this means 65536 iterations",
                )

        if RET_RE.search(stripped) or UNCOND_EXIT_RE.search(stripped):
            if stack_delta != 0:
                add_hit(
                    hits,
                    "stack-delta-at-exit",
                    path,
                    lineno,
                    lines[idx],
                    f"{current_label} exits with approximate PUSH/POP delta {stack_delta:+d} bytes since line {label_line}",
                )
            if di_line is not None:
                add_hit(
                    hits,
                    "exit-with-interrupts-disabled",
                    path,
                    lineno,
                    lines[idx],
                    f"{current_label} exits after DI at line {di_line} without scanned EI",
                )
            if exx_parity:
                add_hit(
                    hits,
                    "odd-exx-at-exit",
                    path,
                    lineno,
                    lines[idx],
                    f"{current_label} exits with odd EXX parity; alternate registers may be swapped",
                )
            if exaf_parity:
                add_hit(
                    hits,
                    "odd-ex-af-at-exit",
                    path,
                    lineno,
                    lines[idx],
                    f"{current_label} exits with odd EX AF,AF' parity; alternate AF may be swapped",
                )
            if sp_hijack_line is not None:
                add_hit(
                    hits,
                    "sp-hijack-at-exit",
                    path,
                    lineno,
                    lines[idx],
                    f"{current_label} exits after LD SP at line {sp_hijack_line}; prove SP restored on every path",
                )

        previous_code = (lineno, stripped)


def scan_c_structure(
    root: Path,
    path: Path,
    lines: list[str],
    clean: list[str],
    hits: dict[str, list[Hit]],
) -> None:
    arrays: dict[str, tuple[int, int]] = {}
    for idx, line in enumerate(clean):
        for name, size_s in ARRAY_DECL_RE.findall(line):
            arrays[name] = (int(size_s), idx + 1)

    for idx, line in enumerate(clean):
        if LOOP_RE.search(line):
            window = "\n".join(clean[idx : min(len(clean), idx + 24)])
            if STRLEN_RE.search(window):
                add_hit(
                    hits,
                    "strlen-or-libcall-in-loop",
                    path,
                    idx + 1,
                    lines[idx],
                    "loop body appears to call strlen; audit latency, libpull, and invariant hoisting",
                )
        if "static const char *" in line and "{" in line and '"' in line:
            add_hit(
                hits,
                "mixed-pointer-literal-table",
                path,
                idx + 1,
                lines[idx],
                "static pointer table with literals; verify generated ASM/data relocation under this z88dk/SDCC version",
            )
        write = ARRAY_WRITE_RE.search(line)
        if write and write.group(1) in arrays:
            size, decl_line = arrays[write.group(1)]
            if size <= 8:
                add_hit(
                    hits,
                    "small-buffer-write",
                    path,
                    idx + 1,
                    lines[idx],
                    f"write to small buffer declared size {size} at line {decl_line}; prove index and terminator bounds",
                )


def scan_file(
    root: Path, path: Path, hits: dict[str, list[Hit]], calls: Counter[str]
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
                    "call-followed-by-ret",
                    path,
                    idx + 1,
                    lines[idx],
                    "tail-call candidate or wrapper; prove stack/calling convention before rewriting",
                )

    if is_asm:
        scan_asm_structure(root, path, lines, clean, hits)
    if is_c:
        scan_c_structure(root, path, lines, clean, hits)


def print_hits(root: Path, hits: dict[str, list[Hit]]) -> None:
    for key in sorted(hits):
        items = hits[key]
        print(f"\n[{key}] count={len(items)}")
        for hit in items[:24]:
            print(f"  {rel(hit.path, root)}:{hit.line_no}: {hit.text}")
        print(f"  note: {items[0].note}")
        if len(items) > 24:
            print(f"  ... {len(items) - 24} more")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    hits: dict[str, list[Hit]] = defaultdict(list)
    calls: Counter[str] = Counter()
    files = list(iter_text_files(root))
    for path in files:
        scan_file(root, path, hits, calls)

    print(f"root: {root}")
    print(f"files_scanned: {len(files)}")
    print(
        "purpose: adversarial hints only; every item needs local proof before reporting"
    )
    print_hits(root, hits)

    repeated = [
        (target, count) for target, count in calls.most_common(32) if count >= 3
    ]
    print("\n[repeated-call-targets] count=" + str(len(repeated)))
    if not repeated:
        print("  none")
    else:
        for target, count in repeated:
            print(f"  {target}: {count} calls")
        print(
            "  note: inspect hot wrappers, RST candidates, helper factoring, and libpull roots"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
