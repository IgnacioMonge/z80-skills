---
name: shrink-z80
description: "shrink-z80 v2026.06.02-divergent: ambitious demoscene-grade binary-size optimizer for mixed Z80 ASM and C projects on ZX Spectrum with z88dk or SDCC. Use to reduce CODE/BSS/stack pressure, explain .asm/.c/.map/.lst/.opt size, and find non-obvious wins around architecture, library drag, dead code, data/code layout, generated/offline work, code/data co-design, tail merging, table compression, RST/call vectors, screen algorithms, Z80/SDCC codegen, and forum-mined tricks. Includes an ADHD-style divergent branch pass so scans do not collapse into micro-wins. Triggers: shrink, optimize size, reduce binary, quitar grasa, quitar lastre."
metadata:
  version: "v2026.06.02-divergent"
  version-note: "ADHD-style divergent branch pass, architecture/data/code-design first, micro-wins demoted unless larger levers are exhausted."
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
---

# Shrink-Z80

Version: `v2026.06.02-divergent`

Treat this skill as a measured size-reduction workflow. Start with preflight and evidence, force a divergent pass for non-local ideas, attack high-impact categories first, and do not stop at dedup or instruction-level polish.

## Modes

- Supported modes: `help`, `preflight`, `scan`, `diverge`, `deadcode`, `dedup`, `micro`, `data`, `refactor`, `arch`, `libpull`, `copt`, `report`
- If no mode is given, run `scan`
- `scan` means: preflight, arch, libpull, deadcode or refactor, data, micro, dedup, report

## Workflow

1. Parse mode and scope.
   - Announce the active version in the first skill-use status line: `shrink-z80 v2026.06.02-divergent`.
   - Narrow the scope only if the user explicitly limits it.
   - Use `scan` for the full pass, not a dedup-only pass.
2. Measure before proposing.
   - Read [references/preflight.md](references/preflight.md).
   - Run `scripts/preflight_scan.py <root>` when build flags or artifacts are unclear.
   - Run `scripts/map_summary.py <mapfile-or-root>` whenever a `.map` exists.
   - Run `scripts/libpull_scan.py <root> [map]` for `scan`, `libpull`, or when arithmetic or library drag may matter.
   - Run `scripts/literal_dup_scan.py <root>` for `dedup` or when strings and tables dominate.
   - Run `scripts/z80_pattern_scan.py <root>` for `scan`, `arch`, `refactor`, `micro`, or when the user asks for demoscene/exotic/Gemini-level ideas. Treat output as candidates, not savings.
3. Run the divergent size pass for `scan`, `diverge`, `arch`, `refactor`, `data`, or when early findings are mostly local.
   - Read [references/divergent-pass.md](references/divergent-pass.md).
   - Generate separated hypothesis branches before judging them; prefer real Agent branches when available.
   - Use branches to seek representation changes, offline/generated work, protocol/state collapse, table/data redesign, library deletion, lifetime reuse, and code/data co-design.
   - Score and converge before reporting. Promote only investigated candidates with byte evidence; keep unproven ideas as `SPECULATIVE` or `Rejected ideas`.
   - If a `scan` returns only sub-20B micro wins without a clear explanation for absent architecture/libpull/data wins, the pass is incomplete.
4. Load only the reference modules that match the task.
   - `scan`, `arch`, `libpull`, or high-level triage: [references/high-impact.md](references/high-impact.md)
   - Divergent high-impact search: [references/divergent-pass.md](references/divergent-pass.md)
   - C-generated size patterns: [references/c-patterns.md](references/c-patterns.md)
   - Hand-written ASM work: [references/asm-micro.md](references/asm-micro.md)
   - External tools and demoscene-grade idea bank: [references/external-toolkit.md](references/external-toolkit.md)
   - Forum-mined black-belt tricks, old-school game routines, and underground idea bank: [references/forum-gems.md](references/forum-gems.md)
   - Final ranking and dependencies: [references/reporting.md](references/reporting.md)
   - Anti-shallow checks: [references/blind-spots.md](references/blind-spots.md)
5. Attack in priority order.
   - For `scan`, inspect `arch` and `libpull` before `dedup`.
   - Prefer high-impact `SAFE` wins over tiny local rewrites, even if they require a broader refactor.
   - Treat representation changes, generated/offline computation, table redesign, generic-code deletion, and buffer lifetime reuse as first-class candidates.
   - Consider `CODE`, `BSS`, stack, complexity, and testing cost together.
6. Run the black-belt pass after the safe pass.
   - Look for screen-memory/layout rewrites, active lists, page-local tables, table/token encodings, suffix merging, RST/call-vector amortization, stack-copy opportunities, generated tables, compiled sprites, compression nets, and code/data co-design.
   - Keep a `Rejected ideas` list for clever candidates that fail byte count, ABI, flags, stack, timing, or maintainability proof.
   - Do not present `EXPERIMENTAL` tricks before exhausting `SAFE` and `AGGRESSIVE` wins with larger expected savings.
7. Enforce category coverage.
   - `scan` must say something explicit about `diverge`, `arch`, `libpull`, `deadcode or refactor`, `data`, `micro`, `dedup`, and black-belt candidates, even if the statement is `none found`.
   - Do not present a dedup-only report as a full shrink pass.
8. Preserve behavior unless the user opts into more risk.
   - Default to `SAFE`.
   - Mark `AGGRESSIVE` and `EXPERIMENTAL` explicitly and leave them after `SAFE` wins.

## Evidence thresholds

- `EXACTO`: counted or measured locally
- `ESTIMADO`: local reasoning is solid but the final build impact may vary
- `REQUIERE BUILD`: linker elimination, `jr` range, or library removal must still be confirmed
- Always say what must be re-measured after the edit

## Bundled scripts

- `scripts/preflight_scan.py`: summarize build flags, output artifacts, copt rules, map files, and memory settings.
- `scripts/map_summary.py`: extract code/data/BSS markers, stack-gap inputs, largest symbol spans, and heavy map symbols from z88dk-style `.map` files.
- `scripts/libpull_scan.py`: correlate heavy library symbols in the map with source-level calls, arithmetic, constant arithmetic, tiny mem helpers, and loop libcalls in `.c`.
- `scripts/literal_dup_scan.py`: list repeated C string literals and repeated ASM `db` string payloads.
- `scripts/z80_pattern_scan.py`: surface high-yield hand-written Z80 shrink candidates and risky exotic shapes: tail-call wrappers, repeated calls, repeated ASM n-grams, repeated suffix tails, stack blitters, page-local indexing, timing pads, pointer dispatch, block ops, IX/IY hot paths, self-modifying/layout dependencies, fixed screen anchors, large byte tables, switch/pointer-table overhead, and costly runtime triggers.

## Output contract

- Put high-value wins first, ordered by bytes, safety, and dependency leverage; do not let tiny quick wins bury architectural savings.
- Include a short divergent shortlist: top investigated branch candidates, their score or rank, and rejected traps.
- Then give detailed findings grouped by category.
- Close with dependencies, open questions, and what still needs a build to confirm.
