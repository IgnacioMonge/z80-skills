"""Reference identities plus optional assembled nominal-Z80 loop checks.

Run with the host Python 3 interpreter. Assembly tests require sjasmplus and
z88dk-ticks on PATH; missing tools are reported as skips, never as passes.
"""
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REFERENCES = Path(__file__).resolve().parents[1] / "references"
ASSEMBLER = shutil.which("sjasmplus")
TICKS = shutil.which("z88dk-ticks")


class TechniqueExamplesTest(unittest.TestCase):
    def test_incremental_quotient_matches_direct_evaluation(self):
        for step in range(65):
            for denominator in range(1, 65):
                q = r = 0
                whole, fraction = divmod(step, denominator)
                for i in range(65):
                    self.assertEqual((q, r), divmod(i * step, denominator))
                    q += whole
                    r += fraction
                    if r >= denominator:
                        q += 1
                        r -= denominator

    def test_nibble_tables_and_unsigned_power_of_two_indexing(self):
        table = [bin(n).count("1") for n in range(16)]
        for value in range(256):
            self.assertEqual(table[value & 15] + table[value >> 4], bin(value).count("1"))
            for bits in range(9):
                self.assertEqual(value & ((1 << bits) - 1), value % (1 << bits))

    def test_sprite_phase_storage_and_compositor_specializations(self):
        # A 16-pixel row plus spill, with no row padding beyond its byte extent.
        storage = 0
        for shift in range(8):
            pixels = [0] * shift + [1] * 16
            rowsize = (len(pixels) + 7) // 8
            storage += 16 * rowsize
        self.assertEqual(storage, 368)
        self.assertEqual(2 * storage, 736)
        for background in range(256):
            self.assertEqual((background & 255) | 0, background)
            for image in range(256):
                self.assertEqual((background & 0) | image, image)

    def test_documented_screen_step(self):
        text = (REFERENCES / "zx-spectrum-hardware.md").read_text(encoding="utf-8")
        example = re.search(r"```python\n(.*?)\n```", text, re.S)
        self.assertIsNotNone(example)
        exec(compile(example.group(1), "documented_screen_step", "exec"), {})

    def run_loop(self, name, prefix, suffix="", payload=b""):
        text = (REFERENCES / "loops-and-data.md").read_text(encoding="utf-8")
        blocks = re.findall(r"```asm\n(.*?)\n```", text, re.S)
        body, = [block for block in blocks if block.startswith(f"; example: {name}\n")]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, binary, dump = (root / n for n in ("test.asm", "test.bin", "ram.bin"))
            source.write_text("    org 0\n" + prefix + body + "\n" + suffix + "    nop\n", encoding="utf-8")
            result = subprocess.run([ASSEMBLER, "--nologo", f"--raw={binary}", str(source)],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            code = binary.read_bytes()
            memory = bytearray(65536)
            memory[:len(code)] = code
            memory[0x8000:0x8000 + len(payload)] = payload
            memory[0x9fff:0xa001 + len(payload)] = b"\xcc" * (len(payload) + 2)
            binary.write_bytes(memory)
            result = subprocess.run(
                [TICKS, "-mz80", "-end", f"{len(code) - 1:x}", "-counter", "2000000",
                 "-output", str(dump), str(binary)],
                capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return int(result.stdout.strip()), dump.read_bytes()

    @unittest.skipUnless(ASSEMBLER and TICKS, "requires sjasmplus and z88dk-ticks on PATH")
    def test_documented_split_counter_visits_and_cycles(self):
        for encoded in (1, 255, 256, 257, 65535, 0):
            with self.subTest(encoded=encoded):
                n = encoded or 65536
                cycles, ram = self.run_loop("split-counter", f"    ld de,{encoded}\n    ld hl,0\n",
                                            "    ld ($f000),hl\n")
                self.assertEqual(int.from_bytes(ram[0xf000:0xf002], "little"), n & 65535)
                self.assertEqual(cycles, 50 + 19 * n + 9 * ((n + 255) // 256))

    @unittest.skipUnless(ASSEMBLER and TICKS, "requires sjasmplus and z88dk-ticks on PATH")
    def test_documented_ldi_block_output_guards_and_cycles(self):
        for n in (16, 32, 256):
            with self.subTest(n=n):
                payload = bytes((i * 17 + 3) & 255 for i in range(n))
                cycles, ram = self.run_loop("ldi-block",
                    f"    ld hl,$8000\n    ld de,$a000\n    ld bc,{n}\n", payload=payload)
                self.assertEqual(ram[0x9fff:0xa001 + n], b"\xcc" + payload + b"\xcc")
                self.assertEqual(cycles, 30 + 16 * n + 10 * (n // 16))

    @unittest.skipUnless(ASSEMBLER and TICKS, "requires sjasmplus and z88dk-ticks on PATH")
    def test_remainder_entry_copies_exact_length(self):
        for n in (1, 15, 17, 31, 257):
            with self.subTest(n=n):
                offset = 2 * (16 - ((n - 1) % 16 + 1))
                payload = bytes((i * 29 + 7) & 255 for i in range(n))
                cycles, ram = self.run_loop("ldi-block",
                    f"    ld hl,$8000\n    ld de,$a000\n    ld bc,{n}\n"
                    f"    jp copy_loop+{offset}\n", payload=payload)
                self.assertEqual(ram[0x9fff:0xa001 + n], b"\xcc" + payload + b"\xcc")
                self.assertEqual(cycles, 40 + 16 * n + 10 * ((n + 15) // 16))


if __name__ == "__main__":
    unittest.main()
