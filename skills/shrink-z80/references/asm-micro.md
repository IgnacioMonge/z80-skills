# ASM Micro Patterns

Use this file when the task is down in hand-written assembly or generated hot spots that need local byte shaving.

## Safe local patterns

- `call foo` plus `ret` to `jp foo`
- repeated tails to one shared `jp tail`
- `dec b` plus `jr nz` to `djnz` when flags after `dec` are dead
- `jp` to `jr` only when range is proven; conditional `jr` exists only for `NZ/Z/NC/C` (never `M/P/PE/PO`)
- `ld a,0` to `xor a` only when flag differences are irrelevant
- branchy `ld a,0` / `ld a,255` boolean masks to carry setup plus `sbc a,a` only when `C` can be made the predicate and `0xff` is acceptable or can be normalized
- remove unnecessary IX or IY preserve pairs only when every callee contract is known
- merge repeated suffix tails when the shared tail plus jumps saves net bytes
- replace repeated short call sequences with a local command byte/table only after counting decoder overhead

## Prefix tax

Count IX or IY prefixes in hot routines. If the same logic fits in BC, DE, or HL without breaking the ABI, that often saves more than tiny instruction swaps.

## Layout leverage

- Reorder local routines to convert long `jp` into `jr`, enable fall-through, or share epilogues.
- Put hot local helpers near their callers when that unlocks relative branches or shorter tables.
- In screen code, consider data order changes before instruction changes; Spectrum bitmap row layout can remove arithmetic.

## Anti-patterns

Do not propose these as automatic wins:

- `ldi` as a substitute for `ld a,(hl)` plus `inc hl`
- rotate-based bit tests that also mutate the source register unless the register is dead
- `pop af` tricks for packed byte parameters
- self-modifying code or RST slot abuse unless the user explicitly opts in
- flag-changing substitutions when a later branch may observe those flags
- stack-pointer tricks unless SP restore and interrupt state are proved
- `DJNZ` loop rewrites when the loop body calls helpers that may clobber `B`

## Local proof

Use `z80-byte-evidence.md` for common opcode sizes when listings are unavailable. Prefer `.lst`/`.lis` bytes over manual tables.


Every micro proposal should mention:

- byte saving
- flag or register preconditions
- stack effect
- whether a rebuild is required to confirm `jr` range or linker fallout
- whether the replacement changes cycle cadence in screen/audio/UART/loader code
