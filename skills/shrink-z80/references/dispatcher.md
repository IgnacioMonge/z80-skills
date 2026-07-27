# Dispatcher

Use this after `SKILL.md` for every real shrink pass except `help`. Obey
`hard-contract.md`.

## Baseline

Run only scripts relevant to the selected mode:

- `preflight_scan.py`: source/toolchain/artifact inventory.
- `artifact_freshness.py`: freshness gate before artifact-based exact claims.
- `map_summary.py`: selected map, sections, stack gap, resident/banked and
  startup hints.
- `libpull_scan.py` and `generated_helper_scan.py`: linked/generated helper
  roots.
- `deadcode_scan.py`: reachability candidates.
- `literal_dup_scan.py`: source literals, tables, and possible encodings.
- `z80_pattern_scan.py`: hand/generated ASM candidates.
- `net_compression_check.py`: storage and peak-RAM arithmetic from measured
  integers.

Never select among multiple maps by mtime alone. Scanner output is a candidate
queue, not confirmed savings.

## Mode Routing

- `preflight`: baseline only, then stop.
- `scan` / `diverge`: `high-impact.md`, evidence-selected lanes from
  `agent-orchestration.md`, `blind-spots.md`, then `reporting.md`.
- `deadcode`: deadcode scanner + `high-impact.md`; verify indirect calls,
  exports, map presence, and shared tails.
- `dedup`: literal/repeated-sequence scanners; separate source duplicates from
  generated echoes.
- `micro`: `asm-micro.md`, `z80-byte-evidence.md`, pattern scanner.
- `data` / `compress`: literal scan, `high-impact.md`, current asset
  measurements, and `external-research.md` only when the trigger fires.
- `arch` / `refactor`: `high-impact.md` plus `arch-resident` and any
  evidence-selected companion lane.
- `libpull`: `c-patterns.md`, map, generated code, and libpull scanners.
- `blackbelt`: SAFE pass first, then targeted sections of
  `size-blackbook.md`, `size-playbook-extended.md`, and
  `external-research.md`.
- `reserve`: use the scan order, SAFE candidates first, and stop when every
  declared target reaches the requested reserve (default 128 bytes only when
  the user gives no target).

## Attack Order

1. Fix the pressure target and baseline.
2. Inspect CRT/resident layout, architecture, and library pulls.
3. Check dead/refactor and data representation.
4. Check ASM/layout and dedup.
5. Enter black-belt or external research only after higher-yield SAFE lanes, or
   earlier when a concrete uncertainty blocks them.

For broad work, cover every applicable high-yield lane; collapse irrelevant
lanes into one concise `n/a` note rather than emitting fixed checklists.

## Evidence

- `EXACTO`: counted from current source/listing or measured on a fresh build.
- `ESTIMADO`: local formula is defensible but linked impact may change.
- `REQUIERE BUILD`: linker elimination, layout, branch range, packed output, or
  multi-target acceptance still needs measurement.

Verify flags, registers, stack, ABI, timing, linker cascades, decoder/setup
cost, workspace lifetime, and all declared target ceilings as applicable.

## Research Trigger

Read `external-research.md` when:

- the user requests deep/forum/demoscene/repository mining;
- a codec, toolchain rule, generated pattern, or target-specific technique can
  change a top result;
- the SAFE pass stalls below the requested goal;
- local sources disagree or an exact external implementation/test is needed.

Research output remains speculative until local byte and behavior proof exists.

## Output

Use `reporting.md`. Rank independent net wins first, then dependencies and
build-required candidates. Keep rejected traps only when they explain why an
apparently strong idea failed.
