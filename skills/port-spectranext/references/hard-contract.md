# Hard Contract

Apply this contract to every real `port-spectranext` task.

## Authorities

- The current Spectranext checkout's `AGENTS.md`, `docs/porting.md`, development
  entry point, pipeline code, and manifest validator are authoritative in that
  order of scope. Read `AGENTS.md` and `docs/porting.md` at the start of every
  real task. Within that task, reuse them only after verifying they are
  unchanged; re-read affected authority when canonical state or the blocker
  changes. Never carry cached authority across tasks or into this plugin.
- The consumer checkout owns its manifest, source, build outputs, reports,
  artifacts, branch, worktree, and Git history.
- The Spectranext checkout owns only generic cartridge code and documentation.
  A consumer port may read and execute it but may not store consumer state or
  application-specific fixes there.
- The external `port request` result owns the current state and next command.
  A skill plan, stale report, filename, or prior session never overrides it.

## Mutation Boundary

Declare one effective class before workflow dispatch:

- **primary-tree read-only**: feasibility, explanation, inspection, the request
  gate, and diagnosis without an authorized repair. Do not create intake files,
  change source, or update reports.
- **disposable-worktree-only**: a bounded experiment that the canonical
  consumer candidate must not inherit. It cannot substitute for the manifest's
  declared port worktree or satisfy a pipeline gate.
- **authorized primary-tree mutation**: only when the user requested starting,
  implementing, or continuing the port and the external gate permits the next
  operation. Limit edits to consumer-owned intake files and the declared seam.

The most restrictive user, consumer, Spectranext, and workflow rule wins.
Protected paths win over allowed paths. Never widen an allowlist to make a
failing diff pass. A generic platform repair is never a consumer-seam edit: it
must use the Spectranext checkout, focused platform gates and its own commit.
When the live Spectranext `AGENTS.md` or `docs/porting.md` grants standing
authorization for a bounded, compatible, consumer-agnostic repair, that is the
required authority; do not stop merely to ask the user to repeat it. Stop only
when the live canon classifies the change as requiring an explicit decision.

Branch or worktree creation must match the authorized topology recorded by the
consumer manifest. Do not rewrite history. Commit or push only when required by
the canonical next state and covered by current authorization; otherwise stop
at that boundary and ask for the missing authority.

## Execution and Evidence

- Run the external entry point by absolute path from the consumer repository
  root. Reject execution from the Spectranext checkout or a consumer
  subdirectory.
- Route start, resume, continuation, and pipeline diagnosis through `port
  request` before edits. Run the emitted gate, not a reconstructed equivalent.
- Treat host, unchanged Classic, Spectranext, capability, installer, and
  artifact checks as distinct. One passing target never proves another.
- A passing command without a current report bound to the consumer commit and
  artifact bytes is incomplete evidence.
- Emulator output and host mocks never replace required cartridge evidence.
  Only the user's observed physical result may change a hardware case from
  pending to passing.
- Never weaken a check, edit a digest, bless changed bytes, or mark a physical
  result on inference to advance the state.

## Stop Rules

Stop and report the exact boundary when:

- the Spectranext authority checkout cannot be verified;
- intake lacks a product decision that changes the seam, maintained targets,
  packaging, artifacts, or hardware cases;
- the diff escapes the allowed seam or touches a protected path;
- the canonical command fails, times out, or reports stale/mismatched state;
- source, manifest, report, commit, artifact hash, firmware, or hardware result
  disagree;
- the next step requires physical action, commit, push, or another authority
  not currently granted;
- two repairs or experiments against the same blocker fail without producing a
  new discriminating observation.

Never improvise cartridge cabling, power sequencing, deployment, or firmware
operations. Follow the current external hardware-safety instructions and ask
the user to perform required physical observations.
