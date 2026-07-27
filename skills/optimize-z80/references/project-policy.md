# Project Policy

A project policy is optional, but when present it overrides guesses from filenames or model prior knowledge.

Look for `z80opt.toml` or `.z80opt.toml` at the project root during preflight.

## Schema

```toml
target = "unknown"        # unknown | pure-z80 | zx-spectrum | msx | cpc | cpm | rc2014 | next
profile = "auto"          # auto | 48k-game | 128k-game | network-app | text-ui-tool | graphics-heavy | demoscene-intro | c-heavy-z88dk-sdcc | asm-heavy | mixed-c-asm-overlays
priority = ["size"]       # size | speed | resident-size | ram | latency | ux | maintainability | load-time

[forbidden]
undocumented = false
smc = false
sp_abuse = false
interrupt_windows = false
hardware_timing = false
banking_changes = false

[constraints]
cpu_floor = "unknown"     # unknown | nmos-z80 | cmos-z80 | z180 | ez80
overlay_size = 0           # bytes; 0 means unknown/not fixed
maintainability = "normal" # normal | release | sizecoding | disposable
abi_check = false
size_check = false
module_guards = false

[build]
command = ""              # optional; preflight reports it, never runs it
```

## Rules

- Policy beats auto-detection.
- `forbidden.* = true` means reject, not demote.
- `target = "unknown"` or `target = "pure-z80"` disables Spectrum-only assumptions unless source/artifacts prove Spectrum.
- `maintainability = "release"` rejects undocumented opcodes, opcode SMC, SP abuse, and long DI windows unless explicitly allowed.
- `maintainability = "sizecoding"` allows dangerous lanes only with a validation path.
- `overlay_size > 0` makes overlay occupancy and slot boundaries first-class metrics; candidates with `overlay_after > overlay_size` are rejected, and overlay/banking candidates without `overlay_after` are downgraded to SPECULATIVE.
- `abi_check`, `size_check`, or `module_guards` are validation hooks, not proof by themselves.
- `[build].command` is a hint for measurement setup; preflight reports it but does not execute it.

## Per-Target Gates Extension

Multi-target projects may add `[targets.<name>]` tables. The scorer does not
read them yet; they are prose-enforced via the multi-target acceptance rule in
`SKILL.md` and give it authoritative numbers:

```toml
[targets.zx]
artifact = "build/GAME.map"
resident_ceiling = 34363   # CODE+DATA upper bound
stack_gap_floor = 1935     # SP gap lower bound
```

A candidate passes only when EVERY declared target meets both figures in its
own fresh artifact from the same frozen source revision and configuration
baseline. The main agent enforces this gate; the scorer only ranks survivors.

## Candidate Schema Vocabulary (avoid the three collisions)

- Policy `profile` (project shape: `mixed-c-asm-overlays`, `48k-game`, ...) is
  NOT the scorer `--profile` (weight set: `size`, `speed`, `network-app`,
  `graphics-render`, `balanced`). Map project profile to the dominant weight
  set when invoking the scorer.
- Candidate `confidence` for the scorer is `PROVEN` / `LIKELY` / `SPECULATIVE`
  (uppercase). The evidence-model words (`none/weak/good/strong`) describe
  static/dynamic evidence in prose, not this field.
- The scorer accepts prose evidence for `LIKELY`, but `PROVEN` needs a current
  evidence card with `kind`, `ref`, and `current = true`; scorer output never
  replaces the caller's multi-target gate.
- Candidate `validation` for the scorer is an integer 0..5 (ease of
  validation), not the textual validation plan; keep the plan in a separate
  prose field.

## Prompt Fallback

If no policy file exists, ask only for constraints that can change recommendations:

- target hardware/platform
- forbidden lanes
- dominant priority
- fixed overlay/bank limits
- release vs sizecoding tolerance

Do not block triage if the user does not answer. Mark missing policy as `policy_status = inferred`.
