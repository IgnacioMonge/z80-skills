---
name: shrink-z80
description: Evidence-first binary-size optimization for Z80 and ZX Spectrum projects, including mixed ASM/C built with z88dk or SDCC. Use to reduce linked code, data, BSS, stack pressure, resident payloads, banks, overlays, library pulls, generated code, and compressed assets. Adapts from a focused single-agent check to independent parallel lanes and targeted external research while ranking only locally evidenced net savings.
---

# Shrink Z80

Use this file as a lean dispatcher. Measure before proposing savings and load
only references selected by current evidence.

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

## Demand

Classify after preflight:

- **Focused**: one file/routine/asset/category and a known pressure target.
  Keep the main agent only.
- **Standard**: multiple plausible size mechanisms or uncertain linked impact.
  Use one independent delegate when available.
- **Deep**: broad scan, multi-target ceilings, banks/overlays, mixed source and
  generated artifacts, insufficient SAFE wins, or an explicit black-belt /
  exhaustive request. Run useful high-yield lanes in parallel up to available
  capacity; add a later wave only when new evidence justifies it.

Unavailable agents reduce parallelism, not byte accounting or safety. Run only
evidence-selected lanes, but an explicit broad `scan` must still cover every
applicable high-yield lane or state that the pass is incomplete.

## First Actions

1. Identify the exact pressure target: storage, linked CODE/DATA, resident
   memory, BSS/stack gap, bank/overlay ceiling, or a per-target reserve.
2. Run `scripts/preflight_scan.py` and `scripts/artifact_freshness.py`; use
   `scripts/map_summary.py` for selected maps.
3. Read `references/agent-orchestration.md` only when independent lanes add
   value.
4. Attack SAFE high-impact mechanisms before micro or dark-art tricks.
5. Read `references/external-research.md` only when a research trigger in
   `references/dispatcher.md` fires.
6. Treat script, subagent, and web output as candidates. Only the main agent
   may confirm net savings.

## Reference Map

- Evidence, worktrees, multi-target gate: `references/hard-contract.md`
- Mode and script routing: `references/dispatcher.md`
- Adaptive parallelism: `references/agent-orchestration.md`
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
