# Heavy effort

Use one persistent Sol controller with bounded Luna workers in a flat topology.

Worker permissions are the intersection of this route and the invoking project
and domain contracts. A read-only or worktree-only contract remains read-only
or worktree-only; workers may not edit or build the primary tree.

## Roles

- `workflow_orchestrator`: Sol, read-only planning, dispatch decisions, repair routing, and integration review.
- `explorer`: Luna, read-only investigation.
- `executor_luna`: default Luna implementation worker.
- `tester`: Luna, independent verification and failure analysis.
- `doc-writer`: Luna, durable documentation from verified facts.
- `executor_sol`: exceptional implementation only when Luna cannot reasonably own the package; at most one.

## Delegation

1. Ask the Sol controller to split only genuinely independent ownership surfaces.
2. Keep it alive while the main thread launches workers and gathers evidence.
3. Keep at most three child threads live, including the Sol controller, unless the user explicitly changes the limit.
4. Spawn every agent with `fork_turns="none"` and a self-contained capsule of at most 400 words.
5. Give each worker a task ID, outcome, ownership, acceptance criteria, source paths, validation, protected areas, and return format.
6. Keep workers away from Git state and main-owned status or handoff files.
7. Return worker evidence to Sol; route its repair decision to the same executor and correction back to the same tester.

Delegate documentation only after verification and only for durable architecture, public behavior, structure, decisions, or usage changes.

## Failure handling

One evidence-free worker response gets one concise retry. A second consecutive evidence-free response requires replacement. If replacement fails, disclose the loss of independent execution before taking over delegated work.

Trust child-thread events, runtime metadata, diffs, logs, and command results. Do not trust natural-language claims about model identity.

## Completion

Ask Sol for the final integration decision. Integrate only verified work and inspect critical hunks and boundaries. Finish with call counts for `workflow_orchestrator`, `explorer`, `executor_luna`, `executor_sol`, `tester`, and `doc-writer`.
