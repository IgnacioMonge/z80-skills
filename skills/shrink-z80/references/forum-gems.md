# Forum Gems Shrink Pass

Use this file when the user asks for forum-mined, demoscene, "black magic", or old-game-programmer Z80 size work. These tricks are candidates only. A candidate becomes a saving after local byte count, branch-range proof, ABI proof, flag/register/stack proof, and rebuild measurement when needed.

## High-yield forum patterns

- Active lists over slot scans: replace full enemy/bullet scans with compact active lists, phase lists, or draw queues when inactive records dominate. Count add/remove code and failure recovery.
- Byte offsets over pointers: if a table fits one page, store low bytes or offsets and keep the high byte in a register. Requires linker alignment; padding may still be cheaper than 2-byte pointers.
- Page-local drawing: screen or sprite rows arranged to allow `inc l`/`dec l` can delete 16-bit address math. Only safe while no row crosses a 256-byte boundary.
- Compiled sprites: generate per-sprite draw code for fixed shapes, common bytes, masks, or line skips. Net count must include generated code, fallback clipped routine, asset duplication, and patch setup.
- Stack line-skip tables: set `SP` to an offset table and `pop de/add hl,de` for next-line addressing. Good for speed and sometimes bytes; costs SP-save/restore and DI discipline.
- SMC line-skip patches: patch `add hl,de` into `add hl,bc` or `add hl,sp` at selected scanlines instead of carrying branchy wrap logic in every line.
- Interleaved mask+sprite data: store mask and sprite bytes in consumption order to remove a second pointer and shadow-register pressure.
- Solid/transparent split: route opaque sprites/tiles through `LDI`/direct stores and reserve mask code only for transparent zones.
- Timing-as-data: for PDM/audio/loaders, preprocess data so the player has constant cadence, or generate output code for fixed chunks. Count ROM/RAM cost and bank-change padding.
- Unrolled block I/O/copy: repeated `outi`/`ldi` blocks can beat `otir`/`ldir` for speed and can be entered at an offset. For shrink, count whether one shared unrolled block replaces many local loops.
- Token/event streams: pack repeated commands into bytes or nibbles with a tiny interpreter when many call sites share grammar.
- RST/call vectors: many calls to hot helpers may justify `rst` vectors, a jump table, or a shared dispatch bytecode. Count vector table and target-machine ROM/RST ownership.
- Dirty redraw: do not redraw text, scoreboards, menus, attributes, or sprite shadows when unchanged. Saves both code paths and frame stalls when paired with state flags.
- Data-order inversion: store map rows, sprite spans, protocol fields, or UI strings in exact consumption order so code becomes `ldi`, `inc l`, or fall-through.
- C calling convention wins: on modern SDCC, register calling can remove stack setup. For z88dk/SDCC, tiny hot functions often become smaller as `__naked`, `__z88dk_fastcall`, `__sdcccall(1)`, or hand-coded ASM.
- C type narrowing: `uint8_t` counters, unsigned countdown loops, `__sfr`, and `__at` hardware/system variables can delete stack, helper calls, and repeated address loads.
- Avoid false size wins: forum optimizer tools may suggest valid peepholes that delete timing waits, change flags, or break assembler dialects. Keep them in `Rejected ideas` unless proof is complete.

## Required black-belt questions

- Can data alignment buy more bytes than local instruction swaps?
- Can generated code remove a general routine and its metadata?
- Can an active list or dirty flag delete whole per-frame scans?
- Can mask/sprite/map data be reordered to eliminate pointer math?
- Can a shared unrolled block, RST vector, or token interpreter amortize repeated helpers?
- Is the current C compiler being used with flags/calling conventions that match the code shape?
- Which clever candidates failed because of SP, DI/EI, flags, bank/ROM placement, clipping, or timing?

## Forum/source trail

- CPCWiki compiled sprites thread: SP-fed line tables, `INC L`, compiled sprite code, clipping fallback, SMC scanline patches, and compression/map-buffer tradeoffs. https://www.cpcwiki.eu/forum/programming/compiled-sprites/
- CPCWiki fast sprites notes: 32-char width/page alignment, solid sprite split, `LDI`, avoiding IX/IY and PUSH/POP in tight loops. https://www.cpcwiki.eu/index.php/Programming%3AFast_Sprites
- MSX.org C/SDCC optimization thread: byte-sized loops, globals/statics vs stack locals, `__sfr`, `__at`, `__z88dk_fastcall`, function-call overhead, and dirty text redraw. https://msx.org/forum/msx-talk/development/about-c-z80-optimizations-sdcc
- MSX.org SDCC calling-convention threads: `__naked`, SDCC 4.1.12+ `__sdcccall(1)`, register parameter passing, IX caveats, and ASM symbol export pitfalls. https://www.msx.org/forum/msx-talk/development/sdcc-4112-a-game-changer-for-c-programming and https://www.msx.org/forum/msx-talk/development/question-about-asm-library-in-sdcc
- SMS Power PDM optimization challenge: cycle-equalized output, branchless bit emission, generated sample code, double-buffered decode/output, and SMC `out` opcode ideas. https://www.smspower.org/forums/15875-PDMAkaPWMCodeOptimisationChallenge
- SMS Power Z80 programming techniques: unrolled block I/O, table alignment, conditional RST, fall-through loops, shadow registers, and "never call and then ret". https://www.smspower.org/Development/Z80ProgrammingTechniques
- SMS Power sprite programming thread: RAM sprite-table shadow and single VRAM copy per frame. https://www.smspower.org/forums/9623-SpriteProgramming
- Cemetech random optimizations and useful routines: data layout, IX tradeoffs, interleaved masks, shadow-register routines, and R-register PRNG. https://www.cemetech.net/forum/viewtopic.php?start=0&t=10416 and https://www.cemetech.net/forum/viewtopic.php?start=140&t=1449
- Cemetech common mistakes archive: overusing IX/IY and macro-vs-call decisions for tiny helpers. https://www.cemetech.net/projects/uti/viewtopic.php?start=0&t=8461
- World of Spectrum Z80 reference: undocumented flags/opcodes, IM 2, R register, and block-repeat behavior that affect whether a byte trick is legal. https://worldofspectrum.org/faq/reference/z80reference.htm
- AtariAge MDL optimizer thread: external peephole output is useful for ideas but can be risky with SDCC dialects and `call; ret` rewrites. https://forums.atariage.com/topic/309783-optimizer-for-z80-assembly/
- ZX-PK z88dk/C thread: compiler flags, `--reserve-regs-iy`, allocator settings, and sccz80/SDCC library-size tradeoffs. https://zx-pk.ru/threads/6844-ishchu-si-dlya-z80/page19.html
