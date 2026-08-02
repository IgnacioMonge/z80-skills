# ASM And ABI Checks

Prioritize the C to ASM boundary. That is the highest-yield surface for real bugs in these projects.

## Register and stack checks

- Verify every preserved register against the real caller contract, not comments.
- Check every exit path for balanced `push` and `pop`.
- Verify callee-clean vs caller-clean exactly. One extra byte on the stack is enough to crash later.
- Confirm shadow registers are restored before returning to C or mixed callers.
- Verify every flag-dependent branch against the actual preceding instruction. `ld`, `ex`, `push`, `pop`, `di`, and `ei` do not set the flags you may wish they did.
- Trace carry separately. `inc` and `dec` leave carry unchanged, so `jr c/nc` after them is either a deliberate stale-carry trick or a bug.
- Treat `exx`, `ex af,af'`, and `ld sp,...` as whole-routine contracts. One missing restore can corrupt code far away from the local routine.

## Packed-byte traps

- On Z80 SDCC stacks, `uint8_t` arguments are byte-packed, not widened to 16 bits for free.
- A `pop af` shortcut is not a safe way to read a packed trailing byte for a `__z88dk_callee` helper. It consumes two bytes and can read garbage into `A`.
- If you suspect a packed-byte bug, trace the exact stack layout from the call site to the return.

## Boundary audit

For every C to ASM symbol in scope:

- Identify the declaration side: cdecl, `__z88dk_callee`, `__z88dk_fastcall`, `__naked`, other local macros
- Verify parameter order and offsets from the real stack layout
- Verify return register width: `L`, `HL`, or `DEHL`
- Verify preservation of IX and IY against the current preflight profile
- Cross-check exports and imports with `"$SKILL_DIR/scripts/abi_inventory.py"`
- For every inline ASM block in C, list registers written or called helpers and verify the surrounding generated `.asm` keeps C temporaries safe
- For `__z88dk_fastcall`, `__z88dk_callee`, `__smallc`, and `__sdcccall(0/1)`, cite the actual convention used before assigning stack offsets

## ASM-specific hazards

- Relative jump range: prove `jr` is in range instead of assuming
- Intentional fall-through: require evidence, not hope
- `ldir` or `lddr`: check overlap direction, `BC=0`, and post-copy assumptions
- Fixed-address loads or stores: confirm the address contract and aliasing
- Tight loops: count T-states only where timing actually matters
- Stack blitters and push-burst screen writers: verify DI/EI, saved SP, clipping exits, and ISR model before calling them safe
- Screen writers: verify bitmap/attribute address math, row carry, third-screen boundaries, and attribute bleed
- Port I/O: verify register clobbers, contention/timing, and hardware target before trusting a generic emulator result
- `DJNZ` loops containing `CALL`: prove the callee preserves `B` or that the loop counter is saved/restored manually
- `EI; RET/JP/HALT`: treat as an explicit delayed-interrupt contract and verify the following instruction is the intended interrupt boundary
- `pop hl ; jp/jr/call target` or other caller-stack edits: prove every caller is at the same stack depth

## Control-flow state

- Prefer exported/global labels as routine starts. Treat branch-only labels as
  internal until proven otherwise.
- `ret`, `reti`, and `retn` are verified exits. Direct `jp`/`jr` are transfers:
  resolve the target before calling one an internal branch, tail call, or
  non-local exit.
- Do not reset stack, DI/EI, EXX, or alternate-AF state at every label.
- Keep DI state across internal labels until `ei`, a verified return, or a
  proven tail transfer.
- Treat conditional returns/jumps/calls as path hypotheses; a linear scanner
  cannot prove all paths.
- State whether stack and interrupt evidence is path-sensitive or a linear-scan
  approximation.

## Coverage reminder

If you run `full` and read mixed C plus ASM code, do not finalize until you have said something explicit about:

- Register preservation
- Stack cleanup
- Parameter width or packing
- Return-value width
- Relative branches or fall-through in the hot spots you inspected
