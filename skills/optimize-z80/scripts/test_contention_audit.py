import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("contention_audit.py")

class ContentionAuditTest(unittest.TestCase):
    def test_parses_z88dk_and_generic_symbols(self):
        with tempfile.TemporaryDirectory() as tmp:
            mapfile = Path(tmp) / "demo.map"
            mapfile.write_text(
                "CODE:main:file.asm: draw = $4000 ; addr, local, , main, code_compiler\n"
                "logic = $9000 ; addr, public, , logic, code_compiler\n",
                encoding="utf-8",
            )
            out = subprocess.check_output([sys.executable, str(MODULE), str(mapfile), "--include-uncontended", "--model", "128k"], text=True)
            self.assertIn("contended_128k", out)
            self.assertIn("uncontended_128k", out)
            self.assertIn("SUMMARY model=128k", out)

    def test_banked_range_requires_page_and_uses_model_mapping(self):
        self.assertEqual(MODULE.exists(), True)
        with tempfile.TemporaryDirectory() as tmp:
            mapfile = Path(tmp) / "banked.map"
            mapfile.write_text("$C000 hot\n", encoding="utf-8")
            base = [sys.executable, str(MODULE), str(mapfile), "--include-uncontended"]
            unknown = subprocess.check_output(base + ["--model", "128k"], text=True)
            odd = subprocess.check_output(base + ["--model", "128k", "--page", "3"], text=True)
            plus3_low = subprocess.check_output(base + ["--model", "plus3", "--page", "3"], text=True)
            plus3_high = subprocess.check_output(base + ["--model", "plus3", "--page", "4"], text=True)
            self.assertIn("unknown_banked_128k", unknown)
            self.assertIn("contended_128k", odd)
            self.assertIn("uncontended_plus3", plus3_low)
            self.assertIn("contended_plus3", plus3_high)

    def test_default_is_conservative_and_missing_map_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            mapfile = Path(tmp) / "banked.map"
            mapfile.write_text("$C000 hot\n", encoding="utf-8")
            out = subprocess.check_output(
                [sys.executable, str(MODULE), str(mapfile), "--include-uncontended"],
                text=True,
            )
            self.assertIn("unknown_banked_auto", out)
            missing = subprocess.run(
                [sys.executable, str(MODULE), str(Path(tmp) / "missing.map")],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(missing.returncode, 0)

if __name__ == "__main__":
    unittest.main()
