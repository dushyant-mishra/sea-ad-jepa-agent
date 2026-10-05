# JEPA V58 — R3 regulatory exposure ledger and external-anchor custody handoff

Date: 2026-09-28

Governance: `TRAINING=OFF` · `TD60=BLOCKED` · no real regulatory molecular outcome opened.

## Purpose

This successor makes the chat-local V58/R3 work and the exploratory external-anchor synthetic probe available in GitHub so the next agent does not depend on this chat or local scratch state.

It also reconciles the final V52 custody **file contents** onto the V57 scientific line. The GitHub connector used here does not expose a branch-merge operation, so this is not represented as a merge commit. Historical ancestry remains divergent; exact final V52 custody content is copied forward and this limitation is explicit.

## Starting scientific head

V57 / PR #194:

`31a3d9742d2683061583a3dbe3f1c337b8eb2afa`

V57 remains the controlling cis-transport scientific closeout:

- V54 transported empirical-rank statistic is biologically responsive but fails its frozen specificity rule at available donor counts.
- V55 within-donor gene ordering: RED.
- V56 donor-neighborhood geometry: RED.
- V57 n=18 precision margin: `-0.02871287128712885`.
- Morabito-sized n=18 is not authorized for real target-state execution by the current cis statistic.

## V52 custody reconciliation

Current V52 head is:

`0369fb7329bd2080260d2ca505fa6bd2e2e89fdd`

V53–V57 branched from earlier V52 head `b5c970de...`, so ancestry diverged after later V52 custody repairs.

V58 carries forward the exact final V52 content for:

- `docs/agent/V52_R2_R4_RECOVERY_CLOSEOUT_20260928.md`
- `docs/agent/V52_R2_R4_RECOVERY_MANIFEST_20260928.json`
- `docs/agent/recovered-v52-20260928/out_seaad-spatial.zip.b64`

This repairs the custody **content state** required by the next agent. It does not erase or rewrite the historical divergent commits.

## R3 regulatory exposure ledger

New implementation:

`src/sea_ad_jepa/regulatory/regulatory_exposure_ledger_v1.py`

Local source SHA-256 before GitHub transfer:

`c2c8afa217df62fedd6d8fe4b6341d402c09300ac8674abf052a1dd7312a2d9a`

Test:

`tests/test_regulatory_exposure_ledger_v1.py`

Local test SHA-256:

`dab1c6ecef0808f4db5eb2ecaa3f2834a43946c83f4b296fa23361e826b6eda3`

Snapshot:

`results/v58/R3_REGULATORY_EXPOSURE_SNAPSHOT_V1.json`

Historical ledger digest represented by the snapshot:

`03dbe2ed966e353aa750c336e7670ee63058c8acba23dd3c381a98521596ea4f`

The ledger is deliberately NON-AUTHORIZING.

It tracks exposure at exact:

`(source, modality, outcome_family)`

rather than assigning one exposure state to an entire dataset.

Properties physically exercised by the test suite:

1. previously inspected metadata does not automatically mark molecular target outcomes exposed;
2. exposure cannot regress;
3. UNKNOWN does not mean pristine;
4. UNKNOWN never self-authorizes prospective confirmation;
5. a regulatory object cannot independently confirm on its own construction source;
6. the possible UCI donor overlap between GSE214979 and Morabito remains binding;
7. ledger mutation after freezing is detected.

Local execution:

`7 passed in 0.04s`

with `PYTHONPATH=<v58_r3>/src`.

### Important R3 exposure distinctions

Morabito:

- RNA / `MICROGLIA_PSEUDOBULK_TF_TARGET_COACTIVITY` = DEVELOPMENT.
- ATAC / `MARGINAL_ACCESSIBILITY_AND_COVERAGE` = INSPECTED.
- ATAC / `TARGET_STATE_CIS_CORRESPONDENCE` = UNKNOWN.

GSE214979:

- metadata pairing/cell-type/donor census = INSPECTED.
- molecular regulatory RNA↔ATAC covariance = UNKNOWN.

GSE272082:

- donor/region/label authentication = INSPECTED.
- molecular regulatory covariance = UNKNOWN.

SEA-AD:

- RNA contribution to FULL104 = DEVELOPMENT.
- target-state ATAC correspondence = UNKNOWN.

SEA-AD spatial:

- technical detection/segmentation metrics = INSPECTED.
- target-program spatial expression = UNKNOWN.

Stage75F TF-tier/target hypotheses = DEVELOPMENT.

UNKNOWN here means “not documented as exposed by this ledger.” It does **not** prove pristine status and does not permit confirmation without a separate physical outcome seal.

## Cross-source rule that must survive

GSE214979 versus Morabito:

`UNDETERMINED_POSSIBLE_UCI_DONOR_OVERLAP`

Binding rule:

any agreement claim must either exclude GSE214979 donors `1224,1230,1238` or carry the overlap caveat explicitly.

The ledger does not authorize independent confirmation between these sources by itself.

## Exploratory external-anchor synthetic probe

Source:

`scripts/regulatory/v53_external_anchor_benchmark.py`

Local SHA-256:

`90b8154327b0467c73f57695279eaf26ae0831acdebc3145933fbace4f369523`

Result:

`results/v58/V53_EXTERNAL_ANCHOR_SYNTHETIC_IDENTIFIABILITY_V1.json`

Local result SHA-256:

`79c07b9f7f699e5e1bfffea3eda32ae8446b12359ce58348e5149f8274203205`

Fresh local replay with 500 replicates reproduced that exact result SHA-256 and exited 0.

Within its represented nuisance class at n=18:

- permitted negative gate-pass rates are near nominal;
- planted edge-specific cis positives pass;
- badly unmatched local decoys are rejected by the balance gate.

However the load-bearing boundary is explicit:

`NEG5_ANCHOR_KEYED_SEMANTIC_TWIN`

is byte-identical to the planted positive and passes at rate 1.0.

Therefore this probe:

- may support design of an externally anchored nuisance class;
- does **not** establish unrestricted biological specificity;
- does **not** authorize real regulatory data;
- does **not** supersede V57.

Its own result sets:

`real_data_authorized = false`.

## What remains for Claude / next agent

The next agent should continue on this V58 branch rather than reconstructing R3.

Required next work:

1. independently audit the R3 seeded exposure facts against PR #164, #175, #182, V50/V51, V52 and V57;
2. improve or reject ledger facts if repository evidence contradicts them;
3. build an external-cis-map candidate inventory using provenance-only criteria before looking at target-state correspondence;
4. explicitly compare Nott-like brain enhancer/promoter maps, large primary-human-microglia regulome resources, ABC-style maps, independent adult-brain ATAC references, and newer enhancer–gene mapping approaches;
5. for each candidate record donor/source overlap, cell-type resolution, construction modality, RNA dependence, disease-selection dependence, target leakage risk, nuisance class addressed and prohibited claims;
6. freeze the external-object selection rule before evaluating correspondence to the target program;
7. only then design the next synthetic gate at the actual donor scale.

Do not open Morabito, SEA-AD, GSE214979 or GSE272082 target-state regulatory outcomes during this audit.

## Authority defect remains open

The existing production authority chain still lacks first-class regulatory/biological-specificity and q-safety roots. Do not enable training.

Any authority repair must use versioned successor schemas and must not pretend the current biological gate passed.

## Current state

- R2: closed for current purpose.
- R4: structurally bounded; spatial supporting only.
- V53–V57: synthetic cis route remains unqualified at real cohort donor counts.
- R3: implementation now GitHub-custodied; locally 7/7 tests pass.
- external-anchor probe: GitHub-custodied exploratory synthetic result; semantic twin remains nonidentifiable.
- real regulatory biology: unopened by V58.
- `TRAINING=OFF`.
- `TD60=BLOCKED`.
