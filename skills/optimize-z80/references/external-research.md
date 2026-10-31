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

For Zeda's *Z80 Optimized Routines*, baze's *Z80 Bits* or the WikiTI and
Z80 Heaven trick pages, start with the
[corpora review](../../audit-z80/references/z80-routine-corpora-review.md).
It records which kernels ran over their full domain, which printed contracts
failed, and each file's reuse terms. Source cycle comments are not measurements.

## Tuerkas128 / Perseus

Selected source inspected on 2026-10-31 at
[`1577d4903c15c19c9382bd8c47a7bd0036f550bf`](https://github.com/RetroBensoft/Tuerkas128-Framework/tree/1577d4903c15c19c9382bd8c47a7bd0036f550bf/Perseus_1_0),
not a whole-engine audit:

| Question | Files and transfer limit |
| --- | --- |
| Model-dependent bank assignment and loading | `loader_template.asm` assigns fast/slow banks by model; treat the loader's complete entry, relocation and final map as its contract. |
| Resident execution and banked audio | `bank_2.asm` and `framework/tuerkas128_code_interrupt.asm` show a resident core with ISR player paging/restoration; verify callees, data and stack visibility in the consumer. |
| Paging helpers | `framework/tuerkas128_code_memory.asm`: `T128_SetBank` ends with unconditional `EI`; do not transplant it into an arbitrary caller/ISR interrupt contract. |

The repository declares [MIT](https://github.com/RetroBensoft/Tuerkas128-Framework/blob/1577d4903c15c19c9382bd8c47a7bd0036f550bf/LICENSE).
No upstream code/assets are imported and no build or hardware result was
obtained here. Use the [visibility transaction](generated-rendering.md#paging-must-preserve-simultaneous-visibility)
and [model rules](zx-spectrum-models.md) to evaluate a local candidate.
