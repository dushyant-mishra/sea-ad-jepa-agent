# Public-source acquisition history correction — 2026-11-03

**Requested by project owner:** all core datasets under analysis were obtained from freely downloadable public releases. This note corrects an **evidence-search failure in later #528 source-rights work**, not an experimental failure or a re-download. There is no user-supplied accession required to identify NPH52.

## Authoritative project acquisition evidence already on `main`

1. `configs/v4/stage81a1d_living_human.yaml`, Git blob `e0e2daf697e1e978a6185d1b5866ba26ead70a5b`, records **NPH52 Zenodo record 8319719**, provider API `https://zenodo.org/api/records/8319719`, required `organized_data.zip` MD5 `3aa418e4f218ff4bfbdefbc21bc89b5a` and `annotations.zip` MD5 `0981c257713e79e9fe775e2576872f9b`. Also records HVS CELLxGENE collection `35928d1c-36fc-4f93-9a8d-0b921ab41745`. It explicitly sets `synapse.accept_terms_automatically: false`, separating any controlled Synapse candidates from freely downloadable assets.
2. `results/v4/stage81a1d_living_human_dataset_role_registry.csv`, Git blob `5e50ae1eb28a6901bf54c3763716e3fc09089b69`, has exact row `NPH52,NPH52,Zenodo,8319719,2,...,verified`. The `2` is the original source registry's revision field, **not** proof of latest Zenodo landing-page version; the current web landing page shows `v1`.
3. `results/v4/stage81a1d_living_human_remote_asset_catalog.csv`, Git blob `582cfd658c79971979a3c3d6c7ac6ad1866922e1`, contains original provider download URLs and archive identities for NPH52 and HVS.
4. `scripts/v4/stage81a1d_acquire_living_human.py`, Git blob `bc10f1330516e99fff4d33ecd44adffd2e5a83fd`, implements the reproducible Zenodo/CELLxGENE acquisition and checksum checks rather than a hypothetical unpublished source.
5. Processed multiregion SEA-AD already has a pinned public Allen Institute source and term/citation references in `SEA_AD_Multiregion_2026_README.md` / original acquisition registry, as acknowledged in #528. Distinguish raw SEA-AD/Synapse controlled access from already obtained **public processed** Allen AWS assets.

## Official external source corroboration checked 2026-11-03

- [Zenodo NPH Integrative Analysis Datasets](https://zenodo.org/records/8319719) advertises direct downloads for `organized_data.zip` and `annotations.zip` with MD5 values matching our original config. It contains published molecular/QC metadata. An exact blanket reuse license was **not** established from the webpage's empty visible Rights/License field; do not infer CC0 or CC-BY.
- [Gazestani et al. associated open-access paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC10274680/) says generated snRNA-seq and 28-study integration are publicly available via `braincelldata.org/resource`.
- [HVS: Human variation study CELLxGENE collection](https://cellxgene.cziscience.com/collections/35928d1c-36fc-4f93-9a8d-0b921ab41745) offers public dataset downloads and explicitly says its published study datasets require no additional IRB permission.
- [Allen SEA-AD official data portal](https://brain-map.org/consortia/sea-ad/our-data) and [AWS public registry](https://registry.opendata.aws/allen-sea-ad-atlas/) offer freely accessible **processed snRNA/ATAC** downloads, with Allen Institute Terms of Use and Citation Policy. The same portal marks **certain raw 10x and Sage/IAC assets controlled access**. Do not conflate data tiers.

## Correct the earlier governance interpretation

**Public dataset access does not require the owner to create a hardware signing key or provide a missing NPH52 accession**. A signing key/trust-root mechanism is an **optional stronger internal agent-independence/audit control**, not publisher-imposed access permission. The original pipeline already used public access and provider-linked hashes. Do not use the absence of an internal signer to falsely assert that publicly released counts/QC are legally barred.

**What remains important:** source version/hash custody, source terms/citations, scientific identification of genes across versions, measurement support, donor/specimen definition, depositor cell-selection methods and data leakage avoidance. These are **scientific validity/experimental-design limits**, not in themselves evidence of closed-source usage rights. NPH52 being blocked in later **real-query issuance** arose from internal qualification/anti-leakage protocol (off-ledger alias/selection effects and quarantined set), **not a claim that Zenodo denies the dataset's download**. Do not silently undo frozen DEV/SEALED and pathology holdouts.

The two QC fields `SEA-AD Doublet score` and `HVS is_primary_data` are public depositor metadata. Their previous **project allowlist hold** remains an internal scope/review choice, not an externally imposed license/IRB prohibition. Resolve using the versioned QC-use policy and independently tested analytics code rather than demanding the owner retrieve an already public source accession. No rereads undertaken in preparing this correction.

**Correction posted directly on Macha #528:** https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/528#issuecomment-6596313824 . Macha-authored #528 original bytes remain intact; an erratum should classify R3 public-source-ID as **KNOWN** and distinguish optional signature custody from source access. Reviewer #529 source-admission RED is separately valid and requires code repair.

**No new target/model winner, source-byte rehash or Stage4:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
