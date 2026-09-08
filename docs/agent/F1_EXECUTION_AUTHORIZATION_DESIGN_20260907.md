# F1 execution authorization design — 2026-09-07

Status: `DESIGN_AND_IMPLEMENTATION__NO_AUTHORIZATION_ISSUED__REAL_F1_STILL_UNAUTHORIZED`

## The dead end this removes

The previous producer carried its own permission:

```python
REAL_EXECUTION_READY: bool = False
FROZEN_REAL_CAPTURE_ROOT_SHA256: str | None = None
FROZEN_REAL_SHARD_SET_ROOT_SHA256: str | None = None
FROZEN_REAL_EFFECT_ROW_ROOT_SHA256: str | None = None
```

Those four names made the freeze self-defeating. The only way to make the frozen
source runnable was to edit the frozen source, and the only way to bind a
produced root was to edit it again after outcomes existed. A freeze that must be
broken in order to be used is not a freeze.

Those names no longer exist. A test asserts their absence both as attributes and
as source text, so they cannot come back quietly.

## Where permission lives now

`scripts/v4/f1_execution_authorization_v1.py` reads an authorization artifact
whose path comes from the environment variable `F1_EXECUTION_AUTHORIZATION`.
There is no in-source fallback and no default location: absence is refused with
`STOP_F1_EXECUTION_AUTHORIZATION_ABSENT`.

An authorization is a **pre-result** binding. It names, before any output
exists:

| binding | what a mismatch raises |
|---|---|
| package root | `..._WRONG_PACKAGE_ROOT` |
| frozen source digests (producer, replay, authorization, tests) | `..._WRONG_SOURCE_ROOT` |
| u0 checkpoint `19fb0c25…` | `..._WRONG_CHECKPOINT` |
| reader population: partition, donor count, roster root | `..._WRONG_READER_POPULATION` |
| the seven preflight authority digests | `..._AUTHORITY_DRIFT` |
| accepted mechanics | `..._WRONG_MECHANICS` |
| frozen geometry | `..._WRONG_GEOMETRY` |
| scope | `..._WRONG_SCOPE` |
| its own body digest | `..._ROOT_MISMATCH` |

Each is a separate named STOP so a reviewer can see which binding drifted
rather than reading one opaque refusal. The body digest check means editing an
issued authorization is detected.

## Closure is not authorization

The post-result data-only closure binds the capture, shard and effect-row roots
that only exist after a run. Two rules keep the directions from collapsing:

1. An authorization carrying any produced-output key is rejected with
   `STOP_F1_EXECUTION_AUTHORIZATION_IS_A_CLOSURE_ARTIFACT`.
2. `assert_not_closure_artifact` additionally rejects anything whose schema
   reads as a closure.

So a run cannot be legitimised after the fact by writing a closure for it. The
sequence is authorization, then execution, then closure, and the closure never
edits frozen source.

## Scope, stated narrowly

The only lawful scope is

```
F1_U0_PRODUCTION_MECHANICS_REFERENCE_BASELINE
```

and a validated authorization reports what it does **not** grant: a healthy
trained-teacher result, biological qualification of u0, selection of a future
training target, starting D1 or production teacher training, or access to
reader-validation, reader-oracle, development, sealed, external holdout or
pathology data.

u0 is a mechanics fixture. Model width 160 is architectural, not a biological
dimension. A future redesigned production teacher will require a new prospective
F1 model/checkpoint binding rather than a reinterpretation of this one.

## Population firewall

Execution is `reader_fit` only, and `foundation` and `train` are not synonyms for
it. The lawful roster is read from the `reader_partition` column of the frozen
`reader_donor_split.csv` (digest `efe43e63…`), which declares 104 `reader_fit`,
22 `reader_validation` and 23 `reader_oracle` donors. The roster root must equal
`a635ddf3…`. Continuation and train donors outside `reader_fit` are therefore
absent by construction rather than removed by a filter, and any delivered donor
off the roster raises `STOP_F1_POPULATION_FIREWALL` instead of being dropped.

## Authority byte classes, and why they differ

Authorities are digested over the bytes that actually define them, declared per
authority rather than guessed:

- the three tracked model sources use **git blob bytes**;
- the assignment CSVs and the checkpoint use **file bytes**, since they are
  large and untracked.

This distinction was a real defect. Hashing working-tree bytes for the tracked
sources passed in a checkout with LF endings and failed in a CRLF checkout of
the same commit: in this worktree `ipb_jepa.py` hashes to `f5bdfb73…` on disk
and to the frozen `732ea46f…` in the index. Separately, the source digests must
be resolved from the frozen package's **own** git rather than from whichever
tree holds the CSVs, because `contextual_query_local.py` is tracked on this
branch and untracked in the main working repository.

## What is still not granted

No authorization artifact has been issued. Nothing in this package authorizes a
real sweep, and this document does not grant one. The mechanics are ready for
independent review; execution permission is a separate act.
