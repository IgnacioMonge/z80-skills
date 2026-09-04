# Latest Session Work

## 2026-09-04 — 0.8.0

- Consolidated the pending documentation, BridgeZX, routing, evidence, and
  Spectranext changes; aligned the Codex, root, and Gemini manifests at 0.8.0.
- Reviewed BridgeZX against the official local client and corrected cancellation
  during preparation. Corrected named timing annotation parsing and made the
  shrink freshness fixture independent of subprocess duration.
- Validated all eleven skills, plugin metadata, 71 unit tests, and the audit and
  shrink smoke checks. Installed and confirmed the 0.8.0 Codex plugin.
- Installed 0.8.0 passed all 34 routing and four evidence cases in fresh,
  read-only Codex sessions; the verified summary is in `evals/baseline.json`.
- Workflow model selection remains canonical in `skills/workflow/`; Grok
  preserves its host-specific model controls and direct Medium execution.

## 2026-09-02

- Added `document-z80`, an explicit routed skill for evidence-grounded public
  repository documentation, compact information architecture, and maintained
  English/Spanish parity.
- Connected it to `route-z80`, the shared adaptive workflow, Codex/Grok/Claude
  installation, bilingual operator documentation, and direct/indirect routing
  evals.

## 2026-08-25

- Added `send-bridgezx`, a routed explicit skill that validates local sources,
  selects the explicit or last-known BridgeZX IP, verifies Classic/Next,
  supports a relative destination and explicit sequential delivery, and stops
  without retrying uncertain outcomes.
- Added deterministic executor tests and direct/indirect routing cases.

## 2026-08-19

- Added a debug evidence eval for open causality and stale map evidence.
- Removed the forked Grok workflow policy; the installer now copies and patches
  the canonical workflow in its staging tree.
- Added `route-z80` to Grok installation and Claude sync, with English and
  Spanish operator documentation and installer regression coverage.
- Moved the detailed debug causal method behind a progressive reference and
  added runtime-portability contracts to debug and develop.
- Added explicit workflow invocation policy metadata.
- Consolidated duplicated audit/shrink scanner mechanics into the canonical
  shrink `scan_common.py` module and added a structural anti-drift test.
- Reconciled behavior-eval metadata with the manifest version used by each run.

## Handoff

The normal validation target is `python -m pytest -q`. The standalone audit and
shrink smoke scripts exercise analyzer behavior beyond the root unit-test
discovery. Runtime model eval results live under ignored `evals/results/`; only
verified summaries belong in `evals/baseline.json`.
