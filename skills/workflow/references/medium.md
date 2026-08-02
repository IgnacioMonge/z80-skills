# Medium effort

Use one persistent controller and one execution stream. Read `roles.md` first.

Worker permissions are the intersection of this route and the invoking project
and domain contracts. A read-only or worktree-only contract remains read-only
or worktree-only; workers may not edit or build the primary tree.

1. Spawn built-in `default` as `workflow_controller` with the controller
   contract and obtain a bounded plan.
2. Spawn at most one active implementation stream, normally built-in `worker`
   as `executor`; use built-in `explorer` first only when targeted investigation
   is genuinely needed.
3. Require the implementer to complete one coherent increment and run its
   smallest relevant check.
4. Send its evidence to the same controller for review.
5. Route production defects back to the same implementer. Add built-in
   `default` as `verifier` only when behavior or risk warrants independent
   verification.
6. Ask the controller for a final integration decision, then perform the main
   thread's critical diff and status checks.

Keep the plan short and avoid durable status files unless the repository already defines them or the user requests a cross-session handoff.

When blocked, report the failed step, evidence, completed work, affected acceptance criterion, and required decision. Do not present partial work as complete.
