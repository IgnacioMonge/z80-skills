# C-Generated Size Patterns

Use this file for C-heavy shrink work and any `libpull` pass.

## High-yield patterns

- `*`, `/`, and `%` can drag library helpers into the binary
- integer promotions widen work to 16-bit and can make trivial expressions expensive
- `switch` can be smaller as a cascade or as a table depending on case count
- struct indexing and wide array indexing can multiply or materialize offsets
- `const` data belongs in `CODE`, not duplicated in writable sections
- manual boolean masks are usually smaller than C bitfields under SDCC

## Source-level rewrite themes

- replace multiply or divide by powers of two with shifts or masks
- replace small constant multiplies with add or shift sequences when safe
- keep counters and indexes 8-bit when the real range allows it
- avoid one-callsite wrappers that only rename an existing library call
- review string formatting or parsing code for heavy stdio drag
- replace repeated switch bodies with token tables or function-less dispatch when table bytes amortize
- pack pointer tables into byte offsets when all targets share a page or base
- hoist invariant `strlen` or table lookups out of loops in input/render/update paths
- split rare paths from hot paths so common code avoids wide arithmetic and helper calls

## Verification

- check the `.map` before claiming a libpull saving
- if a single source-level operator is the only trigger, say that explicitly
- if the saving depends on dead code elimination or helper removal, label it `REQUIERE BUILD`
- inspect generated `.asm` before trusting that SDCC found the obvious 8-bit or strength-reduction form
