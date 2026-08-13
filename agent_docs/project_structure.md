# Project Structure

```text
.codex-plugin/plugin.json       Plugin metadata and skill root
evals/
  baseline.json                Verified non-sensitive behavior summary
  routing.jsonl                 Labelled domain-selection prompts
  evidence.jsonl                Labelled evidence-contract prompts
  fixtures/                     Isolated stale/missing-evidence projects
  schemas/                      Structured runtime-eval outputs
scripts/
  install_personal_marketplace.py
  run_behavior_evals.py          Ephemeral read-only Codex eval runner
  run_in_worktree.py             Shared disposable-worktree gate
  test_behavior_evals.py         Dataset, schema, and scoring tests
  test_personal_marketplace.py   Canonical-source installer tests
  test_run_in_worktree.py        Runner contract tests
  test_workflow_integration.py   Workflow composition and portability tests
skills/
  route-z80/                     Thin Z80 domain selector
  develop-z80/                   Idea-to-implementation SDD workflow
  audit-z80/                     Read-only correctness audit
  organize-z80/                  Architecture and reorganization workflow
  shrink-z80/                    Size-only analysis and analyzers
  optimize-z80/                  Multi-objective optimization and analyzers
  workflow/                      Shared adaptive execution core
```

Each skill owns its `SKILL.md` and `agents/openai.yaml`; domain detail lives in
`references/` only where progressive loading helps. Analyzer-bearing skills
also own `scripts/`; `shrink-z80` additionally owns its smoke tests. The root
README documents installation, usage, safety rules, repository structure, and
validation commands. Runtime behavior results are generated under ignored
`evals/results/`; they are not mixed with deterministic unit tests.

Ownership boundaries are intentionally explicit: route selects a domain;
develop handles explicit product initiatives and their dossiers; audit handles
correctness, organize handles structure, shrink handles size, optimize handles
competing metrics, and workflow handles generic execution control. Domain
evidence and safety gates remain in the specialized skills.

Project workflow instructions live in `AGENTS.md`; durable context is under
`agent_docs/`, including the heavy-route procedure in
`agent_docs/workflows/heavy_route.md`.
