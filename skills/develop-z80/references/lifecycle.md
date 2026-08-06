# SDD Lifecycle

Run the stages autonomously up to the selected mode ceiling and mutation gate.

## Contents

- [Smallest Path](#smallest-path)
- [Idea](#idea)
- [Specification](#specification)
- [Plan](#plan)
- [Tasks](#tasks)
- [Implementation Sequence](#implementation-sequence)
- [Parallelization](#parallelization)
- [Stage Transition](#stage-transition)

## Smallest Path

For a small idea, prefer the five-minute shape:

1. one-paragraph concept and explicit non-goals;
2. three to five acceptance criteria;
3. one runnable or inspectable milestone;
4. no more than three cohesive ready tasks;
5. one verification matrix and product checkpoint.

Expand only when platform evidence, risk, or product scope requires it.

## Idea

- Restate the idea as an outcome for a player or user, not a technology list.
- Identify the core loop or value, intended feel, smallest convincing slice, and
  non-goals.
- Classify the work as greenfield, feature, port, remake, tool, demo, or spike.
- Surface only decisions that can change product or architecture: targets,
  controls, display model, delivery, toolchain, and hard limits.
- Challenge incompatible or expensive premises and recommend the smallest slice
  that proves the experience.

Finish with a concept brief, evidence classes, and at most one blocking product
question. Continue automatically when assumptions are safe and reversible.

## Specification

- Define flows, controls, states, rules, failure behavior, and relevant edge
  cases in observable language.
- Split acceptance into `AC-P-*` product behavior and `AC-T-*` technical
  contracts. Attach a verification method to every criterion.
- Define target-specific behavior, interfaces, preserved behavior, scope, and
  non-goals.
- Use exact byte, RAM, stack, timing, loading, or compatibility budgets only when
  supplied or measured.
- Mark unresolved decisions; do not conceal them in architecture prose.

Advance only when the smallest slice is implementable and every acceptance
criterion can produce evidence.

## Plan

1. Inspect the existing execution, data, build, and asset paths before proposing
   structure.
2. Choose the simplest toolchain and architecture satisfying the specification.
3. Identify seams only where needed: loop/state, rendering, input, audio,
   storage, interrupts, memory placement, assets, and generated data.
4. Order vertical milestones that each yield a runnable or inspectable result.
5. Put the riskiest unknown behind the cheapest early spike or measurement.
6. Give every milestone a completion gate, product checkpoint, and rollback.

If ownership or runtime placement dominates the risk, route to `organize-z80`
and consume its decision before finalizing the plan.

## Tasks

Create tasks only for the active milestone. Give each task:

- stable ID and type: `SPIKE`, `IMPL`, or `VERIFY`;
- one concrete outcome and linked acceptance criteria;
- dependencies and `TODO`, `READY`, `IN PROGRESS`, `BLOCKED`, or `DONE` status;
- risk or learning objective;
- maximum ownership surface to prevent scope creep;
- the smallest completion check and required evidence.

Use `SPIKE` to retire a named unknown cheaply; discard prototype code unless its
promotion gate is explicit. Use `VERIFY` for independent evidence, not as a way
to postpone basic checks from `IMPL`.

Do not fragment mechanical edits into micro-tasks. Mark `DONE` only after the
linked check passes.

## Implementation Sequence

Within an authorized milestone:

1. Select the next `READY` task.
2. Freeze the relevant baseline and inspect repository status.
3. Trace the real execution/data path and shared callers.
4. Implement the smallest coherent slice inside the task's surface ceiling.
5. Run its check and update evidence and status.
6. Continue to the next ready task until the milestone gate, a product decision,
   or a blocker is reached.

Keep generated output derivative. Edit its source, generator, schema, rule, or
manifest rather than generated files.

## Parallelization

Parallelize tasks only when dependencies are satisfied, ownership surfaces do
not overlap, and they do not share a mutable build, artifact, emulator, device,
or dossier section. Otherwise keep one implementation stream.

For Deep demand, brief `$workflow` with bounded lanes such as:

- platform/evidence investigation;
- one vertical-slice implementation owner;
- independent acceptance verifier using the dossier and raw artifacts.

Never split product decisions among agents. The main thread owns dossier
integration, user questions, mutation authorization, and milestone checkpoints.

## Stage Transition

Advance stages automatically when the current gate passes. Stop only at the
mode ceiling, mutation boundary, material product decision, product checkpoint,
real blocker, explicit user stop, or exhausted authorized scope.
