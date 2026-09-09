#!/usr/bin/env python3
"""Run labelled z80-skills behavior evals in isolated Codex sessions."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUITES = (ROOT / "evals" / "routing.jsonl", ROOT / "evals" / "evidence.jsonl")
PLUGIN_NAME = "z80-skills@personal"
USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)
ACTION_TYPES = {
    "command_execution",
    "file_change",
    "mcp_tool_call",
    "collab_tool_call",
    "web_search",
}


def load_cases(suite: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for number, raw in enumerate(suite.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            case = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{suite}:{number}: {exc}") from exc
        if not isinstance(case, dict):
            raise ValueError(f"{suite}:{number}: case must be an object")
        case["_suite"] = str(suite)
        case["_line"] = number
        cases.append(case)
    return cases


def resolve_case_path(case: dict[str, Any], key: str) -> Path:
    suite = Path(case["_suite"])
    return (suite.parent / case[key]).resolve()


def validate_cases(cases: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    allowed_kinds = {"direct", "indirect", "negative", "ambiguous", "evidence"}
    for case in cases:
        location = f"{case.get('_suite')}:{case.get('_line')}"
        for key in ("id", "kind", "schema", "prompt", "expected"):
            if key not in case:
                raise ValueError(f"{location}: missing {key}")
        if not isinstance(case["id"], str) or not case["id"]:
            raise ValueError(f"{location}: id must be a non-empty string")
        if case["id"] in seen:
            raise ValueError(f"duplicate case id: {case['id']}")
        seen.add(case["id"])
        if case["kind"] not in allowed_kinds:
            raise ValueError(f"{location}: unsupported kind {case['kind']!r}")
        if not isinstance(case["prompt"], str) or not case["prompt"].strip():
            raise ValueError(f"{location}: prompt must be non-empty")
        if not isinstance(case["expected"], dict) or not case["expected"]:
            raise ValueError(f"{location}: expected must be a non-empty object")
        schema = resolve_case_path(case, "schema")
        if not schema.is_file():
            raise ValueError(f"{location}: missing schema {schema}")
        json.loads(schema.read_text(encoding="utf-8"))
        if "fixture" in case and not resolve_case_path(case, "fixture").is_dir():
            raise ValueError(f"{location}: missing fixture {case['fixture']}")


def validate_json(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    type_map = {
        "object": dict,
        "array": list,
        "string": str,
        "integer": int,
        "boolean": bool,
    }
    if expected_type in type_map:
        expected_python = type_map[expected_type]
        valid = isinstance(value, expected_python)
        if expected_type == "integer" and isinstance(value, bool):
            valid = False
        if not valid:
            return [f"{path}: expected {expected_type}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} is not in enum")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required property {key}")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}: unexpected property {key}")
        for key, item in value.items():
            if key in properties:
                errors.extend(validate_json(item, properties[key], f"{path}.{key}"))
    if isinstance(value, str) and "maxLength" in schema:
        if len(value) > schema["maxLength"]:
            errors.append(f"{path}: exceeds maxLength")
    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: above maximum")
    return errors


def matches_expected(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            key in actual and matches_expected(actual[key], value)
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(
            matches_expected(a, e) for a, e in zip(actual, expected)
        )
    return actual == expected


def route_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    labelled = [record for record in records if "route" in record["expected"]]
    labels = sorted({record["expected"]["route"] for record in labelled})
    per_route: dict[str, dict[str, float | int]] = {}
    correct = 0
    for label in labels:
        tp = fp = fn = 0
        for record in labelled:
            expected = record["expected"]["route"]
            actual = record.get("actual") or {}
            predicted = actual.get("route") if isinstance(actual, dict) else None
            tp += int(expected == label and predicted == label)
            fp += int(expected != label and predicted == label)
            fn += int(expected == label and predicted != label)
            if expected == predicted:
                correct += int(label == expected)
        per_route[label] = {
            "support": sum(record["expected"]["route"] == label for record in labelled),
            "precision": tp / (tp + fp) if tp + fp else 0.0,
            "recall": tp / (tp + fn) if tp + fn else 0.0,
        }
    return {
        "cases": len(labelled),
        "accuracy": correct / len(labelled) if labelled else 0.0,
        "per_route": per_route,
    }


def manifest_version() -> str:
    manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text())
    return manifest["version"]


def fingerprint_files(paths: list[Path]) -> dict[str, Any]:
    digest = hashlib.sha256()
    files = sorted({
        path.resolve() for path in paths
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    })
    for path in files:
        try:
            relative = path.relative_to(ROOT).as_posix()
        except ValueError:
            relative = f"external/{path.name}"
        content = path.read_bytes()
        digest.update(f"{relative}\0{len(content)}\0".encode())
        digest.update(content)
    return {
        "algorithm": "sha256",
        "digest": digest.hexdigest(),
        "file_count": len(files),
        "installed_content_verified": False,
    }


def evaluated_source_fingerprint(
    cases: list[dict[str, Any]], suites: tuple[Path, ...]
) -> dict[str, Any]:
    paths = [
        ROOT / ".codex-plugin" / "plugin.json",
        Path(__file__),
        ROOT / "scripts" / "run_in_worktree.py",
        *suites,
    ]
    paths.extend(path for path in (ROOT / "skills").rglob("*") if path.is_file())
    for case in cases:
        paths.append(resolve_case_path(case, "schema"))
        if "fixture" in case:
            paths.extend(
                path for path in resolve_case_path(case, "fixture").rglob("*")
                if path.is_file()
            )
    return fingerprint_files(paths)


def workspace_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            digest.update(f"d\0{relative}\0".encode())
        elif path.is_file():
            content = path.read_bytes()
            digest.update(f"f\0{relative}\0{len(content)}\0".encode())
            digest.update(content)
    return digest.hexdigest()


def parse_event_trace(raw: str) -> dict[str, Any]:
    events: list[tuple[int, dict[str, Any]]] = []
    malformed = 0
    for line_number, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        if not isinstance(event, dict):
            malformed += 1
            continue
        events.append((line_number, event))

    usage_totals = {field: 0 for field in USAGE_FIELDS}
    usage_known = {field: True for field in USAGE_FIELDS}
    turn_completed = 0
    runtime_effort: str | None = None
    runtime_model: str | None = None
    actions: dict[str, dict[str, Any]] = {}
    for line_number, event in events:
        if isinstance(event.get("reasoning_effort"), str):
            runtime_effort = event["reasoning_effort"]
        if isinstance(event.get("model"), str):
            runtime_model = event["model"]
        if event.get("type") == "turn.completed":
            turn_completed += 1
            observed = event.get("usage")
            for field in USAGE_FIELDS:
                value = observed.get(field) if isinstance(observed, dict) else None
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                    usage_totals[field] += value
                else:
                    usage_known[field] = False
        if event.get("type") not in {"item.started", "item.updated", "item.completed"}:
            continue
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") not in ACTION_TYPES:
            continue
        action_id = item.get("id")
        key = str(action_id) if action_id is not None else f"line-{line_number}"
        actions[key] = item

    action_items = list(actions.values())
    command_count = sum(item.get("type") == "command_execution" for item in action_items)
    file_changes = [item for item in action_items if item.get("type") == "file_change"]
    web_searches = sum(item.get("type") == "web_search" for item in action_items)
    unknown_effects = sum(
        item.get("type") in {"command_execution", "mcp_tool_call", "collab_tool_call"}
        for item in action_items
    )
    failed_actions = sum(
        item.get("status") in {"failed", "declined"}
        or (
            item.get("type") == "command_execution"
            and isinstance(item.get("exit_code"), int)
            and item["exit_code"] != 0
        )
        for item in action_items
    )
    usage = {
        field: usage_totals[field]
        if turn_completed and usage_known[field]
        else None
        for field in USAGE_FIELDS
    }
    return {
        "event_count": len(events),
        "malformed_event_count": malformed,
        "turn_completed_count": turn_completed,
        "usage": usage,
        "runtime_confirmed_reasoning_effort": runtime_effort,
        "runtime_confirmed_model": runtime_model,
        "actions": {
            "tool_calls_total": len(action_items),
            "command_count": command_count,
            "non_command_tool_count": len(action_items) - command_count,
            "observed_read_attempt_count": web_searches,
            "observed_write_attempt_count": len(file_changes),
            "unknown_effect_attempt_count": unknown_effects,
            "failed_action_count": failed_actions,
            "successful_file_change_count": sum(
                item.get("status") == "completed" for item in file_changes
            ),
        },
    }


def read_only_observed(telemetry: dict[str, Any], workspace_changed: bool) -> bool:
    return (
        telemetry["malformed_event_count"] == 0
        and telemetry["turn_completed_count"] > 0
        and telemetry["actions"]["observed_write_attempt_count"] == 0
        and not workspace_changed
    )


def _subprocess_text(value: str | bytes | None) -> str:
    return value.decode(errors="replace") if isinstance(value, bytes) else value or ""


def resolve_codex_bin(command: str) -> str:
    resolved = shutil.which(command)
    if resolved is None:
        raise FileNotFoundError(f"Codex executable not found: {command}")
    return resolved


def installed_version(codex_bin: str) -> str | None:
    result = subprocess.run(
        [codex_bin, "plugin", "list"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    match = re.search(
        rf"(?m)^{re.escape(PLUGIN_NAME)}\s+installed, enabled\s+(\S+)",
        result.stdout,
    )
    return match.group(1) if match else None


def evaluation_prompt(case: dict[str, Any]) -> str:
    return (
        "This is a read-only behavior evaluation of the installed z80-skills "
        "plugin. Treat the text under USER REQUEST as a fresh real request. "
        "Select and follow the appropriate installed skill exactly as normal, "
        "but do not modify files. Load installed skill instructions and bundled "
        "resources as needed; inspect project inputs only in the current working directory. "
        "Return only JSON matching the supplied output schema.\n\n"
        f"USER REQUEST:\n{case['prompt']}"
    )


def run_case(
    case: dict[str, Any],
    codex_bin: str,
    model: str | None,
    reasoning_effort: str | None,
    timeout: int,
    trace_path: Path | None = None,
) -> dict[str, Any]:
    schema_path = resolve_case_path(case, "schema")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=f"z80-eval-{case['id']}-") as raw_tmp:
        temp_root = Path(raw_tmp)
        workdir = temp_root / "workspace"
        if "fixture" in case:
            shutil.copytree(resolve_case_path(case, "fixture"), workdir)
        else:
            workdir.mkdir()
        workspace_before = workspace_fingerprint(workdir)
        output = temp_root / "last-message.json"
        command = [
            codex_bin,
            "exec",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "--json",
            "--output-schema",
            str(schema_path),
            "--color",
            "never",
            "-o",
            str(output),
            "-C",
            str(workdir),
        ]
        if model:
            command.extend(("--model", model))
        if reasoning_effort:
            command.extend((
                "-c",
                f"model_reasoning_effort={json.dumps(reasoning_effort)}",
            ))
        prompt = evaluation_prompt(case)
        command.append("-")
        timed_out = False
        try:
            result = subprocess.run(
                command,
                input=prompt,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            result = subprocess.CompletedProcess(
                command,
                124,
                _subprocess_text(exc.stdout),
                _subprocess_text(exc.stderr),
            )
        if trace_path is not None:
            trace_path.parent.mkdir(parents=True, exist_ok=True)
            trace_path.write_bytes(result.stdout.encode())
        telemetry = parse_event_trace(result.stdout)
        workspace_after = workspace_fingerprint(workdir)
        actual: Any = None
        parse_error: str | None = None
        if output.is_file():
            try:
                actual = json.loads(output.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                parse_error = str(exc)
        else:
            parse_error = "Codex did not write the final response file"
        schema_errors = validate_json(actual, schema) if parse_error is None else []
        changed = workspace_before != workspace_after
        passed = (
            result.returncode == 0
            and parse_error is None
            and not schema_errors
            and matches_expected(actual, case["expected"])
            and read_only_observed(telemetry, changed)
        )
        return {
            "id": case["id"],
            "kind": case["kind"],
            "expected": case["expected"],
            "actual": actual,
            "passed": passed,
            "duration_seconds": round(time.monotonic() - started, 3),
            "returncode": result.returncode,
            "timed_out": timed_out,
            "parse_error": parse_error,
            "schema_errors": schema_errors,
            "telemetry": telemetry,
            "requested_reasoning_effort": reasoning_effort,
            "observed": {
                "write_attempt": telemetry["actions"]["observed_write_attempt_count"] > 0,
                "successful_file_change": (
                    telemetry["actions"]["successful_file_change_count"] > 0
                ),
                "workspace_changed": changed,
            },
            "trace_file": str(trace_path) if trace_path is not None else None,
            "stderr_tail": result.stderr[-2000:],
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suite",
        action="append",
        type=Path,
        help="JSONL suite; repeat to run several (default: routing and evidence)",
    )
    parser.add_argument("--case", action="append", dest="case_ids")
    parser.add_argument("--model")
    parser.add_argument(
        "--reasoning-effort",
        help="native Codex model_reasoning_effort config value",
    )
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--results-dir", type=Path, default=ROOT / "evals" / "results")
    parser.add_argument("--allow-version-mismatch", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        codex_bin = resolve_codex_bin(args.codex_bin)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc
    suites = tuple(path.resolve() for path in args.suite) if args.suite else DEFAULT_SUITES
    cases: list[dict[str, Any]] = []
    for suite in suites:
        cases.extend(load_cases(suite))
    validate_cases(cases)
    if args.case_ids:
        requested = set(args.case_ids)
        cases = [case for case in cases if case["id"] in requested]
        missing = requested - {case["id"] for case in cases}
        if missing:
            raise SystemExit(f"unknown case ids: {', '.join(sorted(missing))}")
    counts = Counter(case["kind"] for case in cases)
    if args.dry_run:
        print(json.dumps({"cases": len(cases), "kinds": counts}, sort_keys=True))
        return 0

    authored_version = manifest_version()
    active_version = installed_version(codex_bin)
    if active_version != authored_version and not args.allow_version_mismatch:
        raise SystemExit(
            f"installed {PLUGIN_NAME} version {active_version!r} does not match "
            f"manifest version {authored_version!r}; reinstall before evaluating"
        )

    source_before = evaluated_source_fingerprint(cases, suites)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.results_dir / f"behavior-{stamp}.json"
    trace_dir = args.results_dir / f"behavior-{stamp}.traces"
    records: list[dict[str, Any]] = []
    for index, case in enumerate(cases, 1):
        print(f"[{index}/{len(cases)}] {case['id']}", flush=True)
        trace_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", case["id"])
        record = run_case(
            case,
            codex_bin,
            args.model,
            args.reasoning_effort,
            args.timeout,
            trace_dir / f"{index:03d}-{trace_name}.jsonl",
        )
        record["trace_file"] = str(Path(record["trace_file"]).relative_to(args.results_dir))
        records.append(record)

    source_changed = (
        evaluated_source_fingerprint(cases, suites)["digest"]
        != source_before["digest"]
    )
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "manifest_version": authored_version,
        "installed_version": active_version,
        "requested_model": args.model,
        "runtime_confirmed_model": sorted({
            record["telemetry"]["runtime_confirmed_model"]
            for record in records
            if record["telemetry"]["runtime_confirmed_model"] is not None
        }) or None,
        "requested_reasoning_effort": args.reasoning_effort,
        "runtime_confirmed_reasoning_effort": sorted({
            record["telemetry"]["runtime_confirmed_reasoning_effort"]
            for record in records
            if record["telemetry"]["runtime_confirmed_reasoning_effort"] is not None
        }) or None,
        "authored_source_fingerprint": source_before,
        "authored_source_changed_during_run": source_changed,
        "suites": [str(path) for path in suites],
        "passed": sum(record["passed"] for record in records),
        "failed": sum(not record["passed"] for record in records),
        "routing": route_metrics(records),
        "records": records,
    }
    args.results_dir.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("passed", "failed", "routing")}, indent=2))
    print(f"results: {output}")
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
