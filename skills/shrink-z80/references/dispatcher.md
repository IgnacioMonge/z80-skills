# Dispatcher

Use this after `SKILL.md` for every real shrink pass except `help`. Obey
`hard-contract.md`.

## Baseline

Run only scripts relevant to the selected mode:

- `winner_census.py`: the first script of `scan`, `diverge`, `reserve` and
  `agent`; one run per linked target with its overlay/bank binaries.
- `preflight_scan.py`: requested source/toolchain/artifact inventory, or when
  unresolved inventory affects scope or target selection. Skip for a local
  source-only pass whose necessary context is already known.
- `artifact_freshness.py`: freshness gate before artifact-based exact claims;
  reuse an equivalent still-valid gate under workflow verification rules.
  No artifact-based claim means no freshness scan solely to satisfy a checklist.
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
- `scan`: freshness gate, `winner_census.py`, then the winner families of
  `high-impact.md` in census order, above the materiality threshold. Other
  scanners run only when the census points at their category. Then use
  `blind-spots.md` and `reporting.md`.
- `diverge`: cover every applicable high-yield lane, using
  `agent-orchestration.md` only where independent lanes add value, then
  `blind-spots.md` and `reporting.md`.
- `deadcode`: deadcode scanner + `high-impact.md`; verify indirect calls,
  exports, map presence, and shared tails.
- `dedup`: literal/repeated-sequence scanners; separate source duplicates from
  generated echoes.
- `micro`: `asm-micro.md`, `z80-byte-evidence.md`, pattern scanner.
- `data` / `compress`: literal scan, `high-impact.md`, current asset
  measurements, and `external-research.md` only when the trigger fires.
- `arch` / `refactor`: `high-impact.md` plus `arch-data` and any
  evidence-selected companion lane.
- `libpull`: `c-patterns.md`, map, generated code, and libpull scanners.
- `blackbelt`: SAFE pass first, then targeted sections of
  `size-blackbook.md`, `size-playbook-extended.md`, and
  `external-research.md`.
- `reserve`: use the scan order, SAFE candidates first, and stop when every
  declared target reaches the requested reserve (default 128 bytes only when
  the user gives no target).
- `agent`: `winner_census.py` first; with winners above the threshold, report
  them and ask before handing off. Once the user selects the agent (or the
  census is empty), run `preflight` and write `<project>/shrink-agent.toml` when
  missing (template: `../../tools/shrink-agent/examples/template.toml`; fields
  in `../../tools/shrink-agent/README.md`). Choose `size_symbol` by the pressure
  target, set `python` when the build needs the host interpreter, add a `files`
  target for overlays or banks linked apart from the main map (`maps` too when
  their link writes maps, so their routines are proposed), put the project's
  size/layout checks in `tests`, and list only targets the project's
  instructions allow to build. Run
  `<venv-python> "$SKILL_DIR/../../tools/shrink-agent/shrink_agent.py" --config <that file> --dry-run`
  with `<venv-python>` = `~/.z80-skills/venv/bin/python` (Windows:
  `~/.z80-skills/venv/Scripts/python.exe`; if missing or `~/.z80-skills/.env` is
  absent, run `tools/shrink-agent/install.py` first). Gate: at least one
  candidate, `.c` routines listed as `c`, and every `excerpt` line `ok`;
  otherwise fix the config and stop. Then launch the same command without
  `--dry-run` in the background (defaults: 5 routines, 2 USD; pass
  `--iterations` or `--max-usd` only when requested) and report from
  `~/.z80-skills/shrink-runs/<project>-<timestamp>/shrink.log`. No lanes.

## Attack Order

1. Fix the pressure target, threshold and baseline.
2. Run the census per target; work the winner families of `high-impact.md`.
3. Then architecture, library pulls or data, only where the census or user
   points.
4. Micro, dedup, black-belt or external research only when the user names
   them, or when a concrete uncertainty blocks a winner.

For explicitly broad or exhaustive work, cover every applicable high-yield
lane; collapse irrelevant lanes into one concise `n/a` note rather than
emitting fixed checklists.

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
