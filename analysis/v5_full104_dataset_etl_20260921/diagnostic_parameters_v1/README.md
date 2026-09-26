# FULL104 physically rederived metadata parameters — read-only development package

Scope: **PHYSICAL_METADATA_ONLY / NO_TRAINING_AUTHORITY / NO_PROTECTED_OUTCOMES**. This is a local independently audited companion package; it does not supersede the project's existing frozen authorities and has not been merged into any GitHub branch. It uses the **original August 24 calibration ZIP and its original 2.7 GB SQLite member**, not the 94-donor historical analysis or synthetic 50k cells.

## Inputs actually inspected

- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`, 410,278,055 bytes, SHA-256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`.
- Member `metadata/foundation_metadata_rows.sqlite`, 2,709,786,624 uncompressed bytes, SHA-256 `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`.
- Exact member-manifest-authenticated fit donor census, 149-reader donor split, foundation source/partition registry, operator support and 41,238-address recurrence tables. The independent checker pins every exact source-root hash.
- SQL reads are metadata only (`partition`, `source`, `donor_id`, `operator_index`) and do not query expression, pathology, N1 or sealed dimension outcomes. Validation/oracle outcomes are unopened; only partition/source **metadata counts** are included.

## Derived evidence

- 104 reader-fit donors, 4,553,407 cells, 42 operators; HVS 41 donors / 198,718 cells; NPH52 17 / 236,476; SEA_AD 46 / 4,118,213.
- 1,400 donor×operator nonempty groups; 1,361 have at least 3 cells, covering 4,553,348 cells. Group capacities are **mathematical counts of available ordered-anchor/unordered-comparator triplets**, not selected training triplets or independent biological replicates.
- 81–174,111 cells per donor; `81` is an **upper bound on unique cells within a single update under the PR135/PR139 proposed sampling law**, not a selected batch size or training authority.
- 17,186 addresses measured by **every one of the 42 operators**; 17,346 measured by at least one operator in **each source**; 289 measured by none. Do not conflate the two core definitions or treat collisions and structural unmeasurement as observed zero.
- Per-donor base JEPA weights `1/(104*n_d)` over actual reader-fit cells, exactly normalized to 1. This is distinct from D1-P002 program-discovery weights `1/(104*|O_d|*n_do)` where `O_d` are donor d's observed operators; both sets are included and independently checked, never interchangeable.
- G3 source/fit-donor map is now physically present in readable output, but **the CUDA-laptop V5 donor integer-code map, live G3 six-state scorer and byte-bound full expression remain separately unintegrated**.

## Outputs

- `FULL104_AUTHENTICATED_READER_FIT_METADATA_PARAMETER_RECEIPT_V1.json`: source roots, independent census and support summaries, explicit deferred-parameter list and `training_authorized=false`.
- `fit104_donor_scientific_masses.csv`: 104 exact source-joined donor counts, base JEPA rational weights and normalized decimal display.
- `fit104_operator_token_support.csv`: all 42 source/identity-bound measured/missing/collision token counts.
- `fit104_donor_operator_relational_capacity.csv`: all 1,400 real metadata groups, exact triplet capacity, and separate D1-P002 rational mass columns.
- `OUTPUT_SHA256_MANIFEST.json`: immutable per-output content hashes; scripts and test cases in the package.

## Repeat or audit

```sh
# First, independently authenticate and extract SQLite member from the original zip.
# The producer rehashes both the original ZIP and the extracted SQLite member.
python derive_full104_diagnostic_metadata_v1.py \
  /path/to/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip \
  /path/to/extracted/foundation_metadata_rows.sqlite \
  /path/to/empty/out_dir

python verify_full104_metadata_receipt_v1.py /path/to/out_dir
# For the packaged original outputs:
PYTHONPATH=. pytest -q test_full104_diagnostic_metadata_v1.py
```

Tests include deliberately forged 94/small sample substitute, source/heldout leakage, extra donor, wrong weights, old 40% mask inserted as if qualified, numeric D_shared=160, false training/protected claims, group triplet errors, collision-state collapse, wrong support universe, source root substitution and denominator confusion. Attacks first recompute the output SHA manifest to test semantic gates **beyond** simple file hashing. Zero tests skipped.

**Not inferred or authorized:** model width/depth/heads, mask fraction, masking-policy success, EMA half-life, optimizer learning rate, token microbatch memory ceiling, training presentation horizon, healthy teacher state, D_shared/D_private/D_obs, D1 stable program rank, protected or external biological truth. Machine-readable parameter declarations are metadata-bound evidence, NOT a production model configuration or permission to run GPU training. All extracted heavy SQLite and original ZIP bytes are deliberately excluded from this portable package.
