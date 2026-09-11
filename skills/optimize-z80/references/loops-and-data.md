# Loops And Data Layout

Load for hot scans, copies, parsers or repeated address calculations. These
are core-Z80 candidates, not Spectrum timing claims. SAFE means compatible
with the proved data/flag contract; MEDIUM spends code/RAM or changes layout.
Costs below are nominal, excluding waits, contention and ISR work. Derivations
use the [Zilog instruction manual](https://www.zilog.com/docs/z80/um0080.pdf).

## Split 16-bit loop counters

MEDIUM; useful when a long loop spends time on `DEC DE; LD A,D; OR E; JP NZ`.
For N=1..65536, use B=N modulo 256 and D=ceil(N/256) modulo 256. DE=0 on
entry means 65536, so a zero-length API needs a guard before this example.
The body must preserve B/D and cannot require the original DE or incoming
flags. HL counts visits here; replace that instruction with the real body.

```asm
; example: split-counter
    ld b,e
    dec de
    inc d
split_loop:
    inc hl
    djnz split_loop
    dec d
    jp nz,split_loop
```

Setup is 14 T. With K=ceil(N/256), loop control is `13*N + 9*K` T,
excluding the body, versus `24*N` for the four-instruction control above.
This saves repeated 16-bit zero tests, not the body's work. Check 1, 255,
256, 257, 65535 and the zero/65536 convention. Fall back to the original
counter if B/D are live or extra spills erase savings.
Mechanism: [Grauw's fast loops](https://map.grauw.nl/articles/fast_loops.php);
its MSX M1-wait totals are not the nominal totals derived here.

## Partial unrolling and remainder entry

MEDIUM; fixed blocks or frequent medium/large copies. For U=16 and a positive
N divisible by 16, this body uses 35 code bytes and `16*N + 10*(N/16)` T:

```asm
; example: ldi-block
copy_loop:
    DUP 16
    ldi
    EDUP
    jp pe,copy_loop
```

This example uses SjASMPlus DUP/EDUP syntax. HL/DE/BC have normal LDI roles;
BC and P/V must reach the branch unchanged by any added work. Compare against
`21*N-5` for LDIR, then include setup and dispatch. It preserves LDI's forward
overlap behavior, not general memmove semantics.

For arbitrary positive N, enter at the last R instructions of the chain,
where `R=((N-1) mod U)+1`; the skipped bytes are `2*(U-R)`. Then
`ceil(N/U)` chain endings run. Use existing computed dispatch or a short
remainder path; SMC adds the existing SMC/interrupt gates. Never simply run
the full chain for a nonmultiple: BC may pass zero before the branch.
Validate lengths around each block boundary, source/destination overlap and
end guards; retain LDIR for short/irregular copies when entry overhead wins.
See [Grauw's remainder-entry construction](https://map.grauw.nl/articles/fast_loops.php).

## Branch choice and flag lifetime

SAFE with the same live flags and legal jump range. For NZ/Z/NC/C, a
conditional JR costs `7+5*p` expected T when taken probability is p; JP costs
10 T. JP is faster on average above p=0.6 but uses one extra byte. Unconditional
JP is 10 T versus JR's 12 T. A hard deadline needs worst-path cost, not p.
Check displacement after layout changes and preserve relocatability needs.

Reuse a preceding instruction's flags only when they encode the required
condition: DJNZ does not update flags, INC/DEC preserve carry, and LDI's P/V
tests remaining BC, not result parity. A carry-derived mask can replace a
branch, but count mask creation and register pressure. Validate all relevant
inputs and flag consumers; keep the branch if the condition or timing differs.

## Hoisting, specialization and fusion

SAFE for stable inputs; MEDIUM when cloning loops. Move invariant address,
mode and mask work outside the loop. If a mode is fixed for the whole call,
dispatch once to two specialized loops instead of testing it per element
(loop unswitching). Fuse adjacent scans only if reads/writes have no ordering
dependency. Alternatively split a loop when different passes need different
register allocations. Net saving is removed per-item work times N, minus
dispatch, spills and any extra traffic; code duplication consumes resident RAM.
Check aliasing, volatile/I/O reads, ISR mutations and empty inputs. Revert to
the original loop if these contracts or whole-call savings cannot be proved.
[z88dk's guidance](https://github.com/z88dk/z88dk/wiki/WritingOptimalCode)
supports hoisting; fusion/unswitching remain project-specific candidates.

## Pointer induction and termination

SAFE when bounds are proved. Replace repeated `base + index*stride` with a
pointer increment; retain a separate logical index only if it is consumed.
For a page-contained walk, INC L may replace INC HL (4 versus 6 nominal T),
but only if its missing carry cannot change any accessed address or live
post-loop pointer. Sentinel termination can remove a bounds test only when
the terminator is guaranteed inside owned readable storage. A temporary
sentinel requires writable spare storage, restoration and exclusive ownership.
Never remove validation from untrusted input or read one byte beyond allocation.
Check empty/full buffers and page/bank crossings; use bounded 16-bit traversal
as the fallback. Inspect compiler output before rewriting equivalent C syntax.

## Split tables and field arrays

MEDIUM; repeated indexed reads where multiplication/address setup dominates.
Split N 16-bit values into low[N] and high[N], each page-aligned for N<=256.
The same byte index selects both halves; storage remains 2*N plus alignment,
not a free reduction. It can avoid doubling the index/carry handling at the
cost of two table bases. This is a layout candidate derived from Z80 addressing,
not a universal benchmark result. Reconstruct every entry and test index 255;
verify padding, bank visibility and the cost of consumers expecting word pairs.
Keep interleaved words when sequential pair loads dominate.

Similarly, separate frequently scanned fields into arrays when the scan uses
only one or two fields. This can replace record-stride arithmetic with contiguous
walks, but whole-object operations may become slower. Include conversion,
serialization and extra live pointers; preserve record identity and external
formats. Compare with the original array of records on actual access patterns.

## Packed flags and narrow indices

MEDIUM; resident/RAM pressure. N Boolean flags need ceil(N/8) bytes as a bitset
instead of N byte flags; extraction and read-modify-write cost time and may
race with an ISR. Dense same-bank objects can use byte indices instead of
16-bit pointers only when all IDs plus null/sentinel values fit; reconstruction
and lookup still cost time. Test boundary indices, reserved IDs and every flag
operation. Reject if concurrent ownership or external ABI expects the old
representation. Byte flags and full pointers remain the fallback for hot paths.

## Power-of-two indexing

SAFE for unsigned values: `x mod 2^k = x & (2^k-1)`. A 256-byte circular
buffer can wrap an eight-bit index naturally. Capacity and full/empty state
must remain explicit: equal head/tail cannot mean both without a separate
convention. Padding a record/ring to a power of two trades RAM for cheaper
addressing; count padding across all elements. Signed C remainder is not the
same transformation for negative inputs. Validate wrap, full/empty transitions
and producer/consumer ownership; keep general indexing when capacity is fixed
by protocol or RAM budget. For arithmetic range rules, see [math](arithmetic.md).

## Block I/O is not a memory copy

MEDIUM only for a pinned peripheral. Unrolling OUTI/INI can remove block-repeat
overhead, but B changes the high port address, and block input/output differ
in when B is decremented. A peripheral decoding all 16 address bits may see
different ports. Its minimum spacing can also forbid the faster stream.
Audit the Zilog bus sequence plus device manual and capture actual accesses;
include waits and pacing. Keep a fixed-BC IN/OUT loop or the existing paced
driver when address or rate requirements do not permit block I/O.
