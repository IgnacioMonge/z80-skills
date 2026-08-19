#!/usr/bin/env python3
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "skills" / "workflow"
DEVELOP = ROOT / "skills" / "develop-z80"
ROUTER = ROOT / "skills" / "route-z80"
Z80_DOMAIN_SKILLS = (
    "develop-z80",
    "debug-z80",
    "audit-z80",
    "organize-z80",
    "shrink-z80",
    "optimize-z80",
)
Z80_SKILLS = ("route-z80", *Z80_DOMAIN_SKILLS)
ALL_SKILLS = (*Z80_SKILLS, "workflow")
ANALYSIS_SKILLS = ("audit-z80", "shrink-z80", "optimize-z80")
LANE_FILES = (
    "skills/audit-z80/references/agent-orchestration.md",
    "skills/shrink-z80/references/agent-orchestration.md",
    "skills/optimize-z80/references/multiagent-roles.md",
)
ROUTE_FILES = (
    WORKFLOW / "references" / "medium.md",
    WORKFLOW / "references" / "heavy.md",
)
ROLES = WORKFLOW / "references" / "roles.md"


class WorkflowIntegrationTest(unittest.TestCase):
    def test_workflow_is_standalone(self) -> None:
        required = (
            WORKFLOW / "SKILL.md",
            WORKFLOW / "agents" / "openai.yaml",
            ROLES,
            *ROUTE_FILES,
        )
        for path in required:
            self.assertTrue(path.is_file(), path)
        for path in WORKFLOW.rglob("*.md"):
            self.assertNotIn("Z80", path.read_text(encoding="utf-8"), path)

        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text())
        self.assertEqual((ROOT / manifest["skills"]).resolve(), ROOT / "skills")
        self.assertTrue(WORKFLOW.is_dir())

    def test_workflow_uses_portable_builtin_agent_types(self) -> None:
        roles_text = ROLES.read_text(encoding="utf-8")
        roles = " ".join(roles_text.split())
        agent_types = set(
            re.findall(
                r"^\| [^|]+ \| `[^`]+` \| `([^`]+)` \| `[^`]+` \|$",
                roles_text,
                re.MULTILINE,
            )
        )
        self.assertEqual(agent_types, {"default", "worker", "explorer"})
        self.assertIn("not external custom-agent profiles", " ".join(
            (WORKFLOW / "SKILL.md").read_text(encoding="utf-8").split()
        ))
        self.assertNotIn("runtime-provided", roles)

    def test_workflow_avoids_serial_controller_overhead(self) -> None:
        skill = (WORKFLOW / "SKILL.md").read_text(encoding="utf-8")
        roles = ROLES.read_text(encoding="utf-8")
        medium = (WORKFLOW / "references" / "medium.md").read_text(
            encoding="utf-8"
        )
        heavy = (WORKFLOW / "references" / "heavy.md").read_text(
            encoding="utf-8"
        )
        combined = "\n".join((skill, roles, medium, heavy))

        self.assertNotIn("workflow_controller", combined)
        self.assertIn("main thread as the controller", skill)
        self.assertIn("Work directly in the main thread; do not spawn agents.", medium)
        self.assertIn(
            "at least two concrete, bounded, independent workstreams",
            combined,
        )
        self.assertIn('reasoning_effort="medium"', roles)
        self.assertIn("Raise effort to `high` or `max`", roles)

    def test_z80_skills_delegate_without_widening_permissions(self) -> None:
        for name in Z80_DOMAIN_SKILLS:
            skill = ROOT / "skills" / name / "SKILL.md"
            text = skill.read_text(encoding="utf-8")
            self.assertIn("../workflow/SKILL.md", text)
            self.assertIn("A workflow route never", " ".join(text.split()))
            sibling = (skill.parent / "../workflow/SKILL.md").resolve()
            self.assertTrue(sibling.is_file(), sibling)

        for path in ROUTE_FILES:
            text = " ".join(path.read_text(encoding="utf-8").split())
            for boundary in (
                "primary-tree read-only",
                "disposable-worktree-only",
                "authorized primary-tree mutation",
            ):
                self.assertIn(boundary, text)
            self.assertIn("verified, domain-gated disposable worktree", text)

    def test_mutation_dispatch_matches_domain_contracts(self) -> None:
        workflow_files = (WORKFLOW / "SKILL.md", ROLES, *ROUTE_FILES)
        for path in workflow_files:
            text = " ".join(path.read_text(encoding="utf-8").split())
            for boundary in (
                "primary-tree read-only",
                "disposable-worktree-only",
                "authorized primary-tree mutation",
            ):
                self.assertIn(boundary, text, path)

        for name in ANALYSIS_SKILLS:
            contract = (
                ROOT / "skills" / name / "references" / "hard-contract.md"
            ).read_text(encoding="utf-8")
            self.assertIn("Primary tree read-only + disposable sandbox", contract)
            self.assertIn(
                "Implementing edits in the primary tree is **out of scope**",
                contract,
            )
            self.assertIn("scripts/run_in_worktree.py", contract)

        organize = ROOT / "skills" / "organize-z80"
        self.assertIn(
            "Default read-only boundary",
            (organize / "references" / "hard-contract.md").read_text(
                encoding="utf-8"
            ),
        )
        apply_text = (organize / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## Apply gate", apply_text)
        self.assertIn("Enter `apply` only when all conditions hold", apply_text)

        develop_contract = (
            DEVELOP / "references" / "hard-contract.md"
        ).read_text(encoding="utf-8")
        for boundary in (
            "primary-tree read-only",
            "disposable-worktree-only",
            "authorized primary-tree mutation",
        ):
            self.assertIn(boundary, develop_contract)
        self.assertIn("scripts/run_in_worktree.py", develop_contract)

        debug_contract = (
            ROOT / "skills" / "debug-z80" / "references" / "hard-contract.md"
        ).read_text(encoding="utf-8")
        for boundary in (
            "primary-tree read-only",
            "disposable-worktree-only",
            "authorized primary-tree mutation",
        ):
            self.assertIn(boundary, debug_contract)
        self.assertIn("scripts/run_in_worktree.py", debug_contract)

    def test_optimize_runtime_paths_are_structurally_resolvable(self) -> None:
        skill_file = ROOT / "skills" / "optimize-z80" / "SKILL.md"
        skill = skill_file.read_text(encoding="utf-8")

        self.assertIn("following symlinks and Windows junctions", skill)
        self.assertIn("sole preflight entry point", skill)
        self.assertNotIn("references/preflight.md", skill)
        self.assertTrue(
            (skill_file.parent / "scripts" / "preflight.py").is_file()
        )

        canonical_skill_dir = skill_file.resolve(strict=True).parent
        runner = (
            canonical_skill_dir / ".." / ".." / "scripts" / "run_in_worktree.py"
        ).resolve(strict=True)
        self.assertEqual(runner, (ROOT / "scripts" / "run_in_worktree.py").resolve())
        self.assertTrue(runner.is_file())

    def test_skill_corpus_is_structurally_closed(self) -> None:
        skill_dirs = sorted(
            skill_dir for skill_dir in (ROOT / "skills").iterdir()
            if skill_dir.is_dir()
        )
        self.assertEqual(
            [skill_dir.name for skill_dir in skill_dirs], sorted(ALL_SKILLS)
        )
        for skill_dir in skill_dirs:
            skill = skill_dir / "SKILL.md"
            text = skill.read_text(encoding="utf-8")
            frontmatter = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
            self.assertIsNotNone(frontmatter, skill)
            fields = {}
            for line in frontmatter.group(1).splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    fields[key.strip()] = value.strip()
            self.assertEqual(fields.get("name"), skill_dir.name, skill)
            self.assertTrue(fields.get("description"), skill)
            self.assertTrue((skill_dir / "agents" / "openai.yaml").is_file())

            for markdown in skill_dir.rglob("*.md"):
                contents = markdown.read_text(encoding="utf-8")
                for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", contents):
                    target = target.split("#", 1)[0]
                    if not target or re.match(r"[a-z]+://|mailto:", target):
                        continue
                    self.assertTrue((markdown.parent / target).resolve().exists(), (
                        markdown,
                        target,
                    ))

            for target in re.findall(r"references/[A-Za-z0-9_.-]+\.md", text):
                self.assertTrue((skill_dir / target).is_file(), (skill, target))
            for target in re.findall(r"\.\./[A-Za-z0-9_-]+/SKILL\.md", text):
                self.assertTrue((skill_dir / target).resolve().is_file(), (skill, target))

    def test_manifest_respects_final_listing_limits(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text())
        interface = manifest["interface"]
        self.assertLessEqual(len(interface["shortDescription"]), 30)
        self.assertLessEqual(len(interface["defaultPrompt"]), 3)
        for prompt in interface["defaultPrompt"]:
            self.assertLessEqual(len(prompt), 128)
            self.assertRegex(prompt, r"^Use \$[a-z0-9-]+ ")
        self.assertTrue(any(
            "$route-z80" in prompt for prompt in interface["defaultPrompt"]
        ))
        self.assertFalse(any(
            sum(f"${name}" in prompt for name in Z80_DOMAIN_SKILLS) > 1
            for prompt in interface["defaultPrompt"]
        ))

    def test_only_router_is_implicitly_invoked_for_z80_domains(self) -> None:
        for name in Z80_DOMAIN_SKILLS:
            metadata = (
                ROOT / "skills" / name / "agents" / "openai.yaml"
            ).read_text(encoding="utf-8")
            self.assertRegex(
                metadata,
                r"(?m)^policy:\n  allow_implicit_invocation: false$",
                name,
            )

        router_metadata = (
            ROUTER / "agents" / "openai.yaml"
        ).read_text(encoding="utf-8")
        self.assertRegex(
            router_metadata,
            r"(?m)^policy:\n  allow_implicit_invocation: true$",
        )

    def test_project_routes_and_auto_preflight_take_precedence(self) -> None:
        text = " ".join((WORKFLOW / "SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("project instructions define route names", text)
        self.assertIn("run the required domain preflight directly at Light", text)

    def test_z80_domain_router_is_thin_and_develop_is_opt_in(self) -> None:
        router = (ROUTER / "SKILL.md").read_text(encoding="utf-8")
        develop = (DEVELOP / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = re.match(r"\A---\n(.*?)\n---\n", develop, re.DOTALL)
        self.assertIsNotNone(frontmatter)
        description = frontmatter.group(1)

        for name in (*Z80_DOMAIN_SKILLS, "workflow"):
            self.assertIn(f"../{name}/SKILL.md", router)
        self.assertIn("Select one primary route", router)
        self.assertIn("load every sibling `SKILL.md`", router)
        self.assertIn("ordinary bounded fix", router)
        self.assertIn("remain in `route-z80`", router)
        self.assertIn("appear together as alternatives", router)
        self.assertIn("not sufficient activation", develop)
        self.assertIn("Do not use for routine bug fixes", description)
        self.assertNotIn("game, demo, tool, feature, or port", description)

    def test_debug_route_requires_observed_unresolved_failure(self) -> None:
        router = (ROUTER / "SKILL.md").read_text(encoding="utf-8")
        debug = (ROOT / "skills" / "debug-z80" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        audit = (ROOT / "skills" / "audit-z80" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("one observed failure with unresolved causality", router)
        self.assertIn("cause is already established", router)
        self.assertIn("There is an observed failure", debug)
        self.assertIn("The causal owner is genuinely unknown", debug)
        self.assertIn("hand the known-cause fix to `$workflow`", debug)
        self.assertIn("Do not use for root-cause diagnosis", audit)

    def test_domain_lane_files_do_not_duplicate_the_router(self) -> None:
        for relative in LANE_FILES:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("## Workflow Boundary", text)
            self.assertNotIn("## Capacity Negotiation", text)
            self.assertNotIn("## Adaptive Model and Effort Routing", text)


if __name__ == "__main__":
    unittest.main()
