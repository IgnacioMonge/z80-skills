# Optimization Paths

Use paths to produce an ordered strategy, not a bag of tricks. Pick the path matching policy, profile, and evidence; mix paths only when zones genuinely overlap.

## Resident Size

1. Prove artifact freshness or mark all byte deltas unproven.
2. Inspect map/listing for lib pulls, duplicate strings/data, dead wrappers, and cold code in resident area.
3. Move cold code/data to overlays/banks only if architecture already supports it.
4. Dedup tables/literals and collapse call-ret wrappers.
5. Consider C calling convention and generated ASM cleanup.
6. Use instruction peepholes last; use dangerous tricks only for sizecoding or isolated kernels.

## Frame Render

1. Identify frame budget, hot render functions, screen writes, and contention-sensitive placement.
2. Remove redundant redraws and add dirty-region/data-layout wins before rewriting loops.
3. Add screen address/mask tables if RAM budget allows.
4. Consider compiled sprites or generated blitters for repeated shapes.
5. Compare `LDIR`, `LDI` chains, manual loops, and unrolled entry by measured path.
6. Use SP blit, floating bus, or beam racing only when target and validation allow.

## Network / I/O Latency

1. Measure waits, retry cadence, blocked frames, and duplicate init/state transitions.
2. Remove fixed waits and repeated commands before CPU micro-optimization.
3. Preserve state with explicit invalidation.
4. Drain cooperatively during waits; consider ring buffer only if complexity is accepted.
5. Optimize parser/scanner only after transport stalls are not dominant.

## C Codegen

1. Freeze compiler, CRT, clib, flags, and generated ASM freshness.
2. Find library pulls, wide math helpers, stack spills, and ABI boundary costs.
3. Narrow types and remove accidental stdlib calls.
4. Use project-native fastcall/callee conventions where ABI allows.
5. Convert only hot, small, stable kernels to ASM.
6. Reject ASM conversion when bottleneck is I/O, overlays, or algorithm.

## Demoscene / Sizecoding

1. Confirm sizecoding tolerance and target hardware.
2. Reduce data first: procedural generation, shared constants, packed tables.
3. Factor shared tails/prefixes and exploit fallthrough before opaque tricks.
4. Use `call/pop`, `jp (hl)`, dynamic unrolled entry, and SMC immediates when they save bytes.
5. Consider code=data overlap and undocumented opcodes only with target validation.
6. Keep a fallback or explicit compatibility waiver.

## Overlay / Banking

1. Measure resident and each bank/overlay occupancy.
2. Detect fixed slot size, ABI guards, dispatch cost, and load frequency.
3. Remove overlay thrash and duplicate resident/overlay state.
4. Split hot resident stubs from cold overlay bodies.
5. Pack overlays by call graph and usage phase.
6. Change dispatcher/banking architecture only after smaller layout fixes fail.

## Load Time

1. Measure the real load path first: tape/disk/esxDOS read time vs decompress time vs init time; optimize the dominant term only.
2. Compress more aggressively when the loader is I/O-bound (ZX0/LZSA class); choose a faster decoder when CPU-bound.
3. Batch small esxDOS reads into block reads; kill repeated open/seek/close in the load path.
4. Overlap work: decompress or build tables while the next block loads, if the I/O layer allows.
5. Defer non-critical loads past first interactivity (lazy-load assets on first use); show progress on a predictable loading screen.
6. Turbo/custom tape loaders only for tape targets, with fallback and model validation.

## Perceived Latency (UX)

Perceived speed is a lane of its own; users measure response, not T-states.

1. Echo input immediately (cursor move, key highlight) before processing or network round-trips.
2. Optimistic UI: apply the local effect of an action at once and reconcile on ACK/NACK; requires a visible rollback path on rejection.
3. Progressive redraw: paint the element the user is looking at first (board before panels, active line before log).
4. Split long computations across frames with a budget per frame instead of blocking (see temporal amortization technique).
5. Distinguish failure-path from success-path timeouts: fail fast and visibly, succeed patiently.
6. Measure with frames-to-first-feedback, not total completion time.

## Pure Z80 Portable

1. Treat hardware as unknown until proven.
2. Prefer CPU-core techniques: data layout, flags, dispatch, tables, loops, math.
3. Reject ULA/contention/floating-bus/border timing claims.
4. Reject undocumented opcodes unless CPU floor allows them.
5. Validate with assembler/listing and target emulator/hardware if available.
