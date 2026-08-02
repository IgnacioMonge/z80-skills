#!/usr/bin/env python3
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "skills" / "workflow"
Z80_SKILLS = ("audit-z80", "organize-z80", "shrink-z80", "optimize-z80")
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
        roles = " ".join(ROLES.read_text(encoding="utf-8").split())
        for agent_type in ("`default`", "`worker`", "`explorer`"):
            self.assertIn(agent_type, roles)
        self.assertIn("not external custom-agent profiles", " ".join(
            (WORKFLOW / "SKILL.md").read_text(encoding="utf-8").split()
        ))
        self.assertNotIn("runtime-provided", roles)

    def test_z80_skills_delegate_without_widening_permissions(self) -> None:
        for name in Z80_SKILLS:
            skill = ROOT / "skills" / name / "SKILL.md"
            text = skill.read_text(encoding="utf-8")
            self.assertIn("../workflow/SKILL.md", text)
            self.assertIn("A workflow route never", " ".join(text.split()))
            sibling = (skill.parent / "../workflow/SKILL.md").resolve()
            self.assertTrue(sibling.is_file(), sibling)

        for path in ROUTE_FILES:
            text = " ".join(path.read_text(encoding="utf-8").split())
            self.assertIn("Worker permissions are the intersection", text)
            self.assertIn("workers may not edit or build the primary tree", text)

    def test_project_routes_and_auto_preflight_take_precedence(self) -> None:
        text = " ".join((WORKFLOW / "SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("project instructions define route names", text)
        self.assertIn("run the required domain preflight directly at Light", text)

    def test_domain_lane_files_do_not_duplicate_the_router(self) -> None:
        for relative in LANE_FILES:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("## Workflow Boundary", text)
            self.assertNotIn("## Capacity Negotiation", text)
            self.assertNotIn("## Adaptive Model and Effort Routing", text)


if __name__ == "__main__":
    unittest.main()
