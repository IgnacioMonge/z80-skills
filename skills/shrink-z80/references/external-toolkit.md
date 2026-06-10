# External Toolkit

Use this when the user wants stronger, more imaginative Z80 shrink work. Treat every source here as an idea bank. A proposal becomes a `CONFIRMED SAVING` only after local proof: bytes counted, flags/registers/stack preserved, branch ranges checked, and build remeasured when required.

If the user explicitly asks to mine programmer forums or hidden old-school tricks, also load [forum-gems.md](forum-gems.md).

## Tool-backed idea sources

- z88dk: inspect `-SO3`, `-On`, `--opt-code-size`, `--max-allocs-per-node`, `--list`, `-m`, `-s`, `-Cl--split-bin`, `z88dk-dis`, `z88dk-ticks`, `z88dk-zx0`, `z88dk-zx7`, and custom `copt` rules. Use `.map`, `.lis`, `.sym`, and split binaries to measure where bytes really go. Source/docs: https://github.com/z88dk/z88dk and https://github-wiki-see.page/m/z88dk/z88dk/wiki/Tool---z80asm---command-line
- z88dk `copt`: useful for project-specific peephole rules, but pattern matching is textual. Any rule must have tight preconditions about flags, labels, fall-through, and clobbers.
- upeep80/upeepz80-style peephole optimizers: useful as external candidate generators for redundant loads/stores, jump threading, `call; ret -> jp`, `djnz`, and stack-copy cleanup. Do not auto-apply output; licensing and syntax fit must be checked.
- sjasmplus: warnings, listings, fake-instruction diagnostics, and Z80N mode checks can expose accidental size or target issues.
- CPU/timing references: Time Proofing, WikiTI, SpecNext, Sean Young/David Banks undocumented-Z80 docs, redcode/Z80, and z80ex help calibrate bytes/T-states/flags when a rewrite looks clever.

## Demoscene and game-pattern idea bank

- Stack blitters: `ld sp,dst` plus `push` bursts can be extremely fast and sometimes compact for screen writes; Ghosts'n Goblins analysis shows the pattern in a real Spectrum renderer: https://www.emix8.org/ggdisasm/. Only propose if stack restoration, DI span, and caller contract are provable.
- Race-the-beam/direct screen painting: can remove buffers or clipping work, but turns timing and memory placement into behavior. Mark as `AGGRESSIVE` unless already part of the architecture.
- Clipping zones and black-border writes: sometimes cheaper than per-sprite clipping. Requires exact screen/attribute layout proof.
- Pre-rotated sprites/tables: trade data for code and speed. For shrink, verify net bytes after removing shift/mask code.
- Table-driven dispatch: good for repeated protocol/state/screen cases, but include table bytes, index code, and lost `jr` range savings in the count.
- Tail merging/suffix factoring: search for common epilogues, wrappers, and `call target; ret`. Prove helper overhead is net-positive.
- Opcode overlays, `rst` hijacking, self-modifying code, and skip-byte tricks: `EXPERIMENTAL`; only propose if the user explicitly wants maximum aggression and the verification path is clear.
- Packed bytecode/token interpreters: useful when many commands share structure; count interpreter bytes and make sure hot paths can afford dispatch.
- Data-order inversion: store sprites, text, or protocol fields in consumption order so the loop becomes pointer increments instead of address arithmetic.
- Page-local tables: when all targets share a high byte, byte offsets can replace pointer tables; only safe with linker/layout proof.
- ChibiAkumas Z80 lessons/videos (https://www.chibiakumas.com/z80/akuma.php): mine for event-stream compression, nibble-coded commands, vector dispatch, RST-style call indirection, 8-bit coordinate design, clipping zones, and deliberate self-modifying game-engine code.
- Espamatica ZX Spectrum Pong optimization (https://espamatica.com/zx-spectrum-assembly-pong-0x0a-optimisation/): mine for dirty redraw, shared draw tails, direct address constants, multiply-by-power-of-two rewrites, and optimization passes that expose game-logic bugs.

## Compression choices

- ZX0 (https://github.com/einar-saukas/ZX0): strong default for small 8-bit data; Z80 decompressors are small, fast, main-register-only, low stack, and no extra buffer.
- LZSA: optimized for fast 8-bit decompression; useful for larger assets or banked/overlay data when decoder cost amortizes.
- ZX7 and Salvador-style options: compare when decompressor size or legacy toolchain fit matters.
- Compression is a net saving only after counting decoder bytes, packed data, workspace/stack, call sites, and load-time cost.

## Required report additions

- Add a `Rejected ideas` section when external/generated ideas were considered but failed local proof.
- Mark every external candidate as `SPECULATIVE` until the current source and build artifacts prove it.
- For each accepted idea, include the exact local reason the external trick applies here.
