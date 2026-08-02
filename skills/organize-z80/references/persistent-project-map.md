# Persistent Project Map

Keep one human-readable organization map as routed project context. Do not
create a parallel source of truth when the project already has one.

## Locate the authority

Inspect project instructions and architecture memory before choosing a path.
Use this order:

1. Extend the existing canonical architecture document or memory entry.
2. With `.mex`, prefer `.mex/context/architecture.md`; create a separate
   context file only when that document cannot remain focused.
3. Otherwise prefer `docs/project-organization.md` when `docs/` is maintained.
4. Otherwise use `PROJECT-ORGANIZATION.md` at the repository root.

Record the selected path in the report. Never create all variants.

## Write gate

Treat persistence as a documentation edit. Require:

- an explicit request to create or update the map;
- an approved path and, if wanted, an approved routing pointer;
- current evidence for every statement promoted to the current or final map;
- preservation of unrelated instructions and project memory.

A map-only write does not authorize source, build, linker, generated-file, or
configuration changes. Keep analysis in the response when the gate is absent.

## Document contract

Keep one Markdown document with these sections, omitting empty detail:

```text
Scope and freshness
- last verified date and revision when available
- targets/toolchains/configurations covered
- evidence used, unknowns, and drift status

Current verified map
- execution flow
- component/responsibility owners
- mutable state and memory/layout owners
- dependency direction
- source-to-section/bank/overlay/generated-input mapping where relevant

Recommended map
- decision state: proposed | accepted | rejected | superseded
- target owners and dependencies
- smallest justified structural delta
- preserved contracts, cost, validation, and rollback

Final verified map
- actual post-change topology and placement
- accepted deviations from the recommendation
- validation evidence and residual unknowns
```

Use tables or compact arrows. For a small change, let the recommended map be a
delta over the current map instead of duplicating unchanged topology.

## Lifecycle

1. In `map`, derive the current map from maintained evidence.
2. In `design`, add a recommended map labelled `proposed`; never overwrite the
   current map with the proposal.
3. After explicit acceptance, mark the recommendation `accepted` and link the
   approved migration slices.
4. After each applied slice, update only affected facts and keep the document
   stale until the relevant checks pass.
5. After validation, write the final map from actual source and artifacts, mark
   it verified, and make it the canonical reference for later sessions.
6. Mark rejected or superseded recommendations; do not silently delete the
   decision history needed to explain the final structure.

On the next change cycle, use the verified final map as the current baseline;
do not accumulate duplicate full snapshots.

## Routing and drift

If the project uses `.mex`, preserve its frontmatter conventions and add the
map to `.mex/ROUTER.md` only with explicit approval. Otherwise add a concise
pointer to an existing root `AGENTS.md` or project router when approved; do not
create a broad instruction scaffold merely to route one file.

At the start of later `organize-z80` work, load the routed map and check its
revision, named paths, targets, owners, and placement facts against the changed
scope. Mark it `STALE` when evidence diverges. Update surgically; do not rewrite
unchanged sections or claim that a date alone proves freshness.
