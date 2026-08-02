# Heavy effort

Use one persistent controller with bounded workers in a flat topology. Read
`roles.md` first.

Before dispatch, classify each ownership surface using the intersection of user
authorization, project instructions, and the domain contract:

- **primary-tree read-only:** use only `explorer` or read-only `default` roles;
  do not spawn `executor`, `sol_executor`, or `doc_writer` for that surface.
- **disposable-worktree-only:** an `executor` may edit or build only inside a
  verified, domain-gated disposable worktree; never the primary tree.
- **authorized primary-tree mutation:** an implementer may edit and run checks
  only within its assigned ownership surface and effective authorization.

## Roles

- `workflow_controller`: built-in `default`, read-only planning, dispatch,
  repair routing, and integration review.
- `explorer`: built-in `explorer`, read-only investigation.
- `executor`: built-in `worker`, default implementation.
- `verifier`: built-in `default`, independent verification and failure analysis.
- `doc_writer`: built-in `worker`, durable documentation from verified facts.
- `sol_executor`: built-in `worker`, exceptional implementation only when the
  normal implementer cannot reasonably own the package; at most one.

## Delegation

1. Ask the Sol controller to split only genuinely independent ownership surfaces
   and classify the mutation boundary of each one.
2. Keep it alive while the main thread launches workers and gathers evidence.
3. Keep at most three child threads live, including the Sol controller, unless the user explicitly changes the limit.
4. Spawn every agent with `fork_turns="none"` and a self-contained capsule of at most 400 words.
5. Give each worker a task ID, outcome, ownership, acceptance criteria, source paths, validation, protected areas, and return format.
6. Keep workers away from Git state and main-owned status or handoff files.
7. Return worker evidence to the controller; route its repair decision to the
   same implementer and the correction back to the same verifier.

Delegate documentation only after verification and only for durable architecture, public behavior, structure, decisions, or usage changes.

## Failure handling

One evidence-free worker response gets one concise retry. A second consecutive evidence-free response requires replacement. If replacement fails, disclose the loss of independent execution before taking over delegated work.

Trust child-thread events, runtime metadata, diffs, logs, and command results. Do not trust natural-language claims about model identity.

## Completion

Ask the controller for the final integration decision. Integrate only verified
work and inspect critical hunks and boundaries. Finish with call counts for
`workflow_controller`, `explorer`, `executor`, `sol_executor`, `verifier`, and
`doc_writer`.
