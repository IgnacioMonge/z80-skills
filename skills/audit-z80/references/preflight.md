# Preflight

Build the project profile before declaring bugs. Most false positives in mixed Z80 and C reviews come from guessing the ABI, startup, or memory model.

## Required profile

Capture these items before a `full` audit:

- Compiler and assembler: `zsdcc`, `sccz80`, `z80asm`, `z80n`, or hand-written only
- Major flags: `-SO`, `--opt-code-size`, `--fomit-frame-pointer`, `-startup`, `-clib`, `-zorg`, custom copt rules
- SDCC convention flags: `--sdcccall`, `--reserve-regs-iy`, `--fno-omit-frame-pointer`, `--max-allocs-per-node`, `--peep-asm`
- IX status: frame pointer in use or intentionally free
- IY status: CRT or clib reserved or project-local contract
- Target: flat 48K, banked 128K, dot command, overlay-heavy build, other
- Interrupt model: ROM IM1, custom IM1, IM2, or interrupts disabled
- Stack setup: stack top symbol, configured stack size, and any relocated stack area
- Evidence artifacts: `.map`, `.sym`, `.lst`, generated `.asm`, `.opt` or `.rul`
- Special regions: printer buffer, UDG area, system vars, overlay slots, scratch buffers, esxDOS/divMMC-sensitive RAM
- Firmware boundary: ROM calls, `RST 8`, esxDOS file calls, dot-command assumptions, custom loader paging

## Use scripts early

- Run `python3 scripts/preflight_scan.py <root>` when the build system or target contract is not obvious from a single file.
- Run `python3 scripts/map_summary.py <mapfile-or-root>` if a `.map` or `.sym` exists.
- Run `python3 scripts/abi_inventory.py <root>` for mixed C and ASM codebases.
- Run `python3 scripts/z80_pattern_scan.py <root>` before finalizing any broad audit that includes inline ASM, overlays, RST8, screen timing, or hand ASM.

## z88dk or SDCC heuristics

- `--fomit-frame-pointer` usually means IX is free for generated C, but verify the generated contract before assuming every function may trash IX.
- `-clib=sdcc_iy` is a strong clue that IY is not yours to use freely.
- `CRT_STACK_SIZE`, `TAR__register_sp`, `__register_sp`, and `__BSS_END_tail` are high-value symbols in z88dk-style map files.
- `-startup` changes ROM, CRT, and interrupt expectations. Do not assume stock IM1 behavior if the startup or loader says otherwise.
- `--opt-code-size`, `--sdcccall`, and `__z88dk_fastcall` change the generated call surface enough that source-only stack-offset reasoning is weak.
- Inline ASM blocks require generated `.asm/.lst` inspection when they touch registers, call helpers, use labels, or depend on flags.

## Preflight output

Summarize the profile before findings. A short block is enough:

```text
Toolchain: zcc + sdcc + z80asm
Flags: -SO3 --opt-code-size --fomit-frame-pointer -clib=sdcc_iy -startup=31
IX: free in generated C under current flags
IY: treat as reserved unless local proof says otherwise
Target: ZX Spectrum 48K flat build with overlays
Interrupts: custom polling, or ROM IM1, or unknown
Artifacts: .map yes, .lst no, generated .asm yes, .opt yes
Firmware: RST8/esxDOS unknown
```

If a field is unknown, say `unknown` rather than guessing.

`preflight` never escalates by itself. Report escalation signals for `auto` or `full`: mixed C/ASM, inline ASM touching registers, special ABI markers, ISR/DI/EI, fixed RAM, overlays/banks, RST8/esxDOS/divMMC, suspicious stack/BSS gap, generated artifacts needed for proof, or a user-reported runtime symptom.

## Hard contract

Obey `hard-contract.md`: current-code evidence only; primary read-only; disposable sandboxes deleted by default.
