#!/usr/bin/env python3
"""Bounded local runtime for Z80 Jev decisions. Python 3.10+, standard library.

Adapted from the supplied research-workflow 0.2.0 runtime. No project commands,
model spawning, credential copies, automatic retries, or provider switching.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Callable, Iterator

VERSION = "0.9.0"
SKILL_DIR = Path(__file__).resolve().parent.parent
POLICY_PATH = SKILL_DIR / "references" / "jev-policy.json"
MAX_STATE_BYTES = 4_194_304
ENDPOINT = "https://opencode.ai/zen/v1/systemone"
Runner = Callable[[Path, str, Path | None, str, dict[str, Any]], dict[str, Any]]


class RouterError(Exception):
    """Safe machine-readable reason; do not include material or credentials."""

def encode(value: Any, *, canonical: bool = False) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, allow_nan=False,
                          sort_keys=canonical).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise RouterError("invalid_json_value") from exc

def decode(raw: bytes) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    def reject(value: str) -> None:
        raise ValueError("non-finite number")

    try:
        result = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique,
                            parse_constant=reject)
        encode(result)  # Also rejects exponent overflow, e.g. 1e999.
        return result
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise RouterError("invalid_json") from exc

def read_json(path: Path, limit: int = MAX_STATE_BYTES) -> Any:
    try:
        with path.open("rb") as stream:
            raw = stream.read(limit + 1)
    except OSError as exc:
        raise RouterError("unreadable_file") from exc
    if len(raw) > limit:
        raise RouterError("file_too_large")
    return decode(raw)

def digest(value: Any) -> str:
    return hashlib.sha256(encode(value, canonical=True)).hexdigest()

def atomic_json(path: Path, value: Any) -> None:
    """Replace only our scratch state; never write a caller's source file."""
    temporary: str | None = None
    try:
        fd, temporary = tempfile.mkstemp(prefix=".state-", dir=str(path.parent))
        with os.fdopen(fd, "wb") as stream:
            stream.write(encode(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        raise RouterError("scratch_write_failed") from exc
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)

def probability(value: Any) -> bool:
    return (type(value) in (int, float) and 0 <= value <= 1 and math.isfinite(value))

def locate_client(explicit: Path | None = None) -> Path:
    """Only known skill locations; no recursive search, installation or imports."""
    override = explicit or os.environ.get("Z80_JEV_CLIENT")
    if override:
        candidate = Path(override).expanduser().resolve()
        if not candidate.is_file():
            raise RouterError("client_not_found")
        return candidate
    candidates = [
        SKILL_DIR.parent / "jev" / "scripts" / "jev.py",
        Path.home() / ".agents" / "skills" / "jev" / "scripts" / "jev.py",
        Path.home() / ".codex" / "skills" / "jev" / "scripts" / "jev.py",
    ]
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        candidates.append(Path(codex_home).expanduser() / "skills" / "jev" / "scripts" / "jev.py")
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise RouterError("client_not_found")

def run_client(client: Path, command: str, request_path: Path | None,
               model: str, policy: dict[str, Any]) -> dict[str, Any]:
    args = [sys.executable, str(client), command, "--model", model,
            "--timeout", str(policy["client_timeout_seconds"])]
    if request_path is not None:
        args += ["--request", str(request_path)]
    try:
        process = subprocess.run(args, capture_output=True, check=False,
                                 timeout=policy["subprocess_timeout_seconds"])
    except subprocess.TimeoutExpired as exc:
        raise RouterError("client_timeout") from exc
    except OSError as exc:
        raise RouterError("client_execution_failed") from exc
    if len(process.stdout) > MAX_STATE_BYTES:
        raise RouterError("client_output_too_large")
    result = decode(process.stdout)
    if not isinstance(result, dict):
        raise RouterError("invalid_client_output")
    # No stderr, raw provider body or arbitrary error text reaches the receipt.
    if process.returncode != 0 or result.get("ok") is not True:
        error = result.get("error", {})
        kind = error.get("kind") if isinstance(error, dict) else None
        status = error.get("http_status") if isinstance(error, dict) else None
        if type(status) is int and 100 <= status <= 599:
            raise RouterError("http_" + str(status))
        allowed = {"configuration", "input", "response", "network", "cancelled", "http"}
        raise RouterError("client_" + (kind if kind in allowed else "failed"))
    return result

def init_task(policy: dict[str, Any], scratch: Path | None = None,
              max_calls: int | None = None, model: str | None = None) -> dict[str, Any]:
    limit = policy["max_calls_per_task"] if max_calls is None else max_calls
    selected = model or os.environ.get("JEV_MODEL") or policy["default_model"]
    if type(limit) is not int or not 0 <= limit <= policy["max_calls_per_task"]:
        raise RouterError("invalid_call_limit")
    if selected not in policy["models"]:
        raise RouterError("unsupported_model")
    if scratch is not None and not scratch.is_dir():
        raise RouterError("scratch_not_found")
    task_dir = Path(tempfile.mkdtemp(prefix="z80-skills-jev-", dir=scratch)).resolve()
    state = {
        "schema_version": 1, "router_version": VERSION, "policy_sha256": digest(policy),
        "call_limit": limit, "calls_reserved": 0, "model": selected,
        "service_failed": False, "attempts": {}, "cache": {},
    }
    atomic_json(task_dir / "state.json", state)
    return {"ok": True, "task_dir": str(task_dir), "call_limit": limit,
            "model": selected, "network_attempted": False,
            "audit_path": str(task_dir / "audit.jsonl")}

@contextmanager
def task_lock(task_dir: Path) -> Iterator[None]:
    """Fail closed on overlap or an interrupted owner; do not reset a budget."""
    if not task_dir.is_dir():
        raise RouterError("task_not_found")
    lock = task_dir / ".router.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise RouterError("task_busy_or_interrupted") from exc
    except OSError as exc:
        raise RouterError("scratch_write_failed") from exc
    try:
        os.close(fd)
        yield
    finally:
        lock.unlink(missing_ok=True)

def load_state(task_dir: Path, policy: dict[str, Any]) -> dict[str, Any]:
    for name in ("state.json", "audit.jsonl"):
        if (task_dir / name).is_symlink():
            raise RouterError("unsafe_scratch_path")
    state = read_json(task_dir / "state.json")
    try:
        valid = (state["schema_version"] == 1 and state["router_version"] == VERSION
                 and state["policy_sha256"] == digest(policy)
                 and type(state["call_limit"]) is int
                 and 0 <= state["call_limit"] <= policy["max_calls_per_task"]
                 and type(state["calls_reserved"]) is int
                 and 0 <= state["calls_reserved"] <= state["call_limit"]
                 and state["model"] in policy["models"]
                 and type(state["service_failed"]) is bool
                 and isinstance(state["attempts"], dict) and isinstance(state["cache"], dict))
    except (KeyError, TypeError) as exc:
        raise RouterError("invalid_task_state") from exc
    if not valid:
        raise RouterError("invalid_task_state_or_changed_policy")
    return state

def audit(task_dir: Path, report: dict[str, Any]) -> None:
    entry = dict(report, timestamp=datetime.now(timezone.utc).isoformat())
    try:
        fd = os.open(task_dir / "audit.jsonl", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(encode(entry) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise RouterError("audit_write_failed") from exc

def inspect_task(task_dir: Path, policy: dict[str, Any]) -> dict[str, Any]:
    with task_lock(task_dir):
        state = load_state(task_dir, policy)
        path = task_dir / "audit.jsonl"
        entries = []
        if path.exists():
            try:
                with path.open("rb") as stream:
                    for line in stream:
                        if len(line) > MAX_STATE_BYTES:
                            raise RouterError("audit_entry_too_large")
                        entries.append(decode(line))
            except OSError as exc:
                raise RouterError("audit_read_failed") from exc
        return {"ok": True, "network_attempted": False, "calls_reserved": state["calls_reserved"],
                "call_limit": state["call_limit"], "service_failed": state["service_failed"],
                "cached_requests": len(state["cache"]), "audit_path": str(path), "entries": entries}

def doctor(policy: dict[str, Any], client_path: Path | None = None) -> dict[str, Any]:
    client = locate_client(client_path)
    model = os.environ.get("JEV_MODEL") or policy["default_model"]
    if model not in policy["models"]:
        raise RouterError("unsupported_model")
    result = run_client(client, "doctor", None, model, policy)
    if result.get("requests_sent") != 0 or result.get("key_found") is not True:
        raise RouterError("unverified_local_check")
    return {"ok": True, "router_version": VERSION, "client_path": str(client),
            "key_found": True, "model": model, "network_attempted": False,
            "authentication_tested": False}

def load_policy() -> dict[str, Any]:
    policy = read_json(POLICY_PATH)
    try:
        if (policy['max_calls_per_task'] != 2 or policy['max_questions_per_call'] != 32
                or policy['max_packet_bytes'] != 131072
                or set(policy['actions']) != {'procedure', 'assignment', 'delivery', 'specialist'}
                or set(policy['scoring']) != {'audit', 'shrink', 'optimize'}):
            raise RouterError('invalid_policy')
        for action in policy['actions'].values():
            for route in action['routes'].values():
                if not probability(route['threshold']):
                    raise RouterError('invalid_threshold')
        for config in policy['scoring'].values():
            if (set(config['weights']) != {'relevance','support','validation','scope'}
                    or set(config['thresholds']) != set(config['weights'])
                    or not all(probability(v) for v in config['weights'].values())
                    or not all(probability(v) for v in config['thresholds'].values())
                    or not math.isclose(sum(config['weights'].values()),1,abs_tol=1e-9)):
                raise RouterError('invalid_scoring_policy')
    except (KeyError, TypeError, AttributeError) as exc:
        raise RouterError('invalid_policy') from exc
    return policy


def normalize_result(result: Any, payload: dict[str, Any], policy: dict[str, Any],
                     *, cached: bool = False) -> dict[str, Any]:
    """Validate a native receipt; confidence is never a probability of correctness."""
    if (not isinstance(result, dict) or result.get('ok') is not True
            or type(result.get('http_status')) is not int or not 200 <= result['http_status'] < 300
            or type(result.get('requests_sent')) is not int or result['requests_sent'] != 1
            or result.get('requested_model') != payload['model']
            or result.get('endpoint') != ENDPOINT
            or not isinstance(result.get('request_sha256'),str)
            or not re.fullmatch(r'[0-9a-f]{64}',result['request_sha256'])
            or (not cached and result['request_sha256'] != hashlib.sha256(encode(payload)).hexdigest())
            or (cached and result.get('canonical_fingerprint') != digest(payload))):
        raise RouterError('unverified_client_receipt')
    response = result.get('response')
    if not isinstance(response,dict) or response.get('model') not in policy['accepted_response_models']:
        raise RouterError('unexpected_response_model')
    answers = response.get('answers')
    if not isinstance(answers,dict) or set(answers) != set(payload['questions']):
        raise RouterError('answer_ids_mismatch')
    clean = {}
    for ident,question in payload['questions'].items():
        answer = answers[ident]
        kind = question['type']
        if not isinstance(answer,dict) or answer.get('type') != kind or not probability(answer.get('confidence')):
            raise RouterError('invalid_answer_type_or_confidence')
        expected = set(question['criteria']) if kind == 'choice' else {str(i) for i in range(len(question['criteria']))}
        probs = answer.get('probabilities')
        if (not isinstance(probs,dict) or set(probs) != expected
                or not all(probability(p) for p in probs.values())
                or not math.isclose(sum(probs.values()),1,rel_tol=0,abs_tol=.02)):
            raise RouterError('invalid_probabilities')
        item = {'type':kind, 'confidence':answer['confidence'], 'probabilities':probs}
        if kind == 'choice':
            choice = answer.get('choice')
            if not isinstance(choice,str) or choice not in probs or probs[choice] + .02 < max(probs.values()):
                raise RouterError('invalid_choice')
            item['choice'] = choice
        elif kind == 'score':
            value = answer.get('score')
            top = len(expected)-1
            if (type(value) not in (int,float) or not math.isfinite(value) or not 0 <= value <= top
                    or not math.isclose(value, sum(int(k)*p for k,p in probs.items()), rel_tol=0,abs_tol=.06)):
                raise RouterError('invalid_score_or_distribution_mismatch')
            item['score'] = value
        else:
            raise RouterError('unsupported_question_type')
        clean[ident] = item
    usage = response.get('usage',{})
    usage = ({k:v for k,v in usage.items() if k in {'input_tokens','output_tokens','total_tokens'}
              and type(v) is int and v >= 0} if isinstance(usage,dict) else {})
    return {'answers':clean, 'actual_model':response['model'], 'usage':usage,
            'http_status':result['http_status'], 'request_sha256':result['request_sha256']}


def exchange(payload: dict[str, Any], task_dir: Path, policy: dict[str, Any],
             authorized: bool, client_path: Path | None = None,
             runner: Runner = run_client) -> dict[str, Any]:
    """One bounded batch. Same task/session is mandatory for routing and scoring."""
    if type(authorized) is not bool:
        raise RouterError('invalid_external_authorization')
    if (len(encode(payload)) > policy['max_packet_bytes']
            or not 1 <= len(payload.get('questions',{})) <= policy['max_questions_per_call']):
        raise RouterError('request_size_or_question_limit')
    with task_lock(task_dir):
        state = load_state(task_dir,policy)
        if payload.get('model') != state['model']:
            raise RouterError('session_model_mismatch')
        fingerprint = digest(payload)
        report = {'ok':True, 'query_status':'skipped', 'network_attempted':False,
                  'requests_sent':0, 'requested_model':state['model'],
                  'request_fingerprint':fingerprint, 'answers':{},
                  'audit_path':str(task_dir/'audit.jsonl')}
        normalized = None
        if fingerprint in state['cache']:
            try:
                normalized = normalize_result(state['cache'][fingerprint],payload,policy,cached=True)
                report['query_status']='cache_hit'
            except RouterError:
                report['reason']='invalid_cached_receipt'
        elif not authorized:
            report['reason']='external_data_not_authorized'
        elif fingerprint in state['attempts']:
            report['reason']='same_request_already_attempted'
        elif state['service_failed']:
            report['reason']='service_disabled_for_task'
        elif state['calls_reserved'] >= state['call_limit']:
            report['reason']='task_call_budget_exhausted'
        else:
            try:
                client = locate_client(client_path)
                with tempfile.TemporaryDirectory(prefix='request-',dir=task_dir) as directory:
                    request_path = Path(directory)/'request.json'
                    atomic_json(request_path,payload)
                    check = runner(client,'check',request_path,state['model'],policy)
                    if (check.get('ok') is not True or type(check.get('requests_sent')) is not int
                            or check['requests_sent'] != 0 or check.get('mode') != 'offline-schema-check'
                            or check.get('model') != state['model']
                            or check.get('questions') != len(payload['questions'])):
                        raise RouterError('offline_check_failed')
                    state['calls_reserved'] += 1
                    state['attempts'][fingerprint]='reserved'
                    atomic_json(task_dir/'state.json',state)
                    report.update(network_attempted=True,requests_sent=None)
                    result = runner(client,'run',request_path,state['model'],policy)
                    normalized = normalize_result(result,payload,policy)
                    state['cache'][fingerprint] = {
                        'ok':True, 'http_status':normalized['http_status'], 'requests_sent':1,
                        'requested_model':state['model'], 'endpoint':ENDPOINT,
                        'request_sha256':normalized['request_sha256'], 'canonical_fingerprint':fingerprint,
                        'response':{'model':normalized['actual_model'],'answers':normalized['answers'],
                                    'usage':normalized['usage']}}
                    state['attempts'][fingerprint]='complete'
                    atomic_json(task_dir/'state.json',state)
                    report.update(query_status='received',requests_sent=1)
            except RouterError as exc:
                reason=str(exc)
                report.update(query_status='failed',reason=reason)
                if report['network_attempted'] and re.fullmatch(r'http_[1-5][0-9]{2}',reason):
                    report.update(http_status=int(reason[5:]),requests_sent=1)
                state['service_failed']=True
                if fingerprint in state['attempts']:
                    state['attempts'][fingerprint]='failed'
                atomic_json(task_dir/'state.json',state)
        if normalized is not None:
            report.update(actual_model=normalized['actual_model'], http_status=normalized['http_status'],
                          original_request_sha256=normalized['request_sha256'], answers=normalized['answers'],
                          usage=normalized['usage'] if report['query_status']=='received' else {})
        report.update(calls_reserved=state['calls_reserved'],call_limit=state['call_limit'])
        # Contains IDs and decisions, never source excerpts or credentials.
        audit(task_dir,report)
        return report


def task_model(task_dir: Path, policy: dict[str, Any]) -> str:
    with task_lock(task_dir):
        return load_state(task_dir,policy)['model']


def record_decisions(task_dir: Path, report: dict[str, Any]) -> None:
    with task_lock(task_dir):
        audit(task_dir,report)
