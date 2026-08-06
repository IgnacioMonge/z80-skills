# Verification and Reporting

Build a verification matrix from acceptance criteria; do not invent a generic
test stack that the project cannot run.

## Baseline and Freshness

Before implementation, capture the cheapest relevant baseline:

- repository status and current revision/branch when available;
- target/configuration and exact build recipe;
- existing tests, emulator/hardware harness, and known-good behavior;
- relevant map, symbol, listing, binary, asset, timing, or screenshot/state
  artifact.

Treat an artifact as fresh only when it matches current source, target,
configuration, and recipe. A timestamp alone is insufficient.

## Evidence Layers

Use only applicable layers:

| Layer | Evidence | What it can prove |
| --- | --- | --- |
| Build | assembler/compiler/linker exit and diagnostics | syntax, linkage, recipe viability |
| Structure | map, symbols, listing, generated ASM, binary comparison | placement, pulls, emitted code, declared layout |
| Technical runtime | emulator trace/state, probes, instrumentation, hardware measurement | ABI, memory, timing, interrupts, I/O behavior |
| Product runtime | controlled play/use path, captured state/output, human checkpoint | visible flow, controls, feel, failure and edge behavior |
| Multi-target | the applicable layers repeated per target/configuration | compatibility within the exercised matrix |

Use the project's existing emulator, harness, profiler, or hardware path. When
none exists, describe the smallest reproducible manual procedure and mark it
`NOT RUN` until observed. Do not name an arbitrary emulator as proof.

## Acceptance Matrix

Report every criterion in this shape:

```text
AC ID | Product/Technical | Target | Method | Evidence/freshness |
PASS/FAIL/BLOCKED/NOT RUN | Confidence | Notes
```

- Require observed user-visible behavior for `AC-P-*`. A build cannot pass it.
- Require target-appropriate artifact or runtime evidence for `AC-T-*` involving
  ABI, layout, cycles, stack, interrupts, banking, I/O, or compatibility.
- Use `BLOCKED` only when a named dependency prevents the check; use `NOT RUN`
  when the check was available but not executed.
- Keep estimates labeled and separate from measured results.

## Task Gate

Mark a task `DONE` only when its completion check passes, linked criteria remain
consistent, emitted changes stay within its surface ceiling, and rollback is
available. A `SPIKE` completes when it closes or sharply bounds its named unknown;
prototype code is not automatically production code.

## Milestone Product Checkpoint

Require all of the following before declaring a milestone complete:

1. The runnable or inspectable slice exists.
2. Required technical criteria pass for every affected target or are explicitly
   blocked/not run.
3. Product criteria have observed evidence.
4. Feel, usability, or visible trade-offs requiring human judgment are presented
   to the user as one concrete checkpoint question.
5. The dossier, diff, repository status, residual risk, and rollback are current.

Pause after the checkpoint by default. Continue to another milestone only when
the user explicitly authorizes it in the current session or the dossier's
auto-advance session matches the current runtime session and its remaining count
is positive. Decrement the count at the boundary; authorization expires at zero
or session end. Even with auto-advance, pause when observed product behavior
creates a material decision or invalidates the specification.

## Reconciliation

When evidence contradicts the specification, do not patch around it silently.
Apply the dossier's `SPEC REVISION` protocol, identify affected criteria and
tasks, reopen invalidated work, and re-plan only the impacted scope.

End with mode/stage/demand, mutation-boundary class, spec-acceptance state,
references loaded, dossier path, exact checks and evidence classes, acceptance
matrix, product checkpoint, residual risks, rollback, repository status, and the
next automatic action.
