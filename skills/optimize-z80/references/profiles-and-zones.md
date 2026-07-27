# Profiles And Zones

The optimizer must adapt to the project. Never assume a game, a demo, or Shatranj-like architecture.

## Target Guardrail

Target determines which hardware assumptions are legal.

- `unknown` or `pure-z80`: reject Spectrum-only claims such as ULA contention, border timing, attributes, floating bus, esxDOS, or 48K screen layout unless source/artifacts prove them.
- `zx-spectrum`: load `zx-spectrum-hardware.md`; contention, screen layout, border timing, and esxDOS may be relevant.
- `msx`, `cpc`, `cpm`, `rc2014`, `next`: use core Z80 techniques unless a target-specific artifact proves otherwise.
- Policy `forbidden` entries are hard vetoes. Do not recommend a vetoed lane as an experiment.

## Profiles

48k-game:
- pressures: resident size, frame budget, contention, stack/RAM, screen writes
- likely zones: render, sprites, game loop, input, audio, compression

128k-game:
- pressures: bank switching, asset placement, screen flipping, paging discipline
- likely zones: banking, render, decompression, loading, memory layout, AY audio

network-app:
- pressures: UART polling, waits, protocol parser, buffers, reconnect, UI responsiveness
- likely zones: transport, parser, frame wait, background drain, state machine

text-ui-tool:
- pressures: string/data size, font rendering, dirty rectangles, input latency
- likely zones: UI strings, text renderer, menus, buffers

graphics-heavy:
- pressures: sprite blit, screen address math, attributes, contention, frame budget
- likely zones: render, sprites, tables, screen layout, generated assets

demoscene-intro:
- pressures: size first, hardware timing, procedural generation, code=data
- likely zones: sizecoding, SMC, floating bus, undocumented opcodes, compression, audio players

c-heavy-z88dk-sdcc:
- pressures: codegen, lib pulls, stack spills, calling convention, generated asm
- likely zones: C helpers, runtime, standard library, ABI boundaries

asm-heavy:
- pressures: register allocation, branch flow, tables, instruction timing, maintainability
- likely zones: ASM hot loops, screen, math, data movement

mixed-c-asm-overlays:
- pressures: resident/overlay split, ABI, call overhead, thrash, fixed slots
- likely zones: overlays, dispatcher, C-to-ASM, map sizes, ABI guards

## Profile Policy Matrix

48k-game:
- first moves: resident budget, frame/render evidence, data layout, dirty redraw, contention if Spectrum
- allow: SAFE and measured MEDIUM
- reject: code=data, opcode SMC, undocumented opcodes in release builds

128k-game:
- first moves: bank layout, asset placement, paging frequency, duplicated bank state
- allow: SAFE, MEDIUM banking/layout changes with fresh maps
- reject: nested banking assumptions without call graph and bank validation

network-app:
- first moves: waits, retry cadence, duplicate init, background drain, parser copies
- allow: SAFE I/O/state fixes, measured parser ASM
- reject: CPU peepholes as primary fix while I/O/wait dominates

text-ui-tool:
- first moves: strings, font renderer, dirty rectangles, input latency
- allow: SAFE data/layout and measured C-to-ASM kernels
- reject: hardware timing and dangerous lanes unless policy says disposable/sizecoding

graphics-heavy:
- first moves: redundant writes, screen layout, tables, contention, generated assets
- allow: compiled sprites, unrolled kernels, measured blitters
- reject: SP blit/floating bus unless target and validation allow

demoscene-intro:
- first moves: size budget, procedural data, shared tails, fallthrough, SMC immediates
- allow: DANGEROUS lanes with explicit target and validation path
- reject: maintainability objections only if policy is release/normal rather than sizecoding

c-heavy-z88dk-sdcc:
- first moves: lib pulls, wide math, stack spills, calling convention, generated ASM
- allow: compiler flags, fastcall/callee, small ASM kernels
- reject: hand ASM if bottleneck is algorithm, I/O, or overlay layout

asm-heavy:
- first moves: branch flow, register allocation, data movement, dispatch, table layout
- allow: SAFE/MEDIUM core techniques, DANGEROUS only in isolated kernels
- reject: undocumented/SMC/SP if policy forbids or ISR boundary is unclear

mixed-c-asm-overlays:
- first moves: resident/overlay split, fixed slot occupancy, ABI guards, load frequency, state duplication
- allow: hot/cold split, dispatcher cleanup, measured overlay packing
- reject: micro-peepholes before slot pressure and thrash are measured

## Zone Map Template

For each active zone, fill:

- zone:
- files/artifacts:
- current pressure:
- evidence:
- likely technique lanes:
- risk boundary:
- validation path:

## Zone Technique Matrix

render/screen:
- SAFE: dirty redraw, address tables, branch ordering, remove redundant writes
- MEDIUM: compiled sprites, unroll, layout-specific ASM
- DANGEROUS: SP blit, floating bus, racing beam

sprites/assets:
- SAFE: dedup frames, pack masks, generated tables, palette/attribute review
- MEDIUM: compiled sprites, RLE, offline codegen
- DANGEROUS: code=data, self-modifying sprite code without tests

parser/protocol:
- SAFE: byte-state machine, branch common cases, remove copies, bound checks
- MEDIUM: ASM scanner, table dispatch
- DANGEROUS: SMC parser unless sizecoding profile

transport/I/O:
- SAFE: remove fixed waits, avoid duplicate commands, improve polling cadence
- MEDIUM: ring buffers, interrupt mode if project accepts complexity
- DANGEROUS: timing assumptions without hardware proof

math/rules/AI:
- SAFE: algorithmic pruning, tables, 8-bit narrowing
- MEDIUM: C-to-ASM hot primitives, fixed multiply/divide tricks
- DANGEROUS: opaque arithmetic hacks without reference tests

audio/music:
- SAFE: precomputed tone/frequency tables, compact event encoding, remove per-frame recompute
- MEDIUM: optimized player inner loops, AY register batching, pattern compression
- DANGEROUS: cycle-exact PWM/border audio, interrupt/shared-register tricks

compression/decompression:
- SAFE: RLE for repeated graphics/tables, offline packing, decode only off hot path
- MEDIUM: custom small LZ/RLE decoder, Exomizer/APLib-style workflow if decoder budget fits
- DANGEROUS: code=data or self-modifying decompressors in maintainable apps

overlays/banking:
- SAFE: hot/cold split, avoid thrash, map analysis
- MEDIUM: dispatcher redesign, banked assets
- DANGEROUS: nested overlay assumptions, state hidden in banked memory

toolchain/runtime:
- SAFE: remove lib pulls, compiler flags, fastcall where ABI allows
- MEDIUM: peephole copt, MDL cross-check, custom runtime stubs
- DANGEROUS: changing CRT/startup without full boot tests

## Profile Selection Signals

Use file names only as weak hints. Prefer content and artifact signals:

- `out (0xfe)`, border timing, floating bus reads, IM 2 tables, raster waits -> hardware-timing or demoscene/graphics profile.
- screen address math, sprite tables, attributes, dirty rectangles -> render/graphics/game profile.
- AY register writes or music player labels -> audio/music zone.
- UART, ESP-AT, esxDOS, tape/disk wait loops -> transport/I/O or tool profile.
- `+zx`, z88dk CRT/clib, SDCC dumps, z80asm maps -> C-heavy/toolchain profile.
- fixed 2K/4K/8K banks, overlay slots, trampolines -> overlay/banking profile.
- no real-time loop, batch file/data transforms -> tool/utility profile; prioritize algorithm, I/O, and reliability over raster tricks.

If profile is ambiguous, emit a mixed profile and score candidates by active zones, not by project label.
