# Evidence and Handoffs

Read this reference only after the canonical gate run passes or when checking
hardware evidence or final handoff.

## Evidence Chain

Keep these identities aligned without recreating their validators:

1. consumer product and manifest schema;
2. declared base and current consumer commit;
3. successful command stages required by enabled capabilities;
4. declared hardware artifact paths, roles, sizes, and aggregate digest;
5. installer minimum firmware and tested cartridge firmware;
6. required physical cases and their user-observed results;
7. declared branch, upstream, and remotely available tested commit.

Classify each link as `PASS`, `FAIL`, `BLOCKED`, or `NOT RUN`. A later link
cannot repair an earlier mismatch. Any source, manifest, artifact, firmware, or
Git change invalidates the dependent evidence and returns control to the next
state emitted by `port request`.

## Physical Checkpoint

Generate the hardware checklist only from the current passing gate report.
Present the exact artifact identity and required cases, then stop for the user's
physical results. Record `PASS` only from an explicit observation against that
candidate and firmware; preserve failures and pending cases.

One failed case opens one causal lane. Change one axis, regenerate invalidated
evidence, and repeat the canonical gate. Do not reuse a checklist or digest
after rebuilding.

## Final Handoff

Run the external handoff command only after every required physical case passes
and current authorization covers the required Git publication step. Completion
requires the external handoff itself to report `PASS` for the same clean
consumer commit, artifact bundle, firmware floor, physical results, branch, and
upstream.

Report the handoff artifact path, tested commit, bundle digest, firmware, and
residual external risks. Do not call a port complete from source review, a
successful build, generated packaging, or hardware success alone.
