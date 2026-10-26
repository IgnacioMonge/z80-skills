# Latest Session Work

## Verification Handoff

Run from the repository root with the host-approved Python interpreter:

- `python -m pytest -q`: deterministic suite; `pytest.ini` handles collection.
- `python scripts/validate_skills.py`: all eleven skill definitions.
- `python skills/audit-z80/scripts/smoke_test.py` and
  `python skills/shrink-z80/tests/run_smoke.py`: additional analyzer checks.
- `python scripts/run_behavior_evals.py --dry-run`: default evaluation datasets;
  see [validation](../README.md#validation) for optional policy cases and live runs.

Regression lessons: compare Python executable identity, not Windows path
spelling; build tests use `python_for_shell` like production. Preserve
[BridgeZX preparation cancellation](../skills/send-bridgezx/scripts/test_bridgezx_transfer.py),
[named timing-annotation parsing](../skills/optimize-z80/scripts/test_tstate_estimate.py) and
[freshness fixtures independent of subprocess duration](../skills/shrink-z80/tests/run_smoke.py).

## Verified History

On 2026-09-04, installed 0.8.0 passed 71 unit tests, eleven skill definitions,
manifest consistency and audit/shrink smoke checks. Its 34 routing and four
evidence cases passed in fresh read-only sessions with the runtime-default model.
The [baseline](../evals/baseline.json) records the live evaluation results and a later
five-case routing check on installed 0.8.4 (2026-10-09).

These results do not establish full live coverage for later versions or expanded
datasets. Raw results/traces stay in ignored `evals/results/`; retain only verified
summaries in the baseline. [The diary](project_diary.md) retains decision rationale.
