# Medium effort

Use one persistent controller and one execution stream. Read `roles.md` first.

Before dispatch, classify the effective mutation boundary using the intersection
of user authorization, project instructions, and the domain contract:

- **primary-tree read-only:** use one `explorer` or read-only `default` analysis
  stream; do not spawn an implementer.
- **disposable-worktree-only:** use one `executor` only inside a verified,
  domain-gated disposable worktree; never edit or build the primary tree.
- **authorized primary-tree mutation:** use one `executor` that may edit and run
  checks only within its assigned ownership surface and effective authorization.

1. Spawn built-in `default` as `workflow_controller` with the controller
   contract and obtain a bounded plan.
2. Spawn at most one active stream using the role permitted by the classified
   mutation boundary.
3. Require that worker to complete one coherent analysis or increment and run
   the smallest relevant check allowed by the same boundary.
4. Send its evidence to the same controller for review.
5. Route production defects back to the same implementer. Add built-in
   `default` as `verifier` only when behavior or risk warrants independent
   verification.
6. Ask the controller for a final integration decision, then perform the main
   thread's critical diff and status checks.

Keep the plan short and avoid durable status files unless the repository already defines them or the user requests a cross-session handoff.

When blocked, report the failed step, evidence, completed work, affected acceptance criterion, and required decision. Do not present partial work as complete.
