# Size Playbook Extended (Z80 / Spectrum / demoscene)

Idea bank only. Every item is a **search seed**. Promote only with
`hard-contract.md` proof against **current** project source/artifacts.

Use after the safe attack order (`arch` -> `libpull` -> `deadcode/refactor` ->
`data` -> `micro` -> `dedup`). For black-belt, combine with
`size-blackbook.md`; use `external-research.md` only for evidence-selected
questions. Mark `EXPERIMENTAL` where noted.

## A. Resident vs banked accounting (128K / Next / overlays)

- Count **resident low-RAM** separately from **paged banks**. A 2 KB win in a
  bank that is never co-resident with the tight bank is not a win for the
  pressure target that actually fails.
- Prefer moving cold code (menus, loaders, debug, level compilers) into banks
  or overlays; keep ISR, bank-switch stubs, and hot draw paths resident.
- divMMC/esxDOS and +3DOS can shadow low memory: any ROM-pool or fixed-address
  trick must state the paging window where it is valid.
- Spectrum Next: separate **classic Z80** path from **Z80N** path. Do not claim
  a Next-only opcode saving on a 48K target in a multi-target project.

## B. CRT / startup / .dot / esxDOS footprint

- Wrong `-startup` / CRT often costs more than any micro pass. Measure CRT and
  library chunks from the `.map` before rewriting gameplay code.
- Dot-commands and small esxDOS tools: treat **total resident ceiling** as the
  product metric; prefer `__z88dk_fastcall` / naked ASM leaves, no `printf`,
  no malloc, minimal FILE plumbing.
- Custom `crt0` that drops unused RST handlers, stream init, or heap can beat
  months of micro-optimizing game code — only with target proof.

## C. IM2 and interrupt table cost

- Full IM2 vector page is a classic **257-byte** (or 256+1) tax. Alternatives:
  single-byte fill page + one ISR pointer pattern; share vector page with other
  aligned data when hardware allows; IM1 + patch if timing allows.
- Shadow registers: document **owner** (main vs ISR). Free `exx` storage is not
  free if the ISR already claimed it.
- Frame ISR that only sets a flag + bottom-half work can delete duplicated
  poll code across modules (arch win, not micro).

## D. Display file, attributes, and render size

- Spectrum bitmap H-increment / third-block layout: a correct `next_line` of a
  few bytes can delete large address tables; wrong next-line rewrites are
  regressions — prove against current draw loops.
- Attribute-plane design: solid rows, pre-striped attrs, clash-as-style, and
  attr-only animations often remove bitmap data and draw code together.
- Half-buffer / row-buffer / tile-cache: trade 256-2048 B of RAM for deleting
  general clippers; count **net** CODE+BSS.
- Dirty rectangles / tile stamps / name-table indirection: usually beat
  full-screen clears; require current frame-loop evidence.
- Compiled sprites and stack blitters: already in forum/external docs; always net
  decoder/clip fallback/SP+DI proof on **this** renderer.
- Timex hi-res / Next layer2 / ULA+ layer modes: different size tradeoffs —
  do not port 48K screen tricks blindly.

## E. Z80N (Spectrum Next) size surface

When the target matrix includes Next and policy allows Z80N:

- `mul de` can delete software multiply helpers (map-check libpull first).
- `push imm` / compact load forms can shrink init tables and prologue noise.
- DMA / copper / layer2 blits move work out of CPU code — count **driver**
  bytes and bank setup, not only the removed CPU loop.
- Keep a **classic fallback** size for multi-target; Next-only wins must not
  bust 48K ceilings (multi-target gate).

## F. Compression and asset pipelines (net accounting)

- Codecs to compare when tooling exists: ZX0, ZX7, LZSA, aPLib, Exomizer,
  megaLZ, Bitfire-style streaming. Prefer what the **project already ships**.
- Net_storage = original - (packed + decoder share + call glue).
  Report exclusive workspace/stack separately as RAM_peak_delta; never fold
  storage and peak-RAM domains or report packed size alone.
- In-place decompress into screen or into a buffer that becomes gameplay RAM
  (self-destructing load) is often the real win.
- Shared decoder for many assets beats per-asset micro-formats.
- Token/bytecode for UI, cutscenes, enemy scripts, and level events: count
  interpreter once; reject if only 1-2 streams exist.
- Generate assets at build time (PC tools) rather than shipping general
  runtime editors/packers.

## G. Math, tables, and generative data

- Quarter-wave / symmetric sine, delta maps, nibble pair packing, mirrored
  tiles, procedural fonts (3x5, 4x8) vs full 768 B ROM font copy.
- Strength reduction catalog: x3/5/6/10/20 via shifts+adds; replace `%` power
  of two with masks; avoid SDCC helper pulls (`__mulint`, `__divuint`, etc.).
- Bresenham / DDA shared between line, ray, and slide-move paths.
- ROM calculator (Spectrum) is usually a size **loss** except rare cases; treat
  as REJECTED_TRAP unless map shows it already linked and shared.

## H. Control-flow and dispatch density

- `call foo; ret` -> `jp foo`; shared tails; fall-through state machines.
- Relative offset tables (1 byte) vs absolute vectors (2 bytes) inside a page.
- Stack dispatch (`push hl; ret`) vs `jp (hl)` under register pressure.
- Sparse `switch`: SDCC tables can be worse than explicit cascades — inspect
  **generated** ASM of the current build, not source aesthetics.
- RST amortization only when vector ownership is free on **all** targets.

## I. Memory lifetime and overlay of buffers

- Union lifetimes: screen during load, unpack window, music buffer, level
  scratch — one region, many phases (extends self-destructing init).
- Printer buffer / UDG / sysvar gaps as temporary tables only with ownership
  proof and esxDOS safety.
- Stack as scratch for leaf decode (with DI if needed) vs BSS permanence.

## J. Sound engines (size lens)

- Beeper engines vs AY players: data format dominates; strip unused effects
  channels and multi-song drivers when product uses one track.
- Do not pull a full tracker runtime for three hard-coded SFX; specialize.

## K. 256B / 4K intro techniques that transfer to games

- Generate geometry/text from tiny seeds instead of storing frames.
- Reuse ROM character set + few custom UDGs.
- Palette/attr cycling instead of unique bitmaps.
- One generic "plot column/span" instead of many sprite sizes — only when
  current art fits the restriction.
- These are often `AGGRESSIVE` for product code; keep after SAFE arch/data wins.

## L. C / SDCC / z88dk size levers (beyond c-patterns.md)

- `__z88dk_callee` vs caller cleanup: measure **all** callsites.
- `__naked` + hand ASM for leaves that SDCC ruins with IX frame.
- Section attributes and `-pragma-redirect` to drop unused stdio pieces.
- `--max-allocs-per-node` and `--opt-code-size` can change helper selection —
  re-preflight after flag changes; do not mix flag experiments with code edits
  in one candidate.
- `sizeof("lit")` materialization trap (see c-patterns.md).

## M. Anti-patterns (size folklore)

- Replacing working `ldir` with clever SP loops for **bytes** without DI/SP
  proof (often larger after safety glue).
- Shipping both a general clipper and per-sprite special cases "temporarily".
- Keeping debug `printf` paths compiled into release maps.
- Counting decoder-less "RLE" that still needs a unique unpacker per asset.
- Using undocumented opcodes on a support matrix that includes strict
  emulators or non-Z80N cores without opt-in.

## N. Coverage checklist (black-belt / full scan add-on)

When `scan` or `blackbelt` runs, state `found` / `none` / `n/a` for:

- resident vs banked split
- CRT/startup/.dot ceiling
- IM2/vector page cost
- display next-line / attr strategy
- Z80N conditional wins (if Next in matrix)
- compression net chain
- generative/mirrored/packed tables
- buffer lifetime overlays
- sound driver specialization
- SDCC callsite-wide convention math

Silence on these after a broad scan usually means the pass was shallow.

## External research cross-link

For codec choice, IM2/ROM, display/banking, decoder consolidation, or obscure
toolchain behavior, follow the bounded discovery and transfer rules in
`external-research.md`.
