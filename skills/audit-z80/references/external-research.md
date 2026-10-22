# External Research

Research when explicitly requested, or when ABI, toolchain, firmware, opcodes,
flags, emulator/hardware behavior, conflicting evidence, or an unexplained code
shape can change a finding. Include material blind spots after broad local checks.
Skip focused issues already provable from current code.

Read the [shared research method](research-method.md) when this gate holds.
Record the suspected contract or failure mode and its local verification.
External leads are hypotheses; current source or fresh artifacts must satisfy
[the hard contract](hard-contract.md) before promotion.

For *Coding the Impossible* / `oisee/antique-toy`, consult the
[pinned source review](antique-toy-review.md): successful assembly, synchronized
listings and nominal timing annotations each prove different, limited claims.

For Zeda's *Z80 Optimized Routines*, baze's *Z80 Bits* and their linked trick
pages, consult the [corpora review](z80-routine-corpora-review.md). Correct
code can still carry a wrong printed contract; check each claim against execution.
