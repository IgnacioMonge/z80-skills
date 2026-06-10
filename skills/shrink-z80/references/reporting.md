# Reporting

Reports should read like an optimization backlog, not a stream of consciousness.

## Each finding should state

```text
[CATEGORY] ID - short title
Safety: SAFE | AGGRESSIVE | EXPERIMENTAL
Certainty: EXACTO | ESTIMADO | REQUIERE BUILD
File: path:line
Current pattern: what exists now
Proposal: concrete replacement
Savings: CODE and BSS impact
Cost: stack, complexity, and testing notes
Dependency: none or what must land first
Rejected alternative: optional, but required for black-belt candidates that looked tempting and failed proof
```

## Ordering

- order quick wins by savings first
- keep `SAFE` wins ahead of riskier ideas when savings are similar
- group detailed findings by category after the quick-win list

## Scan coverage

A real `scan` must mention:

- `arch`
- `libpull`
- `deadcode` or `refactor`
- `data`
- `micro`
- `dedup`
- black-belt candidates and rejected ideas

If one category yields nothing useful, say `none found` and cite the evidence used.
