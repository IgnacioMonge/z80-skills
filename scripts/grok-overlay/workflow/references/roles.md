# Portable Agent Roles (Grok Build)

Use Grok's `spawn_subagent` tool. Role behavior comes from the self-contained
task capsule (`prompt` + `description`), not from custom profiles.

| Workflow role | Task label (`description`) | `subagent_type` | `capability_mode` | Isolation |
| --- | --- | --- | --- | --- |
| Controller | `workflow_controller` | `plan` (fallback: `general-purpose`) | `read-only` | `none` |
| Investigator | `explorer` | `explore` | `read-only` (explore is read-only) | `none` |
| Implementer | `executor` | `general-purpose` | `read-write` or `all` | `worktree` if disposable-only; else `none` |
| Verifier | `verifier` | `general-purpose` | `read-only` or `execute` | `none` |
| Documentation | `doc_writer` | `general-purpose` | `read-write` | `none` |
| Exceptional implementer | `sol_executor` | `general-purpose` | `all` | same as implementer |

## Spawn rules (Grok)

- Call `spawn_subagent` with a self-contained `prompt` (task capsule ≤400 words).
- Put the workflow role label in `description` (3–5 words, e.g. `workflow controller`).
- Prefer `background: true`; collect results with `get_command_or_subagent_output`.
- Do **not** pass `model` unless the user explicitly requested one. Available
  model slug when needed: `grok-4.5`. Never invent Codex model names
  (`gpt-5.6-sol`, `gpt-5.6-luna`, etc.).
- Codex terms map as: `default` → `plan`/`general-purpose`, `explorer` →
  `explore`, `worker` → `general-purpose`, `fork_turns="none"` → fresh spawn
  (no parent transcript resume unless intentionally using `resume_from`).
- Optional compressed investigators: `caveman:cavecrew-investigator` for
  locate-only work; `caveman:cavecrew-reviewer` for diff review. Do not use
  them when the domain skill requires full evidence capsules.

## Capsule contracts

- **Controller:** remain read-only; do not spawn descendants or edit files;
  return bounded dispatch, repair, completion, or blocker decisions.
- **Investigator:** remain read-only; trace the assigned surface and return
  evidence with paths, symbols, commands, and unresolved uncertainty.
- **Implementer:** own only named files or responsibility; preserve unrelated
  work; make the smallest coherent change and run the requested check.
- **Verifier:** independently test the supplied acceptance criteria; do not fix
  defects; return exact commands, outcomes, and residual risk.
- **Documentation:** edit only named durable documents using verified facts;
  never alter main-owned status or handoff files unless explicitly authorized.
- **Exceptional implementer:** use only when the controller explains why the
  bounded package cannot reasonably be handled by the default implementer.

All permissions are the intersection of the role, project instructions,
domain skill, parent sandbox, and user authorization. Classify each assignment
as **primary-tree read-only**, **disposable-worktree-only**, or **authorized
primary-tree mutation** before spawning it. Investigators and verifiers remain
read-only; implementers may write only in the classified surface. A role never
widens a network, approval, or mutation boundary.

If a preferred model is rejected or unavailable, inherit the parent model and
disclose that pinning was lost. The role contract remains identical regardless
of model.
