# Project Overview

Z80 Skills is a Codex plugin bundling eight engineering specialists, BridgeZX delivery, a domain
router and an adaptive workflow for Z80/ZX Spectrum C, assembly and mixed
z88dk/SDCC projects. See the [skill catalog](../README.md#what-is-included).

Domain and effort are separate: `route-z80` selects one specialist contract;
`workflow` selects the smallest sufficient execution level. Only the router
participates in implicit Z80-domain selection, even for unambiguous requests.
The nine routed skills are explicit-only and loaded individually.

Scanners, research and workers produce candidates; the main agent verifies and
ranks them using current source and fresh, source-matched artifacts. Mutation,
remote-write and evidence limits live in [core technology](project_core_tech.md).

Behavior evaluations complement structural tests with direct, indirect,
negative, ambiguous and evidence cases. Live runs use isolated read-only Codex
sessions and require the installed plugin version to match the manifest.
See the [verification handoff](latest_session_work.md) for commands and history.
