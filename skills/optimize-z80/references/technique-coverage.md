# Technique Coverage

Read for a catalogue audit or when the observed bottleneck has no useful
candidate in the normal route. This is a maintained coverage map, not a claim
to enumerate every Z80 optimization or a checklist to load on each invocation.

**Developed** means the linked guidance gives a mechanism, applicability,
cost/tradeoff and validation/rejection boundary. **Mentioned** means discovery
or selection guidance exists but no operational treatment of that subfamily.
**Absent** means no dedicated treatment beyond this ledger. Documentation
coverage never means a technique is proven faster in the current project.

## Core CPU And Representation

| Family / subfamily | Coverage | Canonical entry / remaining limit |
| --- | --- | --- |
| Split 16-bit loop counters | Developed | [Loops](loops-and-data.md#split-16-bit-loop-counters); zero/65536 and register ownership |
| Partial LDI unroll and remainder entry | Developed | [Copies](loops-and-data.md#partial-unrolling-and-remainder-entry); entry cost and overlap |
| JR/JP choice and flag reuse | Developed | [Branches](loops-and-data.md#branch-choice-and-flag-lifetime); probability versus deadline |
| Hoisting, loop unswitching and fusion | Developed | [Loop transforms](loops-and-data.md#hoisting-specialization-and-fusion); aliasing/ISR boundaries |
| Pointer induction, page walks, sentinels | Developed | [Traversal](loops-and-data.md#pointer-induction-and-termination); bounds and final pointer |
| Split word tables and field arrays | Developed | [Layout](loops-and-data.md#split-tables-and-field-arrays); padding and other consumers |
| Packed flags, narrow IDs, power-of-two indexing | Developed | [Representation](loops-and-data.md#packed-flags-and-narrow-indices); extra accesses and ownership |
| Constant and distribution-specific arithmetic | Developed | [Arithmetic](arithmetic.md); range, intermediate width and worst case |
| Incremental stepping and fixed point | Developed | [Incremental math](arithmetic.md#incremental-coordinates-and-error-accumulators); rounding and drift |
| Small-domain, nibble and symmetry tables | Developed | [Lookup tradeoffs](arithmetic.md#small-domain-and-decomposed-lookup-tables); decomposition proof |
| SMC, shadow registers, stack fill, indirect dispatch | Developed | [Core techniques](z80-techniques.md); existing policy/ABI gates |
| Index halves, SLL, OUT zero, R sampling | Developed | [CPU-specific techniques](z80-techniques.md#undocumented-registers-as-loop-machinery); pinned CPU and live flags |
| ROM constants, overlapping code, self-destructing init | Mentioned | [Size families](z80-techniques.md#size-dark-art-families-condensed-index); individual implementations remain project-specific |
| DAA conversion tricks and packed-string decoders | Mentioned | Same size-family index; no exhaustive flags/decoder treatment |

## Rendering, Hardware And System Costs

| Family / subfamily | Coverage | Canonical entry / remaining limit |
| --- | --- | --- |
| Uncontended placement, frame windows, I/refresh | Developed | [Model timing](zx-spectrum-models.md); actual model/bank/phase still required |
| Vertical bitmap stepping | Developed | [DOWN_HL](zx-spectrum-hardware.md#down_hl-across-character-rows-and-thirds); reference check, not a universal ASM routine |
| Preshifted sprites and shared shift tables | Developed | [Sprite phases](zx-spectrum-hardware.md#preshifted-sprites-or-shared-shift-tables); spill/mask/storage costs |
| Transparent/opaque spans and compiled sprites | Developed | [Specialization](zx-spectrum-hardware.md#transparent-opaque-and-mixed-spans); generator and clipping costs |
| Dirty redraw, restoration and incremental scrolling | Developed | [Redraw](zx-spectrum-hardware.md#incremental-redraw-and-scrolling); overlap and dense-change fallback |
| Floating-bus acquisition | Developed | [Floating bus](zx-spectrum-hardware.md#floating-bus); model-specific marker/cadence still needs implementation |
| Compression selection and decoder/workspace accounting | Developed | [Measurement](measurement.md#compression-tradeoff-evidence-card) and [load path](optimization-paths.md#load-time); individual codec kernels not catalogued |
| UART/filesystem batching and state reuse | Mentioned | [I/O](modern-spectrum-io.md); no device-specific FIFO budgets or driver recipes |
| Frame slicing and perceived latency | Developed | [Temporal amortization](z80-techniques.md#temporal-amortization-work-spread-across-frames) and [UX](optimization-paths.md#perceived-latency-ux) |
| ABI/codegen and linked runtime/initialization | Developed | [ABI](z88dk-sdcc-abi.md), [CRT/sections](toolchain.md#linked-runtime-and-initialization); installed compiler decides |
| Banking/overlays and screen flipping | Mentioned | [Banking path](optimization-paths.md#overlay--banking); no per-engine layout or flip routine |
| AY/beeper kernel optimization | Mentioned | [Audio signals](zx-spectrum-models.md#audio-and-input); player-specific kernels absent |
| Full line/polygon rasterizers and collision algorithms | Absent | Incremental arithmetic is covered; clipping, tie rules and engine-specific algorithms are not |
| Next DMA/Z80N/hardware-sprite recipes | Absent | Separate core/peripheral evidence required; no transfer from classic Spectrum |
| MSX/CPC/other peripheral acceleration recipes | Absent | Core Z80 techniques apply; VDP/CRTC/device recipes are outside current references |

## Research And Evidence

The operational additions concentrate on three questions, checked against
primary material on 2026-09-11:

| Question | Source class / anchor | Transfer and verification |
| --- | --- | --- |
| Can repeated loop control/math work be removed? | [Grauw's loops](https://map.grauw.nl/articles/fast_loops.php) and [multiplication](https://map.grauw.nl/articles/mult_div_shifts.php), author implementations for MSX; [Zilog manual](https://www.zilog.com/docs/z80/um0080.pdf), CPU specification | Mechanisms supported externally; nominal loop formulas derived separately and checked by the bundled example tests. No imported MSX timing percentages. |
| Can layout, phases and byte classes remove rendering work? | [SP1 example](https://www.z88dk.org/wiki/doku.php?id=libnew:examples:sp1_ex1), engine-author documentation for Spectrum | Phase-table precedent; generic storage/compositor formulas are local derivations with reference checks, not SP1 performance claims. |
| Can linked runtime/data costs disappear? | [z88dk guidance](https://github.com/z88dk/z88dk/wiki/WritingOptimalCode), toolchain-maintainer documentation | Supported mechanisms; installed CRT, map and boot validation still decide applicability. No project savings measured. |

Keep absent/mentioned entries honest. Expand them when an actual target or
requested catalogue scope supplies the implementation and validation boundary;
do not copy a manual or add an instruction merely because it exists. A broad
project review should also consider deleting work or changing the algorithm
before selecting assembly mechanisms. Follow [external research](external-research.md)
when the next material gap can affect the decision.
