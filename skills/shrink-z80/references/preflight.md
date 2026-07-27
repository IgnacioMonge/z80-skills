# Preflight

Measure first. Size work without a baseline drifts into folklore.

## Capture the build profile

Record these items before a `scan`:

- compiler, assembler, and linker path or command
- optimization flags such as `-SO`, `--opt-code-size`, `--fomit-frame-pointer`, `-startup`, `-clib`, `-zorg`
- SDCC/z88dk convention flags such as `--sdcccall`, `--reserve-regs-iy`, `--max-allocs-per-node`, `--peep-asm`, `--list`
- copt or peephole rules in the build
- presence of `.map`, `.sym`, `.lst`, generated `.asm`, and split/overlay binaries
- compression tooling already present: ZX0, ZX7, LZSA, RLE, generated assets
- current `CODE`, `DATA`, `BSS`, stack-top, and stack-gap symbols if a `.map` exists
- overlay or banked layout constraints
- for standalone SDCC or sccz80, exact map/listing dialect and whether section/symbol/helper sizes are parser-recognized or manual-only

## Use scripts

- Run bundled `$SKILL_DIR/scripts/preflight_scan.py <scope>` when the build configuration is spread across multiple files.
- Run bundled `$SKILL_DIR/scripts/map_summary.py <mapfile>` whenever a `.map` is selected; if several maps exist, choose explicitly or use `--all` for comparison.
- Run bundled `$SKILL_DIR/scripts/libpull_scan.py <scope> [map]` early in any real `scan`.

## Baseline note

Prefer a short baseline block before findings:

```text
Toolchain: zcc + sdcc + z80asm
Flags: -SO3 --opt-code-size --fomit-frame-pointer -clib=sdcc_iy -startup=31
Artifacts: .map yes, .sym yes, .lst no, generated .asm yes, .rul yes
Stack top: $FF58
BSS end: $F486
Gap: 210 bytes
Compression/tools: zx0 yes, custom RLE no
```

If a value is unknown, say `unknown`. Do not fake precision.

## Hard contract

- Obey `hard-contract.md`: current-code evidence only; primary read-only;
  disposable measurement worktrees deleted at end of run by default.
- Record artifact freshness: map/listing mtime vs sources in scope.


## Hard-contract scripts

- Run bundled `$SKILL_DIR/scripts/artifact_freshness.py <scope>` before any
  EXACTO claim from `.map`/`.lst`/binaries.
- Run bundled `$SKILL_DIR/scripts/map_summary.py <map>` and read
  `[resident_vs_banked_heuristic]` and `[crt_startup_drag]` before micro work.
- If freshness is STALE: rebuild in a disposable worktree or mark REQUIERE BUILD.

## Freshness modes (P3)

- Default: `artifact_freshness.py` **per-unit** (sources in same package unit as the map).
- Monorepo: unrelated trees do not force STALE on local maps.
- Strict: `--mode global` or CI `--touched path...`.
- Net claims: run `net_compression_check.py` with measured integers (Net_storage vs RAM_peak_delta).
