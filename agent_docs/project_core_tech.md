# Project Core Technology

- Distribution format: Codex plugin with `.codex-plugin/plugin.json` and one
  `SKILL.md` per skill.
- Runtime tooling: Python standard-library scripts; Python 3.9+ is supported for
  the general helpers, while complete TOML policy handling requires Python 3.11+
  unless an explicit safe fallback is used.
- Target domain: Z80/ZX Spectrum software, including pure assembly and mixed
  C/ASM projects using z88dk or SDCC.
- Safety boundary: analysis is read-only in the primary tree; builds,
  measurements, diagnostic probes, and candidate repairs run in detached
  disposable Git worktrees via `scripts/run_in_worktree.py`. A requested
  `debug-z80` repair reaches the primary tree only after causal proof.
- Evidence boundary: stale or source-unmatched artifacts cannot support
  `PROVEN`, `EXACTO`, or equivalent promoted claims.
- Runtime-sensitive constraints include ABI/register/flag/stack contracts,
  interrupts, paging/banks, overlays, memory placement, firmware/ports,
  contention, target ceilings, and generated code.
