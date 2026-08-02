# Audit Domain Lanes

Use this only after preflight shows more than one independent investigation
lane. The main agent owns evidence thresholds, promotion, severity, confidence,
and the final report.

## Workflow Boundary

`$workflow` owns effort selection, capacity, model profiles, spawning, failure
handling, and integration review. This reference supplies only Z80 audit lanes
and their evidence contracts. Give selected lane briefs to the workflow control
plan; do not recreate a second router here.

## Lane Selection

Choose from project signals; do not launch every lane by default.

| Lane | Select when |
|---|---|
| `abi-codegen` | mixed C/ASM, inline ASM, calling conventions, IX/IY, generated ASM/listings, copt rules |
| `interrupt-memory` | ISR/DI/EI, shared state, stack/BSS/fixed RAM, overlays, banks, paging |
| `semantics-reachability` | C promotion/signedness/lifetime, buffers, hostile paths, re-entry, state transitions |
| `hardware-firmware-ux` | ULA/contention, ports, ROM/RST8/esxDOS/divMMC, 48K/128K differences, flicker/input/audio/stalls |
| `research-scout` | `external-research.md` trigger fires and source discovery can resolve a top uncertainty |

The main agent keeps preflight, scanner execution, evidence ledger, and final
verification. It may cover the lane with the best local context while delegates
cover the others.

## Independence Contract

- Give every delegate the same immutable baseline digest, not another
  delegate's conclusions.
- Assign one question and a narrow path/artifact set. Overlap only for an
  intentional adversarial check.
- Do not let delegates spawn delegates, edit files, rank globally, or write the
  final report.
- Run deterministic scanners once in the main agent. Pass a short result digest
  instead of duplicating the scan.
- Send only relevant reference sections, exact paths, and at most a short
  project profile. Do not paste the whole skill, tree, or build log.
- Return zero candidates when nothing survives the lane.

## Branch Brief

```text
Task: audit-z80 candidate search
Lane: <lane>
Question: <one falsifiable question>
Scope: <exact paths/artifacts>
Baseline: <target, toolchain, flags, ABI, ISR, map/list freshness; <=12 lines>
Control: <workflow level and assigned worker role>
Constraints: read-only; no nested agents; candidates only
References: <only relevant files/sections>
```

## Compact Return Contract

Return at most three strongest candidates by default; allow five only for an
explicit exhaustive audit when all are distinct and proof-ready:

```text
- Mechanism:
  Anchor:
  Current evidence:
  Missing proof:
  Reachability/impact:
  Confidence: PROVEN | LIKELY | SUSPICIOUS | NEEDS BUILD
  Verification:
```

Add one rejected trap, or two for explicit exhaustive work, only when it
prevents a tempting false positive. No tutorial prose.

## Domain Integration Sequence

1. Run preflight and relevant bundled scanners once.
2. Build the baseline digest and select only evidence-backed lanes.
3. Give selected lane briefs to the `$workflow` control plan.
4. Merge returned candidates by failure mechanism, not syntax or file.
5. Re-read every promoted site and apply `promotion-gate.md`.
6. Ask workflow for another bounded lane only when unresolved evidence can
   change the result.
7. Stop when new lanes produce only duplicates, lack a project-local anchor, or
   cannot alter severity, confidence, or residual risk.
8. Report the actual workflow level, skipped lanes, and unresolved evidence
   needs in a short synthesis block.

External research never promotes a finding by itself; it only sharpens a local
hypothesis or verification method.
