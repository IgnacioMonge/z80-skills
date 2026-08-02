# Reporting

Return a decision artifact, not a transcript.

## Contents

1. [Map or review](#map-or-review)
2. [Target design](#target-design)
3. [Migration plan](#migration-plan)
4. [Applied migration handoff](#applied-migration-handoff)

## Map or review

```text
Scope and mode:
Demand: Focused | Standard | Deep
Targets/toolchains/configurations:
Evidence, freshness, and references loaded:
Persistent map: path | not present | not requested; freshness:

Current topology:
- execution contexts
- responsibilities and owners
- state/memory ownership
- dependency directions and cycles
- runtime placement/banking/overlay map
- generated/build boundaries

Findings (BLOCKER | HIGH | MEDIUM | LOW):
[severity] title
Anchor/evidence:
Owner or boundary problem:
Runtime/maintenance impact:
Smallest correction:
Confidence: VERIFIED | LIKELY | ASSUMED | UNVERIFIED | NEEDS BUILD
Organizational cost: calls | resident bytes | bank switches | indirection | validation

Residual unknowns:
NO REORGANIZATION NEEDED: yes|no + reason
Handoff: audit-z80 | shrink-z80 | optimize-z80 | none + question
```

Prioritize findings by risk and leverage:

1. memory corruption, invalid lifetime, ABI, ISR, bank/page, loader, update, or
   format hazards;
2. multiple writers or missing ownership;
3. cycles and hidden reverse dependencies;
4. policy in rendering/storage/transport/platform code;
5. scattered target and layout facts;
6. change coupling, build friction, and navigation cost;
7. aesthetic inconsistency.

Do not inflate style preferences into architecture findings.

## Target design

```text
Scope and mode:
Demand: Focused | Standard | Deep
Targets/toolchains/configurations:
Evidence, freshness, and references loaded:
Persistent map: path | not present | not requested; planned update:

Design principles selected for this project:
Rejected patterns and why:

Target components:
component | owns | does not own | public boundary | dependencies |
state/lifetime | placement | targets | verification

Dependency direction:
<compact arrows or matrix>

Logical-to-physical mapping:
logical component | files/sections | bank/page/overlay | generated inputs

Proposed tree:
<only directories/files justified now>

Preserved contracts:
Intentional exceptions:
Expected runtime effect: neutral | measured delta | unknown/needs build
Organizational cost: calls | resident bytes | bank switches | indirection | validation
NO REORGANIZATION NEEDED: yes|no + reason
Handoff: audit-z80 | shrink-z80 | optimize-z80 | none + question
```

Explain why each new boundary exists. Do not list empty future modules.

## Migration plan

```text
Phase N - outcome
Scope/files:
Ownership or dependency change:
Preconditions:
Preserved contracts:
Checks and affected targets:
Rollback:
Blocked/unknown:
```

End with:

- ordered phases and dependencies;
- first smallest useful phase;
- checks passed, failed, blocked, and not run;
- expected temporary compatibility code and deletion point;
- residual coupling intentionally retained;
- organizational cost and accepted trade-off;
- mode, demand, references loaded, severity/confidence, and required handoff;
- repository/worktree status;
- persistent-map path, decision state, and required refresh point.

## Applied migration handoff

Report:

- scope, mode, demand, targets, and references loaded;
- boundaries established and old paths removed;
- exact files changed;
- behavior or formats intentionally changed, if authorized;
- relevant binary/map/size/timing differences;
- per-target validation results;
- unresolved risks and next approved phase;
- branch/worktree and recovery state;
- persistent-map path and final-map freshness, or why it was marked stale.

State `NO REORGANIZATION NEEDED` when the smallest justified correction is no
structural change. Hand off correctness questions to `audit-z80`, byte claims to
`shrink-z80`, and speed/RAM/latency trade-offs to `optimize-z80`.

Never claim sustainability, performance, size, or correctness as proven merely
because files moved or builds passed.
