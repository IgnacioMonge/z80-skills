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

    def test_map_hotspots_folds_local_labels_and_uses_section_tails(self):
        hotspots = Path(__file__).with_name("map_hotspots.py")
        with tempfile.TemporaryDirectory() as tmp:
            map_path = Path(tmp) / "game.map"
            map_path.write_text(
                "_first = $8000 ; addr, public, , m_c, code_compiler, m.c:1\n"
                "l_first_00101 = $8020 ; addr, local, , m_c, code_compiler, m.c:10\n"
                "_last_big = $8040 ; addr, public, , m_c, code_compiler, m.c:30\n"
                "l_last_big_00102 = $8080 ; addr, local, , m_c, code_compiler, m.c:50\n"
                "__code_compiler_tail = $8140 ; const, public, def, , ,\n",
                encoding="utf-8",
            )
            payload = json.loads(
                subprocess.check_output(
                    [sys.executable, str(hotspots), str(map_path), "--json"],
                    text=True,
                )
            )
            by_name = {row["name"]: row["size_est"] for row in payload["top"]}
            self.assertEqual(by_name, {"_last_big": 0x100, "_first": 0x40})

if __name__ == "__main__":
    unittest.main()
