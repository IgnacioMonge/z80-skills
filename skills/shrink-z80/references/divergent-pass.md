# Divergent Shrink Pass

Use this pass to avoid shallow reports that only find dedup or 1-byte substitutions. It is a hypothesis generator, not a replacement for byte counting.

## When to run

- Run for `scan`, `diverge`, `arch`, broad `refactor`, broad `data`, or any user request for ambitious/demoscene/forum-level savings.
- Rerun if the current shortlist is mostly micro wins under 20 bytes and no larger levers have been disproven.
- Skip only when the user explicitly asks for a narrow local check.

## Process

1. Establish the project profile first: target, build flags, `.map`/`.lst`, CODE/BSS pressure, stack gap, ABI constraints, and available scripts.
2. Diverge before criticizing. If Agent tools are available, spawn isolated branches in parallel; otherwise run the frames separately in your own notes and say no Agent isolation was available.
3. Give each branch the same scope and constraints. Tell it to generate candidates only, not rank or reject.
4. Merge candidates by underlying mechanism, not by surface syntax.
5. Score each candidate:
   - `bytes`: expected net saving. 10 = 500B+, 8 = 150-500B, 6 = 50-150B, 4 = 20-50B, 2 = under 20B.
   - `viability`: can ship without heroic testing.
   - `proof`: can byte impact and equivalence be measured locally.
   - `fit`: matches the actual codebase and user constraints.
   - `risk`: lower runtime/ABI/timing risk scores higher.
6. Investigate the top candidates until each is promoted, downgraded, or rejected. Never report branch output as a saving without evidence.

## Frames

Pick 5 frames for a normal pass. Always include at least one wild frame.

| Frame | Ask |
|---|---|
| System architect | What representation, state machine, protocol layer, or call graph can disappear? |
| Linker/libpull hunter | Which single C idiom or API call deletes an entire library routine or CRT path? |
| Data compressor | Which table, string set, font, screen asset, or buffer can be tokenized, narrowed, mirrored, generated, or overlapped? |
| Code/data co-designer | Would moving work between code, data, build-time generation, and runtime loops reduce total bytes? |
| Speedrunner | What legal shortcut removes setup, dispatch, checks, or repeated ceremony? |
| Hardware/page thinker | What changes if high bytes, screen pages, alignment, block ops, or pointer locality are treated as the main constraint? |
| Inversion | How would you intentionally make this binary larger? Which causes can be removed? |
| 10-year maximalist | What big redesign would delete whole categories of code if build tooling and tests existed? |

## Ambition Checklist

Before accepting a scan as complete, check:

- Can a generic routine be specialized because all call sites pass the same shape of data?
- Can repeated command/response code become a table, or can an existing table become smaller than the code that consumes it?
- Can strings use prefix/suffix injection, token dictionaries, or build-time packing?
- Can a large table become a smaller table plus computation, such as nibble-table CRC or quadrant mirroring?
- Can buffers share lifetime, move to stack, narrow type, or become generated scratch?
- Can any C operator, varargs, stdlib call, or type promotion delete a whole libpull when rewritten?
- Can data be precomputed offline, compiled as a smaller representation, or generated into tighter ASM?
- Can fall-through, tail merging, page-local indexing, or call-vector amortization remove repeated ceremony?
- Can a feature be represented as a bitset, flags byte, enum nibble, packed trie, or state transition table?
- Can a user-visible tolerance, such as animation precision or debug text, buy an `AGGRESSIVE` but acceptable saving?

## Reporting

- Add a `Divergent shortlist` section for ambitious candidates that were investigated.
- Mark each as `CONFIRMED SAVING`, `DESIGN TRADEOFF`, `SPECULATIVE`, or `Rejected`.
- For rejected ideas, include the concrete blocker: negative byte count, ABI break, flag dependency, timing risk, stack pressure, build dependency, or maintenance cost.
- If no high-impact idea survives, say why. A report with only micro wins must prove larger categories were checked.
