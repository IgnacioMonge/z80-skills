# Project Model

Build a compact model before recommending directories or module splits.

## Contents

1. [Inventory](#inventory)
2. [Project-type routing](#project-type-routing)
3. [Execution contexts](#execution-contexts)
4. [Responsibility map](#responsibility-map)
5. [Devices, ports, and vectors](#devices-ports-and-vectors)
6. [State and memory ownership](#state-and-memory-ownership)
7. [Dependency map](#dependency-map)
8. [Change topology](#change-topology)
9. [Pressure seams](#pressure-seams)

## Inventory

Record only facts that can change the organization decision:

```text
Project type: application | game | ROM | library | tool | driver | mixed
Targets/configurations:
Languages and assemblers/compilers:
Build and generated-code entry points:
Boot/load/update path:
Primary artifacts and placement evidence:
Test and hardware-validation surfaces:
Public compatibility contracts:
Explicit constraints/no-change zones:
```

Identify source of truth for constants, memory layout, target selection, asset
generation, and versioning. Flag duplicated authorities immediately.

## Project-type routing

Use the declared project type to select only the matching profile in
`organization-patterns.md`; do not apply all profiles to a mixed project.

| Type | Map before proposing structure |
|---|---|
| game | frame owner/budget, scene or mode state, assets, rendering and save paths |
| ROM/cartridge | reset/entry table, immutable regions, initialized-RAM copy-down, checksum/header authority |
| driver/resident | installed hooks, port ownership, host memory taken, ISR/reentrancy and install/uninstall symmetry |
| host-side tool | source formats, deterministic generation, versioned manifest, generated/runtime decoder contract |
| library | public ABI, supported toolchains, target adapters, caller-owned state |

For `mixed`, route each actual runtime or build-side component to its applicable
profile. A project type is a constraint on the model, not a directory name.

## Execution contexts

Trace control from each entry point rather than assuming one main loop:

- reset, CRT, loader, installer, startup, initialization;
- foreground loop, state machine, scene, command dispatcher, or library API;
- ISR, NMI, callback, hook, interrupt-disabled region, and reentrant path;
- asynchronous device, DMA, UART, network, storage, or firmware completion;
- error recovery, cancellation, update, shutdown, and reboot.

For each context, record callable responsibilities, shared state, required page
or bank, stack assumptions, interrupt state, and latency budget. A component
used by two contexts needs an explicit reentrancy or synchronization contract.

## Responsibility map

Classify only responsibilities that exist. Typical candidates are:

- application orchestration and state transitions;
- domain/game rules and feature workflows;
- rendering, display lists, sprites, tiles, text, UI, and presentation state;
- input sampling, decoding, repeat/debounce, and action mapping;
- audio sequencing, mixer state, and device output;
- storage, filesystem, serialization, save data, assets, and updates;
- transport, framing, protocol, queues, retries, and recovery;
- hardware drivers, firmware/ROM adapters, ports, and target differences;
- memory layout, allocation, pools, scratch space, banks, and overlays;
- resource generation, compression, conversion, and manifests;
- diagnostics, assertions, tests, emulation, and build/packaging.

Build an ownership table:

```text
responsibility | current owner | entry points | owned state | dependencies |
contexts/targets | placement constraints | evidence | confidence
```

Do not create a module merely because a row exists. Use the map to find owners
and boundaries; small related rows may remain together.

## Devices, ports, and vectors

Inventory hardware resources separately from RAM ownership:

```text
device/ports | owner | authorized readers/writers | contexts/targets |
ISR-visible | temporary-use restoration | evidence | confidence
```

For each active interrupt or hook, name its authority and installation path:

```text
entry/vector | owner | install/uninstall owner | dispatch/hook contract |
IM/I/table or ROM basis | resident placement | shared state | latency budget
```

Use the hard contract for the Z80 safety invariants. This map establishes who
owns the decision and exposes conflicts such as a feature writing a paging or
audio port behind its driver.

## State and memory ownership

Inventory mutable state and significant immutable regions:

```text
item/region | owner | readers | writers | lifetime | reset point | placement |
bank/page | ISR-visible | alias/overlay | invariant
```

Classify lifetimes where relevant:

- build-time/generated;
- ROM or immutable resident;
- process/application lifetime;
- mode, level, scene, document, connection, or command lifetime;
- frame/tick lifetime;
- interrupt-shared or device-owned;
- temporary/scratch/decompression workspace;
- banked or overlay-exclusive lifetime;
- stack frame or caller-provided buffer.

Flag:

- writable globals with multiple policy owners;
- buffers whose allocator, producer, consumer, and reset owner differ;
- physical aliases without proven non-overlapping lifetimes;
- caches with no invalidation owner;
- bank/page state changed across hidden calls;
- layout constants duplicated between loader, payload, client, and tests;
- state accessed directly from rendering, storage, and protocol code.

Prefer one writer and explicit readers. When multiple writers are unavoidable,
name the serialization, interrupt, or state-machine rule.

## Dependency map

Trace more than includes:

- direct calls and tail jumps;
- include/import order and macro expansion;
- exported labels, externs, weak symbols, callbacks, vectors, and tables;
- shared globals and address constants;
- generated files and their source manifests;
- linker sections and placement scripts;
- bank-switch, overlay-load, ROM-call, and driver transitions;
- build scripts, packagers, loaders, and update clients.

Record direction in a compact matrix:

```text
from | to | mechanism | contract | runtime cost | placement coupling |
target scope | cycle? | evidence
```

Separate:

- **logical dependency**: one responsibility needs another's behavior;
- **data dependency**: one responsibility reads or mutates another's state;
- **physical dependency**: two items must share an address, section, bank, or
  compilation unit;
- **build dependency**: generation or packaging order;
- **incidental dependency**: convenience access with no necessary contract.

Remove incidental dependencies first. Preserve documented physical coupling
until measurements support changing it.

## Change topology

Use history only when available and relevant. Ask:

- Which files change together for one feature?
- Which file changes for unrelated rendering, storage, RAM, and protocol work?
- Which modules cause broad rebuilds or merge conflicts?
- Which target-specific conditionals spread through otherwise common logic?
- Which generated artifacts are edited manually?
- Which changes repeatedly cross the same unstable boundary?

Do not split solely because a file is large. A cohesive table or renderer may
be large and stable; a short file may still mix unrelated owners.

## Pressure seams

Rank a seam higher when several signals coincide:

- unclear or multiple state owners;
- dependency cycle or hidden reverse dependency;
- one file changes for unrelated reasons;
- hardware access leaks into application rules;
- rendering or storage owns domain policy;
- C/ASM boundary lacks an ABI contract;
- placement facts are duplicated or implicit;
- target conditionals contaminate common code;
- generated and maintained code are mixed;
- a boundary cannot be tested or measured independently;
- a bug fix must be duplicated across callers.

Rank a seam lower when splitting would add calls, glue, banks, indirection,
duplicated state, or build complexity without clarifying ownership.
