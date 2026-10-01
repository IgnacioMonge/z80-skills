# Reporting

Return findings first. Do not bury real bugs under a long warm-up.

## Finding format

For each finding, include:

```text
[SEVERITY] ID - short title
Type: BUG | ROBUSTNESS | PERF/UX | TRADEOFF | THEORETICAL | OBSERVATION
File: path:line
Confidence: PROVEN | LIKELY | SUSPICIOUS | NEEDS BUILD
What: exact defect or concern
Evidence: concrete proof, symbol, offset, trace, or code contradiction
Impact: practical trigger and user-visible consequence
Fix: specific change or verification step
Cost: bytes, RAM, speed, complexity, or build verification needed
Hardware/toolchain note: real hardware, emulator, SDCC/z88dk version, startup, or generated-artifact dependency when relevant
```


## Severity Scale

- `CRITICAL`: reachable crash, corruption, hang, broken stack/ABI, or exit with SP/interrupt state corrupt.
- `HIGH`: probable bug with visible impact or limited corruption.
- `MEDIUM`: reachable robustness issue, important edge case, or significant UX defect.
- `LOW`: verified observation, tradeoff, or non-blocking improvement.

Severity is independent of `Type` and `Confidence`.

## Ordering

- Order by severity first, then confidence
- Put BUG items before tradeoffs and observations
- Put user-visible stalls, input loss, flicker, corrupt graphics, and blocked feedback under `PERF/UX` unless they already qualify as `BUG`
- If the user asked for a review, keep the overview short and secondary

## Coverage note

After findings, add a short coverage block:

- scope audited
- categories covered
- skipped areas or unknown artifacts
- residual risks or testing gaps
- generated artifacts used: `.map`, `.sym`, `.lst`, generated `.asm`, `.opt/.rul`, or `none`

## No-finding case

If you do not find a bug:

- say that explicitly
- mention the strongest residual risks or unverified areas
- do not pad the answer with weak observations just to sound busy

## Hard contract

Obey `hard-contract.md`: current-code evidence only; primary read-only; disposable sandboxes deleted by default.
