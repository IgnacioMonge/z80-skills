# ZX and Next Platform Profile

Decide or explicitly defer only the surfaces that can change the active slice.

| Surface | Decision to record |
| --- | --- |
| Targets | 48K, 128K, +2A/+3, Next, or a deliberate compatibility subset |
| CPU | Z80/Z80N instruction policy, clock assumptions, and fallback requirement |
| Video | ULA/Timex, Layer 2, tilemap, sprites, copper, palette, and contention implications |
| Memory | Fixed map, paging/MMU, banks, overlays, stack, buffers, and asset residency |
| Timing | Frame rate, raster/audio deadlines, interrupt model, contention, and clock dependence |
| I/O | Keyboard, joystick, mouse, storage, firmware, ports, NextRegs, DMA, and peripherals |
| Delivery | Required TAP/TZX/SNA/Z80/NEX or other artifact, loader, and save-data contracts |
| Toolchain | Assembler/compiler, dialect, linker/CRT, generated assets, recipe, emulator, and hardware |

For each decision, record:

```text
Surface:
Decision or deferred question:
Targets/configurations:
Evidence class and anchor:
Product consequence:
Technical consequence:
Acceptance criteria affected:
```

## Decision Rules

- Do not choose the lowest common denominator unless compatibility is a product
  requirement.
- Do not choose a Next-only feature merely because the target is Next; require a
  product or technical benefit for the active slice.
- Treat clocks, contention, emulator support, firmware behavior, peripheral
  availability, and toolchain syntax as target/configuration claims requiring
  current evidence.
- Defer a choice when it cannot affect the current milestone; record what event
  will force the decision.
- When classic and Next variants share behavior but not implementation, keep one
  product criterion and separate technical criteria or evidence per target.
- Verify exact capabilities against current authoritative documentation, local
  toolchain output, emulator support, or hardware when they constrain design.

## Escalation Signals

Increase demand or route a specialist handoff when the slice includes:

- multiple maintained target families;
- bank/MMU transitions reachable from interrupts or callbacks;
- raster, audio, DMA, copper, or peripheral timing;
- cross-bank pointers, overlays, decompression workspaces, or mutable paging
  shadows;
- generated assets whose format or placement is not yet authoritative;
- disagreement among source, documentation, emulator, and hardware behavior.

Do not finalize architecture while a platform uncertainty can veto it. Use a
bounded `SPIKE` task to close that uncertainty first.
