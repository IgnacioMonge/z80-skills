# Project Progress

## Current State

- Grok reads canonical `skills/` through `[skills].paths`; Claude uses junctions
  or symlinks. Neither needs copied skill trees. The
  [Grok installer](../scripts/install-for-grok.ps1) removes obsolete bundled
  copies; use `-SkipClaudeCleanup` to preserve Claude's links. See
  [installation](../README.md#installation).
- Audit and shrink share traversal, matching, reporting and map/symbol parsing
  in [scan_common.py](../skills/shrink-z80/scripts/scan_common.py); domain rules
  and reports stay separate.
- [Verification commands and version-specific history](latest_session_work.md)
  distinguish deterministic checks from live model evaluations.

No unimplemented durable milestone is recorded.

## Publication Gate

Before publishing, satisfy applicable deterministic checks, validate all skills
and manifests, and reconcile the committed changelog against the latest published
stable baseline, or the first release if none exists. Preserve cumulative pending
entries; a push alone does not require a version bump.

For a plugin release, align all three manifest versions. Reinstall from the
personal marketplace and confirm the installed version matches the manifest
before live behavior evaluations. Follow the repository's changelog/release
policy for versioning and stable-release notes.
