# Policy decision evaluation

Revision 0.8.3 adds 18 optional decision scenarios in `policy.jsonl` and the
strict `schemas/policy-result.schema.json` output contract. Existing routing
and evidence datasets, schemas, runner code, and historical baseline are unchanged.

## Coverage

- Preserve Luna/Sol defaults; allow only assignment-scoped explicit Astra Medium.
- Reject automatic cost escalation, parent inheritance, unverified defaults,
  unsupported settings, and permission spreading to other workers.
- Distinguish workflow Medium from model reasoning effort `medium`.
- Honor already-authorized work and preserve explicit read-only requests.
- Read scope-relevant map sections and preserve explicit project read rules.
- Skip irrelevant inventory/freshness scans; preserve artifact proof gates.
- Reuse equivalent verified evidence without repeating valid checks.

## Validation and live execution

Local dataset validation with the existing runner (requires the Codex executable
on PATH, but does not call a model):

```sh
python3 scripts/run_behavior_evals.py --suite evals/policy.jsonl --dry-run
```

Without Codex, the runner's existing `load_cases`, `validate_cases`, and
`validate_json` functions can validate the dataset and output examples in Python;
this does not execute an evaluation model.

A live run is opt-in. Choose a runtime-supported evaluator model and effort
explicitly and pass `--suite evals/policy.jsonl` to the existing runner. That call
uses inference even though the scenarios prohibit delegated calls, mutations,
builds, and network work. Do not add this suite to the defaults or automatically
launch an Astra evaluator based on this document or the opt-in examples.

The example catalogs in the cases are hypothetical inputs, not claims about the
host. The output booleans describe the scenario's authorized actions; actual
execution remains read-only. `NONE`/false means not applicable or not selected.
`request_new_approval` concerns a necessary new user decision for the proposed
action, not permission already granted. `blocker_source` identifies the policy
source when dispatch is blocked; the rationale distinguishes that policy from
the hypothetical runtime limitation. Rejected dispatch does not block unrelated,
already-authorized direct work.

## Evidence limits

These cases test reported policy decisions, not actual spawn enforcement,
permission enforcement, complete task execution, or hardware correctness.
Review retained runtime traces to detect unintended calls; a passing JSON answer
alone cannot prove the absence of an attempt. No live model result, runtime
setting confirmation, cost saving, or quality gain is recorded for this revision.
Do not replace `baseline.json` with structural results or reinterpret its
historical 0.8.0 PASS entries as validation of 0.8.3.
