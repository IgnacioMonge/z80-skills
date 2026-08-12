# Medium effort

Work directly in the main thread; do not spawn agents.

Before work, classify the effective mutation boundary using the intersection of
user authorization, project instructions, and the domain contract:

- **primary-tree read-only:** inspect and verify only; do not edit production
  files.
- **disposable-worktree-only:** edit or build only inside a verified,
  domain-gated disposable worktree; never edit or build the primary tree.
- **authorized primary-tree mutation:** edit and run checks only within the
  assigned ownership surface and effective authorization.

1. Establish bounded acceptance criteria.
2. Trace the smallest relevant code path and existing project patterns.
3. Make one coherent root-cause change.
4. Run the smallest deterministic check that catches breakage.
5. Inspect the critical diff, integration boundary, and repository status.

In `auto`, escalate to Heavy only when evidence reveals at least two concrete,
bounded, independent workstreams where parallelism or independent comparison
materially improves speed or required coverage. An explicit Medium request
remains direct unless the user changes the level.

Avoid durable status files unless the repository already defines them or the
user requests a cross-session handoff.

When blocked, report the failed step, evidence, completed work, affected
acceptance criterion, and required decision. Do not present partial work as
complete.
