# Heavy effort

Keep the main thread as controller and use bounded workers in a flat topology.
Read `roles.md` first.

Before dispatch, classify each ownership surface using the intersection of user
authorization, project instructions, and the domain contract:

- **primary-tree read-only:** use only `explorer` or read-only `default` roles;
  do not spawn `executor` or `sol_executor` for that surface.
- **disposable-worktree-only:** an `executor` may edit or build only inside a
  verified, domain-gated disposable worktree; never the primary tree.
- **authorized primary-tree mutation:** an implementer may edit and run checks
  only within its assigned ownership surface and effective authorization.

## Roles

- `explorer`: built-in `explorer`, read-only investigation.
- `executor`: built-in `worker`, default implementation.
- `verifier`: built-in `default`, independent verification and failure analysis.
- `sol_executor`: built-in `worker`, exceptional implementation only when the
  normal implementer cannot reasonably own the package; at most one.

## Dispatch gate

1. Identify at least two concrete, bounded, independent workstreams. If none
   exist, do not manufacture delegation; continue directly and state that the
   Heavy dispatch gate did not hold.
2. Start independent workers together. Use at most two by default; add a third
   only for a genuinely separate workstream.
3. Spawn each worker with `fork_turns="none"` and a self-contained capsule of
   at most 400 words.
4. Give each worker a task ID, outcome, ownership, acceptance criteria, source
   paths, validation, protected areas, return format, and stop condition.
5. Assign one owner to each mutable file set. Parallel implementers may write
   only to disjoint surfaces.
6. Keep workers away from Git state and main-owned status or handoff files.
7. While workers run, advance only unassigned architecture, contract, and
   integration work. Do not duplicate delegated discovery, diagnostics,
   implementation, or checks. Integrate upward reports once.
8. Run deterministic checks before adding one independent verifier. Add it only
   when risk, uncertainty, or required coverage justifies the extra call.

## Direct repair loop

Give the verifier and responsible implementer each other's canonical task
names. For a routine production defect, the verifier sends a compact defect
packet directly to that implementer; the implementer repairs within the
original capsule and returns the result directly; the verifier reruns the
failed criterion and affected regression checks. The main thread must not relay
or rediagnose that loop.

Escalate to the main thread only when a repair conflicts with the capsule,
changes a cross-package contract, invalidates a material decision, expands
ownership, introduces security or migration risk, or the same criterion still
fails after two focused repair attempts. Test, fixture, mock, or test-data
defects remain with the verifier.

A defect packet contains the failed criterion, minimal reproduction, observed
and expected behavior, affected contract or files, exact evidence reference,
and whether scope or architecture appears implicated.

## Layered evidence

Follow the upward report contract in `roles.md`. Workers retain raw operational
context and return only the bounded knowledge delta. The main thread normally
accepts a coherent report with `Decision required: none` without reopening its
logs or artifacts; inspect them only when evidence conflicts, uncertainty is
material, or an integration boundary is high risk.

Update durable documentation in the main thread after verification and only for
architecture, public behavior, structure, decisions, or usage changes.

## Failure handling

One evidence-free worker response gets one concise retry. A second consecutive
evidence-free response requires replacement. If replacement fails, disclose the
loss of independent execution before taking over delegated work.

Trust child-thread events, runtime metadata, diffs, logs, and command results.
Do not trust natural-language claims about model identity.

## Completion

Integrate only verified work and inspect critical hunks and boundaries. Finish
with call counts for `explorer`, `executor`, `sol_executor`, and `verifier`.
