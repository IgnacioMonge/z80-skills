# Size Blackbook — Dark-Art Families

Load for `blackbelt` mode and the black-belt pass of `scan`. These families sit
above the general forum catalog: rarer, higher yield, higher proof burden. Every entry is
candidate-only until byte count, ABI, flag/register/stack, and rebuild proof
exist. Families tagged `EXPERIMENTAL` or `undocumented` additionally require an
explicit user opt-in before any edit is proposed as actionable.

Each candidate promoted from this file must state: family, expected net bytes,
preconditions, proof obligations, danger tag (`smc`, `sp_abuse`, `undocumented`,
`interrupt_windows`, `rom_dependency`, `init_order`), and rollback.

## 1. ROM as constant pool and routine library (48K Spectrum)

- Lane: MEDIUM. Tag: `rom_dependency`.
- The 16 KB ROM is always mapped at 0x0000-0x3FFF on the classic targets.
- Font at 0x3D00-0x3FFF: a text renderer that reads glyphs from ROM deletes the
  entire resident font (up to 768 bytes) at the cost of a base-pointer swap.
- Routine reuse: RST 0x10 print channel, KEY-SCAN 0x028E, BEEPER 0x03B5 are
  callable when their sysvar/state contracts are met. Count setup bytes
  honestly; ROM print needs channel state.
- Byte mining: any constant table the project needs may already exist as a byte
  sequence somewhere in ROM. Search the ROM image for the exact sequence (or a
  stride-accessible variant) and point at it instead of storing it.
- Preconditions: target set fixed to machines with the assumed ROM (state which
  ROM images were checked); paging state guaranteed at call time (48K ROM
  mapped, not interface/divMMC shadow at that moment).
- Reject if: esxDOS/divMMC hooks can shadow the address range during the call
  window, or the project targets Next-only cores with modified ROM.
- Validation: dump the assumed ROM bytes at build time and assert equality in a
  host test; hardware smoke on every physical model in the support matrix.

## 2. Instruction-skip and overlapping-opcode tricks

- Lane: DANGEROUS for maintainability, deterministic in behavior. Mark
  `EXPERIMENTAL`.
- 1-byte skip: `db 0x21` (`ld hl,nn`) swallows the next two bytes as an operand;
  `db 0x3E` (`ld a,n`) swallows one. Replaces a 2-byte `jr` over a 1-2 byte
  instruction, saving 1 byte per site and all branch overhead.
- Stacked entry points: `entry1: ld a,1` / `db 0x21` / `entry2: ld a,2` /
  `db 0x21` / `entry3: ld a,3` / shared body — N variants of a helper for
  1 byte each instead of N separate call/jp shims.
- Operand-as-data: small constants can live inside the swallowed operand bytes,
  or code bytes can double as table entries.
- Preconditions: the swallowed load's side effect (a dead HL/A write) is
  provably harmless at every entry; no flag dependency crosses the skip; the
  pattern is wrapped in a named macro (e.g. `SKIP2`) so intent stays visible.
- Reject if: maintainability policy forbids it outside generated code, or any
  debugger/single-step assumption inspects the region.
- Validation: listing shows exact bytes; every entry point exercised by a test;
  disassembly reviewed after each rebuild because label drift silently changes
  the swallowed bytes.

## 3. Demo-grade flag/register idioms

- Lane: SAFE to MEDIUM once flags are proven dead. Tag: none.
- Nibble to ASCII-hex without table or branch (6 bytes):
  `add a,0x90` / `daa` / `adc a,0x40` / `daa`. Kills 10+ byte compare/branch
  or 16-byte table formatters. Protocol/hex formatters are prime callers.
- `rst NN` as 1-byte call for the hottest helper when the vector is free on the
  target (not 48K ROM-owned vectors; valid on custom cores or when an
  interface owns the page). Vector ownership is a precondition, not a hope.
- `push rr` / `ret` computed dispatch: jump-table dispatch with no `jp (hl)`
  register pressure; store plain target addresses.
- Carry-chain arithmetic: replace `cp/jr/inc` ladders with `add`/`adc`/`sbc`
  sequences that accumulate the comparison into carry.
- Shadow set as free storage: `exx` / `ex af,af'` hold a second working set
  across a leaf region — only when ISR ownership of the shadow set is settled
  project-wide (state the owner in the candidate).
- Validation: flags dead-on-entry/exit proven from listing; ISR shadow-register
  contract quoted from project docs, not assumed.

## 4. Self-destructing init code (run-once code in reusable buffers)

- Lane: MEDIUM to DANGEROUS. Tags: `init_order`, sometimes `smc`.
- Place one-shot initialization (table builders, screen setup, config load,
  unpackers) inside a buffer region that the runtime only uses after init has
  finished: UART rings, snapshot/scratch buffers, the screen bitmap during a
  loading picture, BSS arrays whose first use is post-init.
- Resident cost of that init code becomes zero: the bytes are reclaimed as the
  buffer they always were.
- In a project starved for resident bytes this is routinely the single largest
  lever that changes no runtime semantics.
- Preconditions: a written lifetime map proving the buffer has no reader/writer
  until init completes (interrupts included — an ISR feeding the UART ring
  during init kills the trick); load order places the init image there before
  first call; no restart path re-enters init after the buffer went live.
- Reject if: any restart/reinit path exists without a reload, or the buffer is
  touched by ISR/DMA at boot.
- Validation: linker map shows the section placement; a canary test fills the
  buffer post-init and re-runs the app's restart path if one exists; hardware
  cold-boot and warm-restart both smoke-tested.

## 5. Undocumented CPU surface as storage and ops

- Lane: DANGEROUS. Tag: `undocumented`. Requires explicit user opt-in.
- IXH/IXL/IYH/IYL as four extra 8-bit registers: delete memory temporaries and
  their 3-byte load/stores in register-starved leaf routines. Prefix costs
  2 bytes per access — net win only against 3-4 byte memory traffic; count per
  access, not per routine.
- `sll` (shift left, set bit 0) where the stray 1-bit is wanted or masked free.
- Preconditions: target CPUs pinned (genuine Z80 and Next core implement these;
  state the support matrix and any emulator the team uses); no toolchain
  peephole rewrites the prefix form; IY not owned by the runtime/ISR
  (`--reserve-regs-iy` status recorded).
- Reject if: any target in the matrix runs on a core/emulator without
  undocumented-opcode fidelity, or IX/IY ownership is contractual (frame
  pointer, sysvar access).
- Validation: run the project's ISR stress test; verify on every emulator in
  the team's workflow plus hardware; listing greps confirm no accidental
  prefix+opcode combos outside the audited sites.

## 6. Custom SDCC peephole rules (.rul) — shrink the generator, not the output

- Lane: MEDIUM (build-system change, code-neutral until proven). Tag: none.
- z88dk/SDCC accept user peephole files. When the same wasteful shape
  (redundant field reload, push/pop ballet around a helper, wide compare of a
  known-8-bit value) appears at many sites, one rule rewrites every current
  and future instance — unlike hand edits, it also protects the next build
  against regression.
- Attack order: harvest the top repeated n-grams from generated ASM
  (`z80_pattern_scan.py` output), write the narrowest rule that matches, count
  sites x bytes from the listing diff.
- Preconditions: rule conditions (`notUsed`, label refs, flag liveness) encode
  every safety assumption — a peephole that fires on a flag-live site is a
  silent corruption factory; toolchain version pinned because rule dialects
  drift.
- Reject if: the shape has fewer than ~5 sites (hand edit is cheaper to review)
  or flag liveness cannot be expressed in the rule language.
- Validation: full test suite plus a listing diff review of EVERY site the
  rule fired on (grep the peephole log); keep the rule file in version control
  next to the build flags.

## 7. Resident string packing with a micro-decoder

- Lane: SAFE to MEDIUM. Tag: none.
- 5/6-bit alphabet packing or digram/byte-pair encoding for UI/status strings:
  typical 30-40% savings on string bytes against a 20-40 byte decoder plus a
  16-32 byte digram table. Net turns positive at roughly 150-250 bytes of
  resident strings; count exactly.
- Decoder emits into the existing print path one char at a time — no extra
  buffer needed if the renderer accepts a streamed source.
- Interacts with family 1: if the ROM font is used, ROM glyph order can make a
  5-bit alphabet remap nearly free.
- Preconditions: full string inventory measured (dedup first — packing a
  duplicate double-counts against `literal_dup_scan.py` findings); strings are
  read-only; no code indexes into string interiors.
- Reject if: strings are patched at runtime, or the same strings are candidates
  for deletion/dedup with better net.
- Validation: golden vectors decoder-vs-original for every string; byte math in
  the report lists packed bytes + decoder + tables vs original bytes.

## Ordering rule

Families 4 and 6 usually dominate: they harvest bytes across the whole binary
instead of per-site. Check them before spending effort on families 2/3/5, and
report expected net for every family consulted, even when `none found`.

## Further discovery

For techniques beyond these seven families, use `external-research.md` with a
project-specific question rather than loading a fixed underground catalog.
