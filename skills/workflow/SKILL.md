---
name: workflow
description: Route engineering work through a portable adaptive workflow with light, medium, and heavy execution levels. Use when the user invokes `$workflow`, asks to use the workflow, requests a light/medium/heavy route, wants automatic effort selection, or wants bounded parallel workers coordinated by the main agent.
---

# Workflow

Run without installing workflow files in the project. Respect existing `AGENTS.md`, nested instructions, Git policy, documentation, and user work.

## Select effort

Accept `$workflow light|medium|heavy|auto`, `effort=light|medium|heavy`, and equivalent natural language. An explicit level wins for the current task until the user changes it or the task ends. `auto` restores automatic selection.

When no level is explicit, choose the smallest sufficient level:

- **Light:** explanation, diagnosis, review, lookup, or small localized change with straightforward verification.
- **Medium:** cohesive multi-step or multi-file work that one agent can complete in an ordered stream with proportionate verification.
- **Heavy:** broad or cross-cutting work with at least two concrete, bounded, independent workstreams where parallelism or independent comparison materially improves speed or required coverage.

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
- Before any Heavy dispatch, classify the effective mutation boundary:
  - **primary-tree read-only:** use only `explorer` or read-only `default`
    roles; do not spawn an implementer.
  - **disposable-worktree-only:** an executor may edit or build only inside a
    verified, domain-gated disposable worktree, never the primary tree.
  - **authorized primary-tree mutation:** an executor may edit and run checks
    only within its assigned surface and effective authorization.
  The most restrictive applicable user, project, or domain rule determines the
  class.
- In `auto`, treat domain `Focused`, `Standard`, and `Deep` classifications as
  inputs to light, medium, and heavy selection, not as a second control plane.
- In `auto`, run the required domain preflight directly at Light, then announce
  the selected level after classification. Do not report that normal selection
  as an escalation.

## Heavy control plane

For Heavy, use the portable roles in
[references/roles.md](references/roles.md) and keep a flat topology:

1. Keep the main thread as the controller; do not spawn a separate planning or
   controller agent.
2. Spawn only when at least two concrete, bounded, independent workstreams can
   proceed concurrently or independent comparison is required.
3. Start independent workers together. Use at most two by default; add a third
   only for a genuinely separate workstream.
4. Give every worker a self-contained task capsule containing the objective,
   exact scope and inputs, constraints, acceptance criteria, protected areas,
   required evidence or artifact, and stop condition.
5. Assign one owner to each mutable file set. Parallel implementers may write
   only to disjoint surfaces.
6. Continue useful main-thread work before waiting, then integrate worker
   evidence once at the smallest shared boundary.
7. Run deterministic checks before adding an independent verifier. Add one only
   when risk, uncertainty, or required coverage justifies the extra call.

Use only documented built-in `worker`, `explorer`, or `default` types.
Task names identify workflow roles; they are not external custom-agent profiles.

## Run the route

- **Light:** work directly; do not spawn agents.
- **Medium:** read [references/medium.md](references/medium.md), then work
  directly; do not spawn agents.
- **Heavy:** read [references/roles.md](references/roles.md), then
  [references/heavy.md](references/heavy.md); spawn only when the Heavy dispatch
  gate holds.

If subagents are unavailable, continue directly unless the user explicitly
required multi-agent execution; then report the exact limitation. If a preferred
model is unavailable, use the runtime-selected subagent model only when the user
did not explicitly request a model, and disclose that model pinning was lost.
Never substitute an explicitly requested model or claim a model ran without
child-thread or runtime evidence.
