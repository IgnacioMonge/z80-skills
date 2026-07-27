# Z80 Byte Evidence

Use listings when available. Use this table only for local estimates and mark them `ESTIMADO` unless build artifacts confirm the bytes.

## Common sizes

- `call nn` = 3 bytes
- `jp nn` = 3 bytes
- `jr e` = 2 bytes
- `ret` = 1 byte
- `djnz e` = 2 bytes
- `ld r,n` = 2 bytes
- `ld a,0` = 2 bytes
- `xor a` = 1 byte
- `ld ix,nn` / `ld iy,nn` = 4 bytes
- `push ix` / `pop ix` / `push iy` / `pop iy` = 2 bytes
- `(ix+d)` / `(iy+d)` addressing usually pays prefix plus displacement tax; prefer listing bytes when possible.

## Rules

- Prefer `.lst`/`.lis` bytes over manual opcode counts.
- Do not sum local opcode wins with candidates that delete the containing routine.
- Recheck `jr` range after layout changes.

## Extended quick sizes (mark ESTIMADO without listing)

- `nop` = 1; `ei`/`di`/`halt` = 1; `reti`/`retn` = 2; `ex af,af'` / `exx` = 1
- `ld r,r'` = 1; `ld r,n` = 2; `ld rr,nn` = 3; `ld (nn),a` / `ld a,(nn)` = 3
- `ld (nn),hl` / `ld hl,(nn)` = 3; `ld (nn),rr` / `ld rr,(nn)` via ED = 4
- `push rr` / `pop rr` = 1; `push ix/iy` / `pop ix/iy` = 2
- `add/adc/sbc/sub/and/or/xor cp a,r` = 1; `... n` = 2
- `inc/dec r` = 1; `inc/dec rr` = 1; `add hl,rr` = 1; `add ix/iy,rr` = 2
- `jr e` = 2; `jr cc,e` = 2; `djnz e` = 2; `jp nn` = 3; `jp cc,nn` = 3
- `call nn` = 3; `call cc,nn` = 3; `ret` = 1; `ret cc` = 1
- `rst p` = 1; `jp (hl)` = 1; `jp (ix)/(iy)` = 2
- `ldir/lddr/cpir/...` = 2 (ED prefix); each still needs BC setup counted elsewhere
- IX/IY ops: typically +1 prefix byte over HL forms; `(ix+d)` adds displacement
- Bit ops `bit/res/set b,r` = 2; on `(hl)` = 2; on `(ix+d)` = 4
- Undocumented `sll` / IXH/IXL forms: listing-only; require opt-in + target proof

## Freshness rule

If the only size source is a `.map` older than the touched sources, label
`REQUIERE BUILD`. Do not treat historical map deltas as current savings.
