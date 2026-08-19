; Current source revision: sprite-repro-current
; Several causal owners remain plausible; this fixture does not establish one.
blit_masked_sprite:
    di
    call draw_masked_rows
    ei
    ret

draw_masked_rows:
    ; Renderer implementation intentionally omitted from the evidence fixture.
    ret
