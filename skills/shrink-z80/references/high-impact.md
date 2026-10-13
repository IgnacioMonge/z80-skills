# Winner Pass

Start here for `scan`. Work these families in the order the census ranks
them for the pressure target. Each kept candidate must clear the materiality
threshold (user figure, else 30 B net). Put smaller ones in one tail line.

## 1. Overlay-only resident code -> move into that overlay

- Detect: census `[overlay_only]`. A group lists the routine plus its helpers
  that move with it (`with <caller>`).
- Accept only while resident is the pressure target: a move spends the
  destination overlay's margin. Once resident has room and overlays near their
  cap are the constraint, stop moving and work overlay headroom instead.
- Accept: every target's census agrees. Run it per linked map, because another
  target may call the routine from resident. The overlay keeps its cap, and
  moved helpers stay static in the overlay.
- Verify: callers in C and ASM (`rg` the symbol, `EXTERN`, `call`/`jp`,
  function tables). `[weak refs]` means a bare 16-bit match: check data tables.
  Host tests that stub the symbol, layering guards, overlay-state allowlists
  and ABI baselines usually need an intentional update.

## 2. Code dominated by an earlier gate -> delete the re-check

- Detect: for each early-return gate on a dispatch path (peer ready, transfer
  pending, busy, game state), `rg` the same predicate below it on every path
  from that gate.
- Accept: every caller path, in every `#if` target branch, passes the gate
  first. A stricter predicate the gate implies counts too
  (`!game_active || peer` after a `peer` gate).
- Verify: transition and parity tests. Test harnesses that call the inner
  function directly may depend on the re-check.

## 3. Compiler allocation budget -> one flag, every module

- Detect: SDCC builds without `--max-allocs-per-node`, or with a low value.
- Measure: in a disposable worktree, build at 20000, 50000 and 200000. Record
  the resident delta, each overlay's delta and the full-build time against
  the current flag.
- Accept: the resident saving clears the threshold and every overlay stays
  within its cap. Report overlays that grow. If the slowest value wins but
  builds are slow, offer a default value plus a release-only value.

## 4. Generated-code idioms -> shared helper plus one peephole rule

- Detect: census `[frame_idioms]`. SDCC IX epilogues (`ld sp,ix; pop ix;
  ret`) become `jp` to a shared helper. Inline IX prologues in fastcall
  functions become `call` to an HL-preserving helper
  (`ex (sp),ix; push ix; ld ix,2; add ix,sp; ret`).
- Use the project's custom COPT rule file (`-custom-copt-rules`), matching the
  exact text zsdcc emits (`ld	sp, ix` has a space). Export the helper to
  overlays when their rule file uses it.
- Booleanization sequences need flag liveness. Treat them as estimates until a
  rule proves the flags are dead.

## 5. Caller-side stack cleanup -> callee/fastcall ABI

- Detect: census `[abi_cleanup]`, per callee. Convert the largest ones:
  `__z88dk_callee` keeps the C signature; `__z88dk_fastcall` takes one
  argument in registers.
- ASM callees must pop their own arguments, on every exit path. Update ASM
  callers, test drivers and stubs. Guards that pin a dispatcher's decode
  sequence change with it.
- Below the threshold per callee, list only.

## 6. Twin routines -> one implementation plus an adapter

- Detect: census `[mass]` for large ASM. Look for two routines doing the same
  job in different coordinates or ABIs (cell row vs absolute Y, region clear
  vs per-cell clear, unrolled vs loop).
- Accept: output is byte-identical. Prove it with a vector that compares the
  framebuffer or the buffer before and after on the old code first.
- Measure the speed cost with `z88dk-ticks` and report it. A slower hot path
  is a tradeoff for the user, not a free win.

## Then, only when the census or user points there

- `arch`: protocol skeletons, data-driven state machines, buffer lifetimes.
- `libpull`: run `libpull_scan.py` only when `[mass]` shows runtime-library
  modules at or above the threshold.
- `data`/`compress`: strings, tables and assets, counted net of decoder,
  glue and workspace (`net_compression_check.py`).
- Micro lanes, black-belt and external research run only when the user names
  them: `asm-micro.md`, `size-blackbook.md`, `size-playbook-extended.md`,
  `external-research.md`.

Winners can subsume each other: moving a routine removes its idiom and ABI
counts. Re-run the census after each accepted family.
