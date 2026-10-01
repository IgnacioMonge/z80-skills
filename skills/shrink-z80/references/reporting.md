# Reporting

Write an optimization backlog, not a transcript.

## Candidate

```text
[CATEGORY] ID - title | SAFE|AGGRESSIVE|EXPERIMENTAL | EXACTO|ESTIMADO|REQUIERE BUILD
Anchor: current path:line plus artifact/byte evidence
Pressure target:
Change:
Net saving: CODE/DATA/storage/BSS/stack/bank impact
Cost: runtime, peak RAM, complexity, compatibility, testing
Dependency: independent | depends_on:<ID> | subsumed_by:<ID> | exclusive_with:<ID>
Verification:
```

Order by net impact, safety, and leverage. Never sum speculative, dependent,
subsumed, or mutually exclusive candidates.

## Totals

Report only:

- confirmed independent total;
- confirmed dependent items;
- requires-build items;
- speculative items excluded from totals.

For multiple maps or targets, name the selected artifacts. A candidate is
confirmed only when every declared target passes its resident ceiling and
stack-gap floor on the same build.

## Coverage

Add one compact ledger:

```text
Checked: <applicable high-yield lanes + evidence>
None found: <checked lanes with no surviving candidate>
Skipped/n/a: <irrelevant or blocked lanes + reason>
Artifacts: <map/sym/list/generated asm/opt/rul/bin or none>
Freshness:
Sandbox: <none | path + deleted | retained by explicit request>
```

Mention actual agent/research use only when it occurred.

## Compression Net

For every compression claim:

```text
Original_bytes:
Packed_bytes:
Decoder_share:
Call_glue_bytes:
Net_storage = Original - (Packed + Decoder_share + Call_glue)

Workspace/stack/BSS peak delta:
Workspace lifetime/reuse proof:
Pressure target:
Certainty:
Evidence:
```

Do not subtract workspace from storage. Combine them only for an explicitly
defined resident-total metric with proven non-overlapping lifetimes.

## Multi-Target Gate

For each target include:

```text
target | artifact | resident used/ceiling | stack gap/floor | pass|reject|REQUIERE BUILD
```

Missing linked evidence is `REQUIERE BUILD`, never a partial confirmation.

## Hard-Contract Echo

If a disposable worktree was used, state its path, primary-tree clean check,
and whether it was deleted or retained by explicit user request.
