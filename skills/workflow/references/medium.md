# Medium effort

Use one persistent Sol controller and one Luna execution stream.

Worker permissions are the intersection of this route and the invoking project
and domain contracts. A read-only or worktree-only contract remains read-only
or worktree-only; workers may not edit or build the primary tree.

1. Spawn `workflow_orchestrator` with `fork_turns="none"` and obtain a bounded plan.
2. Spawn at most one active Luna worker at a time, normally `executor_luna`; use `explorer` first only when targeted investigation is genuinely needed.
3. Require the Luna worker to implement a coherent increment and run its smallest relevant check.
4. Send its evidence to the same Sol controller for review.
5. Route production defects back to the same executor. Add `tester` only when the behavior or risk warrants independent verification.
6. Ask the Sol controller for a final integration decision, then perform the main thread's critical diff and status checks.

Keep the plan short and avoid durable status files unless the repository already defines them or the user requests a cross-session handoff.

When blocked, report the failed step, evidence, completed work, affected acceptance criterion, and required decision. Do not present partial work as complete.
