"""Reference models plus optional assembled nominal-Z80 example checks.

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

    def test_documented_page_history(self):
        text = (REFERENCES / "zx-spectrum-hardware.md").read_text(encoding="utf-8")
        blocks = re.findall(r"```python\n(.*?)\n```", text, re.S)
        example, = [block for block in blocks if block.startswith("# example: page-history\n")]
        exec(compile(example, "documented_page_history", "exec"), {})

    def run_example(self, name, prefix, suffix="", payload=b"", reference="loops-and-data.md"):
        text = (REFERENCES / reference).read_text(encoding="utf-8")
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
    def test_documented_predicate_contracts_and_chain_paths(self):
        entries = {
            "is_horizontal_space": ({9, 32}, lambda a: 18 if a == 32 else 29),
            "is_colon": ({58}, lambda a: 17),
            "is_delimiter": ({9, 32, 58}, lambda a: 46 if a == 32 else 57 if a == 9 else 78),
        }
        for entry, (matches, cost) in entries.items():
            with self.subTest(entry=entry):
                guard = 0xfefb if entry == "is_delimiter" else 0xfefd
                prefix = ["    ld sp,$ff00\n    ld a,$cc\n"
                          f"    ld ({guard}),a\n    ld ($ff00),a\n"]
                for a in range(256):
                    address = 0x8000 + 14 * a
                    # Exercise both initial Z states; the predicate must set its own result.
                    prefix.append(f"    ld hl,{a * 256 + (255 if a & 1 else 0)}\n"
                                  "    push hl\n    pop af\n"
                                  "    ld bc,$1234\n    ld de,$5678\n    ld hl,$9abc\n"
                                  "    ld ix,$1357\n    ld iy,$2468\n"
                                  f"    call {entry}\n")
                    for offset, register in enumerate(("bc", "de", "hl", "ix", "iy", "sp")):
                        prefix.append(f"    ld ({address + 2 * offset}),{register}\n")
                    prefix.append(f"    push af\n    pop hl\n    ld ({address + 12}),hl\n")
                prefix.append("    jp predicates_done\n")
                cycles, ram = self.run_example("delimiter-predicates", "".join(prefix),
                    "predicates_done:\n", reference="z80-techniques.md")
                for a in range(256):
                    record = ram[0x8000 + 14 * a:0x8000 + 14 * (a + 1)]
                    words = [int.from_bytes(record[i:i + 2], "little") for i in range(0, 14, 2)]
                    self.assertEqual(words[:6], [0x1234, 0x5678, 0x9abc, 0x1357, 0x2468, 0xff00], a)
                    self.assertEqual(words[6] >> 8, a)
                    self.assertEqual(bool(words[6] & 0x40), a in matches, a)
                self.assertEqual((ram[guard], ram[0xff00]), (0xcc, 0xcc))
                # Setup/snapshot/CALL cost is 259 T per input; guards and final JP add 53 T.
                self.assertEqual(cycles, 53 + sum(259 + cost(a) for a in range(256)))

    @unittest.skipUnless(ASSEMBLER and TICKS, "requires sjasmplus and z88dk-ticks on PATH")
    def test_documented_split_counter_visits_and_cycles(self):
        for encoded in (1, 255, 256, 257, 65535, 0):
            with self.subTest(encoded=encoded):
                n = encoded or 65536
                cycles, ram = self.run_example("split-counter", f"    ld de,{encoded}\n    ld hl,0\n",
                                            "    ld ($f000),hl\n")
                self.assertEqual(int.from_bytes(ram[0xf000:0xf002], "little"), n & 65535)
                self.assertEqual(cycles, 50 + 19 * n + 9 * ((n + 255) // 256))

    @unittest.skipUnless(ASSEMBLER and TICKS, "requires sjasmplus and z88dk-ticks on PATH")
    def test_documented_ldi_block_output_guards_and_cycles(self):
        for n in (16, 32, 256):
            with self.subTest(n=n):
                payload = bytes((i * 17 + 3) & 255 for i in range(n))
                cycles, ram = self.run_example("ldi-block",
                    f"    ld hl,$8000\n    ld de,$a000\n    ld bc,{n}\n", payload=payload)
                self.assertEqual(ram[0x9fff:0xa001 + n], b"\xcc" + payload + b"\xcc")
                self.assertEqual(cycles, 30 + 16 * n + 10 * (n // 16))

    @unittest.skipUnless(ASSEMBLER and TICKS, "requires sjasmplus and z88dk-ticks on PATH")
    def test_remainder_entry_copies_exact_length(self):
        for n in (1, 15, 17, 31, 257):
            with self.subTest(n=n):
                offset = 2 * (16 - ((n - 1) % 16 + 1))
                payload = bytes((i * 29 + 7) & 255 for i in range(n))
                cycles, ram = self.run_example("ldi-block",
                    f"    ld hl,$8000\n    ld de,$a000\n    ld bc,{n}\n"
                    f"    jp copy_loop+{offset}\n", payload=payload)
                self.assertEqual(ram[0x9fff:0xa001 + n], b"\xcc" + payload + b"\xcc")
                self.assertEqual(cycles, 40 + 16 * n + 10 * ((n + 15) // 16))


if __name__ == "__main__":
    unittest.main()
