# Dispatcher

Obey `hard-contract.md`. Use this file after `SKILL.md` for every real audit
except `help`.

## Workflow

1. **Profile once**
   - Read `preflight.md`.
   - Run `scripts/preflight_scan.py` when target, flags, startup, or artifacts
     are unclear.
   - Run `scripts/map_summary.py` when `.map`/`.sym`, fixed RAM, overlays,
     contention, or firmware addresses matter.
   - Run `scripts/abi_inventory.py` for mixed C/ASM.
   - Run `scripts/z80_pattern_scan.py` for broad ASM, ISR, timing, or unusual
     control flow.
   - Scanner output is a lead queue, never a finding.
2. **Build a pressure map**
   - Locate C/ASM boundaries, inline/generated ASM, ISR/shared state, stack/BSS,
     fixed RAM, loaders/overlays, firmware calls, screen/attribute writers,
     input/audio paths, and hot loops as applicable.
   - Prefer contradictions between source, prototypes, comments, listings, and
     map symbols over stylistic concerns.
3. **Set demand**
   - Use the focused/standard/deep gate in `SKILL.md`.
   - Read `agent-orchestration.md` only when independent lanes add value.
4. **Load domain references**
   - ASM/ABI/stack/flags/control flow: `asm-abi.md`
   - C semantics or memory: `c-memory.md`
   - ISR, map, stack/BSS, overlays/banks: `isr-map.md`
   - Spectrum timing, firmware, esxDOS/divMMC: `spectrum-hardware-esxdos.md`
   - SDCC/z88dk codegen, inline ASM, copt: `sdcc-z88dk-quirks.md`
   - Broad or unusual scope: apply the cross-domain checks in
     `promotion-gate.md`
5. **Research only on a trigger**
   - Read `external-research.md` when an unknown version/ABI/hardware fact,
     contradictory sources, an obscure technique, or an explicit deep-search
     request can affect a top result.
6. **Promote and report**
   - Apply `promotion-gate.md`.
   - Use `reporting.md`; findings first, residual risk last.

## Mode Routing

- `preflight`: complete step 1, report the profile and escalation signals, stop.
- `auto`: run the workflow at the demand level supported by preflight.
- `full` / `diverge`: cover every applicable domain, but collapse irrelevant
  domains into one concise `n/a` statement.
- Focused modes: run only the named domain plus any boundary required to prove
  it. For example, `abi` includes generated code when present; `spectrum-hw`
  includes interrupt/memory state when ports or paging depend on it.

## Evidence Thresholds

- `PROVEN`: current opcode/stack trace, symbol/offset, direct contradiction, or
  fresh build evidence makes the defect concrete.
- `LIKELY`: local path and mechanism are strong; one bounded check remains.
- `SUSPICIOUS`: a material ABI, reachability, version, or target assumption is
  unresolved.
- `NEEDS BUILD`: generated or linked evidence is required and unavailable.

External sources, scanners, and delegated branches cannot raise confidence
without a current project anchor.

## Script Index

- `preflight_scan.py`: target/toolchain/artifact and risk-surface inventory.
- `map_summary.py`: code/data/BSS, stack, symbols, library, contention, and
  firmware hints.
- `abi_inventory.py`: C/ASM conventions, exports/imports, and cleanup hints.
- `z80_pattern_scan.py`: expert-review candidates around flags, interrupts,
  stack tricks, ports, timing, paging, codegen, and layout.
- `smoke_test.py`: package checks after script changes.
