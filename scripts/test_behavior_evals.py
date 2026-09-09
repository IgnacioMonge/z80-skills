#!/usr/bin/env python3
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

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
        existing_routing_ids = {
            "direct-route", "direct-develop", "direct-audit", "direct-debug",
            "direct-organize", "direct-shrink", "direct-optimize", "direct-workflow",
            "direct-port-spectranext", "direct-send-bridgezx", "direct-document",
            "indirect-develop", "indirect-audit", "indirect-debug",
            "implicit-z80-debug-precedence", "indirect-organize", "indirect-shrink",
            "indirect-optimize", "indirect-port-spectranext", "indirect-send-bridgezx",
            "indirect-document", "negative-fix", "negative-feature",
            "negative-refactor", "negative-build", "negative-code-comment",
            "negative-agent-docs", "negative-known-bug",
            "negative-spectrum-next-not-spectranext", "ambiguous-metrics",
            "ambiguous-size", "ambiguous-crash", "ambiguous-unspecified",
            "ambiguous-spectranext-backend",
        }
        existing_evidence_ids = {
            "audit-stale-map", "shrink-stale-map", "optimize-no-baseline",
            "debug-open-causality-stale-map",
        }
        self.assertTrue(existing_routing_ids <= {case["id"] for case in routing})
        self.assertTrue(existing_evidence_ids <= {case["id"] for case in evidence})
        implicit_debug = next(
            case for case in routing
            if case["id"] == "implicit-z80-debug-precedence"
        )
        self.assertEqual(implicit_debug["kind"], "indirect")
        self.assertEqual(implicit_debug["expected"], {"route": "debug-z80"})
        self.assertNotIn("$", implicit_debug["prompt"])
        self.assertNotIn("skill", implicit_debug["prompt"].lower())
        agent_docs = next(
            case for case in routing if case["id"] == "negative-agent-docs"
        )
        self.assertEqual(agent_docs["kind"], "negative")
        self.assertEqual(agent_docs["expected"], {"route": "workflow"})
        routes = {case["expected"]["route"] for case in routing}
        self.assertEqual(
            routes,
            {
                "route-z80",
                "workflow",
                "document-z80",
                "send-bridgezx",
                "port-spectranext",
                "develop-z80",
                "debug-z80",
                "audit-z80",
                "organize-z80",
                "shrink-z80",
                "optimize-z80",
            },
        )
        new_evidence = [
            case for case in evidence if case["id"].endswith("-unprompted")
        ]
        self.assertGreaterEqual(len(new_evidence), 3)
        for case in new_evidence:
            prompt = case["prompt"].lower()
            for leaked in ("$", "verified", "candidate", "stale", "missing", "open"):
                self.assertNotIn(leaked, prompt)

    def test_expected_matching_is_subset_based(self) -> None:
        actual = {"route": "audit-z80", "rationale": "source evidence"}
        self.assertTrue(behavior.matches_expected(actual, {"route": "audit-z80"}))
        self.assertFalse(behavior.matches_expected(actual, {"route": "workflow"}))

    def test_codex_command_resolves_to_platform_launcher(self) -> None:
        launcher = r"C:\Users\example\AppData\Roaming\npm\codex.CMD"
        with mock.patch.object(behavior.shutil, "which", return_value=launcher):
            self.assertEqual(behavior.resolve_codex_bin("codex"), launcher)
        with mock.patch.object(behavior.shutil, "which", return_value=None):
            with self.assertRaises(FileNotFoundError):
                behavior.resolve_codex_bin("codex")

    def test_run_case_uses_json_telemetry_and_native_effort_config(self) -> None:
        case = {
            "id": "stdin-transport",
            "kind": "direct",
            "schema": "schemas/routing-result.schema.json",
            "prompt": "Observed failure\nwith a second line",
            "expected": {"route": "debug-z80"},
            "_suite": str(ROOT / "evals" / "routing.jsonl"),
            "_line": 1,
        }

        def fake_run(command, **kwargs):
            self.assertEqual(command[-1], "-")
            self.assertIn("--json", command)
            self.assertIn("model_reasoning_effort=\"high\"", command)
            self.assertEqual(kwargs["input"], behavior.evaluation_prompt(case))
            output = Path(command[command.index("-o") + 1])
            output.write_text(
                json.dumps({"route": "debug-z80", "rationale": "observed"}),
                encoding="utf-8",
            )
            stdout = "\n".join((
                json.dumps({"type": "thread.started", "thread_id": "test"}),
                json.dumps({"type": "turn.started"}),
                json.dumps({
                    "type": "turn.completed",
                    "usage": {"input_tokens": 20, "cached_input_tokens": 4,
                              "output_tokens": 8},
                }),
            ))
            return mock.Mock(returncode=0, stdout=stdout, stderr="")

        with mock.patch.object(behavior.subprocess, "run", side_effect=fake_run):
            record = behavior.run_case(case, "codex.CMD", None, "high", 10)

        self.assertTrue(record["passed"])
        self.assertEqual(record["telemetry"]["usage"]["input_tokens"], 20)
        self.assertIsNone(record["telemetry"]["usage"]["reasoning_output_tokens"])
        self.assertEqual(record["requested_reasoning_effort"], "high")
        self.assertIsNone(
            record["telemetry"]["runtime_confirmed_reasoning_effort"]
        )
        self.assertIsNone(record["telemetry"]["runtime_confirmed_model"])

    def test_timeout_preserves_partial_trace_and_returns_failed_record(self) -> None:
        case = {
            "id": "timeout",
            "kind": "direct",
            "schema": "schemas/routing-result.schema.json",
            "prompt": "Diagnose the failure",
            "expected": {"route": "debug-z80"},
            "_suite": str(ROOT / "evals" / "routing.jsonl"),
            "_line": 1,
        }
        partial = b'{"type":"turn.started"}\n'
        timeout = behavior.subprocess.TimeoutExpired(
            ["codex", "exec"], 10, output=partial, stderr=b"partial stderr"
        )
        with tempfile.TemporaryDirectory() as raw_tmp:
            trace = Path(raw_tmp) / "trace.jsonl"
            with mock.patch.object(behavior.subprocess, "run", side_effect=timeout):
                record = behavior.run_case(case, "codex.CMD", None, None, 10, trace)
            self.assertEqual(trace.read_bytes(), partial)

        self.assertFalse(record["passed"])
        self.assertTrue(record["timed_out"])
        self.assertEqual(record["returncode"], 124)
        self.assertEqual(record["telemetry"]["event_count"], 1)
        self.assertIn("partial stderr", record["stderr_tail"])

    def test_event_trace_fixture_counts_actions_and_usage(self) -> None:
        raw = (ROOT / "evals" / "fixtures" / "codex-events" / "complete.jsonl").read_text()
        telemetry = behavior.parse_event_trace(raw)
        self.assertEqual(telemetry["malformed_event_count"], 0)
        self.assertEqual(telemetry["usage"]["reasoning_output_tokens"], 3)
        self.assertEqual(telemetry["actions"]["tool_calls_total"], 2)
        self.assertEqual(telemetry["actions"]["command_count"], 1)
        self.assertEqual(telemetry["actions"]["observed_read_attempt_count"], 0)
        self.assertEqual(telemetry["actions"]["unknown_effect_attempt_count"], 2)

    def test_event_trace_preserves_unknown_usage_and_malformed_count(self) -> None:
        raw = (ROOT / "evals" / "fixtures" / "codex-events" / "malformed.jsonl").read_text()
        telemetry = behavior.parse_event_trace(raw)
        self.assertEqual(telemetry["malformed_event_count"], 2)
        self.assertEqual(telemetry["usage"]["input_tokens"], 12)
        self.assertIsNone(telemetry["usage"]["output_tokens"])
        self.assertFalse(behavior.read_only_observed(telemetry, False))

        missing = behavior.parse_event_trace("")
        self.assertEqual(missing["turn_completed_count"], 0)
        self.assertTrue(all(value is None for value in missing["usage"].values()))
        self.assertFalse(behavior.read_only_observed(missing, False))

    def test_event_trace_aggregates_turns_without_fabricating_missing_usage(self) -> None:
        raw = (ROOT / "evals" / "fixtures" / "codex-events" / "two-turns.jsonl").read_text()
        telemetry = behavior.parse_event_trace(raw)
        self.assertEqual(telemetry["turn_completed_count"], 2)
        self.assertEqual(telemetry["usage"]["input_tokens"], 30)
        self.assertEqual(telemetry["usage"]["cached_input_tokens"], 7)
        self.assertEqual(telemetry["usage"]["reasoning_output_tokens"], 10)
        self.assertIsNone(telemetry["usage"]["output_tokens"])

    def test_source_fingerprint_excludes_runtime_cache_and_includes_shared_runner(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            temp_root = Path(raw_tmp)
            source = temp_root / "source.txt"
            cache = temp_root / "__pycache__" / "module.pyc"
            source.write_text("source", encoding="utf-8")
            cache.parent.mkdir()
            cache.write_bytes(b"runtime")
            self.assertEqual(
                behavior.fingerprint_files([source, cache])["file_count"], 1
            )

        captured: list[Path] = []

        def capture(paths):
            captured.extend(paths)
            return {"digest": "test"}

        with mock.patch.object(behavior, "fingerprint_files", side_effect=capture):
            behavior.evaluated_source_fingerprint([], ())
        self.assertIn(ROOT / "scripts" / "run_in_worktree.py", captured)

    def test_failed_file_change_is_a_write_attempt_not_a_success(self) -> None:
        raw = (ROOT / "evals" / "fixtures" / "codex-events" / "failed-write.jsonl").read_text()
        telemetry = behavior.parse_event_trace(raw)
        actions = telemetry["actions"]
        self.assertEqual(actions["observed_write_attempt_count"], 1)
        self.assertEqual(actions["failed_action_count"], 1)
        self.assertEqual(actions["successful_file_change_count"], 0)
        self.assertFalse(behavior.read_only_observed(telemetry, False))

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

    def test_historical_baseline_remains_honest(self) -> None:
        baseline = json.loads((ROOT / "evals" / "baseline.json").read_text())
        historical_version = baseline["current_manifest_version"]
        self.assertTrue(historical_version)
        self.assertEqual(baseline["routing"]["full_run"]["passed"], 21)
        self.assertIn("previous 24-case routing suite passed", baseline["routing"]["claim"])
        for suite_name in ("routing", "evidence"):
            release = baseline[suite_name]["current_suite"]
            cases = behavior.load_cases(ROOT / "evals" / f"{suite_name}.jsonl")
            self.assertEqual(release["plugin_version"], historical_version)
            self.assertEqual(release["installed_version"], historical_version)
            self.assertGreaterEqual(len(cases), release["cases"])
            self.assertEqual(release["passed"], release["cases"])
            self.assertEqual(release["failed"], 0)
            self.assertEqual(release["status"], "PASS")
        current = baseline["routing"]["previous_suite"]
        self.assertEqual(current["cases"], 24)
        self.assertEqual(current["status"], "SUPERSEDED")
        self.assertEqual(current["model"], "gpt-5.6-sol")
        self.assertEqual(current["passed"], 24)
        self.assertEqual(current["failed"], 0)
        self.assertEqual(current["accuracy"], 1.0)
        targeted = baseline["routing"]["targeted_debug_run"]
        self.assertEqual(targeted["model"], "gpt-5.6-sol")
        self.assertEqual(targeted["passed"], 5)
        self.assertEqual(targeted["failed"], 0)
        self.assertEqual(len(targeted["case_ids"]), 5)
        implicit_debug = baseline["routing"]["targeted_implicit_debug_run"]
        self.assertEqual(implicit_debug["model"], "runtime-default")
        self.assertEqual(
            implicit_debug["case_ids"],
            ["implicit-z80-debug-precedence"],
        )
        self.assertEqual(implicit_debug["passed"], 1)
        self.assertEqual(implicit_debug["failed"], 0)
        self.assertEqual(implicit_debug["accuracy"], 1.0)
        self.assertTrue(implicit_debug["debug_z80_contract_observed"])
        targeted_port = baseline["routing"]["targeted_port_run"]
        self.assertEqual(targeted_port["model"], "gpt-5.6-sol")
        self.assertEqual(targeted_port["passed"], 4)
        self.assertEqual(targeted_port["failed"], 0)
        self.assertEqual(targeted_port["accuracy"], 1.0)
        self.assertEqual(len(targeted_port["case_ids"]), 4)
        self.assertEqual(
            baseline["evidence"]["passed_after_grader_correction"], 4
        )
        self.assertTrue(
            baseline["evidence"]["gates_observed"]
            ["open_causality_not_promoted_from_stale_artifact"]
        )


if __name__ == "__main__":
    unittest.main()
