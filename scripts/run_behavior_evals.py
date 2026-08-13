#!/usr/bin/env python3
"""Run labelled z80-skills behavior evals in isolated Codex sessions."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
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
        "but do not modify files. Inspect only the current working directory. "
        "Return only JSON matching the supplied output schema.\n\n"
        f"USER REQUEST:\n{case['prompt']}"
    )


def run_case(
    case: dict[str, Any],
    codex_bin: str,
    model: str | None,
    timeout: int,
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
        output = temp_root / "last-message.json"
        command = [
            codex_bin,
            "exec",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
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
        command.append(evaluation_prompt(case))
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
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
        passed = (
            result.returncode == 0
            and parse_error is None
            and not schema_errors
            and matches_expected(actual, case["expected"])
        )
        return {
            "id": case["id"],
            "kind": case["kind"],
            "expected": case["expected"],
            "actual": actual,
            "passed": passed,
            "duration_seconds": round(time.monotonic() - started, 3),
            "returncode": result.returncode,
            "parse_error": parse_error,
            "schema_errors": schema_errors,
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
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--results-dir", type=Path, default=ROOT / "evals" / "results")
    parser.add_argument("--allow-version-mismatch", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
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
    active_version = installed_version(args.codex_bin)
    if active_version != authored_version and not args.allow_version_mismatch:
        raise SystemExit(
            f"installed {PLUGIN_NAME} version {active_version!r} does not match "
            f"manifest version {authored_version!r}; reinstall before evaluating"
        )

    records: list[dict[str, Any]] = []
    for index, case in enumerate(cases, 1):
        print(f"[{index}/{len(cases)}] {case['id']}", flush=True)
        records.append(run_case(case, args.codex_bin, args.model, args.timeout))

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "manifest_version": authored_version,
        "installed_version": active_version,
        "model": args.model or "runtime-default",
        "suites": [str(path) for path in suites],
        "passed": sum(record["passed"] for record in records),
        "failed": sum(not record["passed"] for record in records),
        "routing": route_metrics(records),
        "records": records,
    }
    args.results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.results_dir / f"behavior-{stamp}.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("passed", "failed", "routing")}, indent=2))
    print(f"results: {output}")
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
