# Project Progress

## Current State

- The plugin contains `workflow`, `route-z80`, eight explicit engineering
  skills, and the explicit `send-bridgezx` delivery skill.
- `debug-z80` owns unresolved-cause diagnosis and permits a minimal primary-tree
  repair only after its causal gate is satisfied.
- Runtime routing and evidence datasets cover all routes, including repository
  documentation, BridgeZX delivery, the debug mutation boundary, and
  stale-evidence rejection. Installed 0.8.0 passed all 34 routing and four
  evidence cases with the runtime-default model on 2026-09-04.
- The Grok installer derives its workflow overlay from the canonical
  `skills/workflow/` files and installs all eleven skills. Optional Claude sync
  copies the canonical skill set.
- Audit and shrink scanners share traversal, text matching, hit reporting, and
  map/symbol parsing through `skills/shrink-z80/scripts/scan_common.py`; their
  domain rules and reports remain separate.

## Release Gate

Before publishing a local revision, run the deterministic test suite, validate
all skill directories and the plugin manifest, bump the release version,
reinstall from the personal marketplace, and confirm that the
installed version equals the manifest.

No unimplemented durable milestone is currently recorded.
