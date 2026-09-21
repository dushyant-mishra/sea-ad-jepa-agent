# START HERE — JEPA PROJECT

Date: 2026-09-21

Status: `CURRENT_FULL104_ETL_ATLAS_REPRODUCED__SAFE_LANE_GREEN__GPU_C2_MEASURED__PARALLEL_LANES_REQUIRE_RECONCILIATION__TRAINING_OFF`

## Current takeover point

Use the docs-only handoff branch:

`handoff/jepa-v5-full104-etl-safe-lane-20260921`

It is based on the exact green GPT safe-lane / ETL head:

`gpt/v5-full104-safe-lane-20260921 @ 0c2f5fb8419ea7d1572479e6ef1b13768e52f3c5`

The separate Claude GPU/full-data lane at handoff freeze is:

`claude/v5-full104-blocker-clearance-20260921 @ cdac29eba5f08994bc3d8309a31c05cd21da50aa`

The older active science base PR #33 is:

`audit/v5-full104-information-channel-redteam-20260920 @ ae5dc5c624fff341b8ef30c5359c55528383920a`

**Re-fetch all three live heads before making any change.**

PR #35 and the Claude lane are intentionally parallel and diverged. Do not merge either wholesale into the other.

## Read in this order

1. `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`
2. `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260921_V5_FULL104_ETL_SAFE_LANE_CURRENT.md`
3. `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260921_V5_FULL104_ETL_SAFE_LANE_CURRENT.json`
4. `docs/agent/JEPA_NEW_CHAT_COMMANDS_20260921_V5_FULL104_ETL_SAFE_LANE.md`
5. `analysis/v5_full104_dataset_etl_20260921/README.md`
6. `analysis/v5_full104_dataset_etl_20260921/FULL104_DATASET_ETL_ATLAS_REPORT_20260921.md`
7. `analysis/v5_full104_dataset_etl_20260921/evidence/FULL104_DATASET_ETL_ATLAS_SUMMARY_V3.json`
8. `analysis/v5_full104_information_channel_redteam_20260920/FULL104_SCOPE_AND_HISTORICAL_FIREWALL.md`
9. current blocker-specific reports/designs
10. then inspect the five Claude GPU commits in order.

## Current branch roles

### PR #35 — GPT safe lane + ETL

At freeze:
`0c2f5fb8419ea7d1572479e6ef1b13768e52f3c5`

All four hosted workflows passed:

- runtime closure #390
- Stage-A spillover firewall #372
- remaining-RNA / target-semantics #541
- FULL104 masking runner #589

PR #35 contains:

- lossless estimability mechanics;
- H3 precision-resampling mechanics;
- G3 fit-objective weighting mechanics;
- exact Audit-B burden accounting;
- donor-local Audit-E estimands;
- multivariate V5 target decomposition;
- dataset field-role safeguards;
- role-qualified nuisance/technical G4 decoy;
- F13 denominator counterfactual;
- scale-free G2 materiality mechanics;
- G5 consequence-curve machinery;
- G4 content/stability candidates;
- the reproduced FULL104 ETL/composition atlas.

### Claude GPU lane

Five commits above PR #33:

1. `a153ab655b84...` — 4.55M-row parser equivalence PASS and heavy B/C/E statistics qualified for reuse.
2. `1fe022de5f33...` — authenticated fold-aware C2 measurement and independent row-level verification.
3. `065bc12e67a1...` — Phase-III V1 non-estimability contract; **superseded**.
4. `b6cac05aa050...` — Phase-III V2 contract with cross-review fixes and P4 coverage guard.
5. `cdac29eba5f0...` — prospective Audit-B target-sample freeze; no burden result opened.

The next chat must reconcile these commits into the PR #35 safe-lane work deliberately.

## Dataset-understanding lane is now first class

Pathology-blind modeling does **not** mean the team is blind to the dataset.

Authenticated ETL now establishes:

- full metadata 6,351,753 cells / 149 donors;
- reader-fit 4,553,407 cells / 104 donors / 42 operators;
- reader partitions donor-disjoint;
- cell mass: HVS 4.36%, NPH52 5.19%, SEA_AD 90.44%;
- donor mass: HVS 39.42%, NPH52 16.35%, SEA_AD 44.23%;
- HVS/NPH52 operators are native-class-pure;
- SEA_AD operators are anatomical region matrices with 17–26 native classes;
- SEA_AD donor×region coverage is ragged;
- NPH52 broad-class field is absent for all reader-fit cells;
- 41,238 addresses;
- 17,186 measured by all 42 operators;
- 17,346 measured by all three source families;
- 289 measured by no operator;
- 9 exact support patterns: HVS 1 / NPH52 7 / SEA_AD 1;
- support geometry is strongly source identifying;
- structural unmeasurement, measured zero and collision-unresolved are distinct evidence states.

The ETL replay regenerated all ten SQL aggregates + manifest and all 13 machine atlas outputs byte-for-byte.

Do not redo it unless an authenticated input/query/builder contract changes.

## Permanent scientific boundaries

`DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> TARGET SEMANTICS -> PRODUCTION GEOMETRY -> MODEL`

Historical/reduced evidence may motivate tests but must not set current FULL104 thresholds or outcomes.

```text
TERMINAL_MASKING_OUTCOMES = UNOPENED
D_SHARED                  = SEALED
PATHOLOGY                  = SEALED_FOR_MODEL_AND_TERMINAL_ADAPTATION
DEV / SEALED              = SEALED
MASKING_POLICY_SELECTED    = NO
G5_MARGIN_SELECTED         = NO
TRAINING_OFF
```

Measured zero is evidence, not missing.

Do not collapse:
- measured zero;
- structural unmeasurement;
- collision unresolved;
- target non-variable;
- prediction non-variable;
- missing;
- invalid numeric.

## Current major GPU findings

Heavy sufficient statistics:
- parser rows checked: 4,553,407
- parser mismatches: 0
- artifact reuse qualified
- heavy-stats SHA:
  `f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae`

C2:
- 6,653 / 17,053 targets have >=1 undefined held-out term
- 202 targets have a wholly vacuous source guardrail
- 30,451 / 1,773,512 held-out terms undefined
- row-level cross-check: 384/384 classifications agreed

No terminal masking result was opened.

## Immediate next sequence

1. Re-fetch PR #33, PR #35 and Claude heads.
2. Create a fresh integration branch from the current green PR #35 head.
3. Port Claude Phase-I and Phase-II evidence/reporting deliberately.
4. Reconcile PR #35 estimability contract with Claude V2; run both adversarial test sets.
5. Port the exact Claude Audit-B sample freeze without changing its digest.
6. Execute Audit B on GPU:
   - N1=256;
   - N2=1024 only if relative SE > 0.05;
   - N3=4096 only by the same frozen rule.
7. Production-align Audit E.
8. Compare G3 fit objectives on planted/null lawful controls.
9. Advance real healthy-teacher F and G4.
10. Freeze G5 epsilon only after G4 functional qualification.
11. H3/H4/G2/capacity checks.
12. Terminal masking only after prerequisites.
13. Training authority last.

## Do not redo

Unless inputs changed:

- FULL104 lineage;
- corrected pass1;
- support/census derivation;
- ETL atlas/replay;
- operator semantics profiling;
- parser equivalence;
- heavy B/C/E aggregate qualification;
- C2 source×fold measurement;
- historical T0/T1/QID/F1/Stage81A3 work;
- generic shortcut discovery;
- old 50K exploratory findings.

## Load-bearing rule for the next chat

The next job is **integration and successive blocker closure**, not rediscovery.

The dataset is now understood well enough to inform design without exposing pathology to the model. Preserve that distinction.
