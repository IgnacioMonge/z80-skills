# Change Review

Use for `diff` mode: the correctness risk a change set introduces or exposes,
with no observed failure driving the work. Obey `hard-contract.md`; the primary
tree stays read-only.

## Boundary

- An observed failure with unresolved causality, including a regression against
  a known baseline, belongs to `$debug-z80`.
- A review without a Z80 correctness question (naming, duplication, structure,
  general code quality) belongs to `$workflow`.

## Scope

1. Resolve the range. An explicit `<base>..<head>` wins. Otherwise compare the
   merge base of `HEAD` and the default branch (the remote `HEAD`, else `main`
   or `master`) against the working tree, so committed and uncommitted changes
   both count. Never default to `HEAD~1`; it drops earlier commits of the
   change. An empty range ends the audit with that statement.
2. Read the changed hunks with enough context to see each enclosing function or
   routine. Commit messages, PR or change descriptions, and comments asserting
   safety are search seeds, not proof.
3. Name each risk the change creates, then run one focused check per named risk
   outside the hunks. Do not crawl unrelated code. Classify demand with the gate
   in `SKILL.md` from the named risks, not from the diff size.

## Named-risk expansion

| Change | Required check |
| --- | --- |
| Signature, prototype, calling convention, or preserved-register use | Every caller and callee across C/ASM, including inline ASM, jump tables, and function pointers |
| Variable or buffer shared with an ISR | Every access, its atomicity, and the DI/EI or interrupt-mode context |
| Code or data size, section, `org`, alignment, or link order | Fresh `.map`: stack/BSS gap, fixed addresses, overlay/bank slots, contended-memory boundaries |
| C on a hot path or ABI boundary, compiler flags, or copt rules | Generated `.asm`/`.lst` for the changed functions |
| Ports, paging, ROM/firmware calls, or timing-sensitive loops | Target and model constraints from `spectrum-hardware-esxdos.md` |

When a check needs base-versus-head artifacts, build the base in a disposable
worktree per `hard-contract.md` and compare the same targets and flags. Without
both builds, mark the dependent item `NEEDS BUILD`.

## Findings

- Report defects the change introduces or makes reachable. Report a pre-existing
  defect only when the change worsens or exposes it; list other incidental ones
  under coverage as out of scope, with their anchor.
- Apply `promotion-gate.md` and `reporting.md`, including the change verdict.
