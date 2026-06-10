# Forum Gems Audit Pass

Use this file when the user asks for forum-mined, underground, demoscene, or "old master" Z80 review. Public forum posts are idea generators, not evidence. A forum trick becomes a finding only after local proof: exact file/line, build target, ABI, flags, stack state, timing contract, and hardware model.

## Audit surfaces mined from forums

- Active object lists: if code scans every enemy/bullet slot every frame, check whether dead/inactive records can still affect collision, draw order, timers, AI, or spawn reuse. If an active-list exists, prove add/remove paths stay balanced on death, respawn, room change, and level reset.
- Page-local tables: patterns like `ld h,table/256` plus `ld l,index`, `inc l`, or byte offsets need linker/alignment proof. One page crossing can silently corrupt sprite, mask, sine, or dispatch reads.
- Compiled sprites and generated draw code: audit clipping exits, transparent vs opaque paths, screen wrap, modified opcodes, per-scanline skip tables, and whether code copied/generated in RAM can execute on the target.
- Stack-fed screen code: `ld sp,table_or_screen`, `pop de`, `push hl/de/bc`, or `add hl,sp` are not automatic bugs, but every exit must restore SP and prove interrupts, NMI, ROM calls, and C callers cannot observe the temporary stack.
- Timing pads and cycle-equalized output: `nop`, `push/pop` delay pairs, unrolled `out`, and branchless bit output may be required for audio, loaders, rasters, or VDP/ULA pacing. Do not "optimize" them until the timing budget is identified.
- Shadow registers: forum routines often use `exx` to win cycles. Prove ISR, ROM, BIOS, and inline C conventions do not also use alternate registers.
- Self-modifying opcode patches: common for compiled sprites, output streams, jump vectors, and skip tables. Check RAM residency, bank/overlay lifetime, assembler relocation, cache-free CPU assumption, and atomicity with interrupts.
- Data-layout inversion: if code spends cycles walking around a structure, check whether the data was deliberately arranged for another consumer. A bug can be in the data contract, not the instructions.
- Packed mask/sprite streams: interleaving mask and bitmap can remove a second pointer, but mismatched lengths or stale asset tooling create off-by-one corruption that normal source review misses.
- R register use: `ld a,r` can be a cheap counter/noise source, not real entropy. Audit determinism requirements, emulator behavior, interrupt influence, and whether repeated calls become visibly patterned.
- C/ASM mixed functions: SDCC/z88dk forum advice repeatedly warns that inline asm inside C can invalidate compiler assumptions. Check generated `.lst/.asm`, IX/frame pointer use, parameter convention version, and return register.
- Port I/O and VDP/ULA waits: optimizers can delete what looks like dead delay. Check port decode, high-byte assumptions, VDP busy timing, contention, loader handshakes, and exact output cadence.
- Hardware sprite tables or software sprite mirrors: many systems update a RAM shadow then copy once per frame. Audit stale terminators, per-scanline overflow limits, hidden sprite Y values, and emulator-only assumptions.
- Undocumented flags/opcodes: `SLL`, `IXH/IXL`, `IYH/IYL`, `BIT (IX+d)` flag behavior, `LD A,I/R` P/V, and repeated block flags can be intentional compatibility contracts.
- IM 2 tables: Spectrum-style 257-byte tables, floating bus byte assumptions, and `FFFF` jump tricks require exact model proof. Do not generalize across Spectrum/CPC/MSX/SMS/TI.

## Review checklist

- Find the frame loop, ISR, loader, screen writer, input poller, and C/ASM boundary before judging local routines.
- For each clever sequence, write the invariant it relies on: page, SP, DI span, flags, register set, target machine, and asset layout.
- For UX-visible code, treat flicker, sprite half-draw, missed input, audio jitter, text redraw stalls, and corrupt attributes as correctness defects.
- If a scanner reports timing pads, stack blitters, page-local indexing, or dynamic dispatch, inspect neighboring code and comments before classifying severity.

## Forum/source trail

- CPCWiki compiled sprites thread: stack pointer as line-skip table, `INC L`, screen wrap, compiled sprite clipping, and SMC line-skip patches. https://www.cpcwiki.eu/forum/programming/compiled-sprites/
- CPCWiki fast sprites notes: 32-char screen width, page-boundary avoidance, solid vs transparent sprite split, and IX/IY/PUSH/POP cautions. https://www.cpcwiki.eu/index.php/Programming%3AFast_Sprites
- MSX.org C/SDCC optimization thread: byte types, static/global vs stack locals, `__sfr`, `__at`, `__z88dk_fastcall`, avoiding tiny function overhead, and dirty text redraw. https://msx.org/forum/msx-talk/development/about-c-z80-optimizations-sdcc
- MSX.org SDCC/ASM threads: `__naked`, `jp (hl)` wrappers, SDCC 4.1.12+ register calling convention, IX frame-pointer caveats, exported ASM symbols. https://www.msx.org/forum/msx-talk/development/using-sdcc-and-assembly and https://www.msx.org/forum/msx-talk/development/sdcc-4112-a-game-changer-for-c-programming
- SMS Power PDM optimization challenge: constant bit cadence, branchless output, generated sample code, double buffering, and SMC `out` opcode ideas. https://www.smspower.org/forums/15875-PDMAkaPWMCodeOptimisationChallenge
- SMS Power Z80 programming techniques: unrolled block I/O, shadow registers for interrupts, table alignment, conditional RST, fall-through loops, and block-instruction caveats. https://www.smspower.org/Development/Z80ProgrammingTechniques
- SMS Power sprite programming thread: RAM sprite-table shadow, end terminator, scanline sprite overflow, and emulator mismatch risks. https://www.smspower.org/forums/9623-SpriteProgramming
- Cemetech random optimizations and useful routines: data reordering, zero-store idioms, IX tradeoffs, interleaved mask/sprite data, shadow-register sprite code, and R-register PRNG. https://www.cemetech.net/forum/viewtopic.php?start=0&t=10416 and https://www.cemetech.net/forum/viewtopic.php?start=140&t=1449
- Cemetech common mistakes archive: overusing IX/IY, tiny `call`/`ret` helpers, IY under interrupts, and assembler directive/string pitfalls. https://www.cemetech.net/projects/uti/viewtopic.php?start=0&t=8461
- World of Spectrum Z80 reference: undocumented flags/opcodes, R register behavior, `LD A,I/R`, IM 2 table quirks, and repeated block interruptibility. https://worldofspectrum.org/faq/reference/z80reference.htm
- AtariAge MDL optimizer thread: peephole tools are candidate generators; some suggestions are correct but risky, especially `call; ret` rewrites and SDCC dialect handling. https://forums.atariage.com/topic/309783-optimizer-for-z80-assembly/
- ZX-PK z88dk/C threads: compiler flags, `--reserve-regs-iy`, max allocator settings, globals/statics for performance, and code-size tradeoffs across sccz80/SDCC. https://zx-pk.ru/threads/6844-ishchu-si-dlya-z80/page19.html
