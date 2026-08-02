#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import os
import time
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(*args: str, expect: int = 0) -> str:
    proc = subprocess.run([PY, *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if proc.returncode != expect:
        raise AssertionError(f"expected exit {expect}, got {proc.returncode}: {' '.join(args)}\n{proc.stdout}")
    return proc.stdout


def section(out: str, name: str) -> list[str]:
    chunk = out.split(f"[{name}]", 1)[-1].split("note:", 1)[0]
    return [line.strip() for line in chunk.splitlines()]


def main() -> int:
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    dispatcher_text = (SKILL / "references" / "dispatcher.md").read_text(encoding="utf-8")
    agent_text = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
    orchestration_text = (SKILL / "references" / "agent-orchestration.md").read_text(encoding="utf-8")
    assert "../workflow/SKILL.md" in skill_text
    assert "## Workflow Boundary" in orchestration_text
    assert "C:/Program Files" not in skill_text + dispatcher_text

    byte_text = (SKILL / "references" / "z80-byte-evidence.md").read_text(encoding="utf-8")
    blackbook_text = (SKILL / "references" / "size-blackbook.md").read_text(encoding="utf-8")
    assert "`reti`/`retn` = 2" in byte_text
    assert "ASCII-hex without table or branch (6 bytes)" in blackbook_text

    research = (SKILL / "references" / "external-research.md").read_text(encoding="utf-8")
    assert "Trigger Gate" in research and "Source Corridors" in research

    for relative in (
        "references/hard-contract.md",
        "references/agent-orchestration.md",
        "references/reporting.md",
    ):
        assert "multi-target" in (SKILL / relative).read_text(encoding="utf-8").lower()

    root = Path(tempfile.mkdtemp(prefix="shrink-z80-smoke-"))
    try:
        (root / "src").mkdir()
        (root / "engine").mkdir()
        (root / "build").mkdir()
        (root / "single.asm").write_text("start:\n  jr nz,skip\n  ret z\n  call live\nskip:\n  ret\nlive:\n  ret\n", encoding="ascii")
        (root / "main.c").write_text("static int unused(void){ return 1; }\nint used(void){ return 2; }\nint main(void){ return used(); }\n", encoding="ascii")
        (root / "src" / "a.c").write_text("void a(void){ printf(\"SRC\"); }\n", encoding="ascii")
        (root / "src" / "arith.c").write_text("char *p;\nint deref(void){return *p;}\nint mul3(int x){return x * 3;}\n", encoding="ascii")
        (root / "engine" / "hidden.c").write_text("void hidden(void){ printf(\"ENGINE\"); }\n", encoding="ascii")
        (root / "tools").mkdir()
        (root / "tools" / "host.c").write_text("void host(void){ printf(\"HOST_ONLY\"); printf(\"HOST_ONLY\"); }\n", encoding="ascii")
        (root / "Makefile").write_text('noise := malloc("MAKE_NOISE")\n', encoding="ascii")
        (root / "build" / "gen.asm").write_text("call z,__mulint\nld ix,$8000\nret\n", encoding="ascii")
        (root / "build" / "a.map").write_text("__CODE_head = $8000 ;\n__CODE_size = $000C ;\n__CODE_tail = $800C ;\n__CODE_END_tail = $8080 ;\n__mulint = $8010 ;\n", encoding="ascii")
        (root / "src" / "data.asm").write_text("table: db " + ",".join(["0"] * 50 + [str(i) for i in range(50)]) + "\n", encoding="ascii")
        (root / "src" / "strings.asm").write_text('db "ASM_DUP"\ndb "ASM_DUP"\n', encoding="ascii")
        (root / "src" / "comments.c").write_text(
            "// \"COMMENT_DUP\"\n/* \"COMMENT_DUP\" */\n#if 0\nconst char *x = \"COMMENT_DUP\";\n#endif\nconst char *ok = \"ACTIVE_ONE\";\n",
            encoding="ascii",
        )
        (root / "noise.asm").write_text("push hl\nld (hl),a\nld h,$40\nret\n", encoding="ascii")
        (root / "conditional_tail.asm").write_text("wrap:\n  call nz,foo\n  ret\nfoo:\n  ret\n", encoding="ascii")
        (root / "fallthrough.asm").write_text("start:\n  call first\n  call second\n  ret\nfirst:\n  ret\nsecond:\n  ret\n", encoding="ascii")
        (root / "dead_comments.asm").write_text("start:\n  ret\nunused:\n  ret\n; call unused\n", encoding="ascii")
        (root / "dead_comments.c").write_text("static void unused(void){}\nint main(void){return 0;}\n// unused();\n#if 0\nunused();\n#endif\n", encoding="ascii")
        (root / "alias_only").mkdir()
        (root / "alias_only" / "mixed.c").write_text("void foo(void){}\nint main(void){return 0;}\n", encoding="ascii")
        (root / "alias_only" / "mixed.asm").write_text("start:\n  call _foo\n  ret\n", encoding="ascii")
        (root / "inactive_lbp").mkdir()
        (root / "inactive_lbp" / "main.c").write_text("int main(void){return 0;}\n#if 0\nprintf(\"x\");\n#endif\n/* printf(\"comment\"); */\n", encoding="ascii")
        (root / "inactive_lbp" / "a.map").write_text("printf = $8000 ;\n", encoding="ascii")
        (root / "build" / "foo.lst").write_text("call z,__mulint\nret\n", encoding="ascii")
        (root / "build" / "blob.tap").write_bytes(b"\x00\xff" * 32)

        out = run(str(SKILL / "scripts" / "z80_pattern_scan.py"), str(root / "single.asm"))
        assert "scope_kind: file" in out and "files_scanned: 1" in out

        out = run(str(SKILL / "scripts" / "map_summary.py"), str(root / "build" / "a.map"))
        assert "CODE: head=$8000 tail=$8080 size=128" in out
        assert "[resident_vs_banked_heuristic]" in out
        assert "[crt_startup_drag]" in out

        out = run(str(SKILL / "scripts" / "libpull_scan.py"), str(root), str(root / "build" / "a.map"))
        assert "src" in out and "engine" in out
        assert "HOST_ONLY" not in out and "MAKE_NOISE" not in out
        arith_rows = section(out, "c_arithmetic_candidates")
        assert not any("return *p" in line for line in arith_rows)
        assert any("return x * 3" in line for line in arith_rows)
        out = run(str(SKILL / "scripts" / "libpull_scan.py"), str(root / "tools" / "host.c"))
        assert "HOST_ONLY" in out
        out = run(str(SKILL / "scripts" / "z80_pattern_scan.py"), str(root))
        assert "HOST_ONLY" not in out
        out = run(str(SKILL / "scripts" / "deadcode_scan.py"), str(root))
        assert "host:" not in out
        out = run(str(SKILL / "scripts" / "literal_dup_scan.py"), str(root))
        assert "HOST_ONLY" not in out

        out = run(str(SKILL / "scripts" / "literal_dup_scan.py"), str(root))
        assert "estimated_net_save" not in out and "exact_codec_required" in out
        assert "COMMENT_DUP" not in out
        assert "2x | ASM_DUP" in out and "4x | ASM_DUP" not in out

        out = run(str(SKILL / "scripts" / "z80_pattern_scan.py"), str(root / "noise.asm"))
        assert "\n[stack-blitter-shape]" not in out
        assert "\n[compiled-sprite-shape]" not in out
        assert "\n[page-local-indexing]" not in out
        assert "[low-signal-aggregate] count=0" in out

        out = run(str(SKILL / "scripts" / "z80_pattern_scan.py"), str(root / "conditional_tail.asm"))
        assert "\n[tail-call-wrapper]" not in out

        stack_args = root / "stack_args.asm"
        stack_args.write_text("wrap:\n  push de\n  call foo\n  ret\nfoo:\n  ret\n", encoding="ascii")
        out = run(str(SKILL / "scripts" / "z80_pattern_scan.py"), str(stack_args))
        assert "\n[tail-call-wrapper]" not in out
        plain_tail = root / "plain_tail.asm"
        plain_tail.write_text("wrap:\n  call foo\n  ret\nfoo:\n  ret\n", encoding="ascii")
        out = run(str(SKILL / "scripts" / "z80_pattern_scan.py"), str(plain_tail))
        assert "\n[tail-call-wrapper]" in out

        out = run(str(SKILL / "scripts" / "z80_pattern_scan.py"), str(root / "fallthrough.asm"))
        assert "\n[fallthrough-call-chain]" in out

        out = run(str(SKILL / "scripts" / "deadcode_scan.py"), str(root / "single.asm"))
        assert "skip:" not in out.split("[possible_unreferenced_symbols]", 1)[-1]

        out = run(str(SKILL / "scripts" / "deadcode_scan.py"), str(root / "main.c"))
        lines = section(out, "possible_unreferenced_symbols")
        assert any(line.startswith("unused:") for line in lines)
        assert not any(line.startswith("used:") for line in lines)

        out = run(str(SKILL / "scripts" / "deadcode_scan.py"), str(root / "dead_comments.asm"))
        assert any(line.startswith("unused:") for line in section(out, "possible_unreferenced_symbols"))

        out = run(str(SKILL / "scripts" / "deadcode_scan.py"), str(root / "dead_comments.c"))
        assert any(line.startswith("unused:") for line in section(out, "possible_unreferenced_symbols"))

        out = run(str(SKILL / "scripts" / "deadcode_scan.py"), str(root / "alias_only" / "mixed.c"))
        assert any(line.startswith("foo:") for line in section(out, "possible_unreferenced_symbols"))
        out = run(str(SKILL / "scripts" / "deadcode_scan.py"), str(root / "alias_only"))
        assert not any(line.startswith("foo:") for line in section(out, "possible_unreferenced_symbols"))

        out = run(str(SKILL / "scripts" / "libpull_scan.py"), str(root / "inactive_lbp"), str(root / "inactive_lbp" / "a.map"))
        assert "printf(" not in out

        const_map = root / "const_helpers.map"
        const_map.write_text(
            "TAR__clib_malloc_heap_size = $FFFFFFFF ; const, local\n"
            "__code_alloc_malloc_size = $0000 ; const, public\n"
            "__mulint = $8010 ; addr, public\n",
            encoding="ascii",
        )
        out = run(str(SKILL / "scripts" / "libpull_scan.py"), str(root), str(const_map))
        assert "TAR__clib_malloc_heap_size" not in out
        assert "__code_alloc_malloc_size" not in out
        assert "__mulint" in out

        out = run(str(SKILL / "scripts" / "generated_helper_scan.py"), str(root), str(root / "build" / "a.map"))
        assert "__mulint" in out

        out = run(str(SKILL / "scripts" / "preflight_scan.py"), str(root))
        assert "[binary_artifacts]" in out and "blob.tap" in out
        out = run(str(SKILL / "scripts" / "artifact_freshness.py"), str(root))
        assert "verdict:" in out
        out = run(str(SKILL / "scripts" / "generated_helper_scan.py"), str(root / "build" / "foo.lst"), str(root / "build" / "a.map"))
        assert "[listing]" in out

        out = run(str(SKILL / "scripts" / "z80_pattern_scan.py"), str(root / "build" / "gen.asm"))
        assert "[generated_asm]" in out

        # --- audit1: scanner semantics ---
        im2_only = root / "im2_only.asm"
        im2_only.write_text("  im 2\n  ld i,a\n  ret\n", encoding="ascii")
        out = run(str(SKILL / "scripts" / "z80_pattern_scan.py"), str(im2_only))
        assert "[im2-present]" in out
        assert "[im2-rom-hole-candidate]" not in out

        im2_rom = root / "im2_rom.asm"
        im2_rom.write_text("  ld a,$39\n  ld i,a\n  im 2\n  ret\n", encoding="ascii")
        out = run(str(SKILL / "scripts" / "z80_pattern_scan.py"), str(im2_rom))
        assert "[im2-rom-hole-candidate]" in out

        generic_inc = root / "generic_inc.asm"
        generic_inc.write_text("start:\n  inc d\n  inc h\n  ret\n", encoding="ascii")
        out = run(str(SKILL / "scripts" / "z80_pattern_scan.py"), str(generic_inc))
        assert "[next-line-ula]" not in out

        far_ula = root / "far_ula.asm"
        far_ula.write_text("  ld hl,$4000\n" + "  nop\n" * 20 + "  inc d\n  ret\n", encoding="ascii")
        out = run(str(SKILL / "scripts" / "z80_pattern_scan.py"), str(far_ula))
        assert "[next-line-ula]" not in out

        ula_ctx = root / "ula_ctx.asm"
        ula_ctx.write_text(
            "  ld hl,$4000\nupde:\n  inc d\n  ld a,d\n  and 7\n  ret nz\n  ret\n",
            encoding="ascii",
        )
        out = run(str(SKILL / "scripts" / "z80_pattern_scan.py"), str(ula_ctx))
        assert "[next-line-ula]" in out

        one_dec = root / "one_dec.asm"
        one_dec.write_text("  call dzx0_standard\n  ret\n", encoding="ascii")
        out = run(str(SKILL / "scripts" / "z80_pattern_scan.py"), str(one_dec))
        assert "[decoder-present]" in out
        assert "[multi-decoder-smell]" not in out

        two_dec = root / "two_dec"
        two_dec.mkdir()
        (two_dec / "a.asm").write_text("  call dzx0_standard\n  ret\n", encoding="ascii")
        (two_dec / "b.asm").write_text("  call deexo\n  ret\n", encoding="ascii")
        out = run(str(SKILL / "scripts" / "z80_pattern_scan.py"), str(two_dec))
        assert "[multi-decoder-smell]" in out

        # map matrix
        (root / "build" / "b.map").write_text(
            "__CODE_head = $C000 ;\n__CODE_tail = $C100 ;\n__BSS_tail = $C200 ;\n"
            "TAR__register_sp = $FF58 ;\n__BANK_1_head = $C000 ;\n"
            "__BANK_1_tail = $C080 ;\n",
            encoding="ascii",
        )
        out = run(str(SKILL / "scripts" / "map_summary.py"), str(root / "build"), "--all")
        assert "[target_row]" in out
        assert "[multi_map_matrix]" in out
        assert "paged_slot_or_high_ram" in out
        assert "bank_sections: 1" in out
        assert "bank_payload: 128" in out
        assert "BANK_1: head=$C000 tail=$C080 size=128" in out

        # docs: net domains + upde 15
        rep = (SKILL / "references" / "reporting.md").read_text(encoding="utf-8")
        assert "Net_storage" in rep and "Workspace/stack/BSS peak delta" in rep
        assert "Multi-Target Gate" in rep

        # --- P3: freshness per-unit + net checker ---
        (root / "pkg_a").mkdir()
        (root / "pkg_b").mkdir()
        (root / "pkg_a" / "Makefile").write_text("all:\n", encoding="ascii")
        (root / "pkg_b" / "Makefile").write_text("all:\n", encoding="ascii")
        (root / "pkg_a" / "a.c").write_text("int a(void){return 1;}\n", encoding="ascii")
        (root / "pkg_b" / "b.c").write_text("int b(void){return 2;}\n", encoding="ascii")
        (root / "pkg_a" / "a.map").write_text("__CODE_head = $8000 ;\n", encoding="ascii")
        base = time.time() - 100
        os.utime(root / "pkg_a" / "Makefile", (base, base))
        os.utime(root / "pkg_b" / "Makefile", (base, base))
        os.utime(root / "pkg_a" / "a.c", (base, base))
        os.utime(root / "pkg_a" / "a.map", (base + 10, base + 10))
        # Make only pkg_b source newer so global mode would stale pkg_a.
        (root / "pkg_b" / "b.c").write_text("int b(void){return 3;}\n", encoding="ascii")
        os.utime(root / "pkg_b" / "b.c", (base + 20, base + 20))
        out = run(str(SKILL / "scripts" / "artifact_freshness.py"), str(root), "--mode", "per-unit")
        assert "mode: per-unit" in out
        assert "[global_mode_info]" in out
        assert "pkg_a" in out and "FRESH" in out
        out = run(str(SKILL / "scripts" / "artifact_freshness.py"), str(root / "pkg_a"), "--mode", "per-unit")
        assert "verdict: FRESH" in out

        staged = root / "staged"
        staged.mkdir()
        staged_make = staged / "Makefile"
        staged_make.write_text("all:\n", encoding="ascii")
        staged_src = staged / "main.c"
        staged_map = staged / "main.map"
        staged_gen = staged / "generated.h"
        staged_ovl = staged / "overlay.ovl"
        staged_release = staged / "release"
        staged_release.mkdir()
        staged_asset = staged_release / "raw.bin"
        staged_src.write_text("int main(void){return 0;}\n", encoding="ascii")
        staged_map.write_text("__CODE_head = $8000 ;\n", encoding="ascii")
        staged_gen.write_text("/* AUTO-GENERATED -- DO NOT EDIT */\n", encoding="ascii")
        staged_ovl.write_bytes(b"OVL")
        staged_asset.write_bytes(b"ASSET")
        base_time = time.time() - 100
        for path, delta in ((staged_make, 0), (staged_src, 0), (staged_asset, 0), (staged_map, 10), (staged_gen, 20), (staged_ovl, 30)):
            os.utime(path, (base_time + delta, base_time + delta))
        out = run(str(SKILL / "scripts" / "artifact_freshness.py"), str(staged), "--mode", "per-unit", expect=1)
        assert "STAGED generated.h" in out and "verdict: STALE" in out
        assert "STALE main.map" in out and "FRESH overlay.ovl" in out
        out = run(str(SKILL / "scripts" / "artifact_freshness.py"), str(staged), "--mode", "global", expect=1)
        assert "verdict: STALE" in out

        out = run(
            str(SKILL / "scripts" / "net_compression_check.py"),
            "--original",
            "1000",
            "--packed",
            "400",
            "--decoder",
            "69",
            "--assets-sharing-decoder",
            "4",
            "--call-glue",
            "6",
            "--workspace",
            "256",
            "--workspace-mode",
            "reuse",
            "--pressure-target",
            "storage",
        )
        assert "Net_storage" in out
        assert "RAM_peak_delta" in out
        assert "claim_figure: Net_storage" in out
        # Conservative decoder share: ceil(69/4)=18.
        assert "Net_storage = 1000 - (400 + 18 + 6) = 576" in out
        assert "workspace reuse is not proven" in out
        out = run(
            str(SKILL / "scripts" / "net_compression_check.py"),
            "--original",
            "1000",
            "--packed",
            "400",
            "--decoder",
            "69",
            "--workspace",
            "256",
        )
        assert "workspace: 256 mode=exclusive" in out
        assert "RAM_peak_delta = 256 + 0 = 256" in out
        out = run(
            str(SKILL / "scripts" / "net_compression_check.py"),
            "--original",
            "100",
            "--packed",
            "50",
            "--decoder",
            "10",
            "--call-glue",
            "-1",
            expect=2,
        )
        assert "sizes must be non-negative" in out
        print("smoke ok")
        return 0
    finally:
        if str(root).startswith(tempfile.gettempdir()):
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
