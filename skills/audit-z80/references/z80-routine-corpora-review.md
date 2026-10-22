# Routine Corpora: Reviewed Sources And Transfer Limits

Load when researching a routine from Zeda's *Z80 Optimized Routines*, baze's
*Z80 Bits*, or the pages they link, or when extending this plugin's loop,
arithmetic or PRNG references. This is a source assessment, not proof that a
candidate improves the current application.

## Provenance And Scope

- Zeda Thomas's [Zeda/Z80-Optimized-Routines](https://github.com/Zeda/Z80-Optimized-Routines),
  reviewed at [`b39015c8aabb566eaeeca76338b8fc8c7030ef2d`](https://github.com/Zeda/Z80-Optimized-Routines/tree/b39015c8aabb566eaeeca76338b8fc8c7030ef2d),
  its latest commit (2021-05-25), retrieved on 2026-10-22. It holds 239 files
  in spasm-ng syntax: 94 math, 21 conversion, 10 generic utility, 11 graphics,
  search, sort and miscellaneous, 3 example, 4 top-level and 96 TI-83+/84+
  files under `ti8x/`.
- Milos "baze" Bazelides's [mbaze/Z80-Bits](https://github.com/mbaze/Z80-Bits),
  reviewed at [`60467d73ce814fec26c4c829816f299fb8a162b7`](https://github.com/mbaze/Z80-Bits/tree/60467d73ce814fec26c4c829816f299fb8a162b7)
  (2026-05-25), retrieved on 2026-10-22: a README and seven articles,
  approximately 2,700 words.
- Linked pages read on 2026-10-22: the original [Z80 Bits page](https://baze.sk/3sc/misc/z80bits.html)
  (last updated 2006, marked unfinished; Zeda links the
  [Grauw mirror](http://map.grauw.nl/sources/external/z80bits.html)),
  [WikiTI Z80 Optimization](https://wikiti.brandonw.net/index.php?title=Z80_Optimization),
  [Z80 Heaven optimization](http://z80-heaven.wikidot.com/optimization),
  Patrik Rak's [xorshift](https://gist.github.com/raxoft/c074743ea3f926db0037)
  and [CMWC](https://gist.github.com/raxoft/2275716fea577b48f7f0) gists,
  [Zeda/z80float](https://github.com/Zeda/z80float) and Koopman's
  [CRC polynomial zoo](https://users.ece.cmu.edu/~koopman/crc/crc16.html).
- Zeda's [license](https://github.com/Zeda/Z80-Optimized-Routines/blob/b39015c8aabb566eaeeca76338b8fc8c7030ef2d/LICENSE.md)
  permits use, modification and distribution for any purpose, except for files
  with their own license header. File headers add terms or credits:
  [`hotspot.z80`](https://github.com/Zeda/Z80-Optimized-Routines/blob/b39015c8aabb566eaeeca76338b8fc8c7030ef2d/misc/hotspot.z80)
  points to a forum thread, John Metcalf's xorshift asks for credit, and
  several routines credit calc84maniac or Runer112.
- mbaze/Z80-Bits and the 2006 page declare no license. The WikiTI page shows
  no notice; Z80 Heaven declares the GNU FDL; z80float declares Apache-2.0.
  Rak stated in a 2022 reply on the xorshift gist that it may be treated as
  public domain; the CMWC gist states no license.
- This plugin imports no upstream implementation or prose. Its examples are
  original sequences derived from the reviewed mechanisms and checked by the
  bundled tests. Reusing an upstream file requires that file's terms.

## Extracted Guidance

| Active question | Reference | Delta relative to the existing catalogue |
| --- | --- | --- |
| Constant divisor near a power of two | [Arithmetic](../../optimize-z80/references/arithmetic.md) | Fixed-point recurrences for 2^N±1, exact pass counts and preloads, and a measured 16-bit crossover against a reciprocal-style kernel. |
| Long loop that must keep A | [Loops and data](../../optimize-z80/references/loops-and-data.md) | Biased single-pair DJNZ counter with its silent range failure; CPI as pointer advance and BC test with flag and contention limits. |
| Signed value narrowed to a byte | [Arithmetic](../../optimize-z80/references/arithmetic.md) | Sign-extension test for saturating 16→8 narrowing with a Z exactness result. |
| Deterministic noise or sequencing | [Demoscene math](../../optimize-z80/references/demoscene-math.md) | Galois LFSR step, maximal tap bytes and correlation limits. |
| Square root, modulo 3, /3, decimal output | This review, [verified kernels](#verified-kernels) | Externally written kernels checked over their full declared domain; no catalogue treatment. |

None establishes a speed or size win in a consumer project. Existing ABI,
flag, SMC, interrupt, model and evidence gates remain authoritative.

## Technical Coverage

“Existing” means the sound mechanism was already covered locally; “held”
means it was not promoted; “not run” means read without execution.

| Body | Extraction / disposition |
| --- | --- |
| [mbaze: 16-bit loops](https://github.com/mbaze/Z80-Bits/blob/60467d73ce814fec26c4c829816f299fb8a162b7/clever-16-bit-loops.md) | Extracted. The stated range 1..65281 and costs were reproduced; the out-of-range behavior was added. |
| [mbaze: clearing AF](https://github.com/mbaze/Z80-Bits/blob/60467d73ce814fec26c4c829816f299fb8a162b7/clearing-af.md) | Correct: `XOR A; LD B,A; INC B` leaves AF=$0000, including F bits 3/5, with B=1. Held as a one-off setup for the existing PUSH-fill row. |
| [mbaze: signed multiplication](https://github.com/mbaze/Z80-Bits/blob/60467d73ce814fec26c4c829816f299fb8a162b7/deferred-signed-multiplication.md) | Existing [signed correction](../../optimize-z80/references/demoscene-math.md#signed-correction-after-unsigned-multiplication); independent corroboration only. |
| [mbaze: CRC-16](https://github.com/mbaze/Z80-Bits/blob/60467d73ce814fec26c4c829816f299fb8a162b7/fast-crc-16.md) | Algorithm correct; output contract wrong ([below](#exclusions-and-counterexamples)). Held: no catalogue CRC kernel is needed; BridgeZX delegates CRC to its client. Its loop control supports the CPI entry. |
| [mbaze: iterative division](https://github.com/mbaze/Z80-Bits/blob/60467d73ce814fec26c4c829816f299fb8a162b7/iterative-fixed-point-division.md) | Extracted. All five listings are correct over their full domain. |
| [mbaze: LFSR](https://github.com/mbaze/Z80-Bits/blob/60467d73ce814fec26c4c829816f299fb8a162b7/random-lfsr.md) | Extracted. Taps $2D are maximal at 8 and 16 bits; the plugin example uses $39. |
| [mbaze: string length](https://github.com/mbaze/Z80-Bits/blob/60467d73ce814fec26c4c829816f299fb8a162b7/string-length.md) | Code correct; prose inverted. Held as an existing CPIR size idiom. |
| Zeda `conversion/` (21) | [`uitoa_16`](https://github.com/Zeda/Z80-Optimized-Routines/blob/b39015c8aabb566eaeeca76338b8fc8c7030ef2d/conversion/uitoa_16.z80) verified; its alternating add/subtract digit extraction avoids a restore step. Others not run. |
| Zeda `math/division/` (30) | `HL_Div_3` verified. Other cycle claims not imported. |
| Zeda `math/multiplication/` (18) | Not run; operand-distribution guidance already covers variant selection. |
| Zeda `math/squareroot/` (10) | `sqrtHL_very_fastest` and `sqrtA_fastest` verified. |
| Zeda `math/misc/` (14) | `HL_mod_3`, `A_mod_3` and the `cpHL` compare idiom verified. Fixed 8.8 log/ln/pow2 not run: no accuracy contract adopted. |
| Zeda `math/rng/` (14) | `xorshift16` verified; `lfsr.z80` uses taps $2D. `rng8_very_very_fast` held: it mixes R, whose increments depend on the caller's path, conflicting with the [R contract](../../optimize-z80/references/z80-techniques.md#r-sampling-and-refresh). Others not run. |
| Zeda `math/trig/`, `math/float/` | Not run; float notes point to z80float. |
| Zeda `utility/` (10) | Remainder-entry LDI copy and IM2 setup are existing techniques. `stringlength` comments state the CPIR convention correctly. `diRestore` reads IFF2 once through `LD A,R`; the existing [IFF2 caveat](spectrum-hardware-esxdos.md) applies. |
| Zeda `gfx/`, `search/`, `sort/`, `misc/` | Not run. Callback-based circle/line plotters do not change the absent rasterizer entry. |
| Zeda `ti8x/` (96), `examples/` | Not transferable: TI LCD drivers, graph buffers, VAT and OS calls. |
| [Z80 Bits, 2006](https://baze.sk/3sc/misc/z80bits.html) | Read, not run. Restoring multiply/divide/square root, square-table multiply, LCG generators, decimal/hex conversion and CRC-CCITT are existing families; the author marks the table-driven CRC untested. |
| [WikiTI](https://wikiti.brandonw.net/index.php?title=Z80_Optimization) | Read, not run. Mostly existing; its fast 16-bit counter matches the Grauw-derived split counter. `CPI` as a counter extracted; conditional RST rejected for Spectrum ([below](#exclusions-and-counterexamples)). |
| [Z80 Heaven](http://z80-heaven.wikidot.com/optimization) | Read, not run. The compare idiom is verified here; carry masks and flag tricks are existing. |
| [Rak gists](https://gist.github.com/raxoft/c074743ea3f926db0037) | Author figures recorded under [PRNG candidates](#prng-candidates); not reproduced. |
| [z80float](https://github.com/Zeda/z80float) | Pointer only. Single and extended formats document zero/inf/NaN encodings, but no error bounds; no floating format is adopted. |
| Koopman CRC zoo | The site refused connections on 2026-10-22. Its indexed pages list 0xd175 (implicit +1 notation; 0xA2EB conventional) as CRC-16F/4.2 with HD=4 up to 32,751 data bits. Secondary corroboration only. |
| Omnimaga, Cemetech and UTI threads; spasm-ng; Grammer2; Doors CS 7 | Not reviewed: forum discovery threads, an assembler and TI programs. |
| [Metcalf xorshift article](http://www.retroprogramming.com/2017/07/xorshift-pseudorandom-numbers-in-z80.html) | Unreachable on 2026-10-22; checked through Zeda's attributed copy. |

## Verified Kernels

Upstream code was transcribed into SjASMPlus syntax only for these checks.
Costs are input-weighted nominal T under z88dk-ticks, not the source's
figures; they exclude CALL and, where marked, RET.

| Routine | Domain checked | Measured cost / size | Contract and terms |
| --- | --- | --- | --- |
| [`sqrtHL_very_fastest`](https://github.com/Zeda/Z80-Optimized-Routines/blob/b39015c8aabb566eaeeca76338b8fc8c7030ef2d/math/squareroot/sqrtHL_very_fastest.z80) | A=isqrt(HL), all 65,536 | 361.0 T with RET; 88 bytes | Destroys HL/DE; uses a one-byte `CP n` skip. |
| [`sqrtA_fastest`](https://github.com/Zeda/Z80-Optimized-Routines/blob/b39015c8aabb566eaeeca76338b8fc8c7030ef2d/math/squareroot/sqrtA_fastest.z80) | D=isqrt(A), A=remainder, all 256 | 139.2 T with RET; 38 bytes | Destroys E. |
| [`HL_Div_3`](https://github.com/Zeda/Z80-Optimized-Routines/blob/b39015c8aabb566eaeeca76338b8fc8c7030ef2d/math/division/HL_Div_3.z80) | HL=HL/3, all 65,536 | 217 T with RET; 36 bytes | Destroys A/B/C/E. |
| [`HL_mod_3`, `A_mod_3`](https://github.com/Zeda/Z80-Optimized-Routines/blob/b39015c8aabb566eaeeca76338b8fc8c7030ef2d/math/misc/HL_mod_3.z80) | A=HL mod 3 and A mod 3, all inputs | 106.2 / 91.2 T without RET; 30 / 26 bytes with RET | Destroys HL. |
| [`signed16To8`](https://github.com/Zeda/Z80-Optimized-Routines/blob/b39015c8aabb566eaeeca76338b8fc8c7030ef2d/conversion/signed16To8.z80) | Saturating HL→A, all 65,536 | 43.9 T without RET; 12 bytes | HL preserved; Runer112. |
| [`cpHL`](https://github.com/Zeda/Z80-Optimized-Routines/blob/b39015c8aabb566eaeeca76338b8fc8c7030ef2d/math/misc/cpHL.txt) | `OR A; SBC HL,DE; ADD HL,DE`: Z/C as unsigned CP, HL preserved | 81 edge and 3,000 seeded pairs | Not exhaustive; S/P/V/H differ from CP. |
| [`uitoa_16`](https://github.com/Zeda/Z80-Optimized-Routines/blob/b39015c8aabb566eaeeca76338b8fc8c7030ef2d/conversion/uitoa_16.z80) | Decimal string, all 65,536 | 72 bytes; cost not measured | Returned HL may differ from the buffer start. |
| [`xorshift16`](https://github.com/Zeda/Z80-Optimized-Routines/blob/b39015c8aabb566eaeeca76338b8fc8c7030ef2d/math/rng/xorshift16.z80) | Period 65,535 from seed 1 | 82 T without RET; 21 bytes with RET | SMC state; credit Metcalf. |

mbaze listings, all correct over their declared domain: B/3 in 71 T and
18 bytes; B/7 in 74 T and 19 bytes; both B/5 forms in 88 and 91 T (22 and
23 bytes). All but B/3 destroy C, and the second B/5 form also destroys B.
The looped HL=DE/3 takes 460 T in 16 bytes over all 65,536 inputs and
destroys B. Their CRC loop measures 67.0 T
per byte in 27 bytes, excluding the 512-byte tables and generator.

## Exclusions And Counterexamples

| Printed material | Evidence / consequence |
| --- | --- |
| [mbaze string length](https://github.com/mbaze/Z80-Bits/blob/60467d73ce814fec26c4c829816f299fb8a162b7/string-length.md) | Both listings return the length without the terminator. The prose says omitting `SCF` / `DEC A` excludes it; execution shows omission includes it. The 8-bit form leaves B unspecified; it is correct for any B when string plus terminator fit 255 bytes (derived; run with B=0 and $12). |
| [mbaze CRC-16](https://github.com/mbaze/Z80-Bits/blob/60467d73ce814fec26c4c829816f299fb8a162b7/fast-crc-16.md) | “A:A' = CRC” holds only when the high byte mismatches. After a match or low-byte mismatch the final `EX AF,AF'` leaves A=low and A'=high. It also uses D'/E'/H'/L' and destroys A'/F'/BC/HL. The $FE00–$FFFF tables overlap a common IM2 table placement; place them from the project's memory map. |
| Zeda “avg” cycle comments | Some are the midpoint of min and max, not an input-weighted mean: `sqrtA_fastest` claims 129.5 and measures 139.2. `sqrtHL_very_fastest` and `HL_Div_3` claims matched. Measure; do not import counts. |
| Zeda README | Its CMWC link drops the final `0` of gist `2275716fea577b48f7f0` and returns 404. |
| [WikiTI](https://wikiti.brandonw.net/index.php?title=Z80_Optimization) `JR cc,-1` | The displacement byte $FF executes as `RST $38`. On a Spectrum that enters the ROM's IM1 handler, with keyboard-scan and FRAMES side effects. Rejected unless the project owns $0038. |
| [mbaze 16-bit loops](https://github.com/mbaze/Z80-Bits/blob/60467d73ce814fec26c4c829816f299fb8a162b7/clever-16-bit-loops.md) | Correct inside 1..65281. N=65282 biases to BC=1 and runs once without any signal; callers need a guard. |

## PRNG Candidates

| Generator | Evidence | Transfer boundary |
| --- | --- | --- |
| Galois LFSR, taps $2D (mbaze `Lfsr8`/`Lfsr16`, Zeda `lfsr.z80`) | Host model: periods 255 and 65,535. mbaze's 16-bit SMC routine matches the model for 2,000 steps. | Strong adjacent correlation; zero state forbidden. |
| Metcalf xorshift16 | Period 65,535 from seed 1; 82 T measured. | SMC state; credit required. |
| Rak xorshift, 32-bit state, 8-bit output | Author figures: 28 bytes, 122 T, period 2^32−1. | Not reproduced; the author reports better Diehard results for other shift triplets. |
| Rak CMWC | Author figures: 32+10 bytes, 146–149 T, period 253×2^59; its state table must stay in one 256-byte page. | Not reproduced; no license or published statistical results. |

## Observed Verification

Checks ran from the pinned checkouts in a scratch directory outside this
repository, with SjASMPlus 1.23.1, z88dk-ticks v0.14c beta (`-mz80`) and
Python 3.9.6. Results concern those revisions under nominal timing, with no
contention or interrupts.

| Check | Observed result | Limit |
| --- | --- | --- |
| mbaze listings | String length (four lengths, two B values), AF clear (three entry states), biased loop (seven N), five division listings, LFSR model and Z80 run, and CRC all behave as recorded above, including both contract errors. | CRC compared at one 9-byte vector (CRC-16/XMODEM check value $31C3, polynomial $1021) and one 4,096-byte block (polynomial $A2EB), each with matching and mismatching expected values. |
| Zeda kernels | All eight entries in [verified kernels](#verified-kernels) pass. | Only those files were executed; transcription changed syntax, not instructions. |
| Tap search | Six of 255 nonzero tap bytes give 16-bit maximal period; only $2D also gives 8-bit maximal period. | Host model of the left-shift Galois step. |
| Division family | Pass counts and preload sets in the [arithmetic reference](../../optimize-z80/references/arithmetic.md) hold exhaustively for 8-bit and listed 16-bit widths. | Host model; the plugin's B/15 example is also run under z88dk-ticks. |

### Plugin Integration Checks

`scripts/validate_skills.py` passes all 11 skills. The optimize technique
tests pass 16 tests, including the five new examples and two host models;
mutating the B/15 preload or the narrowing clamp makes them fail. A link check
resolves 88 local links/fragments in the changed documents and 19 pinned
upstream paths. Skill frontmatter, invocation metadata and routing are
unchanged; `git diff --check` passes.

## Transfer Policy

Use these sources as discovery catalogues. Reuse an idea only after stating
its input domain, live registers and flags, stack/ISR ownership, physical
placement, CPU model and cost unit. Verify a narrow kernel over its complete
domain and measure an input-weighted cost on the declared target; source
cycle comments are not measurements. Prefer a simpler algorithm or table
before an instruction-level substitution. Runtime-sensitive candidates keep
the normal promotion gate and disposable-worktree requirement.
