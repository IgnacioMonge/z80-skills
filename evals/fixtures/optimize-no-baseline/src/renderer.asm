draw_column:
    ld b, 32
.loop:
    ld a, (hl)
    ld (de), a
    inc hl
    inc de
    djnz .loop
    ret
