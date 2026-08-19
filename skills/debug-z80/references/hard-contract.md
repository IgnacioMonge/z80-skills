# Hard Contract

Apply this contract to every real `debug-z80` task.

## Evidence Boundary

- Anchor observations in current in-scope source, an exact observed failure, or
  artifacts proven fresh for that source, target, configuration, and recipe.
- Treat stale maps, symbols, listings, binaries, screenshots, previous sessions,
  generic Z80 advice, and external reports as hypothesis seeds only.
- Record the target and relevant execution context: Z80/compatible CPU, ZX model,
  ROM or firmware, emulator or hardware, clock, toolchain version, flags, memory
  model, bank layout, and interrupt mode. Record only fields that can change the
  result.
- A plausible explanation is not causal evidence. Require a prediction and a
  discriminating observation, safe negative control, or equivalent controlled
  comparison.
- Never weaken an assertion, accept broken output as the new baseline, or revise
  a requirement merely to make the failure disappear.

## Mutation Boundary

Classify the task before a Medium or Heavy workflow route:

- Diagnosis from existing source and evidence is `primary-tree read-only`.
- A reproduction, build, measurement, emulator run, instrumentation probe, or
  candidate repair is `disposable-worktree-only` while causality remains open.
- A repair becomes `authorized primary-tree mutation` only when the user asked
  for a fix and the causal owner, affected files, invariant, rollback, and narrow
  acceptance check are known.

For every disposable command:

1. Capture the primary tree's initial status and tracked diff. Preserve all
   pre-existing user work.
2. Create a detached disposable worktree outside the primary tree at the same
   revision. If relevant uncommitted source is part of the failure, mirror only
   the declared in-scope state and record omissions.
3. Invoke every build, test, measurement, emulator, instrumentation, or patch
   command through `<skill-dir>/../../scripts/run_in_worktree.py`, passing
   `--primary <primary-root> --worktree <worktree-root> -- <command>`.
   Never pass the temporary directory as a wrapper `cwd`; a refused or
   unverifiable gate is not permission to retry in the primary tree.
4. Do not copy credentials, private unrelated files, or undeclared user changes
   into the disposable tree.
5. Remove probes, unregister the worktree, and delete its temporary directory.
   Confirm that the primary status and diff gained no diagnostic delta.

If a disposable worktree cannot be created, remain read-only, mark the runtime
check unavailable, and return `NEEDS_EVIDENCE`. Do not patch the primary tree as
a fallback.

## Repair Integrity

- Interpret authorization by requested result. “Find the cause” does not
  authorize editing; “find and fix” does once the repair gate is satisfied.
- Preserve public and runtime contracts unless changing one is explicitly
  authorized: C/ASM ABI, registers, flags, stack, interrupt state, vectors,
  bank/page state, sections, absolute addresses, loader offsets, file formats,
  ports, ROM/firmware calls, timing windows, and maintained targets.
- Keep unrelated cleanup, optimization, formatting, dependency upgrades, and
  toolchain changes out of the repair.
- Do not publish, push, merge, tag, flash hardware, alter persistent emulator or
  toolchain configuration, or change external systems without separate explicit
  authorization.
- Before `FIXED`, inspect the final diff and repository status, confirm the
  failure check passes, and state any untested target, hardware path, timing
  path, or residual risk.
