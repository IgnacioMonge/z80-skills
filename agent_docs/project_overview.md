# Project Overview

Z80 Skills is a Codex plugin with four complementary domain skills for Z80 and
ZX Spectrum projects written in assembly, C, or mixed C/ASM with z88dk or SDCC,
plus a shared adaptive workflow core.

The project is evidence-first: current source and fresh, source-matched build
artifacts are required for promoted findings, size claims, and optimization
claims. Scanners, external research, and delegated agents produce candidates;
the main agent verifies and ranks them.

The skills have distinct responsibilities:

- `audit-z80`: read-only correctness and risk auditing.
- `organize-z80`: ownership, dependency, placement, and incremental
  reorganization; source edits are limited to an approved `apply` slice.
- `shrink-z80`: binary-size, residency, BSS/stack, bank, overlay, and linked
  library reduction.
- `optimize-z80`: multi-objective ranking across size, speed, RAM, rendering,
  latency, ABI, banking, and hardware constraints.
- `workflow`: reusable Light, Medium, and Heavy execution control composed with
  the domain skills without replacing their evidence and safety gates.

Normal analysis keeps the primary tree read-only. Measurement and experiments
use detached disposable worktrees and the shared runner contract.
