# Heavy effort

Keep the main thread as controller and use bounded workers in a flat topology.

Apply the [common rules and mutation boundary](../SKILL.md) before dispatch.
Role types and model/effort selection live in [roles.md](roles.md).

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
   Include relevant verified evidence with revision/configuration and remaining
   questions so fresh-context workers do not repeat completed discovery.
5. Assign one owner to each mutable file set. Parallel implementers may write
   only to disjoint surfaces.
6. Keep workers away from Git state and main-owned status or handoff files.
7. While workers run, advance only unassigned architecture, contract, and
   integration work. Do not duplicate delegated discovery, diagnostics,
   implementation, or checks. Integrate upward reports once.
8. Run deterministic checks before adding one independent verifier. Add it only
   when risk, uncertainty, or required coverage justifies the extra call.

## Direct repair loop

Give verifier and implementer each other's canonical task names. The verifier
sends the failed criterion, reproduction, expected/actual behavior, affected
files/contracts, evidence reference, and scope/architecture concerns directly.
The implementer repairs within its capsule and returns results; the verifier
reruns failed and affected checks without editing files or weakening assertions.
The main thread must not relay or rediagnose routine repairs.
Test, fixture, mock, and test-data repairs also belong to the implementer within
its scope; otherwise the main thread assigns an authorized owner.
Escalate capsule conflicts, cross-package contract changes, invalidated decisions,
ownership expansion, security/migration risks, or the same failing criterion
after two focused repair attempts.

## Layered evidence

Follow the upward report contract in `roles.md`. Workers retain raw operational
context and return only the bounded knowledge delta. The main thread normally
accepts a coherent report with `Decision required: none` without reopening its
logs or artifacts; inspect them only when evidence conflicts, uncertainty is
material, or an integration boundary is high risk. Domain promotion gates still
require their specified source/artifact checks; a worker summary cannot replace
that proof.

Update durable documentation in the main thread after verification and only for
architecture, public behavior, structure, decisions, or usage changes.

## Failure handling

One evidence-free worker response gets one concise retry. A second consecutive
evidence-free response requires replacement. If replacement fails, disclose the
loss of independent execution before taking over delegated work.

Trust child-thread events, runtime metadata, diffs, logs, and command results.

## Completion

Integrate only verified work and inspect critical hunks and boundaries. Finish
with call counts by role and runtime-confirmed model/effort when available;
otherwise label settings as requested, not confirmed.
