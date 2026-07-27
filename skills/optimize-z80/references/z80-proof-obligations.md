# Z80 Proof Obligations

Use this reference when a candidate depends on exact CPU behaviour rather than a generic "hot loop" story.

## When A Claim Needs Proof

Escalate from generic advice to proof obligations when the candidate depends on one of these:

- exact T-state counts rather than broad "likely faster"
- flag preservation or deliberate flag reuse across merged code paths
- IX/IY replacement, alternate registers, or stack pointer abuse
- block operations versus manual loops
- undocumented opcodes or undocumented flag behaviour
- DI/EI windows, IM 1 / IM 2 interaction, or ISR ownership of registers

If the proof cannot be shown from listing, map, trace, or hardware/emulator evidence, demote the claim.

## Flags And Control Flow

Before proposing branch factoring, shared tails, or arithmetic rewrites, prove:

- carry / zero / sign / parity expectations at every consumer
- whether the original path consumed flags immediately or incidentally preserved them
- whether a merged suffix changes the last flag-producing instruction
- whether the path crosses inline asm, ISR entry, or ABI boundaries

Good evidence:

- before/after listing of the exact basic block
- functional tests covering all flag-sensitive exits
- cycle note only after correctness proof

## IX And IY

Treat IX/IY as a cost center and an ownership question.

Checklist:

- does the compiler own IX as frame pointer?
- does the clib own IY?
- is `--reserve-regs-iy` in play?
- are ROM interrupts still enabled on a target where IY must remain stable?
- is the candidate saving bytes, cycles, or both after prefix costs are counted?

Recommend index-register work only with generated ASM or listing evidence.

## Block Operations

For `LDI`, `LDIR`, `CPI`, `CPIR`, `INI`, `INIR`, `OUTI`, and `OTIR`, always record:

- fixed versus variable block-size distribution
- overlap semantics
- setup overhead versus loop-body savings
- contention sensitivity on Spectrum targets
- size goal versus speed goal

Do not elevate a block-op suggestion from "interesting" to "top candidate" without realistic size distribution.

## Alternate Registers

`EXX` and `EX AF,AF'` are not free wins unless ownership is explicit.

Require:

- ISR ownership audit
- library-call boundary audit
- clear kernel boundary
- fallback path if the project later enables interrupts in that region

If ownership is unknown, keep alternate-register ideas in CHECK or DANGEROUS lanes.

## Undocumented And Model-Sensitive Work

For undocumented opcodes, undocumented flags, floating-bus timing, snow effects, or raster tricks:

- record CPU / machine floor explicitly
- state compatibility waiver or fallback
- require hardware or faithful emulator validation
- never suggest as a default release-path optimization

## Interrupt Windows

Any candidate using `DI`, long critical sections, shadow registers, stack relocation, or SMC patch points must state:

- entry conditions
- maximum disabled-interrupt window
- whether NMI remains possible
- exact restore point before return / wait / library call
- validation path on the real deployment model
