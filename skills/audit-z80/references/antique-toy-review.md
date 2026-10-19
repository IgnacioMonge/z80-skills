# Antique Toy: Reviewed Source And Transfer Limits

Load when researching a technique from *Coding the Impossible*, checking its
examples, or extending this plugin's demoscene references. This is a source
assessment, not proof that a candidate improves the current application.

## Provenance And Scope

- Source: Alice Vinogradova's [oisee/antique-toy](https://github.com/oisee/antique-toy).
- Reviewed revision: [`7313ecfaab710d1a105b7bff3be19aaf04dc5935`](https://github.com/oisee/antique-toy/tree/7313ecfaab710d1a105b7bff3be19aaf04dc5935),
  retrieved on 2026-10-19. All source links below pin this revision.
- Technical scope: the 23 English chapter drafts, appendices A–P, relevant
  listings/examples, and the companion tools. The English drafts and appendices
  contain approximately 208,000 whitespace-delimited words. Translations were
  checked for listing parity; their complete prose was not separately audited.
- The [author's disclaimer](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/disclaimer.md)
  identifies the material as unfinished and partly LLM-assisted. This review
  found errors beyond that general caveat; neither polished exposition nor
  successful assembly establishes a routine's semantics.
- The root [license](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/LICENSE.md)
  declares CC BY-NC 4.0. `spectools/pyproject.toml` separately declares MIT.
  This plugin imports no upstream implementation, table, illustration, or prose;
  it records original engineering guidance, evidence, and links. Reusing an
  upstream asset requires checking the license applicable to that asset.

## Extracted Guidance

| Active question | Optional reference | What changed relative to the existing catalogue |
| --- | --- | --- |
| Repeated narrow math or stored function tables | [Demoscene math](../../optimize-z80/references/demoscene-math.md) | Exact quarter-square/index-width contracts, signed correction, quantified second differences, bounded answer spaces and display-oriented BCD. |
| Repeated sampling or geometry/render work | [Generated rendering](../../optimize-z80/references/generated-rendering.md) | Compile sampling maps, derive dependent geometry, count generation/execution/transfer separately, and bound executable work lists and mapping ownership. |
| Game-loop state, movement or collision | [Simulation and collision](../../optimize-z80/references/simulation-and-collision.md) | Tick/coordinate domains, pool lifecycle, signed clamps, contact/overflow rules and spatial coverage. This does not supply a complete game engine. |
| Asset storage, loading or decode cost | [Asset representation](../../optimize-z80/references/asset-representation.md) | Reversible pretransforms, consumer layout, codec/decoder identity, overlap and resumable stream state. |
| Audio player, burst work or prepared frames | [Audio and frame queues](../../optimize-z80/references/audio-and-frame-queues.md) | AY shared resources and write events; buffer capacity, publication, service and recovery as separate obligations. |
| Music/effect synchronization or generated parameters | [Timeline assets](../../optimize-z80/references/timeline-assets.md) | Typed events, explicit clocks, exporter semantics, interpolation, catch-up and independent transition state. |

These references extend discovery and verification guidance. None provides a
measured speed/size win in a consumer project. Existing ABI, SMC/SP, model,
mutation and evidence gates remain authoritative.

## Technical Coverage

Every body below was reviewed for useful deltas and exclusion conditions.
“Existing” means its sound general mechanism was already covered locally;
“held” means the specific implementation, number or broad claim was not
promoted. These are review dispositions, not runtime-test results.

| Body | Extraction / disposition |
| --- | --- |
| [01: cycles](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch01-thinking-in-cycles/draft.md) | Existing model/measurement guidance; retain complete cost boundaries, hold narrative timing shortcuts. |
| [02: screen layout](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch02-screen-as-puzzle/draft.md) | Existing DOWN_HL/layout; upward traversal and narrow specializations are bounded candidates, not imported routines. |
| [03: toolbox](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch03-demoscene-toolbox/draft.md) | Generated structure and RET-threaded work lists; existing stack/SMC/LDI gates retained. |
| [04: maths](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch04-maths/draft.md) | Exact table/product contracts, bounded arithmetic and deterministic procedural state; faulty kernels and PRNG rankings held. |
| [05: 3D](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch05-3d/draft.md) | Affine basis/derivation graphs, wide midpoint sums and projection/clipping obligations; no full rasterizer imported. |
| [06: sphere](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch06-sphere/draft.md) | Compile invariant sampling geometry; separate generation and execution; claimed sampler costs held. |
| [07: rotozoomer](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch07-rotozoomer/draft.md) | Source-value encoding, whole-walk wrap proof and resolution units; whole-screen/bank/timing claims held. |
| [08: multicolor](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch08-multicolor/draft.md) | Existing model-specific raster proof; distinguish display selection from CPU mapping; no guaranteed raster recipe imported. |
| [09: tunnels](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch09-tunnels/draft.md) | Compute symmetry versus full output traffic; pre-rendered scene data with explicit lifetime. |
| [10: scroller](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch10-scroller/draft.md) | Address/bit-position specialization; flicker and stable-color claims require product evidence. |
| [11: sound](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch11-sound/draft.md) | Tick/row separation, shared generators, SFX arbitration and write-event traces. |
| [12: music sync](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch12-music-sync/draft.md) | Queue conservation, actual presentation service and recovery, hybrid PCM scheduling; faulty skeleton held. |
| [13: sizecoding](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch13-sizecoding/draft.md) | Entry-state provenance and whole packed/resident costs; existing dangerous-technique gates; branch/opcode folklore held. |
| [14: compression](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch14-compression/draft.md) | Reversible representation search and decoder identity; fixed ratios/entropy rankings held. |
| [15: machines](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch15-anatomy/draft.md) | Existing target split plus simultaneous visibility and complete paging transactions. |
| [16: sprites](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch16-sprites/draft.md) | Existing compositor/specialization coverage is more precise; correct spill storage and SP byte-order obligations retained. |
| [17: scrolling](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch17-scrolling/draft.md) | Existing incremental redraw; an edge update must accompany a real whole-image shift/redraw/offset mechanism. |
| [18: game loop](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch18-gameloop/draft.md) | Tick domains, bounded pool allocation and safe AI cadence; example entity mistakes held. |
| [19: collisions](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch19-collisions/draft.md) | Signed physics, contact/overflow, leading-edge coverage and anti-tunneling preconditions. |
| [20: demo workflow](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch20-demo-workflow/draft.md) | Generated typed timelines, effect lifecycle and transition resource costs; no new workflow control plane. |
| [21: full game](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch21-full-game/draft.md) | Integration hazards, compatible entity schemas and bank visibility; the stubbed example is not adopted as a finished engine. |
| [22: Agon port](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch22-porting-agon/draft.md) | Width/ABI/protocol transfer boundaries below; concrete MOS/mode/VDP recipes held. |
| [23: AI-assisted work](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch23-ai-assisted/draft.md) | Existing first-divergence/evidence workflow; a generated model is not an independent oracle; no LLM reliability ranking adopted. |
| [A: instruction reference](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-a-z80-reference.md) | Existing CPU manual and model references preferred; broad flag/timing shortcuts are unsafe. |
| [B: sine tables](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-b-sine-tables.md) | Exact quantization, 65-entry endpoint contract and second-difference packing; claimed generator totals held. |
| [C: compression tables](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-c-compression.md) | Primary codec/decoder pairs preferred; no copied decoder or universal ranking. |
| [D: setup](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-d-dev-setup.md) | Build/output/dependency contracts and actual tool versions; unpinned install/emulator comparisons held. |
| [E: eZ80](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-e-ez80-reference.md) | Pointer/count/stack and mixed-mode proof scope; primary MOS/manual required. |
| [F: variants](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-f-z80-variants.md) | Existing explicit CPU/core/model policy; no copied timing/compatibility matrix. |
| [G: AY registers](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-g-ay-registers.md) | Shared state and R13 events; primary GI/Next docs supersede conflicting control tables. |
| [H: storage](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-h-storage-apis.md) | Stateful chunking, cleanup and real short-read/error handling; backend constants/probes held. |
| [I: bytebeat](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-i-bytebeat.md) | Deterministic procedural control/assets, width/rotate equivalence and stable init; subjective musical claims held. |
| [J: modern tools](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-j-modern-tools.md) | Typed exporter contracts and build-generated data; incorrect Rocket/VGM recipes excluded. |
| [K: superoptimizer](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-k-superoptimizer.md) | Answer-space specialization and exact input-state/search boundaries; global optimality and faulty snippets excluded. |
| [L: floating point](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-l-floating-point.md) | No format/library adopted; missing exceptional-value, precision and layout contracts block transfer. |
| [M: BCD](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-m-bcd-arithmetic.md) | Display-oriented representation and DAA flag/carry-chain requirements. |
| [N: LUT generators](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-n-lut-generators.md) | Generator versus exact table versus residual comparison; concrete accuracy/speed claims excluded. |
| [O: meta-analysis](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-o-meta-analysis.md) | Bounded search supplies candidates; it cannot establish an unrestricted ISA theorem. |
| [P: allocation](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-p-register-allocation.md) | Existing heterogeneous register/call-clobber costs; unsupported exhaustive/optimal allocation claims held. |

Historical anecdotes, scene rankings, production estimates, GUI prototypes and
tool catalogs were not adopted as technical proof. The supplied JavaScript
visualizers illustrate mathematical effects; they do not execute the emitted
Z80 code or model its interrupts, paging, contention or analog audio. Release
PDF/EPUB layout, complete translations, external submodule implementations and
every linked third-party project were outside the technical extraction scope.

## Important Exclusions And Counterexamples

The counts below come from source inspection, algebra or isolated host models,
not execution of the assembled examples. They justify excluding the particular
claim; they do not establish the performance of a replacement implementation.

| Printed material | Evidence / consequence |
| --- | --- |
| [ch04 multiply](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch04-maths/draft.md#L20) and [standalone example](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch04-maths/examples/multiply8.a80#L36) | The printed shifting kernel omits the last low-bit transfer and leaves incoming carry undeclared. Its host model fails 64,256 of 65,536 pairs with carry clear. The standalone example models 13×17 as 56,584, rather than 221. Do not import a patched kernel from this review. |
| [ch04 quarter squares](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch04-maths/draft.md#L58) | The exact identity passes all 65,536 byte pairs, but the printed implementation loses the ninth sum-index bit. Direct full-domain 16-bit tables need 511 entries, conventionally 512 with padding, rather than 512 bytes. Approximation is not inherent. |
| [B quarter sine](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-b-sine-tables.md#L82) | Consumer indexes 0–64 while one generated allocation supplies 64 bytes. Quantization/negative-peak conventions differ between the printed table and generator. Copying a golden table into a result is not decoder validation. |
| [K ABS and optimality](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-k-superoptimizer.md#L96) | Modeled 16-bit ABS loses borrow: 32,640 failures in 65,536 inputs. Several rotate idioms need an undeclared incoming carry. Restricted search output does not prove globally shortest or fastest code. |
| [N sqrt generator](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-n-lut-generators.md#L93) | The printed formula's full-byte-domain model has maximum absolute error 222, versus the stated 21. The generated routine, not a claimed search score, must be checked against the declared function. |
| [ch06 sampler](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch06-sphere/draft.md#L81) | Eight displayed 15T sample operations already cost 120T, before output, contradicting the 101T base story. Count actual generated bytes and paths. |
| [ch07 resolution and wrapping](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch07-rotozoomer/draft.md#L142) | Full-screen versus subregion units differ by four in the quoted inner cost. `INC L` never carries into H; masking a row's initial H does not bound the rest of its texture walk. |
| [ch08 raster scheduling](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch08-multicolor/draft.md#L289) | Twelve LDI/PUSH pairs alone take 252 nominal T for 24 bytes, beyond a 224T 48K scanline before other writes/setup. A more capable real engine needs its own schedule and proof. |
| [ch16 preshift storage](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch16-sprites/draft.md) | A tightly stored masked 16×16 sprite at phases 0,2,4,6 needs 352 bytes including shifted spill, rather than 256. Existing local sprite accounting already handles this. |
| [ch17 edge-only scrolling](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch17-scrolling/draft.md) | An isolated distinctive-row oracle disagrees in 30 of 32 bytes: shifting only edge columns does not move the interior image. The HTML visualizer redraws a full shifted image, so it does not validate that ASM recipe. |
| [ch19 midpoint/gravity](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch19-collisions/draft.md) and [ch05 geometry](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch05-3d/draft.md) | Byte ADD/SRA midpoint fails 16,384 of 65,536 signed pairs unless its sum is bounded. The gravity snippet turns `$FC80+$0040=$FCC0` into positive `$0400` through an unsigned terminal-speed clamp. |
| [ch12 queue example](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch12-music-sync/examples/music_sync.a80#L283) | Modeled slot offsets advance by 2,304, rather than 768, exceeding the declared ring. A DI sample loop cannot concurrently run the claimed maskable display ISR; prefilling does not prove recovery. |
| [G AY control table](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-g-ay-registers.md) | The [GI datasheet](https://z00m.speccy.cz/files/ay-3-8910.pdf#page=27) programs port A direction with R7 bit 6 set for output, clear for input, contradicting the table. The [Next manual](https://explorer.specnext.dev/documentation/manual/rev3/chapter/22) also contradicts its chip-count/panning controls. Use the actual backend documentation. |
| [J VGM/Rocket exporters](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-j-modern-tools.md#L445) | Primary readers contradict the saved-format and wait assumptions; use the [VGMtools wait implementation](https://github.com/vgmrips/vgmtools/blob/107f65c97d6aad1f5a839d40b094ea261d7a1b26/vgm_ptch.c#L2269) and [Rocket track reader](https://github.com/rocket/rocket/blob/59be1f138c983a7b88bd94cc049db32431ed1ba2/lib/device.c#L177). Preserve interpolation and duplicate register-write events. |
| [H storage recipes](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/appendices/appendix-h-storage-apis.md#L97) | A TR-DOS example writes destination/length over its filename area. The original [+3 manual](https://worldofspectrum.org/ZXSpectrum128%2B3Manual/chapter8pt27.html) contradicts its +3DOS dispatch description. No backend constants, absence probes or disk driver were imported. |

## Platform Transfer That Remains Useful

Retain the architectural question from ch22/E/F: when changing CPU/platform,
which work moves from direct memory operations to a serialized command queue?
Measure wire bytes, device service/completion and CPU work separately. A baud
rate is not bytes/second without framing, and a faster CPU does not shorten
the physical link's transmission time.

Audit pointer-table scaling, upper pointer/count bytes, stack/return frames,
callbacks, OS entry/return and mixed-mode boundaries. Do not globally turn
every `DW` into `DL`: serialized 16-bit fields may intentionally stay 16-bit.
Preserve persisted formats and use the consumer's firmware headers. Byte-level
game logic may transfer; ULA, AY, MMU, storage and VDP behavior require separate
backends. Note-level music can be a new portable format but does not preserve
every AY envelope/noise/timing effect by replacing OUT alone.

The book's concrete MOS table is not adopted: [primary API constants](https://github.com/AgonPlatform/agon-mos/blob/8336409351ee5314e02801a7b72a4f1bb5282519/src/mos_api.inc#L50)
and [MOS documentation](https://github.com/AgonPlatform/agon-docs/blob/f9806bd3cbff6ed5d1c08bef1d51fed11764b86b/docs/mos/API.md#L545)
identify block read as `$1A`, with C handle, HLU buffer and DEU count/result,
contradicting appendix E's `$0C`. Its proposed `$080000–$0FFFFF` free buffer
also exceeds the preceding stated 512KB map. Mixed-mode suffixes, VDP command
bytes and derivative timing tables remain unverified; no Agon support claim
or recipe is added to this plugin from these examples.

## Companion Tools: Useful Mechanisms, Untrusted Results

| Surface | Useful mechanism | Transfer boundary |
| --- | --- | --- |
| [Listing manager](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/tools/manage_listings.py) | Keep a single executable source and identify the ranges displayed in documentation/translations. Compare generated fragments to it. | Equality only establishes synchronization. Missing, untagged, stale, or incorrect source remains outside that proof. Prefer stable example identities to line numbers that drift. |
| [T-state annotator](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/spectools/cli/tstate.py) and [annotation audit](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/tools/audit_tstates.py) | Detect comments inconsistent with a nominal instruction database; retain taken/fallthrough alternatives. | Summing source lines is not a control-flow, loop-count, contention, wait-state, or interrupt proof. Unknown mnemonics must remain visible. Validate the database and emitted instruction forms independently. |
| [Packer workbench](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/tools/packbench.py) | Compare actual packed sizes, examine transforms and plan transitions alongside memory/CPU budgets. | The profiles mix measured packed input sizes with assumed decoder rates. A successful packer process does not prove that its framing/options match the linked Z80 decoder. Do not reuse its platform constants or timeline estimates as evidence. |
| [Screenshot manifest](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/tools/screenshots.py) | Associate captures with source, model, run parameters and example identity. | The harness preloads attributes and an interrupt stub and sometimes changes registers/IFF. Record those interventions; they cannot prove a real loader initializes the machine. Prefer a semantic ready-state over a fixed frame alone. |
| [Screen viewer](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/spectools/cli/scrview.py) | Inspect bitmap addressing, attributes, FLASH and raw screen dumps outside an emulator. | A decoded static image does not establish raster timing, input, paging, or audio correctness. A stored `.scr` already has legal two-color attributes; it cannot recover conversion losses in the original image. |
| [Image alignment search](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/spectools/cli/autodiver.py) | Search crop, scale and sub-cell alignment before committing an asset to the 8×8 attribute grid; optionally weight important regions. | Its two-most-common-colors score ignores the shared BRIGHT bit. Treat it as a ranking heuristic, then encode/decode legal attributes and inspect the actual artifact. |
| [Sine generator](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/spectools/cli/sinetable.py) and [note generator](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/spectools/cli/notetable.py) | Compare representations/errors and generate tables from declared numeric, tuning and clock parameters. | Test the emitted target routine as well as its host model. Account for endpoints, rounding, representation, actual chip clock and out-of-range periods. Generated tables are not automatically optimal or correct for every target. |
| [Assembler comparison](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/test_mza_compat.sh) | Compare emitted bytes and retain regressions for operand syntax, EQU and label resolution. | Pin origin, output format, header extraction and both tool versions. A shared result is not an independent semantic oracle; skips cannot be passes. The Makefile's test targets do not propagate their failure counters. |
| [Translation-memory design](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/translations/README-tm.md) | Diff stable source blocks against a translation baseline; retranslate changed prose with its old context, while keeping executable fragments canonical. | The documented `translations/tm.py` is absent from this revision. The design is a lead, not an available validated tool. Positional alignment and equal hashes cannot prove semantic translation quality. |

### Specific Tool Results Not To Reuse

`packbench.py` lines 141–168 gives the 128K the 48K frame budget of 69,888 T.
PAL 128K/+2 has 228×311 = **70,908 T/frame**; Next budgets depend on clock and
video configuration. Its own `spectools/cli/tstate.py` has the 70,908 value.
Use [model timing](../../optimize-z80/references/zx-spectrum-models.md), not a
constant copied from a packer comparison.

The timeline at `packbench.py` lines 619–654 multiplies **compressed** bytes by
a profile rate described as decoder T-states per output byte. This mixes units.
Measure the exact decoder or use decoded length for a correctly defined rate;
include setup, interrupts, decoder state and maximum uninterrupted bursts.
Its `bench` mode repeats this unit error in `decomp_frames` at lines 358–360.

The analysis mode's first differences and XOR differences omit their initial
sample; second differences need two reconstruction values for streams of at
least three samples. The helpers pass through inputs shorter than two, so the
two-sample second-difference case retains the first difference instead. Define
the small-input convention, count seeds and the inverse transform. A transpose
only permutes bytes, so its order-zero
histogram entropy cannot fall: `improvement = h_raw - h_transposed` cannot rank
that transform. Measure the actual codec, or explicitly examine a contextual
model or transpose-plus-delta; a low entropy or high curve-fit score alone is
not a lossless size result.

The budget mode adds sizes but does not check address intervals, bank aliases
or lifetimes. `demo/packbench.toml` places both stack and IM2 at `$FE00` and
labels an 8,192-byte ring as eight 768-byte slots (6,144 bytes). Its `screen`
already counts 6,912 bytes, then `attrs` begins at offset 6,912: that additional
region is not the actual screen's 768 attribute bytes. Resolve physical banks,
live intervals and stack growth before trusting a memory plan. Size totals can
neither detect overlap nor prove that independently banked resources coexist.

The alignment heuristic returns zero penalty for an 8×8 cell split between
normal blue and bright red. That exact pair cannot share one classic Spectrum
attribute's BRIGHT bit. A zero score is therefore not proof of a lossless
conversion. A significance mask also needs an unweighted background/error
check so it cannot conceal unacceptable damage elsewhere.

## Observed Verification

Checks ran against the pinned checkout, outside this plugin's primary tree.
These results concern that revision, not a newer upstream version.

| Check | Observed result | Limit |
| --- | --- | --- |
| Explicit assembly of every `chapters/ch*/examples/*.a80`, plus `demo/src/torus.a80` and `demo/src/main.a80`, using SjASMPlus 1.23.1 | **31 passed, 0 failed**: 29 chapter examples and 2 demo entry points. `main.a80` has 4 `fileorg` warnings with raw output. | Syntax/linkage only. Raw ORG gaps do not pad automatically; a raw file is not proof of a valid load image. No full emulator or physical-hardware run was performed. |
| `python3 tools/audit_tstates.py --scan-chapters --summary` | Exit 1: **0 WRONG, 19 UNKNOWN**, 0 PARTIAL. | Unsupported instructions remain unresolved; the scan does not validate whole-routine formulas or behavior. Default mode does not count missing annotations. |
| `python3 tools/manage_listings.py verify --lang all` | Exit 1: **1,143 tagged listings; 1,093 equal, 25 stale, 25 missing**. | Normalized text parity only, not instruction correctness or complete prose coverage. |
| Same listing result by language | EN: 259 equal / 18 stale / 7 missing; ES: 268 / 3 / 6; RU: 290 / 2 / 6; UK: 276 / 2 / 6. | English itself is not a synchronized canonical oracle for all snippets. |
| `make test SJASMPLUS=false` | Prints **0 passed, 31 failed** but returns **exit 0**. | This isolated failure-injection check establishes failure masking in the Makefile, not an assembler defect. |
| `tools/packbench.py budget` and `timeline` with `demo/packbench.toml`, Python 3.12 | Both return exit 0; timeline emits 69,888 T/frame for `spectrum128`. | Success is an estimator result, not a valid target timing or memory placement proof. Python 3.9 without `tomli` rejects these modes; no dependency was installed. |
| Calling the image scorer on a normal-blue / bright-red two-color cell | Penalty **0**, despite incompatible intensity modes. | Isolated scorer check; no full image search or PNG conversion was exercised. |
| Host checks of packbench transforms | **2,080** transpose cases preserve length, histogram and order-zero entropy; seeded delta/XOR round trips pass **128** streams and second-difference round trips pass **127** streams of length 3–129. All 256 attribute bytes exclude the normal-blue / bright-red pair. | Deterministic host checks with wraparound data; no target inverse decoder or codec benchmark. The two-sample second-difference convention was checked separately. |

To reproduce the build, create `build/`, enumerate the chapter examples and
check **each process return code**, using `sjasmplus --nologo --raw=<unique.bin>
<source>`. Assemble the demo entry points with `demo/src` as working directory.
Keep the source checkout disposable because some sources issue `SAVEBIN` or
`SAVESNA`. Do not infer build success from the Makefile's aggregate exit code.

### Plugin Integration Checks

The repository's `.venv/bin/python scripts/validate_skills.py` passes all 11
skills. `scripts/test_workflow_integration.py` passes 21 tests and
`scripts/test_workflow_context_efficiency.py` passes 11. A link/coverage check
validates 116 local links/fragments, 86 pinned upstream paths/line ranges and
the complete 39-body coverage set. Skill frontmatter, invocation YAML, plugin
manifests and routing are unchanged; `git diff --check` passes.

Three disjoint research workers were reused for the three documentation
implementation slices. One fresh independent verifier inspected all changes,
including the seven new references, replayed the three documented math checks
and independently reproduced the multiply/midpoint counterexamples. No blocking
integration finding remained. Worker model/effort was requested as
`gpt-6.1-sol` / `high`; the spawn interface did not return model-identity
confirmation. These process checks do not extend the target-runtime evidence.

## Transfer Policy

Use this source as a discovery catalogue. Reuse the underlying idea only after
stating the actual input domain, live registers/flags, stack/ISR ownership,
physical memory placement, CPU model and cost unit. Prefer a simpler algorithm
or representation before a lower-level instruction substitution.

The useful extraction is progressively loaded through the optimize/shrink
research references. A reviewed formula or host model is still not a local
application benchmark. Runtime-sensitive candidates retain the normal domain
promotion gate and disposable-worktree requirements.
