# Modern Spectrum I/O And Macro Optimization

Not all optimization is Z80 instruction work. Many modern Spectrum apps are dominated by I/O, filesystem, serial, or overlay transitions.

## UART / ESP / Serial

Look for:

- fixed guard waits
- polling gaps longer than hardware FIFO budget
- duplicate AT/init commands
- state reinitialization across phases
- synchronous retries with long UI stalls
- missing cancellation during waits
- byte loss before buffer capacity checks

Prefer:

- measured wait paths
- state persistence with explicit invalidation
- cooperative drains during waits
- ring buffers if project accepts complexity
- fail-fast timeouts for failure path, not success path

## esxDOS / divMMC / Filesystem

Look for:

- repeated open/seek/read/close in hot paths
- overlay thrash
- unbatched small reads
- file load during UI-critical frames
- duplicated asset loads

Prefer:

- caching hot overlays
- hot/cold split
- batching
- predictable loading screens

## Perceived Latency

The user measures response, not throughput. Before optimizing any I/O path,
check the cheap perception lanes (full contract in `optimization-paths.md`,
Perceived Latency path):

- input echoed before processing or network round-trip
- optimistic local apply with visible rollback on NACK
- progressive redraw ordered by user attention
- long work sliced per-frame instead of blocking (temporal amortization)
- failure timeouts fast and visible; success timeouts patient
- metric: frames-to-first-feedback, not completion time

## State Redundancy

Search transitions:

- boot/preflight -> setup -> runtime
- resident -> overlay
- host -> game loop
- reconnect -> retry

Questions:

- Did an earlier phase already prove this hardware/software state?
- Is the proof still valid?
- Where is it invalidated?
- If invalidation is missing, do not add a fast path.
