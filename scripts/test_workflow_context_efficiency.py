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
        heavy = (WORKFLOW / "references" / "heavy.md").read_text(encoding="utf-8")
        self.assertIn("references/heavy.md", skill)
        self.assertIn("Do not duplicate delegated discovery", heavy)
        self.assertIn("unassigned architecture, contract, and", heavy)
        self.assertNotIn("## Dispatch gate", skill)

    def test_mutation_classes_have_one_definition_and_linked_consumers(self) -> None:
        skill = WORKFLOW / "SKILL.md"
        definitions = {}
        for path in WORKFLOW.rglob("*.md"):
            for name in re.findall(
                r"^- \*\*([^*]+):\*\*", path.read_text(encoding="utf-8"), re.MULTILINE
            ):
                if name in {
                    "primary-tree read-only",
                    "disposable-worktree-only",
                    "authorized primary-tree mutation",
                }:
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
        heavy = (WORKFLOW / "references" / "heavy.md").read_text(encoding="utf-8")
        normalized = " ".join(heavy.split())
        self.assertIn("## Direct repair loop", heavy)
        self.assertIn("each other's canonical task names", normalized)
        self.assertIn("must not relay or rediagnose", normalized)
        self.assertIn("after two focused repair attempts", normalized)
        self.assertIn("without editing files or weakening assertions", normalized)
        self.assertIn("repairs also belong to the implementer", normalized)

    def test_upward_reports_are_bounded_knowledge_deltas(self) -> None:
        roles = (WORKFLOW / "references" / "roles.md").read_text(encoding="utf-8")
        heavy = (WORKFLOW / "references" / "heavy.md").read_text(encoding="utf-8")
        self.assertIn("within 250 words", roles)
        self.assertIn("Decision required: none", roles)
        self.assertIn("raw logs, large diffs, diagnostics", roles)
        self.assertIn("## Layered evidence", heavy)

    def test_worker_reports_use_a_closed_status_set(self) -> None:
        roles = (WORKFLOW / "references" / "roles.md").read_text(encoding="utf-8")
        normalized = " ".join(roles.split())
        for status in ("DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED"):
            self.assertIn(f"- `{status}`:", roles)
        self.assertIn("never resend it unchanged", normalized)

    def test_verifier_triages_findings_without_prejudgment(self) -> None:
        roles = (WORKFLOW / "references" / "roles.md").read_text(encoding="utf-8")
        heavy = (WORKFLOW / "references" / "heavy.md").read_text(encoding="utf-8")
        roles = " ".join(roles.split())
        self.assertIn("as unverified claims", roles)
        self.assertIn("missing, extra, or misunderstood", roles)
        self.assertIn("Only blocking findings enter the repair loop", roles)
        self.assertIn("never pre-judge findings", " ".join(heavy.split()))

    def test_heavy_batches_resumes_and_recovers_without_status_files(self) -> None:
        heavy = (WORKFLOW / "references" / "heavy.md").read_text(encoding="utf-8")
        normalized = " ".join(heavy.split())
        self.assertIn("same-shape mechanical edits", normalized)
        self.assertIn("## Waiting, resumption, and recovery", heavy)
        self.assertIn("bounded stretches", normalized)
        self.assertIn("Resume an existing worker", normalized)
        self.assertIn("Never re-dispatch work", normalized)
        self.assertIn("needs no status files", normalized)

    def test_completion_maps_criteria_and_surfaces_decisions(self) -> None:
        references = WORKFLOW / "references"
        verification = (references / "verification.md").read_text(encoding="utf-8")
        self.assertIn(
            "map every acceptance criterion to observed evidence",
            " ".join(verification.split()),
        )
        for name in ("heavy", "medium"):
            text = (references / f"{name}.md").read_text(encoding="utf-8")
            self.assertIn("decision made on the user's behalf", " ".join(text.split()))

    def test_grok_workflow_has_no_forked_markdown(self) -> None:
        overlay = ROOT / "scripts" / "grok-overlay" / "workflow"
        self.assertFalse(overlay.exists() and any(overlay.rglob("*.md")))
        installer = GROK_INSTALLER.read_text(encoding="utf-8")
        self.assertIn("Set-GrokSkillsPath", installer)
        self.assertNotIn("Patch-WorkflowForGrok", installer)
        self.assertNotIn("Apply-WorkflowOverlay", installer)
        self.assertNotIn("Copy-SkillTree", installer)

    def test_grok_install_points_at_canonical_skills_and_removes_copies(self) -> None:
        shell = shutil.which("pwsh") or shutil.which("powershell")
        if shell is None:
            self.skipTest("PowerShell is unavailable")

        canonical_skills = (ROOT / "skills").resolve()
        with tempfile.TemporaryDirectory(prefix="z80-grok-install-") as raw_tmp:
            tmp = Path(raw_tmp)
            destination = tmp / "grok-skills"
            claude = tmp / "claude-skills"
            config = tmp / "config.toml"
            stale = destination / "optimize-z80"
            stale.mkdir(parents=True)
            (stale / "SKILL.md").write_text("stale grok copy\n", encoding="utf-8")
            claude_stale = claude / "workflow"
            claude_stale.mkdir(parents=True)
            (claude_stale / "SKILL.md").write_text(
                "stale claude copy\n", encoding="utf-8"
            )
            config.write_text('[ui]\ntheme = "auto"\n', encoding="utf-8")

            result = subprocess.run(
                [
                    shell,
                    "-NoProfile",
                    "-File",
                    str(GROK_INSTALLER),
                    "-Dest",
                    str(destination),
                    "-GrokConfig",
                    str(config),
                    "-ClaudeSkills",
                    str(claude),
                    "-SkipBackup",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            config_text = config.read_text(encoding="utf-8")
            toml_path = canonical_skills.as_posix()
            self.assertIn(toml_path, config_text)
            self.assertIn("[skills]", config_text)
            self.assertFalse(stale.exists())
            self.assertFalse(claude_stale.exists())
            self.assertTrue((canonical_skills / "optimize-z80" / "SKILL.md").is_file())
            self.assertTrue((WORKFLOW / "references" / "verification.md").is_file())
            skill = (WORKFLOW / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("references/heavy.md", skill)
            self.assertIn("references/verification.md", skill)

        installer = GROK_INSTALLER.read_text(encoding="utf-8")
        self.assertIn('"route-z80"', installer)
        self.assertIn("foreach ($name in $SkillNames)", installer)
        self.assertIn("Do not copy", installer)


if __name__ == "__main__":
    unittest.main()
