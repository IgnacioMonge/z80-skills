#!/usr/bin/env python3
"""Detector tests for craft_scan.py: every lead class has a positive and a trap."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "craft_scan.py"
SECTION_RE = re.compile(r"^\[([\w-]+)\] count=(\d+)$")

LOGIC_C = r"""
#include "logic.h"

struct pos { unsigned char x; unsigned char y; };

#define OWN_CALLEE __z88dk_callee

static void tick(void);
void negate(unsigned char a);

static unsigned char helper_add(unsigned char a, unsigned char b) { return a + b; }

static unsigned char fwd(unsigned char a, unsigned char b)
{
    return helper_add(a, b);
}

unsigned char fast_fwd(unsigned char a) __z88dk_fastcall
{
    return negate(a);
}

static void ptr_fwd(void) { tick(); }
static void (*const handlers[])(void) = { ptr_fwd };

/* see draw_cell */
static void orphan_static(void) { tick(); }

static void draw_cell(unsigned char x, unsigned char color) { negate(x + color); }
static void paint(unsigned char c) { negate(c); }

static unsigned char use_one(unsigned char used, unsigned char ignored) { return used; }
static void silenced(unsigned char x) { (void)x; tick(); }

static unsigned char twice(unsigned char v) { return v + v; }

static unsigned char macro_attr(unsigned char v) MACRO_FROM_HEADER
{
    return helper_add(v, v);
}

#if 0
#define ALIAS_OF_ORPHAN orphan_variant
#endif
static void orphan_variant(void) { tick(); }

unsigned char is_greater(unsigned char a, unsigned char b)
{
    return (a > b) ? 1 : 0;
}

unsigned char piece_value(unsigned char p)
{
    switch (p) {
    case 1: return 1;
    case 2: return 3;
    case 3: return 3;
    case 4: return 5;
    default: return 0;
    }
}

unsigned char piece_action(unsigned char p)
{
    switch (p) {
    case 1: tick(); break;
    case 2: negate(p); break;
    case 3: tick(); break;
    case 4: tick(); break;
    default: break;
    }
    return 0;
}

void show(struct pos p) { negate(p.x); }
void show_ptr(const struct pos *p) { negate(p->x); }

void loops(void)
{
    int k;
    unsigned char row;
    for (int i = 0; i < 8; i++) { negate(i); }
    for (unsigned char j = 0; j < 8; ++j) { negate(j); }
    for (k = 0; k < 1000; k++) { negate(k); }
    row = 0;
    row++; // increment row
    row++; // skip the sentinel slot so file zero stays free
    /* previously used a lookup table, now computed inline */
    /* Used to paint the logical cell; the legacy format stays readable. */
    // draw_cell(3, 7);
    // Draw the cell (row-major).
}

unsigned char sum_row(const unsigned char *r)
{
    unsigned char s = 0;
    unsigned char k;
    for (k = 0; k < 8; ++k) {
        if (r[k] > 2) { s += r[k]; } else { s -= 1; }
        if (r[k] == 7) { s ^= 3; }
    }
    return s;
}

unsigned char sum_col(const unsigned char *c)
{
    unsigned char t = 0;
    unsigned char m;
    for (m = 0; m < 8; ++m) {
        if (c[m] > 2) { t += c[m]; } else { t -= 1; }
        if (c[m] == 7) { t ^= 3; }
    }
    return t;
}

void hook_idle(void) { tick(); }

static void hidden_impl(unsigned char v) { negate(v); }
void public_face(unsigned char v) { hidden_impl(v); }

void naked_fill(void) __naked
{
#asm
    push hl
    ld a,0
    ld (de),a
    pop hl
    ret
#endasm
}

void hosts(void)
{
    puts_host("pool.ntp.org");
    puts_host("pool.ntp.org");
    puts_host("other");
}

void entry(unsigned char row)
{
    draw_cell(1, 7);
    draw_cell(2, 7);
    draw_cell(row, 7);
    paint(3);
    paint(4);
    use_one(1, 2);
    use_one(3, 4);
    silenced(1);
    twice(row);
    clamp7(row);
    macro_attr(row);
    public_face(row);
    fwd(1, 2);
    handlers[0]();
}

static void beep(unsigned char pitch) { negate(pitch); }
void chime(void) { beep(5); beep(5); beep(6); }
"""

ROUT_ASM = """\
    SECTION code_user
    PUBLIC _api_entry

_api_entry:
    jp real_entry

real_entry:
    push hl
    ld a,(de)
    inc de
    pop hl
    push bc
    ld b,4
    pop bc
    push de
    call helper
    pop de
    ret

zero_test:
    dec a
    or a
    jr z, done
    and $0f
    or a
    jr c, done
    cp 3
    or a
    jr z, done
done:
    ret

cp_zero:
    ld a,(hl)
    cp 0
    jr nz, cz_xor
    ld a,(de)
    cp 0
    jp pe, done
cz_xor: xor a

loop:
    ld b,8
loop_top:
    dec b
    jr nz, loop_top
    dec c
    jr nz, loop_top
    ret
    ld a,1
    ret

after_data:
    ret
table:
    defb 1,2,3

after_data2:
    jp done
    defb 4,5

const_arg_caller:
    ld a,5
    call set_ink
    ld a,5
    call set_ink
    ld a,2
    call set_paper
    ld a,3
    call set_paper
    call helper
    ret

set_ink:
    ld (ink),a
    ret
set_paper:
    ld (paper),a
    ret

helper:
    call real_entry
    ret

narrate:
    ld a,5              ; load 5 into a
    inc hl              ; increment hl
    ld (hl),a           ; mark square as attacked so the pruning skips it
    pop de              ; E = from, D = to
;   ld a,(hl)
;   inc hl
    ret

    IF 0
    ret
    ld a,9
    ENDIF

copy_pair:
    push hl
    pop de
    push af
    cp 3
    pop af
    ret
only_ret:
    ret

vectors:
    jp only_ret
    jp real_entry

IF FAST
fast_path:
    ret
ELSE
    nop
ENDIF
"""

COPY_A = """\
copy_a:
    ld b,16
copy_a_loop:
    ld a,(hl)
    xor $ff
    and $7f
    ld (de),a
    inc hl
    inc de
    djnz copy_a_loop
    ld a,b
    ret
"""

COPY_B = """\
copy_b:
    ld b,32
copy_b_loop:
    ld a,(hl)
    xor $fe
    and $3f
    ld (de),a
    inc hl
    inc de
    djnz copy_b_loop
    ld a,b
    ret
"""

BRANCH_C = r"""
void out_port(unsigned char port, unsigned char v);

static void hw_poke(unsigned char port, unsigned char v) { out_port(port, v); out_port(v, port); }
static void tone(unsigned char t) { hw_poke(t, t); }

void chirp(void) { tone(1); tone(1); }

#ifdef NEXT
#include "drv_next.c"
#else
#include "drv_esx.c"
#endif

void boot(void) { drv_init(1); drv_init(1); }

#ifdef HOST_TEST
static unsigned char host_stub(unsigned char v) { return v; }
#else
static void real_dead(unsigned char spare) { hw_poke(9, 9); }
void radio_save(void)
{
#ifndef NEXT
    tone(2);
#else
    hw_poke(4, 4);
#endif
}
#endif

#ifdef NEXT
void next_flash(unsigned char row)
#else
static void two_headers(unsigned char row)
#endif
{
    hw_poke(3, 1);
}
"""

TRAPS_ASM = """\
caller_a:
    ld bc,$1234
    out (c),a
    call port_user
    ld hl,$4000
    ld l,a
    call half_user
    ld a,7
    call writes_first
    ld c,2
    call link_add
    call fall_entry
    ret

caller_b:
    ld bc,$1234
    out (c),a
    call port_user
    ld hl,$4000
    ld l,a
    call half_user
    ld a,7
    call writes_first
    ld c,2
    call link_add
    call fall_entry
    ret

port_user:
    ld (port),bc
    ret

half_user:
    ld (ptr),hl
    ret

writes_first:
    ld a,(ptr)
    ld (count),a
    ret

link_chunk:
    ld de,buf
link_add:
    ld a,c
    ret

before_fall:
    ld a,1
fall_entry:
    jp port_user

djnz_trap:
    ld b,4
dt_loop:
    dec b
    jr nz, dt_loop
    ld a,c
    jr z, dt_out
dt_out:
    ret
"""

IO_ASM = """\
io_a:
    ld b,18
    in a,(c)
    call port_f
    ld ix,$5000
    call ix_user
    ret

io_b:
    ld b,18
    in a,(c)
    call port_f
    ld ix,$5000
    call ix_user
    ret

port_f:
    ld a,b
    ret

ix_user:
    ld a,(ix+0)
    ret

computed:
    ld hl,io_b
    jp (hl)
    ld a,1
    ret

colon_save:
    push bc
    ld a, 13 : call port_f
    pop bc
    ret
"""

IF_ASM = """\
    IF FAST
arm_a:
    push hl
    ld a,(de)
    pop hl
    ret
    ELSE
arm_b:
    push hl
    ENDIF
    pop hl
    ret
"""

MAP = """\
_sum_row                        = $8000 ; addr, public, , logic_c, code_compiler, logic.c:90
_sum_col                        = $8100 ; addr, public, , logic_c, code_compiler, logic.c:101
_loops                          = $8120 ; addr, public, , logic_c, code_compiler, logic.c:72
_is_greater                     = $8150 ; addr, public, , logic_c, code_compiler, logic.c:34
_twice                          = $8158 ; addr, local, , logic_c, code_compiler, logic.c:32
_end_mark                       = $8160 ; addr, public, , logic_c, code_compiler, logic.c:200
"""


TAIL_MAP = """\
_twice                          = $8000 ; addr, local, , logic_c, code_compiler, logic.c:32
_is_greater                     = $8008 ; addr, public, , logic_c, code_compiler, logic.c:34
_is_greater_alias               = $8008 ; addr, public, , logic_c, code_compiler, logic.c:34
_loops                          = $8010 ; addr, public, , logic_c, code_compiler, logic.c:72
_sum_row                        = $8020 ; addr, public, , logic_c, code_compiler, logic.c:90
__code_compiler_tail            = $8120 ; const, public, def, , ,
"""


def sections(output: str) -> dict[str, str]:
    found: dict[str, str] = {}
    key = None
    for line in output.splitlines():
        match = SECTION_RE.match(line)
        if match:
            key = match.group(1)
            found[key] = line + "\n"
        elif key is not None:
            if not line.strip():
                key = None
            else:
                found[key] += line + "\n"
    return found


class CraftScanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.mkdtemp()
        root = Path(cls.tmp)
        (root / "src").mkdir()
        (root / "asm" / "ovl_a").mkdir(parents=True)
        (root / "asm" / "ovl_b").mkdir(parents=True)
        (root / "build").mkdir()
        (root / "src" / "logic.h").write_text(
            "void negate(unsigned char a);\n"
            "static unsigned char clamp7(unsigned char v) { return v > 7 ? 7 : v; }\n",
            encoding="utf-8",
        )
        (root / "src" / "logic.c").write_text(LOGIC_C, encoding="utf-8")
        (root / "src" / "branch.c").write_text(BRANCH_C, encoding="utf-8")
        (root / "src" / "drv_esx.c").write_text(
            "static void drv_init(unsigned char mode) { out_port(mode, 0); }\n", encoding="utf-8")
        (root / "asm" / "rout.asm").write_text(ROUT_ASM, encoding="utf-8")
        (root / "asm" / "traps.asm").write_text(TRAPS_ASM, encoding="utf-8")
        (root / "asm" / "io.asm").write_text(IO_ASM, encoding="utf-8")
        (root / "asm" / "arms.asm").write_text(IF_ASM, encoding="utf-8")
        (root / "src" / "main_build.c.asm").write_text(
            ";\tReconstructed for z80 Module Assembler\n_gen:\n    push hl\n    ld a,(de)\n    pop hl\n    ret\n",
            encoding="utf-8")
        (root / "asm" / "ovl_a" / "copy.asm").write_text(COPY_A, encoding="utf-8")
        (root / "asm" / "ovl_b" / "copy.asm").write_text(COPY_B, encoding="utf-8")
        (root / "build" / "app.map").write_text(MAP, encoding="utf-8")
        cls.root = root
        cls.out = cls.run_scan(root, "--map", str(root / "build" / "app.map"))
        cls.sec = sections(cls.out)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @staticmethod
    def run_scan(*args: object) -> str:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            text=True, capture_output=True, check=True,
        )
        return proc.stdout.replace("\\", "/")

    def section(self, key: str) -> str:
        self.assertIn(key, self.sec, f"missing section [{key}]\n{self.out}")
        return self.sec[key]

    def test_every_section_is_printed(self) -> None:
        for key in (
            "c-forwarder", "c-trivial-single-use", "c-constant-argument",
            "c-unused-parameter", "c-codegen-outlier", "asm-forwarder",
            "asm-push-pop-unclobbered", "asm-jump-to-ret", "asm-constant-register-arg",
            "c-clone-family", "asm-clone-family", "comment-narration", "comment-history",
            "hotspots", "summary",
        ):
            self.section(key)

    def test_c_forwarder_skips_abi_bridge_and_address_taken(self) -> None:
        text = self.section("c-forwarder")
        self.assertIn("fwd", text)
        self.assertNotIn("fast_fwd", text)
        self.assertNotIn("ptr_fwd", text)

    def test_constant_argument_needs_every_site(self) -> None:
        text = self.section("c-constant-argument")
        self.assertIn("draw_cell", text)
        self.assertIn("color", text)
        self.assertNotIn("paint", text)

    def test_unused_parameter_skips_void_cast(self) -> None:
        text = self.section("c-unused-parameter")
        self.assertIn("ignored", text)
        self.assertNotIn("silenced", text)

    def test_trivial_single_use(self) -> None:
        text = self.section("c-trivial-single-use")
        self.assertIn("twice", text)
        self.assertNotIn("draw_cell", text)

    def test_map_codegen_outlier(self) -> None:
        text = self.section("c-codegen-outlier")
        self.assertIn("sum_row", text)
        self.assertIn("bytes=256", text)
        self.assertNotIn("sum_col", text)
        self.assertNotIn("loops", text)
        self.assertIn("map: fresh", self.out)

    def test_last_symbol_ends_at_section_tail(self) -> None:
        tail_map = self.root / "build" / "tail.map"
        tail_map.write_text(TAIL_MAP, encoding="utf-8")
        try:
            out = self.run_scan(self.root, "--map", tail_map)
        finally:
            tail_map.unlink()
        self.assertIn("sum_row  # bytes=256", sections(out)["c-codegen-outlier"])

    def test_public_wrapper_over_static_is_not_a_forwarder(self) -> None:
        self.assertNotIn("public_face", self.section("c-forwarder"))

    def test_stale_map_is_needs_build(self) -> None:
        source = self.root / "src" / "logic.c"
        map_path = self.root / "build" / "app.map"
        old = time.time() - 1000
        os.utime(map_path, (old, old))
        try:
            out = self.run_scan(self.root, "--map", map_path)
        finally:
            os.utime(map_path, None)
            os.utime(source, None)
        self.assertIn("STALE", out)
        self.assertIn("NEEDS BUILD", sections(out)["c-codegen-outlier"])

    def test_asm_forwarder(self) -> None:
        text = self.section("asm-forwarder")
        self.assertIn("_api_entry", text)
        self.assertIn("helper", text)

    def test_push_pop_unclobbered(self) -> None:
        text = self.section("asm-push-pop-unclobbered")
        self.assertIn("rout.asm:8:", text)
        self.assertNotIn("rout.asm:12:", text)
        self.assertNotIn("rout.asm:15:", text)
        self.assertNotIn("push af", text)

    def test_directives_are_not_labels(self) -> None:
        self.assertNotIn("ELSE", self.out)

    def test_inline_asm_in_c_is_scanned(self) -> None:
        self.assertIn("logic.c:", self.section("asm-push-pop-unclobbered"))

    def test_macro_attribute_keeps_later_functions(self) -> None:
        self.assertNotIn("macro_attr", self.section("c-forwarder"))
        # the call sites live in entry(), parsed after the macro attribute
        self.assertIn("draw_cell", self.section("c-constant-argument"))

    def test_extern_hook_is_not_a_forwarder(self) -> None:
        self.assertNotIn("hook_idle", self.section("c-forwarder"))

    def test_else_branch_is_scanned(self) -> None:
        unused = self.section("c-unused-parameter")
        self.assertIn("real_dead(spare)", unused)
        # one function with two headers is reported once, under the first-pass name
        self.assertIn("next_flash(row)", unused)
        self.assertNotIn("two_headers", unused)
        constant = self.section("c-constant-argument")
        # tone(2) sits in the first arm of a nested #if that neither pass parses: it still pins tone
        self.assertNotIn("tone(", constant)
        # a static function reached through an #include in the #else branch
        self.assertIn("drv_init(mode)", constant)

    def test_port_reads_and_index_sizes(self) -> None:
        text = self.section("asm-constant-register-arg")
        self.assertNotIn("port_f", text)  # in a,(c) reads B as the port high byte
        self.assertIn("ix_user(ix)  # all 2 entry sites load ix=$5000: load once inside, about 4 bytes", text)

    def test_compiler_output_is_not_reviewed(self) -> None:
        self.assertNotIn("main_build.c.asm", self.out)

    def test_colon_separated_statements(self) -> None:
        # sjasmplus: the call after ':' clobbers BC, so the save is needed
        self.assertNotIn("io.asm", self.section("asm-push-pop-unclobbered"))

    def test_conditional_arms_are_scanned(self) -> None:
        text = self.section("asm-push-pop-unclobbered")
        self.assertIn("arms.asm:3:", text)
        self.assertNotIn("arms.asm:9:", text)  # the pop sits after ENDIF

    def test_register_argument_traps(self) -> None:
        text = self.section("asm-constant-register-arg")
        for name in ("port_user", "half_user", "writes_first", "link_add"):
            self.assertNotIn(name, text)

    def test_fallthrough_and_flag_traps(self) -> None:
        self.assertNotIn("fall_entry", self.section("asm-forwarder"))

    def test_jump_to_ret(self) -> None:
        text = self.section("asm-jump-to-ret")
        self.assertIn("rout.asm:23:", text)
        self.assertIn("jp pe,done", text)
        self.assertNotIn("rout.asm:46:", text)
        self.assertNotIn("jp only_ret", text)

    def test_constant_register_arg(self) -> None:
        text = self.section("asm-constant-register-arg")
        self.assertIn("set_ink", text)
        self.assertNotIn("set_paper", text)

    def test_clone_families_cross_dirs(self) -> None:
        c_text = self.section("c-clone-family")
        self.assertIn("sum_row", c_text)
        self.assertIn("sum_col", c_text)
        self.assertNotIn("piece_value", c_text)
        asm_text = self.section("asm-clone-family")
        self.assertIn("copy_a", asm_text)
        self.assertIn("copy_b", asm_text)
        self.assertIn("spans directories: asm/ovl_a, asm/ovl_b", asm_text)

    def test_comment_leads(self) -> None:
        narration = self.section("comment-narration")
        self.assertIn("increment row", narration)
        self.assertIn("load 5 into a", narration)
        self.assertIn("increment hl", narration)
        self.assertNotIn("sentinel", narration)
        self.assertNotIn("pruning", narration)
        self.assertNotIn("E = from", narration)
        history = self.section("comment-history")
        self.assertIn("previously", history)
        self.assertNotIn("Used to paint", history)

    def test_hotspots_and_summary(self) -> None:
        self.assertIn("logic.c", self.section("hotspots"))
        summary = self.section("summary")
        self.assertIn("c_functions:", summary)
        self.assertIn("asm_routines:", summary)

    def test_single_file_target_keeps_project_context(self) -> None:
        out = self.run_scan(self.root / "src" / "logic.c", "--context", self.root)
        sec = sections(out)
        self.assertNotIn("rout.asm", sec["asm-forwarder"])
        self.assertIn("draw_cell", sec["c-constant-argument"])

    @unittest.skipUnless(shutil.which("git"), "git not available")
    def test_changed_from_limits_to_changed_lines(self) -> None:
        repo = Path(tempfile.mkdtemp())
        try:
            shutil.copytree(self.root / "src", repo / "src")
            git = ["git", "-C", str(repo)]
            subprocess.run([*git, "init", "-q"], check=True)
            subprocess.run([*git, "add", "."], check=True)
            subprocess.run(
                [*git, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base"],
                check=True,
            )
            logic = repo / "src" / "logic.c"
            logic.write_text(
                logic.read_text(encoding="utf-8").replace(" beep(6);", "").replace("/* see draw_cell */\n", "")
                + "\nstatic unsigned char fresh_fwd(unsigned char a, unsigned char b)\n"
                "{\n    return helper_add(a, b);\n}\n"
                "void late(void) { fresh_fwd(1, 2); fresh_fwd(3, 4); }\n",
                encoding="utf-8",
            )
            out = self.run_scan(repo, "--changed-from", "HEAD", "--churn", "5")
        finally:
            shutil.rmtree(repo, ignore_errors=True)
        sec = sections(out)
        self.assertIn("fresh_fwd", sec["c-forwarder"])
        self.assertNotIn(" fwd", sec["c-forwarder"])
        # deleting a comment that names draw_cell does not revive its unchanged lead
        self.assertNotIn("draw_cell", sec["c-constant-argument"])
        # deleting the only varying call creates the lead although the definition is untouched
        self.assertIn("beep(pitch)", sec["c-constant-argument"])
        self.assertIn("changed-from HEAD", out)
        self.assertRegex(sec["summary"], r"changed_code_lines: c=[1-9]\d* ")
        self.assertIn("commits=", sec["hotspots"])


if __name__ == "__main__":
    unittest.main()
