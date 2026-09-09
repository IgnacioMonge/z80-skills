# Z80 Skills — Adaptive Research

**Languages:** English · [Español](README.es.md)

Codex plugin with one standalone adaptive workflow, one thin domain selector,
eight complementary engineering skills, and guarded BridgeZX file delivery for
Z80 projects, especially ZX Spectrum software written in assembly, C, or a
mixture of both using z88dk or SDCC.

The goal is not to produce generic lists of tricks. The skills inspect the
current code and artifacts, adapt depth and parallelism to the actual risk, and
clearly distinguish proven evidence, estimates, and hypotheses.

> Adaptive execution plus specification-driven development, root-cause
> debugging, evidence-first auditing, repository documentation, organization,
> size reduction, and multi-objective optimization for
> Z80 and ZX Spectrum projects.

## Contents

- [What is included](#what-is-included)
- [What it adds beyond generic analysis](#what-it-adds-beyond-generic-analysis)
- [Adaptive and multi-agent execution](#adaptive-and-multi-agent-execution)
- [Targeted external research](#targeted-external-research)
- [Installation](#installation)
- [Usage](#usage)
- [Recommended artifacts](#recommended-artifacts)
- [Safety and limitations](#safety-and-limitations)
- [Repository structure](#repository-structure)
- [Validation](#validation)
- [License](#license)

## What is included

| Skill | Primary question | Result |
|---|---|---|
| [workflow](skills/workflow/SKILL.md) | What is the smallest sufficient execution level for this engineering task? | Direct Light or Medium execution in the main thread, or flat Heavy coordination with bounded built-in workers. |
| [route-z80](skills/route-z80/SKILL.md) | Which single Z80 specialist, if any, owns the requested result? | One domain route, or plain `workflow` for ordinary engineering work. |
| [send-bridgezx](skills/send-bridgezx/SKILL.md) | Which named files or directories should be delivered to a ZX or Next? | A guarded BridgeZX transfer using the explicit or last-known IP, optional destination, and requested sequence. |
| [develop-z80](skills/develop-z80/SKILL.md) | How does this ZX or Next idea become a buildable, verifiable project? | Concept brief, specification, technical plan, task backlog, implementation, and criterion-by-criterion evidence. |
| [document-z80](skills/document-z80/SKILL.md) | How should this repository's public documentation be structured and kept accurate across languages? | An evidence-grounded README and documentation hierarchy with verified commands, hardware requirements, and EN/ES parity. |
| [port-spectranext](skills/port-spectranext/SKILL.md) | How does an existing ZX program move through the Spectranext cartridge's consumer pipeline? | Canonical intake, bounded implementation, artifact-bound gates, physical evidence, and final handoff. |
| [debug-z80](skills/debug-z80/SKILL.md) | What causes this observed failure, and which component owns the repair? | One falsifiable causal explanation and, when requested, one verified root-cause fix. |
| [audit-z80](skills/audit-z80/SKILL.md) | Are there latent defects or broad correctness risks? | Read-only findings prioritized by severity and confidence, with evidence, verification, and residual risk. |
| [organize-z80](skills/organize-z80/SKILL.md) | Which ownership, dependency, source, and runtime-placement boundaries need a change? | Proportional map, design, reversible migration slice, or explicit no-change decision. |
| [shrink-z80](skills/shrink-z80/SKILL.md) | How can storage, linked size, resident memory, BSS/stack, banks, or overlays be reduced? | Net reductions classified by safety and quality of evidence. |
| [optimize-z80](skills/optimize-z80/SKILL.md) | What is the real bottleneck, and which changes offer the best balance among size, speed, RAM, rendering, and latency? | Up to three prioritized experiments with impact, risk, rollback, and validation plans. |

`workflow` is independent of Z80 and routes execution effort. `route-z80` is
the sole implicit entry point for natural-language Z80 domain selection,
including unambiguous specialist matches. The routed skills overlap only where
useful:

- Use `workflow` directly for adaptive planning, implementation, and verification.
- Use `route-z80` to choose one specialist, without loading all candidates.
- Use `send-bridgezx` to deliver named files or directories through the official
  BridgeZX client without maintaining another IP or protocol implementation.
- Use `develop-z80` only for an explicit product initiative or an existing SDD
  dossier, not for routine fixes or isolated repository features.
- Use `document-z80` to create, restructure, review, or synchronize public
  repository documentation without flattening the project's identity.
- Use `port-spectranext` for an existing ZX program's consumer port to the
  Spectranext cartridge, not for ZX Spectrum Next targets or backend work.
- Use `debug-z80` for an observed failure whose causal owner remains unknown.
- Use `audit-z80` for preventive or broad read-only correctness review.
- Use `organize-z80` to map or safely improve ownership, dependencies, source layout, and runtime placement.
- Use `shrink-z80` for an exhaustive search focused exclusively on size.
- Use `optimize-z80` to decide among competing objectives and prioritize the
  next experiments.

## What it adds beyond generic analysis

### Local evidence before folklore

- Only the current code and demonstrably fresh artifacts can confirm a finding
  or improvement.
- Maps, symbols, listings, generated ASM, and linked binaries count as evidence
  only when they correspond to the same revision, configuration, and target.
- Scanners, agents, prior knowledge, forums, and repositories generate
  candidates; they do not replace local verification.
- A stale artifact explicitly lowers confidence to states such as
  `NEEDS BUILD`, `REQUIERE BUILD`, or `SPECULATIVE`.
- In multi-target projects, a proposal passes the promotion gate only when
  every target satisfies its own limits.

### Progressive loading

Each `SKILL.md` acts as a compact dispatcher. Codex first loads the shared
contract and then only the references and scripts relevant to the observed
problem. This avoids adding manuals, techniques, or logs to the context when
they cannot change the result.

### Deterministic tools

The plugin includes dependency-free Python analyzers for profiling the project,
summarizing maps, detecting patterns, inventorying ABI boundaries, assessing
artifact freshness, locating library pulls, and estimating candidates. Their
results are reproducible signals, not automatic verdicts.

## Adaptive and multi-agent execution

The standalone `workflow` skill is the shared execution core:

| Level | Strategy |
|---|---|
| **Light** | The main thread handles a bounded task directly. |
| **Medium** | The main thread handles one ordered multi-step stream directly. |
| **Heavy** | The main thread coordinates bounded independent workers in a flat topology. |

In `auto`, each Z80 skill contributes `Focused`, `Standard`, or `Deep` domain
signals after preflight. Workflow owns the route, dispatch, repair, verification,
and integration; the domain skill keeps its evidence gates, lane definitions,
output contract, and write restrictions. An explicit workflow level wins, but
never grants an operation forbidden by the project or domain skill.
Before dispatch, workflow classifies each surface as primary-tree read-only,
disposable-worktree-only, or authorized primary-tree mutation and selects only
roles that fit that boundary.

## Targeted external research

External research is activated to resolve a specific uncertainty, not to
decorate the report or repeat a list of well-known sites.

### When it is activated

- The user requests deep research across forums, blogs, repositories, or the
  demoscene.
- A compiler version, ABI, firmware, emulator, hardware model, or timing detail
  can change a primary finding.
- The code, generated artifacts, and documentation contradict one another.
- A deep analysis retains a material blind spot.
- An instruction sequence, helper, codec, renderer, loader, or banking scheme
  requires code archaeology.

### How it searches

1. Formulate a question from a minimal local signature: opcode, symbol, emitted
   fragment, version, address, symptom, or constraint.
2. Search for exact fragments and concepts using alternative terminology.
3. Expand terms across English, Spanish, Polish, Russian, Czech, and other
   relevant regional communities.
4. Diversify sources: code, tests, commits, issues, forks, emulators, hardware
   measurements, mailing lists, archived forums, personal blogs, small
   repositories, disassemblies, generators, and demoscene material.
5. Follow authors, citations, forks, related issues, and archived links.
6. Try to refute each finalist by looking for bugs, regressions, closed or
   rejected issues, and model-specific failures.
7. Verify the CPU, Spectrum model, ABI, interrupts, paging, memory, toolchain,
   and timing before transferring a technique.

Research has a budget and stopping rules: it retains only the few sources that
can change a decision. A popular technique without a project-local anchor
remains a hypothesis.

To protect private projects, searches use only minimal normalized signatures;
they must never upload private code or project identifiers.

## Installation

### Requirements

- Codex with plugin and skill support.
- `workflow` Light and Medium run directly; Heavy uses subagents when available.
  Roles and model selection follow the canonical
  [workflow policy](skills/workflow/references/roles.md), which checks runtime
  capabilities and discloses model or effort fallbacks.
- Git to clone and update the repository.
- Python 3.9 or later for general helpers; Python 3.11 or later is required
  whenever `optimize-z80` must parse or enforce a TOML policy.
- z88dk or SDCC only when required by the project or a reproducible measurement.

### Initial installation

Clone the repository anywhere under your home directory. The checkout is the
canonical source for all eleven skills.

```sh
git clone https://github.com/IgnacioMonge/z80-skills.git ~/plugins/z80-skills
cd ~/plugins/z80-skills
python3 scripts/install_personal_marketplace.py
codex plugin add z80-skills@personal
```

`install_personal_marketplace.py` creates or updates
`~/.agents/plugins/marketplace.json`, points `z80-skills` at the actual checkout,
preserves all other entries, and replaces only the entry named `z80-skills`.
Do not maintain authored copies, symlinks, or junctions for any bundled skill
under `~/.agents/skills/<skill-name>` or the legacy
`~/.codex/skills/<skill-name>`.
Those copies can shadow the namespaced plugin and omit package-level files such
as `scripts/run_in_worktree.py`; copying individual directories from `skills/`
is not a complete installation. The plugin already bundles all eleven skills,
including `route-z80` and `workflow`. The installer warns when
it finds one of these duplicate locations; move or disable it before opening a
new Codex task.

Only `route-z80` participates in implicit Z80-domain selection. The nine
routed skills remain available through explicit `$send-bridgezx`, `$develop-z80`,
`$document-z80`, `$port-spectranext`, `$debug-z80`, `$audit-z80`,
`$organize-z80`, `$shrink-z80`, and `$optimize-z80` invocations; after routing,
`route-z80` loads only the selected sibling. Natural-language requests do not
need to be ambiguous to enter the router. This keeps routine repository work on
plain `workflow` and avoids injecting every specialist description.

Open a new Codex task after installing: the skill catalog is loaded when the
task starts and does not update dynamically within an already open task.

### Updating

```sh
cd /path/to/z80-skills
git pull --ff-only
python3 scripts/install_personal_marketplace.py
codex plugin add z80-skills@personal
```

Plugin changes update the committed manifest version so Codex creates a fresh
installed copy. Never edit `~/.codex/plugins/cache` directly. After updating,
open a new task again.

### Grok Build and Claude sync

On Windows, install all eleven skills into Grok Build with the host adaptations
derived from the canonical `workflow` sources:

```powershell
pwsh -File .\scripts\install-for-grok.ps1
```

The installer includes `route-z80`, preserves existing destination skills in a
timestamped backup by default, bundles the disposable-worktree runner, and
patches only the installed copies. Add `-SyncClaude` to also copy the same eleven
canonical skill trees, without Grok adaptations, into `~/.claude/skills`:

```powershell
pwsh -File .\scripts\install-for-grok.ps1 -SyncClaude
```

Use `-SkipBackup` only for disposable test destinations. Open a new Grok or
Claude task after installation so its skill catalog reloads.

## Usage

The skills are invoked through natural language. The more specific the target,
objective, and available artifacts are, the more precise the prioritization
will be.

### Adaptive workflow

```text
Use workflow in auto mode to implement this change with the smallest sufficient
execution level and preserve the repository's existing contracts.
```

### Z80 domain routing

```text
Use route-z80 to choose the single relevant specialist for this Z80 repository
request, or use plain workflow if no specialist evidence contract is needed.
```

### BridgeZX delivery

```text
Use send-bridgezx to send build/game.nex to my Spectrum Next with the last
known BridgeZX IP, under GAMES/DEMO.
```

### Repository documentation

```text
Use document-z80 to restructure this project's README as the landing page,
verify every build and hardware claim, and keep the English and Spanish files
structurally aligned without losing the project's voice.
```

### Specification-driven development

```text
Use develop-z80 to lead this ZX Spectrum Next game idea from concept to verified
implementation. Choose and run the SDD stages for me; ask only when a material
product decision is missing.
```

### Spectranext cartridge porting

```text
Use port-spectranext to resume this existing ZX program's port to the
Spectranext cartridge. Begin with the canonical port request gate, preserve the
consumer seam, and stop for real hardware evidence when required.
```

### Root-cause debugging

```text
Use debug-z80 to isolate why this 128K build crashes after returning from the
ISR. Do not edit until one discriminating check identifies the causal owner;
then apply and verify the minimal fix.
```

### Auditing

```text
Use audit-z80 in auto mode to review this mixed ASM/C project.
Prioritize ABI, ISR, and memory; report only findings anchored in the current code.
```

```text
Use audit-z80 in full mode. Review the differences between the 48K and 128K targets,
including paging, ROM, stack, interrupts, and generated artifacts.
```

### Organization

```text
Use organize-z80 in design mode to map ownership, dependencies, and placement in
this mixed ASM/C project, then propose only the smallest justified boundary change.
```

```text
Use organize-z80 in apply mode to execute this approved phase only; preserve
symbol scopes, maps, ABI, and the existing rollback point.
```

### Size reduction

```text
Use shrink-z80 in scan mode. I need to recover at least 512 bytes of CODE/DATA
without changing behavior, and keep exact savings separate from estimated savings.
```

```text
Use shrink-z80 in compress mode to compare the net size and peak RAM of
the codecs applied to these specific assets.
```

### Multi-objective optimization

```text
Use optimize-z80 in Triage mode to identify the real bottleneck and return
the three experiments with the best balance of impact, risk, and cost.
```

```text
Use optimize-z80 in Measurement mode to obtain a fresh baseline without
modifying my main working tree.
```

## Recommended artifacts

The skills can start with source files alone, but these artifacts increase
confidence:

| Evidence | Usefulness |
|---|---|
| `.asm`, `.s`, `.c`, `.h` | Current semantics, ABI boundaries, patterns, and reachability. |
| `.map`, `.sym` | Layout, symbols, sections, banks, library pulls, and stack gap. |
| `.lst` or generated ASM | Actual compiler behavior and code-generation cost. |
| Binaries, TAP files, and assets | Final size, compression, and reproducible comparisons. |
| Build recipe and flags | Reproducibility, toolchain, ABI, and configuration. |
| Explicit targets and limits | Vetoes, reserves, compatibility, and correct ranking. |

A recent timestamp alone does not prove correspondence. The revision,
configuration, and recipe must belong to the same baseline.

## Safety and limitations

- Normal analyses are read-only.
- `workflow` never widens the permissions granted by a project or domain skill.
- `develop-z80` keeps idea, specification, planning, and task breakdown
  read-only; its first greenfield product-code edit also requires explicit spec
  acceptance. Any multi-milestone auto-advance is bounded to the current session.
- `port-spectranext` keeps the external Spectranext checkout authoritative and
  consumer state isolated; source edits stay inside the authorized consumer
  seam and physical results require explicit user observation.
- `debug-z80` keeps diagnosis and candidate repairs in a disposable worktree;
  it edits the primary tree only for a requested, causally supported repair.
- `document-z80` edits only the public human-facing documentation in scope; it
  does not change code, build configuration, releases, or agent instructions.
- `audit-z80` and `shrink-z80` do not edit the project.
- `organize-z80` edits source only in `apply` mode after an explicit request,
  frozen baseline, approved boundary, one named slice, and rollback point; an
  explicitly requested persistent-map update may edit only that document and
  its routing pointer.
- `optimize-z80` modifies only a disposable copy in `Experiment` mode and
  requires explicit approval.
- The included scripts use the Python standard library, work with local files,
  and do not perform network searches.
- Tests write to temporary directories and remove them when finished.
- The plugin does not include z88dk, SDCC, emulators, or profiling tools.
- It is not a compiler, hardware profiler, or automatic optimizer.
- It does not confirm linked savings, timings, or compatibility without
  appropriate evidence.
- SMC, SP abuse, `DI`/`EI`, undocumented opcodes, floating bus behavior, and
  other hardware-dependent techniques require risk labels and target-specific
  validation.
- External research must never publish private source code, paths, sensitive
  symbols, or project identifiers.

## Repository structure

- `skills/<name>/`: `SKILL.md`, agent metadata, references, and analyzers.
- `scripts/`: installation, worktree runner, and tests.
- `evals/`: routing/evidence cases and fixtures; generated results are ignored.
- `agent_docs/`: maintained project context.

See the [repository map](agent_docs/project_structure.md) for file ownership.

## Validation

Included tests:

```sh
python3 scripts/test_workflow_integration.py
python3 scripts/test_workflow_context_efficiency.py
python3 scripts/test_personal_marketplace.py
python3 scripts/test_run_in_worktree.py
python3 skills/audit-z80/scripts/smoke_test.py
python3 skills/shrink-z80/tests/run_smoke.py
python3 -m unittest discover -s skills/optimize-z80/scripts -p 'test_*.py'
python3 scripts/test_behavior_evals.py
python3 skills/send-bridgezx/scripts/test_bridgezx_transfer.py
```

The plugin manifest and the front matter of each skill should also be validated
before publishing a new version.

Behavior evals are intentionally separate from unit tests. Validate their
datasets without using a model:

```sh
python3 scripts/run_behavior_evals.py --dry-run
```

After installing the same plugin version shown in `.codex-plugin/plugin.json`,
run the labelled routing and evidence suites in fresh, read-only Codex sessions:

```sh
python3 scripts/run_behavior_evals.py --suite evals/routing.jsonl
python3 scripts/run_behavior_evals.py --suite evals/evidence.jsonl
```

The runner refuses a stale installed plugin version unless explicitly
overridden, records per-route precision and recall, and writes ignored JSON
results and per-case runtime traces under `evals/results/`. Use `--model` and
`--reasoning-effort` to make a comparison explicit. Results distinguish requested
settings from runtime-confirmed data, record reported token usage and observed
actions, and compare each fixture's files before and after execution. Unobserved
shell or tool side effects remain unknown; a model's final JSON is not proof
that no writes were attempted. Traces can contain fixture content and local
paths; inspect them before sharing.

Reports fingerprint the authored plugin and evaluation inputs; that fingerprint
does not by itself prove the installed copy matches. Hold cases, fixture inputs,
model, and effort fixed when comparing skill revisions for quality or cost.
`evals/baseline.json` retains historical verified results; it is not
evidence that a later release or expanded suite passed.

## License

This project is licensed under the [MIT License](LICENSE).

Copyright © 2026 M. Ignacio Monge García.

## Author

M. Ignacio Monge García
