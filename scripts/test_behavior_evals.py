#!/usr/bin/env python3
import json
from pathlib import Path
import unittest

import run_behavior_evals as behavior


ROOT = Path(__file__).resolve().parents[1]


class BehaviorEvalTest(unittest.TestCase):
    def test_datasets_are_closed_and_balanced(self) -> None:
        routing = behavior.load_cases(ROOT / "evals" / "routing.jsonl")
        evidence = behavior.load_cases(ROOT / "evals" / "evidence.jsonl")
        behavior.validate_cases([*routing, *evidence])

        self.assertEqual(
            {case["kind"] for case in routing},
            {"direct", "indirect", "negative", "ambiguous"},
        )
        self.assertEqual(len(routing), 22)
        self.assertEqual(len(evidence), 3)
        routes = {case["expected"]["route"] for case in routing}
        self.assertEqual(
            routes,
            {
                "route-z80",
                "workflow",
                "develop-z80",
                "audit-z80",
                "organize-z80",
                "shrink-z80",
                "optimize-z80",
            },
        )

    def test_expected_matching_is_subset_based(self) -> None:
        actual = {"route": "audit-z80", "rationale": "source evidence"}
        self.assertTrue(behavior.matches_expected(actual, {"route": "audit-z80"}))
        self.assertFalse(behavior.matches_expected(actual, {"route": "workflow"}))

    def test_schema_validation_rejects_extra_and_invalid_values(self) -> None:
        schema = json.loads((
            ROOT / "evals" / "schemas" / "routing-result.schema.json"
        ).read_text(encoding="utf-8"))
        valid = {"route": "workflow", "rationale": "bounded fix"}
        invalid = {"route": "unknown", "rationale": "x", "extra": True}
        self.assertEqual(behavior.validate_json(valid, schema), [])
        errors = behavior.validate_json(invalid, schema)
        self.assertTrue(any("enum" in error for error in errors))
        self.assertTrue(any("unexpected property" in error for error in errors))

    def test_route_metrics_report_precision_and_recall(self) -> None:
        records = [
            {"expected": {"route": "workflow"}, "actual": {"route": "workflow"}},
            {"expected": {"route": "workflow"}, "actual": {"route": "audit-z80"}},
            {"expected": {"route": "audit-z80"}, "actual": {"route": "audit-z80"}},
        ]
        metrics = behavior.route_metrics(records)
        self.assertAlmostEqual(metrics["accuracy"], 2 / 3)
        self.assertAlmostEqual(metrics["per_route"]["workflow"]["recall"], 0.5)
        self.assertAlmostEqual(metrics["per_route"]["audit-z80"]["precision"], 0.5)

    def test_baseline_matches_current_manifest_and_is_honest(self) -> None:
        baseline = json.loads((ROOT / "evals" / "baseline.json").read_text())
        manifest = json.loads((
            ROOT / ".codex-plugin" / "plugin.json"
        ).read_text())
        self.assertEqual(
            baseline["current_manifest_version"], manifest["version"]
        )
        self.assertEqual(baseline["routing"]["full_run"]["passed"], 21)
        self.assertIn(
            "complete 22-case replay",
            baseline["routing"]["claim"],
        )
        self.assertEqual(
            baseline["evidence"]["passed_after_grader_correction"], 3
        )


if __name__ == "__main__":
    unittest.main()
