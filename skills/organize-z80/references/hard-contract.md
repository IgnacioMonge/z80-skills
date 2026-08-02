# Hard Contract

Use this contract for every map, design, plan, review, or applied migration.

## 1. Evidence and certainty

- Use severity consistently: `BLOCKER` prevents a safe decision or release;
  `HIGH` can violate a public, placement, or runtime contract; `MEDIUM` weakens
  maintainability or validation without known immediate breakage; `LOW` is an
  improvement with bounded risk.
- Use confidence consistently: `VERIFIED` is directly supported by current
  evidence; `LIKELY` has strong but incomplete evidence; `ASSUMED` is an
  unverified working premise; `UNVERIFIED` was not exercised or inspected;
  `NEEDS BUILD` requires an artifact or runtime check not yet available.
- Ground current-organization claims in maintained source, build files,
  linker/map/symbol/listing output, generated inputs, tests, or explicitly
  identified project documentation.
- Label unsupported architectural intent as `ASSUMED`, runtime behavior not
  exercised as `UNVERIFIED`, and artifact-dependent claims as `NEEDS BUILD`.
- Treat names and directories as hints, not proof of ownership. Trace readers,
  writers, entry points, include order, placement directives, and generated
  origins.
- Treat prior reports, conventions from other projects, and generic Z80 advice
  as candidate context only.

## 2. Default read-only boundary

- Keep `map`, `design`, `plan`, and `review` read-only except for an explicitly
  requested persistent-map write governed by `persistent-project-map.md`. That
  exception may edit only the approved map and its project routing pointer.
- Enter `apply` only after an explicit user request, a frozen relevant baseline,
  an approved design or boundary contract, and one named phase or slice with
  acceptance and rollback gates.
- Before editing, inspect repository instructions, dirty state and current
  branch when version control is available, target matrix, build commands, and
  relevant tests. Otherwise record VCS state as unavailable and name the
  recovery material. Preserve unrelated work.
- Use the repository's required branch or worktree workflow. If none exists,
  prefer a reversible task branch for a multi-file migration.
- Do not publish, merge, push, tag, or delete user branches without explicit
  authorization.

## 3. Contract preservation

Treat these as public until current evidence proves otherwise:

- exported C functions, assembly entry labels, vectors, hooks, and jump tables;
- calling conventions, register/flag preservation, stack layout, and error
  signaling;
- ROM/firmware calls, ports, timing windows, interrupt state, and page/bank
  state;
- linker sections, absolute addresses, binary headers, loader offsets, overlay
  slots, and generated-data offsets;
- command-line interfaces, configuration, save files, wire protocols, asset
  formats, and build entry points;
- target-specific symbols and feature-selection semantics.

Changing a contract requires explicit authorization, a compatibility decision,
and a migration or versioning path.

## 4. Structural purity

- Keep moves and ownership changes separate from functional changes.
- Do not combine reorganization with optimization, cleanup, broad renaming,
  formatting, dependency upgrades, or toolchain changes.
- When a necessary behavior fix is discovered, report or isolate it as a
  separate change unless it blocks the migration's safety.
- Preserve generated output byte-for-byte when the determinism probe shows that
  artifact is stable. Otherwise use the strongest applicable normalized,
  map/symbol/size, or behavioral comparison and explain any difference.

## 5. Runtime placement gate

Before moving placement-sensitive code or data, identify:

- absolute and relative addresses;
- section, bank, page, overlay, ROM/RAM, and contention class;
- lifetime and reuse assumptions;
- interrupt visibility and atomicity;
- stack, scratch, decompression, DMA, or hardware workspace overlap;
- branch-range, self-modifying-code, relocation, and table-offset assumptions.

If these cannot be established, keep the item in place and mark the proposed
move `BLOCKED BY PLACEMENT EVIDENCE`.

## 6. Z80 execution and placement invariants

- Before splitting or moving assembly, identify assembler scope rules, local or
  numeric labels, `MODULE` boundaries, macro and include expansion order,
  duplicate definitions, and exported/imported symbols. Compare the resulting
  symbol table when available; a successful assembly is not proof of equivalent
  scope.
- Give every paging shadow exactly one writer and a documented restore path.
  Keep the stack outside any slot that a reachable paging path can replace.
- Give IM mode, `I`, IM2 table, RST entries, NMI entry, and installed hooks an
  explicit owner. Keep required ISR, vectors, and trampolines resident and
  visible in every reachable bank configuration.
- Define interrupt and bank-state entry/exit rules for every ISR, hook, and
  bank-switch path. Restore the prior interrupt state and bank state on every
  return or explicitly transfer that obligation through a documented contract.
- Treat ROM as immutable. Name the owner and destination of initialized-RAM
  copy-down, distinguish cold from warm reset, and preserve fixed headers,
  entry tables, checksums, and reset vectors.
- Do not let a pointer, address, or table reference local to a bank escape that
  mapping without a stable-bank, bank-tagged, or copy contract.
- Give each port or hardware device an owner, authorized readers/writers,
  ISR visibility rule, target scope, and restoration rule after temporary use.

## 7. Multi-target gate

- Model every maintained target and build configuration affected by a boundary.
- Keep common ownership distinct from common physical implementation: two
  targets may share a contract while requiring different layout or code.
- Accept a migration only when each affected target builds and passes its own
  memory, stack, timing, ABI, and artifact checks.
- Never generalize from one successful target to another.

## 8. Completion gate

Do not call a phase complete until:

- the intended responsibility has one clear owner;
- dependency direction matches the approved design or a documented exception;
- no public or placement contract changed unintentionally;
- relevant builds and tests pass, or blocked checks are named;
- binary/map/timing differences are explained when applicable;
- rollback remains possible;
- an existing persistent map is updated to verified reality or explicitly
  marked stale when the accepted slice changes its mapped scope;
- the full diff and repository status have been inspected.
