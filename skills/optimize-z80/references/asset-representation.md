# Asset Representation And Compression

Load for a measured asset, table, bank-pressure or decompression bottleneck.
Prefer the project's existing format and codec unless another representation
can improve the active constraint. Follow [hard-contract.md](hard-contract.md)
for experiments and reuse the [compression evidence card](measurement.md#compression-tradeoff-evidence-card).
This reference supplies candidate mechanisms, not measured application wins.

## Establish The Actual Data Path

Trace source asset → converter → transform → compressor → linked blob →
decoder → inverse transform → consumer. Freeze the original bytes and identify
which representations must remain public or persisted. A smaller intermediate
file is irrelevant if its linked decoder, inverse or consumer access costs more.

Record only the details that can change correctness or ranking:

- Asset shape, field stride, numeric width, signedness and byte order.
- Consumer access: sequential, indexed, random seek, frame or tile locality.
- Decode destination, source/history visibility, banks and live buffer intervals.
- Codec bitstream version, options, decoder implementation and direction.
- Transform order, reconstruction seeds, resets and final consumer layout.
- Approximation/error allowance, if any; otherwise require byte equality.

Keep these with the existing evidence card; do not create a second accounting
schema. Include packed data, framing, seeds, decoder share, call glue, inverse,
alignment and any required mapping tables in storage. Keep peak workspace,
stack, residency/bank pressure and measured stalls in their existing domains.

## Search A Small Set Of Reversible Representations

Compare unchanged data with only the candidates suggested by its structure:

| Observed structure | Candidate | Obligation |
| --- | --- | --- |
| Records whose individual fields vary smoothly | Field-major layout, then differences within each field | Preserve field identity and define consumer access |
| Related animation frames | Dense XOR/delta frames, sparse edits, changed spans or tiles | Compare framing and restoration work, not just changed bytes |
| Smooth integer controls | First or second differences | Retain initial state and exact arithmetic |
| Mask/pixel or other planes with distinct patterns | Separate or regroup planes | Count lost cross-plane matches and extra decoding |
| Repeated period or symmetric table | Seed/replay or partial table | Count reconstruction, indexing and retained RAM |
| Data generated from a compact description | Generator versus stored representation | Prove output/error, startup cost and dependencies |

Try the existing compressor on each retained representation. A pure transpose
preserves length and byte histogram; it can improve sequence locality without
changing order-zero entropy. Entropy, run lengths and curve-fit scores suggest
experiments. They do not rank actual LZ output or prove lossless savings.

### Differences And Seeds

Define empty, one-element and short-stream behavior before encoding. A first
difference stream needs an initial value; second differences need enough state
to recover both value and slope. XOR differences also need a starting value.
Count seeds even when a helper silently drops them from the returned stream.

For bytewise arithmetic, state whether reconstruction wraps modulo 256. Decode
using that same rule. For multibyte fields, distinguish arithmetic on whole
values from arithmetic on their separate bytes; carry and signed interpretation
can make these different formats. Specify byte order and overflow explicitly.

Reset differences at defined field, block or keyframe boundaries. Do not delta
adjacent bytes belonging to unrelated record fields. A transform order and its
inverse order are part of the format; do not interchange transpose and delta
unless the exact fieldwise operations are proved equivalent.

Integer quadratics can have constant second differences; rounded, clipped or
piecewise mirrored curves need not. Replacing a sine curve with a quadratic is
an approximation. Require an error criterion, including endpoints, accumulated
drift and perceptual acceptance where relevant, before comparing its size.

### Consumer Layout And Access

Transposition has no inverse-copy cost only when the consumer accepts the new
layout directly. Otherwise measure reconstruction/scatter work and altered
indexing. Delta decoding introduces a dependency on earlier values; it can
remove cheap random access even when the packed stream becomes smaller.

Use periodic keyframes or independently reset blocks when seeking, recovery or
parallel asset access needs them. Count their storage and initialization cost.
Sorting particles, tiles or frames also needs an identity/permutation mapping
when their original order is observable. Do not change semantics to improve a
compressor's input order without identifying and preserving that relationship.

Sparse edits and dense XOR frames are different candidates. Offset/value pairs
carry position overhead; dense differences retain unchanged positions. Compare
both against spans, tiles and whole-frame compression on the actual assets.
Separating streams may lose useful matches and duplicate headers or seeds.

## Separate Codec Format From Decoder Implementation

A compact, fast, backward or specialized decoder can change code size, stack,
workspace and time while reading the same format. A codec name alone does not
identify the implementation being measured. Pin the exact compressor/decoder
pair, version and options; reject mismatched bitstreams before benchmarking.

In-place decoding requires a proven overlap layout for the chosen direction.
Use the packer's reported safety margin where applicable; backward decoding is
not blanket permission for arbitrary overlap. Keep decoder, stack and return
path outside overwritten live ranges. Prefix/dictionary compression requires
identical dictionary bytes, placement and lifetime at decode time; rebuilding
the dictionary invalidates dependent packed assets.

A shared decoder can amortize code across assets. A new micro-format may add an
unshared inverse, error path or workspace even when its blob is smaller. A
generator still needs output RAM if the consumer requires a materialized table;
it also has startup latency, numeric error and possible firmware dependencies.

## Chunked Storage Needs A Resumable Decoder

Reading a compressed file in fixed-size chunks does not make a one-shot
routine resumable. Choose independently decodable blocks with bounded output,
or retain the actual decoder state across refills: bit buffer, token progress,
partial literal/match, previous offset, source position and output history.

Do not discard a source chunk while the decoder still references it. A match
may cross a refill or output-ring boundary; define the available history and
prove that source, history and destination stay visible through bank changes.
An output byte quota can stop inside a token, so source pointer plus output
count alone may be insufficient restart state.

Bound input consumption, output production and uninterrupted service time.
Small input chunks can expand into large output bursts. Measure blocking file
calls and recovery paths on the intended backend; request size is not a bound
on filesystem latency. See [modern I/O](modern-spectrum-io.md) for batching.

After open succeeds, close on read, decode, validation and cancellation exits.
Distinguish a short read/EOF from an I/O error and from a truncated packed block.
Check declared packed/decoded lengths and destination bounds before exposing
an asset. Preserve the original error if cleanup also fails. Define underflow,
retry/reset and fallback behavior; do not publish partially reconstructed data.

## Budget And Verify The Complete Candidate

A rate expressed in cycles per output byte multiplies decoded length, not
packed length. Add setup, inverse, placement, interrupts and consumer work.
Use the intended [model and memory placement](zx-spectrum-models.md); include
data-dependent paths and contention where applicable. Buffering can smooth
latency but does not create CPU time or an independently running consumer.

Verify in this order, retaining evidence only for the exercised scope:

1. Host round trip against original bytes, including empty/short data, wrap,
   field boundaries, keyframes and the declared approximation criterion.
2. Target decode/inverse with guards around source, destination, workspace and
   stack; exercise minimum/maximum lengths, overlap and bank edges.
3. Relevant truncation, corruption, refill, reset and recovery paths when those
   inputs can occur; compare consumer output/access semantics.
4. Fresh linked size and peak lifetime/map evidence, then decode and stall
   measurements on representative and worst relevant assets.

## Evidence And Transfer Limits

The transform search derives from reviewed [Chapter 14, preparation](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch14-compression/draft.md#L273-L382)
and [Appendix J, export pipeline](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-j-modern-tools.md#L287-L311).
Their fixed ratios, entropy rankings and inverse-cost claims are not evidence.
[ZX0's primary README](https://github.com/einar-saukas/ZX0/blob/ecde3a2ae05061fe06469ed46df81a33b7de7d86/README.md)
corroborates format-version, decoder-variant, overlap-margin and dictionary
contracts. Obtain implementations and licenses from their primary projects.
See the [source assessment](../../audit-z80/references/antique-toy-review.md)
for errors, observed checks and remaining limits; no upstream code is imported.
