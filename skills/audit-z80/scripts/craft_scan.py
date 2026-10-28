#!/usr/bin/env python3
"""Read-only lead queue for an expert craft review of Z80 C and ASM.

Every row is a candidate, never a finding. Detectors bail out on constructs
whose purpose they cannot see: ABI markers, address-taken or macro/ASM-
referenced functions, labels between instructions, conditional assembly, and
unknown opcodes. References are always counted across the whole context so a
narrow target never makes a used symbol look dead.
"""
from __future__ import annotations

import argparse
import difflib
import math
import re
import statistics
import subprocess
import sys
import zlib
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

COMMON_SCRIPTS = Path(__file__).resolve().parents[2] / "shrink-z80" / "scripts"
if str(COMMON_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(COMMON_SCRIPTS))

from scan_common import (  # noqa: E402
    ASM_MNEMONICS,
    C_EXTS,
    active_c_lines,
    read_text_lines,
    rel_path,
    resolve_target_scope,
    source_kind,
    split_label,
    strip_c_comments,
)
from artifact_freshness import is_declared_generated_source  # noqa: E402
from winner_census import CODE_SECTION_HINTS, LOCAL_PREFIXES, MAP_RE  # noqa: E402

CRAFT_C_EXTS = C_EXTS - {".i"}
CRAFT_ASM_EXTS = {".asm", ".s", ".inc"}

# key: (group, hotspot weight, what the reviewer must prove before promoting)
SECTIONS: dict[str, tuple[str, int, str]] = {
    "c-forwarder": ("structural", 3, "callers can use the target directly; keep ABI bridges, function-pointer adapters and documented public facades"),
    "c-trivial-single-use": ("structural", 2, "SDCC does not inline it; inline at the one site unless it names a concept the caller needs"),
    "c-constant-argument": ("structural", 3, "fold the constant into the callee; host tests and other targets must not pass another value"),
    "c-unused-parameter": ("structural", 3, "no other target variant, function-pointer type or ASM caller fixes this signature"),
    "c-codegen-outlier": ("codegen", 2, "read the generated .lst: function-like macros expanded per site, int/long math, struct access through IX, helper calls"),
    "asm-forwarder": ("structural", 3, "defc/EQU alias costs 0 bytes; a fixed vector or overlay entry may need the jump"),
    "asm-push-pop-unclobbered": ("idiom", 2, "no write to the pair, no SP-relative access, and no exit between the push and the pop"),
    "asm-jump-to-ret": ("idiom", 1, "the target's first instruction is a bare ret; ret cc is 1 byte and also exits"),
    "asm-constant-register-arg": ("structural", 3, "load the constant once inside the routine; every entry path must load the same value"),
    "c-clone-family": ("structural", 3, "one owner can serve all members; separate overlays cannot share code without a resident or common copy"),
    "asm-clone-family": ("structural", 3, "one owner can serve all members; separate overlays cannot share code without a resident or common copy"),
    "comment-narration": ("comment", 1, "the comment restates the instruction; keep only the why"),
    "comment-history": ("comment", 1, "history belongs in git; keep the current contract"),
}

C_KEYWORDS = {
    "auto", "break", "case", "char", "const", "continue", "default", "do", "double",
    "else", "enum", "extern", "float", "for", "goto", "if", "inline", "int", "long",
    "register", "return", "short", "signed", "sizeof", "static", "struct", "switch",
    "typedef", "union", "unsigned", "void", "volatile", "while", "_Bool", "bool",
    "true", "false", "NULL",
}
TYPE_WORDS = {
    "unsigned", "signed", "int", "short", "long", "char", "const", "volatile", "register",
    "static", "uint8_t", "int8_t", "uint16_t", "int16_t", "uint32_t", "int32_t", "size_t",
    "u8", "s8", "u16", "s16", "u32", "s32", "word", "byte",
}
NOT_ABI_ATTRS = {"__asm", "__endasm", "__asm__", "__FILE__", "__LINE__", "__func__"}

TOKEN_RE = re.compile(
    r'"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'|0[xX][0-9A-Fa-f]+[uUlL]*|\d+[uUlL]*'
    r"|[A-Za-z_]\w*|->|\+\+|--|<<=|>>=|<<|>>|<=|>=|==|!=|&&|\|\||[-+*/%&|^]=|\.\.\.|\S"
)
LOCAL_INCLUDE_RE = re.compile(r'#\s*include\s+"([^"]+)"')
DEFINE_RE = re.compile(r"#\s*define\s+([A-Za-z_]\w*)(\([^)]*\))?\s*(.*)")

REG8 = {"a", "b", "c", "d", "e", "h", "l", "i", "r", "ixh", "ixl", "iyh", "iyl", "xh", "xl", "yh", "yl", "hx", "lx", "hy", "ly"}
REG16 = {"af", "bc", "de", "hl", "ix", "iy", "sp", "af'"}
HALVES = {
    "af": {"a", "f", "af"},
    "bc": {"b", "c", "bc"}, "de": {"d", "e", "de"}, "hl": {"h", "l", "hl"},
    "ix": {"ix", "ixh", "ixl", "xh", "xl", "hx", "lx"},
    "iy": {"iy", "iyh", "iyl", "yh", "yl", "hy", "ly"},
}
CONDITIONS = {"z", "nz", "c", "nc", "m", "p", "pe", "po"}
EXTRA_MNEMONICS = {"outi", "outd", "sll", "sli", "ld", "ex"}
MNEMONICS = set(ASM_MNEMONICS) | EXTRA_MNEMONICS
COND_DIRECTIVES_OPEN = {"if", "ifdef", "ifndef", "#if", "#ifdef", "#ifndef"}
COND_DIRECTIVES_CLOSE = {"endif", "#endif"}
PUBLIC_DIRECTIVES = {"public", "global", "xdef"}
DIRECTIVE_WORDS = {"if", "ifdef", "ifndef", "else", "elif", "endif", "macro", "endm", "rept", "endr", "section", "org", "align"}
NUMBER_RE = re.compile(r"^(?:\$[0-9a-f]+|#[0-9a-f]+|0x[0-9a-f]+|[0-9][0-9a-f]*h|%[01]+|[01]+b|\d+)$", re.IGNORECASE)
ASM_IDENT_RE = re.compile(r"(?<![\w$#%.'])([A-Za-z_][\w.]*)")
ZSET_FROM_A_ROT = {"rl", "rr", "rlc", "rrc", "sla", "sra", "srl", "sll", "sli"}

STOP_WORDS = {
    "the", "a", "an", "to", "into", "in", "of", "with", "by", "from", "for", "and", "on",
    "at", "as", "is", "it", "its", "this", "that", "then", "value", "register", "reg",
    "el", "la", "los", "las", "un", "una", "en", "de", "del", "con", "al", "y", "por",
    "para", "que", "se", "lo", "valor", "registro", "variable", "var",
}
ASM_WORDS = {
    "ld": "load loads loaded set sets put puts store stores copy copies move moves get gets read reads write writes carga cargar guarda guardar copia copiar mueve mover pon poner lee leer escribe",
    "inc": "increment increments inc incrementa incrementar next advance advances bump 1 one plus uno siguiente avanza",
    "dec": "decrement decrements dec decrementa decrementar previous minus 1 one uno",
    "push": "push pushes save saves preserve preserves stack guarda salva pila apila",
    "pop": "pop pops restore restores recover stack recupera restaura pila desapila",
    "ret": "return returns exit done retorna vuelve volver salir sale",
    "call": "call calls invoke run llama llamar ejecuta routine rutina subroutine",
    "jp": "jump jumps goto go branch salta saltar ir",
    "jr": "jump jumps goto go branch salta saltar ir",
    "djnz": "loop loops decrement bucle repeat until zero jump",
    "xor": "clear clears zero zeroes reset limpia borra cero xor toggle invert flip",
    "or": "or test check zero set bits comprueba prueba mask",
    "and": "and mask masks keep bits mascara test",
    "cp": "compare compares check checks test is equal compara comprueba igual cmp",
    "add": "add adds plus sum suma sumar",
    "sub": "subtract subtracts minus resta restar",
    "srl": "shift right divide half 2 desplaza derecha",
    "sla": "shift left multiply double 2 desplaza izquierda",
    "rla": "rotate rotates shift left carry rota", "rra": "rotate rotates shift right carry rota",
    "rlca": "rotate rotates shift left rota", "rrca": "rotate rotates shift right rota",
    "rl": "rotate rotates shift left carry rota", "rr": "rotate rotates shift right carry rota",
    "out": "output write send port envia escribe puerto out",
    "in": "input read port lee puerto in",
    "ex": "exchange swap intercambia",
    "neg": "negate negative niega negativo",
    "cpl": "complement invert not invierte",
    "di": "disable interrupts deshabilita interrupciones",
    "ei": "enable interrupts habilita interrupciones",
    "ldir": "copy block bytes copia bloque move",
    "scf": "set carry", "ccf": "complement carry flip",
    "bit": "test bit check comprueba", "set": "set bit pon", "res": "reset clear bit limpia",
}
C_WORDS = {
    "++": "increment increments inc incrementa advance next bump",
    "--": "decrement decrements decrementa",
    "=": "set sets assign assigns store stores save put initialize initialise init reset asigna guarda pon inicializa",
    "return": "return returns devuelve retorna",
    "if": "if check checks si comprueba test",
    "for": "loop iterate each over bucle recorre cada",
    "while": "loop while until mientras",
    "+": "add plus sum suma", "-": "subtract minus resta",
    "(": "call calls invoke llama",
}
REGISTER_WORDS = REG8 | REG16 | {"accumulator", "acumulador"}
HISTORY_RE = re.compile(
    r"\b(no longer|(?:it|this|we|code|caller|function|routine) used to"
    r"|previously (?:used|was|were|did|called|stored|returned|kept|lived)"
    r"|was (?:changed|renamed|moved|replaced|removed)|changed (?:from|to)|replaced (?:by|with)"
    r"|old (?:code|version|implementation)|new (?:code|version|implementation)|refactor(?:ed|ing)?"
    r"|ya no|antes (?:se|era|usaba|hac[ií]a)|versi[oó]n anterior|sustituido por|reemplazad[oa] por)\b",
    re.IGNORECASE,
)
C_CODE_COMMENT_RE = re.compile(
    r"""^\s*(?:
        (?:if|for|while|switch)\s*\(.*\)\s*\{?\s*$
      | return\b[^.!?]*;\s*$
      | [A-Za-z_][\w.\->\[\]]*\s*(?:[-+*/%&|^]?=|\+\+|--)\s*[^=].*;\s*$
      | [A-Za-z_]\w*\s*\(.*\)\s*;\s*$
      | [{}]\s*;?\s*$
      | (?:(?:static|const|unsigned|signed)\s+)*(?:u?int\d+_t|char|int|void|long|short)\s+\**\s*\w+[^.!?]*[;{]\s*$
    )""",
    re.VERBOSE,
)
ASM_OPERAND_RE = re.compile(r"^(?:\(.+\)|[$#%]?[0-9A-Fa-f]+h?|[A-Za-z_][\w.]*|'.')$")


@dataclass
class Lead:
    key: str
    path: Path
    line: int
    text: str
    detail: str
    spans: list[tuple[Path, int, int]] = field(default_factory=list)
    members: list[str] = field(default_factory=list)
    line_ratio: float = 0.0
    symbol: str = ""


@dataclass
class CFunc:
    name: str
    path: Path
    line: int
    end: int
    static: bool
    attrs: set[str]
    params: list[str | None]
    variadic: bool
    body: list[tuple[str, int]]
    has_asm: bool = False
    variant: bool = False


@dataclass
class CallSite:
    caller: CFunc
    line: int
    args: list[list[str]]


@dataclass
class AsmLine:
    no: int
    label: str | None
    mn: str | None
    ops: list[str]
    raw_ops: list[str]
    comment: str
    directive: str | None
    depth: int
    in_macro: bool
    code: str


@dataclass
class Routine:
    name: str
    path: Path
    start: int
    end: int
    lines: list[AsmLine]
    fallthrough: bool = False


# ---------------------------------------------------------------- C parsing

def tok_kind(tok: str) -> str:
    if tok[0] == '"':
        return "str"
    if tok[0] == "'":
        return "chr"
    if tok[0].isdigit():
        return "num"
    if tok[0].isalpha() or tok[0] == "_":
        return "id"
    return "op"


def is_ident(tok: str) -> bool:
    return tok_kind(tok) == "id" and tok not in C_KEYWORDS


def match_close(tokens: list[tuple[str, int]], start: int, open_: str, close: str) -> int:
    depth = 0
    for idx in range(start, len(tokens)):
        text = tokens[idx][0]
        if text == open_:
            depth += 1
        elif text == close:
            depth -= 1
            if depth == 0:
                return idx
    return len(tokens) - 1


def match_open(tokens: list[tuple[str, int]], close_idx: int, open_: str, close: str) -> int:
    depth = 0
    for idx in range(close_idx, -1, -1):
        text = tokens[idx][0]
        if text == close:
            depth += 1
        elif text == open_:
            depth -= 1
            if depth == 0:
                return idx
    return -1


def split_args(tokens: list[tuple[str, int]], open_idx: int, close_idx: int) -> list[list[str]]:
    args: list[list[str]] = [[]]
    depth = 0
    for text, _ in tokens[open_idx + 1:close_idx]:
        if text in "([{":
            depth += 1
        elif text in ")]}":
            depth -= 1
        if text == "," and depth == 0:
            args.append([])
        else:
            args[-1].append(text)
    return [] if args == [[]] else args


def comment_parts(lines: list[str]) -> list[tuple[int, str, bool, bool]]:
    """(line, comment text, code before it on the line, part of a multi-line block)."""
    out: list[tuple[int, str, bool, bool]] = []
    in_block = False
    for lineno, line in enumerate(lines, start=1):
        idx, quote, code_seen = 0, None, False
        buf: list[str] = []
        block_started_here = False
        while idx < len(line):
            ch, nxt = line[idx], line[idx + 1:idx + 2]
            if in_block:
                if ch == "*" and nxt == "/":
                    in_block = False
                    out.append((lineno, "".join(buf), code_seen, not block_started_here))
                    buf = []
                    idx += 2
                    continue
                buf.append(ch)
                idx += 1
                continue
            if quote:
                if ch == "\\":
                    idx += 2
                    continue
                if ch == quote:
                    quote = None
                idx += 1
                continue
            if ch in "\"'":
                quote = ch
                code_seen = True
            elif ch == "/" and nxt == "/":
                out.append((lineno, line[idx + 2:], code_seen, False))
                break
            elif ch == "/" and nxt == "*":
                in_block = True
                block_started_here = True
                idx += 2
                continue
            elif not ch.isspace():
                code_seen = True
            idx += 1
        if in_block:
            out.append((lineno, "".join(buf), code_seen, True))
    return out


IF_RE = re.compile(r"#\s*if(?:def|ndef)?\b")
BRANCH_RE = re.compile(r"#\s*(?:else|elif)\b")
ENDIF_RE = re.compile(r"#\s*endif\b")


def last_branch_lines(lines: list[str]) -> list[tuple[int, str]]:
    """Like active_c_lines, but a conditional with #else or #elif keeps only its last branch."""
    branches: dict[int, int] = {}
    stack: list[int] = []
    in_block = False
    for lineno, raw in enumerate(lines, start=1):
        code, in_block = strip_c_comments(raw, in_block)
        stripped = code.strip().lower()
        if IF_RE.match(stripped):
            stack.append(lineno)
            branches[lineno] = 1
        elif BRANCH_RE.match(stripped) and stack:
            branches[stack[-1]] += 1
        elif ENDIF_RE.match(stripped) and stack:
            stack.pop()
    frames: list[list[int]] = []  # [branch count, current branch, zero]
    out: list[tuple[int, str]] = []
    in_block = False
    for lineno, raw in enumerate(lines, start=1):
        code, in_block = strip_c_comments(raw, in_block)
        stripped = code.strip().lower()
        if IF_RE.match(stripped):
            frames.append([branches[lineno], 0, bool(re.match(r"#\s*if\s+(?:0|false)\b", stripped))])
        elif BRANCH_RE.match(stripped) and frames:
            frames[-1][1] += 1
        elif ENDIF_RE.match(stripped) and frames:
            frames.pop()
        elif all(cur == count - 1 and (cur or not zero) for count, cur, zero in frames):
            out.append((lineno, code))
    return out


class CFile:
    def __init__(self, path: Path, lines: list[str], alternate: bool = False):
        self.path = path
        self.lines = lines
        # idents on lines this pass does not parse; main decides which stay opaque
        self.skipped_ids: dict[int, list[str]] = {}
        self.tokens: list[tuple[str, int]] = []
        self.opaque: list[str] = []
        self.includes: set[str] = set()
        self.macro_attrs: dict[str, set[str]] = {}
        self.asm_lines: set[int] = set()
        self.code_lines = 0
        self.code_by_line: dict[int, str] = {}
        self.inactive: set[str] = set()
        self.cond_lines: set[int] = set()
        active = dict(last_branch_lines(lines) if alternate else active_c_lines(lines))
        in_block, in_pp, in_asm = False, False, False
        for lineno, raw in enumerate(lines, start=1):
            code, in_block = strip_c_comments(raw, in_block)
            stripped = code.strip()
            if lineno not in active:
                if re.match(r"#\s*(?:if|ifdef|ifndef|else|elif)\b", stripped):
                    self.cond_lines.add(lineno)
                idents = [t for t in TOKEN_RE.findall(code) if tok_kind(t) == "id"]
                self.skipped_ids[lineno] = idents
                self.inactive.update(idents)
                continue
            if in_pp:
                self.opaque.extend(t for t in TOKEN_RE.findall(code) if tok_kind(t) == "id")
                in_pp = stripped.endswith("\\")
                continue
            if stripped.startswith("__asm") and "__endasm" not in stripped and "(" not in stripped:
                in_asm = True
                self.tokens.append(("__asm", lineno))
                continue
            if in_asm and stripped.startswith("__endasm"):
                in_asm = False
                self.tokens.extend((t, lineno) for t in TOKEN_RE.findall(code))
                continue
            if stripped.startswith("#"):
                if re.match(r"#\s*asm\b", stripped):
                    in_asm = True
                elif re.match(r"#\s*endasm\b", stripped):
                    in_asm = False
                include = LOCAL_INCLUDE_RE.match(stripped)
                if include:
                    self.includes.add(Path(include.group(1)).name)
                define = DEFINE_RE.match(stripped)
                if define:
                    body_tokens = TOKEN_RE.findall(define.group(3))
                    self.opaque.extend(t for t in body_tokens if tok_kind(t) == "id")
                    attrs = {t for t in body_tokens if t.startswith("__") and t not in NOT_ABI_ATTRS}
                    if attrs and not define.group(2):
                        self.macro_attrs[define.group(1)] = attrs
                in_pp = stripped.endswith("\\")
                continue
            if in_asm:
                self.asm_lines.add(lineno)
                self.opaque.extend(ASM_IDENT_RE.findall(split_comment(raw)[0]))
                continue
            if stripped:
                self.code_lines += 1
                self.code_by_line[lineno] = stripped
            self.tokens.extend((t, lineno) for t in TOKEN_RE.findall(code))
        self.comments = [c for c in comment_parts(lines) if c[0] not in self.asm_lines]
        self.inline_asm = [raw if lineno in self.asm_lines else "    #c" for lineno, raw in enumerate(lines, start=1)]


def is_attr(tok: str, macro_attrs: dict[str, set[str]]) -> bool:
    return (tok.startswith("__") and tok not in NOT_ABI_ATTRS) or tok in macro_attrs


def is_marker(tok: str, macro_attrs: dict[str, set[str]]) -> bool:
    """An attribute, or an unresolved ALLCAPS macro between ) and {."""
    return is_attr(tok, macro_attrs) or (is_ident(tok) and tok.isupper() and len(tok) > 1)


def parse_params(tokens: list[tuple[str, int]], open_idx: int, close_idx: int) -> tuple[list[str | None], bool]:
    params: list[str | None] = []
    variadic = False
    for arg in split_args(tokens, open_idx, close_idx):
        if arg == ["void"]:
            continue
        if "..." in arg:
            variadic = True
            continue
        name = None
        for idx in range(len(arg) - 2):
            if arg[idx] == "(" and arg[idx + 1] == "*" and is_ident(arg[idx + 2]):
                name = arg[idx + 2]
                break
        if name is None:
            idents = [t for t in arg if is_ident(t)]
            if len(arg) >= 2 and idents and idents[-1] not in TYPE_WORDS:
                name = idents[-1]
                if arg[-1] == "]":
                    bracket = arg.index("[")
                    cands = [t for t in arg[:bracket] if is_ident(t)]
                    name = cands[-1] if cands else None
        params.append(name)
    return params, variadic


def parse_c(cfile: CFile, macros: dict[str, set[str]]) -> tuple[list[CFunc], dict[str, set[str]], Counter[str]]:
    tokens = cfile.tokens
    funcs: list[CFunc] = []
    proto_attrs: dict[str, set[str]] = defaultdict(set)
    refs: Counter[str] = Counter()
    stmt_start = 0
    idx = 0
    while idx < len(tokens):
        text = tokens[idx][0]
        if text == "{":
            end = match_close(tokens, idx, "{", "}")
            func = function_header(cfile, stmt_start, idx, end, macros)
            if func:
                funcs.append(func)
                idx = end + 1
                stmt_start = idx
                continue
            for tok, _ in tokens[idx:end + 1]:
                if is_ident(tok):
                    refs[tok] += 1
            looked_like_function = idx and tokens[idx - 1][0] == ")"
            idx = end + 1
            if looked_like_function:
                stmt_start = idx
            continue
        if text == ";":
            stmt = tokens[stmt_start:idx]
            attrs = {t for t, _ in stmt if is_attr(t, macros)}
            for pos, (tok, _) in enumerate(stmt):
                if is_ident(tok) and pos + 1 < len(stmt) and stmt[pos + 1][0] == "(":
                    proto_attrs[tok] |= {a for attr in attrs for a in macros.get(attr, {attr})}
                elif is_ident(tok) and "=" in [t for t, _ in stmt[:pos]]:
                    refs[tok] += 1
            stmt_start = idx + 1
        idx += 1
    return funcs, proto_attrs, refs


def function_header(cfile: CFile, start: int, brace: int, end: int, macros: dict[str, set[str]]) -> CFunc | None:
    tokens = cfile.tokens
    pos = brace - 1
    attrs: set[str] = set()
    while pos > start:
        tok = tokens[pos][0]
        if is_marker(tok, macros):
            attrs |= macros.get(tok, {tok})
            pos -= 1
            continue
        if tok == ")":
            open_idx = match_open(tokens, pos, "(", ")")
            if open_idx > start and is_marker(tokens[open_idx - 1][0], macros) and open_idx - 2 > start and tokens[open_idx - 2][0] == ")":
                attrs.add(tokens[open_idx - 1][0])
                pos = open_idx - 2
                continue
        break
    if pos <= start or tokens[pos][0] != ")":
        return None
    open_idx = match_open(tokens, pos, "(", ")")
    if open_idx <= start:
        return None
    name, line = tokens[open_idx - 1]
    prefix = [t for t, _ in tokens[start:open_idx - 1]]
    if not is_ident(name) or any(t in {"=", "typedef", "(", ")", ","} for t in prefix):
        return None
    attrs |= {a for t in prefix if is_attr(t, macros) for a in macros.get(t, {t})}
    params, variadic = parse_params(tokens, open_idx, pos)
    body = tokens[brace + 1:end]
    func = CFunc(
        name=name, path=cfile.path, line=line, end=tokens[end][1], static="static" in prefix,
        attrs=attrs, params=params, variadic=variadic, body=body,
    )
    func.variant = any(line <= ln <= func.end for ln in cfile.cond_lines)
    func.has_asm = any(t in {"__asm", "__asm__", "asm"} for t, _ in body) or any(
        line <= ln <= func.end for ln in cfile.asm_lines
    )
    return func


def body_calls(func: CFunc) -> list[tuple[str, int, list[list[str]]]]:
    out = []
    body = func.body
    for idx, (tok, line) in enumerate(body[:-1]):
        if not is_ident(tok) or body[idx + 1][0] != "(":
            continue
        if idx and body[idx - 1][0] in {".", "->"}:
            continue
        close = match_close(body, idx + 1, "(", ")")
        out.append((tok, line, split_args(body, idx + 1, close)))
    return out


def body_refs(func: CFunc) -> list[str]:
    body = func.body
    return [
        tok for idx, (tok, _) in enumerate(body)
        if is_ident(tok) and (idx + 1 >= len(body) or body[idx + 1][0] != "(")
    ]


# -------------------------------------------------------------- ASM parsing

def split_comment(line: str) -> tuple[str, str]:
    quote = None
    for idx, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"":
            quote = ch
        elif ch == "'" and not line[max(0, idx - 2):idx].lower().endswith("af"):
            if line[idx + 2:idx + 3] == "'":
                quote = ch
        elif ch == ";":
            return line[:idx], line[idx + 1:]
    return line, ""


def split_operands(text: str) -> list[str]:
    ops, depth, buf = [], 0, []
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            ops.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    tail = "".join(buf).strip()
    if tail or ops:
        ops.append(tail)
    return ops


def split_statements(code: str) -> list[str]:
    """sjasmplus and z80asm put several statements on one line separated by ':'."""
    parts, buf, quote, depth = [], [], "", 0
    for ch in code:
        if quote:
            quote = "" if ch == quote else quote
        elif ch in "\"'":
            quote = ch
        elif ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif ch == ":" and depth == 0:
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    return parts + ["".join(buf)]


def parse_asm(lines: list[str]) -> list[AsmLine]:
    out: list[AsmLine] = []
    depth, in_macro = 0, False
    dead: list[bool] = []  # per open IF: inside an IF 0 arm, never assembled
    for lineno, raw in enumerate(lines, start=1):
        code, comment = split_comment(raw)
        label, rest = split_label(code)
        if label and label.lower() in DIRECTIVE_WORDS:
            label, rest = None, code.strip()
        # each extra statement after ':' becomes its own line with the same number
        for idx, stmt in enumerate(split_statements(rest) if rest else [rest]):
            stmt = stmt.strip()
            words = stmt.split(None, 1)
            first = words[0].lower() if words else ""
            second = stmt.split()[1].lower() if len(stmt.split()) > 1 else ""
            mn, ops, raw_ops, directive = None, [], [], None
            bare_equ = idx == 0 and label is None and code[:1].strip() and second in {"equ", "macro", "=", "defl"}
            if first in MNEMONICS and not bare_equ:
                mn = first
                raw_ops = split_operands(words[1]) if len(words) > 1 else []
                ops = [op.lower().replace(" ", "") for op in raw_ops]
            elif first:
                directive = first
            if idx == 0 and label and not mn and not directive and code.strip().split()[0].lower() in {"equ", "defl"}:
                directive = "equ"
            line_depth = depth
            if directive in COND_DIRECTIVES_OPEN:
                depth += 1
                dead.append(directive in {"if", "#if"} and second in {"0", "false"})
            elif directive in COND_DIRECTIVES_CLOSE:
                depth = max(0, depth - 1)
                line_depth = depth
                if dead:
                    dead.pop()
            elif directive in {"else", "#else"} and dead:
                dead[-1] = False
            elif any(dead):
                out.append(AsmLine(lineno, None, None, [], [], comment.strip(), "dead", line_depth, in_macro, stmt))
                continue
            if directive == "macro" or second == "macro":
                in_macro = True
            out.append(AsmLine(lineno, label if idx == 0 else None, mn, ops, raw_ops,
                               comment.strip() if idx == 0 else "", directive, line_depth, in_macro, stmt))
            if directive == "endm":
                in_macro = False
    return out


def reg_of(op: str) -> str | None:
    return op if op in REG8 or op in REG16 else None


def expand(regs: set[str]) -> set[str]:
    """A pair stands for both of its halves."""
    out = set(regs)
    for reg in regs:
        out |= HALVES.get(reg, set())
    return out


def overlapping(reg: str) -> set[str]:
    """Names whose read or write also reads or writes reg: itself, its halves, its pair."""
    return {reg} | HALVES.get(reg, set()) | {pair for pair, halves in HALVES.items() if reg in halves}


def asm_reads(mn: str, ops: list[str]) -> set[str] | None:
    """Registers read; None when the instruction reads implicitly (block ops, exchanges)."""
    if mn in {"ex", "exx", "ldir", "lddr", "ldi", "ldd", "cpir", "cpdr", "cpi", "cpd",
              "inir", "indr", "ini", "ind", "otir", "otdr", "outi", "outd", "djnz", "rst",
              "call", "ret", "reti", "retn", "jp", "jr", "halt"}:
        return None
    srcs = ops[1:] if mn in {"ld", "pop", "in"} and ops and reg_of(ops[0]) else ops
    regs = {tok for op in srcs for tok in re.findall(r"[a-z]+'?", op) if tok in REG8 or tok in REG16}
    if mn in {"add", "adc", "sub", "sbc", "and", "or", "xor", "cp", "neg", "cpl", "daa",
              "rla", "rra", "rlca", "rrca", "rld", "rrd"} and not (ops and ops[0] in REG16):
        regs.add("a")
    if (mn == "out" and ops and ops[0] == "(c)") or (mn == "in" and ops[-1:] == ["(c)"]):
        regs.add("bc")
    if mn == "in" and ops[-1:] != ["(c)"]:
        regs.add("a")
    return regs


def asm_writes(mn: str, ops: list[str]) -> set[str] | None:
    """Registers written; None when the effect is not a simple local write."""
    if any("sp" in re.findall(r"[a-z']+", op) for op in ops):
        return None
    if mn == "ld":
        if len(ops) != 2 or ops[0] in {"i", "r"}:
            return None
        reg = reg_of(ops[0])
        return {reg} if reg else set()
    if mn in {"inc", "dec"}:
        reg = reg_of(ops[0]) if ops else None
        return {reg} if reg else set()
    if mn in {"add", "adc", "sbc"} and len(ops) == 2 and ops[0] in REG16:
        return {ops[0]}
    if mn in {"add", "adc", "sub", "sbc", "and", "or", "xor", "neg", "cpl", "daa", "rla", "rra", "rlca", "rrca", "rld", "rrd"}:
        return {"a"}
    if mn in {"cp", "bit", "scf", "ccf", "nop", "di", "ei", "im", "out", "push"}:
        return set()
    if mn in ZSET_FROM_A_ROT | {"set", "res"}:
        if not ops:
            return None
        reg = reg_of(ops[-1])
        return {reg} if reg else set()
    if mn == "in":
        reg = reg_of(ops[0]) if ops else None
        return {reg} if reg and reg != "f" else set()
    if mn == "pop":
        reg = reg_of(ops[0]) if ops else None
        return {reg} if reg else None
    return None


def is_uncond_exit(line: AsmLine) -> bool:
    if line.mn in {"ret", "reti", "retn"}:
        return not line.ops
    if line.mn in {"jp", "jr"}:
        return len(line.ops) == 1 and not line.ops[0].startswith("$")
    return False


def branch_symbol(line: AsmLine) -> str | None:
    if line.mn not in {"call", "jp", "jr", "djnz"} or not line.raw_ops:
        return None
    target = line.raw_ops[-1].strip()
    return target if re.fullmatch(r"[A-Za-z_][\w.]*", target) else None


def operand_symbols(ops: list[str]) -> list[str]:
    out = []
    for op in ops:
        for name in ASM_IDENT_RE.findall(op):
            low = name.lower()
            if low in REG8 or low in REG16 or low in CONDITIONS or NUMBER_RE.match(name):
                continue
            out.append(name)
    return out


def is_immediate(op: str) -> bool:
    return bool(op) and not op.startswith("(") and reg_of(op) is None and op not in CONDITIONS


class AsmFile:
    def __init__(self, path: Path, lines: list[str]):
        self.path = path
        self.lines = parse_asm(lines)
        self.instr_lines = sum(1 for line in self.lines if line.mn)


@dataclass
class AsmIndex:
    calls: dict[str, list[tuple[AsmFile, int]]] = field(default_factory=lambda: defaultdict(list))
    jumps: dict[str, list[tuple[AsmFile, int]]] = field(default_factory=lambda: defaultdict(list))
    relative: dict[str, list[tuple[AsmFile, int]]] = field(default_factory=lambda: defaultdict(list))
    data: Counter[str] = field(default_factory=Counter)
    public: set[str] = field(default_factory=set)


def index_asm(files: list[AsmFile]) -> AsmIndex:
    index = AsmIndex()
    for afile in files:
        for pos, line in enumerate(afile.lines):
            if line.mn:
                target = branch_symbol(line)
                if target:
                    bucket = {"call": index.calls, "jp": index.jumps}.get(line.mn, index.relative)
                    bucket[target].append((afile, pos))
                    others = operand_symbols(line.raw_ops[:-1])
                else:
                    others = operand_symbols(line.raw_ops)
                index.data.update(others)
            elif line.directive:
                code = line.code
                if line.directive in PUBLIC_DIRECTIVES:
                    index.public.update(re.findall(r"[A-Za-z_][\w.]*", code.split(None, 1)[1] if len(code.split(None, 1)) > 1 else ""))
                elif line.directive not in {"extern", "xref", "section", "module", "include", "binary", "incbin"}:
                    index.data.update(operand_symbols([code.split(None, 1)[1]] if len(code.split(None, 1)) > 1 else []))
    return index


def routines_of(afile: AsmFile, index: AsmIndex) -> list[Routine]:
    starts: list[int] = []
    prev_exit, prev_data, first = True, False, True
    for pos, line in enumerate(afile.lines):
        if line.label:
            name = line.label
            entry = (
                name in index.calls or name in index.public or index.data.get(name)
                or first or prev_data or (prev_exit and name not in index.relative)
            )
            if entry:
                starts.append(pos)
            first = False
        if line.mn:
            prev_exit = is_uncond_exit(line)
            prev_data = False
        elif line.directive and line.directive not in COND_DIRECTIVES_OPEN | COND_DIRECTIVES_CLOSE | {"else", "#else"}:
            prev_data = True
    out = []
    for idx, start in enumerate(starts):
        stop = starts[idx + 1] if idx + 1 < len(starts) else len(afile.lines)
        body = afile.lines[start:stop]
        last = max((line.no for line in body if line.mn or line.label), default=body[0].no)
        out.append(Routine(afile.lines[start].label or "?", afile.path, body[0].no, last, body,
                           falls_into(afile.lines, start)))
    return out


def falls_into(lines: list[AsmLine], pos: int) -> bool:
    """Execution can reach lines[pos] from the instruction above it."""
    for idx in range(pos - 1, -1, -1):
        line = lines[idx]
        if line.mn:
            return not is_uncond_exit(line)
        if line.directive and line.directive not in COND_DIRECTIVES_OPEN | COND_DIRECTIVES_CLOSE:
            return False
    return False


def next_instr(lines: list[AsmLine], pos: int, *, cross_labels: bool = False) -> int | None:
    for idx in range(pos + 1, len(lines)):
        line = lines[idx]
        if line.label and not cross_labels:
            return None
        if line.mn:
            return idx
        if line.directive:
            return None
    return None


def prev_instr(lines: list[AsmLine], pos: int) -> int | None:
    if lines[pos].label:
        return None
    for idx in range(pos - 1, -1, -1):
        line = lines[idx]
        if line.mn:
            return idx
        if line.label or line.directive:
            return None
    return None




# ----------------------------------------------------------------- detectors

def snippet(code: str) -> str:
    return " ".join(code.split())[:96]


def c_detectors(cfiles: list[CFile], funcs: list[CFunc], asm_refs: Counter[str],
                proto_attrs: dict[str, set[str]], global_refs: Counter[str]) -> list[Lead]:
    leads: list[Lead] = []
    groups = include_groups(cfiles)
    by_name: dict[str, list[CFunc]] = defaultdict(list)
    for func in funcs:
        by_name[func.name].append(func)
    opaque: Counter[str] = Counter()
    for cfile in cfiles:
        opaque.update(cfile.opaque)
    opaque.update(asm_refs)

    calls: dict[int, list[CallSite]] = defaultdict(list)
    nocall_refs: Counter[str] = Counter(global_refs)
    for func in funcs:
        for name, line, args in body_calls(func):
            for target in resolve(name, func, by_name, groups):
                calls[id(target)].append(CallSite(func, line, args))
        nocall_refs.update(body_refs(func))

    def pinned(func: CFunc) -> bool:
        return bool(nocall_refs[func.name] or opaque[func.name] or len(by_name[func.name]) > 1)

    for func in funcs:
        sites = calls[id(func)]
        span = [(func.path, func.line, func.end)]
        inner = [t for t, _ in func.body]
        abi = bool(func.attrs)
        # forwarder
        if not abi and not pinned(func) and inner and len(inner) >= 4:
            core = inner[1:] if inner[0] == "return" else inner
            if core[-1] == ";" and is_ident(core[0]) and core[1] == "(" and match_close(
                [(t, 0) for t in core], 1, "(", ")"
            ) == len(core) - 2:
                target = core[0]
                args = split_args([(t, 0) for t in core], 1, len(core) - 2)
                target_attrs = proto_attrs.get(target, set()) | {a for f in by_name.get(target, []) for a in f.attrs}
                params = [p for p in func.params if p]
                simple = all(len(a) == 1 and (a[0] in params or tok_kind(a[0]) in {"num", "chr"} or a[0].isupper()) for a in args)
                fixed = sum(1 for a in args if a[0] not in params) if simple else 0
                hidden = not func.static and any(t.static for t in resolve(target, func, by_name, groups))
                if simple and sites and not hidden and target != func.name and not target_attrs and (fixed == 0 or len(sites) <= 1):
                    kind = "same arguments" if fixed == 0 and [a[0] for a in args] == params else (
                        f"fixes {fixed} argument(s)" if fixed else "reorders or drops parameters")
                    leads.append(Lead("c-forwarder", func.path, func.line, f"{func.name} -> {target}",
                                      f"{kind}; call sites={len(sites)}{'' if func.static else '; extern'}", span))
        if pinned(func) or func.has_asm or abi or func.variadic:
            continue
        named = [(i, p) for i, p in enumerate(func.params) if p]
        arity_ok = sites and all(len(s.args) == len(func.params) for s in sites)
        # trivial single use
        if func.static and len(sites) == 1 and len(inner) <= 12:
            site = sites[0]
            leads.append(Lead("c-trivial-single-use", func.path, func.line, func.name,
                              f"{len(inner)} body tokens; only caller {site.caller.name} at {rel_path(site.caller.path, site.caller.path.parent)}:{site.line}",
                              span + [(site.caller.path, site.line, site.line)], symbol=func.name))
        # constant argument
        if arity_ok and len(sites) >= 2:
            for pos, pname in named:
                values = {" ".join(s.args[pos]) for s in sites}
                arg = sites[0].args[pos]
                literal = len(arg) == 1 and (tok_kind(arg[0]) in {"num", "chr"} or arg[0].isupper() or arg[0] in {"true", "false", "NULL"})
                if len(values) == 1 and literal:
                    leads.append(Lead("c-constant-argument", func.path, func.line, f"{func.name}({pname})",
                                      f"every one of {len(sites)} call sites passes {arg[0]}{'' if func.static else '; extern'}",
                                      [(func.path, func.line, func.line)] + [(s.caller.path, s.line, s.line) for s in sites],
                                      symbol=func.name))
        # unused parameter
        used = {t for t in inner if is_ident(t)}
        if inner:
            for _, pname in named:
                if pname not in used:
                    leads.append(Lead("c-unused-parameter", func.path, func.line, f"{func.name}({pname})",
                                      f"never read; call sites={len(sites)}{'' if func.static else '; extern'}", span))
    return leads


def include_groups(cfiles: list[CFile]) -> dict[Path, int]:
    parent = {cfile.path: cfile.path for cfile in cfiles}
    by_base: dict[str, list[Path]] = defaultdict(list)
    for cfile in cfiles:
        by_base[cfile.path.name].append(cfile.path)

    def find(node: Path) -> Path:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for cfile in cfiles:
        for inc in cfile.includes:
            if inc.endswith(".h"):
                continue
            for other in by_base.get(inc, []):
                parent[find(other)] = find(cfile.path)
    ids: dict[Path, int] = {}
    roots: dict[Path, int] = {}
    for path in parent:
        ids[path] = roots.setdefault(find(path), len(roots))
    return ids


def resolve(name: str, caller: CFunc, by_name: dict[str, list[CFunc]], groups: dict[Path, int]) -> list[CFunc]:
    cands = by_name.get(name, [])
    local = [f for f in cands if f.static and (f.path.suffix.lower() == ".h" or groups.get(f.path) == groups.get(caller.path))]
    if local:
        return local
    return [f for f in cands if not f.static]


def asm_detectors(afiles: list[AsmFile], index: AsmIndex, routines: list[Routine]) -> list[Lead]:
    leads: list[Lead] = []
    spans: dict[str, Routine] = {r.name: r for r in routines}
    for afile in afiles:
        lines = afile.lines
        returns = set()
        defined = Counter(line.label for line in lines if line.label)
        for pos, line in enumerate(lines):
            if line.label and defined[line.label] == 1 and not line.depth and not line.in_macro:
                first = pos if line.mn else next_instr(lines, pos, cross_labels=True)
                if first is not None and lines[first].mn == "ret" and not lines[first].ops:
                    returns.add(line.label)
        for pos, line in enumerate(lines):
            if not line.mn or line.in_macro:
                continue
            here = [(afile.path, line.no, line.no)]
            raw = f"{line.mn} {','.join(line.raw_ops)}".strip()
            # push/pop around an untouched pair
            # AF is never a removable save: cp, bit, scf and ccf write F without a register
            if line.mn == "push" and line.ops and line.ops[0] in HALVES and line.ops[0] != "af":
                reg = line.ops[0]
                end = unclobbered_pop(lines, pos, reg)
                if end is not None:
                    cost = "4 bytes, 29 T" if reg in {"ix", "iy"} else "2 bytes, 21 T"
                    leads.append(Lead("asm-push-pop-unclobbered", afile.path, line.no, f"push {reg} .. pop {reg} (line {end})",
                                      f"nothing between writes {reg}: drop both, {cost}", [(afile.path, line.no, end)]))
            # jump whose target only returns
            target = branch_symbol(line)
            if line.mn in {"jr", "jp"} and target in returns and not in_vector(lines, pos):
                cond = line.ops[0] if len(line.ops) == 2 else ""
                saved = "1 byte" if line.mn == "jr" else "2 bytes"
                leads.append(Lead("asm-jump-to-ret", afile.path, line.no, raw,
                                  f"`{target}` only returns: `ret{' ' + cond if cond else ''}` saves {saved}", here))
    for routine in routines:
        leads.extend(routine_leads(routine, index, spans))
    return leads


def in_vector(lines: list[AsmLine], pos: int) -> bool:
    """An unconditional jump next to another one is a jump-table entry with a fixed size."""
    if not is_uncond_exit(lines[pos]) or lines[pos].mn == "ret":
        return False
    after = next_instr(lines, pos, cross_labels=True)
    before = next((i for i in range(pos - 1, -1, -1) if lines[i].mn), None)
    return any(i is not None and lines[i].mn in {"jp", "jr"} and is_uncond_exit(lines[i]) for i in (after, before))


def unclobbered_pop(lines: list[AsmLine], pos: int, reg: str) -> int | None:
    depth, writes, count = 0, set(), 0
    for idx in range(pos + 1, len(lines)):
        line = lines[idx]
        if line.label or line.directive or line.in_macro:
            return None
        if not line.mn:
            continue
        count += 1
        if count > 40:
            return None
        if line.mn == "pop":
            if depth == 0:
                return line.no if line.ops == [reg] and not (expand(writes) & HALVES[reg]) else None
            depth -= 1
            writes |= {line.ops[0]} if line.ops else set()
            continue
        if line.mn == "push":
            if any("sp" in op for op in line.ops):
                return None
            depth += 1
            continue
        effect = asm_writes(line.mn, line.ops)
        if effect is None:
            return None
        writes |= effect
    return None


def reads_on_entry(lines: list[AsmLine], reg: str) -> bool:
    """The routine reads reg before writing it or leaving straight-line code."""
    pair = overlapping(reg)
    for line in lines:
        if not line.mn:
            if line.directive:
                return False
            continue
        reads = asm_reads(line.mn, line.ops)
        writes = asm_writes(line.mn, line.ops)
        if reads is None or writes is None:
            return False
        if reads & pair:
            return True
        if expand(writes) & pair:
            return False
    return False


def routine_leads(routine: Routine, index: AsmIndex, spans: dict[str, Routine]) -> list[Lead]:
    leads: list[Lead] = []
    name = routine.name
    lines = routine.lines
    entry = name in index.calls or name in index.public
    if entry and not index.data.get(name) and not routine.fallthrough:
        first = 0 if lines[0].mn else next_instr(lines, 0)
        if first is not None:
            head = lines[first]
            target = branch_symbol(head)
            after = next_instr(lines, first, cross_labels=True)
            vector = after is not None and lines[after].mn in {"jp", "jr"} and len(lines[after].ops) == 1
            if head.mn in {"jp", "jr"} and len(head.ops) == 1 and target and target != name and not vector:
                leads.append(Lead("asm-forwarder", routine.path, head.no, f"{name}: {head.mn} {target}",
                                  f"alias `{name}` to `{target}` (z88dk `defc`, sjasmplus `EQU`): 0 bytes", [(routine.path, routine.start, head.no)]))
            elif head.mn == "call" and len(head.ops) == 1 and target and target != name:
                ret = next_instr(lines, first)
                if ret is not None and lines[ret].mn == "ret" and not lines[ret].ops:
                    leads.append(Lead("asm-forwarder", routine.path, head.no, f"{name}: call {target} / ret",
                                      f"callers can call {target}; `jp {target}` alone saves 1 byte, 17 T",
                                      [(routine.path, routine.start, lines[ret].no)]))
    # constant register argument: every entry path is a visible call or jump
    if name in index.public or index.data.get(name) or routine.fallthrough:
        return leads
    sites = [s for s in index.calls.get(name, []) + index.jumps.get(name, []) + index.relative.get(name, [])
             if not (s[0].path == routine.path and routine.start <= s[0].lines[s[1]].no <= routine.end)]
    if len(sites) < 2:
        return leads
    loads: list[dict[str, str]] = []
    for afile, pos in sites:
        found: dict[str, str] = {}
        touched: set[str] = set()
        idx, steps = pos, 0
        while steps < 4:
            prev = prev_instr(afile.lines, idx)
            if prev is None:
                break
            line = afile.lines[prev]
            effect = asm_writes(line.mn, line.ops)
            reads = asm_reads(line.mn, line.ops)
            if effect is None or reads is None:
                break
            if line.mn == "ld" and len(line.ops) == 2 and reg_of(line.ops[0]) and line.ops[0] not in {"sp", "i", "r"} and is_immediate(line.ops[1]):
                reg = line.ops[0]
                # a load the caller itself reads or overwrites before the call is not an argument
                if not overlapping(reg) & touched and reg not in found:
                    found[reg] = line.raw_ops[1].strip()
            touched |= expand(effect | reads)
            idx, steps = prev, steps + 1
        loads.append(found)
    for reg in sorted(loads[0]):
        values = {load.get(reg) for load in loads}
        if len(values) == 1 and None not in values and reads_on_entry(lines, reg):
            value = values.pop()
            size = 4 if reg in {"ix", "iy"} else 3 if reg in REG16 or reg not in {"a", "b", "c", "d", "e", "h", "l"} else 2
            leads.append(Lead("asm-constant-register-arg", routine.path, routine.start, f"{name}({reg})",
                              f"all {len(sites)} entry sites load {reg}={value}: load once inside, about {size * (len(sites) - 1)} bytes",
                              [(routine.path, routine.start, routine.start)] + [(a.path, a.lines[p].no, a.lines[p].no) for a, p in sites],
                              symbol=name))
    return leads


# -------------------------------------------------------------------- clones

def norm_c(tokens: list[tuple[str, int]]) -> list[str]:
    out = []
    for tok, _ in tokens:
        kind = tok_kind(tok)
        out.append("I" if kind == "id" and tok not in C_KEYWORDS else "N" if kind in {"num", "chr"} else "S" if kind == "str" else tok)
    return out


def norm_asm(line: AsmLine) -> str:
    ops = []
    for op in line.ops:
        op = re.sub(r"(?<![\w$#%])(\$[0-9a-f]+|#[0-9a-f]+|0x[0-9a-f]+|[0-9][0-9a-f]*h|%[01]+|\d+)\b", "N", op)
        op = ASM_IDENT_RE.sub(lambda m: m.group(1) if m.group(1) in REG8 | REG16 | CONDITIONS else "I", op)
        ops.append(op)
    return f"{line.mn} {','.join(ops)}"


def fingerprints(seq: list[str], k: int, w: int = 4) -> set[int]:
    if len(seq) < k:
        return set()
    hashes = [zlib.crc32("\x1f".join(seq[i:i + k]).encode()) for i in range(len(seq) - k + 1)]
    return {min(hashes[i:i + w]) for i in range(max(1, len(hashes) - w + 1))}


def clone_families(units: list[tuple[str, Path, list[str], list[int]]], key: str, k: int, min_block: int, measure: str, base: Path) -> list[Lead]:
    parent = list(range(len(units)))

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    best: dict[int, tuple[int, int, int]] = {}
    # identical units first: a large family would push every fingerprint past the frequency cut
    exact: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for uid, (_, _, seq, _) in enumerate(units):
        if len(seq) >= min_block:
            exact[tuple(seq)].append(uid)
    twins: set[int] = set()
    for members in exact.values():
        if len(members) < 2:
            continue
        for uid in members:
            parent[find(uid)] = find(members[0])
            best[uid] = (units[uid][3][0], units[uid][3][-1], len(units[uid][2]))
        twins.update(members[1:])
    prints = [fingerprints(seq, k) if uid not in twins else set() for uid, (_, _, seq, _) in enumerate(units)]
    # match on k-gram ids, not raw tokens: a rich alphabet keeps find_longest_match near linear
    gram_ids: dict[tuple[str, ...], int] = {}
    grams = [[gram_ids.setdefault(tuple(seq[i:i + k]), len(gram_ids)) for i in range(len(seq) - k + 1)]
             for _, _, seq, _ in units]
    index: dict[int, list[int]] = defaultdict(list)
    for uid, fps in enumerate(prints):
        for fp in fps:
            index[fp].append(uid)
    pair_counts: Counter[tuple[int, int]] = Counter()
    for members in index.values():
        if len(members) > 20:
            continue
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                pair_counts[(a, b)] += 1
    partial: list[tuple[dict[int, tuple[int, int, int]], str]] = []
    for (a, b), shared in pair_counts.most_common(4000):
        if shared < 2:
            break
        seq_a, seq_b = units[a][2], units[b][2]
        match = difflib.SequenceMatcher(None, grams[a], grams[b], autojunk=False).find_longest_match(0, len(grams[a]), 0, len(grams[b]))
        size = match.size + k - 1 if match.size else 0
        if size < min_block:
            continue
        spans = {}
        for uid, start in ((a, match.a), (b, match.b)):
            lines = units[uid][3]
            spans[uid] = (lines[start], lines[start + size - 1], size)
        small, big = sorted((len(seq_a), len(seq_b)))
        if size >= 0.6 * big:
            parent[find(a)] = find(b)
            for uid, span in spans.items():
                if uid not in best or best[uid][2] < size:
                    best[uid] = span
        elif size >= 0.8 * small:
            partial.append((spans, "one unit repeated inside another"))
        elif size >= 2 * min_block:
            partial.append((spans, "shared block inside larger units"))
    families: dict[int, list[int]] = defaultdict(list)
    for uid in best:
        families[find(uid)].append(uid)
    groups = [(members, best, "whole-unit clones") for members in families.values()]
    merged: list[tuple[dict[int, tuple[int, int, int]], str]] = []
    for spans, shape in partial:
        for group, _ in merged:
            if any(uid in group and group[uid][0] <= end and start <= group[uid][1] for uid, (start, end, _) in spans.items()):
                for uid, span in spans.items():
                    if uid not in group or group[uid][2] < span[2]:
                        group[uid] = span
                break
        else:
            merged.append((dict(spans), shape))
    groups += [(list(spans), spans, shape) for spans, shape in merged]
    leads = []
    for members, best, shape in groups:
        members.sort(key=lambda u: (str(units[u][1]), best[u][0]))
        sizes = sorted(best[u][2] for u in members)
        size = f"{sizes[0]}-{sizes[-1]}" if sizes[0] != sizes[-1] else str(sizes[0])
        dirs = sorted({rel_path(units[u][1].parent, base) for u in members})
        first = members[0]
        where = "spans directories: " + ", ".join(dirs) if len(dirs) > 1 else "same directory"
        lead = Lead(key, units[first][1], best[first][0], f"{len(members)} members, block {size} {measure}",
                    f"{shape}; {where}",
                    [(units[u][1], best[u][0], best[u][1]) for u in members])
        lead.members = [f"{units[u][1]}\x00{best[u][0]}-{best[u][1]} {units[u][0]}" for u in members]
        leads.append(lead)
    leads.sort(key=lambda lead: -len(lead.members) * int(lead.text.split("block ")[1].split()[0].split("-")[0]))
    return leads


# ------------------------------------------------------------------ comments

def words_of(text: str) -> list[str]:
    parts = []
    for word in re.findall(r"[A-Za-z0-9_$#]+", text):
        for piece in re.split(r"_|(?<=[a-z])(?=[A-Z])", word):
            if piece:
                parts.append(piece.lower())
    return parts


def number_forms(token: str) -> set[str]:
    raw = token.lower().lstrip("#")
    try:
        if raw.startswith("$"):
            value = int(raw[1:], 16)
        elif raw.startswith("0x"):
            value = int(raw, 16)
        elif raw.endswith("h") and re.fullmatch(r"[0-9][0-9a-f]*h", raw):
            value = int(raw[:-1], 16)
        else:
            value = int(raw)
    except ValueError:
        return set()
    return {str(value), f"{value:x}", f"{value:02x}"}


def narration(comment: str, vocab: set[str], verbs: set[str]) -> bool:
    """The comment only restates the operation: mostly covered, and it names the verb."""
    words = [w for w in words_of(comment) if w not in STOP_WORDS]
    if not 2 <= len(words) <= 8 or not any(w in verbs for w in words):
        return False
    covered = sum(1 for w in words if w in vocab or w.lstrip("$#") in vocab)
    return covered / len(words) >= 0.8


def asm_verbs(line: AsmLine) -> set[str]:
    return set(ASM_WORDS.get(line.mn or "", "").split()) | {line.mn or ""}


def c_verbs(code: str) -> set[str]:
    return {w for tok in TOKEN_RE.findall(code) if tok in C_WORDS for w in C_WORDS[tok].split()}


def asm_vocab(line: AsmLine) -> set[str]:
    vocab = set(ASM_WORDS.get(line.mn or "", "").split()) | REGISTER_WORDS | {line.mn or ""}
    for op in line.raw_ops:
        vocab |= set(words_of(op))
        for tok in re.findall(r"[$#]?[0-9A-Fa-fx]+h?", op):
            vocab |= number_forms(tok)
    return vocab


def c_vocab(code: str) -> set[str]:
    vocab = set(words_of(code))
    for tok in TOKEN_RE.findall(code):
        if tok in C_WORDS:
            vocab |= set(C_WORDS[tok].split())
        if tok_kind(tok) == "num":
            vocab |= number_forms(tok.rstrip("uUlL"))
    if re.search(r"\b0\b", code):
        vocab |= {"zero", "cero", "clear", "reset"}
    return vocab


def asm_commented_code(text: str) -> bool:
    parts = text.strip().split(None, 1)
    if not parts or parts[0].lower() not in MNEMONICS:
        return False
    if len(parts) == 1:
        return parts[0].lower() in {"ret", "exx", "ldir", "lddr", "ei", "di", "halt", "nop", "neg", "cpl", "daa", "scf", "ccf", "rla", "rra", "rlca", "rrca"}
    ops = [op.strip() for op in split_operands(parts[1])]
    if len(ops) > 2 or not all(ASM_OPERAND_RE.match(op) for op in ops):
        return False
    if len(ops) == 1:
        op = ops[0].lower()
        return bool(reg_of(op) or op.startswith("(") or NUMBER_RE.match(op) or "_" in op or any(ch.isdigit() for ch in op) or ops[0].isupper())
    return True


def comment_leads(cfiles: list[CFile], afiles: list[AsmFile]) -> tuple[list[Lead], int]:
    leads: list[Lead] = []
    total = 0
    for cfile in cfiles:
        code_lines = sorted(cfile.code_by_line)
        for lineno, text, trailing, multi in cfile.comments:
            body = text.strip().lstrip("*").strip()
            if not body:
                continue
            total += 1
            if HISTORY_RE.search(body):
                leads.append(Lead("comment-history", cfile.path, lineno, snippet(body), "history in a comment"))
            if not trailing and C_CODE_COMMENT_RE.match(body):
                continue  # commented-out code is not narration
            if multi:
                continue
            if trailing:
                code = cfile.code_by_line.get(lineno, "")
            else:
                later = [ln for ln in code_lines if ln > lineno]
                code = cfile.code_by_line.get(later[0], "") if later and later[0] == lineno + 1 else ""
            if code and narration(body, c_vocab(code), c_verbs(code)):
                leads.append(Lead("comment-narration", cfile.path, lineno, snippet(body), f"restates `{snippet(code)[:40]}`"))
    for afile in afiles:
        lines = afile.lines
        for pos, line in enumerate(lines):
            if not line.comment:
                continue
            total += 1
            body = line.comment.lstrip(";").strip()
            if HISTORY_RE.search(body):
                leads.append(Lead("comment-history", afile.path, line.no, snippet(body), "history in a comment"))
            if not line.mn and not line.label and not line.directive and asm_commented_code(body):
                continue
            target = line if line.mn else None
            if target is None and not line.label and not line.directive and pos + 1 < len(lines):
                nxt = lines[pos + 1]
                target = nxt if nxt.mn and not nxt.label and not nxt.comment else None
            if target is not None and narration(body, asm_vocab(target), asm_verbs(target)):
                leads.append(Lead("comment-narration", afile.path, line.no, snippet(body), f"restates `{target.mn} {','.join(target.raw_ops)}`"))
    return leads, total


# ------------------------------------------------------------------ map cost

def map_rows(path: Path) -> dict[str, list[tuple[int, str, str]]]:
    """Code symbols per section, sorted by address; banks may reuse an address in another section."""
    rows: dict[tuple[str, int], tuple[int, str, str]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = MAP_RE.match(line)
        if not m or not m.group(4).startswith(CODE_SECTION_HINTS):
            continue
        name, addr, module, section = m.group(1), int(m.group(2), 16), m.group(3), m.group(4)
        key = (section, addr)
        if key not in rows or rows[key][1].startswith(LOCAL_PREFIXES):
            rows[key] = (addr, name, module)
    sections: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
    for (section, _), row in sorted(rows.items()):
        sections[section].append(row)
    return sections


MAP_TAIL_RE = re.compile(r"^__(\S+)_tail\s+= \$([0-9A-Fa-f]+)", re.MULTILINE)


def map_costs(map_paths: list[Path], funcs: list[CFunc], base: Path, variants: set[tuple[Path, str]],
              cfiles: list[CFile]) -> tuple[list[Lead], list[str]]:
    by_path = {cfile.path: cfile for cfile in cfiles}
    by_base: dict[str, list[Path]] = defaultdict(list)
    for cfile in cfiles:
        by_base[cfile.path.name].append(cfile.path)
    notes: list[str] = []
    leads: dict[tuple[Path, str], Lead] = {}
    # the map module names the object file: gui_c <- gui.c
    by_symbol: dict[tuple[str, str], CFunc | None] = {}
    for func in funcs:
        key = ("_" + func.name, f"{func.path.stem}_c")
        # two files with one basename share a module name: the map cannot tell them apart
        by_symbol[key] = func if key not in by_symbol or by_symbol[key] is func else None
    for map_path in map_paths:
        if not map_path.is_file():
            notes.append(f"map: missing {map_path}")
            continue
        sizes: dict[tuple[str, str], int] = {}
        sections = map_rows(map_path)
        tails = {name: int(addr, 16) for name, addr in MAP_TAIL_RE.findall(map_path.read_text(encoding="utf-8", errors="replace"))}
        for section, rows in sections.items():
            owner = None
            for idx, (addr, name, module) in enumerate(rows):
                end = rows[idx + 1][0] if idx + 1 < len(rows) else tails.get(section)
                if end is None:
                    break
                size = max(0, end - addr)
                if name.startswith(("__str_", "___str_")):
                    owner = None  # string data is not the function's code
                    continue
                if name.startswith(LOCAL_PREFIXES) and owner and owner[1] == module:
                    sizes[owner] += size
                    continue
                owner = (name, module)
                sizes[owner] = size
        matched = [(by_symbol[key], size) for key, size in sizes.items() if by_symbol.get(key)]
        if not matched:
            notes.append(f"map: no C function matched in {rel_path(map_path, base)}")
            continue
        sources = {func.path for func, _ in matched}
        todo = list(sources)
        while todo:  # include closure by basename; compiler flags are invisible here
            path = todo.pop()
            for inc in by_path[path].includes if path in by_path else ():
                for dep in by_base.get(inc, []):
                    if dep not in sources:
                        sources.add(dep)
                        todo.append(dep)
        newest = max(sources, key=lambda path: path.stat().st_mtime)
        stale = map_path.stat().st_mtime < newest.stat().st_mtime
        state = f"STALE (older than {rel_path(newest, base)}): NEEDS BUILD" if stale else "fresh"
        notes.append(f"map: {state} {rel_path(map_path, base)}")
        ratios = []
        for func, size in matched:
            if func.has_asm or "__naked" in func.attrs or (func.path, func.name) in variants or func.variant:
                continue
            tokens = sum(1 for t, _ in func.body if t not in {";", "{", "}", "(", ")", ","})
            ratios.append((size / max(1, tokens), size, tokens, func))
        if not ratios:
            continue
        median = statistics.median(r[0] for r in ratios)
        for ratio, size, tokens, func in ratios:
            key = (func.path, func.name)
            if size < 48 or ratio < 2 * median or (key in leads and leads[key].line_ratio >= ratio):
                continue
            lead = Lead("c-codegen-outlier", func.path, func.line, func.name,
                        f"bytes={size} tokens={tokens} bytes/token={ratio:.1f} (map median {median:.1f}, {rel_path(map_path, base)})"
                        + ("; NEEDS BUILD" if stale else ""), [(func.path, func.line, func.end)])
            lead.line_ratio = ratio
            leads[key] = lead
    ordered = sorted(leads.values(), key=lambda lead: -lead.line_ratio)
    return ordered, notes


# ------------------------------------------------------------- git evidence

def git(root: Path, *args: str) -> str | None:
    try:
        proc = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=False)
    except OSError:
        return None
    return proc.stdout if proc.returncode == 0 else None


WHOLE_FILE: set[int] = set()  # identity sentinel: an untracked file counts as changed everywhere


def changed_lines(root: Path, rev: str) -> tuple[dict[Path, set[int]], set[str]] | None:
    top = git(root, "rev-parse", "--show-toplevel")
    diff = git(root, "diff", "-U0", "--no-color", "--no-ext-diff", "--no-prefix", rev, "--")
    if top is None or diff is None:
        return None
    top_path = Path(top.strip()).resolve()
    changed: dict[Path, set[int]] = defaultdict(set)
    deleted: set[str] = set()
    current: Path | None = None
    suffix = ""
    for line in diff.splitlines():
        if line.startswith("-") and not line.startswith("---"):
            # identifiers in deleted code, not in deleted comments
            code = strip_c_comments(line[1:], False)[0] if suffix in CRAFT_C_EXTS else split_comment(line[1:])[0]
            deleted.update(re.findall(r"[A-Za-z_]\w*", code))
        elif line.startswith("--- "):
            suffix = Path(line[4:]).suffix.lower()
        elif line.startswith("+++ "):
            name = line[4:]
            current = None if name == "/dev/null" else (top_path / name).resolve()
        elif line.startswith("@@") and current is not None:
            match = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if match:
                start, count = int(match.group(1)), int(match.group(2) or 1)
                changed[current].update(range(start, start + count) if count else {max(start, 1)})
    untracked = git(root, "ls-files", "--others", "--exclude-standard", "--full-name") or ""
    for name in untracked.splitlines():
        changed[(top_path / name).resolve()] = WHOLE_FILE
    return changed, deleted


def churn(root: Path, count: int) -> dict[Path, tuple[int, int]]:
    top = git(root, "rev-parse", "--show-toplevel")
    log = git(root, "log", f"-n{count}", "--no-merges", "--numstat", "--format=\x1e%s")
    if top is None or log is None:
        return {}
    top_path = Path(top.strip()).resolve()
    stats: dict[Path, list[int]] = defaultdict(lambda: [0, 0])
    for chunk in log.split("\x1e")[1:]:
        subject, _, rest = chunk.partition("\n")
        fix = bool(re.search(r"\b(fix|fixes|fixed|bug|hotfix|revert|arregl|corrig)", subject, re.IGNORECASE))
        for row in rest.splitlines():
            parts = row.split("\t")
            if len(parts) == 3:
                path = (top_path / parts[2]).resolve()
                stats[path][0] += 1
                stats[path][1] += int(fix)
    return {path: (v[0], v[1]) for path, v in stats.items()}


# -------------------------------------------------------------------- driver

def in_targets(path: Path, targets: list[Path]) -> bool:
    return any(path == t or t in path.parents for t in targets)


def keep_lead(lead: Lead, targets: list[Path], changed: dict[Path, set[int]] | None, deleted: set[str]) -> bool:
    spans = lead.spans or [(lead.path, lead.line, lead.line)]
    if not any(in_targets(path, targets) for path, _, _ in spans):
        return False
    if changed is None:
        return True
    # a change that deletes the last varying call or reference creates the lead without touching its span
    if lead.symbol and lead.symbol in deleted:
        return True
    return any(changed.get(path) is WHOLE_FILE or any(start <= ln <= end for ln in changed.get(path, ())) for path, start, end in spans)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("targets", nargs="*", default=["."], help="files or directories to report on")
    parser.add_argument("--context", help="root for cross-references (default: git top level, else the target)")
    parser.add_argument("--map", action="append", default=[], help="z88dk .map for per-function bytes (repeatable)")
    parser.add_argument("--changed-from", metavar="REV", help="report only leads touching lines changed since REV")
    parser.add_argument("--churn", type=int, default=0, metavar="N", help="weight hotspots by the last N commits")
    parser.add_argument("--limit", type=int, default=30, help="rows per section")
    args = parser.parse_args()

    targets = [Path(t).resolve() for t in args.targets]
    first = targets[0] if targets[0].is_dir() else targets[0].parent
    if args.context:
        context = Path(args.context).resolve()
    else:
        top = git(first, "rev-parse", "--show-toplevel")
        context = Path(top.strip()).resolve() if top else first
    scope = resolve_target_scope(context, CRAFT_C_EXTS | CRAFT_ASM_EXTS)
    files = [p for p in scope.files if source_kind(p, scope.base) == "source" and p.suffix.lower() in CRAFT_C_EXTS | CRAFT_ASM_EXTS]
    for target in targets:
        if target.is_file() and target not in files:
            files.append(target)

    cfiles: list[CFile] = []
    afiles: list[AsmFile] = []
    for path in sorted(files):
        lines, skipped = read_text_lines(path)
        if skipped:
            continue
        if path.suffix.lower() in CRAFT_C_EXTS:
            cfile = CFile(path, lines)
            cfiles.append(cfile)
            if not cfile.asm_lines:
                continue
            lines = cfile.inline_asm
        afiles.append(AsmFile(path, lines))

    funcs: list[CFunc] = []
    proto_attrs: dict[str, set[str]] = defaultdict(set)
    global_refs: Counter[str] = Counter()
    macros: dict[str, set[str]] = {}
    for cfile in cfiles:
        macros.update(cfile.macro_attrs)
    for cfile in cfiles:
        found, protos, refs = parse_c(cfile, macros)
        funcs.extend(found)
        for name, attrs in protos.items():
            proto_attrs[name] |= attrs
        global_refs.update(refs)
        # second pass over the last #else/#elif branch: functions that exist only there
        covered: set[int] = set()
        if any(BRANCH_RE.match(line.strip()) for line in cfile.lines):
            alt = CFile(cfile.path, cfile.lines, alternate=True)
            cfile.includes |= alt.includes
            alt_found, alt_protos, _ = parse_c(alt, macros)
            names = {func.name for func in found}
            for func in alt_found:
                # a body shared with a parsed function is only another header for it
                shared = any(f.line <= func.end and func.line <= f.end for f in found)
                if func.line in cfile.skipped_ids and func.name not in names and not shared:
                    func.variant = True
                    funcs.append(func)
                    covered.update(ln for ln in range(func.line, func.end + 1) if ln not in alt.skipped_ids)
            for name, attrs in alt_protos.items():
                proto_attrs[name] |= attrs
        # anything else on unparsed lines (tables, defines, variant bodies) pins its symbols
        cfile.opaque.extend(i for ln, ids in cfile.skipped_ids.items() if ln not in covered for i in ids)

    index = index_asm(afiles)
    asm_refs: Counter[str] = Counter()
    for bucket in (index.calls, index.jumps, index.relative):
        for name, sites in bucket.items():
            asm_refs[name.lstrip("_")] += len(sites)
    for name, count in index.data.items():
        asm_refs[name.lstrip("_")] += count
    for name in index.public:
        asm_refs[name.lstrip("_")] += 1
    routines = [r for afile in afiles if afile.path.suffix.lower() not in CRAFT_C_EXTS for r in routines_of(afile, index)]
    # inline ASM: one routine per C function; C callers pass arguments unseen
    asm_by_path = {afile.path: afile for afile in afiles}
    for func in funcs:
        afile = asm_by_path.get(func.path) if func.has_asm else None
        if afile is None or func.path.suffix.lower() not in CRAFT_C_EXTS:
            continue
        body = [line for line in afile.lines[func.line - 1:func.end] if line.mn or line.label]
        if body:
            index.public.add("_" + func.name)
            routines.append(Routine("_" + func.name, func.path, body[0].no, body[-1].no, afile.lines[func.line - 1:func.end]))

    generated = {path for path in files if is_declared_generated_source(path)}

    def own(path: Path) -> bool:
        return in_targets(path, targets) and path not in generated

    leads = c_detectors(cfiles, funcs, asm_refs, proto_attrs, global_refs)
    leads += asm_detectors([a for a in afiles if own(a.path)], index, [r for r in routines if own(r.path)])
    c_units = [(f.name, f.path, norm_c(f.body), [ln for _, ln in f.body]) for f in funcs if own(f.path)]
    leads += clone_families(c_units, "c-clone-family", 10, 40, "tokens", context)
    asm_units = []
    for routine in routines:
        if not own(routine.path):
            continue
        instrs = [line for line in routine.lines if line.mn]
        asm_units.append((routine.name, routine.path, [norm_asm(line) for line in instrs], [line.no for line in instrs]))
    leads += clone_families(asm_units, "asm-clone-family", 4, 8, "instructions", context)
    comments, comment_total = comment_leads(cfiles, afiles)
    leads += comments
    variants = {(cfile.path, name) for cfile in cfiles for name in cfile.inactive}
    cost_leads, map_notes = map_costs([Path(m).resolve() for m in args.map], funcs, context, variants, cfiles)
    leads += cost_leads

    changed, deleted = None, set()
    if args.changed_from:
        diff = changed_lines(context, args.changed_from)
        if diff is None:
            print(f"error: cannot diff against {args.changed_from} in {context}", file=sys.stderr)
            return 2
        changed, deleted = diff
    leads = [lead for lead in leads if lead.path not in generated and keep_lead(lead, targets, changed, deleted)]

    base = context
    print(f"context: {context}")
    print("targets: " + ", ".join(rel_path(t, base) or "." for t in targets))
    print(f"files: c={len(cfiles)} asm={len(afiles)}")
    print(f"mode: changed-from {args.changed_from} ({sum(len(v) for v in changed.values() if len(v) < 1_000_000)} changed lines, {len(changed)} files)" if changed is not None else "mode: full")
    for note in map_notes:
        print(note)

    by_key: dict[str, list[Lead]] = defaultdict(list)
    for lead in leads:
        by_key[lead.key].append(lead)
    for key, (_, _, check) in SECTIONS.items():
        items = sorted(by_key.get(key, []), key=lambda lead: (str(lead.path), lead.line)) if "clone" not in key and key != "c-codegen-outlier" else by_key.get(key, [])
        print(f"\n[{key}] count={len(items)}")
        for lead in items[:args.limit]:
            print(f"  {rel_path(lead.path, base)}:{lead.line}: {lead.text}  # {lead.detail}")
            for member in lead.members:
                path, rest = member.split("\x00")
                print(f"    - {rel_path(Path(path), base)}:{rest}")
        if len(items) > args.limit:
            print(f"  ... {len(items) - args.limit} more")
        if items:
            print(f"  check: {check}")

    code_lines: Counter[Path] = Counter()
    for cfile in cfiles:
        code_lines[cfile.path] += cfile.code_lines
    for afile in afiles:
        code_lines[afile.path] += afile.instr_lines
    history = churn(context, args.churn) if args.churn else {}
    weights: Counter[Path] = Counter()
    counts: Counter[Path] = Counter()
    for lead in leads:
        for path in ({p for p, _, _ in lead.spans} if "clone" in lead.key else {lead.path}):
            if in_targets(path, targets):
                weights[path] += SECTIONS[lead.key][1]
                counts[path] += 1
    rows = []
    for path, weight in weights.items():
        commits, fixes = history.get(path, (0, 0))
        score = weight * (1 + math.log1p(commits) + fixes) if args.churn else weight
        rows.append((score, path, weight, commits, fixes))
    rows.sort(key=lambda r: (-r[0], str(r[1])))
    print(f"\n[hotspots] count={len(rows)}")
    for score, path, weight, commits, fixes in rows[:15]:
        lines = max(1, code_lines.get(path, 1))
        extra = f" commits={commits} fixes={fixes}" if args.churn else ""
        print(f"  {rel_path(path, base)}: score={score:.0f} leads={counts[path]} weight={weight} code_lines={lines} weight_per_100={100 * weight / lines:.1f}{extra}")

    reported = [f for f in funcs if in_targets(f.path, targets)]
    target_routines = [r for r in routines if in_targets(r.path, targets)]
    c_lines = sum(cfile.code_lines for cfile in cfiles if in_targets(cfile.path, targets))
    asm_lines = sum(afile.instr_lines for afile in afiles if in_targets(afile.path, targets))
    groups: Counter[str] = Counter(SECTIONS[lead.key][0] for lead in leads)
    idiom = groups["idiom"]
    print("\n[summary] count=1")
    print(f"  c_functions: {len(reported)} (static {sum(1 for f in reported if f.static)})")
    print(f"  asm_routines: {len(target_routines)}")
    print(f"  code_lines: c={c_lines} asm_instructions={asm_lines}")
    if changed is not None:
        def hit(path: Path, line: int) -> bool:
            return changed.get(path) is WHOLE_FILE or line in changed.get(path, ())
        c_changed = sum(hit(f.path, ln) for f in cfiles if in_targets(f.path, targets) for ln in f.code_by_line)
        a_changed = sum(hit(a.path, line.no) for a in afiles if in_targets(a.path, targets) for line in a.lines if line.mn)
        print(f"  changed_code_lines: c={c_changed} asm_instructions={a_changed}")
    print(f"  comments_seen: {comment_total}")
    print("  leads: " + ", ".join(f"{g}={groups[g]}" for g in ("structural", "codegen", "idiom", "comment")) + f", total={len(leads)}")
    print(f"  leads_per_kloc: {1000 * len(leads) / max(1, c_lines + asm_lines):.1f}")
    print(f"  asm_idiom_leads_per_1000_instructions: {1000 * idiom / max(1, asm_lines):.1f}")
    print("\nnote: candidates only; every lead needs the expert alternative, a measured delta and a preservation argument before promotion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
