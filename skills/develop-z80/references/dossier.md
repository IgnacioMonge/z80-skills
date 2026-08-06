# SDD Dossier

Keep one compact source of truth for the idea, specification, plan, tasks, and
verification state.

## Contents

- [Canonical Location](#canonical-location)
- [Minimal Template](#minimal-template)
- [Change Control](#change-control)
- [Minimal Example](#minimal-example)

## Canonical Location

1. Read project instructions and reuse an existing feature/specification format.
2. Keep small one-session work in the conversation.
3. For authorized multi-session work without a convention, use one
   `specs/<project-or-feature>.md` file.
4. Record the canonical path in every handoff. Do not mirror the same fields into
   several documents.

When a repository uses `agent_docs/project_progress.md` or
`agent_docs/latest_session_work.md`, keep requirements, acceptance criteria,
decisions, and feature tasks canonical in the feature dossier. Let project
progress own deployment sequencing and let the session handoff point to the
dossier and next ready task. Update those project documents only when their
instructions and current working state permit it.

## Minimal Template

```markdown
# <Project or Feature>

Stage: idea | spec | plan | tasks | implement | verify
Mode ceiling: auto | idea | spec | plan | tasks | implement | verify
Demand: Focused | Standard | Deep
Status: ACTIVE | BLOCKED | AT PRODUCT CHECKPOINT | COMPLETE
Canonical dossier: <path | conversation-only>
Spec accepted: pending | assumed | user
Spec acceptance evidence/session: <message/session anchor | none>
Auto-advance milestones: no
Auto-advance session: none
Auto-advance remaining: 0

## Goal
Audience/experience:
Core loop or value:
Smallest convincing slice:
Non-goals:

## Target Profile
Targets/toolchain/delivery:
Platform decisions:
Deferred decisions:

## Evidence Ledger
ID | claim | class | risk | anchor/freshness

## Specification
Behavior and edge cases:
Constraints and preserved contracts:

## Acceptance Criteria
ID | Product/Technical | behavior or contract | verification method | status/evidence

## Milestones
ID | runnable/inspectable outcome | completion gate | rollback | status

## Tasks
ID | SPIKE/IMPL/VERIFY | outcome | deps | risk/learning | surface ceiling | AC links | check | status/evidence

## Decisions and Revisions
ID | reason/evidence | affected AC/tasks/milestones

## Verification and Next Action
Checks:
Product checkpoint:
Residual risks:
Next ready task:
```

Omit empty sections and columns that cannot affect execution. Preserve stable
IDs after creation; retire rather than renumber them.

`Spec accepted: assumed` supports specification, planning, tasks, and disposable
spikes only. Before the first greenfield product-code edit, present scope,
non-goals, active ACs, and the first milestone; change the value to `user` only
after explicit confirmation and record its message/session anchor. A material
spec revision resets it to `pending`.

Persist auto-advance only with a runtime-provided session identifier and a
positive maximum count. Decrement `Auto-advance remaining` after every crossed
milestone boundary and reset all three auto-advance fields when it reaches zero
or the session ends. If no stable session identifier is available, keep any
end-to-end authorization in the current conversation and leave the dossier at
`no`; a later session never inherits it.

## Change Control

When discovery invalidates a material requirement, create a `SPEC REVISION`
entry before changing implementation:

`Material` means a change to any user-gated surface named in step 6.

1. State the trigger and evidence class.
2. Describe the old and proposed behavior.
3. List affected `AC-P-*`, `AC-T-*`, tasks, targets, and milestones.
4. Reopen completed tasks whose evidence no longer proves the revised criterion.
5. Re-plan only the invalidated part of the active milestone.
6. Ask the user when the revision changes visible behavior, product scope,
   compatibility, data/formats, or a previously chosen trade-off. Otherwise log
   the bounded implementation decision and continue.
7. For every revision gated by step 6, reset `Spec accepted` to `pending` until
   the user explicitly accepts the revised specification.

Never edit historical evidence to make the revision appear to have passed
earlier. Keep the reason and replaced decision visible.

## Minimal Example

```markdown
# 48K Scroll Shooter Slice
Stage: tasks
Demand: Standard
Spec accepted: pending
Auto-advance milestones: no
Auto-advance session: none
Auto-advance remaining: 0

Goal: one responsive 60-second playable loop with one enemy type.
Non-goals: bosses, scrolling map editor, 128K audio, persistent scores.

AC-P-01 | ship moves and fires with defined controls | emulator playthrough | TODO
AC-T-01 | frame update fits the budget established by T-01 | measured frame probe | NEEDS BUILD

M1 | playable room with ship, shot, enemy, collision | AC-P-01 + AC-T-01 | revert M1 | ACTIVE
T-01 | SPIKE | measure rendering approach | none | closes timing unknown | renderer only | AC-T-01 | probe | READY
T-02 | IMPL | implement core loop | T-01 | medium | loop/input/render | both | playthrough + probe | TODO
T-03 | VERIFY | capture milestone evidence | T-02 | low | artifacts only | both | matrix | TODO
```
