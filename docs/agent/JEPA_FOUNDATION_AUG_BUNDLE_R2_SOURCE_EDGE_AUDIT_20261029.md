# August Foundation source-edge audit — collision masks and conditional normalization

**Date:** 2026-10-29. **Evidence:** read-only local execution over the user-uploaded historical FOUNDATION_CALIBRATION_BUNDLE_20260824.zip, exact archive SHA-256 07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444. This is not a present TRAIN source issuer or qualified biological target.

## Method and custody

The standalone scripts/v5/td_unified/audit_foundation_bundle_edge_v1.py reads only aggregate/status/manifest/address/measurement/collision contracts and archived loader code. It checks the archive status-manifest hash, exact SHA/size of relevant members, and the combined state law. It does not materialize expression values, sample-level phenotype or protected metadata; no BAM/FASTQ downloads.

Original loader SHA-256: 267fa42a5fa6f8b5f8199c68add1ffe0c8b49142095b7d980d1af27a8a31154a. Archive manifest SHA: da7c3daf507a66118131e88ae6685cf43eb14d4163539ade5e0705f6fb845cef. Machine receipt: results/target_discovery/unified_qualification_v1/JEPA_AUG2026_FOUNDATION_R2_BUNDLE_EDGE_LOCAL_AUDIT_20261029.json.

**Scope:** full archive execution is a LOCAL uploaded-asset run, not hosted GitHub real-data execution. GitHub CI tests only the synthetic auditor code. SHA proves byte identity, not physical or source authentication.

## Result 1 — historical collision-mask law confirmed

- 41,238-address namespace; 42 matrices; 1,731,996 matrix/address support records.
- Main ledger: 24,525 source-feature rows, 11,435 unique matrix/address collision pairs.
- Supplemental unregistered collision CSV: 14 further distinct pairs (28 source-feature rows) across seven NPH52 matrices. Zero overlap with the main ledger.
- All 14 supplemental addresses are marked measured in the pre-mask support table. That status alone is NOT proof of scalar-materializability.
- The archived loader explicitly unions main+supplemental blocked pairs, assigns measured scalars first, then overrides blocked addresses to MEASURED_COLLISION_UNRESOLVED. Thus all 11,449 combined collision pairs are unresolved in this archived contract. Final state counts across the 1,731,996 pairs: MEASURED_SCALAR 1,061,903; STRUCTURALLY_UNMEASURED 658,644; MEASURED_COLLISION_UNRESOLVED 11,449.
- The result corroborates the historic 11,449 collision-pair count at CONTRACT scope, not complete physical source-feature alias closure. Removing a supplemental entry can silently turn its pair into apparently scalar if no independent source-feature census reveals the omission. R2 remains RED.

## Result 2 — archived full-library normalizer is not query-excluded by construction

The archived production_train_loader.py reads local.source_library and calculates:

    normalized = log1p(10000 * raw_count / max(source_library, 1))

If queried mass contributes to source_library, base-visible raw counts held constant do NOT imply invariant normalized base values. Executed synthetic conditional witness: base=3, q=7 versus q=100, denominator=base+q. Base log1p(CP10K) changes 8.0067008454 to 5.6776511253. This is an algebraic test, NOT an observation of a particular human cell, and does not prove actual source_library contains that queried molecule.

**Implication:** historical log1p(CP10K) values, even when structural masks are correct, cannot automatically be reused as prospective V2 base-visible raw-count-sum normalized student evidence. Require independent source_library, QC selection, raw-count, alias and physical-unit derivations. Do not infer raw-count provenance from log1p inverse or matching SHA.

## Naming separation, bounds, next work

Prospective V2 normalization D1 is the base-rights-visible raw measured sum. It is NOT the unrelated historical v4 D1 representation-dimension estimator in scripts/v4/d1_real_data_derivation_core_v1.py. Neither changes physical V1/G7 library_size.

Not established: independent physical nucleus R1, donor/specimen R1D, source feature/alias census R2, q-independent QC/source denominators, actual raw-count shard execution, calibration/source issuer, same-nucleus RNA/ATAC, sealed known-truth biology or target selection.

Next source actions: (1) obtain authorized per-query/operator raw-source feature census and unresolved alias crosswalk; (2) qualify physical source_library and depositor QC selection; (3) crosswalk physical nucleus, specimen and donor from authorized evidence rather than strings or SHA; (4) have Macha repair #474 A4 and independently review #502/#503; (5) only then build/review true G7 E3 V2 with a separate physical-total and D1 depth contract. Do not re-interpret legacy library_size or implement PS Task4 training before source/known-truth gates.

**Verdict:** HISTORICAL_COLLISION_MASK_MECHANICS_CONFIRMED__QUERY_DENOMINATOR_RISK_CONDITIONAL__SOURCE_CLOSURE_UNQUALIFIED.

**Authority:** TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED.
