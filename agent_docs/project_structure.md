# Project Structure

```text
.codex-plugin/plugin.json       Plugin metadata and skill root
scripts/
  install_personal_marketplace.py
  run_in_worktree.py             Shared disposable-worktree gate
  test_personal_marketplace.py   Canonical-source installer tests
  test_run_in_worktree.py        Runner contract tests
  test_workflow_integration.py   Workflow composition and portability tests
skills/
  audit-z80/                     Read-only correctness audit
  organize-z80/                  Architecture and reorganization workflow
  shrink-z80/                    Size-only analysis and analyzers
  optimize-z80/                  Multi-objective optimization and analyzers
  workflow/                      Shared adaptive execution core
```

Each skill owns its `SKILL.md`, `agents/openai.yaml`, and `references/`.
Analyzer-bearing skills also own `scripts/`; `shrink-z80` additionally owns
its smoke tests. The root README documents installation, usage, safety rules,
repository structure, and validation commands.

Ownership boundaries are intentionally explicit: audit handles correctness,
organize handles structure, shrink handles size, optimize handles competing
metrics, and workflow handles generic execution control. Domain evidence and
safety gates remain in the specialized skills.

Project workflow instructions live in `AGENTS.md`; durable context is under
`agent_docs/`, including the heavy-route procedure in
`agent_docs/workflows/heavy_route.md`.
