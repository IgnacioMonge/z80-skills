# Verification reuse

For all levels and domains:

- A+B passed and still valid: run only C for A+B+C. Reuse evidence and artifacts
  across agents, phases, branches, and worktrees after establishing equivalent
  relevant inputs, dependencies, target, configuration, toolchain, and environment.
- Rerun only checks invalidated by changes, failures, or uncertainty.
- Before costly builds, state the missing evidence/artifact and why existing
  results or planned delivery cannot supply it. No unmet need: no build.
- Inspect aggregate dependencies; run missing subtargets. Combine compatible
  validation and delivery builds; avoid duplicate matrices and clean rebuilds.
  Broaden checks for affected contracts or requirements, not file extensions.
- Required repetition needs the exact project/domain rule or inseparable build
  dependency as justification; preserve gates. Never reuse unverifiable evidence.
- Before claiming completion, map every acceptance criterion to observed evidence:
  a valid check, inspected diff, or artifact. A related check (lint for a build)
  or a worker's assertion is not evidence; report uncovered criteria as unmet or
  unverified.
- Stop investigation when causality is established; finish remaining acceptance
  checks and delivery, then stop. Keep evidence in task context, without tooling.
