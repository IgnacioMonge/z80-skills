# Toolchain Layout Contracts

Load this reference only when z88dk, SDCC, assembler/linker selection, CRT or
startup, sections, generated assembly, or banked C/ASM seams affect a proposed
organization. Inspect the project's actual compiler, assembler, linker, and
flags; these are decision prompts, not defaults.

## Contents

1. [Shared boundary record](#shared-boundary-record)
2. [z88dk](#z88dk)
3. [SDCC](#sdcc)
4. [Assemblers](#assemblers)
5. [Artifact chain](#artifact-chain)

## Shared boundary record

For each mixed-language or placement-sensitive boundary, record the selected
toolchain/version, maintained source, generated evidence, and authority for:

- CRT/startup and entry point;
- calling convention, symbol decoration, argument/return ABI, and IX/IY use;
- code, data, BSS, header, and bank/section placement;
- C/ASM shared constants and their generated or maintained source;
- resident banked stub/trampoline and its page-state contract;
- build artifact path and smallest applicable map/listing/symbol check.

Keep compiler-generated ASM as evidence. Maintain it only when the project
explicitly declares it authoritative; otherwise edit C, hand-written ASM,
pragma, build flags, or the generator.

## z88dk

Name the selected frontend/toolchain and CRT authority. At each public seam,
record conventions such as `__z88dk_fastcall` or `__z88dk_callee`, symbol naming,
register use, and any pragma/wrapper that is the source of truth. Keep CRT
selection, `CRT_ORG_CODE`, stack/heap choices, section directives, appmake
packaging, and banked-call support with startup/layout ownership rather than in
feature code. Verify the actual `.map`/listing rather than assuming decoration
or sections from a generic z88dk example.

## SDCC

Record the active ABI variant (including any `__sdcccall` use), underscore
decoration, callee/fastcall wrappers, and whether IY is reserved. Keep
`--code-loc`, `--data-loc`, `--no-std-crt0`, section/area placement, and custom
CRT decisions under build/layout authority. Treat `.rel`, `.ihx`, `.lst`, map,
and conversion/packaging stages as one artifact chain. Put cross-bank wrappers
beside the resident paging contract, not beside arbitrary callers.

## Assemblers

Record assembler-specific `PUBLIC`/`EXTERN`, section/module syntax, local and
numeric label scope, macro/include order, and conditional-assembly authority.
An assembler root composes selected modules; each module exports only its public
contract. Generated includes remain derivative and must identify their source
manifest or generator. Do not move macros, `EQU`/`defc`, or local labels across
files without the scope/symbol checks required by the hard contract.

## Artifact chain

Map the maintained inputs through compile/assemble, link, conversion, loader or
packager to the shipped image. Keep artifact-specific placement facts at the
stage that owns them; do not duplicate them as feature constants. Compare the
relevant map, symbol, listing, section, and final-image evidence after a
structural move; use `audit-z80` for unresolved ABI or toolchain correctness.
