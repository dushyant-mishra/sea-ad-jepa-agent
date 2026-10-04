# V67 Claude data/source map for auditing ChatGPT work

## Purpose

This map distinguishes:
1. repository-resident authorities Claude can audit directly;
2. local scientific artifacts referenced by current Stage-4 custody;
3. files physically available in the ChatGPT project environment but **not** ordinary Git files;
4. historical/supporting files that must not be silently promoted to current authority.

Do not infer that a local file is available in Claude's runtime merely because it exists in the ChatGPT project environment.

## A. Current repository-resident authority sources

Audit these directly from Git:

- Phase-A V3 receipt and rows
- Phase-B measurement-substrate contract
- Phase-B substrate aggregate and closeout receipts
- B6 T3/T4 availability v2 receipt
- R3 conditioning reference
- enumeration intervals
- frozen correspondence design contract
- frozen downstream-null/statistical V3 contract
- Stage-3 feature artifact contract V2
- unmodified E2 continuous-adjustment estimator

Current B6 v2 identity:
- Git blob: `29c248ded42aecd35650699c360512e965ce9345`
- raw SHA-256: `2fd8356b07fd3d4e50007c941fcc8bcdda4a118509775955ded82d90b98ed671`

## B. Current local scientific artifacts referenced by Stage-4 authority

These are external/local scientific binaries, not normal Git blobs. A future execution audit must hash the actual bytes at their local paths.

- eight `PHASE_B_SUBSTRATE_s00.npz ... s07.npz`
- `PHASE_B_T5_DONOR_AGGREGATES.npz`
- `PHASE_B_T3_T4_AVAILABILITY.npz`
- pairing permutation `atac_to_rna_row.npy` — currently corroborative provenance in Claude's authority
- NIH-CARD consensus peak/input material already bound by accepted Phase-B receipts

Use the exact paths/digests from the audited Stage-4/Phase-B authority artifacts. Do not replace these with similarly named copies.

## C. Files physically present in the ChatGPT project environment

These were available to ChatGPT during this project chat. They are **not automatically available to Claude** and are not all current-authority inputs.

| file | bytes | SHA-256 | status / relevance |
|---|---:|---|---|
| `WSL execution issue.txt` | 14,576 | `cd1c50bbec4c80b9b35f1824bba9112c7dbb357ede586b0a46e98532f57e474e` | architecture note used conceptually for observation-operator / invariance / basis-stability / evidence-vs-measurement reasoning; supporting text, not a current scientific result |
| `Status and Repair Plan.txt` | 5,233 | `cb2befc374e4b594fb6d04bbb7c30a0ca702913ddc9d568fbfbf8ebca7bb7c56` | historical V5 dimension-authority/production-closure status; historical only unless a current claim explicitly descends from it |
| `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv` | 437 | `fd003bc8f2f34ac856791dfcf6b0e3b7d81eddfffb8b256d23c3e4a5d40f3356` | custody manifest for split discovery-expression archive |
| `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001` | 303,979,881 | `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e` | large historical/foundation expression asset; not used in the current Stage-4 synthetic work |
| `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002` | 303,979,880 | `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875` | second archive part; same status |
| `checkpoints.zip` | 71,356,460 | `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c` | checkpoint bundle; not used to generate current Stage-4 authority or V67 synthetic results |
| `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` | 410,278,055 | `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444` | historical foundation calibration bundle; do not promote without explicit lineage |
| `expression.zip` | 3,599,456 | `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4` | expression artifact bundle; not used in current V67 synthetic qualification |
| `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` | 1,531,109 | `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70` | local NPZ; not used in current Stage-4/synthetic work unless separately proven by lineage |
| `t1_checkpoint_u0200.zip` | 233,729,581 | `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c` | historical checkpoint; not a current authority input |

The split-archive manifest additionally states the reconstructed archive:
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip`
- expected bytes: 607,959,761
- expected SHA-256: `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

Claude should not claim to have audited the contents of any item in section C unless those bytes are actually made available in Claude's execution environment.

## D. What ChatGPT actually used for the V67 synthetic work

The new V67 synthetic tests were generated from deterministic synthetic data inside the committed Python producers. They did **not** read any of the large local archives/checkpoints listed above.

Specifically:

- `nested_modality_mask_uncertainty_anticollapse_synthetic_v1.py` uses seeded NumPy-generated synthetic donors/RNA/ATAC/state.
- `heldout_source_observation_operator_synthetic_v1.py` uses seeded NumPy-generated source families and planted capture coefficients.
- no NIH-CARD real matrices were opened;
- no Morabito data were opened;
- no TD60/protected outcomes were opened;
- no recoverability TEST donors were opened;
- no real JEPA training was run.

Therefore Claude should audit these synthetic experiments from their source code, tests and CI, not by searching for hidden real input data.

## E. Conceptual source used by ChatGPT

`WSL execution issue.txt` materially informed the architecture reasoning used here. It argues for:

- technology as an observation operator rather than a biological covariate;
- invariance to measurement realization/technical noise while retaining genuine biological variation;
- basis/subspace stability checks before coordinate-specific uncertainty claims;
- separate biological-evidence and measurement-quality uncertainty curves.

These are conceptual design inputs only. They do not provide numerical biological authority.

## F. Historical source that should remain historical

`Status and Repair Plan.txt` documents older V5 FULL104/dimension-authority work, including the historical principle that TRAIN-cache evidence must not be promoted to FULL104 authority and that dimensions require full-stream execution plus prospective Monte-Carlo precision authority.

Use it to detect historical spillover if helpful. Do not treat its old open blockers or branch state as the current V67 execution state.

## Audit rule

If Claude needs a binary from sections B or C to verify a claim and cannot access the exact bytes, report:

`NOT BYTE-AUDITED IN CLAUDE ENVIRONMENT`

rather than reconstructing, substituting, or inferring the file.

Do not request or open protected outcome data merely to make the audit more complete.
