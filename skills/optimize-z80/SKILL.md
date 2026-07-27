---
name: optimize-z80
description: Read-only strategy engine for optimizing Z80 and ZX Spectrum projects across size, speed, RAM, rendering, latency, banking, overlays, data layout, C-to-ASM, z88dk/SDCC codegen, ABI, toolchain, and model-specific hardware constraints. Adapts from focused single-agent triage to independent parallel analysis and targeted external research, then ranks only project-local, policy-compliant candidates with explicit validation.
---

# Optimize Z80

Read `references/hard-contract.md` before promoting any candidate. The primary
project tree remains read-only during analysis.

## Modes

- **Triage** (default): inspect current source/artifacts read-only; no build;
  stale artifacts cap confidence.
- **Measurement**: use a disposable worktree for a reproducible baseline build
  when real byte/cycle/latency deltas matter.
- **Experiment**: requires explicit user approval; apply and measure one
  candidate in a disposable worktree, then remove it unless the user explicitly
  asks to retain it.

Choose a safe temporary/worktree location supported by the host. Do not assume
a branch name, directory layout, shell, or operating system. Never modify a
tracked ignore file merely to host experiments.

This skill ranks cross-metric optimization strategy. Use `shrink-z80` for an
exhaustive size-only harvest and `audit-z80` for correctness auditing; neither
skill's private references are normative dependencies here.

## Demand

Classify after preflight:

- **Focused**: one zone, bottleneck, file, or candidate. Main agent only.
- **Standard**: multiple plausible mechanisms or a material uncertainty. Use
  one independent delegate when available.
- **Deep**: broad project, several active zones/targets, conflicting evidence,
  high-risk timing/banking/ABI work, or an explicit exhaustive request. Run
  independent high-value lanes in parallel up to available capacity; launch a
  later wave only when the first wave changes the optimization frontier.

Unavailable agents reduce parallelism, not evidence or policy gates. A normal
triage stops when new lanes cannot change the ranking; an explicit exhaustive
request covers all applicable lanes serially or reports the limitation.

## Progressive Load

1. Always: `references/hard-contract.md`, then
   `references/project-policy.md` only when a policy file exists or constraints
   must be inferred.
2. Core decision: the matching section of
   `references/optimization-paths.md`.
3. Orchestration: `references/multiagent-roles.md` only when more than one
   independent lane is useful.
4. Commands/measurement: `references/terminal-blockers.md` and
   `references/measurement.md` only when executing or measuring.
5. Technique references only for observed zones:
   `references/profiles-and-zones.md`, then the relevant one of
   `references/z80-techniques.md`, `references/c-to-asm.md`,
   `references/z88dk-sdcc-abi.md`, `references/modern-spectrum-io.md`,
   `references/zx-spectrum-hardware.md`, or
   `references/zx-spectrum-models.md`.
6. Finalist risk only: `references/risk-matrix.md`,
   `references/z80-proof-obligations.md`, and `references/traps.md`.
7. Toolchain experiments only: `references/toolchain.md`.
8. `references/external-research.md` only when its trigger gate fires.
9. `references/usage-examples.md` only when the user requests examples.

Bundled helpers are evidence-selective: start with `scripts/preflight.py`; use
`scripts/pattern_scan.py`, `scripts/asm_callgraph.py`, or
`scripts/map_hotspots.py` only for the matching source/artifact signal;
`scripts/contention_audit.py` and `scripts/tstate_estimate.py` only for timing;
`scripts/bincompare.py` only for measurement; and
`scripts/score_candidates.py` only after policy/target gates. Scanner and
static timing/map estimates are candidate evidence, never `PROVEN` by
themselves. On Python below 3.11, read TOML through the host and pass normalized
`--target`/`--forbidden` values; enforce other policy constraints before the
scorer rather than using its unavailable `--policy` path.

## Workflow

1. Preflight target, policy, dirty state, toolchain, source mix, build recipe,
   artifacts, freshness, and dominant pressure.
2. Choose triage or measurement; do not claim measured deltas from stale
   artifacts.
3. Build a compact zone map and identify the actual bottleneck.
4. Select only useful analysis lanes from `references/multiagent-roles.md`.
5. Generate candidates with current anchors.
6. Apply policy/target vetoes before scoring.
7. Merge duplicates and rank globally for the active bottleneck.
8. Risk-audit the finalists.
9. Recommend at most three next experiments; measure one only with the required
   approval.
10. Clean the disposable worktree and verify the primary tree stayed unchanged.

## Candidate Contract

Each candidate states:

- current anchor and evidence freshness;
- bottleneck/zone and mechanism;
- expected size, cycles/latency, RAM/stack, and UX effect as applicable;
- risk, target applicability, forbidden-lane tags, rollback, and validation;
- confidence: `PROVEN`, `LIKELY`, or `SPECULATIVE`;
- why it outranks alternatives now.

External sources and subagents generate candidates only. `PROVEN` requires
current local evidence or a reproducible measurement.

## Output

- policy, target, profile, and artifact freshness;
- compact zone/coverage ledger;
- ranked candidates and rejected policy/target tricks;
- at most three next experiments;
- validation/measurement plan;
- short process traps only when they affected the result.

## Hard Rules

- Reject forbidden lanes and wrong-target candidates; do not merely demote them.
- Optimize the dominant wait or pressure, not the most interesting assembly.
- Multi-target candidates pass only when every declared target meets its own
  limits from a fresh artifact built from the same frozen source revision and
  configuration baseline.
- DI/EI, SP abuse, SMC, undocumented opcodes, floating bus, and hardware timing
  require explicit risk tags and target-specific validation.
- One failed command must change the next method.
