# High-Impact Pass

Start here for `scan`. Small wins are fine, but do not let them crowd out the categories that usually save real bytes.

## Attack order

1. `crt` / resident pressure (map + freshness)
2. `arch`
3. `libpull`
4. `deadcode` or `refactor`
5. `data`
6. `micro`
7. `dedup`

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
- byte tables with long runs; count packed+decoder+call glue for storage and workspace separately for RAM
- assets stored in update order instead of draw/decode order, forcing extra address math

## Black-belt pass

Only after the safe pass. Load `size-blackbook.md` for the seven dark-art
families (ROM-as-data, instruction-skip, demo flag idioms, self-destructing
init, undocumented registers, custom SDCC peepholes, string packing) and its
ordering rule; then test these ideas and either accept or reject them with
evidence:

- repeated ASM tails and n-grams: factor only when `call`/`jp` overhead is net-positive
- RST/call vectors: count vector handler bytes, call-site count, register contract, and reserved vectors
- stack blitters: count bytes and prove SP restore, interrupt state, and clipping exits
- stack-as-reader copy paths: consider only when repeated `LDI`/manual copies or sprite draws dominate and the SP save/restore plus DI cost is net-positive
- screen-specific algorithms: exploit Spectrum row/attribute layout only when target is fixed
- compression: count packed+decoder+call glue, separate RAM workspace, and load-time cost
- self-modifying/layout tricks: mark `EXPERIMENTAL` unless already an established project pattern

## Extended size playbook

After the safe attack order, load `size-playbook-extended.md` for resident/banked
accounting, CRT/startup, IM2, display geometry, Z80N, compression nets,
generative tables, buffer lifetimes, sound drivers, and 256B/4K transfers.
Still obey `hard-contract.md` — playbook items are seeds, not proof.

## External / demoscene pass

After SAFE categories, use `external-research.md` only for evidence-selected
questions. Keep notable rejected ideas; do not emit a fixed folklore checklist.
