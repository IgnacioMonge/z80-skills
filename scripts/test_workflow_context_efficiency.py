#!/usr/bin/env python3
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "skills" / "workflow"
GROK_INSTALLER = ROOT / "scripts" / "install-for-grok.ps1"


class WorkflowContextEfficiencyTest(unittest.TestCase):
    def test_heavy_policy_is_loaded_from_one_owner(self) -> None:
        skill = (WORKFLOW / "SKILL.md").read_text(encoding="utf-8")
        heavy = (WORKFLOW / "references" / "heavy.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("references/heavy.md", skill)
        self.assertIn("Do not duplicate delegated discovery", heavy)
        self.assertIn("unassigned architecture, contract, and", heavy)
        self.assertNotIn("## Dispatch gate", skill)

    def test_mutation_classes_have_one_definition_and_linked_consumers(self) -> None:
        skill = WORKFLOW / "SKILL.md"
        definitions = {}
        for path in WORKFLOW.rglob("*.md"):
            for name in re.findall(r"^- \*\*([^*]+):\*\*", path.read_text(encoding="utf-8"), re.MULTILINE):
                if name in {"primary-tree read-only", "disposable-worktree-only", "authorized primary-tree mutation"}:
                    definitions.setdefault(name, []).append(path)
        self.assertEqual(len(definitions), 3)
        self.assertTrue(all(paths == [skill] for paths in definitions.values()))
        for name in ("medium", "heavy", "roles"):
            path = WORKFLOW / "references" / f"{name}.md"
            self.assertIn("../SKILL.md", path.read_text(encoding="utf-8"))

    def test_frequent_entrypoints_stay_bounded(self) -> None:
        # Words bound authored context size; actual model tokens are measured by evals.
        for name in ("workflow", "route-z80"):
            text = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertLessEqual(len(text.split()), 650, name)

    def test_routine_repairs_bypass_the_main_thread(self) -> None:
        heavy = (WORKFLOW / "references" / "heavy.md").read_text(
            encoding="utf-8"
        )
        normalized = " ".join(heavy.split())
        self.assertIn("## Direct repair loop", heavy)
        self.assertIn("each other's canonical task names", normalized)
        self.assertIn("must not relay or rediagnose", normalized)
        self.assertIn("after two focused repair attempts", normalized)
        self.assertIn("without editing files or weakening assertions", normalized)
        self.assertIn("repairs also belong to the implementer", normalized)

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
            installed_document = (
                destination / "document-z80" / "SKILL.md"
            ).read_text(encoding="utf-8")
            self.assertIn("~/.grok/skills/workflow/SKILL.md", installed_document)
            self.assertIn("## Runtime Portability", installed_document)
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
            self.assertIn("references/heavy.md", skill)
            self.assertIn("Do not duplicate delegated discovery", heavy)
            self.assertIn("without editing files or weakening assertions", " ".join(heavy.split()))
            self.assertIn("## Direct repair loop", heavy)
            self.assertIn("within 250 words", roles)
            for text in (skill, heavy, roles):
                self.assertNotIn("sol_executor", text)
                self.assertNotIn("gpt-", text)
            self.assertIn("Workers must not spawn children", roles)
            self.assertIn("supported models and reasoning controls", roles)
            canonical_roles = (WORKFLOW / "references" / "roles.md").read_text(
                encoding="utf-8"
            )
            self.assertEqual(
                roles.split("## Capsule contracts", 1)[1],
                canonical_roles.split("## Capsule contracts", 1)[1],
            )
            self.assertEqual(
                medium,
                (WORKFLOW / "references" / "medium.md").read_text(
                    encoding="utf-8"
                ),
            )
            # Conditional verification rules must remain reachable and intact
            # after installation, just like the execution-level references.
            reference = "references/verification.md"
            for entrypoint in (WORKFLOW / "SKILL.md", installed / "SKILL.md"):
                links = re.findall(
                    r"\]\(([^)]+)\)", entrypoint.read_text(encoding="utf-8")
                )
                self.assertIn(reference, links)
                self.assertTrue((entrypoint.parent / reference).is_file())
            self.assertEqual(
                (installed / reference).read_bytes(),
                (WORKFLOW / reference).read_bytes(),
            )
            for name in ("audit-z80", "shrink-z80", "optimize-z80"):
                relative = Path(name) / "references" / "external-research.md"
                source = ROOT / "skills" / relative
                copied = destination / relative
                self.assertEqual(source.read_bytes(), copied.read_bytes())
                links = re.findall(r"\]\(([^)]*research-method\.md)\)", copied.read_text())
                self.assertEqual(len(links), 1)
                self.assertEqual(
                    (source.parent / links[0]).read_bytes(),
                    (copied.parent / links[0]).read_bytes(),
                )

        installer = GROK_INSTALLER.read_text(encoding="utf-8")
        self.assertIn('"route-z80"', installer)
        self.assertIn("foreach ($name in $SkillNames)", installer)


if __name__ == "__main__":
    unittest.main()
