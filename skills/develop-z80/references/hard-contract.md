# Hard Contract

Apply this contract to every real `develop-z80` task.

## Contents

- [Evidence and Certainty](#evidence-and-certainty)
- [Mutation Boundary](#mutation-boundary)
- [Contract Preservation](#contract-preservation)
- [Product and Technical Integrity](#product-and-technical-integrity)
- [Multi-Target Gate](#multi-target-gate)
- [Completion Gate](#completion-gate)

## Evidence and Certainty

Classify every material platform, product, architecture, and completion claim:

- `VERIFIED`: directly supported by current source, current documentation, a
  fresh artifact, or an observed run.
- `LIKELY`: strong project-local evidence exists but one bounded check remains.
- `ASSUMED`: an explicit working premise chosen to maintain progress.
- `UNVERIFIED`: the behavior or target was not inspected or exercised.
- `NEEDS BUILD`: confirmation requires a missing or stale generated artifact.

Record the evidence anchor and freshness. Treat generic Z80 advice, remembered
Next capabilities, file names, prior reports, and emulator behavior as candidate
context, not proof. Never promote a preference—Layer 2, IM2, Z80N, C, ASM, a
framework, or a memory scheme—into a platform fact.

Classify delivery risk separately: `BLOCKER` prevents a safe decision or
milestone; `HIGH` can invalidate product behavior or a preserved contract;
`MEDIUM` can cause bounded rework or weaken verification; `LOW` is contained and
reversible.

## Mutation Boundary

Declare one effective class before every Medium or Heavy dispatch:

- `help`, `idea`, `spec`, `plan`, `tasks`, and non-mutating `verify` are
  `primary-tree read-only`.
- A spike, measurement, emulator/profiler run, or build that writes unapproved
  artifacts is `disposable-worktree-only`. Use a verified detached worktree and
  invoke `<skill-dir>/../../scripts/run_in_worktree.py`, passing
  `--primary <primary-root> --worktree <worktree-root> -- <command>`.
  Never pass the temporary directory as a wrapper `cwd`: a rejected,
  substituted, or unverifiable `cwd` is a hard failure, never permission to
  retry the gate in the primary tree.
- An explicitly requested dossier/status update or an `implement` operation that
  passes every gate below is `authorized primary-tree mutation`, limited to its
  declared files and ownership surface.

Record the class in the workflow capsule. Dispatch only roles compatible with
that class; a route or agent never promotes it.

Keep idea shaping, specification, planning, task breakdown, and review read-only
with respect to product code. A requested dossier write may edit only the
canonical dossier and project routing/status pointers permitted by repository
instructions.

Enter product implementation only when all conditions hold:

1. The user explicitly requests implementation of named product behavior, a task
   ID, a milestone, or the first vertical slice of an accepted specification.
2. The affected acceptance criteria and target profile are present.
3. The active task is `READY`, dependencies are satisfied, and its maximum
   surface and rollback are known.
4. Repository instructions, dirty state, branch/worktree policy, build entry
   points, and the cheapest relevant baseline have been inspected.

For a greenfield product's first primary-tree code mutation, require
`Spec accepted: user` from the current conversation after presenting scope,
non-goals, active `AC-P-*`/`AC-T-*`, and the first milestone. `Spec accepted:
assumed` permits planning and `disposable-worktree-only` spikes but never primary
product-code mutation. Reset acceptance to `pending` after a material spec
revision.

Interpret authorization by object, not verb alone. “Create a plan”, “add an
assumption”, or “change AC-P-02” authorizes documentation or decisions only.

Do not publish, merge, push, tag, delete branches, or change external systems
without separate explicit authorization.

## Contract Preservation

Treat the following as public until current evidence proves otherwise:

- exported C functions, assembly labels, vectors, hooks, calling conventions,
  registers, flags, stack layout, and error signaling;
- interrupt mode/state, ISR residency, bank/page state, firmware calls, ports,
  NextRegs, DMA ownership, and timing windows;
- sections, absolute addresses, binary headers, loader offsets, memory maps,
  banks, MMU pages, overlays, and generated-data offsets;
- build entry points, configuration, public symbols, asset/save/file formats,
  controls, and maintained target behavior.

Require explicit authorization and a compatibility, migration, or versioning
decision before breaking a contract. Keep unrelated cleanup, optimization,
formatting, renaming, dependency upgrades, and toolchain changes outside the
active milestone.

## Product and Technical Integrity

- Maintain product acceptance criteria as `AC-P-*` and technical criteria as
  `AC-T-*`. Never substitute one class for the other.
- Do not mark a product criterion passed from compilation, a map, or a static
  estimate alone.
- Do not mark a technical timing, memory, ABI, or compatibility criterion passed
  from subjective gameplay alone.
- Preserve failing evidence. Do not bless new output, weaken a budget, delete a
  check, or revise a requirement merely to match the implementation.

## Multi-Target Gate

Model every maintained target and configuration affected by the slice. Do not
generalize from one successful target, emulator, clock, memory layout, or input
device to another. Label unbuilt targets `NEEDS BUILD` and unexercised runtime
behavior `UNVERIFIED`.

## Completion Gate

Call a task or milestone complete only when:

- its linked acceptance checks pass or remaining failures are explicit;
- fresh artifacts correspond to the current source, target, configuration, and
  build recipe;
- product behavior has inspectable evidence and required human feedback;
- unintended ABI, memory, timing, target, and format changes are absent or named;
- the dossier, task status, decision log, and verification record match reality;
- rollback remains possible and the full diff and repository status were read.
