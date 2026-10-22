# Demoscene Math And Procedural Data

Load for repeated small-domain arithmetic, table storage, display counters or
procedural data when the normal [arithmetic choices](arithmetic.md) leave a
material gap. These are MEDIUM candidates; flags, ABI, overflow and target
contracts still apply. No project byte or speed win is established here.
The [source assessment](../../audit-z80/references/antique-toy-review.md)
records provenance and rejected claims; use its pinned source as discovery,
not a library of verified routines.

## Exact Quarter-Square Multiplication

For unsigned bytes x,y, let Q(n)=floor(n²/4). Then
`x*y = Q(x+y)-Q(abs(x-y))` exactly: both arguments have the same parity,
so their discarded fractional quarters cancel. There is no inherent rounding
error. The sum needs nine bits (0..510); dropping its carry corrupts products.
Each Q entry needs 16 bits: 511 entries require at least 1022 data bytes;
a conventional 512-entry layout takes 1024, plus alignment padding and code.
Split byte planes still need a ninth index bit and a documented plane layout.

Use when repeated multiplies justify table residency. Count initialization,
lookup/setup, subtract, bank placement and padding against a software kernel;
reject when a rare call or existing hardware multiply removes the benefit.
Validate every input pair and exact table addresses in the assembled routine.
Base-Z80 costs do not predict Z80N/eZ80 costs or their available operations.

## Signed Correction After Unsigned Multiplication

For raw bytes x,y with sign bits sx,sy, their signed 16-bit product is
`(x*y - 256*sx*y - 256*sy*x) mod 65536`. Only the high product byte needs
conditional corrections, but both original factors must survive the kernel.
This can avoid absolute-value/result-negation scaffolding; count saved
operands, corrections and call boundaries before choosing it.

For a wider product, derive the correction at that width. A 16×8 routine
returning 16 bits promises a modulo result unless range proves no overflow;
it is not an unrestricted 24-bit signed product. A signed sine scaled by
128 is Q1.7: dividing its product by 256 halves the intended contribution.
Specify signed scaling, rounding and overflow before selecting result bytes.

Original host checks, exhaustive over 65,536 byte pairs each:

```python
signed = lambda v: v if v < 128 else v - 256
for x in range(256):
    for y in range(256):
        assert (x+y)**2 // 4 - (x-y)**2 // 4 == x*y
        corrected = x*y - 256*(x >= 128)*y - 256*(y >= 128)*x
        assert corrected & 65535 == (signed(x)*signed(y)) & 65535
print("quarter-square and signed correction: 65536 pairs each")
```

Discovery: [quarter squares and signed correction, ch04](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch04-maths/draft.md#L58).
The identities above do not validate that chapter's multiply listings/timings.

## Exact Tables From Second Differences

For a fixed table v, encode v[0], d[0]=v[1]-v[0], then second differences
`e[i]=d[i+1]-d[i]`. Decode by updating delta, then value. Inspect the actual
range before choosing packed width; smoothness alone is not a bound.

For the declared reference `round(127*sin(2*pi*i/256))`, second differences
are in {-1,0,1}. A 65-entry quarter contains 63 such differences: two seed
bytes plus 16 packed bytes = 18 data bytes. Full-period encoding needs
2+ceil(254/4)=66 data bytes. Neither figure includes decoder, folding code,
alignment, output RAM or startup time; no smallest-total-size claim follows.

A lookup folding to indices 0..64 requires **65 output entries**, including
the peak. A 64-byte buffer needs a different explicit peak rule. Negating a
+127 quarter produces -127, not -128; an asymmetric trough needs an exception.
Pin amplitude, phase, rounding and endpoints before claiming exactness.

Original host packing/decoding check against all 256 reference entries:

```python
import math
reference = [round(127*math.sin(2*math.pi*i/256)) for i in range(256)]
quarter = reference[:65]
d = [quarter[i+1]-quarter[i] for i in range(64)]
e = [d[i+1]-d[i] for i in range(63)]
assert set(e) <= {-1, 0, 1}
packed = [sum((v & 3) << (2*j) for j,v in enumerate(e[i:i+4]))
          for i in range(0, len(e), 4)]
seeds = [quarter[0], d[0]]
decoded, delta = [seeds[0]], seeds[1]
decoded.append(decoded[0]+delta)
for i in range(len(e)):
    code = (packed[i//4] >> (2*(i % 4))) & 3
    assert code != 2
    delta += code if code < 2 else code-4
    decoded.append(decoded[-1]+delta)
assert len(decoded) == 65 and 2+len(packed) == 18
for angle in range(256):
    index = angle & 127
    if index > 64:
        index = 128-index
    value = decoded[index] * (-1 if angle & 128 else 1)
    assert value == reference[angle]
print("second differences: 18 data bytes; 65 quarter / 256 full entries exact")
```

Choose full decoded table for frequent random lookup, folded quarter for
lower RAM, or sequential integration when access order permits it. Count
generator residency separately from the RAM it fills; reclaim startup code
only under the existing lifetime proof. Validate packed bit order, seed/delta
widths, buffer bounds and reinitialization. Compare actual codec/decoder totals
before adding an approximate generator plus residual corrections. A copied
golden table cannot stand in for exercising the inverse transform.
Discovery: [second-difference sine storage, appendix B](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-b-sine-tables.md#L153).

## Reduce The Answer Space Before Arithmetic

For unsigned byte n and constant k≥128, quotient n/k is only 0 or 1.
`CP k; SBC A,A; INC A` produces it in 15 nominal T / 4 bytes, clobbering A/F;
other registers survive. This computes no remainder and supplies no general
flag-result contract. Include call/setup costs and target waits. For constants
with an even simpler bit test, compare that alternative too.

Unsigned saturating add uses the wide sum's carry to choose raw sum or 255;
saturating subtract uses borrow to choose raw difference or zero. Preserve
the raw result while constructing a carry mask. These differ from modular
arithmetic and from signed saturation. Choose them only when the caller's
semantics need clamping, then test every input pair and live flags.

Original host value models; they do not execute those instructions:

```python
for k in range(128, 256):
    for n in range(256):
        mask = (-int(n < k)) & 255
        assert ((mask+1) & 255) == n//k
for x in range(256):
    for y in range(256):
        total, difference = x+y, x-y
        add = (total & 255) | (255 if total > 255 else 0)
        sub = (difference & 255) & (0 if difference < 0 else 255)
        assert add == min(total, 255) and sub == max(difference, 0)
print("large divisors: 32768 cases; saturation: 65536 pairs each")
```

Discovery: [answer-range and carry idioms, appendix K](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-k-superoptimizer.md#L45).
Restricted-search results do not establish global optimality; see
[bounded search obligations](z80-proof-obligations.md#bounded-search-results).

## BCD For Frequently Displayed Counters

Packed BCD can avoid repeated binary-to-decimal conversion for scores/timers.
Compare update + render + storage against binary, including other consumers;
physics, arbitrary arithmetic and serialized/public formats may favor binary.
An internal display representation must not silently change persisted data.

DAA consumes H/N/C from its preceding arithmetic. Valid decimal addition or
doubling can use ADD then DAA; decimal carry must survive between bytes.
Loads and 16-bit pointer increments can preserve carry; XOR-to-zero cannot.
Do not treat INC/DEC then DAA as unconditional decimal increment/decrement:
INC preserves incoming carry, and DEC of zero does not create a borrow.
Define zero/99 wrap, carry/borrow and overflow policy, then test all valid
digit patterns, incoming carry states and multi-byte propagation.
Prefer ordinary binary plus existing formatting when BCD conversions or
non-display operations erase its benefit. Source: [BCD tradeoffs, appendix M](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-m-bcd-arithmetic.md#L7).
CPU semantics: [Zilog manual](https://www.zilog.com/docs/z80/um0080.pdf),
DAA and INC/DEC instruction entries; those entries do not prove a project win.

## Procedural Data And PRNG Boundaries

A deterministic generator can replace stored assets only when its seed,
algorithm, output mapping and generation cost together beat the stored form.
For reproducible worlds/effects, specify seed encoding, forbidden states,
reset behavior, call order and register/flag clobbers. A 16-bit state plus
undeclared incoming carry is not an autonomous 16-bit generator. A routine
reading arbitrary memory or R also depends on mapping and execution timing.
Use [R sampling](z80-techniques.md#r-sampling-and-refresh) only within its
existing seed/refresh contract; deterministic mixing creates no new entropy.

Distribution shaping adds contracts: retain the ninth sum bit when averaging
two uniform bytes, and preserve the first sample across the second PRNG call.
Rejection sampling can remove range bias but has unbounded retry time; state
the accepted timing/bias policy before using it under a hard deadline.
Weighted tables require a uniform index; correlated samples need separate
analysis. A bitmap that looks random establishes no period or statistical
ranking. Test repeatability, range, histograms/correlations and target mapping
for the actual use; retain an existing generator when evidence is insufficient.
Discovery: [procedural state and shaping, ch04](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch04-maths/draft.md#L608).

## Galois LFSR Steps

A left-shift Galois step moves the outgoing bit into carry and turns it into
a tap mask. With taps t below bit 8, only L needs the XOR:

```asm
; example: lfsr16-step
    add hl,hl
    sbc a,a
    and $39
    xor l
    ld l,a
```

The step costs 6 bytes / 30 nominal T with HL as state; A/F are destroyed.
Loading and storing the state cost extra. A maximal-period tap set visits
every nonzero state once in 2^W-1 steps; zero never leaves zero. Exclude it
from seeds, resets and corrupted state. Of the 255 nonzero tap bytes, an
exhaustive review search found six maximal 16-bit values: $2D, $39, $3F,
$53, $BD and $D7. Only $2D is also maximal for the 8-bit `ADD A,A` form.

Each state is the previous one shifted, with only tap bits changed, so
adjacent outputs are strongly correlated. Use an LFSR for deterministic noise, dither or sequencing
where its period is the stated requirement, not as a statistical-quality
claim. Take one bit or a sparse sample per step if correlation matters.

```python
# example: lfsr-taps
def period(width, taps):
    mask, state, steps = (1 << width) - 1, 1, 0
    while True:
        state = ((state << 1) & mask) ^ (taps if state >> (width - 1) else 0)
        steps += 1
        if state == 1 or steps > mask:
            return steps
listed = [0x2D, 0x39, 0x3F, 0x53, 0xBD, 0xD7]
assert all(period(16, t) == 65535 for t in listed)
assert [t for t in listed if period(8, t) == 255] == [0x2D]
print("LFSR taps: six 16-bit maximal values; $2D also 8-bit maximal")
```

The model checks the listed values; the exclusion of the other 249 bytes is
review evidence, not repeated here. External generators checked or reported
in the [corpora review](../../audit-z80/references/z80-routine-corpora-review.md#prng-candidates)
include a 16-bit xorshift and 32-bit-state xorshift and CMWC generators.
Their periods, costs and license terms differ; the review records which
figures were reproduced.

## Verification Boundary

The Python blocks prove their declared mathematical/value models only.
Before promotion, run the assembled candidate against the reference domain,
check ABI/flags/stack and physical placement, then measure its complete call
boundary on each declared CPU/model. No custom floating format, GPU optimality
claim, PRNG ranking or source-wide performance number is adopted here.
