# Measurement

Measure only when a number can change the ranking. Before commands, apply the
canonical path, disposable-worktree, runner, cleanup, and contamination rules
in `hard-contract.md`; this reference defines measurement choices, not a second
worktree contract.

## Baseline

1. Capture primary branch, status, and diff as the contamination baseline.
2. Create the worktree and run `RUNNER --primary <primary-root> --worktree
   <worktree-root> -- python3 "$SKILL_DIR/scripts/preflight.py"`.
3. Freeze compiler, assembler, linker, CRT/clib, flags, target, and fixture.
4. Build the smallest target that produces the required fresh artifact.
5. Record artifact path, command, before value, and uncertainty.

## Smallest Useful Metric

| Question | Metric / fixture |
|---|---|
| linked or resident size | map/listing/section bytes and stack gap |
| bank/overlay pressure | resident plus every affected bank/slot occupancy |
| kernel speed | loop-count-adjusted T-states or isolated `ticks` run |
| frame/render latency | deterministic input plus border/frame trace |
| I/O or UX stall | blocked frames, retry cadence, timeout, load count |
| hardware contention | same model/ROM with contention enabled or real hardware |

Static estimates identify candidates; fresh artifacts may prove size; emulator
or `ticks` can prove the exercised kernel; hardware evidence applies only to
the tested model and conditions.

### Compression tradeoff evidence card

Keep one compact card per retained compression candidate, using measured values
when available and labeling estimates explicitly:

```text
asset | original_bytes | packed_bytes | decompressor_plus_glue_bytes |
peak_workspace_bytes | residency/bank_pressure | decompression_cycles |
transition/stall_frames | result | evidence_ref | current
```

`result` must make the tradeoff visible (including net storage and peak-RAM
delta); do not report packed bytes alone. Retain machine-readable results when
the existing tooling supports them, alongside the human summary. Keep
decompression cycles and transition/stall frames separate from static byte
claims.

## One-Candidate Experiment

Requires explicit user approval.

1. Change one main variable in the worktree.
2. Rebuild the same target with the same fixture.
3. Compare matching artifacts with `"$SKILL_DIR/scripts/bincompare.py"`, a
   map/listing diff, or the selected runtime measurement, again through the
   shared runner.
4. Re-run `"$SKILL_DIR/scripts/preflight.py" --json` through the shared runner
   to confirm freshness.
5. Run the narrowest behavior, ABI, interrupt, paging, model, and regression
   checks implicated by the candidate.
6. Compare the primary tree with its captured baseline; a pre-existing dirty
   state is allowed, a skill-caused delta is not.
7. Capture results, then delete the worktree unless the user explicitly asked
   to retain it for hardware testing.

## Decision

- **Graduate to PROVEN** only with a current evidence card for a fresh artifact,
  trace, test, or reproducible measurement.
- **Reject** when the build/test fails, the delta is noise or negative, a target
  ceiling regresses, validation costs exceed the benefit, or a hidden hardware
  state is required.
- **Remain LIKELY/SPECULATIVE** when branch direction, loop count, contention,
  interrupt timing, target coverage, or artifact freshness is unresolved.

For multi-target work, freeze one source revision and configuration, then use
the fresh artifact for each declared target; every target must pass its own
limits.
