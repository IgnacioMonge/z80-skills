# Portable Agent Roles

Use only Codex's documented built-in agent types. Role behavior comes from the
self-contained task capsule, not from custom profiles installed outside this
plugin.

| Workflow role | Task name | Built-in agent type | Preferred model |
| --- | --- | --- | --- |
| Investigator | `explorer` | `explorer` | `gpt-5.6-luna` |
| Implementer | `executor` | `worker` | `gpt-5.6-luna` |
| Verifier | `verifier` | `default` | `gpt-5.6-luna` |
| Exceptional implementer | `sol_executor` | `worker` | `gpt-5.6-sol` |

Spawn every role with `fork_turns="none"` and a self-contained capsule. Set
the preferred model explicitly when supported. For `gpt-5.6-luna`, use
`reasoning_effort="medium"` by default. Raise effort to `high` or `max`
only when the capsule identifies difficult, ambiguous, or high-risk reasoning
whose expected benefit justifies the added latency and token cost. A task name
is only a stable label for messaging and call counts; never pass it as a custom
`agent_type`.

## Capsule contracts

- **Investigator:** remain read-only; trace the assigned surface and return
  evidence with paths, symbols, commands, and unresolved uncertainty.
- **Implementer:** own only named files or responsibility; preserve unrelated
  work; make the smallest coherent change and run the requested check.
- **Verifier:** independently test the supplied acceptance criteria; do not fix
  defects; return exact commands, outcomes, and residual risk.
- **Exceptional implementer:** use only when the main thread explains why the
  bounded package cannot reasonably be handled by the default implementer.

All permissions are the intersection of the role, project instructions,
domain skill, parent sandbox, and user authorization. Classify each assignment
as **primary-tree read-only**, **disposable-worktree-only**, or **authorized
primary-tree mutation** before spawning it. Investigators and verifiers remain
read-only; implementers may write only in the classified surface. Assign one
owner to each mutable file set; parallel implementers must use disjoint
surfaces. A role never widens a network, approval, or mutation boundary.

If a preferred model is rejected, follow `SKILL.md` model fallback rules. The
role contract remains identical regardless of model.
