#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

TEXT_EXTS = {".asm", ".c", ".h", ".i", ".inc", ".lst", ".s"}
TOP_LEVEL_FILES = {"Makefile", "makefile"}
SKIP_DIRS = {".git", ".svn", ".hg", ".venv", "venv", "node_modules", "__pycache__", "third_party", "vendor"}
MAX_BYTES = 2_000_000
DIRECT_CALLCONV_RE = re.compile(r"__z88dk_callee|__z88dk_fastcall|__naked|__smallc|__sdcccall\s*\(\s*[01]\s*\)")
DEFINE_CONV_RE = re.compile(r"^\s*#\s*define\s+(\w+)\b.*(__z88dk_callee|__z88dk_fastcall|__naked|__smallc|__sdcccall\s*\(\s*[01]\s*\))")
FUNC_HEAD_RE = re.compile(r"\b(?P<name>[A-Za-z_]\w+)\s*\((?P<args>[^()]*)\)\s*(?P<tail>[^;{}]*)\s*(?P<kind>[;{])")
PUBLIC_RE = re.compile(r"^\s*(?:PUBLIC|GLOBAL|XDEF|EXPORT|\.globl)\s+(.+)", re.IGNORECASE)
EXTERN_RE = re.compile(r"^\s*(?:EXTERN|XREF|\.extern)\s+(.+)", re.IGNORECASE)
SYMBOL_RE = re.compile(r"[A-Za-z_.$][\w.$?@]*")
LABEL_RE = re.compile(r"^([A-Za-z_.$?@][\w.$?@]*):(?:\s|$)")
RET_N_RE = re.compile(r"\bret\s+(\d+)\b", re.IGNORECASE)
STACK_CLEAN_RE = re.compile(r"\b(pop\s+af|inc\s+sp|dec\s+sp|add\s+sp)\b", re.IGNORECASE)
ALIAS_RE = re.compile(r"^\s*(?:defc\s+)?([A-Za-z_.$?@][\w.$?@]*)\s*=\s*([A-Za-z_.$?@][\w.$?@]*)", re.IGNORECASE)
TYPE_HINT_RE = re.compile(r"\b(void|char|unsigned|signed|uint8_t|uint16_t|uint32_t|int8_t|int16_t|int32_t|int|long|bool|size_t|[A-Za-z_]\w+\s*\*)\b")
CONTROL_NAMES = {"if", "for", "while", "switch", "return", "sizeof"}
EXPR_PREFIX_RE = re.compile(r"(?:=|\+=|-=|/=|%=|==|!=|<=|>=|&&|\|\||\[|\]|->|\.)")


def skip_path(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        parts = path.parts
    return any(part in SKIP_DIRS for part in parts)


def files(root: Path) -> tuple[list[Path], list[Path]]:
    found: list[Path] = []
    too_large: list[Path] = []
    if root.is_file():
        return ([root] if root.suffix.lower() in TEXT_EXTS and root.stat().st_size <= MAX_BYTES else []), too_large
    for path in root.rglob("*"):
        if skip_path(path, root) or not path.is_file():
            continue
        if path.name not in TOP_LEVEL_FILES and path.suffix.lower() not in TEXT_EXTS:
            continue
        if path.stat().st_size > MAX_BYTES:
            too_large.append(path)
            continue
        found.append(path)
    found.sort(key=lambda item: (item.suffix.lower() not in {".h", ".i"}, str(item).lower()))
    return found, too_large


def directive_symbols(line: str, regex: re.Pattern[str]) -> list[str]:
    match = regex.search(line)
    if not match:
        return []
    body = re.split(r";|//", match.group(1), 1)[0]
    return [token for token in re.split(r"[\s,]+", body.strip()) if SYMBOL_RE.fullmatch(token)]


def logical_c_records(lines: list[str]):
    buf: list[str] = []
    start = 1
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("//", "/*", "*", "#")):
            continue
        if not buf:
            start = lineno
        buf.append(stripped)
        if ";" in stripped or "{" in stripped:
            yield start, " ".join(buf)
            buf = []


def convs_in(text: str, macro_convs: dict[str, str]) -> list[str]:
    found = [" ".join(m.group(0).split()) for m in DIRECT_CALLCONV_RE.finditer(text)]
    for macro, target in macro_convs.items():
        if re.search(rf"\b{re.escape(macro)}\b", text):
            found.append(f"{macro}->{target}")
    return sorted(dict.fromkeys(found))


def plausible_decl_prefix(before: str, convs: list[str]) -> bool:
    if not before or before.split()[0] in CONTROL_NAMES:
        return False
    if EXPR_PREFIX_RE.search(before):
        return False
    return bool(convs or TYPE_HINT_RE.search(before) or re.fullmatch(r"[A-Za-z_]\w*(?:\s+[A-Za-z_]\w*)*(?:\s*\*)?", before))


def decl_score(decl: str) -> tuple[int, int, int, int]:
    is_header = int(".h:" in decl or ".i:" in decl)
    is_proto = int(": prototype:" in decl)
    known = int("return=known" in decl)
    special = int("default/unmarked" not in decl)
    return is_header, is_proto, known, special


def best_decl(decls: list[str]) -> str:
    return sorted(decls, key=decl_score, reverse=True)[0]


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    all_files, too_large = files(root)
    c_decls: dict[str, list[str]] = {}
    asm_exports: dict[str, str] = {}
    asm_imports: list[str] = []
    aliases: dict[str, str] = {}
    macro_convs: dict[str, str] = {}

    for path in all_files:
        if path.suffix.lower() not in {".c", ".h", ".i"}:
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            match = DEFINE_CONV_RE.search(line)
            if match:
                macro_convs[match.group(1)] = " ".join(match.group(2).split())

    print(f"root: {root}")
    print(f"files_scanned: {len(all_files)}")
    print("dirs_scanned: .")
    print("dirs_skipped: " + ", ".join(sorted(SKIP_DIRS)))
    print("files_skipped_too_large: " + (str(len(too_large)) if too_large else "0"))
    for path in too_large[:20]:
        print(f"  {rel(path, root)} {path.stat().st_size} bytes")

    print("\n[callconv_lines]")
    found_callconv = False
    for path in all_files:
        if path.suffix.lower() not in {".c", ".h", ".i"}:
            continue
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for lineno, line in enumerate(lines, start=1):
            if DIRECT_CALLCONV_RE.search(line) or any(re.search(rf"\b{re.escape(macro)}\b", line) for macro in macro_convs):
                print(f"{rel(path, root)}:{lineno}: {line.strip()}")
                found_callconv = True
        for start, record in logical_c_records(lines):
            match = FUNC_HEAD_RE.search(record)
            if not match or match.group("name") in CONTROL_NAMES:
                continue
            before = record[: match.start()].strip()
            convs = convs_in(before + " " + match.group("tail"), macro_convs)
            if not plausible_decl_prefix(before, convs):
                continue
            conv = ",".join(convs) if convs else "default/unmarked"
            kind = "prototype" if match.group("kind") == ";" else "definition"
            ret = "known" if TYPE_HINT_RE.search(before) else "unknown/typedef-like"
            signature = " ".join(record.split())[:240]
            c_decls.setdefault(match.group("name"), []).append(
                f"{rel(path, root)}:{start}: {kind}: {conv}: return={ret}: {signature}"
            )
    if not found_callconv:
        print("none")

    print("\n[c_boundary_declarations]")
    boundary = [item for values in c_decls.values() for item in values if "default/unmarked" not in item]
    print("\n".join(boundary[:160]) if boundary else "none")

    print("\n[asm_exports]")
    exports: list[str] = []
    imports: list[str] = []
    stack_cleanup_hints: list[str] = []
    for path in all_files:
        if path.suffix.lower() not in {".asm", ".inc", ".lst", ".s"}:
            continue
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        current_label = "(file-scope)"
        for lineno, line in enumerate(lines, start=1):
            label = LABEL_RE.match(line.strip())
            if label:
                current_label = label.group(1)
            for symbol in directive_symbols(line, PUBLIC_RE):
                exports.append(f"{symbol} <- {rel(path, root)}:{lineno}")
                asm_exports[symbol] = f"{rel(path, root)}:{lineno}"
            for symbol in directive_symbols(line, EXTERN_RE):
                imports.append(f"{symbol} <- {rel(path, root)}:{lineno}")
                asm_imports.append(symbol)
            alias = ALIAS_RE.search(line)
            if alias:
                aliases[alias.group(1)] = alias.group(2)
            if RET_N_RE.search(line) or STACK_CLEAN_RE.search(line):
                stack_cleanup_hints.append(f"{rel(path, root)}:{lineno}: {current_label}: {line.strip()}")
    print("\n".join(exports[:80]) if exports else "none")

    print("\n[asm_imports]")
    print("\n".join(imports[:80]) if imports else "none")

    print("\n[asm_c_boundary_pairs]")
    pairs: list[str] = []
    for cname, decls in sorted(c_decls.items()):
        for aname in (cname, f"_{cname}", f"_{cname}_callee", f"asm_{cname}"):
            if aname in asm_exports:
                pairs.append(f"{cname}: {best_decl(decls)} | {aname} <- {asm_exports[aname]}")
            if aname in aliases and aliases[aname] in asm_exports:
                pairs.append(f"{cname}: {best_decl(decls)} | {aname}={aliases[aname]} <- {asm_exports[aliases[aname]]}")
    print("\n".join(pairs[:160]) if pairs else "none")

    print("\n[boundary_candidates_to_review]")
    candidates: list[str] = []
    for name, where in sorted(asm_exports.items()):
        cname = name.lstrip("_")
        if name not in c_decls and cname not in c_decls and name.removeprefix("asm_") not in c_decls and not name.startswith("__"):
            candidates.append(f"ASM export without parsed C declaration (parser-limited): {name} <- {where}")
    for name, decls in sorted(c_decls.items()):
        if any("default/unmarked" not in item for item in decls):
            asm_names = {name, f"_{name}", f"_{name}_callee"}
            if not any(candidate in asm_exports for candidate in asm_names):
                candidates.append(f"Special-convention C declaration without parsed ASM export (may be C-only or macro-generated): {best_decl(decls)}")
    print("\n".join(candidates[:120]) if candidates else "none")

    print("\n[stack_cleanup_hints]")
    if stack_cleanup_hints:
        print("\n".join(stack_cleanup_hints[:120]))
        print("note: verify byte count against packed SDCC stack args; pop af for uint8_t tails is a common trap")
    else:
        print("none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
