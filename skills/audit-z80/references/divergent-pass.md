# Divergent Audit Pass

Use this pass to widen the investigation queue without weakening precision. It generates hypotheses; it does not generate findings.

## When to run

- Run for `full`, `diverge`, broad reviews, unusual hand-written ASM, mixed C/ASM boundaries, ISR or memory pressure, fuzzy bugs, demoscene/forum-style code, and user requests for more imagination.
- Skip only when the user explicitly asks for a narrow local check.

## Process

1. Establish preflight first: toolchain, target, ABI, IX/IY status, ISR mode, `.map`/`.lst`, fixed RAM, overlays, stack gap, and copt rules.
2. Diverge before judging. If Agent tools are available, spawn isolated branches in parallel; otherwise run the frames separately in your own notes and say no Agent isolation was available.
3. Each branch outputs candidate failure modes only. It must not rank, prove, or write final findings.
4. Merge by failure mechanism, then score:
   - `impact`: crash/corruption/wrong behavior/user-visible stall severity.
   - `reachability`: likely runtime path, not just theoretical possibility.
   - `evidence`: how directly source, `.map`, `.lst`, or build artifacts can prove it.
   - `novelty`: catches a class the linear checklist might miss.
   - `fit`: matches the actual project constraints.
5. Investigate the highest-scoring hypothesis classes using normal audit rules.
6. Promote only with evidence. If proof is missing, classify as `ROBUSTNESS`, `SUSPICIOUS`, `NEEDS BUILD`, `THEORETICAL`, or drop it.

## Frames

Pick 5 frames for a normal pass. Always include one adversarial or wild frame.

| Frame | Ask |
|---|---|
| ABI skeptic | Where can C declarations, ASM stack layout, return registers, or callee cleanup silently disagree? |
| Interrupt adversary | What breaks if an interrupt fires at the worst instruction, or never fires again? |
| Memory accountant | Where can BSS, stack, fixed RAM, printer buffer, screen memory, overlays, or banks overlap? |
| Toolchain pessimist | Which comment, symbol name, optimizer rule, codegen pattern, or `.map` fact contradicts source intent? |
| C semantics pessimist | Which promotion, signedness, pointer mutability, array layout, or lifetime rule is being assumed incorrectly? |
| UX/timing observer | Which hot path can miss input, flicker, stall, corrupt attributes, or block long enough to be visible? |
| Speedrunner breaker | What legal but hostile path skips setup, re-enters a routine, exhausts stack, or hits an edge counter value? |
| Inversion | How would you intentionally make this code crash or corrupt state? Which safeguards are missing? |

## Guardrails

- Do not let novelty outrank proof. A clever hypothesis with no project-specific path is `THEORETICAL` or omitted.
- Do not report a `BUG` below `LIKELY` confidence. Use `ROBUSTNESS` or `SUSPICIOUS` until verified.
- Do not pad the final report with branch ideas. Report only investigated outcomes.
- Keep severity and confidence independent.
- When a branch identifies a scary class but evidence is absent, list it under residual risk with the exact artifact needed to verify it.

## Reporting

- In the coverage note, name the divergent classes checked, for example `ABI skeptic`, `interrupt adversary`, `toolchain pessimist`.
- If a class produced no finding, say `none found` and cite the evidence used.
- If a class was skipped, say why: narrow scope, missing artifacts, no Agent isolation, or not relevant to target.
