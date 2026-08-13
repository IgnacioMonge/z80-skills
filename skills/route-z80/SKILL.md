---
name: route-z80
description: Thin domain dispatcher for Z80, ZX Spectrum, and ZX Spectrum Next work. Use when the user asks which Z80 skill fits, or when a generic Z80 repository request is genuinely ambiguous among product development, correctness auditing, code organization, size reduction, and multi-objective optimization. Select one primary specialist or plain workflow without loading every candidate. Do not use when the user explicitly names a specialist or when an ordinary localized fix, review, refactor, build, test, or documentation task already has a clear workflow-only path.
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

If the request names several possible problem domains but does not identify a
primary outcome, remain in `route-z80` and ask one focused question that
separates those outcomes. Do not select `optimize-z80` merely because size,
structure, and performance appear together as alternatives rather than as
competing acceptance criteria.

| Primary question | Route |
| --- | --- |
| Is this an explicit new product initiative—application, game, demo, tool, or port—that needs an SDD specification and milestones, or are we resuming its existing dossier? | [`develop-z80`](../develop-z80/SKILL.md) |
| Are there defects or correctness risks involving ABI, ISR, memory, firmware, toolchain behavior, hardware timing, or regressions that require an evidence-first read-only audit? | [`audit-z80`](../audit-z80/SKILL.md) |
| Should ownership, dependencies, source layout, module boundaries, banking, overlays, or runtime placement be mapped or reorganized? | [`organize-z80`](../organize-z80/SKILL.md) |
| Is the exclusive objective to reduce linked/storage size or memory footprint and prove net byte savings? | [`shrink-z80`](../shrink-z80/SKILL.md) |
| Must the real bottleneck and trade-offs among speed, size, RAM, rendering, latency, or other competing metrics be ranked? | [`optimize-z80`](../optimize-z80/SKILL.md) |
| Is this an ordinary bounded fix, implementation, review, refactor, test, build, or documentation change without a specialist evidence question? | [`workflow`](../workflow/SKILL.md) |

Do not select `develop-z80` merely because the request mentions a feature,
architecture, planning, implementation, or verification inside an established
repository. Those are normal engineering activities. Select it only for an
explicit product lifecycle or an already active develop dossier.

When size is the sole acceptance metric, prefer `shrink-z80`; when size competes
with speed, RAM, rendering, or latency, prefer `optimize-z80`. When the user asks
to fix a known bug, use `workflow`; use `audit-z80` when the requested result is
an audit or when correctness remains an unresolved evidence question.

## Handoff

State the selected route in one sentence and continue immediately with it. Do
not stop for the user to confirm an unambiguous selection. Do not summarize all
unused skills, load every sibling `SKILL.md`, or turn domain selection into a
second execution control plane.
