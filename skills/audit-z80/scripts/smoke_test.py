#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(script: str, target: Path, *args: str) -> str:
    proc = subprocess.run([PY, str(ROOT / "scripts" / script), *args, str(target)], text=True, capture_output=True, check=True)
    return proc.stdout.replace("\\", "/")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name in ("src", "asm", "build", "lib", "vendor"):
            (root / name).mkdir()
        (root / "src" / "api.h").write_text("#define FAST __z88dk_fastcall\ntypedef unsigned char u8;\n__smallc int foo(uint8_t a);\nint bar(uint8_t a) __sdcccall(0);\nFAST void baz(uint8_t a);\nu8 typed(u8 a);\n", encoding="utf-8")
        (root / "src" / "dummy.c").write_text("int dummy(void) { return 0; }\n", encoding="utf-8")
        (root / "main.c").write_text("static const char *names[] = {\"a\", \"b\"};\nchar buf[4];\nvoid f(int i) { buf[i] = 'x'; }\nvoid g(void) { __asm call helper __endasm; }\nvoid caller(void) { x = foo(1); orphan(1); }\n", encoding="utf-8")
        (root / "top.asm").write_text("PUBLIC _plain\n_plain:\n    di\n.local:\n    ret\ncond:\n    push hl\n    jp nz, later\n    pop hl\nlater:\n    ret\ninternal:\n    push hl\n    jr .restore\n.restore:\n    pop hl\n    ret\nrepeat:\n    call nz, helper\n    call nz, helper\n    call nz, helper\n    ret\nwrapper:\n    call helper\n    ret nz\n", encoding="utf-8")
        (root / "asm" / "mod.asm").write_text("PUBLIC _foo, _bar, _orphan\nPUBLIC _typed\n_foo: push hl\n    ret\n_bar:\n    ret\n_orphan:\n    ret\n_typed:\n    ret\n", encoding="utf-8")
        (root / "lib" / "hidden.asm").write_text("hidden:\n    di\n    ret\n", encoding="utf-8")
        (root / "build" / "gen.lst").write_text("    rst 8\n", encoding="utf-8")
        (root / "build" / "app.map").write_text("__BSS_END_tail = $9000 ;\n__register_sp = $FF00 ;\n", encoding="utf-8")
        (root / "vendor" / "bad.map").write_text("bad = $0000 ;\n", encoding="utf-8")
        sym_path = root / "build" / "app.sym"
        sym_path.write_text("16384 drawFast\n__BSS_END_tail EQU 36864\n__register_sp: EQU 0x0000FF00\n", encoding="utf-8")
        amb_sym = root / "build" / "amb.sym"
        amb_sym.write_text("4000 drawFast\n9000 __BSS_END_tail\n9999 __register_sp\n", encoding="utf-8")

        z80 = run("z80_pattern_scan.py", root)
        assert "main.c" in z80 and "top.asm" in z80 and "lib/hidden.asm" in z80
        assert "mixed-pointer-literal-table" in z80
        assert "small-buffer-write" in z80
        assert "inline-asm-register-clobber" in z80
        assert "exit-with-interrupts-disabled" in z80
        stack_section = z80.split("[stack-delta-at-exit]", 1)[1].split("\n\n", 1)[0] if "[stack-delta-at-exit]" in z80 else ""
        assert "top.asm" not in stack_section
        assert "helper:" in z80 and "nz:" not in z80
        tail_section = z80.split("[call-followed-by-ret]", 1)[1].split("\n\n", 1)[0] if "[call-followed-by-ret]" in z80 else ""
        assert "wrapper" not in tail_section
        assert "build/gen.lst" in z80
        high = run("z80_pattern_scan.py", root, "--level", "high")
        assert "level: high" in high
        assert "exit-with-interrupts-disabled" in high
        assert "repeated-call-targets] count=0" in high

        abi = run("abi_inventory.py", root)
        assert "__smallc" in abi
        assert "__sdcccall(0)" in abi
        assert "FAST->__z88dk_fastcall" in abi
        assert "_foo <- asm/mod.asm" in abi and "_bar <- asm/mod.asm" in abi
        assert "foo: src/api.h" in abi and "foo: main.c" not in abi
        assert "_orphan <- asm/mod.asm" in abi and "orphan:" not in abi
        assert "typed:" in abi and "return=unknown/typedef-like" in abi
        assert "[asm_c_boundary_pairs]" in abi

        preflight = run("preflight_scan.py", root)
        assert "main.c" in preflight and "top.asm" in preflight and "lib/hidden.asm" in preflight
        assert "build/gen.lst" in preflight
        assert "rst 8" in preflight.lower()

        summary = run("map_summary.py", sym_path)
        assert "symbol_file:" in summary
        assert "sym-addr-name=1" in summary and "sym-equ=2" in summary
        assert "address_base: decimal=2, hex=1" in summary
        assert "drawFast: $4000" in summary
        assert "stack_gap: 28416 bytes ($FF00 - $9000)" in summary
        assert "note: approximate" in summary

        root_summary = run("map_summary.py", root)
        assert "vendor/bad.map" not in root_summary
        assert "build/app.map" in root_summary
        assert "selected_reason: only .map outside skipped dirs" in root_summary

        zero_map = root / "zero.map"
        zero_map.write_text("__BSS_END_tail = $0000 ;\n__register_sp = $0000 ;\n", encoding="utf-8")
        zero = run("map_summary.py", zero_map)
        assert "stack_gap: 0 bytes ($0000 - $0000)" in zero

        dup_map = root / "duplicate.map"
        dup_map.write_text("same = $1000 ;\nsame = $2000 ;\n", encoding="utf-8")
        duplicate = run("map_summary.py", dup_map)
        assert "warning: conflicting duplicate symbol same: $1000, $2000" in duplicate

        amb = run("map_summary.py", amb_sym)
        assert "ambiguous-plain-numeric=3" in amb
        assert "warning: plain 4-digit .sym addresses are ambiguous" in amb
        assert "stack_gap: unverified" in amb
        forced = run("map_summary.py", amb_sym, "--sym-base", "hex")
        assert "drawFast: $4000" in forced
        assert "stack_gap: 2457 bytes ($9999 - $9000)" in forced

    print("smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
