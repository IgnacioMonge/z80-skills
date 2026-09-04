---
name: route-z80
description: Thin implicit domain dispatcher for Z80, ZX Spectrum, ZX Spectrum Next, BridgeZX delivery, and Spectranext cartridge work. Use as the entry point for a natural-language Z80 request whose outcome matches a routed specialist, even when the match is unambiguous, or when the user asks which Z80 skill fits. This includes observed unresolved failures, preventive audits, product initiatives, repository documentation, file delivery, organization, size reduction, and competing optimization goals. Select one primary specialist or plain workflow without loading every candidate. Do not use when the user explicitly names a specialist or when a known-cause fix or other ordinary bounded engineering task clearly belongs to workflow.
---

# Route Z80

Choose the smallest domain contract that matches the requested result. This
skill selects the domain; `$workflow` separately selects Light, Medium, or Heavy
execution.

## Selection

1. Honor an explicitly named skill unless it conflicts with the requested
   outcome; explain a material conflict instead of silently substituting.
2. Identify the user's primary question and requested deliverable, not merely
   words found in the repository or implementation steps common to all work.
3. Select one primary route from the table and load only that sibling skill.
4. Use a second specialist only for a separate explicit objective or when the
   primary specialist uncovers a material blocker owned by that domain.

Ambiguity is not an entry condition. When a natural-language request without an
explicitly named skill unambiguously matches one row, select that route
immediately. Ask a question only when multiple primary outcomes remain.

If the request names several possible problem domains but does not identify a
primary outcome, remain in `route-z80` and ask one focused question that
separates those outcomes. Do not select `optimize-z80` merely because size,
structure, and performance appear together as alternatives rather than as
competing acceptance criteria.

| Primary question | Route |
| --- | --- |
| Does the user want named local files or directories sent to a ZX Spectrum Classic or Next through BridgeZX, optionally at a remote destination or in a specific sequence? | [`send-bridgezx`](../send-bridgezx/SKILL.md) |
| Is this a request to start, resume, implement, diagnose, validate, or hand off an existing ZX program's consumer port to the **Spectranext cartridge** through its canonical external pipeline? | [`port-spectranext`](../port-spectranext/SKILL.md) |
| Is this an explicit new product initiative—application, game, demo, tool, or port—that needs an SDD specification and milestones, or are we resuming its existing dossier? | [`develop-z80`](../develop-z80/SKILL.md) |
| Does the user want public GitHub documentation for a Z80 or ZX repository created, restructured, reviewed, or synchronized across languages? | [`document-z80`](../document-z80/SKILL.md) |
| Is there a concrete observed failure whose causal owner remains unknown, evidence conflicts, or an evidence-supported repair failed? | [`debug-z80`](../debug-z80/SKILL.md) |
| Does the user want a preventive or broad read-only audit for defects or correctness risks involving ABI, ISR, memory, firmware, toolchain behavior, hardware timing, or regressions? | [`audit-z80`](../audit-z80/SKILL.md) |
| Should ownership, dependencies, source layout, module boundaries, banking, overlays, or runtime placement be mapped or reorganized? | [`organize-z80`](../organize-z80/SKILL.md) |
| Is the exclusive objective to reduce linked/storage size or memory footprint and prove net byte savings? | [`shrink-z80`](../shrink-z80/SKILL.md) |
| Must the real bottleneck and trade-offs among speed, size, RAM, rendering, latency, or other competing metrics be ranked? | [`optimize-z80`](../optimize-z80/SKILL.md) |
| Is this an ordinary bounded fix, implementation, review, refactor, test, build, source-code comment, or agent-instruction change without a specialist evidence question? | [`workflow`](../workflow/SKILL.md) |

Do not select `develop-z80` merely because the request mentions a feature,
architecture, planning, implementation, or verification inside an established
repository. Those are normal engineering activities. Select it only for an
explicit product lifecycle or an already active develop dossier.

`Spectranext` names the cartridge and its consumer pipeline; it is not shorthand
for the ZX Spectrum Next platform. Route an existing consumer port to that
cartridge through `port-spectranext`. Route a generic Spectrum Next product or
port according to its requested lifecycle or ordinary engineering outcome.

Route a delivery request to `send-bridgezx` even when the named source is a
build artifact. Building, changing, diagnosing, or optimizing that artifact is
a separate engineering objective; merely sending it is not product development
or a Spectranext consumer port.

Route public repository documentation to `document-z80`, including a single
README when the requested outcome is accurate user-facing documentation. Keep
source-code comments, agent-only instructions, and non-repository prose on plain
`workflow`.

When size is the sole acceptance metric, prefer `shrink-z80`; when size competes
with speed, RAM, rendering, or latency, prefer `optimize-z80`. A performance
regression is `debug-z80` only when current behavior violates a known baseline
and the cause is unresolved; improving acceptable behavior is `optimize-z80`.

Use `debug-z80` for one observed failure with unresolved causality, whether the
user requests diagnosis alone or diagnosis plus repair. An unresolved Z80 or ZX
failure belongs here rather than in a generic debugging workflow. Use
`audit-z80` for a preventive or broad read-only correctness review without one
failure driving a causal investigation. When the cause is already established
and the user asks for the fix, use `workflow`.

## Handoff

State the selected route in one sentence and continue immediately with it. Do
not stop for the user to confirm an unambiguous selection. Do not summarize all
unused skills, load every sibling `SKILL.md`, or turn domain selection into a
second execution control plane.
