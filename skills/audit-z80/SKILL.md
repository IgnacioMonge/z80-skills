---
name: audit-z80
description: Evidence-first, read-only review of mixed Z80 ASM/C projects, especially ZX Spectrum code built with z88dk or SDCC. Use for bug audits involving ABI, stack/register/flag clobbers, ISR/shared state, memory maps, banks/overlays, firmware, generated code, toolchain behavior, hardware timing, or user-visible regressions. Adapts from a focused single-agent pass to independent parallel branches and targeted external research when scope, ambiguity, or risk justifies the cost.
---

# Audit Z80

Use this file as a lean dispatcher. Load only references selected by the current
scope. Prefer context-efficient reads, searches, and shell output when the
runtime provides them.

## Modes

- `help`: summarize modes from this file and stop.
- `preflight`: run the relevant profile scripts, report escalation signals, and
  stop.
- `auto` (default): preflight, then choose focused, standard, or deep demand.
- `full` / `diverge`: force broad category coverage; depth still adapts to the
  evidence and available agent capacity.
- Focused modes: `asm`, `c`, `abi`, `isr`, `memory`, `spectrum-hw`, `esxdos`,
  `toolchain`, `copt`, `map`.

For every real audit, read `references/hard-contract.md` and
`references/dispatcher.md`. Read `references/agent-orchestration.md` only when
more than one independent investigation lane is useful.

## Demand

Classify after preflight:

- **Focused**: explicit files/functions, one boundary, and a concrete question.
  Keep the main agent only.
- **Standard**: two or more interacting domains, a fuzzy symptom, or a material
  evidence gap. Use one independent delegate when available.
- **Deep**: broad/full scope, high-impact corruption or timing risk, mixed
  source/generated evidence, several targets, contradictory artifacts, or an
  explicit exhaustive request. Use parallel independent lanes up to useful
  runtime capacity; add later waves only when the first wave changes the search
  frontier.

Unavailable agents reduce parallelism, not evidence standards. In `auto`, stop
after risk-prioritized lanes cease changing the result. In explicit `full`,
cover every applicable lane serially or state that the audit is incomplete.

## First Actions

1. Resolve the skill directory before invoking bundled scripts.
2. Parse scope and mode; narrow only on an explicit user limit.
3. Build one project profile and one evidence digest.
4. Select domain references from `references/dispatcher.md`.
5. Select independent lanes from `references/agent-orchestration.md` when
   demand is standard or deep.
6. Read `references/external-research.md` only when a research trigger in
   `references/dispatcher.md` fires.
7. Treat scripts, agents, prior knowledge, and web sources as candidate
   generators. The main agent verifies every promoted finding.

## Reference Map

- Evidence and sandbox rules: `references/hard-contract.md`
- Routing and scripts: `references/dispatcher.md`
- Adaptive parallelism: `references/agent-orchestration.md`
- External discovery: `references/external-research.md`
- Promotion: `references/promotion-gate.md`
- Reporting: `references/reporting.md`
- Domain checks: `references/asm-abi.md`, `references/c-memory.md`,
  `references/isr-map.md`, `references/sdcc-z88dk-quirks.md`,
  `references/spectrum-hardware-esxdos.md`,
  `references/promotion-gate.md`

## Core Rules

- Findings first; never edit project code during an audit.
- Promote only current-code or fresh-artifact evidence.
- Verify reachability, ABI, stack, flags, registers, interrupt state, memory
  layout, generated-code reality, and target constraints as applicable.
- If no finding survives, say so and identify the strongest residual risk.
