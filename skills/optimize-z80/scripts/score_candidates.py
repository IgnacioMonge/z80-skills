#!/usr/bin/env python3
"""Score optimization candidates with policy veto, evidence gate, and profile weights.

Policy veto (hard reject, score -999):
  - forbidden tags: a candidate whose `tags` intersect the policy `[forbidden]`
    set (undocumented, smc, sp_abuse, interrupt_windows, hardware_timing,
    banking_changes) is rejected, not demoted.
  - wrong target: a candidate whose `targets` do not cover the active target is
    rejected. A hardware-specific candidate (e.g. zx-spectrum-only) under
    target unknown/pure-z80 is rejected unless it lists "all"/"pure-z80".

Candidate JSON fields used by the veto: `tags` (list), `targets` (list).
Use "all" in `targets` for portable CPU-core techniques.
Dangerous candidates without known danger tags are rejected.
This script ranks candidates; the caller still enforces multi-target gates.
`PROVEN` requires at least one current evidence card:
`{"kind": "measurement|fresh-artifact|trace|test|current-source",
"ref": "...", "current": true}`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11: policy veto via --forbidden/--target only.
    tomllib = None

CONF = {"PROVEN": 5, "LIKELY": 3, "SPECULATIVE": 1, "REJECT": -10}
LANE_PENALTY = {"SAFE": 0, "CHECK": 1, "MEDIUM": 2, "DANGEROUS": 6, "REJECT": 99}
NUMERIC_FIELDS = {
    "bytes",
    "speed",
    "ram",
    "ux",
    "latency",
    "simplicity",
    "validation",
    "low_risk",
    "reversible",
}
PHYSICAL_INT_FIELDS = {"overlay_before", "overlay_after", "overlay_delta"}
DANGER_TAGS = {
    "undocumented",
    "smc",
    "sp_abuse",
    "interrupt_windows",
    "hardware_timing",
    "banking_changes",
}
RELEASE_FORBIDDEN_TAGS = {
    "undocumented",
    "smc",
    "sp_abuse",
    "interrupt_windows",
}
PRIORITY_TO_PROFILE = {
    "size": "size",
    "resident-size": "size",
    "load-time": "size",
    "speed": "speed",
    "latency": "network-app",
    "ux": "network-app",
    "ram": "size",
}
PROFILES = {
    "size": {"bytes": 3, "speed": 1, "ram": 2, "ux": 1},
    "speed": {"bytes": 1, "speed": 3, "ram": 1, "ux": 2},
    "network-app": {"bytes": 1, "speed": 1, "ram": 1, "ux": 3, "latency": 4},
    "graphics-render": {"bytes": 1, "speed": 3, "ram": 1, "ux": 3, "latency": 2},
    "balanced": {"bytes": 2, "speed": 2, "ram": 2, "ux": 2, "latency": 2},
}
# Targets that do not commit to specific hardware.
PORTABLE_TARGETS = {"all", "pure-z80", "unknown"}
PROOF_KINDS = {"measurement", "fresh-artifact", "trace", "test", "current-source"}


def has_evidence(c):
    ev = c.get("evidence")
    if isinstance(ev, list):
        return bool(ev)
    return bool(str(ev or "").strip())


def has_current_proof(c):
    evidence = c.get("evidence")
    if not isinstance(evidence, list):
        return False
    return any(
        isinstance(item, dict)
        and str(item.get("kind", "")).strip().lower() in PROOF_KINDS
        and bool(str(item.get("ref", "")).strip())
        and item.get("current") is True
        for item in evidence
    )


def as_int(value):
    return 0 if value is None else int(value)


def load_policy_data(policy_path):
    if not policy_path:
        return {}
    p = Path(policy_path)
    if not p.is_file():
        raise SystemExit(f"policy file not found: {policy_path}")
    if tomllib is None:
        raise SystemExit(
            "reading --policy requires Python 3.11+ tomllib; "
            "use --forbidden/--target or run with Python 3.11+"
        )
    try:
        return tomllib.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise SystemExit(f"invalid policy TOML {policy_path}: {e}") from e


def load_forbidden(policy_data, extra):
    """Forbidden tag set from a z80opt.toml [forbidden] table, maintainability, plus --forbidden."""
    table = policy_data.get("forbidden", {})
    if not isinstance(table, dict):
        raise SystemExit("invalid policy TOML: [forbidden] must be a table")
    forbidden = {str(k).strip().lower() for k, v in table.items() if v is True}
    explicit_allowed = {str(k).strip().lower() for k, v in table.items() if v is False}
    constraints = policy_data.get("constraints", {})
    if isinstance(constraints, dict):
        maint = str(constraints.get("maintainability", "") or "").strip().lower()
        if maint == "release":
            forbidden |= (RELEASE_FORBIDDEN_TAGS - explicit_allowed)
    forbidden |= {t.strip().lower() for t in (extra or "").split(",") if t.strip()}
    return forbidden


def load_target(policy_data, override):
    if override:
        return override.strip().lower()
    return str(policy_data.get("target", "") or "").strip().lower()


def load_constraints(policy_data):
    constraints = policy_data.get("constraints", {})
    if not isinstance(constraints, dict):
        raise SystemExit("invalid policy TOML: [constraints] must be a table")
    return constraints


def load_target_gates(policy_data):
    """Per-target resident_ceiling and stack_gap_floor gates from [targets.<name>]."""
    raw = policy_data.get("targets", {})
    if not raw:
        return {}
    if not isinstance(raw, dict):
        raise SystemExit("invalid policy TOML: [targets] must be a table")
    gates = {}
    for name, cfg in raw.items():
        if not isinstance(cfg, dict):
            raise SystemExit(f"invalid policy TOML: [targets.{name}] must be a table")
        entry = {}
        for key in ("resident_ceiling", "stack_gap_floor"):
            if key in cfg and cfg[key] is not None:
                val = cfg[key]
                if isinstance(val, bool) or not isinstance(val, int) or val < 0:
                    raise SystemExit(
                        f"invalid policy TOML: targets.{name}.{key} must be a non-negative integer"
                    )
                if val > 0:
                    entry[key] = val
        if entry:
            gates[str(name).strip().lower()] = entry
    return gates


def resolve_profile(policy_data, cli_profile):
    if cli_profile and cli_profile != "auto":
        return cli_profile
    priorities = policy_data.get("priority", [])
    if isinstance(priorities, list):
        for item in priorities:
            mapped = PRIORITY_TO_PROFILE.get(str(item).strip().lower())
            if mapped:
                return mapped
    return "balanced"


def string_list(c, field):
    value = c.get(field, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    out = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{field} entries must be strings")
        item = item.strip().lower()
        if item:
            out.append(item)
    return out


def schema_reject_reason(c):
    lane = str(c.get("lane", "SAFE")).upper()
    if lane not in LANE_PENALTY:
        return f"invalid lane: {c.get('lane')}"
    conf = str(c.get("confidence", "SPECULATIVE")).upper()
    if conf not in CONF:
        return f"invalid confidence: {c.get('confidence')}"
    for field in NUMERIC_FIELDS:
        if field not in c or c[field] is None:
            continue
        value = c[field]
        if isinstance(value, bool) or not isinstance(value, int):
            return f"{field} must be an integer"
        # out-of-range ints are clamped with a warning, not rejected (see clamp_numeric)
    for field in PHYSICAL_INT_FIELDS:
        if field not in c or c[field] is None:
            continue
        value = c[field]
        if isinstance(value, bool) or not isinstance(value, int):
            return f"{field} must be an integer 0..5"
        if field != "overlay_delta" and value < 0:
            return f"{field} must be >= 0"
    try:
        tags = set(string_list(c, "tags"))
        string_list(c, "targets")
    except ValueError as e:
        return str(e)
    if lane == "DANGEROUS" and not (tags & DANGER_TAGS):
        return "DANGEROUS candidates require at least one known danger tag"
    return None


def clamp_numeric(c):
    """Clamp 0..5 score fields into range in place; record any clamp as a warning.

    Type is already validated by schema_reject_reason; here only out-of-range
    ints are corrected so a single slip (e.g. speed:7) does not drop a real win.
    """
    for field in NUMERIC_FIELDS:
        value = c.get(field)
        if not isinstance(value, int) or isinstance(value, bool):
            continue
        clamped = 0 if value < 0 else 5 if value > 5 else value
        if clamped != value:
            c[field] = clamped
            c.setdefault("schema_warnings", []).append(
                f"{field} {value} clamped to {clamped} (0..5)"
            )


def touches_overlay(c):
    words = []
    for field in ("category", "zone"):
        value = c.get(field)
        if isinstance(value, str):
            words.append(value.lower())
    for field in ("zones", "tags"):
        try:
            words.extend(string_list(c, field))
        except ValueError:
            pass
    text = " ".join(words)
    return "overlay" in text or "bank" in text or "banking_changes" in text


def overlay_reject_reason(c, constraints):
    overlay_size = constraints.get("overlay_size", 0)
    if isinstance(overlay_size, bool) or not isinstance(overlay_size, int):
        raise SystemExit(
            "invalid policy TOML: constraints.overlay_size must be an integer"
        )
    declares_overlay = (
        c.get("overlay_after") is not None or c.get("overlay_before") is not None
    )
    if overlay_size <= 0 or not (touches_overlay(c) or declares_overlay):
        return None
    overlay_after = c.get("overlay_after")
    if overlay_after is None:
        c["confidence"] = "SPECULATIVE"
        c["evidence_gate"] = "demoted: missing overlay_after for overlay_size policy"
        return None
    if overlay_after > overlay_size:
        return f"overlay_after {overlay_after} exceeds overlay_size {overlay_size}"
    return None


def target_gates_reject_reason(c, target_gates):
    if not target_gates:
        return None
    metrics = c.get("target_metrics")
    if metrics is None:
        if str(c.get("confidence", "SPECULATIVE")).upper() == "PROVEN":
            c["confidence"] = "LIKELY"
            c["evidence_gate"] = (
                "demoted: multi-target policy requires target_metrics for PROVEN"
            )
        return None
    if not isinstance(metrics, dict):
        return "target_metrics must be a table of per-target measurements"
    norm_metrics = {str(k).strip().lower(): v for k, v in metrics.items()}
    missing = sorted(set(target_gates) - set(norm_metrics))
    if missing:
        return "missing target_metrics for declared target(s): " + ", ".join(missing)
    for tname, gate in sorted(target_gates.items()):
        trow = norm_metrics.get(tname)
        if not isinstance(trow, dict):
            return f"target_metrics.{tname} must be an object"
        ceiling = gate.get("resident_ceiling")
        if ceiling is not None:
            used = trow.get("resident_used", trow.get("resident_after"))
            if used is None:
                c["confidence"] = "SPECULATIVE"
                c["evidence_gate"] = (
                    f"demoted: missing resident_used for target {tname}"
                )
            elif isinstance(used, bool) or not isinstance(used, int):
                return f"target_metrics.{tname}.resident_used must be an integer"
            elif used > ceiling:
                return f"target {tname} resident_used {used} exceeds resident_ceiling {ceiling}"
        floor = gate.get("stack_gap_floor")
        if floor is not None:
            gap = trow.get("stack_gap", trow.get("stack_gap_after"))
            if gap is None:
                c["confidence"] = "SPECULATIVE"
                c["evidence_gate"] = f"demoted: missing stack_gap for target {tname}"
            elif isinstance(gap, bool) or not isinstance(gap, int):
                return f"target_metrics.{tname}.stack_gap must be an integer"
            elif gap < floor:
                return f"target {tname} stack_gap {gap} below stack_gap_floor {floor}"
    return None


def policy_reject_reason(c, forbidden, target, constraints, target_gates=None):
    """Return a reject reason string if policy vetoes this candidate, else None."""
    tags = set(string_list(c, "tags"))
    overlay_reason = overlay_reject_reason(c, constraints)
    if overlay_reason:
        return overlay_reason
    gate_reason = target_gates_reject_reason(c, target_gates or {})
    if gate_reason:
        return gate_reason
    hit = tags & forbidden
    if hit:
        return "forbidden tags: " + ", ".join(sorted(hit))
    if target:
        targets = set(string_list(c, "targets"))
        if not targets:
            return "missing targets under active target policy"
        if "all" in targets or target in targets:
            return None
        if target in PORTABLE_TARGETS and not (targets & PORTABLE_TARGETS):
            return f"hardware-specific candidate under target={target}"
        if target not in PORTABLE_TARGETS and target not in targets:
            return f"wrong target: needs {sorted(targets)}, active={target}"
    return None


def score(c, profile, forbidden, target, constraints=None, target_gates=None):
    constraints = constraints or {}
    schema_reason = schema_reject_reason(c)
    if schema_reason:
        c["lane"] = "REJECT"
        c["confidence"] = "REJECT"
        c["schema_error"] = schema_reason
        return -999
    clamp_numeric(c)
    reason = policy_reject_reason(c, forbidden, target, constraints, target_gates)
    if reason:
        c["lane"] = "REJECT"
        c["confidence"] = "REJECT"
        c["policy_veto"] = reason
        return -999
    if str(c.get("lane", "SAFE")).upper() == "REJECT":
        return -999
    conf = str(c.get("confidence", "SPECULATIVE")).upper()
    if conf == "PROVEN" and not has_current_proof(c):
        conf = "LIKELY" if has_evidence(c) else "SPECULATIVE"
        c["confidence"] = conf
        c["evidence_gate"] = "demoted: PROVEN requires a current structured evidence card"
    elif not has_evidence(c):
        conf = "SPECULATIVE"
        c["confidence"] = "SPECULATIVE"
        c["evidence_gate"] = "demoted: missing evidence"
    weights = PROFILES.get(profile, PROFILES["balanced"])
    total = 0
    for f, w in weights.items():
        total += as_int(c.get(f, 0)) * w
    total += as_int(c.get("simplicity", 0))
    total += as_int(c.get("validation", 0))
    total += as_int(c.get("low_risk", 0)) * 2
    total += as_int(c.get("reversible", 0))
    total += CONF.get(conf, 1) * 2
    total -= LANE_PENALTY.get(str(c.get("lane", "SAFE")).upper(), 0)
    if c.get("stale_artifacts") and conf == "PROVEN":
        c["confidence"] = "LIKELY"
        c["evidence_gate"] = "demoted: stale artifacts"
        total -= 4
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", help="JSON list of candidates; stdin if omitted")
    ap.add_argument("--profile", default="balanced", choices=sorted([*PROFILES, "auto"]))
    ap.add_argument("--policy", help="path to z80opt.toml for forbidden/target veto")
    ap.add_argument("--forbidden", help="comma list of forbidden tags (adds to policy)")
    ap.add_argument("--target", help="active target override (beats policy file)")
    args = ap.parse_args()
    policy_data = load_policy_data(args.policy)
    forbidden = load_forbidden(policy_data, args.forbidden)
    target = load_target(policy_data, args.target)
    constraints = load_constraints(policy_data)
    target_gates = load_target_gates(policy_data)
    profile = resolve_profile(policy_data, args.profile)
    data = json.loads(
        open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    )
    if not isinstance(data, list) or any(not isinstance(c, dict) for c in data):
        raise SystemExit("candidate JSON must be a list of objects")
    for c in data:
        c["score"] = score(
            c, profile, forbidden, target, constraints, target_gates
        )
    data.sort(key=lambda x: x["score"], reverse=True)
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
