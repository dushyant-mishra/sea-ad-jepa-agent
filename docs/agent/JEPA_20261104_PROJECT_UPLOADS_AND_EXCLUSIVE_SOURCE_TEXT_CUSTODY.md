# User/project-exclusive JEPA source assets and verbatim text preservation — 2026-11-04

The current JEPA Project has **11 mounted source attachments**. All eleven exact original SHA-256 and size identities are saved in `results/target_discovery/unified_qualification_v1/JEPA_20261104_PROJECT_LOCAL_ASSET_SHA256_CUSTODY_V1.json`. Project attachments should be accessed by original filename and SHA, not by the session-local `/mnt/data` path. The original 1.3 GB of binaries are NOT repackaged into GitHub, to avoid copying heavy datasets/checkpoints, losing local custodial provenance, or reclassifying 50K expression as the actual 4.55M FULL104 physical source.

## Original uploaded text documents preserved in GitHub

| Original uploaded project text | Original SHA-256 | GitHub text copy on audit branch | Scientific classification |
|---|---|---|---|
| `Status and Repair Plan.txt` (101 lines) | `cb2befc374e4b594fb6d04bbb7c30a0ca702913ddc9d568fbfbf8ebca7bb7c56` | `docs/agent/archive/user_supplied_evidence_20261104/SEPT12_DATASET_FIRST_V5_STATUS_AND_REPAIR_PLAN_20260912.txt` | Original September12 V5 repair / dimension plan, **superseded in the precision-gate details** by PRs #270/#273/#274. Preserved as historical, not an active gate |
| `WSL execution issue.txt` (661 lines) | `cd1c50bbec4c80b9b35f1824bba9112c7dbb357ede586b0a46e98532f57e474e` | `docs/agent/archive/user_supplied_evidence_20261104/ORIGINAL_WSL_TECHNOLOGY_AS_OBSERVATION_OPERATOR_NOTE_20260811.txt` | Original conceptual proposal on technology as observation operator and preserving biology vs measurement uncertainty. Later FHRA/Foundation V4 supplied actual empirical test; this is **not** an executed independent result |

These two original text files were imported from the Project file source using the text-read facility, with an exact **GitHub round-trip equality check** against the fetched copy after write. Their original binary attachment SHA-256 are recorded separately (a GitHub text copy may differ at the byte/encoding level after provider text extraction; no binary-equality claim is made).

The separately mounted `Pasted markdown.md` has original source SHA-256 `9f3059039a0afca8a135a353ed6f0acf2606a88c5b68a76663c35ded3071e1e7` and 12,832 bytes. It is a historical work-status/priority summary, **not** a new primary experiment; its contents are summarized under PR #525/#533 source review, real source→CaseBundle and V80-law priorities in the master handoff. A verbatim GitHub copy was **not** created because its File-source backing was not surfaced by the Project search in this turn. The Project attachment remains authoritative for those original bytes.

## Exact mounted archives

The machine asset manifest includes the August calibration archive, two original 41K expression parts and original part-hash ledger, `expression.zip`, `checkpoints.zip`, `t1_checkpoint_u0200.zip`, and `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`. ZIP central-directory member counts were recorded without tensor reads. In the original foundation calibration archive, `BUNDLE_STATUS.json` reports 97 underlying manifest files and no dev/sealed expression; this differs from its 60 ZIP *entries* due to archive layout, **not** a contradiction in source custody.

**Newly recovered historical receipts inside calibration archive:**
- Original `FOUNDATION_TEACHER_SHORTCUT_ATLAS.md` reports u0→u205 source/operator/support probe median delta **zero** and continuous biology median delta **−0.0002308**. This is historical descriptive evaluation on real heldout TRAIN donors.
- Original `SYNTH_BALANCED_VS_EMPIRICAL_ADJUDICATION.md` terminal `MECHANISM_STRESS_ONLY_NOT_PRODUCTION_TRAINING`: empirical-minus-balanced factor R² `−0.02488698065`, operator BA `+0.18132440476`, biological change from u0 balanced `+0.0012166947` vs empirical `+0.0208621621`.
- Original `FOUNDATION_GEOMETRY_REVIEW.md` warns that a single integrated UMAP does not separate biology from source/operator/donor/support and the old 3,292-cell cache is compositionally distorted. It called for pre-frozen donor-block/source-aware graphs and did **not** claim the physical expression analysis was executed by that original report.

These historical findings were **already tested and/or reviewed at their original scope**. Their discovery in the current ZIP inventory is **not permission to claim new biological results**, restart u0/u205, rerun Stage81B 500 steps, or use old checkpoint tensors as a current EMA teacher.

## Source provenance and no-repeat rules

- All original data ZIP, NPZ and PyTorch checkpoint bytes remain in Project/GPU custody, with original names and SHA identity. Future agents can use exact attachment matching and existing Macha physical receipts, never infer stable storage from `/mnt/data`.
- **Do not re-download or reconstruct 50K expression or stage81a3 calibration** unless an explicit source integrity contradiction is demonstrated; PR #492 already verified 97 member SHA and inverted 246,702,069 log nonzeros.
- **Do not claim the Project archive is the 4,553,407-cell / 8,915-block physical FULL104 store** or a production dimension metric receipt; the latter has its own binder and numerical authority protocol.
- Avoid committing large original binary data/checkpoints to GitHub by default. A future scientifically required source value uses the existing authenticated GPU-local data/reader and returns compact provenance-binding metrics, not raw expression.
- Source/model PII, pathology, TEST/Morabito and production teacher access remain separated under existing original producer/split rules.

**Classification:** `ORIGINAL_PROJECT_ASSETS_HASHED__TWO_ORIGINAL_TEXT_NOTES_COPIED_AND_ROUNDTRIP_VERIFIED__BULK_BYTES_NOT_DUPLICATED__NO_NEW_SCIENCE`.
