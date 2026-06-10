# Preflight

Build the project profile before declaring bugs. Most false positives in mixed Z80 and C reviews come from guessing the ABI, startup, or memory model.

## Required profile

Capture these items before a `full` audit:

- Compiler and assembler: `zsdcc`, `sccz80`, `z80asm`, `z80n`, or hand-written only
- Major flags: `-SO`, `--opt-code-size`, `--fomit-frame-pointer`, `-startup`, `-clib`, `-zorg`, custom copt rules
- IX status: frame pointer in use or intentionally free
- IY status: CRT or clib reserved or project-local contract
- Target: flat 48K, banked 128K, dot command, overlay-heavy build, other
- Interrupt model: ROM IM1, custom IM1, IM2, or interrupts disabled
- Stack setup: stack top symbol, configured stack size, and any relocated stack area
- Evidence artifacts: `.map`, `.lst`, `.sym`, `.opt` or `.rul`
- Special regions: printer buffer, UDG area, system vars, overlay slots, scratch buffers, esxDOS-sensitive RAM

## Use scripts early

- Run `scripts/preflight_scan.py <root>` when the build system or target contract is not obvious from a single file.
- Run `scripts/map_summary.py <mapfile-or-root>` if a `.map` exists.
- Run `scripts/abi_inventory.py <root>` for mixed C and ASM codebases.

## z88dk or SDCC heuristics

- `--fomit-frame-pointer` usually means IX is free for generated C, but verify the generated contract before assuming every function may trash IX.
- `-clib=sdcc_iy` is a strong clue that IY is not yours to use freely.
- `CRT_STACK_SIZE`, `TAR__register_sp`, `__register_sp`, and `__BSS_END_tail` are high-value symbols in z88dk-style map files.
- `-startup` changes ROM, CRT, and interrupt expectations. Do not assume stock IM1 behavior if the startup or loader says otherwise.

## Preflight output

Summarize the profile before findings. A short block is enough:

```text
Toolchain: zcc + sdcc + z80asm
Flags: -SO3 --opt-code-size --fomit-frame-pointer -clib=sdcc_iy -startup=31
IX: free in generated C under current flags
IY: treat as reserved unless local proof says otherwise
Target: ZX Spectrum 48K flat build with overlays
Interrupts: custom polling, or ROM IM1, or unknown
Artifacts: .map yes, .lst no, .opt yes
```

If a field is unknown, say `unknown` rather than guessing.
