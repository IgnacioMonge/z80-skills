# External Research

Research when explicitly requested, local evidence conflicts, a bottleneck lacks
a known solution, broad analysis exhausts obvious wins, or toolchain, ABI,
firmware, model, or an unusual code shape can change the ranking.
Skip when current code and fresh measurements already determine it.

Read the [shared research method](../../audit-z80/references/research-method.md).
Add the expected effect on the active bottleneck and local measurement to each
card. Rank by local evidence, decision impact, and verification cost.

Search by affected zone:

- size/resident: startup, libpull, layouts, codecs, generators, overlays;
- speed/render: traces, blitters, screen algorithms, contention, tables;
- I/O/latency: protocols, retry/state bugs, loaders, buffering, feedback;
- C/codegen: compiler issues, ABI, peepholes, emitted examples;
- hardware: model matrices, emulator tests, captures, paging/ROM effects.

For demoscene material from *Coding the Impossible* / `oisee/antique-toy`, start
with the [source assessment](../../audit-z80/references/antique-toy-review.md)
and load only the matching extracted technique family:
[math](demoscene-math.md), [generated rendering](generated-rendering.md),
[simulation/collision](simulation-and-collision.md),
[asset representation](asset-representation.md),
[audio/queues](audio-and-frame-queues.md), or [timelines](timeline-assets.md).
Upstream benchmark tables and build success do not establish local performance
or correctness.
