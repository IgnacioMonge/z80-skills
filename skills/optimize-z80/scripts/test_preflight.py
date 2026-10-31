import json
import os
import subprocess
import sys
import tempfile
import time
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

    def test_freshness_ignores_listing_and_host_python_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "src" / "main.c"
            src.parent.mkdir(parents=True)
            src.write_text("int main(void) { return 0; }\n", encoding="utf-8")
            build_dir = root / "build"
            build_dir.mkdir()
            art = build_dir / "app.bin"
            art.write_bytes(b"\xc9")
            lst = root / "src" / "main.lst"
            lst.write_text("0000 C9 RET\n", encoding="utf-8")
            host_py = root / "tools" / "gen.py"
            host_py.parent.mkdir()
            host_py.write_text("print('helper')\n", encoding="utf-8")
            venv_c = root / ".venv" / "pkg" / "mod.c"
            venv_c.parent.mkdir(parents=True)
            venv_c.write_text("int ignored(void) { return 1; }\n", encoding="utf-8")

            now = time.time()
            os.utime(src, (now - 20, now - 20))
            os.utime(art, (now - 10, now - 10))
            os.utime(lst, (now, now))
            os.utime(host_py, (now, now))
            os.utime(venv_c, (now, now))

            data = json.loads(subprocess.check_output([sys.executable, str(MODULE), str(root), "--json"], text=True))
            self.assertEqual(data["freshness"]["status"], "mtime_fresh_or_unknown")
            self.assertEqual(data["freshness"]["newest_source"], "src/main.c")
            self.assertEqual(data["sources"][".c"], 1)

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
