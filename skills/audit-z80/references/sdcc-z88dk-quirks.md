# SDCC And z88dk Quirks

Use this file for `toolchain`, `abi`, `asm`, `copt`, generated-code suspicion, inline ASM, or mixed C/ASM audits.

## Generated output is evidence

- Prefer generated `.asm`/`.lst` over source intuition whenever a finding depends on stack offsets, register arguments, prologue/epilogue, IX/IY, optimizer output, or copt rules.
- For changed C functions on hot paths or ABI boundaries, inspect the generated output before finalizing a bug or a no-finding.
- If only C source is available, mark optimizer/codegen-dependent findings as `NEEDS BUILD` or `SUSPICIOUS`.

## Inline assembler blindness

- SDCC does not validate code inside `__asm ... __endasm` and does not know which registers it uses. Any register save/restore must be manual.
- Treat inline ASM that writes `A/F`, `BC`, `DE`, `HL`, `IX`, `IY`, or `SP` as a real audit target unless surrounded by an explicit project-local preserve contract.
- Inline ASM inside macros must place each instruction on a separate generated line. Otherwise the assembler or copt may see something different from what the C macro suggests.
- `--peep-asm` can pass inline assembler through peephole rules. Review `.opt`/`.rul` and generated `.asm` before trusting inline timing, flags, or labels.

## Calling convention checkpoints

- SDCC Z80 default `__sdcccall(1)` can pass early parameters in registers and later parameters on stack right-to-left. Do not assume all parameters are stack-only.
- `__sdcccall(0)` passes all parameters on stack right-to-left and returns 8/16/32-bit values in `L`/`HL`/`DEHL`.
- `__smallc` passes arguments on stack left-to-right and 1-byte arguments consume 2 bytes with the value in the lower byte.
- `__z88dk_fastcall` allows one parameter up to 32 bits, passed like the return value of the selected convention.
- `__z88dk_callee` changes stack cleanup: the callee must remove stack parameters.
- Variadic functions fall back to stack-passed arguments. Hidden struct/union return pointers can shift visible stack offsets.

## IX/IY and frame-pointer profile

- When SDCC uses a frame pointer on Z80, it resides in IX. `--fomit-frame-pointer` and `--fno-omit-frame-pointer` change the IX contract.
- `--reserve-regs-iy` tells SDCC not to use IY and is incompatible with `--fomit-frame-pointer`.
- z88dk `sdcc_iy` or project CRT conventions can reserve IY for runtime state. Treat IY as reserved until preflight proves otherwise.
- Hand ASM that borrows IX/IY inside a DI window must prove all exits restore it and no called/generated path observes the borrow.

## Optimizer and copt suspicion

- `--opt-code-size` and high `--max-allocs-per-node` can materially change generated Z80. Treat pre/post-build `.asm` diffs as part of review when enabled.
- Do not assert a specific optimizer bug without the generated instructions. Use `SUSPICIOUS` and request `.asm/.lst` when a known-risk flag combination meets `fastcall`, inline ASM, or naked wrappers.
- copt rules are textual transformations. Audit flags, labels, fall-through, stack, and register liveness for every custom rule that touches in-scope code.

## C constructs that deserve generated-ASM review

- `uint8_t` arguments and packed stack bytes at ABI boundaries.
- `int`, `size_t`, or pointer arithmetic in loops that the source expects to be byte-sized.
- `switch`, pointer tables, string tables, and `static const char *` arrays.
- Calls to `strlen`, `strcmp`, `memcpy`, `memset`, `printf`, arithmetic helpers, and one-callsite wrappers.
- `__naked` functions. The user must supply return instruction, prologue/epilogue, register preservation, and ISR return form.
