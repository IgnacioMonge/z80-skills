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
- Cross-check exports and imports with `scripts/abi_inventory.py`

## ASM-specific hazards

- Relative jump range: prove `jr` is in range instead of assuming
- Intentional fall-through: require evidence, not hope
- `ldir` or `lddr`: check overlap direction, `BC=0`, and post-copy assumptions
- Fixed-address loads or stores: confirm the address contract and aliasing
- Tight loops: count T-states only where timing actually matters
- Stack blitters and push-burst screen writers: verify DI/EI, saved SP, clipping exits, and ISR model before calling them safe
- Screen writers: verify bitmap/attribute address math, row carry, third-screen boundaries, and attribute bleed
- Port I/O: verify register clobbers, contention/timing, and hardware target before trusting a generic emulator result

## Coverage reminder

If you run `full` and read mixed C plus ASM code, do not finalize until you have said something explicit about:

- Register preservation
- Stack cleanup
- Parameter width or packing
- Return-value width
- Relative branches or fall-through in the hot spots you inspected
