#!/usr/bin/env python3
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "skills" / "workflow"
GROK_INSTALLER = ROOT / "scripts" / "install-for-grok.ps1"


class WorkflowContextEfficiencyTest(unittest.TestCase):
    def test_main_does_not_duplicate_delegated_operations(self) -> None:
        skill = (WORKFLOW / "SKILL.md").read_text(encoding="utf-8")
        heavy = (WORKFLOW / "references" / "heavy.md").read_text(
            encoding="utf-8"
        )
        for text in (skill, heavy):
            self.assertIn("Do not duplicate delegated discovery", text)
            self.assertIn("unassigned architecture, contract, and", text)

    def test_routine_repairs_bypass_the_main_thread(self) -> None:
        heavy = (WORKFLOW / "references" / "heavy.md").read_text(
            encoding="utf-8"
        )
        normalized = " ".join(heavy.split())
        self.assertIn("## Direct repair loop", heavy)
        self.assertIn("each other's canonical task names", normalized)
        self.assertIn("must not relay or rediagnose", normalized)
        self.assertIn("after two focused repair attempts", normalized)

    def test_upward_reports_are_bounded_knowledge_deltas(self) -> None:
        roles = (WORKFLOW / "references" / "roles.md").read_text(
            encoding="utf-8"
        )
        heavy = (WORKFLOW / "references" / "heavy.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("within 250 words", roles)
        self.assertIn("Decision required: none", roles)
        self.assertIn("raw logs, large diffs, diagnostics", roles)
        self.assertIn("## Layered evidence", heavy)

    def test_grok_workflow_has_no_forked_markdown(self) -> None:
        overlay = ROOT / "scripts" / "grok-overlay" / "workflow"
        self.assertFalse(overlay.exists() and any(overlay.rglob("*.md")))
        installer = GROK_INSTALLER.read_text(encoding="utf-8")
        self.assertIn("Patch-WorkflowForGrok", installer)
        self.assertNotIn("Apply-WorkflowOverlay", installer)

    def test_grok_install_preserves_canonical_efficiency_contract(self) -> None:
        shell = shutil.which("pwsh") or shutil.which("powershell")
        if shell is None:
            self.skipTest("PowerShell is unavailable")

        with tempfile.TemporaryDirectory(prefix="z80-grok-install-") as raw_tmp:
            destination = Path(raw_tmp) / "skills"
            result = subprocess.run(
                [
                    shell,
                    "-NoProfile",
                    "-File",
                    str(GROK_INSTALLER),
                    "-Dest",
                    str(destination),
                    "-SkipBackup",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            installed = destination / "workflow"
            self.assertTrue((destination / "route-z80" / "SKILL.md").is_file())
            skill = (installed / "SKILL.md").read_text(encoding="utf-8")
            medium = (installed / "references" / "medium.md").read_text(
                encoding="utf-8"
            )
            heavy = (installed / "references" / "heavy.md").read_text(
                encoding="utf-8"
            )
            roles = (installed / "references" / "roles.md").read_text(
                encoding="utf-8"
            )

            self.assertIn("Host runtime (Grok Build)", skill)
            self.assertIn("spawn_subagent", roles)
            for text in (skill, heavy):
                self.assertIn("Do not duplicate delegated discovery", text)
            self.assertIn("## Direct repair loop", heavy)
            self.assertIn("within 250 words", roles)
            self.assertEqual(
                medium,
                (WORKFLOW / "references" / "medium.md").read_text(
                    encoding="utf-8"
                ),
            )

        installer = GROK_INSTALLER.read_text(encoding="utf-8")
        self.assertIn('"route-z80"', installer)
        self.assertIn("foreach ($name in $SkillNames)", installer)


if __name__ == "__main__":
    unittest.main()
