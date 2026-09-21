# FULL104 information-channel red-team — 2026-09-20

Reconnaissance and qualification audits of information channels exposed by the
current FULL104 code, with historical results retained only as supporting
failure-mode priors.

**No current scientific authority is modified by anything in this directory.**
No pass1, Census Authority V2, target eligibility set, masking burden ladder,
masking policy, G3/G4/G5 authority, terminal contract, or training authority has
been changed.

The scope discipline for this lane is explicit in
`FULL104_SCOPE_AND_HISTORICAL_FIREWALL.md`. Smaller pools, fixtures, historical
runs, stale handoffs, and withdrawn findings cannot silently become FULL104
production claims.

```
TERMINAL_MASKING_OUTCOMES   = UNOPENED
D_SHARED                    = SEALED
PATHOLOGY / DEV / SEALED    = SEALED
TERMINAL_BURDEN_SELECTED    = NO
MASKING_POLICY_SELECTED     = NO
TRAINING_OFF
```

The corrected authoritative
`core_measured_zero_frequency = 0.8329826626244999` remains unchanged.

---

## Current audit state

| audit | current state | what is established | what remains open |
|---|---|---|---|
| **A — normalization denominator** | FULL104 reconnaissance | outside-ledger RNA enters the normalization denominator and is strongly source-structured; causal rescaling route exists | whether a model can recover source from the resulting model-visible features |
| **B — effective mask burden** | FULL104 burden geometry + reduced-pool screening diagnostic | burden per address is highly heterogeneous; screening-preferred addresses are burden-enriched inside the deterministic 512-address diagnostic | exact fold-specific full-universe TOP8/RIDGE8/PREFIX3 burden |
| **C — target/source estimability** | FULL104 reconnaissance; C2 instrument repaired | all-donor source support/all-zero geometry is measured; current scorer maps undefined target correlation to finite zero | authenticated source×fold C2 execution and terminal evidence-schema treatment of non-estimability |
| **D — score/standardization estimand** | design finding | current score discards pure between-donor/source location-scale information | complementary guardrail / attacker estimand design |
| **E — co-detection vs quantitative association** | reduced-pool diagnostic | pooled E1/E2 and screening-shaped E3 measured on current rows | production-aligned within-donor/source-balanced E1/E2 with training-side partner selection |
| **F — target decomposition** | historical mechanism fixture only | scalar fixture controls exist | real V5 multivariate query-local latent-state decomposition |
| **G — calibration cache** | **NO_ISSUE_FOUND** | equal-donor cache behaves as designed | only the separate G3 question of which fit-weight geometry is right for capacity calibration |

Additional prospective designs:

- `G3_ATTACKER_FIT_OBJECTIVE_CONTRACT_GAP.md`: keeps
  `CURRENT_CELL_WEIGHTED`, `PRODUCTION_OBJECTIVE_MATCHED`, and
  `SOURCE_DONOR_BALANCED_DIAGNOSTIC` distinct.
- `H3_TARGET_VS_DONOR_PRECISION_DECOMPOSITION_DESIGN.md`: separates target-panel
  uncertainty from donor-within-source uncertainty.
- the upstream G4 design now requires a technical-only decoy before any biological
  content functional can be frozen.

`CROSS_AUDIT_INTERACTIONS.md` carries the dependency graph and current blocker
states.

## Evidence scope classes

Every result belongs to one of:

- `CURRENT_FULL104_AUTHORITY`
- `CURRENT_FULL104_RECONNAISSANCE`
- `REDUCED_POOL_DIAGNOSTIC`
- `FIXTURE_ONLY`
- `HISTORICAL_SUPPORTING_ONLY`
- `WITHDRAWN`

Only the first class may set current numeric authority, and only for its bound
role. Historical findings may motivate tests and negative controls; they cannot
set thresholds, margins, policies, target universes, or expected effects.

## Evidence layout

```
scripts/                     producing/qualification scripts
evidence/                    compact committed evidence
EVIDENCE_SHA256.csv          byte size + SHA-256 manifest; regenerated LAST
EXTERNAL_ARTIFACTS.json      immutable provenance for large GPU-machine artifacts
```

Large external artifacts preserve the producer commit and producer-script hash
that created the bytes. A later manifest rebuild is not allowed to relabel old
bytes as current output.

The existing 242 MB B/C/E sufficient-statistics artifact predates adoption of the
production-exact `source_library` parser in the shared audit builder. It is
therefore **not reusable yet**. Reuse is allowed only if
`audit_source_library_parser_equivalence_20260920.py` verifies exact equality of
legacy and current parser outputs over all authenticated 4,553,407 metadata rows;
otherwise the heavy statistics must be rebuilt.

## Audit G: hosted CI versus physical qualification

GitHub-hosted Linux runners cannot access the Windows-local calibration cache.
The responsibilities are therefore split without using skips:

1. hosted CI validates the committed Audit G evidence fixture, cache role/design,
   and content-blind selector implementation;
2. `qualify_audit_g_physical_artifact_20260920.py` re-authenticates and
   re-derives the physical cache/pass1 invariants on the machine that actually
   holds those bytes.

The physical qualifier fails closed on missing bytes, hash mismatch, geometry
mismatch, or disagreement with committed evidence. Hosted CI does **not** claim
physical access it does not have.

## Verification protocol

For a result to advance beyond reconnaissance:

1. bind current FULL104 authority inputs;
2. implement and unit-test;
3. include a positive control with known answer;
4. include a falsifying negative/adversarial control;
5. execute on the declared substrate and candidate universe;
6. fail closed on provenance/estimability;
7. independently cross-check headline quantities where possible;
8. red-team the interpretation and scope class;
9. regenerate manifests only after scientific/code content is stable.

`NOT_MEASURABLE`, `OPEN`, and undefined scientific quantities are never
silently converted to zero.

## Current next work

Before G4/G5 or terminal masking:

1. run the metadata-only parser-equivalence qualification for the existing B/C/E
   heavy statistics;
2. if it passes, execute authenticated fold-aware C2 from those bound statistics;
   otherwise rebuild the heavy statistics first;
3. run exact/prospectively sampled fold-specific production-policy burden for B;
4. recompute E under production-aligned donor/source conditioning;
5. settle the attacker score/fit-objective questions;
6. then freeze G4 (including the technical-only decoy), justify G5, and proceed
   through H3/H4/G2/G3 in dependency order.

Nothing in this lane authorizes terminal masking or training.
