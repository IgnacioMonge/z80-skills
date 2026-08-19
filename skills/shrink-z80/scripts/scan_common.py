#!/usr/bin/env python3
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

SCAN_DIRS = (
    "src", "asm", "include", "overlay", "build", "obj", "out", "gen", "generated",
    "dist", "tmp", "tools", "scripts",
)
HOST_ONLY_DIRS = {"tools", "scripts", "tests", "test", "host", "client", "pc"}
EXCLUDE_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules", "target",
    "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox", ".cache",
    ".worktrees", ".codex-safety", ".aider.tags.cache.v4", "third_party", "vendor",
}
SOURCE_EXTS = {".c", ".h", ".i", ".asm", ".s", ".inc", ".opt", ".rul"}
C_EXTS = {".c", ".h", ".i"}
ASM_EXTS = {".asm", ".s", ".inc", ".opt"}
LISTING_EXTS = {".lst", ".lis"}
TEXT_BUILD_EXTS = {".map", ".sym", ".rel", ".ihx", ".lk", ".noi", ".mem"}
BINARY_ARTIFACT_EXTS = {".bin", ".tap", ".sna", ".tzx", ".scr", ".ovl"}
BUILD_EXTS = TEXT_BUILD_EXTS | BINARY_ARTIFACT_EXTS
TEXT_EXTS = SOURCE_EXTS | LISTING_EXTS | TEXT_BUILD_EXTS | {
    ".mk", ".txt", ".ps1", ".sh", ".bat", ".cmd", ".json", ".yaml",
    ".yml", ".cmake", ".cfg", ".conf", ".ini", ".toml", ".def", ".z80",
    ".a80", ".mac", ".bas",
}
GENERATED_DIRS = {"build", "obj", "out", "gen", "generated", "tmp"}
DIST_DIRS = {"dist", "release", "releases"}
TEXT_FILE_SIZE_LIMIT = 2_000_000

TOP_LEVEL_FILES = {
    "Makefile", "makefile", "GNUmakefile", "CMakeLists.txt", "build.sh", "build.ps1",
    "build.bat", "build.cmd", "build.mk", "zproject.lst", "project.lk",
}
ASM_MNEMONICS = {"adc", "add", "and", "bit", "call", "ccf", "cp", "cpd", "cpdr", "cpi", "cpir", "cpl", "daa", "dec", "di", "djnz", "ei", "ex", "exx", "halt", "im", "in", "inc", "ind", "indr", "ini", "inir", "jp", "jr", "ld", "ldd", "lddr", "ldi", "ldir", "neg", "nop", "or", "otdr", "otir", "out", "pop", "push", "res", "ret", "reti", "retn", "rl", "rla", "rlc", "rlca", "rld", "rr", "rra", "rrc", "rrca", "rrd", "rst", "sbc", "scf", "set", "sla", "sra", "srl", "sub", "xor"}
LABEL_RE = re.compile(r"^([A-Za-z_.$?@][\w.$?@]*):\s*(.*)$")
BARE_LABEL_RE = re.compile(r"^[A-Za-z_.$?@][\w.$?@]*$")
BRANCH_TARGET_RE = re.compile(r"\b(?:call|jp|jr)\s+(?:(?:z|nz|c|nc|m|p|pe|po)\s*,\s*)?([A-Za-z_.$?@][\w.$?@]*)", re.IGNORECASE)
CALL_TARGET_RE = re.compile(r"\bcall\s+(?:(?:z|nz|c|nc|m|p|pe|po)\s*,\s*)?([A-Za-z_.$?@][\w.$?@]*)", re.IGNORECASE)
UNCOND_CALL_TARGET_RE = re.compile(r"\bcall\s+(?!(?:z|nz|c|nc|m|p|pe|po)\s*,)([A-Za-z_.$?@][\w.$?@]*)", re.IGNORECASE)
ASM_COMMENT_RE = re.compile(r";.*$")
UNCOND_EXIT_RE = re.compile(
    r"^\s*(?:ret\s*$|jp\s+(?!(?:z|nz|c|nc|m|p|pe|po)\s*,)[^,;]+|jr\s+(?!(?:z|nz|c|nc)\s*,)[^,;]+)\b",
    re.IGNORECASE,
)
EXPLICIT_LABEL_RE = re.compile(r"^([A-Za-z_.$?@][\w.$?@]*):(?:\s*(.*))?$")
CONDITIONAL_CALL_RE = re.compile(
    r"\bcall\s+((?:z|nz|c|nc|m|p|pe|po)\s*,\s*)?"
    r"([A-Za-z_.$?@][\w.$?@]*)",
    re.IGNORECASE,
)
ADDRESS_TOKEN = (
    r"(?:\$[0-9A-Fa-f]+|#[0-9A-Fa-f]+|0x[0-9A-Fa-f]+|"
    r"[0-9A-Fa-f]+h|[0-9A-Fa-f]{4,})"
)
MAP_SYMBOL_RE = re.compile(rf"^(\S+)\s*=\s*({ADDRESS_TOKEN})\s*;")
SYM_ADDR_NAME_RE = re.compile(
    rf"^({ADDRESS_TOKEN})\s+([A-Za-z_.$?@][\w.$?@]*)\b"
)
SYM_NAME_ADDR_RE = re.compile(
    rf"^([A-Za-z_.$?@][\w.$?@]*)\s+(?:=\s*)?({ADDRESS_TOKEN})\b"
)
SYM_EQU_RE = re.compile(
    rf"^([A-Za-z_.$?@][\w.$?@]*):?\s+EQU\s+({ADDRESS_TOKEN})\b",
    re.IGNORECASE,
)


@dataclass
class Hit:
    path: Path
    line_no: int
    text: str
    note: str

@dataclass
class Scope:
    target: Path
    base: Path
    kind: str
    scan_roots: list[Path]
    files: list[Path]


def rel_path(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def strip_line_comment(line: str) -> str:
    return line.split(";", 1)[0].split("//", 1)[0].rstrip()


def add_hit(
    hits: dict[str, list[Hit]],
    key: str,
    path: Path,
    line_no: int,
    text: str,
    note: str,
) -> None:
    hits[key].append(Hit(path, line_no, text.strip(), note))


def print_pattern_hits(
    root: Path,
    hits: dict[str, list[Hit]],
    *,
    include_source_kind: bool = False,
    limit: int = 24,
) -> None:
    base = root.parent if root.is_file() else root
    shown_base = base if include_source_kind else root
    for key in sorted(hits):
        items = hits[key]
        print(f"\n[{key}] count={len(items)}")
        for hit in items[:limit]:
            prefix = f"[{source_kind(hit.path, base)}] " if include_source_kind else ""
            print(
                f"  {prefix}{rel_path(hit.path, shown_base)}:{hit.line_no}: {hit.text}"
            )
        print(f"  note: {items[0].note}")
        if len(items) > limit:
            print(f"  ... {len(items) - limit} more")


def explicit_label(line: str) -> tuple[str, str] | None:
    match = EXPLICIT_LABEL_RE.match(line.strip())
    return (match.group(1), match.group(2) or "") if match else None


def conditional_call(line: str) -> tuple[str, bool] | None:
    match = CONDITIONAL_CALL_RE.search(line)
    if not match:
        return None
    return match.group(2), bool(match.group(1))


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def is_host_only_path(path: Path, base: Path) -> bool:
    """Omit conventional host trees only when scanning their project parent."""
    try:
        parts = [part.lower() for part in path.resolve().relative_to(base.resolve()).parts]
    except ValueError:
        return False
    return bool(parts and parts[0] in HOST_ONLY_DIRS)


def source_kind(path: Path, base: Path) -> str:
    suffix = path.suffix.lower()
    base_name = base.name.lower()
    if suffix in LISTING_EXTS:
        return "listing"
    if base_name in DIST_DIRS:
        return "dist"
    if base_name in GENERATED_DIRS:
        return "generated_asm" if suffix in ASM_EXTS else "build_artifact"
    try:
        parts = [part.lower() for part in path.relative_to(base).parts]
    except ValueError:
        parts = [part.lower() for part in path.parts]
    top = parts[0] if parts else ""
    if top in DIST_DIRS:
        return "dist"
    if top in GENERATED_DIRS:
        return "generated_asm" if suffix in ASM_EXTS else "build_artifact"
    if suffix in BUILD_EXTS:
        return "build_artifact"
    if suffix in SOURCE_EXTS:
        return "source"
    return "unknown"


def split_label(code: str) -> tuple[str | None, str]:
    stripped = code.strip()
    match = LABEL_RE.match(stripped)
    if match:
        return match.group(1), match.group(2).strip()
    if code and not code[0].isspace() and BARE_LABEL_RE.match(stripped) and stripped.lower() not in ASM_MNEMONICS:
        return stripped, ""
    return None, code


def branch_targets(line: str) -> list[str]:
    return [match.group(1) for match in BRANCH_TARGET_RE.finditer(line)]


def call_targets(line: str) -> list[str]:
    return [match.group(1) for match in CALL_TARGET_RE.finditer(line)]


def unconditional_call_targets(line: str) -> list[str]:
    return [match.group(1) for match in UNCOND_CALL_TARGET_RE.finditer(line)]


def is_unconditional_exit(line: str) -> bool:
    return bool(UNCOND_EXIT_RE.search(line.strip()))


def strip_c_comments(line: str, in_block: bool) -> tuple[str, bool]:
    out: list[str] = []
    idx = 0
    quote: str | None = None
    escape = False
    while idx < len(line):
        ch = line[idx]
        nxt = line[idx + 1] if idx + 1 < len(line) else ""
        if in_block:
            if ch == "*" and nxt == "/":
                in_block = False
                idx += 2
            else:
                idx += 1
            continue
        if quote:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            idx += 1
            continue
        if ch in {'"', "'"}:
            quote = ch
            out.append(ch)
            idx += 1
            continue
        if ch == "/" and nxt == "/":
            break
        if ch == "/" and nxt == "*":
            in_block = True
            idx += 2
            continue
        out.append(ch)
        idx += 1
    return "".join(out), in_block


def active_c_lines(lines: list[str]) -> list[tuple[int, str]]:
    active_stack = [True]
    in_block = False
    out: list[tuple[int, str]] = []
    for lineno, raw in enumerate(lines, start=1):
        line, in_block = strip_c_comments(raw, in_block)
        stripped = line.strip().lower()
        parent_active = all(active_stack)
        if re.match(r"#\s*if\s+(?:0|false)\b", stripped):
            active_stack.append(False if parent_active else False)
            continue
        if re.match(r"#\s*if(?:def|ndef)?\b", stripped):
            active_stack.append(parent_active)
            continue
        if re.match(r"#\s*else\b", stripped):
            if len(active_stack) > 1:
                old = active_stack.pop()
                parent = all(active_stack)
                active_stack.append(parent and not old)
            continue
        if re.match(r"#\s*elif\b", stripped):
            if len(active_stack) > 1:
                active_stack[-1] = False
            continue
        if re.match(r"#\s*endif\b", stripped):
            if len(active_stack) > 1:
                active_stack.pop()
            continue
        if all(active_stack):
            out.append((lineno, line))
    return out


def active_source_lines(path: Path, lines: list[str]) -> list[tuple[int, str]]:
    suffix = path.suffix.lower()
    if suffix in C_EXTS:
        return active_c_lines(lines)
    if suffix in ASM_EXTS:
        return [(lineno, ASM_COMMENT_RE.sub("", line)) for lineno, line in enumerate(lines, start=1)]
    return [(lineno, line) for lineno, line in enumerate(lines, start=1)]


def read_text_lines(path: Path, max_bytes: int = TEXT_FILE_SIZE_LIMIT) -> tuple[list[str], bool]:
    try:
        if path.stat().st_size > max_bytes:
            return [], True
        return path.read_text(encoding="utf-8", errors="ignore").splitlines(), False
    except OSError:
        return [], True


def collect_pattern_hits(
    files: list[Path],
    base: Path,
    patterns: list[str],
    *,
    limit: int,
    excluded_exts: set[str] | None = None,
) -> list[str]:
    hits: list[str] = []
    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    excluded_exts = excluded_exts or set()
    for path in files:
        if path.suffix.lower() in excluded_exts:
            continue
        lines, skipped = read_text_lines(path)
        if skipped:
            continue
        for lineno, line in enumerate(lines, start=1):
            if len(line) > 300:
                continue
            if any(regex.search(line) for regex in compiled):
                hits.append(f"{rel_path(path, base)}:{lineno}: {line.strip()}")
                if len(hits) >= limit:
                    return hits
    return hits


def parse_address(
    value: str,
    default_hex: bool = False,
    sym_base: str = "auto",
) -> tuple[int, str]:
    raw = value.strip().lower()
    if raw.startswith(("$", "#")):
        return int(raw[1:], 16), "hex"
    if raw.startswith("0x"):
        return int(raw[2:], 16), "hex"
    if raw.endswith("h"):
        return int(raw[:-1], 16), "hex"
    if re.search(r"[a-f]", raw):
        return int(raw, 16), "hex"
    if default_hex:
        return int(raw, 16), "hex-default"
    if sym_base == "hex":
        return int(raw, 16), "hex-forced"
    if sym_base == "decimal":
        return int(raw, 10), "decimal-forced"
    if re.fullmatch(r"\d{4}", raw):
        return int(raw, 10), "ambiguous-plain-numeric"
    return int(raw, 10), "decimal"


def parse_symbol_line(
    line: str,
    sym_base: str = "auto",
) -> tuple[str, int, str, str] | None:
    line = line.strip()
    if not line or line.startswith((";", "#")):
        return None
    match = MAP_SYMBOL_RE.match(line)
    if match:
        addr, base = parse_address(match.group(2), default_hex=True)
        return match.group(1), addr, "map-equals", base
    match = SYM_EQU_RE.match(line)
    if match:
        addr, base = parse_address(match.group(2), sym_base=sym_base)
        return match.group(1), addr, "sym-equ", base
    match = SYM_ADDR_NAME_RE.match(line)
    if match:
        addr, base = parse_address(match.group(1), sym_base=sym_base)
        return match.group(2), addr, "sym-addr-name", base
    match = SYM_NAME_ADDR_RE.match(line)
    if match:
        addr, base = parse_address(match.group(2), sym_base=sym_base)
        return match.group(1), addr, "sym-name-addr", base
    return None


def load_symbol_table(
    symbol_path: Path,
    sym_base: str = "auto",
) -> tuple[dict[str, int], Counter[str], Counter[str], dict[str, set[int]]]:
    symbols: dict[str, int] = {}
    formats: Counter[str] = Counter()
    bases: Counter[str] = Counter()
    duplicates: dict[str, set[int]] = {}
    for line in symbol_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parsed = parse_symbol_line(line, sym_base)
        if parsed is None:
            continue
        name, addr, fmt, base = parsed
        if name in symbols and symbols[name] != addr:
            duplicates.setdefault(name, {symbols[name]}).add(addr)
        else:
            symbols.setdefault(name, addr)
        formats[fmt] += 1
        bases[base] += 1
    return symbols, formats, bases, duplicates


def fmt_hex(value: int | None) -> str:
    return "n/a" if value is None else f"${value:04X}"


def parse_byte_payload(payload: str) -> list[int]:
    values: list[int] = []
    for raw in payload.split(";", 1)[0].split(","):
        token = raw.strip()
        if not token or token.startswith(("'", '"')):
            return []
        try:
            if token.startswith("$"):
                value = int(token[1:], 16)
            elif token.lower().startswith("0x"):
                value = int(token, 16)
            elif re.fullmatch(r"[0-9a-f]+h", token, re.IGNORECASE):
                value = int(token[:-1], 16)
            elif token.isdecimal():
                value = int(token)
            else:
                return []
        except ValueError:
            return []
        if not 0 <= value <= 255:
            return []
        values.append(value)
    return values


def _walk_files(base: Path, exts: set[str]) -> list[Path]:
    out: list[Path] = []
    if not base.exists():
        return out
    for path in base.rglob("*"):
        if not path.is_file() or is_excluded(path):
            continue
        if path.suffix.lower() in exts or path.name in TOP_LEVEL_FILES:
            out.append(path)
    return out


def resolve_scope(target: str | Path, exts: set[str]) -> Scope:
    target = Path(target).resolve()
    if target.is_file():
        files = [target] if target.suffix.lower() in exts or target.name in TOP_LEVEL_FILES else []
        return Scope(target=target, base=target.parent, kind="file", scan_roots=[target], files=files)
    if not target.exists():
        return Scope(target=target, base=target, kind="missing", scan_roots=[], files=[])
    files = _walk_files(target, exts)
    scan_roots = [target]
    for name in SCAN_DIRS:
        path = target / name
        if path.is_dir():
            scan_roots.append(path)
    return Scope(target=target, base=target, kind="directory", scan_roots=scan_roots, files=files)


def resolve_target_scope(target: str | Path, exts: set[str]) -> Scope:
    """Resolve linked-target candidates, excluding conventional host-only trees."""
    scope = resolve_scope(target, exts)
    if scope.kind != "directory":
        return scope
    scope.files = [
        path for path in scope.files
        if path.name not in TOP_LEVEL_FILES and not is_host_only_path(path, scope.base)
    ]
    scope.scan_roots = [
        path for path in scope.scan_roots
        if path == scope.target or not is_host_only_path(path, scope.base)
    ]
    return scope


def map_symbol_is_runtime(line: str) -> bool:
    """Map constants/config values are not linked runtime helpers."""
    return re.search(r";\s*const\b", line, re.IGNORECASE) is None


def counts_by_kind(files: list[Path], base: Path) -> dict[str, int]:
    counts = {"source": 0, "generated_asm": 0, "listing": 0, "build_artifact": 0, "dist": 0, "unknown": 0}
    for path in files:
        kind = source_kind(path, base)
        counts[kind] = counts.get(kind, 0) + 1
    return counts


def print_scope(scope: Scope) -> None:
    print(f"root: {scope.target}")
    print(f"scope_kind: {scope.kind}")
    print("scan_roots:")
    if not scope.scan_roots:
        print("  none")
    for path in scope.scan_roots:
        print(f"  - {rel_path(path, scope.base)}")
    print(f"files_considered: {len(scope.files)}")
    counts = counts_by_kind(scope.files, scope.base)
    print(f"source_files: {counts.get('source', 0)}")
    print(f"generated_files: {counts.get('generated_asm', 0)}")
    print(f"listing_files: {counts.get('listing', 0)}")
    print(f"build_artifact_files: {counts.get('build_artifact', 0)}")
    print(f"dist_files: {counts.get('dist', 0)}")
