# Project Structure

| Path | Ownership |
| --- | --- |
| `.codex-plugin/plugin.json`, `plugin.json`, `gemini-extension.json` | Host manifests; keep versions aligned. |
| `skills/<name>/` | Each skill owns its `SKILL.md`, `agents/openai.yaml`, progressive references and any analyzers/tests. |
| [workflow](../skills/workflow/SKILL.md) | Canonical execution policy; load only when invoked or composed. |
| `scripts/` | Installers, skill validator, disposable-worktree gate, behavior-eval runner and regression tests. |
| [shrink-agent](../tools/shrink-agent/README.md) | Optional applying optimizer with its own worktree controller and tests. |
| `evals/` | Routing, evidence and policy datasets; fixtures, schemas and verified historical `baseline.json`. |
| `pytest.ini` | Repository-wide test collection and local import paths. |
| `agent_docs/` | Selective project context governed by [AGENTS.md](../AGENTS.md). |

The [README](../README.md) owns installation, usage, the skill catalog and public
validation instructions. Domain contracts and safety gates stay in their skills.
`port-spectranext` keeps the external cartridge checkout authoritative; do not
duplicate its pipeline here.

Audit and shrink own standalone smoke checks in addition to pytest. Live model
results and traces belong under ignored `evals/results/`, separate from
deterministic tests; only verified summaries belong in `evals/baseline.json`.
