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
