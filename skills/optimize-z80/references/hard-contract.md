# Hard Contract (shared)

Evidence meaning, provenance, and non-fabrication are mandatory and cannot be
overridden. Operational read-only, scope, measurement, and sandbox-retention
defaults change only when the user explicitly requests that change.

## 1. Evidence = current code only

- Every finding, promoted candidate, byte claim, or `CONFIRMED`/`EXACTO`/`PROVEN`
  statement MUST be anchored to **current in-scope source** and/or **build
  artifacts proven fresh against that source**.
- Allowed anchors: files in the working tree under the declared scope; symbols
  and sections from a `.map`/`.sym`/`.lst`/generated `.asm` produced from that
  same source; opcode counts of those current bytes.
- Forbidden as proof (may be used only as **search seeds / hypotheses**):
  - prior audits, session memory, chat history, or "we already found this"
  - forum posts, blackbooks, demoscene writeups, external optimizers
  - stale maps/listings/binaries whose mtime or content cannot be tied to the
    current source (treat as `REQUIERE BUILD` / non-proof prioritization only)
  - generic "on the Z80 people do X" without a project-local site
- Scanners, subagents, and idea banks emit **candidates only**. The main agent
  promotes only after re-reading the current site and counting current bytes.
- If evidence is missing: say so, use `NEEDS BUILD` / `REQUIERE BUILD` /
  `SPECULATIVE`, or drop. Never invent historical continuity as proof.

## 2. Primary tree read-only + disposable sandbox

- The **primary project directory and its checked-out branch are read-only**
  for analysis/audit/measurement passes. No edits, no commits, no baseline
  rewrites, no tracked `.gitignore` changes, no leftover build dirt from the skill.
- If a build, measurement, or one-candidate trial is required:
  1. Capture the primary tree's initial status and tracked diff. Pre-existing
     user changes are allowed and must be preserved.
  2. Create a **detached disposable worktree** in a host temporary directory
     outside the primary tree. Do not edit `.git/info/exclude`, tracked ignore
     files, or project configuration merely to host it.
  3. Run builds/patches **only** there. Invoke every sandbox build, test,
     measurement, or patch command from an allowed directory with the host
     Python interpreter. First canonicalize the discovered `SKILL.md` path by
     following symlinks and Windows junctions, derive `<skill-dir>` from its
     physical parent, and verify
     `<skill-dir>/../../scripts/run_in_worktree.py` exists. A missing runner
     below an uncanonicalized catalog alias is not evidence that the packaged
     runner is absent. Invoke the verified runner, passing
     `--primary <primary-root> --worktree <worktree-root> -- <command>`.
     Never pass the temporary directory as a wrapper `cwd`: a rejected,
     substituted, or unverifiable `cwd` is a hard failure, never permission to
     retry the gate in the primary tree.
  4. Before finishing, compare primary status/diff with the captured baseline.
     Require no skill-caused delta; do not require an initially dirty tree to
     become clean.
  5. **Delete** the disposable worktree and temporary directory at the end.
- **Do not retain** experimental worktrees by default.
- Retain a sandbox **only** if the user explicitly asks to keep it (e.g. for
  hardware flash). Report paths when retained.
- Implementing edits in the primary tree is **out of scope** for analysis modes.
  It requires an explicit user request to apply changes, and still must not
  silently alter unrelated files.
- If worktree creation is impossible: stay pure read-only on primary, mark
  measurement unavailable, and do not patch primary "just this once".
