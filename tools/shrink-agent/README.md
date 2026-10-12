# shrink-agent

Unattended, evidence-gated binary-size reduction for z88dk projects, driven by
the Claude API. It is the applying counterpart of the read-only `shrink-z80`
skill: the skill finds and ranks savings; this tool tries them one routine at a
time and keeps only those that survive the gates.

## How a run works

1. Creates a disposable git worktree of the project on a new branch
   `shrink/auto-<timestamp>`. The primary checkout is never touched.
2. Builds every configured target and records the linked size of each
   (`size_symbol - origin`, from the map).
3. Ranks routines by size from the first target's map (`code_compiler` and
   `code_user`, editable files only).
4. For each routine, up to `--iterations` routines:
   - Claude (`proposer_model`) receives the routine source, its compiled code
     (z88dk-dis, when a target provides `binary`), the project rules and the
     `shrink-z80`/`optimize-z80` reference notes, and returns one exact
     search/replace edit or declines.
   - The edit is applied and **all** targets are rebuilt.
   - Gates, in order: every target builds; total size falls and no target
     grows; configured `tests` pass; an independent review call
     (`reviewer_model`) returns `EQUIVALENT`.
   - Pass: one commit per routine, message records per-target byte deltas and
     `HW PENDING`. Fail: the worktree is reset; the proposer gets the failure
     as feedback for up to `max_rounds` rounds.
5. Removes the worktree. The branch keeps the accepted commits (deleted if
   none). Nothing is pushed or merged.

The reviewer is a filter, not a proof. Every accepted commit is separate, so a
hardware regression can be bisected and reverted commit by commit.

## Setup

- Claim the monthly API credit (claude.ai -> Settings -> Billing -> API
  credits -> Link organization) and create a key in that Console organization.
- Put the key in `~/.z80-skills/.env` (outside any repository):

  ```
  ANTHROPIC_API_KEY=sk-ant-...
  ```

  The tool reads the key only from that file (`--env` to change it), never
  from the environment, so interactive Claude Code keeps using the
  subscription.
- If the key is not scoped to a workspace, the API rejects requests until a
  workspace is named. Add its ID (Console -> Settings -> Workspaces) to the
  same file, or create the key inside a workspace:

  ```
  ANTHROPIC_WORKSPACE_ID=wrkspc_...
  ```
- `python -m pip install anthropic` (Python 3.11+).
- z88dk and the project's own build tools on `PATH`.

## Use

```powershell
$py = "C:/Program Files/Python311/python.exe"
cd C:\dev\z80-skills\tools\shrink-agent

# Baseline sizes and candidate list; no API calls, no branch kept.
& $py shrink_agent.py --config examples/bitstream.toml --dry-run

# Real run: 20 routines, stop before spending $5.
& $py shrink_agent.py --config examples/bitstream.toml --iterations 20 --max-usd 5

# Only some routines.
& $py shrink_agent.py --config examples/bitstream.toml --routine format_size --routine u32_to_dec
```

Each run writes to `~/.z80-skills/shrink-runs/<project>-<timestamp>/`:

- `shrink.log`: one line per routine (outcome, bytes, cost, totals).
- `events.jsonl`: every proposal, review and result in full.

Outcomes: `ACCEPT`, `DECLINE`, `BADEDIT` (edit did not match the source),
`NOBUILD`, `NOGAIN`, `TESTFAIL`, `REVIEW-DIFFERENT`, `REVIEW-UNSURE`, `SKIP`,
`ERROR` (unexpected model or tool failure for that routine; the run continues).

After a run:

```powershell
git -C C:\dev\BitStream log --stat main..shrink/auto-<timestamp>
```

Test the branch on hardware before merging any of it.

### Supervising from Claude Code

Ask Claude Code to launch the run in the background and read `shrink.log`
periodically, not the full output. Suggested stop conditions: the tool already
stops on budget, on `max_consecutive_failures`, or when no candidates remain;
also stop on repeated `NOBUILD` for unrelated reasons (toolchain problem).

## Configuration

See `examples/bitstream.toml`. Key fields:

| Field | Meaning |
|---|---|
| `project.root` | Primary checkout (read-only for the tool). |
| `project.editable` | Globs of files the proposer may edit. Keep timing-critical drivers out. |
| `project.rules`, `project.toolchain` | Project facts given to both models. |
| `project.tests` | Extra commands run after a size gain, before review. `{python}` expands to this interpreter. |
| `[[targets]]` | One per build variant: `build` command, `map`, `size_symbol`, `origin`, optional `binary` for disassembly. The first target's map drives routine ranking. |
| `agent.*_model` | Model IDs. Prices for cost tracking are in `llm.py`; override with a `[prices]` table: `model = [input, output, cache_write, cache_read]` USD per MTok. |
| `agent.max_rounds` | Proposal plus repair rounds per routine. |
| `agent.max_attempts_per_routine` | Times a routine may be revisited in one run. |

## Limits

- Routine boundaries come from the linker map: a routine's size runs to the
  next routine entry, so inline data and local labels count toward it. Map
  location formats were verified on sccz80 builds (BitStream); check
  `--dry-run` output before relying on another toolchain mode.
- Only routines up to 400 source lines are attempted.
- Behavioural equivalence is judged by a model, not proven. Timing, interrupt
  and hardware interaction need hardware tests.
- Builds run sequentially; total time is dominated by the project's build time.

## Tests

```powershell
& $py -m pytest -q tools/shrink-agent
```

The tests use a fake project and a scripted agent: no z88dk and no API calls.
