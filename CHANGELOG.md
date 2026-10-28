# Changelog

## [Unreleased]

No published stable release or release tags are currently available in the
repository; these entries track development toward the first published release.

### Added

- `audit-z80` `craft` mode answers whether an expert Z80/SDCC programmer would
  accept the code or find it inflated, hollow, duplicated, or non-idiomatic;
  `craft diff` judges only what a change set adds. `scripts/craft_scan.py`
  queues structural C and ASM leads (forwarders, single-use helpers, constant
  or unused parameters, clone families across files and overlays, untouched
  register saves, codegen outliers from a fresh map, narrating and history
  comments) with churn-weighted hotspots, counting references across the whole
  project and both arms of `#if`/`#else` and ASM `IF` blocks. Dead code,
  duplicated literals and ASM micro idioms stay with `shrink-z80`'s scanners.
  `references/craft-review.md` requires an expert alternative, a measured delta
  and a preservation argument per finding, adds a blind-rewrite lane that never
  sees the original body, and ends in an evidence-based verdict.
- Reviewed Zeda and baze routine corpora add biased single-pair and CPI loop
  control, iterative division near powers of two, signed saturating narrowing
  and Galois LFSR steps, with original examples, emulator tests and a source
  assessment of checked kernels, contract errors and reuse terms.
- Reviewed Antique Toy references cover math tables, generated rendering,
  simulation, asset representation, audio queues and timeline data, with a
  source assessment and explicit limits on executable and hardware evidence.
- Compact ordered FSM rows, archive-member extraction granularity,
  A-preserving predicates with Z results, and page-local screen history, with
  applicability conditions, fallbacks and executable examples.
- `shrink-z80` winner pass: `scripts/winner_census.py` ranks resident code used
  by a single overlay (with the helpers that move with it), unreferenced
  routines, caller-side stack cleanup per callee and repeated SDCC frame or
  boolean idioms from a linked map and its overlay binaries. `scan` now works
  six winner families (overlay moves, gate-dominated re-checks, allocation
  budget sweep, peephole helpers, callee/fastcall ABI, twin routines) above a
  30 B materiality threshold; micro lanes run only when named, and `agent`
  runs the census and asks before launching shrink-agent.
- `optimize-z80` scorer enforces `constraints.maintainability = "release"`
  (vetoes `undocumented`, `smc`, `sp_abuse` and `interrupt_windows` tags unless
  `[forbidden]` sets them to `false`) and per-target `resident_ceiling` /
  `stack_gap_floor` gates from `[targets.<name>]` against candidate
  `target_metrics`; a missing or failing target vetoes the candidate, and
  omitting `target_metrics` demotes `PROVEN` to `LIKELY`. `--profile auto`
  derives scoring weights from the policy `priority`.
- Workflow roles map to Gemini / Antigravity `invoke_subagent` types and model
  tiers.
- `tools/shrink-agent`: unattended Claude API loop that applies size reductions to a
  z88dk project in a disposable worktree, one routine per commit, gated by all-target
  builds, byte measurement, optional tests and an independent model review.
- Claude Code host mapping in the workflow roles policy: `Agent` subagent types,
  explicit `opus`/`sonnet` selection, no reasoning-effort parameter, no Astra
  equivalent. Codex tables and defaults are unchanged.
- Claude Code installation notes: per-skill junctions from `~/.claude/skills`
  plus a `~/.claude/scripts` junction so `scripts/run_in_worktree.py` resolves.

- Explicit, assignment-scoped Astra Medium option for causal/high-risk delegation.
  Automatic fallback, inheritance, unverified defaults, and effort upgrades cannot
  enable it.
- Opt-in policy decision cases cover authorization, model selection, selective
  context, and verification reuse without replacing historical evaluation results.
- `audit-z80` `diff` mode reviews the correctness risk of a change set: merge-base
  range by default, one focused check per named Z80 risk, and a `BLOCK` /
  `VERIFY FIRST` / `NO BLOCKER FOUND` verdict. Routing and two routing
  evaluation cases cover the boundary with `debug-z80` and generic `workflow`
  review.

- Portable workflow, Z80 domain routing, eight engineering specialists, and
  guarded BridgeZX delivery, with installation tooling and English/Spanish
  documentation.
- Isolated-worktree tooling and routing/evidence evaluation infrastructure.

### Changed

- English and Spanish READMEs cover every supported host: Codex, Claude Code
  and Grok Build installation and invocation, partial Gemini / Antigravity
  support, per-host delegation models, the optional `shrink-agent` tool, and
  root `pytest` validation, with behavior evals marked Codex-only.
- Agent context is compacted around canonical sources, current Grok/Claude
  installation, actual tooling dependencies and distinct worktree boundaries;
  validation commands, historical evidence and decision rationale are preserved.
- Heavy workflow de-escalates to direct work when preflight or a first worker
  leaves fewer than two independent workstreams, and passes one immutable
  preflight/baseline digest to worker capsules so workers neither repeat
  discovery nor create competing worktrees.
- `shrink-z80` moves the shrink-agent setup, `--dry-run` gate and runbook into
  `references/dispatcher.md`, and resolves the worktree runner from the
  physical skill directory after following symlinks and Windows junctions.
- Workflow delegation adds a closed worker status set, verifier finding triage,
  bounded waits with worker resumption, file-less recovery after context
  compaction, and one-worker batching of same-shape edits. Completion maps every
  acceptance criterion to evidence and lists decisions made on the user's behalf.
- Audit, shrink, and optimize hard contracts treat commit messages, change
  descriptions, and asserting comments as search seeds, not proof. Audit coverage
  states a reason for every skipped area, and audit and shrink instructions use
  the host-selected Python interpreter instead of a hardcoded `python3`.
- The nine routed specialists declare `disable-model-invocation: true` so Claude
  Code exposes only `route-z80` and `workflow` implicitly, mirroring the Codex
  implicit-invocation policy. Hosts without that field ignore it.
- The Grok installer test runs PowerShell with `-ExecutionPolicy Bypass`, so a
  Mark-of-the-Web on the checkout no longer fails it under `RemoteSigned`.
- Workflow delegation uses Sol 6.1 instead of Luna/Sol 5.6, preserving each
  assignment's reasoning effort and the explicit Astra Medium opt-in. Current
  documentation and policy evaluation cases follow the new defaults; historical
  evaluation results retain their recorded models.
- Optimize references quantify copy/fill costs, explain model-specific raster
  windows, screen stepping, refresh/snow and undocumented operations, and
  separate demoscene sizecoding from throughput/timing objectives.
  A coverage map distinguishes developed, mentioned and absent families;
  selectively loaded loop/data and arithmetic references, sprite specialization
  and runtime guidance add cost boundaries and executable example checks.
- Behavior evaluations record runtime traces, token usage, observed actions,
  fixture changes, timeouts, and source fingerprints; requested settings remain
  separate from runtime-confirmed data. Additional unprompted evidence cases
  check that domain safeguards do not depend on hints in the request.
- Router and specialist entrypoints load only relevant instructions, share
  execution and worktree contracts, and preserve domain-specific mutation gates.
- Default size scans begin with the highest-value evidenced lane and expand
  only when useful; explicitly exhaustive scans retain full coverage requirements.
- Workflow uses direct Light/Medium execution and bounded Heavy coordination,
  shared model routing, focused repair loops, and bounded evidence handoffs.
  Verification and repair instructions are condensed, with redundant reminders removed.
- English/Spanish README catalogs link to skill contracts instead of repeating
  them; repository maps and project context no longer duplicate the catalog.
- Audit, shrink, and optimize share the external-research procedure while keeping
  domain triggers and evidence rules; organization reports use common fields.
- Audit analyzers share directive-symbol parsing and call the path helper directly.
- Verification now reuses valid results across phases and trees, executes only
  missing or invalidated checks, inspects aggregate build dependencies, and
  combines compatible validation and delivery builds to avoid duplicate work.
- Grok Build loads the canonical `skills/` trees in place through
  `[skills].paths`. The Grok installer no longer copies or patches skill trees
  into `~/.grok/skills`; it removes those obsolete copies instead.

### Fixed

- Standard `python -m pytest -q` collects same-named test modules without
  collisions; shrink-agent tests handle Windows Python paths with spaces and
  aliases through the existing shell-path helper and executable identity checks.
- Plugin version 0.8.7 refreshes installed copies after the routine-corpora
  references were added; a cached 0.8.6 copy does not contain those additions.
- Plugin version 0.8.6 refreshes installed copies after the Antique Toy
  references were added; a cached 0.8.5 copy does not contain those additions.
- Repository-owned skill validation accepts boolean `disable-model-invocation`
  without changing invocation policy and survives skill-creator updates.
  Regression tests and documented dependency setup cover the durable validator.
- Plugin manifests use the same version across Codex, the root package, and
  Gemini, so package consistency checks pass after restoring the 0.8.3 tree.
- Workflow distinguishes explicit user overrides from still-applicable project,
  domain, runtime, and evidence requirements; skill-induced stops identify their
  exact source. Organization maps and shrink scans are now scope-conditional.
- Develop and organize activation descriptions are shorter, with their detailed
  scope and exclusions retained in the skill body.

- Optimize's T-state estimator accounts for IX/IY half-register loads,
  INC/DEC and accumulator arithmetic, recognizes SLL, and reports unsupported
  half-register combinations as unknown instead of assigning fallback costs.
- The T-state estimator times CPL, SCF, CCF, DAA, NEG, RETI, RETN, RLD, RRD,
  IM, RLC/RRC and the Z80N extended instructions, with NEXTREG at 17 T
  (`reg,A`) and 20 T (`reg,value`).
- `map_hotspots.py` folds compiler local labels and string literals into the
  owning function and sizes each section's last symbol from z88dk
  `__<section>_tail` constants.
- `winner_census.py` no longer proposes moving a routine to one overlay when
  another overlay references it through a table word, nor lists
  table-referenced routines as unreferenced. It counts SDCC's 5-byte
  `ld hl,n; add hl,sp; ld sp,hl` caller cleanup, marks single-site ABI
  candidates as fastcall-only, and reports resident net bytes for frame-idiom
  helpers when overlays exist.
- BridgeZX instructions now match the executor's client-resolution precedence
  and reject an invalid supplied root without silently selecting another client.
- Audit reports place findings before profile details outside preflight mode.
