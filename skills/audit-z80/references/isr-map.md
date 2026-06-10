# ISR And Map Checks

Use this reference for `isr`, `map`, `memory`, and any `full` audit where concurrency or RAM layout can bite.

## Interrupt contract

- Identify the active interrupt mode from startup, CRT, or explicit `im 1` or `im 2` code
- Verify which registers the ISR saves and restores
- List shared variables between ISR and foreground code
- Check atomicity for multi-byte shared state
- Verify `di` and `ei` balance on every path, including early returns and error exits

## ZX Spectrum assumptions

- ROM IM1 is only a safe assumption when the project still uses the stock path
- Custom startup, overlay loaders, and banked projects frequently break default ROM assumptions
- If the project disables interrupts for long polling or UART work, verify no helper re-enables them unexpectedly

## Map file priorities

In z88dk-style `.map` files, look for:

- `__CODE_head`, `__CODE_tail`, `__CODE_size`
- `__DATA_head`, `__DATA_tail`, `__DATA_size`
- `__BSS_head`, `__BSS_tail`, `__BSS_END_tail`
- `CRT_STACK_SIZE`, `TAR__register_sp`, `__register_sp`
- Any pulled-in `__mul*`, `__div*`, or `__mod*` helpers

## Gap formula

If both symbols exist, compute:

```text
stack_gap = stack_top - bss_end
```

Common z88dk signals:

- `stack_top`: `TAR__register_sp` or `__register_sp`
- `bss_end`: `__BSS_END_tail` or `__BSS_tail`

Treat the result as one input, not the whole truth. Fixed-address variables and ISR stack usage can tighten the real margin further.

## copt or opt files

Treat `.opt` and `.rul` files as executable transformations. Review them when present:

- false positives
- missing guard conditions
- rule ordering hazards
- rules that are dead or untested in the current build
