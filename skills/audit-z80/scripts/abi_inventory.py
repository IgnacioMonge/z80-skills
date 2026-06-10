#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

TEXT_EXTS = {".asm", ".c", ".h", ".inc", ".s"}
TOP_LEVEL_FILES = {"Makefile", "makefile"}
PREFERRED_DIRS = ("src", "asm", "include", "overlay")
CALLCONV_RE = re.compile(r"(__z88dk_callee|__z88dk_fastcall|__naked)")
DECL_RE = re.compile(
    r"\b(?P<conv>__z88dk_callee|__z88dk_fastcall|__naked)?\s*"
    r"(?P<ret>void|char|unsigned\s+char|uint8_t|int|unsigned|uint16_t|long|uint32_t|bool|[A-Za-z_]\w+\s*\*)"
    r"\s+(?P<name>[A-Za-z_]\w+)\s*\((?P<args>[^;{}]*)\)\s*;"
)
PUBLIC_RE = re.compile(r"^\s*PUBLIC\s+([A-Za-z_.$][\w.$@]*)", re.IGNORECASE)
EXTERN_RE = re.compile(r"^\s*EXTERN\s+([A-Za-z_.$][\w.$@]*)", re.IGNORECASE)
LABEL_RE = re.compile(r"^([A-Za-z_.$?@][\w.$?@]*):\s*$")
RET_N_RE = re.compile(r"\bret\s+(\d+)\b", re.IGNORECASE)
STACK_CLEAN_RE = re.compile(r"\b(pop\s+af|inc\s+sp|dec\s+sp|add\s+sp)\b", re.IGNORECASE)


def source_roots(root: Path) -> list[Path]:
    roots = [root / name for name in PREFERRED_DIRS if (root / name).exists()]
    return roots or [root]


def files(root: Path):
    for name in TOP_LEVEL_FILES:
        path = root / name
        if path.is_file():
            yield path
    for base in source_roots(root):
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_EXTS:
                yield path


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    c_decls: dict[str, list[str]] = {}
    asm_exports: dict[str, str] = {}
    asm_imports: list[str] = []

    print(f"root: {root}")
    print("\n[callconv_lines]")
    found_callconv = False
    for path in files(root):
        if path.suffix.lower() not in {".c", ".h"}:
            continue
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for lineno, line in enumerate(lines, start=1):
            if CALLCONV_RE.search(line):
                print(f"{path.relative_to(root)}:{lineno}: {line.strip()}")
                found_callconv = True
            decl = DECL_RE.search(line)
            if decl:
                conv = decl.group("conv") or "cdecl"
                signature = " ".join(line.strip().split())
                c_decls.setdefault(decl.group("name"), []).append(
                    f"{path.relative_to(root)}:{lineno}: {conv}: {signature}"
                )
    if not found_callconv:
        print("none")

    print("\n[c_boundary_declarations]")
    boundary = [
        item
        for values in c_decls.values()
        for item in values
        if "__z88dk_" in item or "__naked" in item
    ]
    print("\n".join(boundary[:120]) if boundary else "none")

    print("\n[asm_exports]")
    exports = []
    imports = []
    stack_cleanup_hints = []
    for path in files(root):
        if path.suffix.lower() not in {".asm", ".inc", ".s"}:
            continue
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        current_label = "(file-scope)"
        for lineno, line in enumerate(lines, start=1):
            label = LABEL_RE.match(line.strip())
            if label:
                current_label = label.group(1)
            pub = PUBLIC_RE.search(line)
            if pub:
                exports.append(f"{pub.group(1)} <- {path.relative_to(root)}:{lineno}")
                asm_exports[pub.group(1)] = f"{path.relative_to(root)}:{lineno}"
            ext = EXTERN_RE.search(line)
            if ext:
                imports.append(f"{ext.group(1)} <- {path.relative_to(root)}:{lineno}")
                asm_imports.append(ext.group(1))
            if RET_N_RE.search(line) or STACK_CLEAN_RE.search(line):
                stack_cleanup_hints.append(
                    f"{path.relative_to(root)}:{lineno}: {current_label}: {line.strip()}"
                )
    print("\n".join(exports[:80]) if exports else "none")

    print("\n[asm_imports]")
    print("\n".join(imports[:80]) if imports else "none")

    print("\n[boundary_mismatches_to_review]")
    mismatches: list[str] = []
    for name, where in sorted(asm_exports.items()):
        cname = name.lstrip("_")
        if (
            name not in c_decls
            and cname not in c_decls
            and not name.startswith(("asm_", "__"))
        ):
            mismatches.append(
                f"ASM export without obvious C prototype: {name} <- {where}"
            )
    for name, decls in sorted(c_decls.items()):
        if any("__z88dk_" in item or "__naked" in item for item in decls):
            asm_names = {name, f"_{name}", f"_{name}_callee"}
            if not any(candidate in asm_exports for candidate in asm_names):
                mismatches.append(
                    f"C special-convention decl without obvious ASM export: {decls[0]}"
                )
    print("\n".join(mismatches[:120]) if mismatches else "none")

    print("\n[stack_cleanup_hints]")
    if stack_cleanup_hints:
        print("\n".join(stack_cleanup_hints[:120]))
        print(
            "note: verify byte count against packed SDCC stack args; pop af for uint8_t tails is a common trap"
        )
    else:
        print("none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
