# V26 independent reader-fit population audit — CPU/metadata only

Date: 2026-09-25. Status: **READ-ONLY PHYSICAL METADATA VERIFIED; FULL104 RAW/CELL/PROPOSAL NOT VERIFIED; TRAINING OFF**.

This is a narrow independent successor to the V26 PR #123 handoff and stacked on the PR #129 optimizer-hook fix. Do not merge the stacked implementation branches blindly or treat passing synthetic tests as a physical full-data outcome.

## Exact authenticated inputs and independent observations

The physical `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` available in this conversation was streamed through SHA-256 independently of the existing V26 manifest. Observed size **410,278,055 bytes** and SHA-256 **07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444**, exactly matching PR #123's recorded binary inventory. The following are the **only** two members needed by the new preflight:

| ZIP member suffix | Physical bytes | Verified SHA-256 |
|---|---:|---|
| `/splits/reader_donor_split.csv` | 3,589 | `efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511` |
| `/metadata/FOUNDATION_METADATA_DONOR.csv` | 2,129 | `c9cbe47d4727aabec8a0c3fed5474c2dab4f9f2b8848357e08b0cec6ef044508` |

Physical read-only checks on these small metadata files established **149 distinct** reader donor IDs: `reader_fit=104`, `reader_validation=22`, `reader_oracle=23`. The 104 metadata donor IDs equal the 104 `reader_fit` IDs exactly and intersect neither closed reader partition. Sum of `cell_count` across the 104 metadata rows: **4,553,407**. Additional independent fingerprints over the data: SHA-256 of sorted reader-fit IDs with terminal newline = `9332e77c71769f5084e6c94afc9c1aa825f369fe08c8b25bb70682d981d8e977`; sorted `donor_id<TAB>cell_count<LF>` = `b2da4aa99c66df435497cf52059c35c11f548b0c7771cb101eee9a6ff14de875`. No donor IDs are committed in this change or printed in the public receipt.

The frozen foundation split registry, a **third** metadata file, independently matches recorded SHA-256 `35afb7f53fa36d580a4552dd5ad7e59841e454ea85d4adcb761666cb20d05433` (215 rows with 149 foundation/train, 17 continuation/train and the separate development/holdout rows). **Direct equality join of reader `donor_id` with foundation `canonical_person_id` produces zero matches on these archived CSVs**. These are not interchangeable identifiers; do not silently coerce them or infer that the populations are biologically disjoint. A separately authenticated identity bridge and the frozen population-authority proof are required to make the foundation-to-reader nesting claim independently executable from this archive. The new verifier deliberately does not attempt that unqualified join.

## Implementation and red-team boundary

`src/sea_ad_jepa/v5/reader_fit_population_preflight_v1.py` independently SHA-checks the whole ZIP first, then opens only the two allowlisted, bounded-size metadata CSVs. It verifies exact byte and derived membership/count hashes, strict CSV schemas, distinct partitions and identities, counts, disjointness and the exact scientific target mass `p_i = 1 / (104 * n_d)` with Python rational arithmetic. It returns no raw donor IDs. The **private structural-only test helper never emits a frozen-source receipt**: a self-audit caught and fixed an earlier false-green labeling path before review. An authoritative metadata receipt is returned only after both the archive and member byte checks pass.

`tests/test_v26_reader_fit_population_preflight_v1.py` and `.github/workflows/v26-reader-fit-metadata-preflight.yml` fail closed on fake identities, oracle substitution, extra continuation donors, duplicate keys, edited counts/headers/partitions, synthetic ZIP spoofing, malformed fields and synthetic status inflation. CI uses an exact named test census and rejects skipped tests. CPU/synthetic test success is **not** full input qualification.

## What remains excluded

- **No FULL104 raw-block reaggregation or per-cell source/donor lineage verification.** The metadata's cell count matching 4,553,407 is a consistency check, not proof of an authentic Level-4 read.
- **No sampling proposal `q_i` authentication.** An exact `p_i` computed for a **claimed** donor is a conditional arithmetic identity, not permission to apply `p_i / q_i` to unverified cells.
- **No target, masking, geometry, EMA, initial/resume cursor, optimizer parameter movement or checkpoint integration authority.** Do not pass this receipt to `CurrentTrainingAuthorityV1` as a substituted upstream closure or use this code as a data loader.
- **No expression, pathology, `reader_validation` outcomes, `reader_oracle` outcomes, foundation development/holdout or Siletti study data were opened.** Reading partition *metadata* does not spend the held-out *outcomes*.
- The unidentified NPZ with observed `001375ec...` remains quarantined; neither historical T1 checkpoints nor the smaller TRAIN cache are eligible FULL104 proxies.

Next CPU boundary: fail-closed **diagnostic source adapter** must bind per-cell keys/donors and proposal `q_i` to the authenticated 8,915-block FULL104 manifest and the exact source SHA. Run only under a separately approved DEVELOPMENT diagnostic contract. In a separate step, prove the current V5 update/EMA/atomic-checkpoint chain without importing V4 production defaults. Keep Claude's physical N1 and perturbation lanes independent; their receipts do not grant this diagnostic's training permission.
