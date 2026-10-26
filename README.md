# Z80 Skills

**Languages:** English · [Español](README.es.md)

Agent skills for Z80 projects, especially ZX Spectrum and ZX Spectrum Next
software written in assembly, C, or both with z88dk or SDCC. They work with
Codex, Claude Code, and Grok Build from one checkout; Gemini / Antigravity
support is partial.

The bundle has eleven skills: a portable adaptive `workflow`, a thin Z80
router, eight engineering specialists, and guarded BridgeZX file delivery. It
also includes an optional unattended size-reduction tool,
[`shrink-agent`](tools/shrink-agent/README.md).

The skills do not produce generic lists of tricks. They inspect the current
code and build artifacts, scale depth and parallelism to the actual risk, and
keep proven evidence, estimates, and hypotheses apart.

## Contents

- [Supported hosts](#supported-hosts)
- [Quick start](#quick-start)
- [Installation](#installation)
- [Which skill do I need?](#which-skill-do-i-need)
- [Usage](#usage)
- [How it works](#how-it-works)
- [Optional: shrink-agent](#optional-shrink-agent)
- [Recommended artifacts](#recommended-artifacts)
- [Safety and limitations](#safety-and-limitations)
- [Repository structure](#repository-structure)
- [Development and validation](#development-and-validation)
- [License](#license)

## Supported hosts

Every host reads the same canonical `skills/` trees. Nothing is copied, so a
`git pull` updates all of them.

| Host | Installation | Explicit invocation | Implicit entry points | Status |
|---|---|---|---|---|
| Codex | Personal marketplace plugin | `$route-z80`, `$debug-z80`, … | `route-z80`, `workflow` | Full; behavior evals run here |
| Claude Code | Junctions (Windows) or symlinks (macOS, Linux) | `/route-z80`, `/debug-z80`, … | `route-z80`, `workflow` | Full |
| Grok Build | `[skills].paths` in `~/.grok/config.toml` | Through Grok's skill catalog | Follows Grok's catalog; the Codex and Claude Code restriction fields may not apply | Full skill loading |
| Gemini / Antigravity | No installer in this repository | — | — | Partial: manifest and delegation mapping only |

In every host you can also describe the task in natural language; `route-z80`
picks the specialist. Heavy multi-agent delegation adapts to each host's
subagent primitive and model names (see [Adaptive and multi-agent
execution](#adaptive-and-multi-agent-execution)).

## Quick start

1. Clone the repository once, anywhere under your home directory:

   ```sh
   git clone https://github.com/IgnacioMonge/z80-skills.git ~/plugins/z80-skills
   cd ~/plugins/z80-skills
   ```

2. Register it with your host (details in [Installation](#installation)):

   | Host | Command |
   |---|---|
   | Codex | `python3 scripts/install_personal_marketplace.py` then `codex plugin add z80-skills@personal` |
   | Claude Code, Windows | `pwsh -File .\scripts\install-for-claude.ps1` |
   | Claude Code, macOS or Linux | `sh scripts/install-for-claude.sh` |
   | Grok Build | `pwsh -File .\scripts\install-for-grok.ps1` |

3. Open a **new** task or session. Skill catalogs load at start and do not
   refresh inside a task that is already open.

4. Try a request inside a Z80 project:

   ```text
   Use route-z80 to choose the right specialist for this request: the 128K
   build crashes after returning from the ISR.
   ```

## Installation

### Requirements

- One supported host: Codex with plugin support, Claude Code, or Grok Build.
- Git, to clone and update the repository.
- Python 3.9 or later for the bundled helpers. `optimize-z80` needs Python 3.11
  or later to parse a TOML project policy; BridgeZX delivery needs 3.10 or later;
  `shrink-agent` needs 3.11 or later. On Windows, use `python` or `py` where the
  examples say `python3`.
- PowerShell (`pwsh`) for the Windows Claude Code installer and the Grok Build
  installer.
- z88dk or SDCC only when the project or a reproducible measurement needs them.
  This repository includes no compilers, emulators, or profilers.

### Codex

```sh
cd ~/plugins/z80-skills
python3 scripts/install_personal_marketplace.py
codex plugin add z80-skills@personal
```

`install_personal_marketplace.py` creates or updates
`~/.agents/plugins/marketplace.json`, points the `z80-skills` entry at this
checkout, and keeps all other entries. Codex then installs the plugin with all
eleven skills.

Only `route-z80` and `workflow` are invoked implicitly. The nine specialists
stay available as `$send-bridgezx`, `$develop-z80`, `$document-z80`,
`$port-spectranext`, `$debug-z80`, `$audit-z80`, `$organize-z80`,
`$shrink-z80`, and `$optimize-z80`. After routing, `route-z80` loads only the
selected specialist, so routine work stays on plain `workflow` and the context
is not filled with every specialist description.

Do not keep copies, symlinks, or junctions of bundled skills under
`~/.agents/skills/<name>` or the legacy `~/.codex/skills/<name>`. They shadow
the plugin and miss package-level files such as `scripts/run_in_worktree.py`.
The installer warns when it finds one; move or disable it before opening a new
task. Never edit `~/.codex/plugins/cache` directly.

### Claude Code

```powershell
pwsh -File .\scripts\install-for-claude.ps1
```

```sh
sh scripts/install-for-claude.sh
```

The installer links `~/.claude/skills/<name>` to `skills/<name>` for the eleven
skills. It also links `~/.claude/scripts` and `~/.claude/tools` to this
repository's `scripts/` and `tools/`, so the skills' `../../scripts/...` and
`../../tools/...` references resolve. Both installers are idempotent. They
replace stale links, and they report but never delete real directories in the
way.

Only `route-z80` and `workflow` are invoked implicitly. The nine specialists set
`disable-model-invocation: true` and stay available as `/develop-z80`,
`/optimize-z80`, and so on.

### Grok Build

```powershell
pwsh -File .\scripts\install-for-grok.ps1
```

The installer adds `<repo>/skills` to `[skills].paths` in
`~/.grok/config.toml`, so Grok Build reads the trees in place. It also deletes
obsolete copies of the eleven bundled skills from `~/.grok/skills` and
`~/.claude/skills`, and leaves unrelated personal skills untouched.

If you also use Claude Code, run the Grok installer with `-SkipClaudeCleanup`.
Otherwise it removes the Claude Code links as obsolete copies.

### Gemini / Antigravity

The repository includes `gemini-extension.json`, and `workflow` maps its
delegation roles to `invoke_subagent` on runtimes that expose it (see
[roles](skills/workflow/references/roles.md#other-hosts-gemini--antigravity)).
There is no installer or tested setup for these hosts yet.

### Updating

```sh
cd ~/plugins/z80-skills
git pull --ff-only
```

Claude Code and Grok Build read the updated trees directly. Codex installs a
versioned copy, so rerun the marketplace installer and
`codex plugin add z80-skills@personal`. Plugin changes raise the manifest
version so Codex creates a fresh copy. Then open a new task or session in every
host.

## Which skill do I need?

| Skill | Use it when | You get |
|---|---|---|
| [workflow](skills/workflow/SKILL.md) | Any engineering task, Z80 or not, where effort and delegation should match the risk. | Direct Light or Medium execution, or flat Heavy coordination with bounded workers. |
| [route-z80](skills/route-z80/SKILL.md) | Any natural-language Z80 request, even when the specialist seems obvious; skip it only when you name the specialist directly. | One specialist, or plain `workflow` for ordinary work. |
| [send-bridgezx](skills/send-bridgezx/SKILL.md) | Named files or directories should go to a ZX or Next over BridgeZX. | A guarded transfer using the explicit or last-known IP, optional destination, and requested order. |
| [develop-z80](skills/develop-z80/SKILL.md) | An explicit product initiative or an existing SDD dossier, not routine fixes. | Concept brief, specification, plan, backlog, implementation, and evidence per acceptance criterion. |
| [document-z80](skills/document-z80/SKILL.md) | A project's public documentation needs creating, restructuring, review, or EN/ES sync. | An evidence-grounded README and documentation hierarchy with verified commands and hardware claims. |
| [port-spectranext](skills/port-spectranext/SKILL.md) | An existing ZX program is being ported to the Spectranext cartridge (not the Spectrum Next). | Canonical intake, bounded implementation, artifact-bound gates, physical evidence, and handoff. |
| [debug-z80](skills/debug-z80/SKILL.md) | You observe a failure and its cause is unknown. | One falsifiable causal explanation and, on request, one verified root-cause fix. |
| [audit-z80](skills/audit-z80/SKILL.md) | You want a preventive or broad correctness review, or the risk of a change set (`diff` mode). | Read-only findings ranked by severity and confidence, with evidence and residual risk. |
| [organize-z80](skills/organize-z80/SKILL.md) | Ownership, dependencies, source layout, or runtime placement need mapping or a safe change. | A proportional map, design, reversible migration slice, or an explicit no-change decision. |
| [shrink-z80](skills/shrink-z80/SKILL.md) | Storage, linked size, resident memory, BSS/stack, banks, or overlays must shrink. | Net reductions classified by safety and quality of evidence. |
| [optimize-z80](skills/optimize-z80/SKILL.md) | Several objectives compete: size, speed, RAM, rendering, latency. | Up to three prioritized experiments with impact, risk, rollback, and validation. |

## Usage

Describe the target, the objective, and the artifacts you have; the more
specific the request, the better the prioritization. The examples name the
skill in prose. In Codex you can prefix it with `$`, and in Claude Code invoke
it as `/name`.

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
Use audit-z80 in diff mode against main. Check whether this branch's ISR and
C/ASM changes break the ABI, preserved registers, shared state, or the memory map.
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

## How it works

### Local evidence before folklore

- Only the current code and demonstrably fresh artifacts can confirm a finding
  or an improvement.
- Maps, symbols, listings, generated ASM, and linked binaries count as evidence
  only when they match the same revision, configuration, and target.
- Scanners, agents, prior knowledge, forums, and other repositories generate
  candidates; they do not replace local verification.
- A stale artifact lowers confidence explicitly, to states such as
  `NEEDS BUILD`, `REQUIERE BUILD`, or `SPECULATIVE`.
- In multi-target projects, a proposal is promoted only when every target meets
  its own limits.

### Progressive loading

Each `SKILL.md` is a compact dispatcher. The host first loads the shared
contract, then only the references and scripts relevant to the observed
problem. Manuals, technique catalogs, and logs stay out of the context unless
they can change the result.

### Deterministic tools

The skills ship Python analyzers, mostly standard-library only. They profile
the project, summarize maps, detect patterns, inventory ABI boundaries, check
artifact freshness, locate library pulls, estimate T-states, and score
candidates. Their output is a reproducible signal, not an automatic verdict.

### Adaptive and multi-agent execution

The standalone `workflow` skill is the shared execution core:

| Level | Strategy |
|---|---|
| **Light** | The main thread handles a bounded task directly. |
| **Medium** | The main thread handles one ordered multi-step stream directly. |
| **Heavy** | The main thread coordinates bounded independent workers in a flat topology. |

In `auto`, each Z80 skill classifies demand as `Focused`, `Standard`, or `Deep`
after preflight. Workflow owns the route, dispatch, repair, verification, and
integration. The domain skill keeps its evidence gates, lanes, output contract,
and write restrictions. An explicit workflow level wins, but never grants an
operation the project or domain skill forbids. Before dispatch, workflow
classifies each surface as primary-tree read-only, disposable-worktree-only, or
authorized primary-tree mutation, and selects only roles that fit.

Explicit user instructions override skill defaults within their scope;
project constraints, evidence requirements, and runtime limits stay in force.
When a skill stops, it names the exact rule, following the shared
[authorization policy](skills/workflow/references/authorization.md).

Heavy delegation maps the same roles (investigator, implementer, verifier) to
each host. The canonical [roles policy](skills/workflow/references/roles.md)
holds the per-host mapping:

- **Codex:** subagents default to Sol 6.1 with per-assignment reasoning effort.
  Astra Medium is used only on an explicit user request for a named difficult
  causal or high-risk analysis
  ([opt-in rules](skills/workflow/references/roles.md#explicit-astra-medium-opt-in)).
- **Claude Code:** the `Agent` tool with `Explore` or `general-purpose`
  subagents and an explicit `opus` or `sonnet` model; the host exposes no
  reasoning-effort parameter.
- **Gemini / Antigravity:** `invoke_subagent` with `research` or `self` types
  and the inherited model tier.

The host must support and enforce the requested settings; a skill is not a
runtime spending control.

### Targeted external research

External research resolves a specific uncertainty; it does not decorate the
report or repeat a list of well-known sites.

It is activated when:

- The user asks for deep research across forums, blogs, repositories, or the
  demoscene.
- A compiler version, ABI, firmware, emulator, hardware model, or timing detail
  can change a primary finding.
- The code, generated artifacts, and documentation contradict one another.
- A deep analysis keeps a material blind spot.
- An instruction sequence, helper, codec, renderer, loader, or banking scheme
  needs code archaeology.

How it searches:

1. Formulate a question from a minimal local signature: opcode, symbol, emitted
   fragment, version, address, symptom, or constraint.
2. Search for exact fragments and concepts with alternative terminology.
3. Expand terms across English, Spanish, Polish, Russian, Czech, and other
   relevant regional communities.
4. Diversify sources: code, tests, commits, issues, forks, emulators, hardware
   measurements, mailing lists, archived forums, personal blogs, small
   repositories, disassemblies, generators, and demoscene material.
5. Follow authors, citations, forks, related issues, and archived links.
6. Try to refute each finalist: look for bugs, regressions, closed or rejected
   issues, and model-specific failures.
7. Check the CPU, Spectrum model, ABI, interrupts, paging, memory, toolchain,
   and timing before transferring a technique.

Research has a budget and stopping rules and keeps only the few sources that
can change a decision. A popular technique without a local anchor remains a
hypothesis. Searches use only minimal normalized signatures and never upload
private code or project identifiers.

## Optional: shrink-agent

[`tools/shrink-agent`](tools/shrink-agent/README.md) is the applying
counterpart of the read-only `shrink-z80`. It is an unattended loop for z88dk
projects. It proposes one size reduction per routine through the Claude API,
rebuilds every target, and keeps a change only when all targets build, total
size falls, the configured tests pass, and an independent model review accepts
it. It works in a disposable worktree branch, makes one commit per routine,
and never merges or pushes.

It needs Python 3.11 or later, its own virtual environment
(`tools/shrink-agent/install.py`), and an Anthropic API key. Runs cost money and
are capped by `--max-usd`, 2 USD by default. In Claude Code, `/shrink-z80 agent`
runs the census first and asks before launching it. Its README has the
configuration, outcomes, and limits.

## Recommended artifacts

The skills can start from source files alone; these artifacts raise confidence:

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
  consumer state isolated. Source edits stay inside the authorized consumer
  seam, and physical results require explicit user observation.
- `debug-z80` keeps diagnosis and candidate repairs in a disposable worktree.
  It edits the primary tree only for a requested, causally supported repair.
- `document-z80` edits only the public human-facing documentation in scope. It
  does not change code, build configuration, releases, or agent instructions.
- `audit-z80` and `shrink-z80` do not edit the project. `shrink-agent` commits
  only to its own disposable branch.
- `organize-z80` edits source only in `apply` mode, after an explicit request,
  a frozen baseline, an approved boundary, one named slice, and a rollback
  point. An explicitly requested persistent-map update may edit only that
  document and its routing pointer.
- `optimize-z80` modifies only a disposable copy in `Experiment` mode and
  requires explicit approval.
- `send-bridgezx` sends only the named sources to the selected machine and never
  retries an uncertain transfer.
- The bundled analyzers work on local files and perform no network access.
  Tests write to temporary directories and remove them when finished.
- This is not a compiler, hardware profiler, or automatic optimizer. It does not
  confirm linked savings, timings, or compatibility without appropriate
  evidence.
- SMC, SP abuse, `DI`/`EI`, undocumented opcodes, floating bus behavior, and
  other hardware-dependent techniques require risk labels and target-specific
  validation.
- External research must never publish private source code, paths, sensitive
  symbols, or project identifiers.

## Repository structure

- `skills/<name>/`: `SKILL.md`, agent metadata, references, and analyzers.
- `scripts/`: host installers, the disposable-worktree runner, the skill
  validator, and repository tests.
- `tools/shrink-agent/`: the optional unattended size-reduction tool.
- `evals/`: routing, evidence, and policy cases with fixtures; generated
  results are ignored.
- `agent_docs/`: maintained project context for agents.
- `.codex-plugin/plugin.json`, `plugin.json`, `gemini-extension.json`: host
  manifests with one shared version.

See the [repository map](agent_docs/project_structure.md) for file ownership
and [CHANGELOG.md](CHANGELOG.md) for changes.

## Development and validation

Set up the validator and test dependencies in a virtual environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r scripts/requirements-validation.txt pytest
```

In Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` and use
`python` instead of `python3`.

Validate the skills and run the test suite from the repository root:

```sh
python3 scripts/validate_skills.py
python3 -m pytest -q
python3 skills/audit-z80/scripts/smoke_test.py
python3 skills/shrink-z80/tests/run_smoke.py
```

`validate_skills.py` checks all eleven skills, or one when you pass its folder,
without rewriting `SKILL.md` or `agents/openai.yaml`. It does not establish
runtime behavior or activation. `pytest` collects the `scripts/`,
`optimize-z80`, `send-bridgezx`, and `shrink-agent` tests. The two smoke
scripts run separately. Validate the manifests and each skill's front matter
before publishing a new version.

### Behavior evals (Codex only)

Behavior evals are separate from the unit tests. They drive the Codex CLI.
Check the datasets without a model:

```sh
python3 scripts/run_behavior_evals.py --dry-run
```

After installing the plugin version shown in `.codex-plugin/plugin.json`, run
the routing and evidence suites in fresh, read-only Codex sessions:

```sh
python3 scripts/run_behavior_evals.py --suite evals/routing.jsonl
python3 scripts/run_behavior_evals.py --suite evals/evidence.jsonl
```

The runner refuses a stale installed plugin unless overridden. It records
per-route precision and recall and writes ignored JSON results and per-case
traces under `evals/results/`. Use `--model` and `--reasoning-effort` to make a
comparison explicit, and keep cases, fixtures, model, and effort fixed when you
compare skill revisions. Results separate requested settings from
runtime-confirmed data, record token usage and observed actions, and compare
fixture files before and after each case. Unobserved side effects remain
unknown, and traces can contain fixture content and local paths, so inspect
them before sharing. `evals/baseline.json` keeps historical results only; it
does not prove a later release passes.

The optional `evals/policy.jsonl` suite checks decisions about model opt-ins,
authorization, selective reads, and reuse. Its scenarios ask only for
decisions, with no delegated calls, builds, edits, or transfers. A live run uses
paid inference and tests policy interpretation, not runtime enforcement. See
[policy evaluation](evals/POLICY.md). Check its dataset locally with:

```sh
python3 scripts/run_behavior_evals.py --suite evals/policy.jsonl --dry-run
```

## License

This project is licensed under the [MIT License](LICENSE).

Copyright © 2026 M. Ignacio Monge García.

## Author

M. Ignacio Monge García
