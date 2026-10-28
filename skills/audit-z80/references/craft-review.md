# Craft Review

Use for `craft` mode: would an expert Z80/SDCC programmer accept this code, or
find it inflated, hollow, duplicated, or non-idiomatic? Obey `hard-contract.md`;
the primary tree stays read-only. A correctness defect met on the way is
reported under the normal audit rules, not as craft.

## Boundary

- Authorship is not evidence. No detector reliably identifies AI-generated or
  "vibecoded" code; judge each construct by what it costs and by what removing,
  merging, or rewriting it would break.
- Byte savings as the sole goal belong to `$shrink-z80`; speed or competing
  metrics to `$optimize-z80`; naming or formatting without a cost or
  expert-craft question to `$workflow`.
- A reviewer who wrote or just read the code tends to keep it. Every unit must
  justify its existence. Scanner rows, delegate output, and the reviewer's own
  impression are candidates until the proof below promotes them.

## Workflow

1. Scope. A path list reviews code as it stands. `craft diff [<base>..<head>]`
   reviews only what a change set adds: resolve the range as in
   `change-review.md` and pass `--changed-from <base>` to the scanner. The
   scanner reads the files on disk, so when `<head>` is not the working tree,
   run it in a disposable worktree at `<head>` per `hard-contract.md`. The
   change's correctness risk belongs to `diff` mode; when it was not also
   requested, say in the coverage note that it was not reviewed.
2. Profile compiler, flags, ABI, targets, and overlay model with
   `preflight.md`; every cost below depends on them.
3. Run the scanner once, from the main agent:
   `<python> "$SKILL_DIR/scripts/craft_scan.py" <paths> --map <map> --churn 200`
   (repeat `--map` for the resident and every overlay map of the judged
   target; add `--changed-from <base>` in `craft diff`). References are counted
   across the git top level, or `--context <dir>`, so a narrow path never makes
   a used symbol look dead. A map it marks `STALE` supports nothing above
   `NEEDS BUILD`. Dead code and duplicated literals come from
   `$shrink-z80`, not from this scanner: run its `deadcode_scan.py` and
   `literal_dup_scan.py` (in `../shrink-z80/scripts/`) once per judged path,
   never on the repository root when it holds snapshots or vendored copies.
   ASM micro idioms (`djnz`, flag tests, `xor a`, tail calls) are its `micro`
   mode (`asm-micro.md`); cite them in the verdict only when that mode ran.
4. Triage by `[hotspots]` (lead weight, and churn and fix commits with
   `--churn`), structural leads first, then codegen, idiom, and comments.
5. For each lead, re-read the site, rule out the trap in the table below, and
   write the expert alternative as code.
6. Read every hotspot unit you judge in full. The scanner cannot see:
   - a hand-rolled routine that a library, ROM, resident helper, or sibling
     module already provides;
   - checks for states the caller already excludes, or validation repeated at
     every layer instead of once at the trust boundary;
   - options, flags, modes, or hooks used with one value only;
   - layers or macros that only rename, and state duplicated in two variables;
   - round-trip conversions (text to number to text) and runtime tables that
     could be const data, or the reverse when RAM is the limit;
   - generic code for one case: a loop that runs once, a dispatcher with one
     entry, a parser for one fixed string;
   - hot-path C against the SDCC grain (pointer chains through IX, 16/32-bit
     math on 8-bit data), or ASM that recomputes what registers or flags
     already hold;
   - comments that explain what instead of why.
7. Apply `promotion-gate.md` to every expert alternative: ABI, preserved
   registers and flags, IX/IY, ISR and shared state, stack, and layout. An
   alternative that fails one item is not a finding.
8. Measure the strongest candidates (Proof). Stop when new candidates no longer
   change the verdict.

## Lead Classes

| Lead | Expert alternative | Trap to rule out first |
| --- | --- | --- |
| `c-forwarder`, `asm-forwarder` | Call the target; `defc`/`EQU` alias costs 0 bytes | ABI bridge, function-pointer adapter, fixed vector, overlay entry name |
| `c-trivial-single-use` | Inline at the one site | It names a concept the caller needs to read |
| `c-constant-argument`, `asm-constant-register-arg` | Fold the constant into the callee | Host tests, other targets, or unseen entry paths pass another value |
| `c-unused-parameter` | Drop it from signature and callers | Signature fixed by another variant, pointer type, or ASM caller |
| `c-codegen-outlier` | C that SDCC compiles well, or ASM | Function-like macros expanded per site |
| `asm-push-pop-unclobbered` | Drop both | SP-relative access or an exit between them |
| `asm-jump-to-ret` | `ret cc` or `ret` | Jump-table entry with a fixed size |
| `c-clone-family`, `asm-clone-family` | One owner with parameters | Overlays cannot share code without a resident or common copy; target variants may need separate sources |
| `comment-narration`, `comment-history` | Keep only the why | A comment that records an ABI or hardware contract |

Moving overlay code into resident memory is a resident-cost tradeoff, never a
saving. A clone family split by target (`next/` against `spectrum/`) is waste
only when one parameterized source can serve both builds.

## Verified Toolchain Facts

Checked 2026-10-28 with z88dk `v24860-762578732-20260915`,
`zcc +zx -compiler=sdcc -SO3 --opt-code-size -S`:

- identical string literals are not pooled: each use emits its own `___str_N`;
- a static function with one caller is not inlined: the `call` remains;
- an `int` loop counter with a bound of 8, used only in 8-bit context, was
  narrowed to an 8-bit register.

These are anchors for this toolchain; recheck them on another version.

## Proof

Confidence uses the thresholds in `dispatcher.md`:

- `PROVEN`: the rewrite was built in a disposable worktree per
  `hard-contract.md` with the same target and flags, before and after map or
  overlay sizes were compared, and the project's focused tests passed.
- `LIKELY`: current source and a fresh map or listing show the waste, and the
  preservation argument is complete, but the rewrite was not built.
- `SUSPICIOUS`: depends on an unseen caller, target, or toolchain behavior.
- `NEEDS BUILD`: needs generated code that is stale or missing.

`PROVEN` here means the saving is measured; it never certifies correctness.
A defect met while measuring is an ordinary audit finding.

Byte deltas come from maps, listings, or builds; T-states from instruction
timings for hot paths. Map freshness compares source and header times only;
after a flag or configuration change, treat the map as `NEEDS BUILD`. Mark a delta reasoned from source as an estimate. When
the project's agent instructions gate builds and the user has not authorized
one, cap at `LIKELY` or `NEEDS BUILD` and name the single build or test target
that would prove the strongest finding.

### Blind Rewrite

Use it for the verdict on a core hotspot unit. A delegate on the
`craft-blind-rewrite` lane in `agent-orchestration.md` receives the unit's
contract and the tests that pin it, never the original body. The main agent
builds both versions in a disposable worktree and compares lines, bytes, and
test results:

- the rewrite passes the same tests, meets every contract item the tests do
  not pin, and links to half the bytes or less: `PROVEN` inflation for that
  unit; fewer lines alone prove nothing;
- the rewrite is not smaller: no finding; one failed attempt does not prove the
  unit tight.

## Finding Format

```text
[IMPACT] C-ID - short title
Lead: <scanner key> | manual
File: path:line (every member for a clone family)
Confidence: PROVEN | LIKELY | SUSPICIOUS | NEEDS BUILD
Waste: what exists and why an expert would not write it
Expert alternative: the replacement code, complete enough to apply
Delta: lines; bytes (map, listing, or build) or NEEDS BUILD; T-states on hot paths
Preservation: why behavior, ABI, timing, and every target stay the same; trap checked
Verification: the build or test that proves it
```

Impact is independent of confidence:

- `HIGH`: structural waste that multiplies (clone family, forwarding layer,
  speculative parameter, duplicated subsystem), at least 5% of a unit's
  measured bytes and at least 16 bytes, or waste that blocks a size cap.
- `MEDIUM`: one unit with measurable bytes or T-states on a resident or hot
  path.
- `LOW`: local idiom or comment waste.

## Verdict

State one verdict line after the findings and before coverage:

- `EXPERT-GRADE`: no promoted finding above `LOW`, and the units read in full
  showed none of the smells in Workflow step 6. Read at least the hotspot
  units, the three largest units in scope, and every public entry point, even
  when the scanner reports nothing.
- `SOLID`: only `LOW` or `MEDIUM` findings.
- `INFLATED`: a `HIGH` finding at `LIKELY` or `PROVEN`, or promoted deletable
  lines of at least 10% of the reviewed code lines.
- `REWRITE`: a blind or measured rewrite of a core unit is half its size or
  smaller with the same tests.

- `UNRATED`: the units read fall short of the `EXPERT-GRADE` floor; name what
  remains unread.

Give the deletable fraction (promoted deletable lines over the reviewed code
lines in `[summary]`: `code_lines`, or `changed_code_lines` in `craft diff`;
count overlapping deletions once) and the strongest residual doubt. The verdict summarizes
promoted evidence; scanner counts alone never decide it. In the coverage note
of `reporting.md`, also list the maps used and their freshness, sections with
no leads, and the units read in full.
