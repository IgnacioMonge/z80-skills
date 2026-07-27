# External Research

Browse to resolve a project-specific uncertainty, not to decorate the report.
Web material is a search seed; `hard-contract.md` still requires current local
evidence for a finding.

## Trigger Gate

Research when at least one condition holds:

- the user explicitly requests deep, forum, blog, repository, or demoscene
  discovery;
- an ABI, compiler/assembler version, firmware, opcode, flag, emulator, or
  hardware behavior can change a top finding;
- source, generated output, manuals, or emulator behavior contradict;
- a broad/deep audit has a material blind spot after local checks;
- a local code shape is unusual enough that exact-code archaeology may reveal
  its contract or known failure mode.

Skip research for a focused issue already provable from current code.

## Discovery Ladder

1. **Form a local question.** Include an exact opcode sequence, symbol, emitted
   pattern, tool/version, hardware model, symptom, or address.
2. **Search wide.** Vary terminology and language; use English plus relevant
   Spanish, Polish, Russian, Czech, or community vocabulary. Search exact code
   fragments as well as concepts.
3. **Diversify source classes.** Do not stay on a fixed allowlist:
   - compiler/assembler source, tests, issues, commits, blame, and release notes;
   - emulator test suites and hardware-derived measurements;
   - mailing lists, archived forums, Usenet mirrors, personal technical blogs,
     disassemblies, and postmortems;
   - demoscene release notes/NFOs and linked source or generators;
   - regional communities and calculator/MSX/CPC/SMS circles when a CPU-level
     idea may transfer.
4. **Snowball.** Follow cited code, author profiles, forks, related issues,
   thread pages, archived dead links, and repositories named by the first
   useful source.
5. **Try to falsify.** Repeat the strongest query with `bug`, `wrong`,
   `regression`, rejected/closed issues, clone/model names, interrupts, and
   timing counterexamples.
6. **Verify transfer.** Record CPU variant, Spectrum model, toolchain version,
   ABI, interrupt assumptions, memory layout, and timing conditions before
   mapping the idea to this project.

Search only minimal normalized signatures; never upload private source or
project identifiers.

Search surfaces such as SourceForge compiler trackers, small personal retro
blogs, GitHub/GitLab gists and issue histories, Pouët/Demozoo notes, zx-pk,
speccy.pl, and foro.speccy.org are examples, not boundaries.

## Research Card

Keep only material leads:

```text
Question:
Exact query / access date / source revision:
Source URL:
Source class:
Claim or code shape:
Target/version/preconditions:
Independent corroboration:
Current project anchor:
Local verification:
Status: SEED | EXTERNALLY CORROBORATED | LOCALLY APPLICABLE | REJECTED
```

Prefer a primary artifact plus independent corroboration when the external fact
is important. A forum consensus without code, tests, or a project-local match
remains `SEED`.

## Efficient Parallel Use

For deep demand, a `research-scout` may run independently while code lanes
inspect the immutable baseline. Give it only the bounded questions and project
signature. It returns at most five research cards, ordered by ability to
change a finding. It must not read other agents' conclusions.

Budget at most three cards for Standard and five total for Deep; verify only
the two or three that can still change a finding.

Without an available delegate, research only the top unresolved question, then
reassess before expanding.

If browsing is unavailable, preserve the exact pending queries and continue
with local evidence; do not fabricate search results.

## Stop Rules

Stop when:

- independent source classes converge and a local verification path exists;
- additional results repeat the same unsourced claim;
- no project-local anchor appears after query and vocabulary expansion;
- the answer cannot change a finding, confidence, or residual-risk statement.

Report external provenance near the affected hypothesis, but cite current code
or fresh artifacts as the finding evidence.
