# Optimization Domain Lanes

Use this file only when preflight exposes more than one independent
optimization question. The main agent remains cartographer, judge, policy
enforcer, and auditor of record.

## Workflow Boundary

`$workflow` owns effort selection, capacity, model profiles, spawning, failure
handling, and integration review. This reference supplies only Z80 optimization
lanes and their evidence contracts. Give selected lane briefs to the workflow
control plan; do not recreate a second router here.

## Selectable Lanes

Choose by observed zones and pressure:

| Lane | Question |
|---|---|
| `architecture-data` | What work, state, representation, table, buffer, asset, or phase can disappear or move? |
| `toolchain-codegen` | What do compiler, ABI, libraries, generated ASM, linker layout, or build flags actually cost? |
| `hotpath-latency` | Which measured loop, render path, parser, I/O wait, or overlay transition dominates the user-visible budget? |
| `hardware-memory` | Which contention, paging, screen, interrupt, stack, bank, or model constraint changes the strategy? |
| `research-scout` | Which external implementation, issue, test, or obscure technique can resolve a top uncertainty? |

The main agent retains policy discovery, artifact freshness, zone map, scoring,
and final risk review. A separate risk-only delegate is justified only for
high-impact SP/SMC/interrupt/hardware candidates and should adversarially review
the finalists, not repeat discovery.

## Independence Contract

- Use one immutable baseline digest for all lanes.
- Give each delegate one falsifiable question and exact paths/artifacts.
- Do not pass another delegate's conclusions; overlap only for intentional
  adversarial validation.
- No nested agents, edits, builds, global scoring, or final-report prose.
- Run deterministic collection/scoring once in the main agent and share compact
  summaries.
- Load only lane-relevant reference sections.

## Branch Brief

```text
Task: optimize-z80 candidate search
Lane:
Question:
Scope:
Baseline: <target, policy, toolchain, freshness, bottleneck; <=12 lines>
Control: <workflow level and assigned worker role>
Constraints: read-only; no nested agents/builds; candidates only
References: <only relevant files/sections>
```

## Compact Return Contract

Return at most three candidates by default; allow five only for an explicit
exhaustive request when all can change the frontier:

```text
- Mechanism:
  Current anchor/evidence:
  Expected effect:
  Risk/target constraints:
  Confidence:
  Validation:
  Why now:
```

Add one rejected trap, or two for explicit exhaustive work, only when it would
otherwise look attractive.

## Domain Integration Sequence

1. Build policy/profile, freshness, bottleneck, and zone digest once.
2. Select lanes by expected decision value, not role completeness.
3. Give selected lane briefs to the `$workflow` control plan.
4. Merge returned candidates by mechanism, apply vetoes, and score survivors.
5. Adversarially review only the finalists.
6. Ask workflow for another bounded lane only when unresolved evidence can
   change the result.
7. Stop when new work cannot change the top three experiments, confidence, or
   residual risk.
8. Report the actual workflow level and materially skipped lanes in one short
   block.

The research lane follows `external-research.md`; its sources never substitute
for project-local proof.
