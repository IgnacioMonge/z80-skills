# Reporting

Return a decision artifact, not a transcript. Use the common fields once,
then only the section matching the requested mode.

## Common fields

- Scope/mode; demand (`Focused | Standard | Deep`); targets/toolchains/configurations.
- Evidence, freshness, references loaded; persistent-map path/status, freshness,
  planned update or refresh point.
- Preserved contracts, authorized exceptions, residual unknowns/coupling,
  severity/confidence where applicable, and next decision or approved phase.
- Organizational cost: calls, resident bytes, bank switches, indirection,
  validation; accepted trade-offs.
- Repository/worktree and recovery state for migrations.
- `NO REORGANIZATION NEEDED`: yes/no and reason.
- Handoff and question: correctness → `audit-z80`; bytes → `shrink-z80`;
  speed/RAM/latency → `optimize-z80`; otherwise none.

## Map or review

Describe contexts, responsibilities, state/memory owners, dependencies/cycles,
runtime placement/banks/overlays, and generated/build boundaries.

For each finding:
```text
Severity: BLOCKER | HIGH | MEDIUM | LOW
Title / anchor / evidence:
Owner or boundary problem / runtime or maintenance impact:
Smallest correction:
Confidence: VERIFIED | LIKELY | ASSUMED | UNVERIFIED | NEEDS BUILD
```

Rank runtime hazards first (memory/lifetime/ABI/ISR/banks/loaders/formats), then
ownership, cycles, misplaced policy, scattered layout facts, change/build cost,
and aesthetics. Do not inflate style preferences into architecture findings.

## Target design

State selected principles and rejected patterns, then:

- components: owner, exclusions, public boundary, dependencies, state/lifetime,
  placement, targets, verification;
- dependency arrows and logical component → files/sections → bank/overlay →
  generated inputs;
- proposed tree containing only justified directories/files;
- expected runtime effect: neutral, measured delta, or unknown/needs build.

Explain each new boundary; no empty future modules.

## Migration plan

```text
Phase N / outcome / scope/files:
Ownership or dependency change / preconditions:
Preserved contracts / checks and affected targets:
Rollback / blockers:
```

Order phases by dependencies and name the first useful slice. Include checks
passed/failed/blocked/not run, temporary compatibility code and its deletion
point, and persistent-map decision state.

## Applied migration handoff

Report boundaries established, removed paths, exact changed files, authorized
behavior/format changes, relevant binary/map/size/timing differences, per-target
checks passed/failed/blocked/not run, and final-map freshness or why it is stale.

Moving files or passing builds alone proves neither sustainability nor
performance, size, or correctness.
