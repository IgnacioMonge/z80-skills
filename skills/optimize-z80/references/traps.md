# Traps

## Optimization Traps

- Optimizing CPU when bottleneck is I/O, wait, disk, network, or frame delay.
- Optimizing cold setup while hot loop dominates UX.
- Chasing small byte wins with high regression risk.
- Moving code to overlay if latency path needs it resident.
- Adding tables that save cycles but blow resident size.
- Adding compression whose decoder/runtime cost exceeds saved bytes.
- Using a generic optimized routine with wrong calling convention or clobbers.
- Applying MDL/optimizer output wholesale without ABI/timing review.
- Optimizing AY/audio player at cost of frame stability without timing test.
- Using undocumented opcodes without compatibility decision.
- Using SP abuse without interrupt proof.
- Using floating bus without model/fallback proof.
- Trusting compiler intuition without map/listing evidence.
- Treating missing generated asm as a blocker.
- `sizeof("literal")` under SDCC materializes the literal in the target binary; use a macro constant or host-side assert.
- Judging a calling-convention change by the callee alone: fastcall/`__sdcccall(1)` often fatten every callsite; net = callee delta minus sum of callsite deltas from the linked map (measured case: promised win collapsed to 5 bytes across 11 callsites).
- Accepting a candidate that fits one target but busts another target's resident ceiling or stack-gap floor; multi-target projects gate on ALL targets, same build.
- Deferring the link-time byte gate: any block destined for a constrained target is assembled and linked with production flags in the phase it is written; qualitative ASM review cannot detect physical impossibility (measured case: a portable dispatch core cost +31 KiB resident and could never link).
- Recommending sizecoding tricks for maintainable application code.
- Proposing C-to-ASM for code whose cost is actually overlay thrash.
- Comparing T-states without accounting for Spectrum contention.

## Process Traps

- Running broad `git --all` commands in repos with tool refs.
- Rebuilding repeatedly to answer read-only questions.
- Launching a second build while first still runs.
- Dumping huge logs into context.
- Retrying a failed command unchanged.
- Letting one recent topic dominate global scope.
- Returning per-agent reports without a final judge.
- Installing or invoking external tools without approval.

## Review Traps

- Long report with no ranking.
- Per-zone findings but no global strategy.
- Multiple agents repeating same candidate.
- No validation path.
- No rollback plan.
- No process self-tuning notes after failures.
