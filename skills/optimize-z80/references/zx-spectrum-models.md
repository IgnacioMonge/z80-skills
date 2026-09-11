# ZX Spectrum Models And Timing

Use this reference only for Spectrum targets and only when the recommendation depends on model behaviour.

## Model Split

Treat these as separate evidence buckets:

- 48K / 48K+
- 128K / +2
- +2A / +3
- Next or clone-specific targets

Do not silently transfer a cycle-exact trick from one bucket to another.

## What Counts As Safe Cross-Model Advice

Usually safe across standard Spectrum targets:

- dirty redraw
- screen-address tables
- duplicated-write removal
- attribute-only updates
- bank-aware hot/cold split
- avoiding unnecessary work in visible-frame paths

Not safe to generalize without model evidence:

- border-stripe timing
- floating-bus synchronization
- beam racing
- exact interrupt-window budgets
- contention claims that depend on machine generation

## Screen And Attribute Checklist

For render work, always confirm:

- bitmap traffic versus attribute traffic
- whether writes happen in visible display or border time
- whether the working set sits in contended RAM
- whether double-buffering uses legal screen pages on the active model

## Audio And Input

Use explicit lanes:

- beeper / border / PWM timing -> hardware_timing
- AY register batching / event compaction -> MEDIUM unless correctness is already proven
- keyboard scanning -> check matrix assumptions, ghosting tolerance, and polling cadence

## Paging Discipline

For 128K-family projects, prove:

- which code must stay resident
- which bank owns mutable state
- whether interrupts can fire while a banked routine is active
- whether page changes occur on hot paths or only phase boundaries

## Frame Window Planning

PAL reference timing, T-states relative to ULA /INT assertion:

| Model | T/line | T/frame | First contention |
| --- | ---: | ---: | --- |
| 48K | 224 | 69888 | 14335 |
| 128K / +2 | 228 | 70908 | 14361 |
| +2A / +3 | 228 | 70908 | Use its distinct contention pattern |
| Next / clones / other video modes | model-specific | model-specific | measure active configuration |

The approximately 14336 T initial 48K interval includes border/retrace;
it is not a universal VBlank budget. Some machines shift timing by one T.
Sources: [48K timing observations](https://worldofspectrum.org/faq/reference/48kreference.htm)
and [128K/+2/+3 timing](https://worldofspectrum.org/faq/reference/128kreference.htm).

Budget from a defined phase: subtract instruction completion before IRQ
acceptance, interrupt entry, ISR work, setup and a measured margin. Check every
memory/I/O access through the end of the burst: starting in border does not
make later visible-display writes uncontended. Include opcode, stack and table
traffic. Split work across windows/frames or use validated beam racing when
it cannot fit; see [copy/fill lower bounds](z80-techniques.md#ldi-chains-vs-ldir-vs-manual-copy).
On 128K/+2, odd banks contend; +2A/+3 contend banks 4-7. A high logical
address alone does not prove uncontended placement.

## IM2, I And Refresh Safety

I supplies the high address byte during refresh even outside IM2. On affected
48K machines, I=$40-$7F can cause snow; 128K/+2 can also lock up when I points
into contended memory. Sources: [48K refresh observations](https://worldofspectrum.org/faq/reference/48kreference.htm)
and [128K snow behavior](https://worldofspectrum.org/faq/reference/128kreference.htm).

For IM2, select a verified uncontended, resident vector area and ISR; check
the entire possible vector read, including a page-crossing second byte. Avoid
I=$40-$7F on affected models and check bank mapping for higher addresses.
Keep stack and handler visible throughout paging. Save/restore the interrupt
contract when returning to a runtime. DI does not remove the refresh hazard.
Do not extrapolate snow behavior to +2A/+3, Next or clones.

Avoiding this failure is ordinary correctness work; deliberately exploiting
it is a separate DANGEROUS `hardware_timing` candidate with explicit target
restriction and hardware validation. See [R sampling](z80-techniques.md#r-sampling-and-refresh).

## Floating Bus And Deliberate Snow Effects

Only propose these effects if at least one of the following is true:

- the current effect already depends on them
- tearing / raster sync is the active bottleneck
- the project profile is explicitly demoscene or disposable

Otherwise mark them as rejected ideas, not hidden options.

## Recommended Validation Ladder

1. listing + static cycle note;
2. emulator with contention enabled;
3. border or frame instrumentation;
4. validation on the target model or a faithful equivalent.
