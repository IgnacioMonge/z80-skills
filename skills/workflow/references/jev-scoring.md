# Jev proposal scoring: audit, shrink, optimize

The coordinator considers this stage when the loaded specialist has current
candidate cards. It is not conditional on a separate `$jev` mention or on a
failed router. Help/preflight-only modes and empty sets do not score. Read
[jev.md](jev.md) for session, privacy and execution. Numerical computation and
proof remain with the original tools and domain gates.

## Pre-session gates

Apply these gates in order before invoking the adapter, running `init`, building
a packet or creating a temporary file:

1. Apply the domain's hard vetoes, evidence gates, deduplication and baseline
   ordering. Form the contiguous hard-equivalent groups defined below.
2. A group is actionable only when it contains at least two eligible candidates
   and every member can be scored. Candidates in singleton groups, or in a group
   frozen by an ineligible member, cannot change priority and are not queried.
3. If no actionable group remains, record one internal `jev_score_skipped:no_priority_effect`
   note and stop. Do not read the preference or ask the user.
4. Apply the external-data preference and one-per-task authorization procedure in
   [jev.md](jev.md). A denial, refusal, no answer or privacy restriction stops the
   hook without a session or packet.
5. Only now initialize or reuse the task session. Build the packet from actionable
   groups only; keep every other candidate in the domain backlog at baseline.

This order is canonical for audit, shrink and optimize. Sibling skills delegate
to it and must not implement their own gate order.

## Prepare the candidates

Apply hard policy/target vetoes, deduplicate and retain the domain's evidence,
safety, dependency and ranking rules BEFORE scoring. Keep the original backlog
(including rejected or unscored candidates) and all required coverage. For audit
and shrink, put the array in the established domain order first. Jev is a priority
overlay, not a new severity scale or a replacement for net-byte accounting.

Use the matching `../examples/jev-audit.json`, `jev-shrink.json` or
`jev-optimize.json` as a shape only; synthetic fixtures are not project evidence.
The packet contains `schema_version:1`, `snapshot`, `external_data_authorized`,
`domain`, `objective`, `candidates`. Because the authorization gate already
passed, new packets set `external_data_authorized:true`; `false` remains accepted
for compatibility and runtime defense, not as a way to probe a skipped hook.
Each candidate contains exactly:

- `id`: stable ASCII letter-led ID with letters, digits, `_` or `-` (max 64).
- `baseline`: original candidate record. Keep all measurements and evidence labels.
- `context`: `title`, `anchor`, `mechanism`, `validation`, `risk`, `dependencies`
  as strings, and `evidence` as cards `{ref, excerpt, current}`. Include actual
  bounded excerpts, not only paths or the coordinator's favorable conclusion.
- `gates`: booleans `policy_allowed`, `target_compatible`, `current_anchor`,
  `in_scope`, supplied from local checks. These gates permit evaluation of the
  proposal, NOT implementation and NOT a declaration that it is correct.

Exact-shape validation reports the failing candidate path and, for a misplaced
known field, its expected nested path. It never includes field values in errors.

Record alternatives, contradictions and unresolved checks honestly in these
fields. Do not copy another candidate's evidence into its card. Lack of a current
anchor/excerpt preserves the candidate as unscored for the coordinator. Do not
turn a missing source into a discarded finding. Packet size is limited to 128 KiB;
select narrow excerpts without omitting a contradiction or necessary contract.

### Audit baseline

Keep `severity` (`CRITICAL|HIGH|MEDIUM|LOW`), `confidence`
(`PROVEN|LIKELY|SUSPICIOUS|NEEDS BUILD`) and `type` from the reporting contract.
The exact triple defines a hard comparison group. No score can move a LOW item
above a HIGH item or turn a suspicious concern into a BUG. BUG below LIKELY is
not accepted for scoring: the original promotion gate must be resolved first.

### Shrink baseline

Keep `safety` (`SAFE|AGGRESSIVE|EXPERIMENTAL`), `certainty`
(`EXACTO|ESTIMADO|REQUIERE BUILD`), the exact `pressure_target` and `net_bytes`
(integer or null). EXACTO requires an independently obtained net byte number;
include decoder/glue effects in the appropriate baseline, with workspace and
peak RAM separate. Never ask Jev to calculate it. The safety/certainty/pressure/
net tuple is a hard comparison group. Declared targets still require the original
multi-target gate; dependencies, subsumption and exclusions are not summed.
Jev's overlay computes NO totals.

### Optimize baseline

Supply the original `score_candidates.py` record, including tags, targets,
structured evidence, physical overlay constraints and the existing 0..5 features.
Do not replace these fields with Jev scores. The adapter imports the unchanged
bundled scorer by verified absolute path, applies its schema/evidence/policy
checks, and preserves its resulting `score` and adjusted record.

Pass exactly the active original options when calling the adapter:

```text
<PYTHON> <ADAPTER> score --task-dir <SAME_TASK_DIR> --input <PACKET> --profile <PROFILE> --policy <ABSOLUTE_POLICY_PATH> --target <TARGET> --forbidden <TAGS>
```

Omit options that do not apply. Never omit a real policy to obtain a higher score.
With TOML use Python 3.11+ as required by the original scorer; otherwise follow
its existing explicitly verified overrides. Profile defaults remain `balanced`.
The original numerical score, lane and evidence confidence form a hard group.
A policy-rejected candidate is never sent for scoring or rescued by Jev.

## Four independent Score questions per candidate

Each question uses five concrete descriptive levels (positions 0..4), not a
request to calculate an arbitrary number. `jev_z80.py` contains the full rubric.
Its instructions name the candidate inside `state.items`: the API does not use
question IDs as semantic instructions. Do not rely on the ID alone.

| Dimension | Audit | Shrink | Optimize |
| --- | ---: | ---: | ---: |
| Relevance to reachable impact / active pressure / bottleneck | 20% | 35% | 40% |
| Support in the supplied current evidence | 35% | 30% | 25% |
| Specificity and discriminating value of validation | 30% | 20% | 20% |
| Bounded scope and handling of dependencies/protected behavior | 15% | 15% | 15% |

`score_0_100 = 100 * sum(weight * native_score / 4)` is computed locally.
`confidence` and the entire probability distribution remain separate for each
dimension. Default thresholds are 0.85 for support and 0.80 for the other three.
All dimensions must meet their threshold before the score can change an order.
These weights and thresholds are operational starting values, not validated
quality, accuracy, probability of correctness or expected percentage speedup.
They are recorded in `jev-policy.json`; changing them requires a new session.

## What changes operationally

The adapter returns `baseline_order`, `recommended_order`, original baseline
records and a separate `jev` assessment for every candidate. Use the score to
prioritize the next examination/validation and explain the proposal's strengths
or missing evidence; retain all hard ordering rules in the published backlog.

Within a contiguous group of equivalent hard priority, complete confident scores
order which candidate to examine first. The base order is stable for equal scores.
If any member is unscored, policy-rejected or below a dimension threshold, that
whole group keeps the baseline; return the question to the current coordinator.
An uncertain score is NOT zero. Groups cannot leapfrog measured gains, severity,
safety, evidence classes, original optimizer scores, or intervening unmatched
candidates. A single candidate is never sent because it cannot change priority.

No field from Jev overwrites `PROVEN`, `LIKELY`, `EXACTO`, risk tags, net bytes,
T-states, targets, required tests or acceptance criteria. No score authorizes
patches/builds/experiments. Preserve optimize's three-experiment limit and audit/
shrink coverage and reporting. A confidence of one is not proof of correctness.

## Inspect real participation

The normal report keeps its format. A skipped hook is not mentioned. When a
session exists, its `audit.jsonl` contains actual
calls and the per-candidate scoring decisions. `status --task-dir ...` retrieves
it without another query. Record exactly which candidates were scored and which
retained baseline because of budget, missing evidence, low confidence, missing
client or a service error. Do not invent a Jev result or claim that every proposal
was scored if the shared two-attempt budget covered only part of a large set.

The score result and audit decision include `utility`: `comparable_groups`,
`orderable_candidates`, `scored_candidates`, `accepted_decisions`, and
`changed_order`. `changed_order` also remains a top-level result field for direct
inspection. These are observed counts, not a claim that Jev improved correctness.
