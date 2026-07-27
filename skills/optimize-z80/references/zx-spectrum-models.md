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

## Floating Bus And Snow

Only discuss these if at least one of the following is true:

- the current effect already depends on them
- tearing / raster sync is the active bottleneck
- the project profile is explicitly demoscene or disposable

Otherwise mark them as rejected ideas, not hidden options.

## Recommended Validation Ladder

1. listing + static cycle note;
2. emulator with contention enabled;
3. border or frame instrumentation;
4. validation on the target model or a faithful equivalent.
