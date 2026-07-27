# Blind Spots

Use this file as a pre-submit guard against shallow shrink passes.

## Do not finalize if you have done any of these

- stopped after strings or duplicate literals and called it a full scan
- claimed a libpull saving without proving the helper is present in the `.map`
- proposed a byte win that silently changes flags, registers, or stack cleanup
- ignored `BSS` or stack tradeoffs while focusing only on `CODE`
- recommended experimental tricks before exhausting larger safe wins
- counted a local `jr` saving without proving range after the edit
- ignored repeated ASM tails, repeated instruction n-grams, or wrapper layers while polishing one-line substitutions
- ignored screen layout, clipping zones, table encoding, and decompressor net cost when data dominates code
- proposed RST/self-modifying/stack-blitter tricks without proving ABI, DI/EI, SP restoration, and target hardware
- suggested RLE/compression without subtracting decoder/setup/workspace bytes
- suggested `sbc a,a` or `xor a` without checking flags consumed later
- suggested IX/IY removal without checking frame pointer/reserved-register contract

## High-value reminders

- architecture and library drag usually beat dedup for total bytes
- one wrong ABI-preserve assumption can turn a shrink idea into a regression
- repeated tiny tails and wrapper layers add up, but only after the bigger categories have been checked
- black-belt ideas must include rejected candidates; silence usually means the pass was not actually done
- experimental tricks can be excellent, but only after safe arch/libpull/data wins have been checked and rejected

## Extended coverage (do not finalize a broad scan without)

- resident vs banked / overlay pressure targets separated
- CRT/startup/.dot contribution checked from current map
- IM2 vector-page tax considered when IM2 is in use
- display next-line / attribute strategy considered when screen code dominates
- Z80N wins gated by multi-target matrix
- compression reported as Net_storage (packed+decoder+call glue) plus separate RAM_peak_delta
- buffer lifetime overlays considered before growing BSS
- hard-contract: current-code evidence; no leftover experiment worktrees

## External pass

- Use `external-research.md` only for a bounded local question.
- Do not present forum/demoscene techniques before SAFE arch/libpull/data wins,
  unless they directly unblock one of those lanes.
- Do not recommend a codec without current asset, decoder, glue, workspace, and
  load-time measurements.
- Do not transfer IM2/ROM, screen, or undocumented tricks across targets without
  the full target gate.
