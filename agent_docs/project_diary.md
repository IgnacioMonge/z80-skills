# Project Diary

Initialized by the Codex workflow installation. Record only durable architecture decisions, discarded approaches, and lessons.

## 2026-10-09 — Superpowers comparison (workflow, audit-z80)

Compared against superpowers 6.4.2 (`subagent-driven-development`,
`verification-before-completion`, `requesting-code-review`).

- Adopted: closed worker statuses, verifier finding triage, worker resumption
  and file-less recovery after compaction, decisions listed at completion,
  criterion-to-evidence completion mapping, and an `audit-z80` `diff` mode.
- Discarded: "fresh verification" before every claim, because it contradicts
  tested verification reuse; superpowers' own task reviewer also forbids
  re-running valid suites. The 5-round fix loop, because two focused attempts
  is a tested gate. The ban on parallel implementers, because disjoint
  ownership already prevents conflicts. Rationalization tables and reviewer
  praise sections, because of word budgets and findings-first reporting.
- Change review lives in `audit-z80`, not `workflow`, because its value is
  Z80-specific risk expansion (ABI callers, ISR accesses, map and generated
  code). Generic review stays in `workflow`; observed failures stay in
  `debug-z80`.
