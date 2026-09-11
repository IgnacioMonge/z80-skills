# ZX Spectrum Hardware

Use this reference for Spectrum targets. For non-Spectrum Z80, load only the general Z80 technique files. For model-specific timing or paging claims, also load `zx-spectrum-models.md`.

## Contention

48K contended RAM is 0x4000-0x7fff. The ULA steals cycles while drawing the display. Timing-critical code/data should prefer uncontended RAM when possible.

Questions:

- Does hot code execute from contended RAM?
- Does the stack sit in contended RAM during heavy PUSH/POP?
- Are screen writes scheduled during visible display?
- Is the program relying on `HALT`/frame waits?
- Does the claim need machine-specific timing rather than a general contention warning?

For actual scheduling budgets, use
[frame-window planning](zx-spectrum-models.md#frame-window-planning).

## Screen Layout

ZX bitmap layout is interleaved. Avoid full address recomputation in hot paths.

Safe optimizations:

- screen address tables
- `inc h` vertical step inside 8-line char block
- row/third lookup
- dirty square/dirty rectangle redraw
- attribute-only update when pixels unchanged

### DOWN_HL across character rows and thirds

For the classic bitmap, HL points to byte column x (0-31), pixel row y
(0-190). The next scanline is not generally `HL+32` or `INC H` alone.
Implement the complete step in the project's existing screen helper:

1. Increment H. If `H & 7` is nonzero, finish (same eight-line block).
2. Add 32 to L as an eight-bit value. If that addition carries, finish
   (the next 64-line third is already selected by H).
3. Otherwise subtract 8 from H (next character row within the same third).

The input excludes y=191: the caller must clip or stop before leaving the
bitmap. Track A/flags clobbers in the chosen ASM lowering. This also applies
to a banked screen mapped at $C000, provided the mapping stays stable.
Validate all 191*32 transitions against the independent address formula
`base | ((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2) | x`,
especially 7->8, 63->64 and 127->128. Compare the helper's branch costs with
a row table or compiled sprite before choosing one; neither is always smaller
or faster. This step is derived from the classic interleaved bitmap layout.

Runnable reference check (Python 3, not a target implementation):

```python
def address(base, y, x):
    return base | ((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2) | x

for base in (0x4000, 0xC000):
    for y in range(191):
        for x in range(32):
            h, l = divmod(address(base, y, x), 256)
            h += 1
            if h & 7 == 0:
                total = l + 32
                l = total & 255
                if total < 256:
                    h -= 8
            assert (h << 8) | l == address(base, y + 1, x)
```

## Rendering Lanes

SAFE:
- dirty redraw
- attribute-only updates
- precomputed screen addresses
- aligned row tables
- avoid redundant redraws

MEDIUM:
- compiled sprites
- partial unroll
- layout-specific ASM helpers
- offscreen buffer strategy
- generated masks/tables

DANGEROUS:
- SP blitting into screen
- racing the beam
- floating bus sync
- raster/multicolor timing

## Sprite And Redraw Specialization

MEDIUM candidates for measured render work. Preserve clipping, compositing
order, attributes and model timing; the generic renderer is the fallback.
The costs below are representation calculations, not measured frame savings.

### Preshifted sprites or shared shift tables

Store only the horizontal phases the movement contract permits. For width W
pixels, height H, phases S and P byte planes (image plus mask when used),
storage without metadata is `H*P*sum(ceil((W+s)/8) for s in S)`. Include spill
columns: a tightly stored 16x16 image at all eight phases takes 368 bytes,
or 736 with a mask, before alignment. It is not simply eight times 32 bytes.
Selection/copy costs replace runtime shifting; frame count multiplies storage.
Do not reduce movement precision just to discard phases without product approval.

A shared byte-shift table amortizes storage across many sprites but adds
lookups and merging. SP1 provides a concrete example: seven 512-byte tables
for shifts 1..7 (3584 bytes). Reuse an existing engine's format and initialization
contract before inventing one. Source: [SP1 rotation tables](https://www.z88dk.org/wiki/doku.php?id=libnew:examples:sp1_ex1).
Validate each phase against a pixel reference, including spill columns, masks,
edge clipping and the last animation frame. Choose runtime shifts when the
table/phase cost exceeds RAM or asset-loading budgets.

### Transparent, opaque and mixed spans

For `out=(background & mask) | image`, require `image & mask == 0` if the
format uses complementary image/mask planes. A transparent byte (mask=$FF,
image=0) needs no screen access; an opaque byte (mask=0) needs no background
read; only mixed bytes require merging. Preclassify runs offline or compile
them into specialized code instead of testing every byte at runtime.
Address stepping and run metadata still cost time/bytes. Mutable sprite data
can invalidate the classification. Test all byte classes against the generic
compositor, plus overlapping sprites and clipped spans. Keep generic drawing
for irregular assets whose metadata or code expansion does not amortize.

### Compiled sprites

Generate immediate stores, masks and skips for fixed artwork. This removes
data decoding and repeated decisions at the cost of executable bytes per
shape/phase and possibly patched addresses. Count generator output, alignment,
bank transfers and clipped variants as well as the inner body. RAM-patched
variants inherit SMC/ISR rules; code in ROM needs another addressing strategy.
Verify generated output pixel-for-pixel against the existing renderer for all
positions and phases. Use data-driven spans when code growth or clipping
complexity outweighs throughput. This is specialization of the compositor
above, not a universally faster sprite format.

### Incremental redraw and scrolling

Dirty redraw must include both old and new object bounds, then redraw every
layer intersecting the affected cells. Background save/restore requires enough
storage and correct overlap order; stale saved pixels cannot restore a scene
changed by another object. Scrolling can update exposed strips instead of
regenerating the scene, but count the retained-area move, wrap, attributes and
new strip generation. A logical tile-ring does not eliminate physical screen
writes on the classic Spectrum. Test moving overlaps, disappearance, camera
jumps and full-screen invalidation. Fall back to full redraw above the measured
dirty-coverage crossover; bookkeeping can dominate dense changes.

## Floating Bus

Floating bus reads ULA bus values through unattached ports. It can sync to raster position on compatible machines.

Use only when:

- visual stability/timing is the bottleneck
- target model supports the trick
- code runs from non-contended memory if timing matters
- fallback or model restriction is acceptable

Reject for normal UI/game optimization unless tearing/raster timing is proven.

`IN A,($FF)` samples display data or idle $FF on compatible machines, not
a raster counter. Previous A supplies the high port byte, affecting contention.
[48K hardware observations](https://worldofspectrum.org/faq/reference/48kreference.htm)
describe this behavior; [+2A/+3 do not provide the classic $FF-port signal](https://worldofspectrum.org/faq/reference/128kreference.htm).

For sync without HALT, reserve a known bitmap/attribute marker, poll its
expected bus transition within a bounded acquisition window, then apply a
measured model-specific delay. Reset the port's high byte deliberately before
each immediate IN. Prove marker uniqueness and sampling cadence across frame
phases; a missed marker must time out to a fallback. Screen edits, peripherals
and paging can invalidate the signal. Count the entire poll loop and interrupt
jitter; an unbounded `wait until A != $FF` loop is not a reliable raster lock.

## 128K / Paging

Check:

- bank switch cost
- double-buffer via screen pages
- assets in banks vs resident pressure
- code/data ownership across banks
- interrupt code visibility across banks

Do not propose bank tricks for 48K-only projects.
