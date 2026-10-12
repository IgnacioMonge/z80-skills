#!/usr/bin/env python3
"""shrink-agent: unattended, evidence-gated binary-size reduction for z88dk projects.

The orchestrator owns every decision. Claude only proposes edits; a candidate
is committed only when every configured target builds, the summed linked size
falls, no target grows, configured tests pass, and an independent review call
finds no behavioural difference.

All work happens in a disposable git worktree on a new branch
``shrink/auto-<timestamp>``. The primary checkout is never modified; the
worktree is removed at the end and the branch keeps the accepted commits.

Usage (see README.md):
    python shrink_agent.py --config examples/bitstream.toml --iterations 20
    python shrink_agent.py --config ... --dry-run          # baseline only, no API
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import fnmatch
import json
import os
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import mapfile  # noqa: E402
from llm import DEFAULT_PRICES, ApiFatal, Claude, load_api_key, load_env  # noqa: E402

REPO_ROOT = HERE.parent.parent
DEFAULT_KNOWLEDGE = [
    "skills/shrink-z80/references/size-blackbook.md",
    "skills/shrink-z80/references/c-patterns.md",
    "skills/shrink-z80/references/asm-micro.md",
    "skills/optimize-z80/references/z88dk-sdcc-abi.md",
    "skills/optimize-z80/references/z80-proof-obligations.md",
    "skills/optimize-z80/references/traps.md",
]
REVIEW_KNOWLEDGE = DEFAULT_KNOWLEDGE[3:]
MAX_EXCERPT_LINES = 400

PROPOSE_TOOL = {
    "name": "submit_candidate",
    "description": "Submit exactly one behaviour-preserving size-reduction edit for the target routine, or decline.",
    "input_schema": {
        "type": "object",
        "properties": {
            "analysis": {
                "type": "string",
                "description": "Where the bytes go in the current code, the transformation, and why behaviour is identical.",
            },
            "decision": {"type": "string", "enum": ["edit", "decline"]},
            "edits": {
                "type": "array",
                "description": "Exact search/replace edits. 'old' must occur exactly once in 'file'.",
                "items": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string", "description": "Repository-relative path, forward slashes."},
                        "old": {"type": "string"},
                        "new": {"type": "string"},
                    },
                    "required": ["file", "old", "new"],
                },
            },
            "summary": {"type": "string", "description": "Imperative commit subject, at most 60 characters."},
            "expected_saving": {"type": "integer", "description": "Estimated bytes saved."},
        },
        "required": ["analysis", "decision"],
    },
}

REVIEW_TOOL = {
    "name": "submit_verdict",
    "description": "Judge whether the patched code is behaviourally identical to the original for every input and machine state.",
    "input_schema": {
        "type": "object",
        "properties": {
            "analysis": {"type": "string"},
            "verdict": {"type": "string", "enum": ["EQUIVALENT", "DIFFERENT", "UNSURE"]},
            "issues": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["analysis", "verdict"],
    },
}

PROPOSER_ROLE = """You are a Z80 / ZX Spectrum size-optimisation engineer working inside an automated loop.
Each request names ONE target routine. Propose ONE edit that makes the linked binary smaller while keeping
behaviour bit-for-bit identical: same outputs, side effects, memory writes, I/O order, flags and registers
that callers or interrupt code can observe, timing where the code is timing-sensitive, and the same ABI.

Hard rules:
- Do not change any function signature, calling convention, global layout, exported label, string text,
  protocol byte or user-visible behaviour.
- Edit only files listed as editable. Keep edits local to the target routine; touch a helper only if the
  saving requires it and the helper's behaviour is unchanged for all its callers.
- Each 'old' string must be copied exactly from the source shown and occur exactly once in its file.
- Prefer transformations with a clear proof (dead stores, redundant reloads, shared tails, cheaper
  idioms with identical flag/register effects, table/data compaction with identical decoded values).
- If you see no safe saving, decline. A decline is a correct answer; an unsafe edit is not.
The build, byte measurement and an independent reviewer will check you. Your claims are not evidence."""

REVIEWER_ROLE = """You are an adversarial Z80 code reviewer. You receive an original routine and a patch made to
reduce its size. Decide whether the patched program behaves identically to the original for every input,
every caller, and every machine state, including flags and registers observable by callers, memory side
effects, I/O ordering, interrupt interaction, stack depth limits and self-modifying or computed jumps.
Answer EQUIVALENT only if you can justify it; DIFFERENT if you find a concrete divergence (name the input or
path); UNSURE if equivalence depends on facts you cannot see. Byte savings are irrelevant to your verdict."""


# --------------------------------------------------------------------- config


@dataclass
class Target:
    name: str
    build: str
    map: str
    size_symbol: str
    origin: int
    binary: str = ""


@dataclass
class Config:
    name: str
    root: Path
    editable: list[str]
    targets: list[Target]
    rules: str = ""
    toolchain: str = ""
    exclude_routines: list[str] = field(default_factory=list)
    context_files: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    knowledge: list[str] = field(default_factory=lambda: list(DEFAULT_KNOWLEDGE))
    proposer_model: str = "claude-opus-5-5"
    reviewer_model: str = "claude-opus-5-5"
    max_rounds: int = 2
    max_attempts_per_routine: int = 1
    sections: list[str] = field(default_factory=lambda: ["code_compiler", "code_user"])
    min_routine_size: int = 16
    build_timeout: int = 900
    max_consecutive_failures: int = 12
    prices: dict = field(default_factory=lambda: dict(DEFAULT_PRICES))


def load_config(path: Path) -> Config:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    proj, agent = raw.get("project", {}), raw.get("agent", {})
    targets = [
        Target(
            name=t["name"],
            build=t["build"],
            map=t["map"],
            size_symbol=t.get("size_symbol", "__data_compiler_tail"),
            origin=int(t.get("origin", 0)),
            binary=t.get("binary", ""),
        )
        for t in raw.get("targets", [])
    ]
    if not targets:
        raise SystemExit("config: at least one [[targets]] entry is required")
    cfg = Config(
        name=proj.get("name") or Path(proj["root"]).name,
        root=Path(proj["root"]).resolve(),
        editable=list(proj.get("editable", [])),
        targets=targets,
        rules=proj.get("rules", ""),
        toolchain=proj.get("toolchain", ""),
        exclude_routines=list(proj.get("exclude_routines", [])),
        context_files=list(proj.get("context_files", [])),
        tests=list(proj.get("tests", [])),
    )
    if not cfg.editable:
        raise SystemExit("config: project.editable must list at least one glob")
    for key in (
        "proposer_model", "reviewer_model", "max_rounds", "max_attempts_per_routine", "sections",
        "min_routine_size", "build_timeout", "max_consecutive_failures", "knowledge",
    ):
        if key in agent:
            setattr(cfg, key, agent[key])
    for model, vals in raw.get("prices", {}).items():
        cfg.prices[model] = tuple(float(v) for v in vals)
    return cfg


# ------------------------------------------------------------------------ git


def run(cmd, cwd: Path, timeout: int | None = None, shell: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=str(cwd), shell=shell, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout,
    )


def git(cwd: Path, *args: str, check: bool = True) -> str:
    cp = run(["git", *args], cwd)
    if check and cp.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed in {cwd}: {cp.stderr.strip()}")
    return cp.stdout.strip()


class Worktree:
    def __init__(self, project: Path, path: Path, branch: str):
        self.project, self.path, self.branch = project, path, branch
        self.base = git(project, "rev-parse", "HEAD")

    @classmethod
    def create(cls, project: Path, stamp: str) -> "Worktree":
        branch = f"shrink/auto-{stamp}"
        path = Path(os.environ.get("TEMP") or "/tmp") / f"shrink-agent-{project.name.replace(' ', '_')}-{stamp}"
        git(project, "worktree", "add", "-q", "-b", branch, str(path), "HEAD")
        return cls(project, path.resolve(), branch)

    def _guard(self) -> None:
        if self.path == self.project.resolve() or not (self.path / ".git").is_file():
            raise RuntimeError(f"refusing to reset {self.path}: not the disposable worktree")

    def revert(self) -> None:
        self._guard()
        git(self.path, "reset", "-q", "--hard", "HEAD")
        git(self.path, "clean", "-fdq")

    def commit(self, message: str) -> str:
        self._guard()
        git(self.path, "add", "-A")
        git(self.path, "commit", "-q", "-m", message)
        return git(self.path, "rev-parse", "--short", "HEAD")

    def accepted(self) -> int:
        return int(git(self.project, "rev-list", "--count", f"{self.base}..{self.branch}"))

    def remove(self, keep: bool) -> None:
        if keep:
            return
        git(self.project, "worktree", "remove", "--force", str(self.path), check=False)
        git(self.project, "worktree", "prune", check=False)
        if self.accepted() == 0:
            git(self.project, "branch", "-D", self.branch, check=False)


# ---------------------------------------------------------------- build/measure


@dataclass
class TargetResult:
    ok: bool
    size: int = 0
    error: str = ""
    map_path: Path | None = None
    binary_path: Path | None = None


def build_all(cfg: Config, wt: Path, cache: Path, python: str) -> dict[str, TargetResult]:
    results: dict[str, TargetResult] = {}
    for t in cfg.targets:
        cmd = t.build.replace("{python}", python)
        try:
            cp = run(cmd, wt, timeout=cfg.build_timeout, shell=True)
        except subprocess.TimeoutExpired:
            results[t.name] = TargetResult(False, error=f"build timed out after {cfg.build_timeout}s")
            break
        if cp.returncode != 0:
            tail = (cp.stdout + cp.stderr).strip().splitlines()[-40:]
            results[t.name] = TargetResult(False, error="\n".join(tail))
            break
        tdir = cache / t.name
        tdir.mkdir(parents=True, exist_ok=True)
        map_src = wt / t.map
        if not map_src.is_file():
            results[t.name] = TargetResult(False, error=f"map not produced: {t.map}")
            break
        map_copy = tdir / "out.map"
        shutil.copyfile(map_src, map_copy)
        bin_copy = None
        if t.binary and (wt / t.binary).is_file():
            bin_copy = tdir / "out.bin"
            shutil.copyfile(wt / t.binary, bin_copy)
        try:
            size = mapfile.symbol_value(mapfile.parse_map(map_copy), t.size_symbol) - t.origin
        except KeyError as exc:
            results[t.name] = TargetResult(False, error=str(exc))
            break
        results[t.name] = TargetResult(True, size, map_path=map_copy, binary_path=bin_copy)
    return results


def run_tests(cfg: Config, wt: Path, python: str) -> str:
    for cmd in cfg.tests:
        cp = run(cmd.replace("{python}", python), wt, timeout=cfg.build_timeout, shell=True)
        if cp.returncode != 0:
            return f"test failed: {cmd}\n" + "\n".join((cp.stdout + cp.stderr).strip().splitlines()[-30:])
    return ""


# ---------------------------------------------------------------- source tools


def _strip_code(line: str, state: dict) -> str:
    """Remove comments, strings and char literals; track block comments across lines."""
    out, i, n = [], 0, len(line)
    while i < n:
        if state["block"]:
            j = line.find("*/", i)
            if j < 0:
                return "".join(out)
            state["block"], i = False, j + 2
            continue
        ch = line[i]
        if line.startswith("/*", i):
            state["block"], i = True, i + 2
        elif line.startswith("//", i):
            break
        elif ch in "\"'":
            i += 1
            while i < n and line[i] != ch:
                i += 2 if line[i] == "\\" else 1
            i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def c_function_span(lines: list[str], line_no: int) -> tuple[int, int]:
    """0-based inclusive span of the C function whose body starts at or after line_no (1-based)."""
    i = max(0, line_no - 1)
    while i < len(lines) and "{" not in lines[i]:
        i += 1
    if i >= len(lines):
        raise ValueError("function body not found")
    start = i
    while start > 0:
        prev = lines[start - 1].rstrip()
        if not prev.strip() or prev.endswith(("}", ";")) or prev.lstrip().startswith("#"):
            break
        start -= 1
    depth, opened, state = 0, False, {"block": False}
    for j in range(i, len(lines)):
        for ch in _strip_code(lines[j], state):
            if ch == "{":
                depth, opened = depth + 1, True
            elif ch == "}":
                depth -= 1
                if opened and depth == 0:
                    return start, j
    raise ValueError("unbalanced braces")


def asm_span(lines: list[str], line_no: int, next_lines: list[int]) -> tuple[int, int]:
    start = max(0, line_no - 1)
    while start > 0 and lines[start - 1].lstrip().startswith(";"):
        start -= 1
    later = [n for n in next_lines if n > line_no]
    end = (min(later) - 2) if later else len(lines) - 1
    while end > start and lines[end].lstrip().startswith(";"):
        end -= 1  # trailing comment block belongs to the next routine
    return start, end


def excerpt(cfg: Config, wt: Path, r: mapfile.Routine, all_routines: list[mapfile.Routine]) -> str:
    lines = (wt / r.file).read_text(encoding="utf-8", errors="replace").splitlines()
    if r.lang == "c":
        s, e = c_function_span(lines, r.line)
    else:
        others = [x.line for x in all_routines if x.file == r.file and x.name != r.name]
        s, e = asm_span(lines, r.line, others)
    if e - s + 1 > MAX_EXCERPT_LINES:
        raise ValueError(f"routine spans {e - s + 1} lines (> {MAX_EXCERPT_LINES})")
    return "\n".join(f"{n + 1:5d}| {lines[n]}" for n in range(s, e + 1))


def disassemble(t: Target, res: TargetResult, r: mapfile.Routine) -> str:
    if not res.binary_path or not res.map_path or not shutil.which("z88dk-dis"):
        return ""
    syms = [s for s in mapfile.parse_map(res.map_path) if s.name == r.symbol]
    if not syms:
        return ""
    addr = syms[0].addr
    cp = run(
        ["z88dk-dis", "-mz80", "-o", hex(t.origin), "-s", hex(addr), "-e", hex(addr + r.size), str(res.binary_path)],
        res.binary_path.parent,
    )
    out = cp.stdout.strip().splitlines()
    return "\n".join(out[:300]) if cp.returncode == 0 else ""


def editable(cfg: Config, rel: str) -> bool:
    rel = rel.replace("\\", "/")
    if rel.startswith("/") or ".." in Path(rel).parts or ":" in rel:
        return False
    return any(fnmatch.fnmatch(rel, g) for g in cfg.editable)


def apply_edits(cfg: Config, wt: Path, edits: list[dict]) -> tuple[str, str]:
    """Apply search/replace edits atomically (all or nothing). Returns (unified diff, error).

    Text is matched with LF line ends; each file keeps its original line-end style.
    """
    if not edits:
        return "", "no edits supplied"
    originals: dict[str, str] = {}
    current: dict[str, str] = {}
    newline: dict[str, str] = {}
    for ed in edits:
        rel = str(ed.get("file", "")).replace("\\", "/")
        if not editable(cfg, rel):
            return "", f"file not editable: {rel}"
        path = wt / rel
        if not path.is_file():
            return "", f"file not found: {rel}"
        if rel not in current:
            raw = path.read_bytes().decode("utf-8", errors="surrogateescape")
            newline[rel] = "\r\n" if "\r\n" in raw else "\n"
            originals[rel] = current[rel] = raw.replace("\r\n", "\n")
        old = str(ed.get("old", "")).replace("\r\n", "\n")
        new = str(ed.get("new", "")).replace("\r\n", "\n")
        count = current[rel].count(old) if old else 0
        if count != 1:
            return "", f"'old' text occurs {count} times in {rel} (must be exactly once)"
        current[rel] = current[rel].replace(old, new, 1)
    diff: list[str] = []
    for rel, text in current.items():
        if text != originals[rel]:
            diff += difflib.unified_diff(
                originals[rel].splitlines(keepends=True), text.splitlines(keepends=True), f"a/{rel}", f"b/{rel}", n=4
            )
    if not diff:
        return "", "edits produce no change"
    for rel, text in current.items():
        if text != originals[rel]:
            (wt / rel).write_bytes(text.replace("\n", newline[rel]).encode("utf-8", errors="surrogateescape"))
    return "".join(diff), ""


# ------------------------------------------------------------------- proposer


class LLMAgent:
    def __init__(self, cfg: Config, claude: Claude):
        self.cfg, self.claude = cfg, claude
        knowledge = "\n\n".join(_read_rel(REPO_ROOT, k) for k in cfg.knowledge)
        context = "\n\n".join(f"### {c}\n{_read_rel(cfg.root, c)}" for c in cfg.context_files)
        project = f"## Project: {cfg.name}\nEditable files (globs): {', '.join(cfg.editable)}\n"
        if cfg.toolchain:
            project += f"\nToolchain:\n{cfg.toolchain}\n"
        if cfg.rules:
            project += f"\nProject rules:\n{cfg.rules}\n"
        self.prop_system = [PROPOSER_ROLE, f"{project}\n{context}\n\n## Reference notes\n{knowledge}"]
        review_k = "\n\n".join(_read_rel(REPO_ROOT, k) for k in REVIEW_KNOWLEDGE)
        self.rev_system = [REVIEWER_ROLE, f"{project}\n\n## Reference notes\n{review_k}"]
        self.messages: list[dict] = []
        self._pending = None

    def start(self, prompt: str) -> dict:
        self.messages = [{"role": "user", "content": prompt}]
        return self._ask()

    def feedback(self, text: str) -> dict:
        call = self._pending
        self.messages += [
            {"role": "assistant", "content": call.assistant_content},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": call.tool_use_id, "content": text}]},
        ]
        return self._ask()

    def _ask(self) -> dict:
        call = self.claude.call(self.cfg.proposer_model, self.prop_system, self.messages, PROPOSE_TOOL, 16000)
        self.messages = call.history
        self._pending = call
        return call.data

    def review(self, prompt: str) -> dict:
        call = self.claude.call(
            self.cfg.reviewer_model, self.rev_system, [{"role": "user", "content": prompt}], REVIEW_TOOL, 12000
        )
        return call.data

    @property
    def spent(self) -> float:
        return self.claude.spent


class ScriptedAgent:
    """Offline stand-in for tests: replays proposals and verdicts from a JSON file."""

    def __init__(self, script: dict):
        self.proposals = list(script.get("proposals", []))
        self.verdicts = list(script.get("verdicts", []))
        self.spent = 0.0

    def start(self, prompt: str) -> dict:
        return self._next()

    def feedback(self, text: str) -> dict:
        return self._next()

    def _next(self) -> dict:
        item = self.proposals.pop(0) if self.proposals else {"analysis": "script exhausted", "decision": "decline"}
        if "raise_fatal" in item:
            raise ApiFatal(item["raise_fatal"])
        return item

    def review(self, prompt: str) -> dict:
        return self.verdicts.pop(0) if self.verdicts else {"analysis": "", "verdict": "EQUIVALENT"}


def _read_rel(base: Path, rel: str) -> str:
    p = (base / rel)
    return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""


# ----------------------------------------------------------------------- loop


class Log:
    def __init__(self, run_dir: Path):
        run_dir.mkdir(parents=True, exist_ok=True)
        self.compact = (run_dir / "shrink.log").open("a", encoding="utf-8")
        self.events = (run_dir / "events.jsonl").open("a", encoding="utf-8")

    def line(self, text: str) -> None:
        stamp = dt.datetime.now().strftime("%H:%M:%S")
        print(f"{stamp} {text}", flush=True)
        self.compact.write(f"{stamp} {text}\n")
        self.compact.flush()

    def event(self, **data) -> None:
        data["t"] = dt.datetime.now().isoformat(timespec="seconds")
        self.events.write(json.dumps(data, ensure_ascii=False) + "\n")
        self.events.flush()


def fmt_sizes(sizes: dict[str, int]) -> str:
    return ", ".join(f"{k} {v}" for k, v in sizes.items())


def candidate_queue(cfg: Config, rs: list[mapfile.Routine], attempts: dict[str, int], only: list[str]) -> list[mapfile.Routine]:
    out = []
    for r in rs:
        if only and r.name not in only:
            continue
        if r.size < cfg.min_routine_size or r.name in cfg.exclude_routines:
            continue
        if not editable(cfg, r.file) or attempts.get(r.name, 0) >= cfg.max_attempts_per_routine:
            continue
        out.append(r)
    return out


def proposal_prompt(cfg, r, src, dis, sizes, history) -> str:
    parts = [
        f"Target routine: {r.name} ({r.lang}, {r.size} bytes in {r.section}, defined in {r.file}:{r.line})",
        f"Current linked sizes per target: {fmt_sizes(sizes)}",
        "\nSource:\n```\n" + src + "\n```",
    ]
    if dis:
        parts.append("\nCurrent compiled code (z88dk-dis):\n```\n" + dis + "\n```")
    if history:
        parts.append("\nEarlier attempts on this routine that were rejected:\n" + "\n".join(f"- {h}" for h in history))
    parts.append("\nPropose one edit with submit_candidate, or decline.")
    return "\n".join(parts)


def review_prompt(r, src, diff, analysis, deltas) -> str:
    return (
        f"Routine under change: {r.name} ({r.lang}, {r.file})\n"
        f"Measured size change per target: {deltas}\n\n"
        f"Original routine:\n```\n{src}\n```\n\nPatch:\n```diff\n{diff}\n```\n\n"
        f"Author's justification (a claim, not evidence):\n{analysis}\n\n"
        "Return submit_verdict."
    )


def promote(cache: Path, new: dict[str, TargetResult]) -> dict[str, TargetResult]:
    """Make the accepted candidate's artifacts the new baseline cache."""
    base, cand = cache / "base", cache / "cand"
    shutil.rmtree(base, ignore_errors=True)
    cand.rename(base)
    return {
        k: TargetResult(v.ok, v.size, v.error, base / k / "out.map", (base / k / "out.bin") if v.binary_path else None)
        for k, v in new.items()
    }


def primary_routines(cfg: Config, res: dict[str, TargetResult]) -> list[mapfile.Routine]:
    first = res[cfg.targets[0].name]
    return mapfile.routines(mapfile.parse_map(first.map_path), cfg.sections)


def disasm_for(cfg: Config, res: dict[str, TargetResult], r: mapfile.Routine) -> str:
    for t in cfg.targets:
        tr = res.get(t.name)
        if tr and tr.binary_path:
            text = disassemble(t, tr, r)
            if text:
                return text
    return ""


def python_for_shell() -> str:
    """This interpreter as a shell-safe token (8.3 short path on Windows, quoted if it has spaces)."""
    exe = sys.executable
    if os.name == "nt":
        import ctypes

        buf = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(exe, buf, 1024):
            exe = buf.value
    exe = exe.replace("\\", "/")
    return f'"{exe}"' if " " in exe else exe


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--iterations", type=int, default=10, help="routines to attempt (default 10)")
    ap.add_argument("--max-usd", type=float, default=5.0, help="stop before spending more than this (default 5)")
    ap.add_argument("--routine", action="append", default=[], help="restrict to these routine names")
    ap.add_argument("--dry-run", action="store_true", help="build baseline and list candidates; no API calls")
    ap.add_argument("--mock-script", type=Path, help="replay proposals/verdicts from JSON (offline testing)")
    ap.add_argument("--env", type=Path, default=Path.home() / ".z80-skills" / ".env")
    ap.add_argument("--runs-dir", type=Path, default=Path.home() / ".z80-skills" / "shrink-runs")
    ap.add_argument("--keep-worktree", action="store_true")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    python = python_for_shell()
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = args.runs_dir / f"{cfg.name.replace(' ', '_')}-{stamp}"
    log = Log(run_dir)

    agent = None
    if not args.dry_run:
        if args.mock_script:
            agent = ScriptedAgent(json.loads(args.mock_script.read_text(encoding="utf-8")))
        else:
            env = load_env(args.env)
            agent = LLMAgent(cfg, Claude(load_api_key(args.env), cfg.prices, env.get("ANTHROPIC_WORKSPACE_ID", "")))

    primary_status = git(cfg.root, "status", "--porcelain")
    wt = Worktree.create(cfg.root, stamp)
    log.line(f"project {cfg.name} base {wt.base[:7]} branch {wt.branch}")
    log.line(f"worktree {wt.path}  run dir {run_dir}")
    log.event(kind="start", project=str(cfg.root), base=wt.base, branch=wt.branch, args=vars(args) | {"config": str(args.config), "env": "<hidden>", "runs_dir": str(args.runs_dir), "mock_script": str(args.mock_script)})

    accepted_total = 0
    stop_reason = "iterations done"
    exit_code = 0
    try:
        cache = run_dir / "cache"
        res = build_all(cfg, wt.path, cache / "base", python)
        bad = [k for k, v in res.items() if not v.ok]
        if bad or len(res) != len(cfg.targets):
            name = bad[0] if bad else "?"
            log.line(f"BASELINE BUILD FAILED ({name}):\n{res[name].error if bad else ''}")
            stop_reason, exit_code = "baseline build failed", 2
            return exit_code
        base_sizes = {k: v.size for k, v in res.items()}
        sizes = dict(base_sizes)
        log.line(f"baseline: {fmt_sizes(sizes)}  (total {sum(sizes.values())})")
        rs = primary_routines(cfg, res)
        attempts: dict[str, int] = {}
        history: dict[str, list[str]] = {}
        queue = candidate_queue(cfg, rs, attempts, args.routine)
        log.line(f"{len(queue)} candidate routines; largest: " + ", ".join(f"{r.name} {r.size}B" for r in queue[:8]))
        if args.dry_run:
            for r in queue:
                log.line(f"  {r.size:5d}B  {r.lang:3s} {r.name:32s} {r.file}:{r.line}")
            stop_reason = "dry run"
            return 0

        failures = 0
        for it in range(1, args.iterations + 1):
            queue = candidate_queue(cfg, rs, attempts, args.routine)
            if not queue:
                stop_reason = "no candidates left"
                break
            if agent.spent >= args.max_usd:
                stop_reason = f"budget reached (${agent.spent:.2f})"
                break
            if failures >= cfg.max_consecutive_failures:
                stop_reason = f"{failures} consecutive failures"
                break
            r = queue[0]
            attempts[r.name] = attempts.get(r.name, 0) + 1
            spent0 = agent.spent
            try:
                src = excerpt(cfg, wt.path, r, rs)
            except (OSError, ValueError) as exc:
                log.line(f"[{it:03d}] {r.name:24s} {r.size:5d}B  SKIP   {exc}")
                log.event(kind="skip", routine=r.name, reason=str(exc))
                continue
            dis = disasm_for(cfg, res, r)
            outcome, detail = "DECLINE", ""
            try:
                proposal = agent.start(proposal_prompt(cfg, r, src, dis, sizes, history.get(r.name, [])))
                for rnd in range(1, cfg.max_rounds + 1):
                    log.event(kind="proposal", routine=r.name, round=rnd, proposal=proposal)
                    if proposal.get("decision") != "edit":
                        outcome, detail = "DECLINE", proposal.get("analysis", "")[:200]
                        break
                    diff, err = apply_edits(cfg, wt.path, proposal.get("edits", []))
                    feedback = ""
                    if err:
                        outcome, detail, feedback = "BADEDIT", err, f"Edit not applied: {err}. Re-read the source and resubmit, or decline."
                    else:
                        new = build_all(cfg, wt.path, cache / "cand", python)
                        failed = [k for k, v in new.items() if not v.ok]
                        if failed or len(new) != len(cfg.targets):
                            name = failed[0] if failed else "?"
                            outcome, detail = "NOBUILD", f"{name}: " + (new[name].error.splitlines()[-1] if failed and new[name].error else "")
                            feedback = f"Build failed for target {name}:\n{new[name].error if failed else ''}\nFix it or decline."
                        else:
                            new_sizes = {k: v.size for k, v in new.items()}
                            deltas = {k: new_sizes[k] - sizes[k] for k in sizes}
                            total = sum(deltas.values())
                            dtxt = ", ".join(f"{k} {v:+d}" for k, v in deltas.items())
                            if total >= 0 or any(v > 0 for v in deltas.values()):
                                outcome, detail = "NOGAIN", dtxt
                                feedback = f"Measured size change: {dtxt} (total {total:+d}). Not accepted: total must fall and no target may grow. Try a different transformation or decline."
                            else:
                                test_err = run_tests(cfg, wt.path, python)
                                if test_err:
                                    outcome, detail, feedback = "TESTFAIL", test_err.splitlines()[0], test_err
                                else:
                                    verdict = agent.review(review_prompt(r, src, diff, proposal.get("analysis", ""), dtxt))
                                    log.event(kind="review", routine=r.name, verdict=verdict)
                                    if verdict.get("verdict") != "EQUIVALENT":
                                        issues = "; ".join(verdict.get("issues", [])) or verdict.get("analysis", "")[:300]
                                        outcome, detail = f"REVIEW-{verdict.get('verdict')}", issues[:200]
                                        feedback = f"Independent review verdict {verdict.get('verdict')}: {issues}\nFix the behavioural difference or decline."
                                    else:
                                        summary = (proposal.get("summary") or f"shrink {r.name}").strip()[:60]
                                        msg = (
                                            f"shrink({r.name}): {summary}\n\n"
                                            f"Size: {dtxt} (total {total:+d} bytes)\n"
                                            f"Review: EQUIVALENT ({getattr(cfg, 'reviewer_model')}); HW PENDING\n\n"
                                            f"{proposal.get('analysis', '').strip()[:1500]}\n\n"
                                            f"Shrink-Agent-Model: {cfg.proposer_model}\n"
                                        )
                                        sha = wt.commit(msg)
                                        sizes, res = new_sizes, promote(cache, new)
                                        rs = primary_routines(cfg, res)
                                        accepted_total += -deltas[cfg.targets[0].name]
                                        outcome, detail = "ACCEPT", f"{dtxt} commit {sha}"
                                        break
                    wt.revert()
                    if rnd < cfg.max_rounds and feedback:
                        if agent.spent >= args.max_usd:
                            break
                        history.setdefault(r.name, []).append(f"{outcome}: {detail}")
                        proposal = agent.feedback(feedback)
                        continue
                    break
            except ApiFatal:
                raise
            except (RuntimeError, OSError, ValueError) as exc:
                outcome, detail = "ERROR", f"{type(exc).__name__}: {exc}"[:200]
                log.event(kind="error", routine=r.name, error=repr(exc))
            if outcome != "ACCEPT":
                history.setdefault(r.name, []).append(f"{outcome}: {detail}")
                wt.revert()
            failures = 0 if outcome == "ACCEPT" else failures + 1
            cost = agent.spent - spent0
            log.line(
                f"[{it:03d}] {r.name:24s} {r.size:5d}B  {outcome:8s} {detail[:90]}  "
                f"${cost:.2f}  saved {accepted_total}B on {cfg.targets[0].name}  spent ${agent.spent:.2f}"
            )
            log.event(kind="result", routine=r.name, outcome=outcome, detail=detail, cost=cost, sizes=sizes)
    except ApiFatal as exc:
        stop_reason = f"API stopped the run: {exc}"
        exit_code = 3
    except Exception as exc:  # noqa: BLE001 - report, then clean up in finally
        stop_reason = f"error: {type(exc).__name__}: {exc}"
        log.event(kind="crash", error=repr(exc))
        exit_code = 1
    except KeyboardInterrupt:
        stop_reason = "interrupted"
        exit_code = 130
    finally:
        try:
            wt.revert()
        except Exception:  # noqa: BLE001 - best effort before removal
            pass
        n = wt.accepted()
        wt.remove(args.keep_worktree)
        if git(cfg.root, "status", "--porcelain") != primary_status:
            log.line("WARNING: primary checkout status changed during the run; inspect it.")
        spent = agent.spent if agent else 0.0
        log.line(f"stop: {stop_reason}. accepted commits {n}, saved {accepted_total} bytes on {cfg.targets[0].name}, spent ${spent:.2f}")
        if n:
            log.line(f"review: git -C \"{cfg.root}\" log --stat {wt.base[:7]}..{wt.branch}")
        else:
            log.line("no accepted commits; branch deleted" if not args.keep_worktree else "no accepted commits")
        tokens = getattr(getattr(agent, "claude", None), "tokens", {})
        for model, t in tokens.items():
            log.line(
                f"tokens {model}: input {t.get('input_tokens', 0)}, output {t.get('output_tokens', 0)}, "
                f"cache write {t.get('cache_creation_input_tokens', 0)}, cache read {t.get('cache_read_input_tokens', 0)}"
            )
        log.event(kind="end", reason=stop_reason, accepted=n, saved=accepted_total, spent=spent, tokens=tokens)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
