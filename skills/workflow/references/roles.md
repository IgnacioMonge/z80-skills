# Portable Agent Roles

Use only Codex's documented built-in agent types. Role behavior comes from the
self-contained task capsule, not from custom profiles installed outside this
plugin.

| Workflow role | Task name | Built-in agent type |
| --- | --- | --- |
| Investigator | `explorer` | `explorer` |
| Implementer | `executor` | `worker` |
| Verifier | `verifier` | `default` |

Spawn every role with `fork_turns="none"` and a self-contained capsule. Set
the selected model and effort explicitly when supported. Pass `agent_type`
only if the runtime exposes that parameter; otherwise express the role in the
capsule. Task names are stable labels, never custom agent profiles.

## Model and reasoning selection

Choose for the assignment, independently of role and workflow level. Keep the
main thread on its current model. These are starting preferences based on
runtime model descriptions, not measured price, speed, or quality rankings.
Check the live tool schema or runtime catalog before dispatch; it determines
available model IDs, supported efforts, and spawn parameters. Do not infer
availability from this table or transfer Codex model IDs to another host.

| Assignment | Preferred model | Initial reasoning effort |
| --- | --- | --- |
| Narrow lookup, mechanical edit, or execution of predefined checks with supplied expected results and acceptance rules | `gpt-5.6-luna` | `max` |
| Cohesive coding, debugging, code review, or designing checks and judging evidence sufficiency | `gpt-5.6-sol` | `high` |
| General analysis, research synthesis, documentation, or mixed non-coding work | `gpt-5.6-sol` | `high` |
| Difficult causal reasoning, conflicting evidence, or high-risk contract analysis | `gpt-5.6-sol` | `xhigh` |

Use the table's initial effort for each assignment. Reserve `max` for the
narrow Luna assignments listed above; do not set Sol to `max` merely because a
delegate or workflow is Heavy. Other effort levels require explicit user choice
or task-specific evidence, and must be supported by the selected model.

Select a suitable model upfront; do not require a failed Luna attempt before
using Sol. Missing inputs, tools, permissions, or reproduction
evidence require fixing the capsule or reporting a blocker, not more reasoning.
If a worker's reasoning falls short, retain its evidence, identify the gap, and
choose either more effort or a better-suited model. Stop the prior worker before
transferring mutable ownership; do not replay completed checks without cause.

An explicit user model or effort wins; never silently substitute it. For an
unavailable preference, select another advertised model suited to the same
assignment; if none can be selected, use the runtime default. Disclose the
fallback and any lost effort pinning. If an explicit choice cannot be honored,
report the limitation before dependent work. Record requested settings and
runtime-confirmed settings separately; do not infer actual identity from a
worker's prose.

## Capsule contracts

Workers must not spawn children; the main thread owns dispatch and model changes.

Executing predefined checks and recording their outcomes is mechanical;
designing checks, assessing coverage, or deciding whether evidence proves a
contract requires judgment, even when the acceptance criterion is explicit.
Mechanical execution does not certify correctness beyond the supplied checks.
Choose the model for the hardest reasoning obligation in a mixed assignment;
the `verifier` role never determines the model.

- **Investigator:** remain read-only; trace the assigned surface and return
  evidence with paths, symbols, commands, and unresolved uncertainty.
- **Implementer:** own only named files or responsibility; preserve unrelated
  work; make the smallest coherent change and run the requested check.
- **Verifier:** independently test the supplied acceptance criteria; do not fix
  production, test, fixture, mock, or test-data defects. Return exact commands,
  outcomes, and residual risk; send repairs to the assigned implementer.

## Upward report contract

Keep each worker's final report within 250 words and describe the knowledge
delta, not the activity transcript: status, outcome, contract changes,
invalidated assumptions, verification evidence, residual risk, decision
required, and exact references. Use `Decision required: none` explicitly when
appropriate. Keep raw logs, large diffs, diagnostics, inventories, and verbose
test output in the retained worker thread or a referenced artifact. The main
thread opens that detail only for a material contradiction, uncertainty, or
high-risk integration boundary.

Apply the [mutation boundary](../SKILL.md#mutation-boundary) before spawning.
Investigators and verifiers remain read-only; implementers own only the assigned
write surface. The role contract remains identical regardless of model.
