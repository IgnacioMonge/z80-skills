# Project Overview

Z80 Skills is a Codex plugin with eight complementary engineering skills for
Z80 and ZX Spectrum projects written in assembly, C, or mixed C/ASM with z88dk
or SDCC, one BridgeZX delivery skill, a thin domain selector, and a shared
adaptive workflow core.

The project is evidence-first: current source and fresh, source-matched build
artifacts are required for promoted findings, size claims, and optimization
claims. Scanners, external research, and delegated agents produce candidates;
the main agent verifies and ranks them.

Skill responsibilities and entry points are listed in the
[README catalog](../README.md#what-is-included).

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
