# Stage75 historical pilot coverage — local read-only audit

Date: 2026-09-26. Status: NON-AUTHORIZING, HISTORICAL REGISTRY ONLY.

## Scope and observed result

The committed `results/tables/stage75_integrated_tf_target_summary_v1.csv` on GitHub main at `c49b13bd75c2d23716c777336db8fbfc78c09cd0` has 96 rows, **27 distinct target gene symbols**, and **7 regulators with candidate support** (ELF1, SPI1, STAT1, BACH1, CEBPA, IRF8, RELA). The companion summary has 10 regulator rows: the other three are historical negative-gate regulators, not supported TF–target results. This observation came from reading the live GitHub file and grouping its target and TF columns. The full integrated table's Git blob SHA is `fd0f8e12c1161629f53f568f30cbc0bf8e3ff1a1`.

The attached August 24 `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` carries a historical `contracts/address_namespace.csv` with 41,238 addresses. Crosswalking the pilot's 27 symbols to that namespace gives 25 unambiguous single-entry targets, two ambiguous gene symbols (HLA-DPA1 and HLA-DPB1; each has a `current_exact` and a `legacy_exact` entry), and zero missing target symbols. All seven supported TF symbols have unique historical matches. There are 33 distinct symbols in the union because IRF8 appears as a TF and a target.

**Do not mistake this for current FULL104 identity verification:** the August namespace is a historical attachment; the live V5 canonical registry, observational states, and Morabito gene identifiers must all be authenticated and explicitly crosswalked before production claims. In particular, never resolve the two HLA collisions by arbitrary `drop_duplicates` or by treating the legacy duplicate as another biological gene.

## Major distinction

- Morabito acquisition report: 61,770 snRNA features, 58,721 snRNA cells; 219,070 snATAC peaks, 143,401 snATAC cells.
- Historical microglia subset: 4,126 snRNA cells (18 samples) and 12,232 snATAC cells (20 samples).
- Stage75 regulatory inference: 96 *candidate* rows across 27 gene symbols and 7 motif-supported regulators. Candidate TF–gene relationships use an RNA coactivity candidate graph, motif enrichment, and **nearest-gene proximity-only** peak–gene links. They are not confirmed causal regulations or a genome-wide eRegulon resource.

The stage75 peak-to-gene assembler expressly tags `region_gene_support_class = proximity_only_nearest_gene`. Treat this as a computational mapping hypothesis. RNA/ATAC sample pairing is not established merely because both files come from GSE174367.

## What is missing from this environment

The historical Morabito raw/processed H5 RNA and ATAC files are not mounted here. The current V5 FULL104 canonical registry (a separate 59.8-MB GitHub file) is not mounted here either. This local computation therefore does not estimate genome-wide gene coverage by ATAC or measured external RNA, donor intersection, ATAC target gene coverage, or remaining independent confirmations. These are `NOT_MEASURED`, not zero.

## Reproduce

Run `python audit_stage75_pilot.py` alongside the user-provided August 24 calibration ZIP in `/mnt/data`, or adjust the script's `ROOT`. The script never opens protected pathology or training data and does not launch training. `stage75_pilot_historical_registry_crosswalk.csv` contains the gene-level records; `stage75_pilot_coverage_summary.json` records source identifiers and current evidence limits.

## Next directly executable tasks on Claude's full-data laptop

1. Verify live repo heads and read START_HERE and the latest handoff. Rehash the original four Morabito files and Stage75 freeze before reuse.
2. Fetch the current authentic FULL104 canonical-address registry and observation-state authority. Resolve the two HLA symbols through source-native IDs and policy, with no automatic gene-symbol deduplication.
3. Read **actual** GSE174367 H5 gene IDs and report exact full-41,238 overlap (measured, unmeasured, symbol ambiguous, unknown); reclassify genes only after resolving Ensembl annotation versions.
4. Read all 219,070 ATAC peak coordinate strings, verify hg38 and coordinate conventions against GENCODE v44, then report promoter-overlap, distal-proximity and *independently supported* region–gene coverage separately. Do not label the nearest-gene mapping as verified enhancer targeting.
5. Build explicit snRNA/snATAC donor/sample crosswalk and conduct donor-disjoint or sample-aware analyses only when pairing is supported by identifiers.
6. Audit potential circularity: if a gene/peak relationship was derived from Morabito RNA or ATAC, it is not an independent test of a prediction trained on those same derived associations.

Training OFF; sealed FULL104 outcome data unopened. No new teacher-target authority or regulatory target promotion is implied.