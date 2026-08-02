---
name: shrink-z80
description: Evidence-first binary-size optimization for Z80 and ZX Spectrum projects, including mixed ASM/C built with z88dk or SDCC. Use to reduce linked code, data, BSS, stack pressure, resident payloads, banks, overlays, library pulls, generated code, and compressed assets. Uses the shared workflow skill to scale execution while ranking only locally evidenced net savings.
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
- `scan` (default): adaptive full size pass.
- Focused: `deadcode`, `dedup`, `micro`, `data`, `compress`, `refactor`,
  `arch`, `libpull`, `blackbelt`, `reserve`.
- `diverge`: force a broad candidate search but retain normal proof gates.

For every real pass, read `references/hard-contract.md` and
`references/dispatcher.md`.

## Domain Demand

Classify after preflight and pass the result to `$workflow` when it is in
`auto`:

- **Focused**: one file/routine/asset/category and a known pressure target.
  A light route is normally sufficient.
- **Standard**: multiple plausible size mechanisms or uncertain linked impact.
  A medium route can isolate the highest-value uncertainty.
- **Deep**: broad scan, multi-target ceilings, banks/overlays, mixed source and
  generated artifacts, insufficient SAFE wins, or an explicit black-belt /
  exhaustive request. A heavy route can investigate independent high-yield
  lanes.

An explicit workflow level wins. Missing agents reduce parallelism, not byte
accounting or safety. An adaptive `Deep` pass may select only the two or three
highest-payload lanes, but must record the remaining applicable lanes as
skipped and explain why. An explicitly broad, exhaustive, or `diverge` pass
takes precedence and must cover every applicable high-yield lane, or state that
the pass is incomplete.

## First Actions

1. Identify the exact pressure target: storage, linked CODE/DATA, resident
   memory, BSS/stack gap, bank/overlay ceiling, or a per-target reserve.
2. Run `python3 "$SKILL_DIR/scripts/preflight_scan.py"` and
   `python3 "$SKILL_DIR/scripts/artifact_freshness.py"`; use
   `python3 "$SKILL_DIR/scripts/map_summary.py"` for selected maps.
3. Read `references/agent-orchestration.md` only when independent lanes add
   value, then pass selected briefs to `$workflow`.
4. Attack SAFE high-impact mechanisms before micro or dark-art tricks.
5. Read `references/external-research.md` only when a research trigger in
   `references/dispatcher.md` fires.
6. Treat script, subagent, and web output as candidates. Only the main agent
   may confirm net savings.

## Reference Map

- Evidence, worktrees, multi-target gate: `references/hard-contract.md`
- Mode and script routing: `references/dispatcher.md`
- Domain lanes for delegated analysis: `references/agent-orchestration.md`
- SAFE attack order: `references/high-impact.md`
- Rare/high-risk static techniques: `references/size-blackbook.md`,
  `references/size-playbook-extended.md`
- Dynamic forum/blog/repository discovery:
  `references/external-research.md`
- Byte and report rules: `references/z80-byte-evidence.md`,
  `references/reporting.md`
- Guardrails: `references/blind-spots.md`

## Core Rules

- Preserve behavior unless the user explicitly accepts more risk.
- Rank larger SAFE wins before AGGRESSIVE or EXPERIMENTAL ideas.
- Never sum dependent, subsumed, mutually exclusive, or unbuilt candidates.
- Compression claims use net storage and separate peak-RAM accounting.
- If only micro wins survive, state which higher-yield categories were checked.
