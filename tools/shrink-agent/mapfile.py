"""Parse z88dk linker maps into symbols and per-routine byte sizes.

A z88dk map line looks like::

    _ftp_passive = $9F48 ; addr, local, , src_main_build_c, code_compiler, src\\ftp.c::ftp_passive::0::279:137
    ring_put     = $D512 ; addr, public, , bitstream_asm_asm, code_user, asm/bitstream_asm.asm:812
    __BSS_END_tail = $FC08 ; const, public, def, , ,

Routine size is the distance from a routine's entry to the next routine entry
in the same section (or the section tail). That attributes inline literals and
local labels to the routine that owns them, which is what a size pass needs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

LINE_RE = re.compile(r"^(?P<name>\S+)\s*=\s*\$(?P<addr>[0-9A-Fa-f]+)\s*;\s*(?P<rest>.*)$")
C_LOC_RE = re.compile(r"^(?P<file>.+?)::(?P<func>[^:]+)::\d+::\d+:(?P<line>\d+)$")
ASM_LOC_RE = re.compile(r"^(?P<file>[^:]+(?::[\\/][^:]*)?):(?P<line>\d+)$")


@dataclass(frozen=True)
class Symbol:
    name: str
    addr: int
    kind: str
    scope: str
    module: str
    section: str
    location: str


@dataclass(frozen=True)
class Routine:
    name: str
    symbol: str
    addr: int
    size: int
    section: str
    file: str
    line: int
    lang: str  # "c" or "asm"


def parse_map_text(text: str) -> list[Symbol]:
    symbols: list[Symbol] = []
    for raw in text.splitlines():
        m = LINE_RE.match(raw.strip())
        if not m:
            continue
        fields = [f.strip() for f in m["rest"].split(",", 5)]
        fields += [""] * (6 - len(fields))
        kind, scope, _def, module, section, location = fields[:6]
        symbols.append(Symbol(m["name"], int(m["addr"], 16), kind, scope, module, section, location))
    return symbols


def parse_map(path: str | Path) -> list[Symbol]:
    return parse_map_text(Path(path).read_text(encoding="utf-8", errors="replace"))


def symbol_value(symbols: list[Symbol], name: str) -> int:
    for s in symbols:
        if s.name == name:
            return s.addr
    raise KeyError(f"symbol {name!r} not found in map")


def _norm(path: str) -> str:
    path = path.replace("\\", "/")
    return path[2:] if path.startswith("./") else path


def routines(symbols: list[Symbol], sections: list[str]) -> list[Routine]:
    """Return routines in the given sections, with sizes, largest first."""
    tails = {s.name: s.addr for s in symbols if s.kind == "const"}
    out: list[Routine] = []
    for section in sections:
        entries = []
        for s in symbols:
            if s.kind != "addr" or s.section != section:
                continue
            c = C_LOC_RE.match(s.location)
            if c:
                if s.name == "_" + c["func"]:
                    entries.append((s, "c", _norm(c["file"]), int(c["line"]), c["func"]))
                continue
            a = ASM_LOC_RE.match(s.location)
            if a and s.scope == "public":
                entries.append((s, "asm", _norm(a["file"]), int(a["line"]), s.name))
        entries.sort(key=lambda e: (e[0].addr, e[3], e[0].name))
        deduped = []
        for e in entries:  # same-address aliases collapse onto the earliest-defined label
            if not deduped or deduped[-1][0].addr != e[0].addr:
                deduped.append(e)
        entries = deduped
        tail = tails.get(f"__{section}_tail")
        for i, (sym, lang, file, line, name) in enumerate(entries):
            end = entries[i + 1][0].addr if i + 1 < len(entries) else tail
            if end is None:
                continue
            size = end - sym.addr
            if size <= 0:
                continue  # alias of the next label
            out.append(Routine(name, sym.name, sym.addr, size, section, file, line, lang))
    out.sort(key=lambda r: (-r.size, r.name))
    return out
