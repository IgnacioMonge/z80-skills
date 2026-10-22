# Arithmetic And Incremental Computation

Load for measured math, coordinate, collision or audio-control hotspots.
These MEDIUM core-Z80 candidates require explicit operand range, signedness,
overflow, rounding and live flags. Fallback is the existing tested routine.
Do not assume Z80N multiplication exists on a base Z80.

For exact quarter-square/signed-product contracts, second-difference tables,
bounded arithmetic or display-oriented BCD, load
[demoscene math](demoscene-math.md). Its host proofs do not establish target
routine timing or ABI correctness.

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

## Iterative division near powers of two

MEDIUM; unsigned quotient by one constant divisor near a power of two.
For d=2^N-1, `d*y=x` is equivalent to `y=(x+y)>>N`, so the quotient is a
fixed point of that recurrence. Truncation biases the estimate low; a preload
of floor(2^W/d) for a W-bit dividend compensates. For d=2^N+1 use
`y=(x-y)>>N` from y=0; its first pass is a plain shift and needs no preload.

The preload and pass count are exact facts of the declared width, not tunable
approximations. Exhaustive checks give: 8-bit /3, /7, /15, /31 in 4, 3, 2, 2
passes; 8-bit /5, /9, /17 in 4, 4, 2; 16-bit /3, /7, /15 in 8, 6, 4. Only 85
works for 8-bit /3 and only 17 for /15 at those counts; /7 accepts 36..73.
The sum x+y needs W+1 bits: keep its carry through RRA or RR.

```asm
; example: div15-iterative
    ld a,17
    add a,b
    rra
    rrca
    rrca
    rrca
    and $1f
    add a,b
    rra
    rrca
    rrca
    rrca
    and $1f
```

A = B/15 in 16 bytes / 61 nominal T; B survives, F is destroyed. RRA keeps
the ninth sum bit; RRCA plus a mask completes the shift faster than SRL.
No remainder is produced: x-q*d costs extra. Composite divisors can shift
afterwards because floor(floor(x/a)/b)=floor(x/(a*b)): /6 is /3 then SRL.

Speed depends on width. At 16 bits the review measured a looped /3 at
460 T in 16 bytes, against 217 T in 36 bytes, both including RET, for a
reciprocal-style kernel. Treat the 16-bit form as a size candidate and the 8-bit form as a
speed candidate against generic division. A 256-byte quotient table is faster
when residency permits. Check the complete dividend domain and the carry chain.

Original host model of the pass counts and preload limits above:

```python
# example: iterative-division-model
def exact(divisor, width, steps, preload, plus):
    shift = (divisor + 1 if plus else divisor - 1).bit_length() - 1
    for x in range(1 << width):
        y = preload
        for _ in range(steps):
            assert plus or x >= y
            y = (x + y if plus else x - y) >> shift
        if y != x // divisor:
            return False
    return True
for width, divisor, steps in ((8, 3, 4), (8, 7, 3), (8, 15, 2), (8, 31, 2),
                              (16, 3, 8), (16, 7, 6), (16, 15, 4)):
    assert exact(divisor, width, steps, (1 << width) // divisor, True)
    assert not exact(divisor, width, steps - 1, (1 << width) // divisor, True)
for divisor, steps in ((5, 4), (9, 4), (17, 2)):
    assert exact(divisor, 8, steps, 0, False)
    assert not exact(divisor, 8, steps - 1, 0, False)
preloads = lambda d, s: [p for p in range(256) if exact(d, 8, s, p, True)]
assert preloads(3, 4) == [85] and preloads(15, 2) == [17]
assert preloads(7, 3) == list(range(36, 74))
print("iterative division: pass counts and preloads exact")
```

Mechanism: [iterative fixed-point division](https://github.com/mbaze/Z80-Bits/blob/60467d73ce814fec26c4c829816f299fb8a162b7/iterative-fixed-point-division.md);
see the [corpora review](../../audit-z80/references/z80-routine-corpora-review.md)
for its checked listings and the reciprocal comparison.

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

## Signed narrowing with saturation

MEDIUM; only where the caller specifies clamping rather than wrap. A signed
16-bit value fits a signed byte exactly when H equals the sign extension of
L's bit 7; `ADD A,A; SBC A,A` builds that byte from L.

```asm
; example: narrow-s16-sat
    ld a,l
    add a,a
    sbc a,a
    xor h
    ld a,l
    jr z,narrow_done
    ld a,h
    add a,a
    sbc a,a
    xor $7f
narrow_done:
```

A = HL clamped to -128..127 in 12 bytes; 32 nominal T when it fits and
46 T when it clamps. HL survives; Z is set exactly when no clamping occurred.
The clamped results $7F/$80 are nonzero, so Z stays a valid exactness result
on both paths. Other flags are destroyed. Check all 65,536 inputs, both
paths' cost and every consumer of Z. Wrap semantics need plain `LD A,L`.
The same identity appears, without the Z result, in a
[reviewed external routine](../../audit-z80/references/z80-routine-corpora-review.md#verified-kernels);
that review also lists checked square-root, modulo-3, constant-division and
decimal-conversion kernels. Licenses and local proof gate their reuse.

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
