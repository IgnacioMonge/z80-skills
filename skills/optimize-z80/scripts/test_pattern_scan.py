import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("pattern_scan.py")

class PatternScanTest(unittest.TestCase):
    def test_detects_abi_and_hardware_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "demo.c").write_text(
                "#pragma output CRT_ORG_CODE = 32768\n"
                "void __z88dk_fastcall foo(unsigned char a) { __asm\nout (254), a\n__endasm; }\n",
                encoding="utf-8",
            )
            out = subprocess.check_output([sys.executable, str(MODULE), str(root), "--limit-total", "20"], text=True)
            self.assertIn("c_fastcall", out)
            self.assertIn("c_pragma_output", out)
            self.assertIn("asm_border_beeper", out)

if __name__ == "__main__":
    unittest.main()
