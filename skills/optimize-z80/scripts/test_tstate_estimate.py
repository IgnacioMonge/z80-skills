import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tstate_estimate import clean, estimate

MODULE = Path(__file__).with_name("tstate_estimate.py")

class TstateEstimateTest(unittest.TestCase):
    def test_index_halves_and_sll_timings(self):
        cases = {"sll a": 8, "sll (hl)": 15, "sll (ix+1)": 23,
                 "sll (iy-2),b": 23, "ld h,(ix+1)": 19,
                 "ld (iy-2),l": 19, "out (c),0": 12}
        for pair in ("ix", "iy"):
            for half in (pair + "h", pair + "l"):
                for register in ("a", "b", "c", "d", "e", pair + "h", pair + "l"):
                    cases[f"ld {register},{half}"] = 8
                    cases[f"ld {half},{register}"] = 8
                for immediate in ("0", "$ff", "255", "limit-1"):
                    cases[f"ld {half},{immediate}"] = 11
                for op in ("inc", "dec"):
                    cases[f"{op} {half}"] = 8
                for op in ("add", "adc", "sbc", "sub", "and", "or", "xor", "cp"):
                    cases[f"{op} a,{half}"] = 8
                    cases[f"{op} {half}"] = 8
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(estimate(*clean(source)), expected)

    def test_unencodable_index_halves_and_sll_are_unknown(self):
        for source in ("ld ixh,iyl", "ld iyh,ixl", "ld h,ixh", "ld iyl,l",
                       "ld ixh,(hl)", "ld ixh,(ix+1)", "ld (iy+1),iyl",
                       "ld ixh,bc", "ld ixh,", "inc ixh,a", "add ixh,a",
                       "bit 0,ixh", "push iyl", "sll ixh", "sll (hl),a",
                       "sll a,b", "sll 3", "sll (ix+1),ixh"):
            with self.subTest(source=source):
                self.assertIsNone(estimate(*clean(source)))

    def test_annotation_audit_undocumented_timings(self):
        result = self.run_audit("ld a,ixh ; 8T\ninc iyl ; 8T\nsll a ; 8T\n")
        self.assertEqual(result.returncode, 0, result.stdout)
        result = self.run_audit("ld a,ixh ; 7T\ninc ixh ; 4T\nld ixh,iyl ; 8T\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout.count("mismatch:"), 2)
        self.assertIn("unknown:", result.stdout)

    def run_audit(self, source):
        with tempfile.TemporaryDirectory() as tmp:
            asm = Path(tmp) / "audit.asm"
            asm.write_text(source, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(MODULE), "--audit-annotations", str(asm)],
                text=True, capture_output=True,
            )

    def test_annotation_audit_fixed_match(self):
        result = self.run_audit("nop ; 4T\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("match", result.stdout)

    def test_annotation_audit_conditional_pair_and_partial(self):
        result = self.run_audit("jr nz,target ; 12/7T\njr z,target ; 7T\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("partial", result.stdout)

    def test_annotation_audit_named_forms_djnz_and_equal_jp(self):
        result = self.run_audit(
            "jr nz,target ; taken 12T, not-taken 7T\n"
            "jr z,target ; not-taken 7T, taken 12T\n"
            "djnz loop ; 13/8T\n"
            "jp nz,target ; 10T\n"
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.count("match:"), 4)

    def test_annotation_audit_named_semicolon_requires_units(self):
        result = self.run_audit("jr nz,target ; taken 12T; not-taken 7T\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("match", result.stdout)
        result = self.run_audit("jr nz,target ; taken 12T, not-taken 7\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown", result.stdout)

    def test_annotation_audit_swapped_wrong_unknown_fail(self):
        result = self.run_audit("jr nz,target ; 7/12T\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mismatch", result.stdout)
        result = self.run_audit("mystery ; 4T\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown", result.stdout)

    def test_legacy_invocation_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            asm = Path(tmp) / "legacy.asm"
            asm.write_text("nop ; 4T\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(MODULE), str(asm)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("estimated_static_tstates_single_pass: 4", result.stdout)
        self.assertNotIn("annotation_audit:", result.stdout)
    def test_distinguishes_common_ld_forms(self):
        with tempfile.TemporaryDirectory() as tmp:
            asm = Path(tmp) / "demo.asm"
            asm.write_text(
                "ld a,b\n"
                "ld a,(hl)\n"
                "ld a,(ix+1)\n"
                "ld sp,hl\n",
                encoding="utf-8",
            )
            out = subprocess.check_output([sys.executable, str(MODULE), str(asm)], text=True)
            self.assertIn("estimated_static_tstates_single_pass: 36", out)

    def test_corrects_indirect_indexed_and_repeat_timings(self):
        with tempfile.TemporaryDirectory() as tmp:
            asm = Path(tmp) / "timings.asm"
            asm.write_text(
                "jp (hl)\n"
                "ld hl,($1234)\n"
                "adc hl,bc\n"
                "bit 0,(hl)\n"
                "ex (sp),ix\n"
                "ldir\n",
                encoding="utf-8",
            )
            out = subprocess.check_output([sys.executable, str(MODULE), str(asm)], text=True)
            self.assertIn("estimated_static_tstates_single_pass: 86", out)
            self.assertIn("total=21*(iterations-1)+16", out)

    def test_index_stack_immediates_io_and_partial_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            asm = Path(tmp) / "forms.asm"
            asm.write_text(
                "push ix\n"
                "pop iy\n"
                "and $7f\n"
                "add a,1\n"
                "in a,(c)\n"
                "out (c),a\n"
                "ret nz\n"
                "ld a,i\n"
                "unknown_op\n",
                encoding="utf-8",
            )
            out = subprocess.check_output([sys.executable, str(MODULE), str(asm)], text=True)
            self.assertIn("estimated_static_tstates_single_pass: 87", out)
            self.assertIn("warning: total excludes unknown opcodes", out)

if __name__ == "__main__":
    unittest.main()
