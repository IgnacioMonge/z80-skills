import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("tstate_estimate.py")

class TstateEstimateTest(unittest.TestCase):
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
