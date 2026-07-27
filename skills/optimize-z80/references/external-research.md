# External Research

Use live search to resolve a project-specific optimization uncertainty or
discover a mechanism absent from the local corpus. External material creates
hypotheses and validation methods, not project proof.

## Trigger Gate

Research when:

- the user explicitly requests deep forum/blog/repository/demoscene discovery;
- compiler, assembler, linker, ABI, emulator, firmware, or model behavior can
  change a top candidate;
- local evidence conflicts or the dominant bottleneck lacks an adequate known
  path;
- a broad/deep pass has exhausted obvious architecture/data/toolchain wins;
- an exact local instruction sequence, helper, protocol, renderer, loader, or
  bank pattern warrants code archaeology.

Skip research when current code and fresh measurements already determine the
ranking.

## Discovery Process

1. Form bounded questions from exact local signatures: tool/version/flags,
   emitted code, helper names, map sections, addresses, target model, symptom,
   timing budget, or asset shape.
2. Search exact fragments and concepts with synonyms. Expand into English and
   relevant Spanish, Polish, Russian, Czech, or other community terms.
3. Diversify source classes:
   - toolchain source/tests/issues/commits/release notes;
   - emulator tests and real-hardware measurement projects;
   - small repositories, forks, gists, disassemblies, generators, and build
     scripts;
   - mailing lists, regional forums, personal blogs, archived sites, and
     postmortems;
   - demoscene NFOs/source and adjacent Z80 communities when transfer is
     plausible.
4. Follow citations, authors, linked source, related issues, commit history,
   forks, and archived dead links. Do not stop at search snippets.
5. Try to falsify finalists with `bug`, `wrong`, `regression`, rejected/closed
   issues, clone/model names, interrupts, timing, and compatibility failures.
6. Verify transfer assumptions: CPU, Spectrum model, memory layout, ABI,
   interrupts, paging, timing, tool version, and pressure objective.

Search only minimal normalized signatures; never upload private source or
project identifiers.

Named sites in existing knowledge are starting points, never an allowlist.
Search-engine ranking is not an evidence ranking.

## Research Card

```text
Question / exact query:
URL / access date / source revision / source class:
Claim, implementation, or measurement:
Original target/version/constraints:
Independent corroboration:
Current project anchor:
Expected effect on active bottleneck:
Local validation/measurement:
Status: SEED | EXTERNALLY CORROBORATED | LOCALLY APPLICABLE | REJECTED
```

Prefer source/tests/measurements plus independent corroboration for material
facts. A popular forum trick without a matching local site remains `SEED`.

## Zone-Specific Search

- size/resident: startup, libpull, layouts, codecs, generators, overlays;
- speed/render: profiler traces, generated blitters, screen algorithms,
  contention, table/layout tradeoffs;
- I/O/latency: protocol implementations, retry/state bugs, loader behavior,
  buffering and user-feedback strategies;
- C/codegen: compiler issues, ABI transitions, peephole rules, emitted examples;
- hardware: model matrices, emulator tests, timing captures, paging/ROM effects.

## Efficient Parallel Use

For deep demand, a `research-scout` can work independently from local lanes.
Give it bounded questions and a compact project signature. It returns at most
five research cards ranked by decision impact and verification cost.

Budget at most three cards for Standard and five total for Deep; verify only
the two or three that can change the optimization frontier.

Without a delegate, research the top unresolved question, reassess the
frontier, and expand only if the answer changes it.

If browsing is unavailable, record exact pending queries and continue with
local evidence; do not invent external support.

## Stop Rules

Stop when independent source classes converge and local validation is clear,
when results repeat folklore, when no local anchor emerges after vocabulary and
language expansion, or when further search cannot change the top experiments.

Report provenance with the affected candidate, but base confidence and ranking
on current local evidence.
