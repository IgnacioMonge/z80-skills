# Project Core Technology

- Distribution format: Codex plugin with `.codex-plugin/plugin.json` and one
  `SKILL.md` per skill.
- Runtime tooling: Python standard-library scripts; Python 3.9+ is supported for
  the general helpers, while complete TOML policy handling requires Python 3.11+
  unless an explicit safe fallback is used.
- Transfer tooling: `send-bridgezx` requires the official BridgeZX Python client
  (Python 3.10+) and imports its planner and transfer engine; the plugin does not
  duplicate the wire protocol or IP store.
- Target domain: Z80/ZX Spectrum software, including pure assembly and mixed
  C/ASM projects using z88dk or SDCC, plus external-pipeline consumer ports to
  the Spectranext cartridge.
- Safety boundary: analysis is read-only in the primary tree; builds,
  measurements, diagnostic probes, and candidate repairs run in detached
  disposable Git worktrees via `scripts/run_in_worktree.py`. A requested
  `debug-z80` repair reaches the primary tree only after causal proof.
- Remote-write boundary: a BridgeZX delivery request authorizes only the named
  sources, selected Spectrum, optional destination, and requested sequence; an
  uncertain transfer outcome is never retried automatically.
- Documentation boundary: `document-z80` verifies public repository claims
  against current source and edits only the human-facing documentation in scope.
- Evidence boundary: stale or source-unmatched artifacts cannot support
  `PROVEN`, `EXACTO`, or equivalent promoted claims.
- Runtime-sensitive constraints include ABI/register/flag/stack contracts,
  interrupts, paging/banks, overlays, memory placement, firmware/ports,
  contention, target ceilings, and generated code.
