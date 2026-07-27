# Toolchain

## Analysis Build Rules

A professional analysis build may differ from release only when labeled as analysis.

Useful zcc/z88dk flags and concepts:

- `-m`: map
- `--list`: listings
- `--no-cleanup`: keep intermediates
- `--c-code-in-asm`: correlate C and ASM, but analysis-only because it may affect sccz80 optimization
- `-Ca`, `-Cl`, `-Cs`: pass options to assembler/linker/compiler
- `--split-bin`: section/bin attribution when available
- sections/segments for code/data placement

SDCC/zsdcc introspection (also load `z88dk-sdcc-abi.md` when changing linkage or inline asm):

- `--i-code-in-asm`
- `--dump-i-code`
- `--dump-graphs`
- `--dumpraw`
- `--cyclomatic`
- `--peep-file`
- `--codeseg`, `--constseg`

sjasmplus ASM-first standard:

- `--lst`
- `--lstlab`
- `--sym`
- `--sld`
- CSPECTMAP / LABELSLIST when useful
- Lua/codegen only as build-time generated artifact with source generator tracked

## Toolchain Matrix

Only run with approval or in measurement mode.

Compare one variable at a time:

- sccz80 O-levels
- zsdcc SO-levels
- analysis vs release instrumentation
- custom copt/peephole rule
- section placement

Do not mix CRT/clib/compiler/flags changes in one experiment.

## z88dk-copt

Use as a possible MEDIUM lane when repeated generated-ASM patterns are proven.

Good copt targets:

- consecutive byte loads/stores
- repeated stack shuffle
- redundant sign/zero extension
- repeated `call; ret`
- repeated address recomputation

Do not propose copt from one isolated pattern.

## MDL Z80 Optimizer

Use as optional external evidence, not as a blind patcher.

Useful concepts:

- call graph
- function stats
- expanded annotated ASM
- hotspot execution when harness exists
- peephole pattern discovery

Reject whole-file autopatching unless user explicitly asks and validation is strong.

## Other Tools

- z88dk-z80nm: object/library symbol inventory
- z88dk-dis: post-link symbolic disassembly
- z88dk-ticks: microbench kernels
- DeZog: source/listing debug with z88dk/sld artifacts
- Fuse/Spectrum debugger: runtime validation
- Emulicious: methodology reference for profiler/coverage on Z80-like systems
- Spectrum Analyser: frame trace/memory diff/I/O analysis reference

## Listings Missing

If `.lst`/`.lis`/`.sld` is missing:

- use map + source + known lib pulls
- propose listing generation as measurement step
- cap confidence for codegen claims

## Build Artifacts

Prefer fresh artifacts:

- map
- sym/sld
- lst/lis
- generated asm/opt
- size report
- overlay/bank report
- build log
- tap/bin/ovl/dat sizes

If stale, run one baseline build in a detached disposable worktree outside the
primary tree before claiming measured deltas.

## Tool Coverage Rule

Do not invent tool commands. Map memory-contention checks to
`scripts/contention_audit.py`; treat any unbundled size or CPU-detection helper
as a future idea, not a runnable command.

Prefer this evidence stack when available:

- z88dk/zcc: `-m`, `--list`, `--no-cleanup`, `--split-bin`, z80asm map/listing outputs.
- SDCC/zsdcc: `--dump-i-code`, `--dump-graphs`, `--cyclomatic`, `--i-code-in-asm`, `--peep-file`.
- sjasmplus: `--lst`, `--lstlab`, `--sym`, `--sld`, CSPECTMAP/LABELSLIST.
- MDL: call graph, function stats, expanded ASM, execution/hotspot reports when a harness exists.
- z88dk-ticks: deterministic microbench for small kernels.
- DeZog/Fuse/Spectrum Analyser/real hardware: runtime validation where timing, ULA, I/O, or compatibility matters.
- pasmo/WLA-DX/RGBDS: parse their maps/symbols conservatively; use as compatibility models, not Spectrum defaults.

If no profiler exists, use the fallback ladder in `measurement.md`:

1. fresh map/listing + static T-state estimate;
2. microbench isolated kernel with ticks/MDL;
3. FRAMES or border timing on Spectrum/emulator;
4. hardware/manual timing for UART, tape/disk, ULA, floating bus, and contention claims.
