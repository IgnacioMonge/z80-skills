# Z80 Techniques

Use techniques only when project policy, target, profile, and bottleneck match. Cleverness is not evidence.

## Technique Template

Each recommended technique must state:

- Technique:
- Lane: SAFE | MEDIUM | DANGEROUS
- Targets:
- Profiles:
- Preconditions:
- Pattern:
- Expected win:
- Reject if:
- Validation:
- Fallback:

## Core SAFE Lane

Peepholes are cleanup, not strategy:

- `xor a` / `sub a` instead of `ld a,0` when flags may change.
- `add a,a` instead of `sla a` for simple left shift of A.
- `add hl,hl` for 16-bit left shift.
- `DJNZ` for 8-bit B counters.
- `jp fn` instead of `call fn; ret`.
- `or a`, `cp a`, `scf`, `ccf`, `sbc a,a` for flag/mask work when flags are acceptable.
- Merge adjacent 8-bit loads into 16-bit loads when register pairing allows.
- Prefer 8-bit state and counters over 16-bit when range proves it.
- Branch common path as fallthrough.
- Remove accidental `strlen`, `strcmp`, `memcpy`, division, long math pulls.

## C Source Guardrails

- Before replacing a C stdlib call, search the whole linked target and the map/listing. If the old helper remains linked and the replacement helper is new, a size win is speculative or likely negative.
- Fixed-buffer `strcmp` -> `memcmp` is valid only when the compared byte count is proven, NUL inclusion/exclusion is intentional, both buffers are initialized for that count, and `memcmp` is already linked or measured. Otherwise prefer measurement or a tiny local loop.
- `strncpy` -> bounded copy is valid only when dropping `strncpy` zero-fill semantics is intentional and the change removes a lib pull, shrinks current listing, or hits a hot bounded path.
- Table dispatch replacing a short `if` chain needs hot-path evidence or measured byte shrink. Cold menu/action paths stay as branches unless proven.
- Render/full-scan loops: hoist stable data pointers across the loop and pass them into internal helpers before calling a provider per cell/square. Validate the pointer cannot change through called render functions.

## Deep Techniques

### call/pop address acquisition

- Lane: MEDIUM
- Targets: pure-z80, Spectrum, MSX, CPC, CP/M; portable if stack discipline is clear.
- Profiles: demoscene-intro, asm-heavy, parser/dispatch kernels.
- Preconditions: caller stack is valid; interrupt/ISR does not inspect transient stack contents; assembler syntax supports local labels.
- Pattern: `call next` then `pop hl` to obtain address of inline table/code, or to avoid absolute relocation data.
- Expected win: saves pointer literals or relocation tables; improves position-independent code; sometimes reduces dispatch setup.
- Reject if: stack depth is tight, code runs inside fragile ISR/window, C ABI boundary expects stack untouched, or maintainability policy is release and equivalent table is cheap.
- Validation: listing proves stack balanced; run path with interrupts enabled/disabled as deployed; inspect map for byte delta.
- Fallback: absolute table label or `ld hl,label`.

### jp (hl) compact dispatch

- Lane: SAFE to MEDIUM
- Targets: pure-z80 and all Z80-family targets.
- Profiles: asm-heavy, interpreters, parsers, game state machines, sizecoding.
- Preconditions: HL contains trusted code address; target table entries are code pointers or computed labels; no bank switch invalidates target.
- Pattern: compute handler address in HL then `jp (hl)` instead of compare chains or `push hl; ret`.
- Expected win: smaller dispatch, fewer branches, better table-driven flow.
- Reject if: handlers cross banks/overlays without validation, target address can be data-corrupted, or indirect flow hurts required auditability.
- Validation: call graph/table bounds; map confirms handlers in resident/current bank; tests cover every dispatch value.
- Fallback: direct jump table macro or compare/jump chain.

### shared tails and fallthrough factoring

- Lane: SAFE
- Targets: all.
- Profiles: resident-size, c-heavy generated ASM, asm-heavy, sizecoding.
- Preconditions: suffix/prefix code has identical live registers, flags, stack, and memory side effects.
- Pattern: merge duplicated epilogues, branch into shared suffix, reorder cases so common continuation is fallthrough.
- Expected win: byte savings without new hardware assumptions.
- Reject if: flags differ, local labels hide non-equivalent side effects, or branch cost dominates hot path speed.
- Validation: before/after listing diff; focused functional test of each merged path.
- Fallback: keep duplicate code.

### SMC immediates and JR offsets

- Lane: MEDIUM; DANGEROUS for opcode/control-flow SMC.
- Targets: RAM-executed code only; not ROM; not immutable bank.
- Profiles: demoscene-intro, graphics kernels, parsers, isolated hot loops.
- Preconditions: patched byte is immediate, displacement, mask, table page, or operand; no ISR/concurrent reader observes half-patched state.
- Pattern: patch `ld a,n`, `ld hl,nn`, `jr disp`, mask constants, or table high byte instead of recomputing each iteration.
- Expected win: removes per-iteration setup, branches, or table selection overhead.
- Reject if: policy forbids SMC, code may execute from ROM/flash, cache/prefetch semantics are target-unclear, patch crosses bank boundary, or code is maintainable release and gain is small.
- Validation: map proves RAM/current bank; emulator/hardware run covers patch and unpatch paths; comment invariant at patch site.
- Fallback: table lookup, register setup, or duplicate specialized routines.

### square-table / reciprocal math

- Lane: MEDIUM
- Targets: all, if RAM/ROM table budget fits.
- Profiles: math/rules/AI, render, audio, fixed-point kernels.
- Preconditions: operand ranges and error bounds are known; table storage beats code/time cost.
- Pattern: use square tables for multiply, reciprocal multiply for division by known range, shift/add for fixed constants.
- Expected win: large speed gain for repeated math; sometimes code shrink vs generic multiply/divide helpers.
- Reject if: table exceeds resident/bank budget, precision is unproven, inputs exceed range, or C helper cost is not actually present.
- Validation: exhaustive or property tests for full operand range; map diff for helper removal/table cost.
- Fallback: shift/add constant multiply, early-exit multiply, or existing library helper.

### LDI chains vs LDIR vs manual copy

- Lane: SAFE to MEDIUM
- Targets: all; Spectrum additionally checks contention.
- Profiles: render, decompression, memory movement, I/O block output.
- Preconditions: block size distribution is known; overlap behavior is understood; interrupts/timing constraints known.
- Pattern: replace `LDIR` with fixed `LDI` chains for speed, or replace manual copy with `LDIR`/`LDI` for size/clarity.
- Expected win: speed for fixed small/medium copies; size for generic large copies.
- Reject if: block size is variable and setup dominates, overlap semantics differ, or unroll grows resident beyond budget.
- Validation: static T-states with loop multiplier; map/listing byte diff; render/copy correctness test.
- Fallback: existing copy primitive.

### stack blit / stack fill

- Lane: DANGEROUS
- Targets: all Z80 RAM targets, but target interrupt model must be explicit.
- Profiles: demoscene-intro, graphics-heavy isolated kernels, large copy/fill.
- Preconditions: SP saved/restored; stack region is safe; DI/EI window is bounded or interrupt-safe by construction; no C ABI boundary crosses the abuse window.
- Pattern: use `ld sp,src/dst`, `pop`/`push` bursts, optional shadow regs, for fast copy/fill.
- Expected win: high throughput for large screen/data blocks.
- Reject if: policy forbids SP abuse or interrupt windows, code can be interrupted, stack gap is unknown, NMI/hardware IRQ cannot be controlled, or maintainability is release and ordinary blit is acceptable.
- Validation: stack map/gap proof; interrupt-disabled T-state window; hardware/emulator render test; diff verifies SP restored before return/EI.
- Fallback: `LDIR`, `LDI` chain, generated blitter.

### shadow registers with ISR boundary rules

- Lane: MEDIUM to DANGEROUS
- Targets: all Z80; depends on interrupt convention.
- Profiles: render/audio/ISR kernels, asm-heavy.
- Preconditions: project owns alternate AF/BC/DE/HL convention; ISRs either save/restore or never use them; C ABI boundary documented.
- Pattern: use `exx` / `ex af,af'` to keep extra live state or accelerate inner loops.
- Expected win: fewer memory spills, tighter loops, faster ISR/player/render kernels.
- Reject if: interrupts use shadow regs, compiler/runtime assumes them, code crosses opaque library calls, or policy forbids interrupt-sensitive tricks.
- Validation: audit every ISR and library boundary; run interrupt-heavy path; document ownership.
- Fallback: RAM spill, index registers, or narrower live range.

### temporal amortization (work spread across frames)

- Lane: SAFE to MEDIUM.
- Targets: any target with a frame or event loop.
- Profiles: games, network apps, UI tools — anything with a per-frame budget.
- Preconditions: the computation tolerates partial completion across frames;
  intermediate state fits a small resumable context (index, phase byte).
- Pattern: convert "do all N items now" into "do K items per frame, resume at
  cursor"; schedule cold maintenance (presence, GC, timers, redraw scans) on a
  rotating N-frame wheel so no single frame pays for everything.
- Expected win: removes worst-case frame spikes and blocked input; often the
  largest UX win available without touching any inner loop.
- Reject if: the work has a hard same-frame deadline, or slicing adds shared
  state that an ISR can observe mid-update.
- Validation: frame counter instrumentation before/after on the worst path;
  input-latency check during the sliced work.
- Fallback: keep the monolithic call but move it off the interactive path.

### uncontended placement (Spectrum)

- Lane: SAFE. Spectrum-family targets only.
- Profiles: any timing-sensitive Spectrum code.
- Preconditions: linker/section control available; map proves current
  placement.
- Pattern: move hot loops, ISR code, the stack, and hot tables out of
  contended 0x4000-0x7FFF into 0x8000+; on 128K, prefer uncontended banks for
  hot code.
- Expected win: up to ~20-40% wall-clock on loops currently executing from
  contended RAM during display — free speed, zero code change.
- Reject if: layout is already uncontended (check the map, not the vibes) or
  moving code breaks fixed low-RAM contracts.
- Validation: border-timing or frame-count measurement before/after; map diff
  proves the move.
- Fallback: move only the stack and the single hottest routine.

### page-aligned tables (H-constant addressing)

- Lane: MEDIUM (costs alignment padding; buys speed and often bytes).
- Targets: all Z80.
- Preconditions: table fits one 256-byte page or row-starts can be aligned;
  linker supports alignment.
- Pattern: align table so the high byte is constant: `ld h,PAGE` once, then
  `ld l,index` / `inc l` replaces 16-bit adds and reloads in the loop.
- Expected win: deletes `add hl,de`/reload pairs from inner loops; typical
  2-3x on the addressing portion of a loop.
- Reject if: padding costs exceed the loop's total savings (count both).
- Validation: listing diff of the loop; padding bytes counted in the map.
- Fallback: byte-offset tables with a shared base register.

### undocumented registers as loop machinery

- Lane: DANGEROUS. Tag: `undocumented`. Explicit opt-in required.
- Targets: pinned CPU set only (real Z80 NMOS/CMOS and Next core are fine;
  verify emulators in the team workflow).
- Preconditions: IY not owned by runtime/ISR contract; toolchain emits or
  passes through the prefixed forms; support matrix documented.
- Pattern: IXH/IXL/IYH/IYL hold loop counters/limits in register-starved hot
  loops, freeing B/C/D/E and deleting memory temporaries mid-loop.
- Expected win: removes 13-16 T-state memory accesses from inner iterations;
  prefix costs 4 extra T-states per access — net only when replacing memory.
- Reject if: any supported platform/emulator lacks undocumented fidelity.
- Validation: ISR stress test; run on every emulator in the workflow plus
  hardware.
- Fallback: EXX shadow set if ISR ownership allows, or memory temp.

### size dark-art families (condensed index)

- Lane: MEDIUM to DANGEROUS per family; see per-family tags.
- Targets: Spectrum-family; family 1 requires fixed ROM targets.
- Profiles: size-starved residents, demoscene-intro, mature codebases where
  safe lanes are exhausted.
- Families: (1) ROM as constant pool / routine library / font at 0x3D00
  (`rom_dependency`); (2) instruction-skip and overlapping opcodes
  (`db 0x21` skip, stacked entry points) — EXPERIMENTAL; (3) demo flag idioms
  (daa hex-ASCII in 4 bytes, rst-as-call, push/ret dispatch, carry chains,
  shadow-set storage); (4) self-destructing init code placed in buffers that
  only go live post-init (`init_order`) — often the largest semantic-free
  resident win; (5) IXH/IXL/IYH/IYL and `sll` as extra storage/ops
  (`undocumented`, explicit opt-in); (6) custom SDCC peephole `.rul` rules
  harvested from repeated generated-ASM n-grams — fixes the generator, guards
  future builds; (7) resident string packing (5/6-bit or digram) with a
  20-40 byte decoder.
- Expected win: families 4 and 6 harvest across the whole binary and dominate;
  check them first.
- Reject if: ROM/model is not pinned, overlapped control flow or stack effects
  are unproved, init-buffer lifetimes overlap, a peephole rule lacks generated
  ASM evidence, or packed strings do not amortize their decoder.
- Validation: listing/map delta plus the family-specific runtime, lifetime,
  target, ABI, or exhaustive-value obligation.

## Target-Specific Gate

- Spectrum-only: contention, floating bus, border timing, ULA-safe placement, attributes, esxDOS/divMMC.
- Pure Z80: reject all Spectrum-only claims unless project evidence proves target.
- Unknown target: recommend only core techniques and measurement setup.
- Undocumented opcodes: require CPU floor and policy allowance.

## Evidence Gate

A technique must cite at least one: map symbol size, hot loop/listing, generated ASM pattern, measured timing, repeated source pattern, artifact pressure, or hardware timing constraint.

No evidence, no recommendation.

## Wrong-Bottleneck Rejection

- I/O wait -> do not recommend CPU ASM first.
- Network latency -> inspect retries/waits/protocol order first.
- Disk/overlay load -> inspect caching/layout before loop tricks.
- Render tearing -> inspect frame timing/contention before generic C changes.
- Resident pressure -> inspect data/lib/cold split before dangerous opcodes.
- Policy veto -> reject, not demote.
