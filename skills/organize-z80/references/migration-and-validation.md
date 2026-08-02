# Migration and Validation

Reorganize incrementally. Preserve behavior first; improve behavior in separate
work after the structure has a verified baseline.

## Contents

1. [Migration strategy](#migration-strategy)
2. [Demand-scaled phases](#demand-scaled-phases)
3. [Phase gates](#phase-gates)
4. [Move ordering](#move-ordering)
5. [Validation matrix](#validation-matrix)
6. [Rollback and stopping](#rollback-and-stopping)
7. [Apply-mode discipline](#apply-mode-discipline)

## Migration strategy

Choose the smallest migration unit that establishes one real boundary:

- move a generated asset behind its generator contract;
- centralize duplicated layout constants;
- give one buffer or state group a single owner;
- isolate one hardware adapter;
- separate one renderer from application policy;
- split durable serialization from filesystem transport;
- create one explicit C/ASM ABI wrapper;
- centralize bank or overlay transitions.

Avoid a repository-wide move as the first step. Path churn hides semantic drift,
breaks blame, and makes rollback expensive.

Reuse current maps, symbol tables, listings, build recipes, and smoke commands.
Do not create replacement analysis tooling when existing evidence answers the gate.

## Demand-scaled phases

Use only phases needed by the selected demand and changed boundary:

| Demand | Required sequence | Add only when evidence requires it |
| --- | --- | --- |
| Focused | 0, 2, one of 3–7, validation | 1, 4–6, 7 |
| Standard | 0–3, selected 4–6, validation | 7 after callers migrate |
| Deep | 0–7 | none; cover all active targets/classes |

Do not run a ceremonial full sequence. Record skipped phases and why.

## Phase gates

### Phase 0: Freeze the baseline

Capture:

- revision, branch, and dirty state when available; otherwise mark VCS state
  unavailable and record the recovery material; also capture targets,
  configurations, and tool versions;
- build/test commands and generated-input chain;
- artifact hashes/sizes and relevant map/layout facts;
- public symbols, binary/file/wire formats, and behavioral smoke tests;
- known failures and unavailable hardware checks.

Gate: reproduce the cheapest relevant baseline or label it unavailable before
editing.

### Phase 1: Publish the map

Produce responsibility, state, dependency, execution-context, and placement
tables. Identify assumptions and no-change zones. When persistence was
explicitly requested, record the baseline and proposed target using
`persistent-project-map.md`; do not present a proposal as current reality.

Gate: every proposed component has an existing responsibility and evidence.

### Phase 2: Define contracts

Define the target owner and public boundary before moving code. Add the smallest
guard that will detect breakage: build assertion, ABI harness, source guard,
unit test, emulator test, or artifact comparison.

Gate: the old implementation passes the new guard.

### Phase 3: Move leaf responsibilities

Move components with few outgoing dependencies and no shared mutable ownership:
constants, generated resources, pure conversions, platform adapters, private
helpers, or immutable tables.

Gate: paths/includes/build inputs change; behavior and relevant artifacts remain
equivalent or every difference is explained.

For every ASM split or move, also:

- record assembler scope rules and all affected local/numeric labels, `MODULE`,
  macro, `EQU`/`defc`, `PUBLIC`, and `EXTERN` declarations;
- compare pre/post symbol tables when available, including address changes;
- explain each changed public symbol or address before accepting the move.

Do not accept successful assembly or linking as proof that a scope-preserving
move is safe.

### Phase 4: Transfer state ownership

Introduce one owner, route writers through it, then remove direct access. Avoid
moving representation and changing semantics in the same step.

Gate: readers/writers, reset, lifetime, ISR access, and error paths match the
approved contract.

### Phase 5: Reverse dependencies

Move application policy out of rendering, storage, transport, and platform
code. Prefer narrow calls, data snapshots, or command/event structures already
justified by actual interactions.

Gate: dependency cycles disappear or remain as documented exceptions; runtime
cost stays within target constraints.

### Phase 6: Align physical layout

Only when needed, adjust sections, banks, overlays, generated addresses, or
link order to match the logical organization.

Gate: fresh per-target maps, binaries, stack margins, branch ranges, relocation,
interrupt safety, and loader/update contracts pass.

### Phase 7: Remove obsolete paths

Delete forwarding shims, duplicate constants, legacy includes, and temporary
compatibility code only after all callers have migrated.

Gate: search confirms no maintained caller remains; full relevant validation
passes; rollback point is recorded.

Before deleting ASM or an entry point, inspect maps/symbols and explicit
indirect references. Block deletion until jump tables, interrupt vectors,
RST/NMI hooks, SMC targets, generated offsets, loaders, absolute-address
contracts, and external callers are absent or migrated. Text search alone is
insufficient.

## Move ordering

Prefer this order unless project evidence contradicts it:

1. source-of-truth and generated-data boundaries;
2. immutable constants/tables and pure helpers;
3. hardware or OS adapters;
4. stateless capabilities;
5. stateful capabilities with one existing owner;
6. shared state requiring ownership transfer;
7. orchestration and dependency reversal;
8. placement, banking, overlay, or ABI-sensitive moves;
9. removal of compatibility paths.

Delay a move when it combines multiple unknowns, lacks a rollback, or cannot be
validated independently.

## Validation matrix

Select checks from the changed boundary; do not run a ceremonial full matrix
when it adds no evidence.

```text
boundary | target/config | build | functional | ABI | map/layout | size/hash |
timing | hardware/emulator | generated freshness | result
```

### Source and build

- all maintained targets/configurations compile and link;
- include/import paths, assembler order, linker inputs, and generators use the
  new authority;
- no generated or build artifacts remain unintentionally dirty;
- public symbols and entry points remain present where required.

### Behavioral

- existing tests pass;
- focused tests exercise the moved owner and failure/recovery paths;
- CLI, file, save, protocol, and update compatibility remain intact;
- emulator or hardware smoke tests cover timing/device behavior when relevant.

### ABI and control state

- argument/return conventions and symbol decoration match;
- registers, flags, alternate sets, IX/IY, SP, and interrupt state are preserved;
- bank/page state is restored on every success and error path;
- callbacks, vectors, and tables retain address and lifetime validity.

### Memory and placement

- resident/banked/overlay sizes and ceilings pass per target;
- BSS, stack floor, scratch buffers, aliases, and lifetimes do not overlap;
- absolute addresses, alignment, branch ranges, SMC, relocation, and generated
  offsets remain valid;
- contention or latency class changes are measured when material.

### Artifact comparison

First probe determinism: build twice without source changes and identify stable
artifacts. For a pure structural move, use the strongest applicable step:

1. identical hash for stable artifacts;
2. normalized hash after removing documented non-semantic variation;
3. map, section, symbol, size, and generated-resource comparison;
4. emulator, hardware, or manual smoke check for the changed behavior.

Binary difference is not automatically failure, but unexplained difference is.

### No-test fallback

When no automated tests exist, run the available evidence ladder and report
the ceiling:

1. rebuild and compare maps/symbols/artifacts;
2. run an emulator or hardware smoke scenario when available;
3. record a repeatable manual scenario, expected result, target, and observer;
4. mark unrun behavior `UNVERIFIED` or `NEEDS BUILD`.

## Rollback and stopping

Give every phase:

```text
Scope:
Precondition:
Expected structural result:
Runtime invariants:
Checks:
Rollback:
Blocked evidence:
```

Define recovery without assuming VCS: save a patch, copy the affected files to
a named recovery location, or keep a reversible move manifest before editing.
Verify that the recovery material restores the prior paths, includes, and build
inputs.

Stop and reassess when:

- a supposedly structural move changes behavior or format;
- the new boundary needs broad writable access to old internals;
- target-specific glue spreads rather than contracts;
- calls, bank transitions, code size, or latency grow materially without an
  accepted trade-off;
- a build failure exposes a hidden placement or include-order contract;
- the next step requires unrelated cleanup to proceed;
- remaining pain is aesthetic rather than operational.

## Apply-mode discipline

- Follow repository instructions and preserve unrelated changes.
- Keep one migration phase per coherent commit when commits are requested.
- Do not reformat moved code unless required for correctness.
- Prefer move-aware history preservation where tooling supports it.
- Run the smallest decisive check after each phase; run the full affected matrix
  before handoff.
- Inspect the full diff and status. Report passed, failed, blocked, and not-run
  checks separately.
- When a canonical project map exists and the slice changes its mapped scope,
  refresh its final map from verified source and artifacts or mark it stale.
- Leave no temporary worktrees, generated debris, or hidden configuration
  changes unless the user explicitly requests retention.
