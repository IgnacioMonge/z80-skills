#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).with_name("run_in_worktree.py")


class RunInWorktreeTest(unittest.TestCase):
    def test_all_runner_backed_skills_require_the_shared_runner(self) -> None:
        root = RUNNER.parents[1]
        for skill in ("audit-z80", "shrink-z80", "optimize-z80"):
            contract = (
                root / "skills" / skill / "references" / "hard-contract.md"
            ).read_text(encoding="utf-8")
            self.assertIn("scripts/run_in_worktree.py", contract)
            self.assertIn("Never pass the temporary directory as a wrapper `cwd`", contract)

    def test_gate_runs_only_in_distinct_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            primary = Path(tmp) / "primary"
            worktree = Path(tmp) / "worktree"
            primary.mkdir()
            subprocess.run(["git", "init", "-q", str(primary)], check=True)
            subprocess.run(["git", "-C", str(primary), "config", "user.name", "test"], check=True)
            subprocess.run(
                ["git", "-C", str(primary), "config", "user.email", "test@example.com"],
                check=True,
            )
            (primary / "tracked.txt").write_text("tracked\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(primary), "add", "tracked.txt"], check=True)
            subprocess.run(
                ["git", "-C", str(primary), "commit", "-qm", "fixture"], check=True
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(primary),
                    "worktree",
                    "add",
                    "--detach",
                    str(worktree),
                    "HEAD",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
            )

            command = [
                sys.executable,
                str(RUNNER),
                "--primary",
                str(primary),
                "--worktree",
                str(worktree),
                "--",
                sys.executable,
                "-c",
                "import subprocess; from pathlib import Path; "
                "top = Path(subprocess.check_output("
                "['git', 'rev-parse', '--show-toplevel'], text=True).strip()).resolve(); "
                "assert top == Path.cwd(); Path('gate-ran').write_text('ok')",
            ]
            hostile_env = os.environ.copy()
            hostile_env.update(
                {
                    "PWD": str(primary),
                    "GIT_DIR": str(primary / ".git"),
                    "GIT_WORK_TREE": str(primary),
                }
            )
            self.assertEqual(
                subprocess.run(command, cwd=primary, env=hostile_env).returncode,
                0,
            )
            self.assertTrue((worktree / "gate-ran").is_file())
            self.assertFalse((primary / "gate-ran").exists())

            command[command.index(str(worktree))] = str(primary)
            command[-1] = (
                "from pathlib import Path; "
                "Path('primary-contaminated').write_text('bad')"
            )
            self.assertNotEqual(
                subprocess.run(
                    command,
                    cwd=primary,
                    env=hostile_env,
                    capture_output=True,
                ).returncode,
                0,
            )
            self.assertFalse((primary / "primary-contaminated").exists())


if __name__ == "__main__":
    unittest.main()
