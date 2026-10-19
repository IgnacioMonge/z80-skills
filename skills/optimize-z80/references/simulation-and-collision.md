# Simulation And Collision Contracts

Load for measured entity, physics, collision or decision-loop work. Preserve the
game's behavior and data schema; a different update rate or movement precision is
a product change. These are MEDIUM representation/algorithm candidates, not a
complete game engine. Reuse [arithmetic contracts](arithmetic.md),
[loop/layout choices](loops-and-data.md) and [CPU/ISR proof](z80-proof-obligations.md).

## Simulation Ticks, Presentation And Input

Choose a fixed simulation tick and express velocity, acceleration and timers in
those units. Presentation may repeat a completed frame while simulation advances;
AI decisions can have another cadence. Identical per-frame constants at 50Hz and
60Hz do not preserve speed or jump duration. Two sequential HALTs first idle for
two interrupts; they do not grant the following work a two-frame deadline.

Use a tick counter or explicit phases to perform useful work across frames.
Define overrun behavior: bounded catch-up, deliberate slowdown or dropped
presentation. Count worst-case backlog and interrupt work, not average idle time.
Reject an unbounded catch-up loop or a schedule that changes accepted feel;
the existing fixed-step loop is the fallback. Validate long runs and overload
with deterministic input/tick replay, state snapshots and input-latency checks.

Capture input consistently for each tick: held state drives movement, while
pressed edges are current AND NOT previous. Consume one-shot edges once; do not
replay a single press on every catch-up tick or lose it between presentations.
Specify buffering for a press that arrives while rendering. Edge detection is
distinct from menu repeat/debounce; verify press, hold, release and state changes.

## Bounded Entity Pools

A fixed slot array makes allocation time and storage bounded. Size it from the
maximum overlapping lifetimes and emission cadence, including competing effects;
define full-pool behavior explicitly. Reuse inactive slots by initializing every
required field, then publishing ACTIVE last under the existing ownership model.
Activation order alone is not synchronization if an ISR also consumes the pool.

Keep iteration counters independent of stride/pointer registers; pin handler
clobbers. Power-of-two records can simplify indexing but spend padding across all
slots. A larger IX displacement does not itself cost more; choose hot/cold fields
or separate arrays from actual access patterns, preserving IDs and external data.

Count inactive-slot scans, active handler worst paths, initialization and rendering
as well as successful allocation. Reject a pool partition that drops required
actions or layout conversion that costs more than it saves; retain the current
pool/layout. Test full/empty, last-slot allocation, immediate reuse, spawn during
iteration and removal. Prevent one entity from accidentally receiving two updates.

## World, Camera And Fixed-Point Widths

Distinguish world coordinates from camera-relative and screen coordinates.
Unsigned 8.8 position reaches only 255+255/256 pixels; it cannot directly hold a
2,048-pixel world. Use a wider world value or a chunk/tile coordinate with bounded
local position, then narrow after culling. Count conversion, storage and register
pressure; retain the existing width unless all intermediate ranges are proved.

Signed velocity, unsigned position and signed screen-relative differences need
different comparisons. Preserve carry from fractional ADD to integer ADC; widen
products and endpoint sums before narrowing. A terminal-fall clamp must accept
negative upward velocity and clamp only values above the signed upper bound.
Snapping position also needs an explicit fractional-byte policy.

Arithmetic shift halves negative values toward minus infinity: raw fixed-point
-1 stays -1 forever. Friction that must stop needs a specified deadband/zero snap
or division rounding toward zero. Count the correction and preserve accepted
motion; do not replace existing damping with an approximate shift automatically.
Validate negative/positive extrema, fractional carries, jump apex, terminal speed,
long-run drift and stopping against an independent integer model. Keep the tested
arithmetic path if range, rounding or visible error cannot be bounded.

## Half-Open AABB Tests

For positive dimensions define boxes as `[x,x+w) x [y,y+h)`; touching edges do not
overlap. Reject a pair on any separating axis. Order rejection tests from measured
scene distributions; a preliminary distance test may duplicate existing work and
slow close pairs. Count complete calls and candidate-pair enumeration before
optimizing field loads. Spatial bins help only when their maintenance amortizes.

Widen endpoints or prove each sum fits: x+w=256 already overflows an 8-bit sum,
although the last covered pixel is 255. Define zero-size, inactive and out-of-world
behavior explicitly. Do not reinterpret unsigned screen differences as signed
distances without a range proof. Test symmetry, identical/contained boxes, edge
and corner contact, one-pixel overlap, overflow and offscreen positions.
Reject approximate broadphase results as final collisions; the existing AABB
or a wider reference comparison remains the fallback.

## Tile Coverage And Axis-Separated Response

Use a collision-property tilemap to replace many world-box comparisons with
bounded lookups. Move along one axis, test its prospective leading edge against
the accepted position on the other axis, resolve, then move/test the other axis.
Keep axis order consistent with the game's behavior; it affects corner sliding.

Check every tile row/column crossed by a long leading edge and every traversed
cell required by the movement bound. Two corners or a fixed midpoint can miss a
solid tile between them. Define outside-map behavior and coordinate-to-tile
rounding. Resolve using movement direction/previous position so touching a wall
does not push an entity moving away. On snap, update fraction and velocity
consistently; clear grounded state when leaving support.

One-way platforms require downward crossing of their top from an allowed prior
position, plus a drop-through policy. A half-tile speed cap is not a universal
anti-tunneling guarantee: obstacle thickness, body extent, sampled coverage and
moving targets matter. Fast bullets may need swept segment/box tests or substeps;
their added work must fit the worst scene. A broadphase cannot replace these tests.

Count map lookup, crossed-cell count and response, including the maximum travel
path. Reject a reduced sampling scheme without spatial coverage proof. Keep the
current collision solver or use bounded substeps as fallback. Validate diagonal
sliding, narrow obstacles, wide bodies, ceilings, map edges, leaving ledges,
one-way landing/drop-through and fast crossings with fixed-point boundary inputs.

## Safe AI Cadence

Separate decisions from movement: keep physics/input at their specified cadence,
retain velocity between AI decisions and stagger entity decision phases to avoid
a shared expensive frame. State transitions, cooldowns and line-of-sight caches
need declared tick units and invalidation. Counter wrap must not starve a phase.

Measure decision cost, dispatch/scheduler overhead and worst reaction delay;
slower decisions are not automatically imperceptible. Reject when an attack,
hazard or product criterion requires same-tick response. Per-tick decisions remain
the fallback. Replay combat/threshold/counter-wrap cases, check phase fairness and
measure the busiest frame, not only average work.

## Evidence And Sources

Host properties establish their model's arithmetic and spatial rules. Assembled
helpers still need register/flag/stack checks and actual call timing; game feel
needs a [product runtime check](../../develop-z80/references/verification.md#evidence-layers).
This reference supplies no full rasterizer, pathfinder or Next DMA recipe.

Discovery sources: [entity pools/input/ticks](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch18-gameloop/draft.md#L353-L765)
and [collision/physics/AI](https://github.com/oisee/antique-toy/blob/7313ecfaab710d1a105b7bff3be19aaf04dc5935/chapters/ch19-collisions/draft.md#L13-L956).
Their implementations and timings are not adopted; see the
[source assessment](../../audit-z80/references/antique-toy-review.md).
