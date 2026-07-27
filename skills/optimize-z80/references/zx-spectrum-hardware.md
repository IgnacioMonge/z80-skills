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

## Screen Layout

ZX bitmap layout is interleaved. Avoid full address recomputation in hot paths.

Safe optimizations:

- screen address tables
- `inc h` vertical step inside 8-line char block
- row/third lookup
- dirty square/dirty rectangle redraw
- attribute-only update when pixels unchanged

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

## Floating Bus

Floating bus reads ULA bus values through unattached ports. It can sync to raster position on compatible machines.

Use only when:

- visual stability/timing is the bottleneck
- target model supports the trick
- code runs from non-contended memory if timing matters
- fallback or model restriction is acceptable

Reject for normal UI/game optimization unless tearing/raster timing is proven.

## 128K / Paging

Check:

- bank switch cost
- double-buffer via screen pages
- assets in banks vs resident pressure
- code/data ownership across banks
- interrupt code visibility across banks

Do not propose bank tricks for 48K-only projects.
