# Arithmetic And Incremental Computation

Load for measured math, coordinate, collision or audio-control hotspots.
These MEDIUM core-Z80 candidates require explicit operand range, signedness,
overflow, rounding and live flags. Fallback is the existing tested routine.
Do not assume Z80N multiplication exists on a base Z80.

## Constant multiplication and division

For constant k, compare addition/subtraction chains with a generic multiply:
`15*x = (x<<4)-x` is a candidate, not automatically the cheapest register
sequence. Include copies of x, intermediate width and carry propagation.
For unsigned x, division by 2^k is a logical shift; signed division truncating
toward zero needs correction for negative nonmultiples (arithmetic shift alone
rounds down). Modulo and overflow semantics must match the original language.
Validate the full narrow domain, including negative boundaries where applicable.

For other divisors, reciprocal multiplication is profitable only if the
multiply, wider product and correction cost less than division. Choose the
multiplier/shift for the actual range and prove quotient and remainder; do
not transplant host-CPU magic constants or float approximations blindly.
See [existing table/reciprocal techniques](z80-techniques.md#square-table--reciprocal-math).

## Multiplication by operand distribution

A shift/add multiply that stops when the multiplier becomes zero can favor
small multipliers. A fixed-iteration or unrolled variant avoids that termination
test but spends work on unused bits. Compare setup, significant-bit count,
set-bit count and worst-case input; fixed iteration count alone does not mean
constant cycles when additions branch on bits. Swapping operands to choose
the smaller multiplier also has a cost. Preserve the full product or explicitly
specified modulo result. Exhaustively compare 8x8 results, then sample boundary
classes for wider forms. Reject an average-speed win that misses a raster deadline.
Source: [Grauw's multiplication variants](https://map.grauw.nl/articles/mult_div_shifts.php);
its measured examples include MSX M1 waits and are not Spectrum benchmarks.

## Incremental coordinates and error accumulators

For regular sampling, compute an initial value once and update by addition
instead of multiplying/dividing every point. Example: for nonnegative step s,
positive denominator d and sample i, maintain quotient q and remainder r of
`i*s/d`. Add `s//d` to q and `s%d` to r; when r>=d, subtract d and increment q.
Since both remainders are below d, at most one correction is needed. This is
the integer error-accumulator principle used in DDA-style stepping; handle
negative direction and tie-breaking explicitly in a drawing implementation.

It trades q/r state and an update for repeated division. Prove accumulator
width, endpoint inclusion, reset on discontinuities and the original rounding
rule. Compare the entire trajectory with direct evaluation, not only its final
position. Use direct recomputation for random access or after a state jump.

## Fixed-point and reduced precision

Replace floating-point state with an explicitly scaled integer only when its
range and error budget permit it. Count the library removed, conversion at
boundaries and required wider intermediates. An 8.8 representation does not
make its product fit 16 bits; define rescaling and rounding before narrowing.
For signed code, specify saturation versus wrap and avoid C signed-overflow
assumptions. Measure accumulated error over a complete animation/audio interval,
plus min/max and negative inputs. Retain existing precision if visible or
functional error exceeds the project's accepted bound.

## Small-domain and decomposed lookup tables

When a function's input domain is small, a complete table can replace arithmetic;
include entry width, alignment, lookup code and generation/initialization cost.
A byte-to-property table costs 256 bytes per byte of result. Two 16-entry nibble
tables can replace one 256-entry table only for a decomposable function:
for example popcount(x)=popcount(x&15)+popcount(x>>4). Extra extraction and
combination can erase the speed win. Never assume arbitrary functions decompose.
For symmetry-based tables, count reflection/sign fixups and boundary entries.
Generate from a trusted reference and compare every domain value; retain the
full table or arithmetic when proof or total cost favors it.

## Flags as data

SAFE only with an exact flag contract. `SBC A,A` turns incoming carry into
$00/$FF, destroying A and changing flags. It can help construct a mask after
an unsigned comparison, but signed comparisons need sign/overflow reasoning.
Carry propagation can combine multi-byte arithmetic or bit streams without
memory temporaries. Count all setup and consumed registers; do not replace
a conditional path merely because branchless sounds faster. Test carry 0/1,
all boundary values and the subsequent flag consumers. Keep the explicit branch
when other flags or the original A must survive.
Source: [Zilog arithmetic semantics](https://www.zilog.com/docs/z80/um0080.pdf).

## Verification boundary

`scripts/test_technique_examples.py` checks the arithmetic identities and
selected documented loops. Those checks prove their stated model, not a
project's ASM lowering, ABI, contention or real-time behavior. Before promotion,
use the project's assembled routine and compare full-domain output where cheap,
then measure its complete call boundary on the declared target.
