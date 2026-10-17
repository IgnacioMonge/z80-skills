#!/usr/bin/env python3
"""Executable examples for packed FSM semantics and archive extraction units."""
from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def pack(rows: list[tuple[int, int, int, int]]) -> bytes:
    if any(not 0 <= value <= 15 for row in rows for value in row):
        raise ValueError("IDs must fit a nibble")
    return bytes(byte for state, condition, action, next_state in rows
                 for byte in (state << 4 | condition, action << 4 | next_state))


def step(table: bytes, state: int, event: int) -> tuple[int, int | None]:
    if not 0 <= state <= 15 or len(table) % 2:
        raise ValueError("invalid state or truncated row")
    conditions = {0: True, 1: event == 1, 2: event != 0}
    for offset in range(0, len(table), 2):
        match, effect = table[offset:offset + 2]
        if match >> 4 != state:
            continue
        condition, action = match & 15, effect >> 4
        if condition not in conditions or action not in (0, 2, 15):
            raise ValueError("missing condition/action handler")
        if conditions[condition]:
            return effect & 15, action
    return state, None


def check_fsm() -> None:
    table = pack([(0, 1, 15, 15), (0, 2, 2, 1), (0, 0, 0, 0),
                  (15, 0, 0, 0)])
    for state in range(16):
        for event in range(4):
            # Independent direct-branch reference: event 1 satisfies both guards.
            if state == 0:
                expected = (15, 15) if event == 1 else (1, 2) if event else (0, 0)
            else:
                expected = (0, 0) if state == 15 else (state, None)
            assert step(table, state, event) == expected, (state, event)
    assert step(b"", 0, 1) == (0, None)
    assert step(pack([(0, 0, 0, 0), (0, 1, 15, 15)]), 0, 1) == (0, 0)
    for state, broken in [(-1, table), (16, table), (0, table[:-1]),
                          (0, pack([(0, 15, 0, 0)])),
                          (0, pack([(0, 0, 1, 0)]))]:
        try:
            step(broken, state, 1)
        except ValueError:
            pass
        else:
            raise AssertionError((state, broken))
    for value in (-1, 16):
        for field in range(4):
            row = [0, 0, 0, 0]
            row[field] = value
            try:
                pack([tuple(row)])
            except ValueError:
                pass
            else:
                raise AssertionError(row)
    print("packed FSM: 64 state/event cases, order and error boundaries passed")


def check_archive() -> None:
    assembler = shutil.which("z88dk-z80asm") or shutil.which("z80asm")
    if not assembler:
        print("archive extraction: SKIP (z88dk-z80asm unavailable)")
        return
    help_text = subprocess.run([assembler, "-h"], capture_output=True, text=True, timeout=10)
    if help_text.returncode or "Z80 Macro Assembler" not in help_text.stdout or "-x[=]FILE" not in help_text.stdout:
        print("archive extraction: SKIP (assembler lacks verified z88dk library interface)")
        return
    with tempfile.TemporaryDirectory(prefix="shrink-archive-") as temporary:
        root = Path(temporary)

        def assemble(directory: Path, *args: str) -> None:
            proc = subprocess.run([assembler, *args], cwd=directory, capture_output=True, text=True, timeout=10)
            assert proc.returncode == 0, proc.stdout + proc.stderr

        routines = {"used": "ld a,42\nret\n", "extra": "ld a,99\nret\n"}
        results = {}
        for layout in ("whole", "split"):
            directory = root / layout
            directory.mkdir()
            sources = []
            for name, body in routines.items():
                text = f"PUBLIC {name}\n{name}:\n{body}"
                if layout == "split":
                    (directory / f"{name}.asm").write_text(text, encoding="ascii")
                    sources.append(f"{name}.asm")
                else:
                    sources.append(text)
            if layout == "whole":
                (directory / "both.asm").write_text("".join(sources), encoding="ascii")
                sources = ["both.asm"]
            assemble(directory, "-xhelpers.lib", *sources)
            for consumer in ("minimal", "all"):
                calls = "call used\n" + ("call extra\n" if consumer == "all" else "")
                source = "EXTERN used, extra\nPUBLIC start\nstart:\n" + calls + "ret\n"
                (directory / f"{consumer}.asm").write_text(source, encoding="ascii")
                assemble(directory, "-b", "-m", "-r32768", f"-o{consumer}.bin",
                         f"{consumer}.asm", "-lhelpers.lib")
                binary = (directory / f"{consumer}.bin").read_bytes()
                symbols = dict(re.findall(r"^(used|extra)\s*=\s*\$([0-9A-Fa-f]+)",
                                          (directory / f"{consumer}.map").read_text(), re.M))
                assert "used" in symbols
                for name, value in (("used", 42), ("extra", 99)):
                    if name in symbols:
                        offset = int(symbols[name], 16) - 32768
                        assert binary[offset:offset + 3] == bytes((0x3E, value, 0xC9))
                results[layout, consumer] = binary, symbols
        assert len(results["whole", "minimal"][0]) == 10
        assert len(results["split", "minimal"][0]) == 7
        assert "extra" in results["whole", "minimal"][1]
        assert "extra" not in results["split", "minimal"][1]
        assert results["whole", "all"][0] == results["split", "all"][0]
        assert len(results["split", "all"][0]) == 13
    print("archive extraction: minimal 10 -> 7 B; all-feature binaries identical (13 B)")


if __name__ == "__main__":
    check_fsm()
    check_archive()
