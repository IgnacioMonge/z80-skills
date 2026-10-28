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

## 2026-10-28 — Craft review in audit-z80

- Added a `craft` mode to `audit-z80` for the question "would an expert
  Z80/SDCC programmer accept this code?". It lives in audit, not `shrink-z80`,
  because shrink accepts only net byte savings and rejects zero-byte waste such
  as narrating comments or hollow layers; not in `workflow`, because the value
  is Z80 cost evidence (maps, SDCC codegen, overlay and target ownership).
  Generic naming or readability review stays in `workflow`.
- Authorship detection was discarded: no detector reliably identifies
  AI-generated code, and the useful verdict is the cost of each construct.
- A blind-rewrite lane counters self-approval: the delegate gets the contract
  and tests, never the body.
- `zcc` v24860 checks: SDCC does not pool identical string literals or inline
  single-use statics, but it narrowed an 8-bit-bounded `int` counter, so
  declared counter width alone is not byte evidence.

## 2026-10-29 — Cross-review of craft mode (Codex, Grok, Gemini)

- The reviewers' main defect: flag idioms (`cp 0`, `or a`, `djnz`) checked
  only the first flag consumer and recommended unsafe drops (`xor b / cp 0 /
  jr nz / ret pe`). A liveness walk fixed them, then the corpus prune below
  removed them.
- Corpus prune: 9 projects (~105k lines). Removed detectors that duplicate
  `shrink-z80` (`deadcode_scan.py`, `literal_dup_scan.py`, `wide-c-type`,
  `large-switch-dispatch`, `asm-micro.md` `djnz`, booleanization) or yielded
  0-2 leads (`cp 0`, redundant zero test, unreachable, commented-out code,
  struct by value), and `push`/`pop` copies (T-states only, `optimize-z80`).
  The flag model went with them; the scanner fell from 2188 to 1771 lines.
  The removed unreferenced-static check gave 19 leads on BitStream-SPCTX,
  false where verified (`fs_init`, conditional `#include`); shrink's gave 2.
- Scope fixes from the corpus: compiler output copied into `src/`
  (`*.c.asm`, "Reconstructed for z80 Module Assembler") is not reviewed;
  clone units come from target files only (documentation snapshots made a
  38-member family); sjasmplus `:`-separated statements are split.
- C conditionals get a second pass over the last `#else`/`#elif` branch: the
  shared `active_c_lines` skips every `#else`, which hid 2122 lines of
  NetChessZX Spectrum code behind `#ifdef NETCHESSZX_HOST_TEST`. A function
  whose body a first-pass function already owns is only another header.
- ASM inside `IF` arms is scanned (20% of NetChessZX instructions); `IF 0`
  arms are dead code. Local windows never cross a directive.
- Clone matching runs on k-gram ids instead of tokens: identical output,
  19 s to under 2 s on NetChessZX.
- Kept against review: moving overlay code resident is never a saving
  (project architecture rule); touching one clone member keeps the family in
  `craft diff`, since editing one copy is the classic clone bug.
