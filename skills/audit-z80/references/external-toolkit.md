# External Toolkit

Use this file when the task asks for unusually deep, external, demoscene, Gemini/Claude-style, or tool-assisted Z80 review. These sources are idea generators and verification aids. They never override the project source, build flags, `.map`, `.lst`, or ABI contract.

If the user explicitly asks to mine programmer forums or hidden old-school tricks, also load [forum-gems.md](forum-gems.md).

## Verification tools to prefer

- z88dk toolchain: use `zcc`, `z88dk-z80asm`, `.map`, `.sym`, `.lis`, `z88dk-dis`, and `z88dk-ticks` when available. z88dk docs/source: https://github.com/z88dk/z88dk and z80asm command-line notes: https://github-wiki-see.page/m/z88dk/z88dk/wiki/Tool---z80asm---command-line
- sjasmplus projects: enable/list warnings when possible. Its warning IDs catch low-address reads, syntax traps, and fake-instruction issues; suppressions must be intentional.
- Accurate CPU references: redcode/Z80, z80ex, ZEXALL/ZEXDOC/Fuse tests, and hardware-derived instruction tests are useful when flags, IM behavior, undocumented opcodes, or interrupt timing matter.
- Instruction tables: Time Proofing, WikiTI, SpecNext, and Sean Young/David Banks undocumented-Z80 references are for opcode/timing/flag sanity checks.

## Audit patterns to force

- Block ops: `LDIR`, `LDDR`, `CPIR`, `OTIR`, `INIR` alter registers/flags and have interrupt-visible edge cases. Prove overlap direction, `BC=0` behavior, post-copy assumptions, and ISR expectations.
- Shadow register tricks: `exx` and `ex af,af'` are safe only with a proven whole-program convention. Treat ISR or ROM interaction as hostile until checked.
- Stack-as-pointer or stack blitter code: `ld sp,...` plus `push` bursts can be correct and very fast, but audit all exits, interrupt state, stack restoration, and caller stack assumptions.
- Self-modifying code or opcode overlays: verify RAM location, cache-free hardware assumption, relocation, overlays, and assembler/linker layout.
- Raster/border/screen tricks: direct `$4000..$5aff` writes, port `$fe`, floating bus, and contended RAM are machine-model contracts, not generic memory accesses.
- `I`, `R`, `SCF`, `CCF`, `BIT (HL)`, and block-repeat flags: do not assume textbook flags if the code observes undocumented flags or interrupt flip-flops.
- Next-only/Z80N opcodes: reject in 48K/divMMC code unless the build target explicitly allows them.
- Flag provenance: prove the exact instruction that produced Z/NZ/C/NC before every suspicious conditional branch. Stale flags are a classic "works until refactor" bug source.
- UX timing: missed input, audio clicks, flicker, border glitches, and blocking file/UART paths count as defects when they break the intended experience.

## Case-study sources to mine for ideas

- Ghosts'n Goblins ZX Spectrum graphics analysis (https://www.emix8.org/ggdisasm/): direct video writes, stack-driven right-to-left sprite drawing, clipping zones, mixed background/sprite painting, and race-the-beam constraints.
- ZQloader: turbo loader code moves itself away from contended lower RAM; useful reminder that memory placement can be a correctness/timing contract.
- ZX0/LZSA decompressor sources, including ZX0 (https://github.com/einar-saukas/ZX0): good models for small, register-disciplined routines; audit integration for clobbers, stack, buffer direction, and decompressor workspace.
- Classic isometric/action engines: object lists, dirty rectangles, draw-order invariants, and sprite masks often encode logic contracts that are invisible if you audit one function at a time.
- Demoscene raster/audio code: tight timing often depends on exact instruction placement; assembler layout and interrupt model are part of correctness.
- ChibiAkumas Z80 lessons/videos (https://www.chibiakumas.com/z80/akuma.php): useful for auditing real game-engine contracts: 8-bit coordinate budgets, clipping zones, event streams, vector dispatch, self-modifying commands, register-preservation warnings, and cross-platform Z80 tradeoffs.
- Espamatica ZX Spectrum Pong optimization (https://espamatica.com/zx-spectrum-assembly-pong-0x0a-optimisation/): practical examples of not repainting unchanged UI, tail jumping into shared draw code, replacing loops with address arithmetic, and finding collision/scoreboard logic bugs while optimizing.

## Reporting rule

External inspiration is never a finding. Convert it into a finding only after local proof: exact file/line, contract, clobber/flag/stack effect, and concrete failure mode.
