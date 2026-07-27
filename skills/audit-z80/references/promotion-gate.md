# Promotion Gate

Use this before reporting any scanner, serial-branch, or subagent candidate as a finding.

## Promote Only With

- Concrete source, symbol, offset, stack, opcode, `.map`, `.lst`, generated `.asm`, or build-artifact evidence.
- Reachability under the project target, startup, toolchain, and memory model.
- ABI contract checked: params, return regs, callee cleanup, preserved regs, IX/IY, shadow regs.
- Stack and memory checked: exits balanced, BSS/stack/fixed RAM/overlay/bank assumptions verified.
- ASM flags and interrupt timing checked for hot paths and ISR-sensitive paths.
- Firmware/hardware constraints checked: RST8/esxDOS, ROM/ULA timing, contention, 48K/128K differences where relevant.
- Requested cross-domain boundaries checked: C/ASM, ISR/shared state,
  generated code, and map/copt evidence when present.
- User-visible stalls, missed input, flicker, audio jitter, and screen/attribute
  corruption treated as correctness or UX evidence, not dismissed as style.
- Hardware/emulator/model and toolchain version stated when they affect the
  mechanism.

## Downgrade Rules

- Never report `BUG` below `LIKELY`.
- Use `NEEDS BUILD` when generated artifacts are required but absent.
- Use `SUSPICIOUS` when proof depends on unverified path, ABI, or toolchain behavior.
- Use `THEORETICAL` or drop when no project-specific path exists.
- Keep severity and confidence independent.
