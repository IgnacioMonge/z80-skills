# C And Memory Checks

Read this reference for `c`, `memory`, or any `full` audit that touches generated C behavior or RAM pressure.

## C semantics to verify

- Integer promotions: watch for mixed signed or unsigned comparisons and accidental 16-bit work
- Pointer arithmetic: multi-byte element indexing can hide expensive or wrong address math
- Array and buffer bounds: verify write lengths, terminators, and stack-local buffer size
- `const` correctness: string literals and read-only tables must not be passed to mutating code
- Operator drag: `*`, `/`, and `%` can pull in library helpers and also hide type-width bugs
- Switches and bool logic: verify the generated intent, not just the source appearance
- Blocking calls in input/render/audio paths are UX defects when they can drop keys, tear frames, or stall feedback
- `strlen`, `strcmp`, `memcpy`, and `memset` inside small loops deserve generated-ASM inspection; they can be both slow and size-expensive

## Memory reality

- In 48K flat builds, `__BSS_END_tail` versus stack-top symbols matters more than the TAP file size
- Fixed-address RAM reduces usable margin even when BSS looks safe
- Overlay loaders, shared scratch buffers, and ring buffers can turn "harmless" state into real corruption
- Worst-case stack depth includes ISR overhead, nested calls, and hand-written register saves
- Frame buffers, clipping buffers, decompressor workspaces, UART buffers, and screen scratch regions must be checked for non-overlapping lifetimes, not just separate names

## Fixed-address checklist

Verify any use of:

- Screen or attribute RAM
- Printer buffer or other hijacked system areas
- UDG or ROM-adjacent scratch space
- Overlay slots or loader scratch regions
- esxDOS-sensitive areas if the code does RST 8 or file work

## Generated-code sanity

When the C looks suspicious:

- Read the generated `.asm` or `.lst` if available
- Check that pointer tables and string tables were emitted correctly
- Confirm the compiler kept operations at 8-bit width when the source seemed to expect that
- Confirm jump tables, switch cascades, and pointer-table initializers match the C source when a logic bug would be user-visible
