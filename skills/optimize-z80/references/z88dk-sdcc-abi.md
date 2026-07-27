# z88dk SDCC ABI And Codegen

Load this reference for z88dk / zsdcc / SDCC projects, especially when evaluating C-to-ASM moves or compiler-flag changes.

## Linkage Questions

Before proposing `fastcall`, `callee`, `__sdcccall(N)`, or a handwritten asm boundary, record:

- compiler and clib identity
- function prototype visible to C
- input register and stack contract
- return register contract
- preserved registers
- IX / IY ownership
- whether varargs or struct returns are involved

If any of these are unknown, downgrade the candidate.

## Net Across Callsites Rule

A convention or boundary change is scored on the whole linked program, never on
the callee alone: SDCC frequently fattens each callsite to satisfy the new
contract. Compute `net = callee_delta - sum(callsite_deltas)` from map/listing
of the same build, and state the callsite count in the candidate. Field data
point: a fastcall promotion with 11 callsites shrank the callee substantially
but delivered only 5 net bytes. Generic dispatch layers (event/action structs,
pointer-fed plumbing) are the extreme case: near-free on GCC hosts, +31 KiB
resident in a measured Z80 port — link-gate such designs in the same phase
they are written.

## Inline ASM Risk Gates

Inline asm requires stricter review than standalone asm because the compiler may still optimize around it.

Ask:

- does the compiler know which registers are clobbered?
- is `--peep-asm` enabled?
- would a `__naked` function or standalone asm file be safer?
- is the code trying to depend on temporary register allocation around the asm block?

Do not recommend inline asm as a casual fix for calling-convention or register-allocation problems.

## Common High-Value Checks

- accidental wide math helpers
- stack-frame setup in tiny hot functions
- helper calls inside hot loops
- repeated sign/zero extension
- standard-library pulls for short fixed operations
- `sdcc_ix` versus `sdcc_iy` trade-off
- `--reserve-regs-iy` side effects

## Artifact Set To Request

Prefer this minimal analysis bundle:

- map
- listing
- generated asm with source correlation when possible
- iCode / graph dumps only when codegen is the active bottleneck
- one representative binary size report

## C To ASM Promotion Rule

A C function graduates to an ASM candidate only when:

- it is hot or size-dominant
- the generated output shows a specific loss mechanism
- ABI can be stated in one short block
- validation can be done without redesigning half the project

## Do Not Oversell Compiler Knobs

A new pragma, clib variant, or peephole level is not a win until:

- the generated output is compared on the same toolchain baseline
- only one main variable changes
- any new runtime or CRT pull is accounted for
