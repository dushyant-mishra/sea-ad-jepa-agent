# Synthetic dataset agent handoff — ETL→generator propagation

Status: **TAKEOVER / NON-AUTHORIZING**  
Date: 2026-10-08

## Branch to merge / take over

`handoff/synthetic-etl-propagation-20261008`

Base synthetic/S174 head:

`750cb83c8c0535cc67a70d58b62db5607bd7d01e`

This branch is intentionally **docs-only**. It does not alter synthetic generator code, results, tests, workflows, runtime, or training authority.

## Why this handoff exists

A cross-lane audit was accidentally performed from the target-discovery conversation. The work is scientifically relevant to the synthetic-data lane, so it has been separated here for the synthetic agent to merge and continue without contaminating target-discovery.

The decision-changing audit is:

`docs/agent/ETL_TO_SYNTHETIC_RECONCILIATION_20261008.md`

## Main finding

The real-data ETL/calibration work already captured much of the structure needed for a realistic synthetic population. The primary gap is not lack of ETL characterization; it is **failure to propagate broad cell-class structure into the synthetic truth generator**.

The real calibration explicitly extracts `broad_cell_class`, cell-class counts, and says cell-class composition should be used so that synthetic cell identity carries realistic dominance. But current V73/V77 truth construction does not carry a broad-cell-class variable into truth and does not condition the main biological latent programs on class.

This makes the corrected T5 mismatch understandable:

- corrected real T5 within-class / pooled ratio: ~0.7435;
- replayed synthetic arms: ~1.02–1.21;
- current hidden substates are independent of annotated broad class.

This is a **generator propagation defect / missing mechanism**, not evidence that the FULL104 population geometry or the observer must be redesigned.

## What ETL information is already carried correctly

Keep these unchanged unless a separate audit finds a defect:

- FULL104 source composition;
- 104-donor empirical population geometry;
- 42 observation operators;
- 1,400 donor×operator groups;
- ragged operator support;
- 2K operator-support rescue;
- source/operator nesting;
- operator-specific structural availability;
- frozen measurement/counting observer for the first propagation experiment;
- corrected S174 real-data reference points.

## What is missing or only post-hoc

Primary missing pieces:

1. explicit broad-cell-class assignment in synthetic truth;
2. class-shared covariance-generating biology;
3. within-class continuous/state biology that remains after class effects;
4. optional donor×class biology as a separate later ablation.

T5 currently measures class-conditioned structure **after** generation but the generator was not physically equipped to create the relevant class contribution.

## Correct next task

Do **not** tune the existing dynamic-range arms further.

First write and freeze a prospective **ETL→synthetic propagation contract**. The minimum proposed experiment family is:

- **E0:** current generator unchanged;
- **E1:** explicit broad-class composition only, with no class-dependent expression program;
- **E2:** broad class + random-content class-shared expression programs;
- **E3:** E2 + within-class continuous biology;
- **E4:** E3 + donor×class interaction, only as a later ablation.

For the first experiment, keep the observation/counting model fixed.

Preserve the existing design rule:

**real geometry, random content**

That means real class proportions and geometry may constrain the synthetic population, but real gene identities/program memberships must not simply be planted as the answer.

## Scoring

Evaluate the corrected invariants together, not only T5:

- expression median |r|;
- expression fraction |r| > 0.3;
- expression top-10-PC variance;
- detection median |r|;
- detection strong-pair fraction / degree;
- detection transitivity / community structure;
- T5 within-class / pooled ratio;
- abundance max/median and top-1% share;
- median detected genes per cell.

Do not declare a winner by matching one statistic.

Do not use the current S159 donor-bootstrap p05–p95 bands as binary pass/fail gates; some corrected real points lie outside their own bootstrap interval. Treat current point estimates as descriptive references and donor bootstrap as uncertainty diagnostics until S159 is repaired.

## Important corrected S174 state

Source branch:

`claude/s174-train-cache-rebuild-20261007`

Current source head:

`750cb83c8c0535cc67a70d58b62db5607bd7d01e`

Replay checkpoint:

`46d8eaa8fa23cd60762a8a90c55b84e8d86364b2`

Replay CI:

`37693603160` — 146 tests passed, zero skipped.

Do not resurrect the old Stage81A3R interpretation. The corrected replay supersedes it.

Key corrected reference points include approximately:

- expression median |r|: 0.0562;
- expression fraction |r| > 0.3: 0.0242;
- expression top-10-PC variance: 0.262;
- detection median |r|: 0.1946;
- detection fraction |r| > 0.3: 0.1348;
- detection mean degree: 404.36;
- detection transitivity: 0.6672;
- T5 within/pool: 0.7435;
- abundance max/median: 2273.21;
- top-1% count share: 0.2741;
- median detected genes/cell: 4495.5.

## Explicit non-goals / boundaries

Do not change in this takeover step:

- runtime / optimizer / EMA / checkpoint code;
- q-safety / provenance machinery;
- real-data training authority;
- TEST or Morabito protections;
- 500K or Stage 4 authority;
- production EMA selection;
- 353 historical Ensembl-ID remappings;
- production scientific estimand selection;
- target-discovery lane artifacts.

## Merge guidance

This branch is designed to be merged directly into the synthetic/S174 lane because it is based exactly on `750cb83c...` and adds only two audit/handoff documents.

After merging, the synthetic agent should:

1. independently re-audit the ETL→generator conclusion;
2. freeze the propagation contract before code changes;
3. add RED tests proving broad class is absent from the current truth path and specifying the intended new behavior;
4. implement the smallest E1/E2 path first;
5. keep observer/counting fixed;
6. replay E0–E2 before adding E3/E4;
7. record every decision-changing result with exact SHAs and CI receipts.

## Provenance of this handoff

The original accidental audit was recorded on the general takeover branch at commit:

`ef8612f7ece7bd6af629d25146bbfdc6f318ae77`

This dedicated branch re-homes that work onto the correct synthetic/S174 lineage so the synthetic agent can merge it cleanly.