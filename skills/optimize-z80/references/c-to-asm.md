# C To ASM Candidates

Convert C to ASM only when evidence proves the compiler or ABI is the bottleneck.

## Elevation Gate

A C function may move to ASM only if it passes all three:

- weight: hotspot, dominant call graph node, large symbol, or frame/latency critical
- stability: stable contract and test/harness possible
- explainability: generated ASM shows the loss mechanism

Valid loss mechanisms:

- stack spills or excessive stack args
- repeated helper calls in inner loop
- expensive division/long math/library pull
- layout the compiler cannot exploit
- need for exact register allocation
- need for contention-aware placement
- need for self-modifying or generated code
- ABI/calling boundary cost dominates

## Good Candidates

- byte scanners/parser loops
- screen address math
- small hot loops with fixed-width ints
- memcpy/fill/blit-like routines
- decompressor inner loops
- fixed multiply/divide kernels
- audio/player inner loops

## Bad Candidates

- I/O-bound waits
- network latency
- file/disk waits
- rarely executed setup code
- complex rules with many edge cases unless tests are strong
- code already dominated by overlay/bank load

## Required ABI Checklist

- calling convention
- input registers/stack args
- return registers
- clobbers
- preserved registers
- IY/IX ownership
- interrupt assumptions
- section/segment placement
- PUBLIC/EXTERN names
- C prototype compatibility
- test/harness

## z88dk/SDCC Checks

- `--i-code-in-asm`, `--dump-i-code`, `--dump-graphs`, `--cyclomatic` where available
- zcc `--list`, `-m`, `--no-cleanup`, `--c-code-in-asm` for analysis builds only
- helper/lib pulls from string/memory/division/long math
- generated ASM stack use and frame pointer
- call graph and symbol size

## Required Output

For each C-to-ASM candidate:

- C function and symbol size
- call frequency/hotness evidence
- generated ASM symptom
- proposed register contract
- clobbers
- validation test
- expected byte/cycle impact
- ABI risk
