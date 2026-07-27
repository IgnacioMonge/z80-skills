#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

TEXT_EXTS = {".asm", ".s", ".inc", ".c", ".h", ".i", ".map", ".opt", ".lst", ".rul", ".sym"}
TOP_LEVEL_FILES = {"Makefile", "makefile"}
SKIP_DIRS = {".git", ".svn", ".hg", ".venv", "venv", "node_modules", "__pycache__", "third_party", "vendor"}
MAX_BYTES = 2_000_000
SKIPPED_TOO_LARGE: list[Path] = []
CONDITIONS = {"z", "nz", "c", "nc", "m", "p", "pe", "po"}
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
        r"\b(ld\s+sp\s*,|ex\s+\(sp\)\s*,|add\s+hl\s*,\s*sp)",
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
        r"\b(inc\s+l|dec\s+l|align\s+256|defs\s+256)\b|/\s*256|>>\s*8",
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
    "rst8-or-esxdos": (
        r"\brst\s+(?:8|\$08|0x08|08h)\b|\besxdos\b|\bdivmmc\b|\b(f_open|f_read|f_write|f_close|m_getsetdrv)\b",
        "firmware/divMMC boundary; verify RST8 ABI, paged ROM state, scratch RAM, IY/AF/BC/DE/HL clobbers, and error exits",
    ),
    "screen-or-rom-anchor": (
        r"(?:\$|#)(?:4[0-9A-Fa-f]{3}|5[0-9A-Fa-f]{3}|ff58|ffff)\b|0x(?:4[0-9A-Fa-f]{3}|5[0-9A-Fa-f]{3}|ff58|ffff)\b|\b(?:16384|22528|23296|23552|23610|23672|65368|65535)\b",
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
    "inline-asm-marker": (
        r"\b__asm\b|\b__endasm\b|#asm\b|#endasm\b",
        "inline ASM inside C makes register/flag/stack effects invisible to the optimizer; inspect generated ASM and manual preserves",
    ),
}

CALL_RE = re.compile(r"\bcall\s+((?:z|nz|c|nc|m|p|pe|po)\s*,\s*)?([A-Za-z_.$?@][\w.$?@]*)", re.IGNORECASE)
RET_UNCOND_RE = re.compile(r"^\s*ret[imn]?\s*$", re.IGNORECASE)
JUMP_RE = re.compile(r"^\s*(jp|jr)\s+(.+)$", re.IGNORECASE)
DI_RE = re.compile(r"\bdi\b", re.IGNORECASE)
EI_RE = re.compile(r"\bei\b", re.IGNORECASE)
HALT_RE = re.compile(r"\bhalt\b", re.IGNORECASE)
DJNZ_RE = re.compile(r"^\s*djnz\b", re.IGNORECASE)
EI_ONLY_RE = re.compile(r"^\s*ei\b", re.IGNORECASE)
EI_BOUNDARY_RE = re.compile(r"^\s*(?:ret[imn]?|jp\s+[^,;]+|jr\s+[^,;]+|halt)\b", re.IGNORECASE)
EXX_RE = re.compile(r"\bexx\b", re.IGNORECASE)
EX_AF_RE = re.compile(r"\bex\s+af\s*,\s*af'\b", re.IGNORECASE)
PUSH_RE = re.compile(r"^\s*push\s+(af|bc|de|hl|ix|iy)\b", re.IGNORECASE)
POP_RE = re.compile(r"^\s*pop\s+(af|bc|de|hl|ix|iy)\b", re.IGNORECASE)
POP_HL_RE = re.compile(r"^\s*pop\s+hl\b", re.IGNORECASE)
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
LABEL_RE = re.compile(r"^([A-Za-z_.$?@][\w.$?@]*):(?:\s*(.*))?$")
LOOP_RE = re.compile(r"\b(for|while)\s*\(", re.IGNORECASE)
STRLEN_RE = re.compile(r"\bstrlen\s*\(", re.IGNORECASE)
INLINE_ASM_START_RE = re.compile(r"\b__asm\b|#asm\b", re.IGNORECASE)
INLINE_ASM_END_RE = re.compile(r"\b__endasm\b|#endasm\b", re.IGNORECASE)
INLINE_ASM_TOUCH_RE = re.compile(
    r"\b(?:ld|pop|push|exx|ex|add|adc|sbc|sub|xor|or|and|cp|inc|dec|call|rst|jp\s*\(|out|in|di|ei)\b",
    re.IGNORECASE,
)
EXPORT_RE = re.compile(r"^\s*(?:PUBLIC|GLOBAL|XDEF|EXPORT|\.globl)\s+(.+)", re.IGNORECASE)
SYMBOL_RE = re.compile(r"[A-Za-z_.$][\w.$?@]*")
ARRAY_DECL_RE = re.compile(r"\b(?:uint8_t|char|unsigned\s+char)\s+(\w+)\s*\[(\d+)\]")
ARRAY_WRITE_RE = re.compile(r"\b(\w+)\s*\[[^]]+\]\s*=")

HIGH_KEYS = {
    "block-op-bc-zero", "halt-while-di-active", "exit-with-interrupts-disabled",
    "sp-hijack-at-exit", "odd-exx-at-exit", "odd-ex-af-at-exit",
    "inline-asm-register-clobber",
}
MEDIUM_KEYS = HIGH_KEYS | {
    "long-di-span", "stack-delta-at-exit", "pop-hl-nonlocal-exit",
    "djnz-loop-with-call", "stale-flag-branch", "carry-after-inc-dec",
    "ei-delayed-boundary", "block-repeat-op", "shadow-register-use",
    "stack-pointer-trick", "page-local-indexing", "dynamic-vector-dispatch",
    "rst8-or-esxdos", "screen-or-rom-anchor", "port-io", "i-or-r-register",
    "next-only-or-undocumented", "call-followed-by-ret",
}
LEVEL_KEYS = {"high": HIGH_KEYS, "medium": MEDIUM_KEYS, "broad": None}



def parse_args(argv: list[str]) -> tuple[str, Path]:
    level = "broad"
    args = list(argv)
    if args and args[0] == "--level":
        if len(args) < 2 or args[1] not in LEVEL_KEYS:
            raise SystemExit("usage: z80_pattern_scan.py [--level high|medium|broad] <root>")
        level = args[1]
        args = args[2:]
    elif args and args[0].startswith("--level="):
        level = args[0].split("=", 1)[1]
        if level not in LEVEL_KEYS:
            raise SystemExit("usage: z80_pattern_scan.py [--level high|medium|broad] <root>")
        args = args[1:]
    return level, Path(args[0] if args else ".").resolve()


def apply_level(hits: dict[str, list[Hit]], level: str) -> dict[str, list[Hit]]:
    keep = LEVEL_KEYS[level]
    if keep is None:
        return hits
    return defaultdict(list, {key: value for key, value in hits.items() if key in keep})


def skip_path(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        parts = path.parts
    return any(part in SKIP_DIRS for part in parts)


def iter_text_files(root: Path):
    if root.is_file():
        if root.suffix.lower() in TEXT_EXTS and root.stat().st_size <= MAX_BYTES:
            yield root
        return
    for path in root.rglob("*"):
        if skip_path(path, root) or not path.is_file():
            continue
        if path.name not in TOP_LEVEL_FILES and path.suffix.lower() not in TEXT_EXTS:
            continue
        if path.stat().st_size > MAX_BYTES:
            SKIPPED_TOO_LARGE.append(path)
            continue
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


def split_label(line: str) -> tuple[str, str] | None:
    match = LABEL_RE.match(line.strip())
    return (match.group(1), match.group(2) or "") if match else None


def directive_symbols(line: str, regex: re.Pattern[str]) -> list[str]:
    match = regex.search(line)
    if not match:
        return []
    body = re.split(r";|//", match.group(1), 1)[0]
    return [token for token in re.split(r"[\s,]+", body.strip()) if SYMBOL_RE.fullmatch(token)]


def exported_labels(clean: list[str]) -> set[str]:
    labels = set()
    for line in clean:
        labels.update(directive_symbols(line, EXPORT_RE))
    return labels


def parse_call(line: str) -> tuple[str, bool] | None:
    match = CALL_RE.search(line)
    if not match:
        return None
    return match.group(2), bool(match.group(1))


def is_uncond_jump(line: str) -> bool:
    match = JUMP_RE.match(line)
    if not match:
        return False
    args = match.group(2).strip()
    if "," in args:
        return args.split(",", 1)[0].strip().lower() not in CONDITIONS
    return args.split()[0].lower() not in CONDITIONS


def is_uncond_exit(line: str) -> bool:
    return bool(RET_UNCOND_RE.match(line))


def is_boundary_transfer(line: str) -> bool:
    return is_uncond_exit(line) or is_uncond_jump(line)


def starts_new_label(line: str, label: str) -> bool:
    if is_uncond_exit(line):
        return True
    match = JUMP_RE.match(line)
    if not match or not is_uncond_jump(line):
        return False
    target = match.group(2).strip().split()[0]
    return target.lower() != label.lower()


def is_nonlocal_exit_after_pop(line: str) -> bool:
    call = parse_call(line)
    return is_boundary_transfer(line) or (call is not None and not call[1])


def scan_asm_structure(
    root: Path,
    path: Path,
    lines: list[str],
    clean: list[str],
    hits: dict[str, list[Hit]],
) -> None:
    exports = exported_labels(clean)
    current_label = "(file-scope)"
    label_line = 1
    stack_delta = 0
    di_line: int | None = None
    long_di_reported = False
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
            long_di_reported, \
            exx_parity, \
            exaf_parity, \
            sp_hijack_line, \
            previous_code
        current_label = name
        label_line = lineno
        stack_delta = 0
        di_line = None
        long_di_reported = False
        exx_parity = 0
        exaf_parity = 0
        sp_hijack_line = None
        previous_code = None

    for idx, code in enumerate(clean):
        lineno = idx + 1
        stripped = code.strip()
        if not stripped:
            continue

        label = split_label(stripped)
        if label is not None:
            if label[0] in exports or current_label == "(file-scope)" or (
                previous_code is not None
                and starts_new_label(previous_code[1], label[0])
            ):
                reset_state(label[0], lineno)
            stripped = label[1].strip()
            if not stripped:
                continue

        if DI_RE.search(stripped):
            di_line = lineno
            long_di_reported = False
        if EI_RE.search(stripped):
            di_line = None
            long_di_reported = False
        if di_line is not None and HALT_RE.search(stripped):
            add_hit(
                hits,
                "halt-while-di-active",
                path,
                lineno,
                lines[idx],
                f"HALT appears after DI in {current_label}; prove an EI or interrupt source can wake it",
            )
        if di_line is not None and not long_di_reported and lineno - di_line > 64:
            add_hit(
                hits,
                "long-di-span",
                path,
                di_line,
                lines[di_line - 1],
                f"DI span in {current_label} exceeds 64 scanned code lines before EI",
            )
            long_di_reported = True

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
            if EI_ONLY_RE.search(prev) and EI_BOUNDARY_RE.search(stripped):
                add_hit(
                    hits,
                    "ei-delayed-boundary",
                    path,
                    lineno,
                    lines[idx],
                    f"EI at line {prev_lineno} only takes effect after this instruction; prove this boundary is intentional",
                )
            if POP_HL_RE.search(prev) and is_nonlocal_exit_after_pop(stripped):
                add_hit(
                    hits,
                    "pop-hl-nonlocal-exit",
                    path,
                    lineno,
                    lines[idx],
                    f"POP HL at line {prev_lineno} edits caller stack/control flow; prove every caller has identical stack depth",
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

        if DJNZ_RE.search(stripped):
            window_start = max(label_line - 1, idx - 24)
            window = "\n".join(clean[window_start:idx])
            if CALL_RE.search(window):
                add_hit(
                    hits,
                    "djnz-loop-with-call",
                    path,
                    lineno,
                    lines[idx],
                    f"DJNZ loop in {current_label} contains a CALL in the scanned loop window; prove callee preserves B/BC",
                )

        if is_uncond_exit(stripped):
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

    in_inline_asm = False
    asm_start = 0
    touched_regs = False
    for idx, line in enumerate(clean):
        if INLINE_ASM_START_RE.search(line):
            in_inline_asm = True
            asm_start = idx + 1
            touched_regs = bool(INLINE_ASM_TOUCH_RE.search(line))
        elif in_inline_asm and INLINE_ASM_TOUCH_RE.search(line):
            touched_regs = True

        if in_inline_asm and INLINE_ASM_END_RE.search(line):
            if touched_regs:
                add_hit(
                    hits,
                    "inline-asm-register-clobber",
                    path,
                    asm_start,
                    lines[asm_start - 1],
                    "inline ASM block appears to touch registers or call helpers; verify manual preserves and generated C temporaries",
                )
            in_inline_asm = False
            touched_regs = False

        if "__asm" in line and "__endasm" not in line and INLINE_ASM_TOUCH_RE.search(line):
            add_hit(
                hits,
                "inline-asm-register-clobber",
                path,
                idx + 1,
                lines[idx],
                "one-line inline ASM appears to touch registers; verify optimizer assumptions and generated ASM",
            )

    if in_inline_asm and touched_regs:
        add_hit(
            hits,
            "inline-asm-register-clobber",
            path,
            asm_start,
            lines[asm_start - 1],
            "inline ASM block appears unterminated in this file scan and touches registers; inspect generated output",
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
        call = parse_call(line) if is_asm else None
        if call is not None:
            target, conditional = call
            calls[target] += 1
            nxt = idx + 1
            while nxt < len(clean) and not clean[nxt].strip():
                nxt += 1
            if not conditional and nxt < len(clean) and RET_UNCOND_RE.search(clean[nxt]):
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
    level, root = parse_args(sys.argv[1:])
    hits: dict[str, list[Hit]] = defaultdict(list)
    calls: Counter[str] = Counter()
    files = list(iter_text_files(root))
    for path in files:
        scan_file(root, path, hits, calls)

    hits = apply_level(hits, level)
    print(f"root: {root}")
    print(f"level: {level}")
    print(f"files_scanned: {len(files)}")
    print("dirs_scanned: .")
    print("dirs_skipped: " + ", ".join(sorted(SKIP_DIRS)))
    print("files_skipped_too_large: " + (str(len(SKIPPED_TOO_LARGE)) if SKIPPED_TOO_LARGE else "0"))
    for path in SKIPPED_TOO_LARGE[:20]:
        print(f"  {rel(path, root)} {path.stat().st_size} bytes")
    print("purpose: adversarial hints only; every item needs local proof before reporting")
    print_hits(root, hits)

    repeated = [] if level == "high" else [
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
