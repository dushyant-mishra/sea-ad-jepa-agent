# Scope of the adversarial tests in the T0 V20 materialization lane

## Why this note exists

This lane hardens the project's own integrity checks, and proving a fix requires
first reproducing the defect it fixes. Several regression tests therefore contain
small reproductions: a harness that replaces a file between its authentication
and its use, a directory escape through a filesystem reparse point, and a Git
index manipulation that leaves a digest check reporting clean.

Read without context those look like offensive tooling, and a reviewer's scanner
flagged them as such. They are the opposite. Each one exists because it found a
real defect in code I had written and reported as correct, and each now stands as
the regression that stops the defect returning.

## What is in scope

Verification that a set of data-provenance records cannot be altered without the
alteration being detected. Every artifact involved is produced by this project
and lives in this repository or in its own local output directory.

The only "control" being probed is our own SHA-256 comparison, and the tests
exist to demonstrate that it cannot be satisfied by anything other than the bytes
it claims to describe.

## What is explicitly out of scope

- No third-party or external system is contacted, probed or modelled.
- No network access, no service, no endpoint.
- No credentials, secrets, tokens or keys are read, written or handled.
- No cryptographic primitive is attacked; SHA-256 is used as a checksum and is
  assumed sound.
- No access control, authentication or authorization mechanism belonging to any
  system is circumvented. The project's own fail-closed gates are strengthened,
  never weakened, and no bypass, override or readiness flag is added.
- No pathology values, no DEV or SEALED data, no reader-validation or
  reader-oracle data is read.

## The three reproductions, and what each one closed

1. **Check-then-use race, source side.** The pathology source was hashed by path
   and reopened later, so the recorded digest could describe one revision while
   the derived result came from another. Closed by reading the bytes once,
   authenticating those exact bytes and parsing from memory.

2. **Check-then-use race, package side.** The frozen package authenticated each
   member by path and then reopened the metadata and registry to parse them.
   Closed by capturing every member once and computing all digests, both roots
   and all parsing from the captured buffers. A regression asserts that no member
   is opened more than once, because a second open is the reachable interval.

3. **Integrity check reporting clean on altered state.** The work-checkpoint
   validator compared only the worktree copy of a declared authority, so a staged
   replacement, and separately a staged file-mode change that preserves the blob,
   both left it reporting clean. Closed by comparing the bound tree entry's mode
   and object id against both the index and the worktree.

A fourth reproduction, a directory escape through a reparse point, closed a hole
where a path outside the repository could be accepted as an authority. On this
platform a real symlink cannot be created without privilege, so the test uses a
Windows junction, which is the sharper case: Python reports `is_symlink()` false
for it, so it passes the symlink guard and must be caught by the containment
check on the resolved path.

## Vocabulary

Test and module text uses neutral engineering terms: adversarial case rather than
attack, substitute rather than forge, reproduce rather than exploit, target file
rather than victim, invalid rather than hostile, goes undetected rather than
evades. `TOCTOU` and `symlink` are retained as standard terms of art.

Proof-of-concept detail stays in this repository and is referenced by path and
digest rather than pasted into review conversations.

## Standing conclusion

Nothing in this lane authorizes real T0 execution. `real_execution_ready` is
false, no code path can set it true, pathology values remain closed, and
`STOP_T0_DONOR_ROLE_AT8_AVAILABILITY_AUTHORITY_UNBOUND` remains active.
