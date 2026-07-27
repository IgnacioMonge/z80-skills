# Risk Matrix

## High Risk: Explicit Approval And Strong Validation

- SMC of opcodes or control flow
- SP blitting / stack copy/fill
- shadow registers shared with interrupts
- undocumented opcodes / IXH / IXL / IYH / IYL
- floating bus / raster timing
- custom CRT/startup
- bank/paging architecture changes
- custom peephole/copt rules used in release

Required mitigation:
- isolated kernel or one-file change
- rollback path
- emulator or hardware validation
- comments documenting invariants

## Medium Risk: Validate Carefully

- C-to-ASM conversion
- SMC of immediate operands
- partial unrolling
- compiled sprites
- compression/decompression format change
- ring buffer or polling cadence change
- overlay placement/caching change
- generated asset/code pipeline changes

Required mitigation:
- fresh baseline
- focused test/manual path
- map/listing diff

## Low Risk: Usually Safe But Still Measured

- remove duplicate work
- delete dead wrappers
- delete static functions proved unused by whole-file/repo search
- `call; ret` -> `jp`
- table/literal dedup
- branch ordering
- `DJNZ` where register allocation already fits
- remove stale retry/status redraws

Required mitigation:
- build or artifact diff if claiming bytes
- quick functional check for touched zone

## Auto-Reject Until Reframed

- no evidence
- stale artifacts for numeric claim
- wrong bottleneck category
- multiple unrelated changes in one experiment
- optimization depends on unverified hardware state
