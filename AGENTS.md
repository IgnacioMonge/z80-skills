# AGENTS.md

## Project Context

Z80 Skills is a Codex plugin: portable workflow, Z80 router, and
five specialists. `skills/workflow/` is canonical; do not duplicate its routes
in repository-local documents.

Read the smallest relevant context. When needed, use
`agent_docs/project_overview.md` for architecture,
`agent_docs/project_structure.md` for ownership, and
`agent_docs/project_core_tech.md` for technology and safety boundaries.

## Design And Verification

- Keep modules focused, with clear interfaces and minimal coupling.
- Prefer the smallest coherent behavior-preserving change; keep code testable,
  debuggable, replaceable, extensible, and reusable.
- Define proportionate acceptance criteria before non-trivial work. Keep tests
  cohesive; never weaken coverage, assertions, or failure visibility.
- Preserve unrelated user work. Verify claims against current evidence.

## Execution

- When `$workflow` is invoked or composed, follow `skills/workflow/SKILL.md`.
  An explicit user level wins; otherwise use its smallest sufficient level.
- Keep the main thread as controller. Spawn only when workflow dispatch and
  ownership rules permit it.
- Batch independent, known, non-conflicting reads. Keep dependencies, writes,
  approvals, Git mutations, and checks sharing state sequential.
- Inspect only relevant interfaces, call sites, tests, config, and docs. Run
  the smallest meaningful deterministic checks, then inspect diff and status.

## Durable Documentation

- Record only verified facts; exclude temporary reasoning, raw logs, and
  short-lived checkpoints.
- Use `agent_docs/project_progress.md` and
  `agent_docs/latest_session_work.md` only for durable plans or handoffs. Only
  the main agent may edit them.
- Reserve `agent_docs/project_diary.md` for durable, non-derivable decisions,
  discarded approaches, or lessons.
- Never delete a main project document without warning the user and receiving
  a second explicit confirmation.

Use host-native paths in commands; `/` in documentation is platform-neutral.
