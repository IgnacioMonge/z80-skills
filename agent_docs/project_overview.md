# Project Overview

Z80 Skills is a Codex plugin with six complementary domain skills for Z80 and
ZX Spectrum projects written in assembly, C, or mixed C/ASM with z88dk or SDCC,
plus a thin domain selector and a shared adaptive workflow core.

The project is evidence-first: current source and fresh, source-matched build
artifacts are required for promoted findings, size claims, and optimization
claims. Scanners, external research, and delegated agents produce candidates;
the main agent verifies and ranks them.

The skills have distinct responsibilities:

- `route-z80`: selects one specialist from an ambiguous Z80 request, or plain
  workflow for ordinary engineering work; it does not select execution effort.
- `develop-z80`: specification-driven development for an explicit ZX or Next
  product initiative or existing dossier, through autonomously managed
  specification, milestone, task, implementation, and verification stages.
- `debug-z80`: evidence-bounded root-cause diagnosis for an observed failure
  with unresolved causality, plus an authorized minimal repair after its gate.
- `audit-z80`: read-only correctness and risk auditing.
- `organize-z80`: ownership, dependency, placement, and incremental
  reorganization; source edits are limited to an approved `apply` slice.
- `shrink-z80`: binary-size, residency, BSS/stack, bank, overlay, and linked
  library reduction.
- `optimize-z80`: multi-objective ranking across size, speed, RAM, rendering,
  latency, ABI, banking, and hardware constraints.
- `workflow`: reusable Light, Medium, and Heavy execution control composed with
  the domain skills without replacing their evidence and safety gates.

Domain selection and execution effort are separate decisions: `route-z80`
chooses the contract, while `workflow` chooses the smallest sufficient route.
Only the router participates in implicit Z80-domain selection; the six domain
skills are explicit-only and are loaded individually after routing.

Labelled behavior evals complement structural tests with direct, indirect,
negative, and ambiguous routing prompts plus evidence fixtures for audit, size,
and multi-objective optimization. Runtime evals use isolated read-only Codex
sessions and require the installed plugin version to match the manifest.

Normal analysis keeps the primary tree read-only. `develop-z80`, a causally
proven requested `debug-z80` repair, and an approved `organize-z80 apply` slice
may edit it within their explicit mutation gates;
measurement and experiments use detached disposable worktrees and the shared
runner contract.
