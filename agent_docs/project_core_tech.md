# Project Core Technology

## Tools

- General helpers target Python 3.9+; compatibility at that minimum still needs
  verification. Full TOML policy parsing needs Python 3.11+ or an explicit safe
  fallback. [shrink-agent](../tools/shrink-agent/README.md) requires Python 3.11+.
- Most helpers use the standard library. The [skill validator](../scripts/validate_skills.py)
  requires [PyYAML](../scripts/requirements-validation.txt); the test suite uses
  pytest. shrink-agent imports the Anthropic SDK only for live API use.
- BridgeZX delivery uses the official client's planner and transfer engine with
  Python 3.10+; do not duplicate its wire protocol or IP store.

## Boundaries

- Analysis keeps the primary tree read-only. Explicit mutation gates permit
  `develop-z80`, authorized `port-spectranext` consumer slices, requested
  `debug-z80` repairs after causal proof, and approved `organize-z80 apply` slices.
  `document-z80` verifies source claims and edits only requested public docs.
- Skill builds, measurements, probes and experimental repairs use detached
  disposable worktrees via [the shared runner](../scripts/run_in_worktree.py).
  Explicitly launched shrink-agent has its own controller and disposable branch
  worktree: all-target builds, size gates, configured tests and model review
  precede accepted commits. It never merges or pushes automatically.
- BridgeZX authorization covers only named sources, the selected Spectrum,
  optional destination and requested sequence. Never retry an uncertain transfer.
- Stale or source-unmatched artifacts cannot support `PROVEN`, `EXACTO` or
  equivalent promoted claims. Model review alone is not proof.
- Preserve ABI/register/flag/stack contracts, interrupts, paging/banks, overlays,
  memory placement, firmware/ports, contention, target ceilings and generated code.
