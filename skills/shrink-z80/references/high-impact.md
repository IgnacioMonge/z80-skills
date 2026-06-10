# High-Impact Pass

Start here for `scan`. Small wins are fine, but do not let them crowd out the categories that usually save real bytes.

## Attack order

1. `arch`
2. `libpull`
3. `deadcode` or `refactor`
4. `data`
5. `micro`
6. `dedup`

## Arch checks

Look for:

- sequential blocks that should collapse into a loop and table
- repeated protocol send or parse skeletons
- shared suffixes or prefixes that can move into a helper
- state machines that can become data-driven
- buffers or scratch regions whose lifetimes do not overlap
- object/render/update pipelines where a single table can replace parallel switch/case code
- repeated command/protocol/screen emitters that can become token streams or bytecode
- layout changes that create fall-throughs, shared suffixes, shorter branches, or bank/locality wins

Architecture changes can subsume later dedup or micro wins. Account for that dependency in the report.

## Libpull checks

Prioritize:

- `*`, `/`, `%` on non-constant operands
- `printf`, `sprintf`, `snprintf`, `scanf`
- `malloc`, `free`
- string and memory helpers that are linked for a single call site

Use the `.map` to prove the routine is actually present before claiming the saving.

## Deadcode and refactor

- verify truly dead functions with textual references, map presence, and indirect-use sanity
- look for repeated epilogues, wrappers, and one-use helpers
- measure whether a helper saves bytes after `call` and `ret` overhead

## Data

- large tables
- duplicate strings
- read-only data sitting in `DATA` instead of `CODE`
- boolean flags spread across multiple bytes
- buffers larger than the real worst case
- pointer tables where byte offsets, packed deltas, or token streams beat 16-bit addresses
- sprite/text/screen tables that can be generated, mirrored, delta-coded, RLE-packed, or ZX0/LZSA-compressed
- assets stored in update order instead of draw/decode order, forcing extra address math

## Black-belt pass

Only after the safe pass, test these ideas and either accept or reject them with evidence:

- repeated ASM tails and n-grams: factor only when `call`/`jp` overhead is net-positive
- RST/call vectors: count vector handler bytes, call-site count, register contract, and reserved vectors
- stack blitters: count bytes and prove SP restore, interrupt state, and clipping exits
- screen-specific algorithms: exploit Spectrum row/attribute layout only when target is fixed
- compression: count decoder, packed bytes, workspace, call sites, and load-time cost
- self-modifying/layout tricks: mark `EXPERIMENTAL` unless already an established project pattern
