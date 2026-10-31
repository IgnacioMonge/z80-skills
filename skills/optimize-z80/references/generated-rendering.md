# Generated Rendering And Sampling Maps

Load for repeated texture warps, geometry transforms, generated render lists or
banked render kernels. These are candidates for a measured bottleneck, not a
complete engine. Fixed tables/native specialization are MEDIUM; opcode generation
and repurposed SP inherit the existing DANGEROUS gates. Apply
[policy](project-policy.md), [SMC](z80-techniques.md#smc-immediates-and-jr-offsets),
[stack](z80-techniques.md#stack-blit--stack-fill),
[CPU/ISR proof](z80-proof-obligations.md) and
[model timing](zx-spectrum-models.md#frame-window-planning).

## Compile The Sampling Map

Beyond [compiled sprites](zx-spectrum-hardware.md#compiled-sprites), specialize
where a renderer reads, advances and packs samples. Represent a fixed distortion
as source addresses, skip distances or an emitted instruction sequence. Remove
per-sample decisions only when geometry and source format make them invariant.

Source encoding can make packing branchless: eight samples restricted to 0/1
form a byte by repeated left-shift/add; four samples restricted to 0/3 form four
two-bit fields with two left shifts between samples. Other values can carry into
neighboring fields. Compare every binary input pattern with a pixel oracle;
include masking, clipping, field order and the initial accumulator value.

An arbitrary gather can emit `LD HL,source; LDI` per output byte: nominal 26 T
and five executable bytes, before framing. Thus 768 cells need 3,840 code bytes;
multiple mapping phases multiply storage. LDI advances HL/DE, decrements BC and
changes flags; preserve the [block-op contract](z80-proof-obligations.md#block-operations).
This instruction-derived cost is not a measured effect or frame rate.

Choose the smallest representation that removes the actual repeated work:

| Representation | Paid before execution | Remaining runtime cost |
| --- | --- | --- |
| Interpreted address/skip table | Table generation and storage | Fetch, address setup and loop control |
| Build-time native kernel | Generator, emitted code and alignment | Kernel execution and mapping selection |
| Runtime operand patching | Patch stores and synchronization | Specialized kernel execution |
| Runtime opcode generation | Generator, output buffer and synchronization | Generated kernel execution |

Count the whole interval: generation/patching + all kernel calls + transfer,
paging, setup, dispatch, interrupts and contention. Compare with the existing
renderer over the same number of reused frames/calls. A cheap inner loop loses
if regeneration or executable storage does not amortize. Longitudinal rotation
may change a texture origin without changing its skip geometry; prove which
parameters actually invalidate the map before regenerating it.

Reject when code growth, patch latency, irregular mapping or required clipped
variants exceed budget. Retain the interpreted map, arithmetic or generic renderer
as fallback; a smaller viewport/update rate changes product behavior and needs
the corresponding product criterion.

## Shared Transforms And Affine Basis DAGs

Compute frame-constant transform coefficients and repeated subexpressions once;
count their setup, live storage and reuse before instruction tuning. Linear
rotation preserves negation and midpoint relationships, so rotate basis vertices and
derive dependent vertices afterward. Perspective is nonlinear: averaging
projected endpoints generally differs from projecting their midpoint.

Encode dependencies as a bounded, topologically ordered DAG with initialized
roots and checked indices. For a few static objects, generated native operations
can beat a compact interpreter; many objects may favor shared bytecode. Charge
fetch, address reconstruction, loads/stores and dispatch as well as arithmetic.

Prove model relationships and accepted approximation. Widen signed midpoint
sums or bound them before narrowing; an 8-bit ADD then SRA overflows for some
valid signed coordinates. Define rounding at each node and bound propagated
error after projection. Reuse [fixed-point rules](arithmetic.md#fixed-point-and-reduced-precision)
for products, negation and narrowing. Validate the whole angle/animation cycle,
near-plane denominators and final pixel error against direct transforms.
Reject if topology or precision cannot satisfy the visible contract; keep
independent transforms. This does not supply clipping or a polygon rasterizer.

## Bound The Complete Texture Walk

Declare sample domain, dimensions, stride, alignment, wrapping and bank mapping.
`INC L` never carries into H: page alignment makes that behavior match a circular
256-byte texture row; it does not make arbitrary rows safe. An H step can leave
a multi-page texture midway through a scanline even if H was masked at row entry.

Prove every intermediate read for every supported angle, scale and row start.
Use explicit wrapping, duplicated guard rows, bounded start margins or another
layout when needed; count padding and extra traffic. Also bound the final live
pointer. Clip logical coordinates before converting them to addresses. A clipped
sample's sink must be explicitly owned scratch storage, not a presumed free
address. Address-only dot streams cannot express an arbitrary changing bit index;
fixed SET-bit kernels need matching phases, masks or separately selected kernels.

Reject a page-only shortcut without the complete trajectory proof. Fall back to
bounded 16-bit addressing or per-sample wrap. Compare seams and all guard regions
with an independent sampling oracle, then exercise the assembled implementation.

## Count Output, Replication And Symmetry Separately

Keep source samples, unique packed bytes, physical screen writes and attribute
writes in separate units. A full physical 256x192 display at 2x2 chunks has
128x96 samples and 32x96 = 3,072 unique packed bytes. Duplicating each row writes
6,144 bitmap bytes; the replication/transfer is additional work. A logical tile
ring or edge-column update does not shift unchanged interior pixels on a classic
Spectrum; see [incremental scrolling](zx-spectrum-hardware.md#incremental-redraw-and-scrolling).

Symmetry reduces expensive evaluation only when the effect is symmetric. Charge
quarter-domain evaluation plus all four destination writes, address generation,
mirroring, transfer and asymmetric overlays. It is not automatically four times
faster. Reject if copy/bookkeeping or lost artistic freedom outweighs saved math;
direct evaluation is the fallback. Compare the complete image and full-call cost,
including center seams, odd dimensions and overlays.

## SP Address Streams And RET-Threaded Worklists

A POP address stream retrieves a two-byte target and advances SP in nominal 10 T.
A RET-threaded list instead places handler addresses on that stream; each RET
consumes the next address into PC in nominal 10 T. Neither is free dispatch:
include list construction, entry/terminal handling, handler work and SP restoration
when comparing with ordinary calls or an explicit pointer/jump-table loop.

This is DANGEROUS control flow. Prove target bounds, bank visibility, register/flag
handoffs, consumed words and a terminal handler that restores the real stack
before returning to the original caller. Protect list ownership from concurrent
mutation. Ordinary CALL/PUSH/POP/RET operations need an explicit scratch/stack
contract so they neither overwrite pending targets nor consume list entries.
Use the canonical stack/ISR gates above; DI alone does not exclude NMI.

Reject if any target, terminal path, interrupt window or ABI boundary is unproved.
An explicit read pointer plus indirect dispatch is the fallback. Trace empty,
single-item, maximum-size, invalidated-bank and interrupted paths; guard both the
real stack and worklist. Nominal instruction counts do not prove raster safety.

## Paging Must Preserve Simultaneous Visibility

On ordinary 128K Spectrum paging, graphics in one bank and a back screen in bank 7
cannot both occupy the single `C000-FFFF` window. Stage bounded data in fixed RAM,
place both resources in an available visible layout, or change the schedule;
include staging and page changes in cost. The same applies to decoder source and
destination. Display-page selection does not remap bank 7 to `4000`. Reserve screen
storage by address and lifetime before reusing the rest of that physical bank.

If mainline and ISR both page, the latch shadow and hardware OUT need one coherent
ownership transaction, serialized from the initial shadow read through the OUT;
masking only the final write can leave a stale read/modify/write. An ISR between
updates must not observe/restore a mismatched mapping. If an ISR temporarily
pages a player without updating the foreground shadow, prove restoration on
every exit and that nested paths do not treat the shadow as the instantaneous
hardware map. Reuse the project's helper and preserve its interrupt contract;
an unconditional EI is unsuitable for callers requiring interrupts disabled.
Keep every switching helper and its continuation, stack, vector read, workspace
and patched operand valid, not only ISR entry. A resident trampoline must restore
the caller's bank before returning to a banked return address. Apply
[page history/flip rules](zx-spectrum-hardware.md#page-local-history-and-screen-flipping).

Reject unproved aliases or interrupted transactions; fixed-memory staging or the
existing renderer is the fallback. Trace all source/destination/music mappings,
inject IRQ at latch-update boundaries and check guards. Pin the machine model.

## Evidence And Sources

Host arithmetic/image models prove only their stated representation. Generated
output still needs listing/map inspection, assembled semantic checks, complete
call timing and deployed-model ISR/paging validation. Full line/polygon rasterizers
and Next DMA/hardware-sprite recipes remain outside this reference.

Discovery sources at the reviewed revision: [sampling/code generation](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch06-sphere/draft.md#L25-L145),
[affine basis](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch05-3d/draft.md#L34-L188),
[gather/symmetry](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch09-tunnels/draft.md#L78-L145),
and [RET worklists](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch03-demoscene-toolbox/draft.md#L361-L423).
These inspire original guidance, not copied implementations or accepted upstream
timings; read the [source assessment](../../audit-z80/references/antique-toy-review.md).
