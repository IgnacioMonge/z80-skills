---
name: shrink-z80
description: Evidence-first binary-size optimization for Z80 and ZX Spectrum projects, including mixed ASM/C built with z88dk or SDCC. Use to reduce linked code, data, BSS, stack pressure, resident payloads, banks, overlays, library pulls, generated code, and compressed assets. Uses the shared workflow skill to scale execution while ranking only locally evidenced net savings.
disable-model-invocation: true
---

# Shrink Z80

Use this file as a lean dispatcher. Measure before proposing savings and load
only references selected by current evidence.

## Workflow Core

Apply the sibling `$workflow` skill at `../workflow/SKILL.md` as the execution
control plane. Workflow owns effort, agent topology, dispatch, repair,
verification, and integration; this skill owns size modes, byte evidence,
domain lanes, accounting, ranking, and its read-only contract. A workflow route
never widens that contract. If the sibling skill is unavailable, report the
exact limitation and continue directly without claiming delegated execution.

## Runtime Portability

- Resolve `SKILL_DIR` as the directory containing this file.
- Use the Python 3 interpreter exposed by the host or explicitly provided by
  the user; never assume a Windows, macOS, or Linux path.
- Invoke bundled scripts by absolute path so project-local same-named scripts
  cannot masquerade as skill evidence.

## Modes

- `help`: summarize modes from this file and stop.
- `preflight`: profile artifacts and pressure targets, then stop.
- `scan` (default): the winner pass in `references/high-impact.md`. Each
  kept candidate saves at least the materiality threshold: the user's figure,
  else 30 B net on the pressure target. Smaller ones go in one tail line.
- Focused: `deadcode`, `dedup`, `micro`, `data`, `compress`, `refactor`,
  `arch`, `libpull`, `blackbelt`, `reserve`. Micro-level lanes (`micro`,
  `dedup`, `blackbelt`, `asm-micro.md`, `z80_pattern_scan.py`,
  `literal_dup_scan.py`) run only when the user names that mode.
- `diverge`: force a broad candidate search but retain normal proof gates.
- `agent`: only on an explicit request to apply savings or to run
  shrink-agent. shrink-agent makes one local edit per routine, so it yields
  micro savings. First run `winner_census.py` (see First Actions). If any
  family reaches the threshold, report those winners and their bytes, say the
  agent would find tens of bytes, and ask whether to apply the winners or run
  the agent; launch only after the user chooses the agent or when the census
  is empty. Then run `preflight`, then write `<project>/shrink-agent.toml`
  from its findings when the file is missing (template:
  `../../tools/shrink-agent/examples/template.toml`; fields in its README).
  Choose `size_symbol` by the pressure target, set `python` when the build
  needs the host interpreter, add a `files` target for overlays or banks
  linked apart from the main map (`maps` too when their link writes maps,
  so their routines are proposed), put the project's own size or layout
  checks in `tests`, and list only targets the project's instructions allow
  to build. Then run
  `<venv-python> "$SKILL_DIR/../../tools/shrink-agent/shrink_agent.py" --config <that file> --dry-run`
  with `<venv-python>` = `~/.z80-skills/venv/bin/python` (Windows:
  `~/.z80-skills/venv/Scripts/python.exe`); no venv or `~/.z80-skills/.env`
  means run `tools/shrink-agent/install.py` first. Gate: at least one
  candidate, `.c` routines listed as `c`, every `excerpt` line `ok`; otherwise
  fix the config and stop. Then launch the same command without `--dry-run`
  in the background. The tool defaults to 5 routines and 2 USD; pass
  `--iterations` or `--max-usd` only when the user states other values.
  Report from `~/.z80-skills/shrink-runs/<project>-<timestamp>/shrink.log`.

For every real pass, read `references/hard-contract.md` and
`references/dispatcher.md`.

## Domain Demand

Classify after preflight and pass the result to `$workflow` when it is in
`auto`:

- **Focused**: one file/routine/asset/category and a known pressure target.
  A light route is normally sufficient.
- **Standard**: multiple plausible size mechanisms or uncertain linked impact.
  A medium route can isolate the highest-value uncertainty.
- **Deep**: an explicit broad/exhaustive request, or several independent
  high-risk size mechanisms whose evidence cannot be resolved in one stream. A
  heavy route can investigate independent high-yield lanes.

An explicit workflow level wins. Missing agents reduce parallelism, not byte
accounting or safety. A default `scan` begins with the highest-payload evidenced
lane; it is not a full-project promise. Expand only while another lane can
materially change the result. An explicitly broad, exhaustive, or `diverge`
pass must cover every applicable high-yield lane, or state that the pass is
incomplete.

## First Actions

1. Identify the exact pressure target: storage, linked CODE/DATA, resident
   memory, BSS/stack gap, bank/overlay ceiling, or a per-target reserve.
2. A local, source-only pass (one routine, known source, no linked claims)
   needs no census, inventory or artifact check. Otherwise gate artifacts with
   `artifact_freshness.py` unless an equivalent gate remains valid under
   workflow verification rules. Stale maps make the census triage only.
3. Run the census once per linked target, passing every overlay or bank
   binary linked against that map:
   `<python> "$SKILL_DIR/scripts/winner_census.py" --map <map> --bin <CODE.bin>
   --origin <load address> --overlay <NAME>=<binary> ...`
   It ranks `[overlay_only]`, `[unreferenced]`, `[abi_cleanup]` and
   `[frame_idioms]` above the threshold, plus `[mass]` for where large code
   sits. `<python>` is the host interpreter described above.
4. Work the winner families in `references/high-impact.md` in census order.
   Run `libpull_scan.py`, `deadcode_scan.py` or `preflight_scan.py` only when
   the census or the user points at that category.
5. Read `references/agent-orchestration.md` only when independent winner
   families add value, then pass selected briefs to `$workflow`.
6. Read `references/external-research.md` only when a research trigger in
   `references/dispatcher.md` fires.
7. Treat script, subagent, and web output as candidates. Only the main agent
   may confirm net savings.

## Reference Map

- Evidence, worktrees, multi-target gate: `references/hard-contract.md`
- Mode and script routing: `references/dispatcher.md`
- Domain lanes for delegated analysis: `references/agent-orchestration.md`
- Winner families and materiality: `references/high-impact.md`
- Rare/high-risk static techniques: `references/size-blackbook.md`,
  `references/size-playbook-extended.md`
- Dynamic forum/blog/repository discovery:
  `references/external-research.md`
- Byte and report rules: `references/z80-byte-evidence.md`,
  `references/reporting.md`
- Guardrails: `references/blind-spots.md`
- Unattended applying loop (`agent` mode): `../../tools/shrink-agent/README.md`.
  It edits a disposable worktree and commits to its own branch; this skill's
  read-only contract still governs analysis passes.

## Core Rules

- Preserve behavior unless the user explicitly accepts more risk.
- Rank by net bytes on the pressure target; below the threshold, list only.
- Moving resident code that only one overlay or bank uses into it is a
  resident saving. Moving overlay code into resident is never a saving.
- Rank larger SAFE wins before AGGRESSIVE or EXPERIMENTAL ideas.
- Never sum dependent, subsumed, mutually exclusive, or unbuilt candidates.
- Exact artifact claims require the freshness gate; stale or unbound artifacts
  remain `REQUIERE BUILD`.
- Compression claims use net storage and separate peak-RAM accounting.
- If only micro wins survive, state which higher-yield categories were checked.
