# Latest Session Work

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
