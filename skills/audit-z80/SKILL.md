---
name: audit-z80
description: "audit-z80 v2026.06.02-divergent: structured bug, logic, performance, UX, and inconsistency audit for mixed Z80 ASM and C projects on ZX Spectrum with z88dk or SDCC. Use for deep review of .asm, .c, .h, .map, .lst, or .opt files: ABI mismatches, stack balance, stale flags, ISR/shared-state hazards, memory layout, fixed-address RAM, calling conventions, hot-path stalls, user-visible regressions, and real 48K/128K failures. Includes an ADHD-style divergent threat-model pass that broadens hypotheses without lowering evidence thresholds. Triggers: audit, review z80, check code, revisar codigo, buscar bugs."
metadata:
  version: "v2026.06.02-divergent"
  version-note: "ADHD-style divergent threat-model pass, expanded pressure map, evidence thresholds unchanged."
allowed-tools:
  - Read
  - Glob
  - Grep
  - Agent
---

# Audit-Z80

Version: `v2026.06.02-divergent`

Treat this skill as a workflow, not a free-form persona prompt. Start with preflight, use divergent threat modeling to broaden what gets investigated, load only the reference files needed for the chosen mode, gather evidence, then report findings first.

## Modes

- Supported modes: `help`, `preflight`, `full`, `diverge`, `asm`, `c`, `abi`, `isr`, `memory`, `copt`, `map`
- If no mode is given, run `full`
- If the user only wants a quick overview, summarize `help` without loading every reference file

## Workflow

1. Parse mode and scope.
   - Announce the active version in the first skill-use status line: `audit-z80 v2026.06.02-divergent`.
   - Narrow the scope only if the user explicitly limits it.
   - For `full`, include preflight and every major category.
2. Build the project profile before judging code.
   - Read [references/preflight.md](references/preflight.md).
   - Run `scripts/preflight_scan.py <root>` when build flags, target, startup, or artifact availability are not already obvious.
   - If a `.map` exists or the user mentions memory pressure, run `scripts/map_summary.py <mapfile-or-root>`.
   - If the project mixes C and ASM, run `scripts/abi_inventory.py <root>` before concluding about calling conventions.
   - For `full`, `asm`, `isr`, unusual hand-written code, or demoscene-style hot paths, run `scripts/z80_pattern_scan.py <root>` and treat its output as hints to investigate, not findings.
3. Build a pressure map before reading linearly.
   - Identify boundary code, ISR/shared state, hot loops, screen/attribute writers, input polling, loaders/overlays, and fixed-RAM users.
   - Compare comments, symbol names, C prototypes, ASM exports, and `.map` reality; contradictions outrank style concerns.
   - For games/demos/apps with visible interaction, include UX failure modes: missed input, frame hitching, flicker, corrupt attributes, bad clipping, blocking I/O, and silent stalls.
4. Run the divergent threat-model pass for `full`, `diverge`, large/unusual scopes, fuzzy failures, or demoscene-style code.
   - Read [references/divergent-pass.md](references/divergent-pass.md).
   - Generate isolated hypothesis branches before judging them; prefer real Agent branches when available.
   - Use branches to widen the investigation queue across ABI, ISR, map, toolchain, UX/timing, memory pressure, and contradiction classes.
   - Never promote a branch hypothesis directly to a finding. It must pass the normal evidence thresholds or be downgraded to `ROBUSTNESS`, `SUSPICIOUS`, `NEEDS BUILD`, or dropped.
5. Load only the reference modules that match the task.
   - `asm` or `abi`: [references/asm-abi.md](references/asm-abi.md)
   - `c` or `memory`: [references/c-memory.md](references/c-memory.md)
   - `isr`, `map`, or memory-pressure work: [references/isr-map.md](references/isr-map.md)
   - Divergent threat modeling: [references/divergent-pass.md](references/divergent-pass.md)
   - Any large or unusual codebase: [references/blind-spots.md](references/blind-spots.md)
   - If the user asks for external/Gemini/Claude-level imagination, demoscene tricks, exotic routines, or tool-backed hardening: [references/external-toolkit.md](references/external-toolkit.md)
   - If the user asks for forum-mined, underground, old-school, demoscene, or "black magic" review: [references/forum-gems.md](references/forum-gems.md)
   - Final report rules: [references/reporting.md](references/reporting.md)
6. Gather evidence before naming a bug.
   - Read every in-scope source file fully.
   - Cross-check declarations, call sites, stack layout, and fixed-address usage.
   - Treat `.map`, `.lst`, `.sym`, `.opt`, and build flags as evidence, not optional garnish.
7. Enforce coverage.
   - `full` must explicitly cover: preflight, divergent hypothesis coverage, ASM/registers/flags, C semantics, ABI boundary, ISR/shared state, memory/BSS gap, hot-path or UX risk, and `.map` or copt when present.
   - If a category has no findings, say `none found` and cite the evidence used.
   - Do not stop after the first plausible bug class.
8. Report findings first and never edit files.
   - Use the reporting contract in [references/reporting.md](references/reporting.md).
   - Separate `BUG`, `ROBUSTNESS`, `PERF/UX`, `TRADEOFF`, `THEORETICAL`, and `OBSERVATION`.
   - Keep severity and confidence independent.

## Evidence thresholds

- Use `PROVEN` only when an opcode trace, stack trace, symbol, offset, or direct contradiction makes the bug concrete.
- Use `LIKELY`, `SUSPICIOUS`, or `NEEDS BUILD` when the missing proof is real.
- State the contract you are assuming when the target, startup, or toolchain changes the analysis.

## Bundled scripts

- `scripts/preflight_scan.py`: summarize toolchain flags, artifacts, calling-convention markers, and interrupt clues.
- `scripts/map_summary.py`: extract code/data/BSS boundaries, stack-top symbols, largest symbol spans, and libpull signatures from z88dk-style `.map` files.
- `scripts/abi_inventory.py`: inventory calling convention markers, C boundary prototypes, ASM exports/imports, mismatch candidates, and stack-cleanup hints.
- `scripts/z80_pattern_scan.py`: surface expert-review hints around stale flags, carry-after-INC/DEC, DI exits, HALT under DI, block ops, shadow registers, stack tricks, page-local indexing, timing pads, dynamic dispatch, self-modifying/layout code, IX/IY hot paths, Next-only opcodes, port I/O, screen/ROM anchors, C mutability traps, loop libcalls, and repeated call targets.

## Output contract

- Put findings first.
- Follow with open questions or assumptions.
- Close with a short coverage note or residual-risk note, including which divergent hypothesis classes were investigated or rejected.
- If no findings remain, say so explicitly instead of padding with observations.
