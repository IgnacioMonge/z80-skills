# Adaptive Agent Orchestration

Use this only after preflight shows more than one independent investigation
lane. The main agent owns evidence thresholds, promotion, severity, confidence,
and the final report.

## Capacity Negotiation

Inspect the subagent capabilities actually exposed by the runtime. Do not
assume a model name, role type, or fixed number of slots.

| Demand | Delegation |
|---|---|
| Focused | No delegate |
| Standard | One delegate on the highest-uncertainty lane while the main agent checks another lane |
| Deep | After reserving capacity for the main agent, run `min(useful independent lanes, available delegate capacity)` in parallel, normally no more than three delegates in one wave |

Start a second wave only when the first wave exposes a new high-impact lane,
contradiction, or exact verification question. More agents are not useful when
they would reread the same files or return the same hypothesis class.

If no subagent tool is available:

- run the highest-risk lane in the main pass;
- continue to another lane only if it can change the result;
- list materially skipped coverage;
- never label serial notes as simulated agents.

If a spawn fails, times out, or capacity drops, keep completed results and do
not relaunch the same brief unchanged. Cover locally only the missing lane that
can still change severity, confidence, or residual risk.

## Adaptive Model and Effort Routing

After preflight and the baseline digest, route every selected lane separately.
Do not map lane names or demand classes to fixed model/effort pairs.

1. Inspect the models and reasoning levels actually exposed by the runtime.
2. Use the highest-capability available decision model at a high reasoning
   tier, normally `high` or `xhigh`, to choose the routes. If the main agent
   cannot provide that tier and explicit overrides are available, run one
   read-only routing adviser before launching investigation delegates; the main
   agent verifies its proposal. Reserve `max` for a contradictory or unusually
   high-impact preflight, not as a default; never enable nested delegation.
3. For each lane, assess ambiguity, cross-domain coupling, impact, evidence
   freshness and determinism, context breadth, and verification burden.
4. Select model capability for ambiguity, judgment, and context handling;
   select reasoning effort independently for proof depth and checking. Use the
   least costly setting likely to clear the evidence gates.
5. Record the requested model/effort, one-line rationale, and actual setting or
   fallback. If an override requires a smaller context fork, pass the compact
   baseline digest instead of full history.
6. Re-evaluate after lane results. Escalate only for contradictions, missing
   proof, low confidence, or a candidate that can change severity, confidence,
   or residual risk. Never rerun an unchanged brief merely at higher effort.

## Lane Selection

Choose from project signals; do not launch every lane by default.

| Lane | Select when |
|---|---|
| `abi-codegen` | mixed C/ASM, inline ASM, calling conventions, IX/IY, generated ASM/listings, copt rules |
| `interrupt-memory` | ISR/DI/EI, shared state, stack/BSS/fixed RAM, overlays, banks, paging |
| `semantics-reachability` | C promotion/signedness/lifetime, buffers, hostile paths, re-entry, state transitions |
| `hardware-firmware-ux` | ULA/contention, ports, ROM/RST8/esxDOS/divMMC, 48K/128K differences, flicker/input/audio/stalls |
| `research-scout` | `external-research.md` trigger fires and source discovery can resolve a top uncertainty |

The main agent keeps preflight, scanner execution, evidence ledger, and final
verification. It may cover the lane with the best local context while delegates
cover the others.

## Independence Contract

- Give every delegate the same immutable baseline digest, not another
  delegate's conclusions.
- Assign one question and a narrow path/artifact set. Overlap only for an
  intentional adversarial check.
- Do not let delegates spawn delegates, edit files, rank globally, or write the
  final report.
- Run deterministic scanners once in the main agent. Pass a short result digest
  instead of duplicating the scan.
- Send only relevant reference sections, exact paths, and at most a short
  project profile. Do not paste the whole skill, tree, or build log.
- Return zero candidates when nothing survives the lane.

## Branch Brief

```text
Task: audit-z80 candidate search
Lane: <lane>
Question: <one falsifiable question>
Scope: <exact paths/artifacts>
Baseline: <target, toolchain, flags, ABI, ISR, map/list freshness; <=12 lines>
Routing: <requested model/effort; one-line rationale; fallback>
Constraints: read-only; no nested agents; candidates only
References: <only relevant files/sections>
```

## Compact Return Contract

Return at most three strongest candidates by default; allow five only for an
explicit exhaustive audit when all are distinct and proof-ready:

```text
- Mechanism:
  Anchor:
  Current evidence:
  Missing proof:
  Reachability/impact:
  Confidence: PROVEN | LIKELY | SUSPICIOUS | NEEDS BUILD
  Verification:
```

Add one rejected trap, or two for explicit exhaustive work, only when it
prevents a tempting false positive. No tutorial prose.

## Main-Agent Sequence

1. Run preflight and relevant bundled scanners once.
2. Build the baseline digest and select only evidence-backed lanes.
3. Route each lane with the adaptive model/effort policy and record the
   requested and actual settings.
4. Launch independent delegates together; inspect non-overlapping evidence
   while they run.
5. Merge by failure mechanism, not syntax or file.
6. Re-read every promoted site and apply `promotion-gate.md`.
7. Re-evaluate routing and escalate only where unresolved evidence can change
   the result.
8. Stop when new lanes produce only duplicates, lack a project-local anchor, or
   cannot alter severity, confidence, or residual risk.
9. Report actual delegation, model/effort fallbacks, skipped lanes, and
   unresolved evidence needs in a short synthesis block.

External research never promotes a finding by itself; it only sharpens a local
hypothesis or verification method.
