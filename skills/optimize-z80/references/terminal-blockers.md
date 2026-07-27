# Terminal Blockers And Self-Tuning

The analysis process must be optimized too.

## Command Rules

- Every command gets a timeout.
- First failure records a trap.
- Second attempt must change method.
- Never repeat a blocked command unchanged.
- Prefer existing artifacts over rebuilding.
- Do not launch a new build while old build processes are alive.
- Use narrow commands over broad ones.

## Hard Stops For Proven Claims

Do not claim PROVEN deltas if any is true:

- no reproducible build recipe
- stale artifacts and no measurement build
- no map/listing/symbol artifact for linked binary analysis
- binary and symbols do not match by timestamp/config
- different CRT/clib/compiler/flags between before and after
- unknown bank/section placement for banking/layout claim
- no timing mechanism for speed claim, not even static T-state or FRAMES proxy

## Common Traps

- `git log --all` can fail on broken tool refs. Use branch-local logs or explicit refs.
- Shell wrappers can break path translation. Use absolute executables if needed.
- Builds can outlive tool timeout. Check processes and artifacts before retry.
- Huge logs can flood context. Summarize with search/scripts.
- Missing `.lst/.sym` is not fatal, but it caps confidence.
- `--c-code-in-asm` and SDCC dumps are analysis configs, not release-equivalent configs.
- Use an available read-only web/search tool when `external-research.md`
  triggers. Package installs or executing downloaded code remain out of scope
  without approval.

## Self-Tuning Output

When the process fails or wastes time, emit:

```text
Process trap detected:
- command:
- failure:
- workaround used:

Skill weakness detected:
- weakness:
- proposed SKILL.md/reference/script change:
- apply only with approval:
```

Do not autoedit the skill unless the user asks.
