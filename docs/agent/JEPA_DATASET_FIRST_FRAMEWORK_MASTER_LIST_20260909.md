# JEPA dataset-first framework master list — 2026-09-09

This is the active master list after T0 R5. The framework goal is not to maximize tests around toy examples; it is to create a replayable authority chain around the actual frozen dataset.

## Framework principle

The dataset is the authority. Code exists to prove, transform, package, and replay the dataset-derived facts without pathology leakage or post-hoc fitting.

Synthetic fixtures are allowed only to prove fail-closed behavior and regression boundaries. They are not production evidence.

## Authority DAG target

```
Frozen source assets
  ├─ MTG source H5AD
  ├─ Phase2 block manifests and payloads
  ├─ B1 feature/projection authority
  ├─ membership authorities
  └─ donor metadata authorities
        ↓
B2 logical row authority
        ↓
Raw-source population authority over 20,804 rows
        ↓
Technical-completeness authority
        ↓
Age/sex, immune fraction, AT8 availability authorities
        ↓
Estimability preflight
        ↓
Eligible donor authority
        ↓
Teacher/student framework
        ↓
Production inference gates
```

## Current blocker level

### Blocker 1 — Real B2 population authority not materialized

Status: open.

The R5 implementation has a mechanism, but the production run was blocked before producing the 20,804-row artifact. This is the highest-priority blocker.

### Blocker 2 — Technical completeness not production-materialized

Status: blocked by Blocker 1.

The production technical-completeness package must be built only after the raw-source population authority exists and replays.

### Blocker 3 — Eligible-donor authority not allowed yet

Status: intentionally blocked.

Do not start eligible donors until B2 raw-source population authority and technical completeness both replay.

### Blocker 4 — Teacher/student framework cannot become production until T0 authorities are real

Status: intentionally blocked.

Teacher/student architecture work can continue as design, but no production claims should depend on unmaterialized T0 authorities.

## Immediate task set

1. Commit reproducible real-B2 runner and replay verifier.
2. Execute real 20,804-row B2 raw-source population proof through an allowed permission path.
3. Emit immutable raw-source population artifacts.
4. Replay raw-source population artifacts from disk.
5. Commit the hash/run/replay summary.
6. Build production technical-completeness package using the real population authority.
7. Replay technical completeness from disk.
8. Only then revisit eligible-donor construction.

## Evidence standard

Each materialized authority must provide:

- artifact path;
- bytes;
- SHA-256;
- package root;
- parent roots;
- stored root;
- recomputed root;
- externally expected root;
- row/cell/donor counts;
- mismatch counts;
- replay verdict;
- explicit pathology-read status.

Console output alone is not evidence.

## Things not to do

- Do not add more synthetic fixtures unless a new concrete defect is found.
- Do not interpret a successful preflight as population closure.
- Do not flip readiness flags without an artifact and replay.
- Do not construct eligible donors while T0 population and technical completeness remain unmaterialized.
- Do not let temp scratchpad scripts become the only runnable record.
- Do not treat a physical plan root as audit evidence if the actual payload map is separately caller-supplied and not tied to the plan.

## Next external review questions

1. Does the committed runner reproduce the exact preflight Claude ran locally?
2. Does the runner avoid pathology fields by construction?
3. Does the raw-source population root bind row order and exact cardinality?
4. Does replay recompute from bytes, not trust the in-memory run object?
5. Does technical completeness use the raw-source proof for Q_DEPTH and the 35,076 B1 projection for Q_DETECT?
6. Does the physical plan actually determine consumed payloads?

## Definition of sufficiently there

The T0 framework is sufficiently there for downstream eligible-donor construction only after both are true:

```
raw-source population authority: real 20,804 rows, replay PASS
technical-completeness authority: real dataset-derived package, replay PASS
```

Until then, framework design is improved but the dataset chain is not closed.
