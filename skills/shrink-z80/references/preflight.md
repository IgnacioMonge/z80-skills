# Preflight

Measure first. Size work without a baseline drifts into folklore.

## Capture the build profile

Record these items before a `scan`:

- compiler, assembler, and linker path or command
- optimization flags such as `-SO`, `--opt-code-size`, `--fomit-frame-pointer`, `-startup`, `-clib`, `-zorg`
- copt or peephole rules in the build
- presence of `.map`, `.lst`, `.sym`, and generated `.asm`
- current `CODE`, `DATA`, `BSS`, stack-top, and stack-gap symbols if a `.map` exists
- overlay or banked layout constraints

## Use scripts

- Run `scripts/preflight_scan.py <root>` when the build configuration is spread across multiple files.
- Run `scripts/map_summary.py <mapfile-or-root>` whenever a `.map` is available.
- Run `scripts/libpull_scan.py <root> [map]` early in any real `scan`.

## Baseline note

Prefer a short baseline block before findings:

```text
Toolchain: zcc + sdcc + z80asm
Flags: -SO3 --opt-code-size --fomit-frame-pointer -clib=sdcc_iy -startup=31
Artifacts: .map yes, .lst no, .rul yes
Stack top: $FF58
BSS end: $F486
Gap: 210 bytes
```

If a value is unknown, say `unknown`. Do not fake precision.
