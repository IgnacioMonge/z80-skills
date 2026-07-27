# Adaptive Agent Orchestration

Use this after preflight only when several independent size mechanisms can
materially change the result. The main agent owns measurement, byte accounting,
promotion, ranking, and the final report.

## Capacity Negotiation

Inspect the actual runtime for subagent capability and available capacity. Do
not assume a model, role implementation, or slot count.

| Demand | Delegation |
|---|---|
| Focused | No delegate |
| Standard | One delegate on the highest-value uncertain lane while the main agent measures another |
| Deep | After reserving capacity for the main agent, run `min(useful independent lanes, available delegate capacity)` in parallel, normally no more than three delegates in one wave |

Start another wave only for a newly exposed high-value mechanism or a bounded
verification dispute. High duplicate rates are a stop signal, not a request for
more agents.

Without subagents, run the most promising lane in the main pass and continue
only while another lane can change the ranked result. Report skipped material
coverage; do not fabricate simulated agents.

If a spawn fails, times out, or capacity drops, keep completed results and do
not relaunch the same brief unchanged. Cover locally only a missing lane that
can still change the ranked savings or requested reserve.

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
ledger. A deep scan normally assigns the two or three lanes with the largest
observable payload, not every lane.

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

## Main-Agent Sequence

1. Establish pressure target, artifact freshness, and one baseline digest.
2. Select lanes by observable byte mass and expected leverage.
3. Launch delegates together; inspect non-overlapping evidence concurrently.
4. Merge by mechanism and remove dependent, subsumed, or exclusive duplicates.
5. Recount top candidates locally, including linker cascades, setup/decoder
   cost, flags/registers/stack, branch range, and multi-target gates.
6. Stop when new lanes only duplicate candidates, lack current anchors, or
   cannot alter the top experiments.
7. Report actual delegation and materially skipped lanes in a compact synthesis.

External research can discover a mechanism or benchmark method; it cannot
confirm a saving without current project bytes and, where required, a build.
