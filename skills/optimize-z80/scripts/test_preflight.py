import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("preflight.py")

class PreflightTest(unittest.TestCase):
    def test_detects_abi_and_toolchain_hints(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "main.c").write_text(
                "#pragma output CRT_ORG_CODE = 32768\n"
                "int __z88dk_fastcall foo(int a) { return a; }\n"
                "void bar(void) __naked;\n",
                encoding="utf-8",
            )
            data = json.loads(subprocess.check_output([sys.executable, str(MODULE), str(root), "--json"], text=True))
            self.assertIn("custom-abi", data["abi_hints"])
            self.assertIn("fastcall", data["abi_hints"])
            self.assertIn("naked", data["abi_hints"])
            self.assertIn("z88dk", data["toolchain_hints"])

if __name__ == "__main__":
    unittest.main()
