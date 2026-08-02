# Organization Patterns

Choose a proportional pattern after building the project model. These are
decision tools, not mandatory directories.

## Contents

1. [Four design axes](#four-design-axes)
2. [Dependency direction](#dependency-direction)
3. [Capability boundaries](#capability-boundaries)
4. [Project profiles](#project-profiles)
5. [Module composition and privacy](#module-composition-and-privacy)
6. [Mixed C and assembly](#mixed-c-and-assembly)
7. [Memory, banks, and overlays](#memory-banks-and-overlays)
8. [Multi-target structure](#multi-target-structure)
9. [Boundary contracts](#boundary-contracts)
10. [Anti-patterns](#anti-patterns)

## Four design axes

Evaluate every proposed split against:

1. **Ownership:** one component controls policy and mutable state.
2. **Dependency direction:** callers depend on a stable capability, not its
   private representation or device details.
3. **Runtime placement:** code/data location, lifetime, bank, page, stack, and
   timing remain valid.
4. **Change cohesion:** related changes stay together; unrelated changes stop
   colliding.

A good logical boundary may remain physically colocated. Conversely, one
logical component may need target-specific physical fragments.

## Dependency direction

Use this default direction only where the project contains the corresponding
roles:

```text
entry/startup -> application orchestration -> features/domain
                                      |-> capabilities/services
capabilities/services -> platform adapters/drivers
all runtime components -> explicit layout/resource contracts
build/generation -> generated resources -> runtime consumers
```

Rules:

- Keep application policy out of display, filesystem, transport, and hardware
  drivers.
- Let rendering consume snapshots, view models, commands, or narrow queries;
  do not let it become the owner of game/application state.
- Let storage serialize domain-owned data through an explicit schema; do not
  make filesystem code decide domain validity.
- Let input translate devices into stable actions before application policy
  consumes them, unless a tiny polling loop makes a separate layer needless.
- Keep protocol framing separate from transport when both change independently;
  keep them together when there is one small fixed protocol and no reuse.
- Centralize target selection and layout facts; avoid target conditionals in
  unrelated features.
- Allow deliberate reverse callbacks only through a documented narrow contract.

## Capability boundaries

### Application orchestration

Own startup order, main state transitions, scheduling, scene/mode selection,
error routing, and coordination. Do not own device registers or render details.

### Domain or feature logic

Own rules, commands, validation, persistent meaning, and feature-local state.
Expose intent-level operations rather than raw buffers or globals.

### RAM and memory layout

Own addresses, sections, budgets, pools, aliases, scratch regions, bank/overlay
slots, stack floors, and lifetime assertions. Users may own the data semantics;
the layout authority owns where and when it can live.

Prefer:

- one layout include/header/linker source;
- generated cross-language constants where duplication cannot be avoided;
- named regions and assertions rather than scattered numeric addresses;
- explicit acquire/release or phase ownership for reused workspace.

Export narrow named regions, limits, and accessors to users. Do not make every
component include a complete layout header or linker representation; generate
small cross-language views where that is the only shared fact.

### Rendering and UI

Own display hardware interaction, render queues/lists, dirty regions, draw
primitives, font/sprite/tile decoding, and presentation-only caches. Receive
stable application state or render commands. Keep gameplay, filesystem, and
protocol decisions outside.

Name the frame-sync owner and budget before splitting render work. Keep bitmap,
attribute, and screen-address authority together when their timing/placement is
coupled. Treat a shadow screen as a paging decision owned by the paging/layout
authority; record contention class and beam-critical regions where relevant.

### Storage and serialization

Own filesystem/ROM calls, paths, blocks, buffering, atomic replacement,
integrity, versioned encoding, and error translation. Domain code owns what the
data means. Separate durable format from device API when either can vary.

### Input

Own scan timing, device decoding, debounce/repeat, and target-specific mapping.
Expose actions or normalized state. Keep menu/game policy in the consumer.

### Audio

First classify the timing model. CPU-blocking beeper/PWM owns its interrupt
policy and exclusive time window; do not present it as an ordinary tick service.
Tick-driven AY/music owns its periodic schedule, device writes, and bounded ISR
or frame work. In either case features request sounds/music through a small
semantic contract rather than writing device ports.

### Transport and protocol

Let transport own bytes, ports, retries, and link state. Let protocol own
framing, commands, validation, compatibility, and message semantics. Combine
them for a truly fixed tiny stack; split when they have distinct tests or
change reasons.

### Platform and target adapters

Own ROM, firmware, OS, ports, interrupts, drivers, compiler/assembler ABI, and
model-specific behavior. Expose only the capability the application needs.
Avoid an abstraction layer for one implementation unless it also isolates a
volatile boundary or enables a real host-side test.

### Resources and generated data

Keep source assets, converters, schemas, generated outputs, manifests, and
runtime decoders distinguishable. Commit generated output only when the build
or release contract requires it. Never edit it as the authority.

## Project profiles

### Tiny single-file assembly

Keep one file when splitting adds no ownership or validation value. Use ordered
sections and a visible dependency direction:

```text
constants/layout
entry and orchestration
feature logic
render/input/storage/device routines
private helpers
immutable data and generated includes
RAM/BSS/stack assertions
```

Give each section one owner and private-label convention. Extract only when a
section gains a distinct contract, target variant, generated source, or change
history.

### Modular assembly

Use an assembler-root file to select targets and order modules, but keep module
internals private where the assembler permits:

```text
src/
  main.asm                 # composition only
  app/                     # orchestration and feature state
  services/                # only capabilities that exist
  platform/<target>/       # ROM, ports, drivers, target variants
  layout/                  # memory/bank/overlay authority
resources/                 # maintained sources and generators
tests/                     # source guards, models, emulation/hardware checks
```

Do not create every example directory. One `display.asm` is better than empty
`render/core`, `render/api`, and `render/backends` layers.

### Mixed C/assembly

Organize around explicit ABI seams:

```text
src/app/                   # portable orchestration/domain C
src/services/              # capability logic in C or ASM
src/platform/<target>/     # hardware and toolchain adapters
src/asm/                   # shared hand-written kernels with declared ABI
include/                   # public contracts only
layout/                    # shared addresses, sections, and generated constants
```

Keep private headers beside owners. Avoid a global include directory for every
internal definition. Generate shared constants when C and assembly must agree.

### Banked or overlay project

Model logical ownership and physical packaging separately. Choose one physical
pattern only when it matches the linker and change topology:

- **bank-as-package:** put a cohesive feature or overlay in one bank when it
  changes, loads, and executes together;
- **feature plus sections:** keep feature sources together and assign their
  fragments to sections/banks when several features share a physical package.

In both cases:

```text
logical component -> resident API/stub -> bank or overlay implementation
                   -> owned state      -> loader/transition contract
```

Keep the paging shadow, resident dispatch, bank selection, overlay loading,
trampolines, and slot ownership centralized. A cross-bank caller uses the
resident entry; a feature does not switch a bank ad hoc. Define pointer lifetime
as stable-bank, bank-tagged, or copied before return. Document call cost,
reentrancy, interrupt behavior, and rollback.

### Library or reusable engine

Separate public ABI and target adapters from private implementation. Keep the
public surface minimal, versioned when necessary, and demonstrably usable from
supported toolchains. Do not expose internal memory layout as convenience API.

### Game

Keep the main loop/frame scheduler, scene or mode ownership, simulation state,
asset pipeline, rendering, audio, input, and save data separate only where they
change or are timed independently. Keep a small game in one file with those
ordered sections; introduce a scene boundary only when it owns state or a real
transition contract.

### ROM or cartridge

Keep reset, fixed headers/entry tables/checksum, startup, copy-down, and
immutable ROM placement under explicit authorities. A ROM profile must make
cold/warm reset distinction and writable-RAM destination visible, but need not
invent an application layer.

### Driver or resident service

Keep install/uninstall, vector/hook ownership, device ports, host memory taken,
reentrancy, and restoration in one visible contract. Export the smallest host
API; do not let clients reach ISR state, paging state, or device registers.

### Host-side tool

Separate maintained source formats, converters, and deterministic manifests
from generated runtime data. Name the versioned contract between generator and
decoder; keep host-only dependencies out of the target runtime tree.

## Module composition and privacy

Use one composition root per target/build to select modules, target variants,
and link order. It may wire public capabilities but must not become a second
implementation owner.

- Export only documented entry labels, data, includes, and C declarations.
- Keep private labels, macros, includes, and headers beside their owner; import
  another module's public contract, never its internal include.
- Give generated includes a visible source authority; include generated output
  only at its declared boundary.
- State the assembler's local-label, `MODULE`, numeric-label, and macro/include
  scope rules before splitting assembly. Preserve source order when it is part
  of the contract.

## Mixed C and assembly

For every boundary, record:

- compiler/toolchain and calling convention;
- symbol decoration and section placement;
- argument order/width/sign and return convention;
- preserved/clobbered registers, flags, alternate set, IX/IY, and SP;
- interrupt and bank/page assumptions;
- ownership and lifetime of pointers/buffers;
- generated wrapper or pragma source of truth;
- smallest runnable ABI verification.

Place the contract beside the public declaration or wrapper. Keep compiler-
generated assembly as evidence, not maintained source, unless the project
explicitly treats it otherwise.

Read `toolchain-layout.md` when z88dk, SDCC, a specific assembler, CRT/startup,
sections, or banked C/ASM stubs affect the boundary. It supplies organization
contracts, not a replacement for toolchain manuals or `audit-z80` ABI evidence.

## Memory, banks, and overlays

- Keep semantic ownership separate from allocation/layout authority.
- Express region ceilings, alignments, stack floors, and overlap assumptions as
  build assertions when possible.
- Group data by lifetime and access pattern before grouping by type name.
- Keep ISR-visible state resident and prove atomicity or interrupt discipline.
- Prevent bank-local addresses from escaping their valid mapping lifetime.
- Treat decompression and scratch buffers as temporal allocations with owners.
- Keep self-modifying code, relocation tables, and absolute jumps attached to
  their placement contract even if their logical owner moves.

## Multi-target structure

Model target variation by independent axes: machine/ROM, memory and paging,
display, audio/input devices, storage/loader, and toolchain/build mode. Share a
contract only when its semantics match; place implementations under a target or
axis-specific adapter only when physical code/layout differs. Do not force every
axis into directories or scatter `IFDEF`s through domain code.

## Boundary contracts

Use a minimum contract for a small local split:

```text
Name and owner:
Public entry/data and allowed callers:
State/lifetime and dependency direction:
Placement or runtime assumption:
Verification:
```

Use the complete contract for public ABI, C/ASM, ISR/hook, banking/overlay,
ROM/fixed-placement, device, or multi-target seams:

```text
Name and owner:
Purpose and non-responsibilities:
Public entry points/data:
Inputs, outputs, errors:
State and lifetime:
Callers and dependencies:
Registers/flags/stack/interrupts:
Bank/page/section/address assumptions:
Target variants:
Runtime cost:
Verification:
```

If a boundary cannot be described without exposing most internals, it is
probably drawn in the wrong place.

## Anti-patterns

- `manager`, `utils`, `common`, or `misc` as owners of unrelated policy;
- one global context structure writable by every component;
- directory layers that mirror fashionable host architectures but add Z80
  calls, wrappers, or indirection;
- splitting every opcode helper or C function into its own file;
- circular includes repaired with more globals or forward declarations;
- target `IFDEF`s scattered through domain logic;
- memory addresses duplicated across languages, loaders, and tests;
- renderers that mutate domain state or storage code that owns validation;
- generated output beside maintained code with no visible source chain;
- bank switching hidden inside generic helpers;
- abstraction for hypothetical hardware, formats, or second implementations;
- aesthetic moves with no owner, dependency, test, or change-cohesion benefit.
