# Audio Ownership And Frame Queues

Load for player/SFX integration, sampled audio, audio jitter or bursty frame
production. Trace the actual player, ISR, foreground, output and bank paths.
Use the existing [ISR/stack contract](../../audit-z80/references/isr-map.md),
[ABI checks](../../audit-z80/references/asm-abi.md) and
[measurement policy](measurement.md). These mechanisms require local proof.

## Identify The Clocks And Resources

A tracker row and a player tick are different clocks. A row can span multiple
ticks while ornaments, slides and other modulation still update each tick.
Keep row advancement separate from per-tick processing and output. An early
return on every non-row tick can silently freeze modulation or hardware writes.

Record the active clock source, rate, song-start origin, looping behavior and
what happens after a missed tick. A generic Z80 has no built-in AY or display
clock. Stock ZX48K beeper and ZX128K AY paths have different requirements;
expansions, TurboSound and Next audio capabilities are explicit target choices.

For each AY chip distinguish ownership of:

| Resource | Scope to arbitrate |
| --- | --- |
| Tone period and channel volume | Individual channel |
| Mixer control fields | Per-channel fields within shared register state |
| Noise period | Shared by channels using that chip's noise source |
| Envelope period and shape/retrigger | Shared by channels using that envelope |
| Selected chip and selected register | Shared output-interface state |

Stealing a channel does not make shared noise or envelope state private. An
SFX can change a sustained instrument on another channel through those shared
resources. Reserve them, arbitrate them, or explicitly accept the audible
compromise. Additional chips provide more independent resource groups; they
are not automatically one enlarged chip with interchangeable voices.

## Compose Desired State, Then Preserve Write Events

A useful integration seam is music's desired register image → SFX/resource
arbitration → deliberate hardware flush. Prefer the current player interface
when it already expresses these responsibilities. Do not rewrite a working
player just to introduce this structure.

Define SFX priority, preemption, channel/resource lease, termination and release.
Choose whether release resumes current music state or restarts an instrument.
Restore shared mixer/noise/envelope ownership as well as the stolen channel.
Use a bounded length or unambiguous control encoding; an otherwise legal tone
byte must not accidentally serve as an end marker.

Register values do not capture all audio semantics. An AY envelope-shape write
can retrigger the envelope even when its value is unchanged. A value-difference
flush may suppress that event; an unconditional full dump may add unwanted
retriggers. Preserve event/write masks or an ordered event stream separately
from the last-value image. Preserve same-value writes and sub-tick ordering
when the player uses them deliberately.

For register-select followed by data-write, prove that another context cannot
change the selected register/chip between the two operations. Serialize access
or give the whole output transaction one owner. State whether selection is
restored or remains owned afterward. Do not rely on an unrelated helper's last
selected register, active chip or mixer configuration.

## Make The ISR Boundary Explicit

List all registers and flags used by the player and its helpers, including the
alternate sets and IX/IY. An ISR saving main AF/BC/DE/HL is insufficient if its
callee also uses foreground-owned alternate registers. Define stack depth,
reentrancy, interrupt state and every helper's preservation obligations.

Prove player code, mutable state, song data, stack and interrupt vectors remain
visible while the foreground pages banks. Account for ROM/firmware calls and
output handlers that can change paging or interrupt state. Keep this contract
at the integration boundary rather than inferring it from one routine's body.

Measure worst relevant ticks: new row/pattern, tempo changes, song loop, dense
modulation and simultaneous SFX. Include arbitration, output, bank transitions,
ISR entry/save/restore and contention. An average player cost does not prove a
frame or sample deadline. See [model timing](zx-spectrum-models.md).

## PCM And Hybrid Sound Are Scheduling Choices

Volume-register sample playback requires a known mixer/output state, sample
encoding and amplitude mapping. Numeric volume levels need not form a linear
DAC. Multi-channel amplitude mixing additionally depends on chip and analogue
mix behavior; calibrated tables do not transfer automatically across devices.

A short sampled attack followed by hardware-generated decay can reduce the
CPU blackout compared with a complete sample. It still consumes a measured
burst, and its envelope may conflict with music. Specify sample count, actual
rate, loop timing, allowed jitter, handoff state and resource-release behavior.

If interrupts are masked during playback, maskable display/music handlers do
not run. A RAM queue alone cannot change that. Alternatives include bounded
cooperative service points, an interruptible player with a proved jitter budget,
independent audio/display hardware, or deliberate repeated display frames.
Choose according to the product's audio/visual requirements and validate the
chosen fallback. Buffering cannot manufacture spare cycles.

## Prove Capacity, Service And Recovery Separately

A frame queue can decouple generation from presentation only when all three
conditions hold:

1. **Capacity:** usable reserve covers the longest producer blackout plus
   presentation latency and jitter. Count complete published frames, not a
   partially written slot or nominal allocation.
2. **Service:** a consumer actually presents a frame at each required deadline
   during that blackout. The classic ULA does not autonomously consume an
   arbitrary RAM ring; copying or a legal page flip still needs service.
3. **Recovery:** over repeated bursts the producer can replenish what was
   consumed. Generating at most one frame per presentation interval cannot
   refill a reserve after losing a generation interval.

Track occupancy as previous occupancy plus produced minus consumed, maintaining
zero through usable capacity. Derive this over the actual dense music/timeline
passage, including consecutive bursts, transitions and slow generation paths.
Initial prefill is not a steady-state throughput proof. A larger queue can
absorb a finite burst but cannot repair a sustained production deficit.

Define queue-empty and queue-full behavior: repeat/drop/stall/reset according
to the product contract. Preserve an underrun/overrun signal for verification;
do not silently clamp a broken count and call the schedule correct.

## Publish Complete Slots With Single Ownership

Give each index/state variable an owner. A single-producer/single-consumer
head/tail design can avoid a count modified by both contexts, but its capacity,
wrap and full/empty rules still need proof. A byte-sized load/increment/store
sequence is not atomic merely because its storage is one byte.

Write the full payload and metadata before publishing a slot. Do not consume
before publication or overwrite before release. If publication needs a short
critical section, bound it and preserve the caller's interrupt contract.
Snapshot multibyte clocks/pointers without torn reads. More producers or
consumers need additional synchronization; do not reuse the single-owner proof.

Associate generated frames with their intended presentation time and scene
state. Advancing generation time must not fire display/audio events early.
After a scene change, drain, tag or discard queued frames explicitly so old
content cannot appear under new parameters. Generate prefill frames at their
own intended times rather than repeating one current-state frame by accident.

Calculate slot addresses from validated indices and stride; prove every slot
fits its actual address interval. Account for metadata, history, alignment and
stack growth. On banked targets, identify the physical bank of each live slot,
consumer, producer and interrupt path. Logical address ranges alone do not
prove simultaneous visibility or non-overlap.

## Verification And Evidence

Use a fixed song/input interval and retain register-write traces with time,
chip, register, value and retrigger events. Compare against a known-good player
where available. Exercise row/pattern/loop and tempo boundaries, shared-resource
conflicts, SFX preemption/release and all legal data values.

For a queue, log produced/published/consumed IDs, occupancy, timestamps and
underruns. Check blackout and recovery intervals, full/empty/wrap boundaries,
scene changes and relevant interrupt interleavings. Guard payload/stack regions
and test the worst observed producer/consumer paths on the intended model.
A host schedule model does not prove ISR timing, paging or actual presentation.

Listen or capture the intended output for timbre, analogue-mix or jitter claims.
A register trace alone cannot establish those perceptual results. Conversely,
a pleasant recording cannot prove stack safety or absence of queue corruption.
If runtime evidence is unavailable, retain a candidate with explicit NOT RUN
checks and a concrete fallback; do not promote it as seamless playback.

## Sources And Scope

The mechanisms were extracted critically from [Chapter 11, player/SFX](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch11-sound/draft.md#L590-L858)
and [Chapter 12, buffering/scripts](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch12-music-sync/draft.md#L130-L267).
Their sample engine does not establish these obligations; see the
[source assessment](../../audit-z80/references/antique-toy-review.md).
Use [official Next audio documentation](https://wiki.specnext.dev/Turbo_Sound_Next)
for that backend's chip selection, channel mapping and audio-mode controls.
[The primary chips emulator implementation](https://github.com/floooh/chips/blob/9e88298ce56319953ac7a43213a1120359f7a3a6/chips/ay38910.h#L551-L555)
restarts the shape on each shape-register write; its [restart routine](https://github.com/floooh/chips/blob/9e88298ce56319953ac7a43213a1120359f7a3a6/chips/ay38910.h#L424-L433)
resets the envelope counter. This corroborates event semantics in that model,
not a fresh hardware measurement. Exact register bits, expansion protocols and
chip/firmware behavior require primary documentation for the active target;
no upstream player is imported.
