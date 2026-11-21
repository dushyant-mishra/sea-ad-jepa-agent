# Macha #528 erratum: public source provenance, access tiers, re-classified requirements — 2026-11-03

This file is append-only. It corrects `JEPA_MACHA_SOURCE_QUALIFICATION_CORRECTION_20261103.md` (#528 `c1d85688`) without editing it.

Machine-readable companion: `results/target_discovery/unified_qualification_v1/JEPA_MACHA_528_PUBLIC_SOURCE_PROVENANCE_ERRATUM_20261103.json`.

## 1. What I got wrong
§3 of the correction said three things that the project's own acquisition records contradict:
- **NPH52:** "release metadata not supplied" and "accession and terms unknown".
- **HVS:** "no terms record found".
- **R1–R3 and R8:** worded as if a hardware signing key or new institutional authorization were needed before public data could be used.

I relied on a later identity-audit sentence and keyword searches. I did not read the Stage81A1D acquisition records, which are the authority:
- `configs/v4/stage81a1d_living_human.yaml`
- `scripts/v4/stage81a1d_acquire_living_human.py`
- `results/v4/stage81a1d_living_human_dataset_role_registry.csv`
- `results/v4/stage81a1d_living_human_remote_asset_catalog.csv`
- `results/v4/stage81a1d_living_human_download_hashes.csv`

## 2. Public source provenance
Taken from those records, plus public record metadata fetched on 2026-11-03. The snapshots are committed under `results/target_discovery/unified_qualification_v1/public_source_metadata_20261103/`.

| Source | Public record | Version | Terms | Acquisition integrity |
|---|---|---|---|---|
| SEA-AD | Allen Institute SEA-AD Open Data on AWS (`stage81a1b_remote_asset_catalog.csv`: 17 `open_aws` rows and 1 `local_historical` row) | per-object `last_modified` and ETag in the catalog | Allen Institute Terms of Use and Citation Policy (catalog `terms_or_license_reference`; pinned `SEA_AD_Multiregion_2026_README.md`) | `stage81a1b_download_hashes.csv` and `stage81a1b_download_events.jsonl` |
| HVS | CELLxGENE collection `35928d1c-36fc-4f93-9a8d-0b921ab41745`, PUBLIC, published 2024-08-05, revised 2026-06-11; Johansen et al. 2023, doi 10.1126/science.adf2359 | 24 datasets, each with a dataset ID and a version ID (Stage81A1D catalog) | CELLxGENE Discover public deposit. The curation-API payload carries no licence field. | 24/24 rows in `stage81a1d_living_human_download_hashes.csv` with a local SHA-256. CELLxGENE publishes no official checksum. |
| NPH52 | Zenodo record **8319719**, **revision 2**, `access_right: open`; Gazestani et al.; related doi 10.1101/2023.06.03.543569 | revision 2 (registry `source_version=2`) | **CC-BY-4.0** (Zenodo record metadata) | `organized_data.zip` md5 `3aa418e4…` and `annotations.zip` md5 `0981c257…`, both `official_checksum_pass=True`; local SHA-256 `f1d485e8…` and `0e2038d8…` |

## 3. Public processed data versus controlled raw releases
**Public, processed, acquired.** SEA-AD, HVS and NPH52 were acquired as public processed data. Stage81A1D policy sets `processed_data_only: true` and forbids `.fastq`, `.bam`, `.cram` and `.sra` files.

**Controlled raw, not acquired.** The Stage81A1D Synapse audit (`stage81a1d_living_human_synapse_access_audit.csv`) lists 5,005 AD Knowledge Portal objects:
- 4,981 are `raw_or_prohibited`, mostly FASTQ;
- 23 are metadata or processed candidates;
- 1 had no metadata available.

Access is unresolved for all of them. None is `required_for_stage81a1d_pass`, and none was acquired. Raw reads stay prohibited by project policy whatever their access tier.

## 4. Requirements re-classified
This replaces the R1–R9 status column in the correction's §3.

| # | Requirement | Corrected class | Status |
|---|---|---|---|
| R1 | Independent signer key | **Optional governance hardening** (internal agent governance; no provider requires it) | Not a prerequisite for using public data |
| R2 | Trust root, rotation, revocation | **Optional governance hardening** | as R1 |
| R3 | Source accession, version, terms, checksums | **Source accessibility: RESOLVED** (table above). Obligations kept: cite each source, keep version pins, honour CC-BY-4.0 attribution for NPH52 and the Allen terms for SEA-AD. | Optional: record the HVS licence string from the CELLxGENE dataset page |
| R4 | Alias closure: span overlap versus feature identity | **Scientific qualification** | open |
| R5 | Depositor QC and cell selection | **Scientific qualification** | open (HVS supplement not retrieved) |
| R6 | Donor, specimen, library and dataset identity | **Scientific qualification** | open (SEA-AD block keys; NPH52 specimen) |
| R7 | Input custody for every released view | **Data integrity / software readiness** | partial (#528 wrapper) |
| R8 | A release object with content digests and a receipt binding every enforced field, re-verified by its consumer; D1 only, D2 excluded | **Software readiness**. A signature is optional hardening; consumer re-verification is the required part (#516). | specified, not built |
| R9 | Separation of issuer, producer, student and host | **Software readiness / optional governance hardening** | open |

## 5. NPH52: public download status versus internal restriction
**Public:** NPH52 is open on Zenodo under CC-BY-4.0. Access was never a barrier.

**Still restricted internally,** for scientific reasons that public access does not answer:
- symbol-only features have no alias closure;
- eligibility imports the depositor's annotation-based selection, which quarantined 22,715 reader-fit cells, and its effect is unmeasured;
- each cell type has its own feature set.

The restriction covers real query issuance and analysis of the quarantined expression.

**I do not propose lifting it now.** An evidence-based proposal to lift it would need:
1. alias closure for NPH52's symbol-only features at operator scope;
2. an approved and executed selection-effect protocol (#513 §4) showing exclusion is not associated with query detection beyond library size and cell-type composition.

Until the owner records a decision, the restriction stands.

## 6. Proposal: versioned QC-only analytic allowlist (decision pending)
**Name:** `JEPA_QC_ONLY_ANALYTIC_ALLOWLIST_V1`.

**Columns:** SEA-AD `Doublet score`; HVS `is_primary_data`.

**Permitted use:** aggregate QC and selection characterization only, meaning distributions, floors and duplicate-cell checks, reported as aggregates.

**Prohibited uses:**
- as a model input or covariate;
- joined to pathology or outcome columns;
- for target, representation or donor-split selection;
- for filtering cells before a query-independence assessment. `Doublet score` is itself expression-derived, so a filter on it depends on expression.

**Versioning:** any new column needs a V2 entry with its own justification.

**Decision owner:** Dushyant. Public status alone does not lift the internal hold. Until a decision is recorded, the wrapper refuses to replay the real frozen probe (`REPLAY_HOLD`).

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
