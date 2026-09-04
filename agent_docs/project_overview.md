# Project Overview

Z80 Skills is a Codex plugin with eight complementary engineering skills for
Z80 and ZX Spectrum projects written in assembly, C, or mixed C/ASM with z88dk
or SDCC, one BridgeZX delivery skill, a thin domain selector, and a shared
adaptive workflow core.

The project is evidence-first: current source and fresh, source-matched build
artifacts are required for promoted findings, size claims, and optimization
claims. Scanners, external research, and delegated agents produce candidates;
the main agent verifies and ranks them.

The skills have distinct responsibilities:

- `route-z80`: implicitly selects one specialist from a natural-language Z80
  request, including unambiguous matches, or plain workflow for ordinary
  engineering work; it does not select execution effort.
- `send-bridgezx`: sends named files or directories through the official
  BridgeZX client using its explicit or last-known IP, with optional target,
  remote destination, and ordered-operation safeguards.
- `develop-z80`: specification-driven development for an explicit ZX or Next
  product initiative or existing dossier, through autonomously managed
  specification, milestone, task, implementation, and verification stages.
- `document-z80`: creates, restructures, reviews, and synchronizes public
  repository documentation with verified Z80/ZX facts and language parity.
- `port-spectranext`: drives an existing ZX consumer port through the external
  Spectranext cartridge pipeline while keeping its checkout and canon
  authoritative and consumer state isolated.
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
Only the router participates in implicit Z80-domain selection; the nine routed
skills are explicit-only and are loaded individually after routing. Ambiguity is
not required for the router to hand an unqualified request to one specialist.

Labelled behavior evals complement structural tests with direct, indirect,
negative, and ambiguous routing prompts plus evidence fixtures for audit, size,
and multi-objective optimization. Runtime evals use isolated read-only Codex
sessions and require the installed plugin version to match the manifest.

Normal analysis keeps the primary tree read-only. `develop-z80`, an authorized
`port-spectranext` consumer slice, a causally proven requested `debug-z80`
repair, and an approved `organize-z80 apply` slice may edit it within their
explicit mutation gates. `document-z80` may edit only the requested public
documentation. `send-bridgezx` may write only the requested sources to the
selected remote Spectrum;
measurement and experiments use detached disposable worktrees and the shared
runner contract.
