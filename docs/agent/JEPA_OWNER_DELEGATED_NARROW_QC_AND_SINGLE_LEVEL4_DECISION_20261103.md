# JEPA owner-delegated narrow source-read decisions — 2026-11-03

**Decision classification:** `OWNER_DELEGATED_SCOPE_APPROVAL__QC_ONLY_V1_AND_SINGLE_LEVEL4_ADAPTER_PREFLIGHT`. The project owner, in conversation on 2026-11-03, explicitly deferred the two limited experimental-scope decisions to GPT; GPT chose to allow both **only under the following conditions**. This records an **owner-delegated project decision**, **NOT** a cryptographic human signature, independent data-rights issuance, external institutional permission, source-material integrity proof, or biological/scientific qualification.

**Standing authority:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`. This decision does not supersede existing Task2/3 data isolation, gene/alias rights, NPH52 restrictions, independent review, V79/V80, source licensing, or STOP_A/B/C.

## 1. JEPA_QC_ONLY_ANALYTIC_ALLOWLIST_V1 — APPROVED WITH CONDITIONS

**Exact columns:** `SEA_AD.Doublet score` and `HVS.is_primary_data` only, under their pre-existing public processed deposits and frozen source/matrix identities. **No other previously excluded field is added.** This is **internal analytical scope**, not permission needed to download public data.

**Allowed:** aggregate depositor-QC metadata distributions; source selection characterizations; missing-value and duplicate-cell checks; descriptive comparison with measured selection metadata. Existing #513 aggregate outputs and #528 input-admission receipts **should be reused** rather than indiscriminately re-reading large H5ADs. If one additional replay is scientifically necessary, it must stay within the two named columns and use the admitted, source-pinned, versioned and independently reviewed code path. No person-, donor-, library- or cell-identifying rows are published.

**Forbidden:**
- No model/student/teacher inputs, covariates, losses, selection of C1/C2/C3, rank/representation/target choice or donor/fold reassignment.
- No joins with pathology, disease outcomes or DEV/SEALED/reader-validation/oracle data.
- No doublet-score thresholding or primary-data filtering before its query-independence effect is established. `Doublet score` is expression-derived and cannot be presumed independent of any candidate query.
- No auto-enlargement of this allowlist or accessing NPH52 quarantined expression; any additional column requires a separately reviewed V2.
- No quiet bypass of the original #528 wrapper's `REPLAY_HOLD`. The decision removes the **policy hold** on these two QC fields, not the **software guard**. Macha may propose a narrow versioned one-use gate update with CI and nonauthor review that checks this exact recorded decision, frozen probe and output hash; do not modify the frozen #513 probe or accept a changed aggregate as prior authority. No replay is required if existing bounded aggregates answer the QC question.

**Output:** machine-readable aggregate-only QC receipt citing source versions, pinned input IDs, reading mode, field allowlist and any failure/limitations; explicitly `NO_QUERY_INDEPENDENCE_CLAIM` and all model/training/selection flags false.

## 2. SINGLE_SEA_AD_READER_FIT_LEVEL4_SOURCE_TO_CASEBUNDLE_PREFLIGHT_V1 — APPROVED WITH CONDITIONS

**Source choice:** SEA-AD publicly acquired *processed* data, **one** existing `reader_fit` Level-4 expression block only. Reason: existing source audit reports that SEA-AD deposited per-cell matrix totals equal the depositor `Number of UMIs` for 4,118,213 deposited reader-fit cells, a useful *internal consistency* condition; the same deposited files do **not** authenticate external origin or guarantee query-independent cell selection. HVS has an unexplained total-definition gap, and NPH52 remains internally barred from real query issuance.

**Predeclaration, before count values:** From the already-frozen Level-4 manifest and source/operator permit/alias/measurement metadata, select the **lexicographically first eligible SEA-AD reader_fit block** in canonical (`source`, `matrix_id`, `block_id`) order. Freeze the manifest hash, exact block identity, operator, donor/region/library identity **inside private receipts**, and any permitted test query molecular address/alias rights in a committed no-outcomes preflight object before reading the numeric count block. A block or query must not be chosen because of high expression, positive coverage or desirable results. **No fallback or block-shopping after seeing counts:** if the first candidate is unsupported by source rights, define eligibility solely by frozen metadata before opening; if no permitted block/query exists, abstain `NOT_ESTIMABLE`.

**Read scope:** exactly the one predeclared `reader_fit` Level-4 block's count values, independently sourced per-cell physical library totals, already pinned source/operator molecular-address and assay-support mapping and the minimal donor/library join required to verify CaseBundle provenance. No other blocks; no DEV/SEALED, reader_validation, reader_oracle, pathology/disease, raw FASTQ/BAM, NPH52 quarantined cells or unrelated columns. Do not expose donor, cell or specimen identifiers in GitHub outputs.

**Required software behavior:** check the established Task2/3 reader split and producer-access receipt, existing eight-field #513 source/query/alias/right contract, molecular-address identity and collision states, and parent/source SHA evidence. Preserve physical private `source_library` / `library_size` and construct the D1 student view **separately** from permitted `MEASURED_SCALAR` base-right counts. Never copy private library size into D1 or use a D1 sum to fill the CaseBundle physical denominator. Withheld, structural unmeasurement and collision-unresolved values must not be coerced to zero. Existing Task5 CaseBundle V1 is `FIXTURE_ONLY`: this decision does not lift it or silently give it real-data acceptance. Any real-path successor needs a **new versioned validator/adapter**, fail-closed tests and nonauthor review.

**Allowed proof/output:** byte-bound receipt for one block, source/operator/q-right/feature-state/denominator consistency result, explicitly scoped rejection examples, counts of admissible/non-admissible rows and hash-only provenance. Where legal/technical identity cannot be established, output `NOT_ESTIMABLE` with precise cause. Do not publish per-cell raw counts or use these data for fitted models, query-specific biological validation, teacher target choice or representation comparison.

**Stop after one block.** If the single-block path passes mechanics tests, publish the exact-head receipt and request independent review before any expansion. This approval is not a second read authorization for new blocks, donors, source strata or validation folds.

## 3. Responsibilities and persistence

- **Macha:** choose the one eligible block using **metadata only**, produce frozen source-bound preflight identity and original data/custody receipts on GPU laptop; reuse already-acquired ETL and QC artifacts; execute one-block test only after predeclared identity and software gating. No repeat global ETL.
- **GPT:** audit the binding, reuse accepted producer→artifact→executor→verdict architecture (#379), make only the minimal versioned real-path CaseBundle/rights adapter necessary, author hostile tests, and independently review Macha's output. Neither agent claims independence for its own results.
- **Independent review:** original RED tests, source hashes, exact PR head, test CI, explicit `NOT_ESTIMABLE` and scientific scope required; do not claim a trained JEPA or real target was qualified.
- **Owner delegation resolved:** no additional owner question is required for these two **specified** scopes. Any *wider* scope, additional matrices or NPH52 quarantined expression requires a separately documented decision.

## 4. Source references

- [Macha #528](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/528), head `1a4fda758936a3cc3868948b44d25694de216bd9`: `docs/agent/JEPA_MACHA_528_PUBLIC_SOURCE_PROVENANCE_ERRATUM_20261103.md` §6 proposed the exact QC-only field allowlist; `scripts/v5/review_probes/macha_20261103/specimen_qc_input_admission_v1.py` preserves `REPLAY_HOLD`; original R01/R02 repaired in scoped independent review, 24/24 Ubuntu/Windows tests.
- [Source #513](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/513) original `0b1af4f06ba423753899e7c564d3b16ce609ac6a`, `JEPA_MACHA_SPECIMEN_AND_DEPOSITOR_QC_20261030.json`; `#528` correction withdraws overclaims about physical HVS molecules, no depositor selection independence established.
- [Audit #322](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/322) source-to-CaseBundle gap and [handoff #460](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/460) current takeover; #531/532 and #533 remain bounded independent review/terminal selection work.
- Source terms: SEA-AD Allen Terms/Citation; HVS public CELLxGENE processed deposit; NPH52 Zenodo 8319719 CC-BY-4.0. This decision does **not** change any source/provider term or raw-data access rule.

**Authority unchanged:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
