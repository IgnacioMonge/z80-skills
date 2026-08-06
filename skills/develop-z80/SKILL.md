---
name: develop-z80
description: Specification-driven product and engineering workflow for turning a Z80, ZX Spectrum, or ZX Spectrum Next idea into a verified implementation. Use when exploring or defining a game, demo, tool, feature, or port; choosing classic ZX versus Next targets; writing functional and technical specifications; planning milestones and architecture; breaking work into dependency-aware tasks; implementing an authorized milestone or task; tracking multi-session progress; or validating the finished result against explicit product and technical acceptance criteria.
---

# Develop Z80

Lead the user from idea to verified code without requiring SDD knowledge or
workflow commands. Keep one source of truth and stop scope growth at playable or
otherwise inspectable product checkpoints.

## Workflow Core

Apply the sibling `$workflow` skill at `../workflow/SKILL.md` as the execution
control plane. Workflow owns effort, dispatch, repair, verification, and
integration; this skill owns SDD stages, evidence, the dossier, Z80 decisions,
and mutation gates. A workflow route never widens those gates. If the sibling
skill is unavailable, report the limitation and continue directly without
claiming delegated execution.

## Modes

- `auto` (default): infer the earliest incomplete stage and progress to the
  current authorization ceiling.
- `idea`: shape the concept and smallest convincing product slice.
- `spec`: define behavior, constraints, and acceptance criteria.
- `plan`: choose technical direction, milestones, risks, and validation.
- `tasks`: produce the ready backlog for the active milestone.
- `implement`: execute one authorized task or the active milestone.
- `verify`: reconcile an implementation with its acceptance criteria.
- `help`: explain the lifecycle, mutation boundary, and a minimal invocation;
  do not inspect or edit a project.

Treat a named mode as a ceiling, not a step the user must operate. In `auto`,
never ask the user to choose a mode, stage, methodology, or next task.

## Routing

For every real task, read `references/hard-contract.md` first. Then load only
the references selected by current evidence:

| Signal | Read |
| --- | --- |
| Idea, spec, plan, tasks, or implementation sequencing | `references/lifecycle.md` |
| Create, resume, revise, or persist the source of truth | `references/dossier.md` |
| Target, CPU, video, memory, timing, I/O, delivery, or toolchain decision | `references/platform-profile.md` |
| Baseline, implementation, milestone gate, emulator/hardware check, or final reconciliation | `references/verification.md` |

Infer the earliest incomplete stage from the request, repository, dossier, and
current evidence. Ask one focused question only when a missing product decision
would materially change scope, architecture, compatibility, or visible behavior;
otherwise label the assumption and continue.

## Domain Demand

Classify after the initial concept and project inspection, then pass the signal
to `$workflow` when project route policy permits automatic selection:

- **Focused**: one bounded feature or task, one target, and one milestone. Light
  normally suffices.
- **Standard**: one vertical slice crossing several components or one material
  platform unknown. Medium can own one cohesive stream.
- **Deep**: a greenfield product spanning several domains or milestones,
  multiple targets, banking/MMU, ISR/timing, or a material generated-asset
  pipeline. Heavy can investigate independent evidence lanes while keeping
  implementation slices bounded.

An explicit workflow level and project route instructions win. Reduced agent
capacity reduces parallelism, not evidence or checkpoint requirements.

## Product-Code Apply Gate

Authorize product-code mutation only when the request explicitly names product
implementation, such as “implement T-03”, “build the first playable milestone”,
or “add joystick support to the game”. Generic verbs aimed at documents or
decisions—“create a design”, “add to the dossier”, “change the scope”—do not
authorize product-code edits. Interpret authorization by object and bounded
scope, never by verb alone.

Before editing, require a relevant baseline, an accepted specification, linked
acceptance criteria, a ready task, one active milestone, and rollback. Before
the first greenfield product-code mutation, show scope, non-goals, all active ACs,
and the first milestone, then record explicit user acceptance. An `ASSUMED`
specification permits planning and disposable spikes, never that first mutation.
A broad “build this game” authorizes the first playable vertical slice, not every
future milestone.

At each milestone boundary, present the runnable or inspectable result and pause
for one product checkpoint. Continue automatically only when the user explicitly
authorized end-to-end continuation in the current session or the dossier records
a matching session ID and a positive remaining milestone limit. Never inherit
auto-advance authorization into a later session.

## Handoffs

- Hand correctness, ABI, ISR, corruption, or hardware-risk investigation to
  `audit-z80` before implementation when it can veto the slice.
- Hand ownership, dependency direction, source layout, or runtime placement to
  `organize-z80` when topology is the primary risk; consume its approved design
  rather than creating a competing one.
- Hand size-only decisions to `shrink-z80` and competing size/speed/RAM/rendering
  decisions to `optimize-z80` before promoting those claims into the spec.

Keep the dossier and acceptance IDs authoritative across handoffs. Other skills
supply evidence or approved decisions; they do not silently change product scope
or authorize implementation.

## Output Contract

Return a decision artifact, not a workflow transcript:

- mode ceiling, inferred stage, demand, targets, and references loaded;
- effective mutation-boundary class and specification-acceptance state;
- dossier path or `conversation-only`, plus evidence classes and open decisions;
- changed product/spec decisions, affected acceptance criteria, and task status;
- checks as `PASS`, `FAIL`, `BLOCKED`, or `NOT RUN` with fresh evidence;
- product checkpoint, residual risk, rollback, and next automatic action.

Prefer the smallest idea, dossier, task set, and implementation that proves the
intended experience. Never weaken criteria or widen the active milestone merely
to obtain a pass.
