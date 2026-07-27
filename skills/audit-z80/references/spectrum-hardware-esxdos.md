# Spectrum Hardware And esxDOS Checks

Use this file for `spectrum-hw`, `esxdos`, `isr`, `memory`, `map`, overlay, loader, screen, divMMC, dot-command, or real-hardware-sensitive audits.

## Contended memory and timing

- Treat `$4000..$7fff` on 48K Spectrum as contended RAM. Code executing there, or data accessed there, can gain ULA wait states while the display is being drawn.
- Treat bitmap `$4000..$57ff`, attributes `$5800..$5aff`, and any even ULA port access as timing-sensitive when used in raster/audio/UART/input loops.
- Flag ISR, `_fast`, `uart`, `poll`, `audio`, `beep`, `loader`, `draw`, `copy`, `blit`, and delay-loop symbols linked into `$4000..$7fff` as `PERF/UX` or `SUSPICIOUS` until timing is measured on the intended machine.
- Check high byte of I/O port addresses. On Spectrum, high bytes `$40..$7f` can create contention-like effects even when the port itself is not screen RAM.
- Snow is a real hardware class, not emulator noise. If `I` is put in `$40..$7f`, screen corruption can appear on affected machines.

## Firmware, system variables, and RST 8

- Treat `$5b00..$5bff` printer buffer, `$5c00..$5cff` system variables, `FRAMES` `$5c78`, UDG/font areas, and stream/channel structures as firmware contracts.
- If code calls `RST 8`, esxDOS, ROM print/error paths, dot-command APIs, or divMMC services, re-check any scratch use of printer buffer/system variables.
- Do not mark printer-buffer hijacking as a bug when the project never calls ROM/esxDOS paths that touch it and documents the contract. Mark it as `ROBUSTNESS` if later firmware calls could alias it.
- `FRAMES` or `LD A,R` can be acceptable for cheap visual randomness or timing jitter. It is not acceptable for security, protocol nonces, or deterministic replay unless the weakness is intended.

## divMMC, dot commands, and overlays

- Treat divMMC/esxDOS paging as a bank/firmware boundary. Any assumption that an overlay slot, ROM page, or scratch area remains loaded across RST8/file calls needs proof.
- For dot commands and loaders, ask whether interrupts are masked or routed through firmware while divMMC is paged. Do not assume stock ROM IM1.
- File handles, current drive, errno-like state, and persistent firmware state survive across calls. Audit early exits for leaked handles or half-updated state.
- Overlay-heavy projects with one fixed slot must prove every call into that slot is preceded by the correct load, and every non-local exit preserves the caller's stack level.

## Interrupt and machine-model traps

- `HALT` after `DI` is only a deliberate stop or NMI-wakeup construct. If normal IRQ wakeup is expected, it is a bug.
- `EI` enables maskable interrupts after the following instruction. `EI; RET`, `EI; JP`, and `EI; HALT` are contracts, not ordinary sequencing.
- `LD A,I` and `LD A,R` copy IFF2 into P/V, but if interrupted during the instruction, P/V can report disabled. Do not use this as a sole interrupt-state proof on NMOS/real Spectrum-sensitive code.
- Repeated block instructions can be interrupted between internal iterations. Audit shared buffers and ISR-visible partial state.

## Self-modifying and generated code

- Locate every patch site, generated routine, compiled sprite, opcode overlay, and table-written jump.
- Prove code is in writable RAM, not ROM or a paged-out overlay.
- Prove the patched bytes survive linker relocation, overlay reload, decompression, and divMMC/ROM paging.
- For DI-protected patch windows, prove no called path re-enables interrupts and no NMI-relevant state is left inconsistent.

## Evidence to cite

- `.map`/`.sym`: final addresses for hot symbols and scratch regions.
- `.lst`/generated `.asm`: exact instructions, wait-state-relevant layout, and generated SDCC register use.
- Emulator/hardware run: ZEsarUX/Fuse with contention enabled, breakpoints/watchpoints on `$5b00..$5cff`, overlay slot, stack, RST8, and screen RAM.
