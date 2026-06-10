# Blind Spots

Use this file as a pre-submit check against shallow audits.

## Do not finalize if you have done any of these

- Audited C logic but skipped the C to ASM boundary
- Assumed IX or IY status without checking build flags or startup clues
- Reported a 48K tradeoff as a bug without a concrete failure mode
- Flagged a theoretical interrupt hazard without proving the ISR model
- Ignored `.map` even though one exists
- Ignored `.opt` or `.rul` even though copt rules are part of the build
- Trusted comments about preserved registers instead of tracing the code
- Stopped after one bug class without saying anything about the rest of the requested coverage
- Skipped flag provenance around conditional branches after `ld`, `ex`, `push`, `pop`, `di`, `ei`, `inc`, or `dec`
- Treated frame hitches, flicker, missed input, blocking I/O, or attribute corruption as "performance only" when they are user-visible defects
- Ignored generated `.lst`/`.asm` after flagging a C pattern whose truth depends on SDCC output

## High-value reminders

- Packed-byte stack arguments are still one of the easiest ways to miss a real ABI bug
- Reused scratch RAM, overlay slots, and ring buffers can make state bugs look unrelated
- Relative branch range and fall-through intent need proof, not intuition
- Long DI spans, HALT under DI, odd `exx` parity, and stack-pointer tricks are not bugs by themselves; they are audit accelerants
- Screen, attribute, printer-buffer, system-variable, UDG, and esxDOS areas are UX/correctness contracts, not just addresses
- Evidence-backed `none found` is better than a vague low-confidence finding
