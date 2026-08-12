#!/usr/bin/env python3
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "skills" / "workflow"


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


if __name__ == "__main__":
    unittest.main()
