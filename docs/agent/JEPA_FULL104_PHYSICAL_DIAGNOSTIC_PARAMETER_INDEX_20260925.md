# FULL104 physical diagnostic parameter evidence — current navigation and use boundary

**Evidence date:** 2026-09-25 (local study); **GitHub publication:** 2026-09-25/26 UTC. **Status:** `PHYSICALLY_AUTHENTICATED_METADATA_ONLY__TRAINING_OFF__NO_PROTECTED_OUTCOMES`. This is a self-contained evidence package on a **draft, separately reviewable branch** based on main `c49b13bd75c2d23716c777336db8fbfc78c09cd0`; do not mistake a draft branch for merged current-V5 model or training authority.

## Start here

The complete, readable version-controlled evidence and replay package lives at

[analysis/v5_full104_dataset_etl_20260921/diagnostic_parameters_v1/](../../analysis/v5_full104_dataset_etl_20260921/diagnostic_parameters_v1/README.md).

Everything except the original ~410MB calibration ZIP and expanded ~2.7GB SQLite is published **as individually inspectable files**, rather than only as a local ZIP:

| File | What to use it for |
|---|---|
| [Physical receipt](../../analysis/v5_full104_dataset_etl_20260921/diagnostic_parameters_v1/FULL104_AUTHENTICATED_READER_FIT_METADATA_PARAMETER_RECEIPT_V1.json) | Exact source roots, all census and support findings, deferred parameters and non-training status. |
| [104-donor scientific masses CSV](../../analysis/v5_full104_dataset_etl_20260921/diagnostic_parameters_v1/fit104_donor_scientific_masses.csv) | Actual donor IDs/sources/counts, exact rational base JEPA weights `1/(104*n_d)` and donor observed-operator count. |
| [42-operator token support CSV](../../analysis/v5_full104_dataset_etl_20260921/diagnostic_parameters_v1/fit104_operator_token_support.csv) | Actual matrix IDs/source/cell counts and distinct scalar/missing/collision support per operator. |
| [1,400 donor×operator capacity CSV](../../analysis/v5_full104_dataset_etl_20260921/diagnostic_parameters_v1/fit104_donor_operator_relational_capacity.csv) | Physical group counts, exact combinatorial anchored-triplet capacities and separately labeled D1-P002 `1/(104*|O_d|*n_do)` weights. |
| [Original physical derivation script](../../analysis/v5_full104_dataset_etl_20260921/diagnostic_parameters_v1/derive_full104_diagnostic_metadata_v1.py) | Read-only regeneration from **authenticated original August 24 bundle AND expanded original SQLite**, plus authenticated donor split/registry and operator-support members. |
| [Independent output verifier](../../analysis/v5_full104_dataset_etl_20260921/diagnostic_parameters_v1/verify_full104_metadata_receipt_v1.py) | Strict content SHA-256 and semantic cross-file arithmetic/identity checks; does not substitute for original source authentication. |
| [24 adversarial tests](../../analysis/v5_full104_dataset_etl_20260921/diagnostic_parameters_v1/test_full104_diagnostic_metadata_v1.py) | Fail even after rehash on fabricated source/donor/weight/support/relational rows, small-run or synthetic-rank substitution and false authorization. |
| [Exact four-output SHA-256 manifest](../../analysis/v5_full104_dataset_etl_20260921/diagnostic_parameters_v1/OUTPUT_SHA256_MANIFEST.json) | Durable byte identity of the three published CSVs and original physical receipt. |
| [Original read-only run log](../../analysis/v5_full104_dataset_etl_20260921/diagnostic_parameters_v1/physical_run.log) | Local producer's original concise physical completion record, not a GitHub-hosted source-input replay. |
| [Fail-closed GitHub Action](../../.github/workflows/v26-full104-metadata-parameters.yml) | Independently replays *the committed exported evidence* on GitHub's runner and requires exactly 24 executed tests with zero skips. |

Every published original package file above was independently compared to its local `git hash-object` **after GitHub upload**, including CRLF CSV endings; all ten source blobs were exact. This avoids the six-decimal/serialization false-green failure seen in other lanes.

## Physical input roots (reference, **not** duplicated in Git history)

- Original `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`: **410,278,055 bytes**, SHA-256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`.
- ZIP member `metadata/foundation_metadata_rows.sqlite`: **2,709,786,624 bytes** expanded, SHA-256 `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`.
- Exact authority member roots: `source_roots` of the receipt. The 149-person registry, 104-fit donor count authority, operator support and address recurrence are independently cross-joined. Nonfit validation/oracle *partition and source metadata counts* were inspected; their expression, pathology, biological outcomes, and sealed dimension data were **not** opened.

## New physically derived outputs

- 104 fit donors / 4,553,407 fit cells / 42 operators: HVS 41 donors / 198,718 cells; NPH52 17 / 236,476; SEA_AD 46 / 4,118,213.
- 1,400 authentic donor×operator groups; **1,361** have at least 3 cells, collectively **4,553,348** cells. These are *available* mathematical triplets, not sampled triplets or independent replicates.
- Per-donor cells range 81 to 174,111. **81** is a conditional maximum *unique* presented-cell count for PR135/139's exact proposed sampling law when every donor must support within-update no-replacement, not an authorized GPU batch size.
- 17,186 strictly scalar-measured addresses in **all 42 operators**, versus 17,346 measured by **at least one operator per source family**. 289 measured by none. Structural absence and collision unresolved are never treated as measured zero.
- Exact per-cell base-JEPA scientific weight `p_i=1/(104*n_d)`, versus distinct D1-P002 donor/operator/cell analytical weight `a_i=1/(104*|O_d|*n_do)`. Both rationals cross-sum to 1 under their own estimand; **do not mix them**.

## Independent historical context and no-spillover ownership

This work **extends but does not redo** the September 21 FULL104 SQL/atlas ETL [reproducibility receipt on the original experimental ETL branch](https://github.com/dushyant-mishra/sea-ad-jepa-agent/blob/analysis/perturbation-etl-gse301119-claude-20260923/analysis/v5_full104_dataset_etl_20260921/FULL104_DATASET_ETL_REPRODUCIBILITY_RECEIPT_V1.json) (11 SQL files and 13 generated atlas outputs byte-identical in its own source lineage). The earlier ETL is a design input and **not a model-input authority**. Current draft PR #142 separately authenticated the 149-reader donor source cross-tab; draft PR #132 is the independent frozen-pass1 bridge; PRs #135/#139 own actual sampler mechanics. Draft PRs #143/#144 own G3 fit-law mechanics; PR #145 owns the **provisional** diagnostic parameter firewall. This package *only* owns newly derived metadata/rational weights and their physical provenance. Do not cherry-pick or silently merge unrelated, partly divergent branches.

### Reproduction on the local authorized data drive

```bash
cd analysis/v5_full104_dataset_etl_20260921/diagnostic_parameters_v1
python derive_full104_diagnostic_metadata_v1.py \
  /absolute/path/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip \
  /absolute/path/extracted/foundation_metadata_rows.sqlite \
  /absolute/path/new_empty_output_directory
python verify_full104_metadata_receipt_v1.py /absolute/path/new_empty_output_directory
python -m pip install pytest
python -m pytest -q test_full104_diagnostic_metadata_v1.py
```

The code explicitly pins the **original** bundle and SQLite hashes, and emits STOP if the source/cell/feature lineage differs. Committed-output GitHub CI independently verifies existing published files; it cannot rehash the original heavy ZIP absent from the runner.

## Hard scientific limits

**Nothing in this package** selects the model's width/depth/heads, mask fraction, EMA half-life, learning rate, masked views, total presentation horizon, D_shared/D_private/D_obs, stable D1 program rank, or actual V5 checkpoint. Source-/operator-specific support is not causal proof that observed variation is technical. No terminal N1, D_shared, protected validation/oracle, foundation sealed, Siletti or pathology outcome was opened; no training was run or authorized. The live V5 GPU entrypoint is **not wired** to this receipt yet. A separate reviewed, byte-bound execution adapter must map the current V5 donor integer codes to these exact canonical donor IDs and independently authenticate the frozen pass1/split/support sources before consumption. Any new held-donor development split changes the active training donor set, requiring recalculated weights over that selected set (do not blindly keep denominator 104).
