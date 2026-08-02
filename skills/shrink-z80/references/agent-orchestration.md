# Size Domain Lanes

Use this after preflight only when several independent size mechanisms can
materially change the result. The main agent owns measurement, byte accounting,
promotion, ranking, and the final report.

## Workflow Boundary

`$workflow` owns effort selection, capacity, model profiles, spawning, failure
handling, and integration review. This reference supplies only Z80 size lanes
and their evidence contracts. Give selected lane briefs to the workflow control
plan; do not recreate a second router here.

## Lane Selection

Choose from preflight evidence rather than launching a fixed roster.

| Lane | Select when |
|---|---|
| `arch-resident` | repeated systems, state/protocol collapse, CRT/startup drag, resident/banked split, lifetime reuse |
| `libpull-codegen` | C, generated ASM/listings, arithmetic/stdio/heap helpers, conventions, copt opportunities |
| `data-compress` | strings, tables, screens, sprites, levels, packed assets, buffers, decoder or workspace tradeoffs |
| `asm-layout` | hand ASM, repeated tails, prefix density, branch/layout/page opportunities, micro candidates |
| `research-scout` | external discovery can resolve a codec/toolchain/technique uncertainty or the SAFE pass stalls |

The main agent runs deterministic scripts once and keeps the map/freshness
ledger. An adaptive `Deep` scan normally assigns the two or three lanes with
the largest observable payload, not every lane; it must record other applicable
lanes as skipped with a reason. An explicitly broad, exhaustive, or `diverge`
pass overrides that optimization and covers every applicable high-yield lane,
or reports the pass incomplete.

## Independence Contract

- Give each delegate the same immutable baseline digest; do not expose another
  delegate's conclusions.
- Assign one mechanism family and exact paths/artifacts. Overlap only for a
  deliberate adversarial count.
- No nested agents, edits, builds, global ranking, or final-report prose.
- Pass short scanner summaries and relevant reference sections, never full
  logs or the entire skill.
- A lane may return zero candidates.

## Branch Brief

```text
Task: shrink-z80 candidate search
Lane: <lane>
Pressure target: <storage|linked|resident|BSS/stack|bank/overlay>
Scope: <exact paths/artifacts>
Baseline: <toolchain, flags, selected map, freshness, current sizes; <=12 lines>
Control: <workflow level and assigned worker role>
Constraints: preserve behavior; no edits/builds/nested agents; candidates only
References: <only relevant files/sections>
```

## Compact Return Contract

Return at most three candidates by default; allow five only for an explicit
exhaustive pass when all are independent and materially sized:

```text
- Mechanism:
  Anchor:
  Current bytes/evidence:
  Proposed representation/change:
  Net saving: <exact|estimate|needs build>
  Cost/risk:
  Dependency:
  Verification:
```

Include one rejected trap, or two for explicit exhaustive work, only when it
prevents plausible false savings.

## Domain Integration Sequence

1. Establish pressure target, artifact freshness, and one baseline digest.
2. Select lanes by observable byte mass and expected leverage.
3. Give selected lane briefs to the `$workflow` control plan.
4. Merge returned candidates by mechanism and remove dependent, subsumed, or
   exclusive duplicates.
5. Recount top candidates locally, including linker cascades, setup/decoder
   cost, flags/registers/stack, branch range, and multi-target gates.
6. Ask workflow for another bounded lane only when unresolved evidence can
   change the result.
7. Stop when new lanes only duplicate candidates, lack current anchors, or
   cannot alter the top experiments.
8. Report the actual workflow level and materially skipped lanes in a compact
   synthesis.

External research can discover a mechanism or benchmark method; it cannot
confirm a saving without current project bytes and, where required, a build.
