# Causal Method

Use this reference only after the `debug-z80` entry gate passes.

## Causal Loop

1. Capture the complete primary evidence: command and cwd, first meaningful
   diagnostic before cascades, full relevant log or stack span, failing input,
   target, toolchain and flags, expected result, actual result, and frequency.
2. Reuse fresh evidence when it identifies the source state and configuration.
   Otherwise reproduce once with the narrowest command or input that preserves
   the symptom. Do not repeat an unchanged deterministic command.
3. Compare one known-good case when available. Change one axis at a time:
   source revision, target, 48K/128K/Next model, emulator/hardware, ROM,
   toolchain, optimization flags, memory map, bank state, interrupt state,
   input, or timing.
4. Inspect the failure locus, its immediate producer, applicable generated
   ASM/listing/map, and the smallest recent change surface. The owner is the
   first component that receives valid state and emits invalid state, or the
   component defining the violated invariant.
5. Keep one primary hypothesis and at most one credible alternative:

```text
Observed:
Hypothesis: X causes Y through Z.
Prediction: check C will observe P if true, otherwise N.
Evidence:
Falsifier:
Fix owner:
```

6. Run one check that discriminates the live hypotheses. Revise after a
   falsifier; do not apply several fixes at once.
7. Stop expanding when one explanation predicts all observed behavior and
   identifies a local owner or an external cause.

## Z80 Symptom Router

Choose the first discriminator that fits; do not run every row.

| Observed symptom | First discriminator |
| --- | --- |
| Assemble, compile, or link failure | Read the first complete diagnostic and reproduce its exact command; inspect the generated symbol, section, ABI, or library boundary it names. |
| Crash, corruption, or bad return | Start at the nearest owned boundary; verify stack, return address, calling convention, preserved registers and flags, alternate registers, and paging state. |
| ISR-only, flaky, or timing-sensitive failure | Declare the sample or event stop rule; capture interrupt state and event order, then compare with interrupts removed or serialized when safe. Never substitute sleeps for evidence. |
| Wrong output or input-specific failure | Minimize the input and compare expected versus actual state at the nearest invariant, including signedness, width, lifetime, table bounds, and generated code. |
| 48K/128K/Next, bank, or overlay divergence | Compare the same path with bank/page/slot state, residency, stack visibility, and restoration obligations made explicit. |
| Emulator versus hardware divergence | Hold binary, ROM, model, clock, contention, floating-bus assumptions, ports, and undocumented opcodes constant one axis at a time. |
| Performance or memory regression against a known baseline | Establish one fresh known-good and one fresh known-bad point, then partition code, build, map, contention, and target deltas. |
| Failed repair | Revert the hypothesis, not the evidence; confirm the original reproduction still fails and reassess ownership before another edit. |

Generic Z80 knowledge, file names, scanners, prior reports, and stale artifacts
generate hypotheses only. Confirm behavior from current source and fresh,
source-matched artifacts. Inspect generated instructions when compiler behavior,
ABI, timing, or linked pulls are causal.
