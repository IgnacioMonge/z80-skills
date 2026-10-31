import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("asm_callgraph.py")


class AsmCallgraphTest(unittest.TestCase):
    def test_conditional_edges_use_real_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "target" / "project"
            root.mkdir(parents=True)
            (root / "demo.asm").write_text(
                "start:\n  call nz,target\n  jp c,done\n",
                encoding="utf-8",
            )
            (root / ".claude" / "worktrees" / "dup").mkdir(parents=True)
            (root / ".claude" / "worktrees" / "dup" / "ghost.asm").write_text(
                "ghost:\n  call phantom\n",
                encoding="utf-8",
            )
            out = subprocess.check_output(
                [sys.executable, str(MODULE), str(root)],
                text=True,
            )
            self.assertIn("start --call--> target", out)
            self.assertIn("start --jp--> done", out)
            self.assertNotIn("--call--> nz", out)
            self.assertNotIn("phantom", out)


if __name__ == "__main__":
    unittest.main()
