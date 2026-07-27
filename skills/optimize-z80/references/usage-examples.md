# Usage Examples

## Triage

Prompt: analyze this project read-only and rank the best optimization paths.

Expected:

- run preflight and report policy, target, bottleneck, and freshness;
- load only references and lanes justified by observed zones;
- reject wrong-target or forbidden candidates;
- return at most three experiments, with stale evidence capped below `PROVEN`.

## Measurement

Prompt: produce a fresh size/layout baseline without changing my project tree.

Expected:

- create a detached disposable worktree in a safe host temporary directory;
- freeze toolchain/configuration and run the smallest baseline build;
- capture the selected fresh metrics and contamination check;
- delete the worktree after reporting.

## Approved Experiment

Prompt: measure candidate #1 and keep its worktree for hardware testing.

Expected:

- change one variable in the disposable worktree;
- rebuild and compare the same target/fixture against baseline;
- validate implicated behavior, ABI, timing, paging, and target limits;
- keep the worktree only because the prompt explicitly requested it;
- leave the primary tree exactly at its captured baseline.
