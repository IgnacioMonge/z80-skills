# Timeline And Generated Asset Contracts

Load when effect sequencing, music sync, parameter curves or generated asset
freshness can change the current result. Existing editors and trackers can
prepare data; the runtime needs only the validated representation it consumes.
Use [measurement](measurement.md) and the existing
[deterministic verification policy](../../develop-z80/references/verification.md#deterministic-visual-state-evidence).
Do not add an editor, engine or exporter dependency without a concrete need.

## Choose One Authoritative Timebase

State whether event time means display interrupts, player ticks, tracker rows,
decoded song time or a rational mapping to wall time. A tracker row can span
several ticks and change duration with tempo; it is not inherently one frame.

Record origin, startup lead-in, zero/one-based indexing, actual target rate,
loop/reset behavior and capture/audio latency. Specify rounding/resampling when
converting editor time to target ticks. An editor's nominal frame rate need not
match a target's physical refresh exactly; check drift over the complete track.
Freeze model, configuration and binary when comparing timing changes.

## Export Typed, Bounded Events

A runtime event needs a time, a valid action identity and its typed parameters.
Define widths, signedness, ranges and pointer/bank interpretation. Keep public
or persisted formats intact unless their change is authorized.

Validate count/end bounds, unknown actions, truncated parameters, out-of-range
values, duplicate timestamps and deterministic tie order. An event at time zero
must not collide with an end sentinel. A sorted table is useful only when its
sort preserves the intended order of same-time side effects.

Dispatch all due events under an explicit missed-deadline policy. Equality-only
checks can skip an event permanently after an overrun. Define whether overdue
actions catch up, coalesce, drop or reset, including the cost of a catch-up
burst. Do not duplicate irreversible side effects during replay or seeking.

Use sufficient clock width or a proved wrap-aware comparison with a bounded
comparison horizon. Test the final event, loop boundary, long gap, time wrap and
multiple events due together. A table's nominal duration does not establish
that actual presentation and music remain aligned.

## Choose Curves As Representations

Keep discrete actions separate from continuously changing parameters. Compare
sparse keyframes plus target interpolation with baked per-tick values. Count
interpolator code/state, table bytes, decoding and consumer access using the
[asset representation method](asset-representation.md).

Define step/linear/smooth/ramp semantics, endpoint handling, quantization,
clipping, overflow and rounding. Preserve interpolation type when importing
keys; the same timestamps and values can produce different curves. Validate
exported values at every key and relevant frames between keys. For accumulated
fixed-point deltas, verify endpoint error and reset state at seeks or loops.

For captured trajectories, use recorded timestamps and explicit units/scale.
Do not infer a constant source sample rate from a tool's typical refresh.
Report clipping and approximation error after resampling/quantization, then
round-trip any lossless transform separately. Packed-size promises require
actual assets and the linked decoder/inverse costs.

## Preserve Effect State And Asset Lifetimes

Pass explicit generation/presentation time and parameters where generation runs
ahead. Do not fire an audio or display event when merely computing its future
frame. Queue time/state metadata must survive presentation; see
[audio and frame queues](audio-and-frame-queues.md).

An incoming scene's initialization must not overwrite resources still read by
an outgoing scene. During a transition, keep independent effect time, parameters
and mutable state where both are live. Delay cleanup until the final consumer
releases that state. Budget both renderers, blending/output and any concurrent
asset decode; one effect's budget does not prove the transition's budget.

## Treat Editor Formats As An Import Boundary

Read the actual versioned format or use the tool's supported export API. Check
headers, counts, lengths, interpolation types, byte order and unsupported data;
reject unknown records rather than guessing their byte length. Keep action-name
mapping explicit and validate it against target handlers.

Generate tables as build dependencies from their source asset. Retain source
hash, exporter revision/options and generated hash with the target artifact.
Rebuilding after a source edit must regenerate every dependent output. A copied
console export is a manual step whose freshness needs separate proof.

Compare source timeline/curve intent with exported data, then trace actual
target dispatch and audio/presentation boundaries. Use named ready/event states
for captures and scripted input where applicable. A host preview or raw binary
launch does not prove the release loader initializes clocks, banks and state.

## Evidence And Transfer Limits

This workflow draws on reviewed [Chapter 20, sync planning](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch20-demo-workflow/draft.md#L209-L269)
and [Appendix J, recipes](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-j-modern-tools.md#L491-L709).
Their example exporters are not validated implementations. For example,
[Rocket's primary track reader](https://github.com/rocket/rocket/blob/59be1f138c983a7b88bd94cc049db32431ed1ba2/lib/device.c#L177-L195)
includes a count and interpolation type, and its [curve implementation](https://github.com/rocket/rocket/blob/59be1f138c983a7b88bd94cc049db32431ed1ba2/lib/track.c#L7-L24)
defines the interpolation semantics. Audio-log import also needs write-event
ordering, waits and envelope retriggers, not just snapshots of final values.
See the [source assessment](../../audit-z80/references/antique-toy-review.md)
for observed errors and validation limits. No upstream exporter is imported.
