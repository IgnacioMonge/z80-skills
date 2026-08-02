---
name: workflow
description: Route engineering work through a global adaptive workflow with light, medium, and heavy execution levels. Use when the user invokes `$workflow`, asks to use the workflow, requests a light/medium/heavy route, wants automatic effort selection, or wants a dedicated Sol control agent to coordinate Luna workers independently of the model used by the main session.
---

# Workflow

Run without installing workflow files in the project. Respect existing `AGENTS.md`, nested instructions, Git policy, documentation, and user work.

## Select effort

Accept `$workflow light|medium|heavy|auto`, `effort=light|medium|heavy`, and equivalent natural language. An explicit level wins for the current task until the user changes it or the task ends. `auto` restores automatic selection.

When no level is explicit, choose the smallest sufficient level:

- **Light:** explanation, diagnosis, review, lookup, or small localized change with straightforward verification.
- **Medium:** cohesive multi-step or multi-file work benefiting from Sol planning and one Luna execution stream.
- **Heavy:** broad or cross-cutting work with at least two independent packages, meaningful parallelism, or independent verification.

Prefer the lower level when borderline. Change level only when evidence materially changes scope; announce the change and reason. These are workflow levels, not model reasoning-effort settings.

## Common rules

1. Read applicable project instructions and only necessary context.
2. If project instructions define route names, selection policy, or spawning
   limits, those definitions win. Map the workflow level only when unambiguous;
   otherwise report the conflict instead of overriding the project.
3. State the selected level briefly.
4. Establish acceptance criteria before non-trivial edits.
5. Trace the real code path and preserve contracts and unrelated work.
6. Make the smallest coherent root-cause change.
7. Verify proportionately and report observed evidence.
8. Inspect final diff and repository status after edits when Git is present.

Do not create project workflow scaffolding or documentation unless requested or already required by the repository.

## Compose with domain skills

When another skill names `$workflow` as its execution core:

- Workflow owns effort selection, the control plane, dispatch, repair routing,
  verification, and integration.
- The domain skill owns its modes, evidence gates, lane definitions, output
  contract, and mutation permissions.
- Domain restrictions win. A workflow level never authorizes edits, builds,
  network access, or other effects forbidden by the domain skill or project.
- In `auto`, treat domain `Focused`, `Standard`, and `Deep` classifications as
  inputs to light, medium, and heavy selection, not as a second control plane.
- In `auto`, run the required domain preflight directly at Light, then announce
  the selected level after classification. Do not report that normal selection
  as an escalation.

## Control plane

For Medium and Heavy, keep a flat agent topology so behavior does not depend on the main session's model:

1. Spawn one fresh `workflow_orchestrator` agent with `fork_turns="none"`. Its profile pins `gpt-5.6-sol`.
2. Give it a self-contained task capsule containing the request, constraints, acceptance criteria, relevant project instructions, known evidence, and protected areas.
3. Treat its response as the control plan. The main thread owns actual worker spawning, messages, waits, approvals, Git operations, and final user communication.
4. Spawn Luna workers from the main thread using the installed named profiles. Keep the Sol controller alive.
5. Return worker evidence to the same Sol controller through concise follow-ups. Let it issue the next dispatch, repair, completion, or blocker decision.
6. Accept completion only after Sol reviews the gathered evidence and the main thread checks critical integration boundaries.

The Sol controller must not spawn grandchildren or edit production files. This preserves concurrency and avoids nested-agent routing and permission problems.

## Run the route

- **Light:** work directly; do not spawn agents.
- **Medium:** read [references/medium.md](references/medium.md).
- **Heavy:** read [references/heavy.md](references/heavy.md).

If the Sol controller or requested Luna profiles are unavailable, report the exact limitation. Do not silently substitute the main model or claim a requested model ran without child-thread or runtime evidence.
