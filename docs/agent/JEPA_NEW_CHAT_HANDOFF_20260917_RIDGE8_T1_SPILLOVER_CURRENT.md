# JEPA new-chat handoff — 2026-09-17 — RIDGE8 expansion, T1 stress, spillover boundary

## Read this first
This handoff is a successor to the September 15 target-authority handoff and the September 17 masking-successor lane. Do **not** restart the project from T0/T1, QID/F1, Stage81A3, FULL104 lineage, Stage-A, or generic shortcut discovery.

## Current working branch
`analysis/v5-ridge8-expanded-validation-20260917`

Before acting, re-fetch the live head. At handoff construction the branch lineage already contained the expanded RIDGE8/nonlinear32 package through `99dc3a6ff5f540fac17e86b135f2c6710bb41405`; this handoff and T1 stress package are successor commits on the same branch.

## Global posture
- `TRAINING_OFF`
- protected/pathology/DEV/SEALED/D_shared outcomes remain sealed
- no production masking authority yet
- no production evidence-budget authority yet
- no production EMA-timescale authority yet
- no production geometry authority yet

## Scientific semantic invariant — DO NOT DRIFT
We are **not** training the model to reconstruct the numerical expression of a hidden gene.

The intended task is: mask evidence and ask whether the remaining RNA supports recovery of the underlying biological/cellular state, including query-local state associated with the addressed molecular feature.

Expression prediction in the masking lane is only an **anti-shortcut attacker**: it tests whether an easy proxy remains visible. It is not the JEPA target and must never silently become the loss.

## Dataset-first design invariant
`DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> TARGET SEMANTICS -> PRODUCTION GEOMETRY -> MODEL`

Do not adapt the dataset to a preferred architecture. Build each authority from the available data and its support.

## Historical-spillover firewall
Historical T0/T1 work is valuable as a testing bed and regression/adversarial fixture. It is **not** automatically current authority.

Before reusing any historical component classify it as:
- `ALREADY_AUDITED`
- `SUPERSEDED`
- `OPEN`
- `CHANGED_INPUT_REQUIRES_REQUALIFICATION`

Never carry forward historical weights, target semantics, optimizer state, QID/F1 assumptions, Stage81A3 scope, post-u0 T1 conclusions, old masking estimators, or legacy context/source interpretations merely because code exists.

The current branch already includes Stage-A spillover-firewall CI. Any new production component must bind to current V5 authority explicitly rather than import a historical default.

## RIDGE8 masking successor — current evidence
Status remains **exploratory, not masking authority**.

### Unified 32-target, same ridge scorer
At 6,000 addresses, 32 targets, 4 folds, same common random masks and 15% exploratory burden:
- RIDGE8 mean shortcut-score drop: `0.007979` = `6.42%`; target-win `30/32`
- TOP8: `0.004734` = `3.81%`; target-win `29/32`
- PREFIX3: `0.000184` overall = `0.15%`; acts on only `10/32` targets

At 800 and 2,000 addresses RIDGE8 also remains broadly positive. PREFIX3 is sparse/selective rather than simply bad: when it acts, effects can be larger, but action collapses with universe size.

### Outside-original-800 target challenge
Targets were selected deterministically from the other 5,200 addresses without inspecting RIDGE8 outcomes.

At 6,000 addresses:
- RIDGE8: mean drop `0.010597`, relative `10.55%`, target-win `31/32`, target-clustered 95% CI `[0.006861, 0.014994]`
- TOP8: `0.006433`, `6.40%`, target-win `29/32`, CI `[0.003450, 0.010235]`
- RIDGE8 minus TOP8: `+0.004164`, target-clustered 95% CI `[0.001527, 0.007009]`
- PREFIX3: `0.002215` overall; acts on `6/32`; acted-row mean `0.016676`

This removes the main concern that RIDGE8 only looked good because targets came from the original 800-address subset.

### Nonlinear outside-800 challenge
32 targets x 4 folds with a nonlinear held-donor attacker:
- RIDGE8 mean reduction `0.007563` = `6.22%`; positive target mean `29/32`
- TOP8 `0.005077` = `4.17%`; positive target mean `24/32`
- paired RIDGE8-TOP8 mean advantage about `+0.00249`; target-clustered 95% CI about `[+0.00073, +0.00432]`

Thus RIDGE8's discovery-side advantage is not merely a ridge/linear-attacker artifact. This still does not establish biological-state recovery.

### STABLE10 / STABLE15
- STABLE15: vacuous at tested threshold; zero action rows.
- STABLE10: not primarily a mask-construction bug. In nearly all action rows the selected feature is actually swapped into the mask; the simple attacker often selects the same strongest remaining predictor, so the score does not change. Treat as ineffective selector for that threat model, not broken burden-preserving masking.

## T1 checkpoint stress fixture
Local historical checkpoints available: u0, u10, u25, u50, u100, u200, u205. They include the actual old online encoder, EMA target encoder, predictor and training state. The calibration bundle also contains original `ipb_jepa.py`, `stage81a3_prod41k_teacher_t1.py`, loader/schedule and shortcut atlas.

These checkpoints are **historically defective post-u0 training lineage** and may only be used as quarantined adversarial fixtures.

### State-level masking challenge at u200
Using the actual old model and query-local latent-state error (not gene-expression error), equal-burden UNIFORM/RIDGE8/TOP8/PREFIX3 masks are almost indistinguishable:
- UNIFORM mean query cosine error `0.605672`
- RIDGE8 `0.605669` (delta `-0.000002`)
- TOP8 `0.605664` (delta `-0.000008`)
- PREFIX3 `0.605669` (delta `-0.000002`)

A small u0 matched slice has UNIFORM `1.075453` vs RIDGE8 `1.075476`.

Interpretation: the historical trajectory improved teacher-state alignment, but the endpoint is nearly insensitive to which local evidence is removed. This does **not** validate or invalidate RIDGE8 as production masking. It tells us the new pipeline must explicitly prove that remaining RNA matters for query-local state instead of allowing query identity/global state/predictor routing to dominate.

## Already audited — do not repeat as new discoveries
- historical T1/C2 zero-gradient/training-mechanics failure and repair chronology
- Stage81A3 corrected TRAIN cache and its non-FULL104 scope
- T0 V20 and T0 measurement closeout
- QID mismatch / matched-null vs paired-wrong-query issue
- F1-B optimizer/receipt guard pattern and CELL/identity controls
- D_shared design chain; outcomes sealed
- FULL104 lineage recovery
- V0/V1 rebuild
- visibility ablation and same-cell thinning
- context/source/operator pooled interpretation problems
- donor recurrence/generalization work
- historical correlated-gene masking review
- teacher/student/EMA mechanics
- V5 fail-closed carryover defect
- target-identity shortcut discovery and Stage-A structural qualification
- observation-state gradient firewall
- accidental carryover/spillover findings

Consult `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md` before starting any related work.

## Current V5 authorities that should remain controlling
- primary molecular representation: `VALUE_ONLY_256`
- support/estimability authority: unmeasured = missing, not zero; common core = comparability, not biology
- base training estimand: donor-uniform, cell-uniform-within-donor
- shared target address provider: deterministic hashed canonical identity -> shared trainable projection; no per-address free embedding
- Stage-A structural qualification passed
- current masking policy schema exists, but production masking authority is still open

## Important open semantic defect
The current teacher-target semantics authority historically used free-form strings and does not by itself prove that future code cannot bind scalar hidden-gene reconstruction as the teacher target. A successor target-semantics authority/regression should explicitly bind:
1. biological/cellular latent state;
2. query-local state semantics;
3. hidden-gene scalar reconstruction forbidden as the objective;
4. remaining-RNA necessity test;
5. identity-only and generic/global-cell-only routes must not suffice for production authority.

Do not overwrite historical V1 in place; build a successor with explicit supersession.

## Distinctive project direction to preserve
The strongest project thesis is an **evidence-calibrated, observation-aware, pathology-blind JEPA** whose state must survive falsification.

Prospective requirements, not yet production authority:
- evidence-dose response `z_i(e)`
- measurement-depth response `z_i(e,d)`
- separate biological uncertainty from measurement uncertainty
- observation operator `O_t` for physical acquisition/support, without free donor/dataset identity embeddings
- dataset-derived latent/subspace stability rather than arbitrary coordinate interpretation
- representation certificate reporting latent state, support, evidence stability, measurement unfamiliarity and biological unfamiliarity
- hierarchical transfer: held donor -> operator/matrix -> source/study -> technology
- external/protected biology only after design freeze

These should strengthen qualification contracts, not be bolted on as arbitrary losses.

## Immediate next work
1. Finish the **historical-spillover coverage audit**: map every known old failure to a current V5 guard; add only genuinely missing regressions.
2. Highest-priority missing regression: **remaining-RNA necessity for query-local state** while allowing legitimate global biological context.
3. Build successor teacher-target-semantics authority that forbids scalar hidden-gene reconstruction and binds state semantics explicitly.
4. Prospectively freeze FULL104 masking qualification; do not inspect successor outcomes first.
5. Keep RIDGE8, TOP8 and selective PREFIX3 as named comparators in the frozen contract; do not post-hoc combine them.
6. Freeze evidence-budget authority separately from partner-selection/masking-policy authority.
7. Add nonlinear attacker-class robustness as a masking qualification requirement, using target-clustered uncertainty.
8. Only after target/masking/evidence/geometry/EMA/runtime contracts are frozen should training authority be considered.

## Local/heavy assets available in this chat environment
- frozen 50k x 41,238 discovery expression matrix, reconstructed SHA-256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- foundation calibration bundle
- historical T1 trajectory checkpoints u0/u10/u25/u50/u100/u200/u205
- T1 historical code bundle extracted locally
- current RIDGE8 derived 6,000-address caches and outside-800 target caches

Heavy derived caches are not GitHub authority. Scripts/results/provenance are committed; caches should be regenerated from frozen substrate where needed.

Known suspicious standalone NPZ with SHA beginning `001375ec...` remains provenance-mismatched and must **not** be used as authority.

## FULL104 production substrate reference
- 4,553,407 cells
- 104 donors
- 42 operators
- 41,238 addresses
- 17,186 common-core addresses
- 8,915 Level-4 blocks
- block manifest SHA-256 `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`
- heavy substrate lives on the separate GPU-enabled machine / attached drive and is not expected in this chat runtime

## New-chat startup checklist
1. Fetch live `analysis/v5-ridge8-expanded-validation-20260917` head.
2. Read `START_HERE.md`.
3. Read `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`.
4. Read this handoff.
5. Read `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md`.
6. Read the RIDGE8 expanded-validation provenance and reports.
7. Read the T1 state-stress report only as historical fixture evidence.
8. Classify proposed work before executing; do not repeat settled audits.
9. Keep training OFF and protected outcomes sealed.
10. Continue from remaining-RNA necessity / target-semantics successor / prospective FULL104 masking qualification.
