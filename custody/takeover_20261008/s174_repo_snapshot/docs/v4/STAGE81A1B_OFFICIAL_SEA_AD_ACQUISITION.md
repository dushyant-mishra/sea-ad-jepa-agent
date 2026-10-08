# Stage81A1B Official SEA-AD Acquisition

Stage81A1B revision `june_2026_complete_multiregion` acquires the consolidated
official processed foundation needed to close the pre-vocabulary cross-modal contract. It does not train a
model, freeze the 4,096-gene vocabulary, freeze a donor split, construct a
graph, or inspect pathology values.

## Authoritative sources

The catalog is restricted to Allen Institute SEA-AD Open Data on AWS and the
official AD Knowledge Portal study record. The June 2026 SEA-AD README marks
the older MTG/PFC release as deprecated and identifies the multiregion release
as its replacement. PFC/A9 is published under `PFC/RNAseq` with `DFC` object
names.

The bounded live discovery identifies:

- final-nuclei RNA for all ten June 2026 cortical regions: MTG, DFC/PFC/A9,
  STG, V1C, MEC, LEC, HIP, ITG, AnG and FI;
- the current consolidated Caudate object, which is the eleventh region in the
  official portal and is presently published only as an all-nuclei object;
- the June 2026 ten-region Immune/Microglia-PVM subclass object;
- MTG final-nuclei ATAC, release 2024-12-06;
- combined MTG MERFISH, HIP and MEC MERSCOPE, and Caudate Xenium AnnData.

Redundant all-nuclei copies, donor-level duplicates, raw microscopy, and
duplicate spatial objects are excluded. The Caudate all-nuclei object is not a
duplicate because no final-nuclei alternative is advertised. The local 2024 MTG RNA object is
preserved as an official historical source, not overwritten.

Processed ATAC availability is recorded independently of RNA availability.
The bounded regional catalogs currently expose the MTG processed ATAC matrix;
other regions are recorded as announced/pending. Official fragment files are
controlled through AD Knowledge Portal study `syn26223298`. The acquisition
does not bypass terms or credentials, and records an exact human-action blocker
for each region.

## Download safety

Each remote object has a recorded URL, size, ETag and release. Downloads use a
`.part` file and resumable `curl`, enforce the remote byte count, compute a
local SHA-256, open HDF5 read-only, and rename only after size verification.
An existing object with a different size is never overwritten. Download
destinations must be ignored by Git, and the storage preflight reserves at
least 750 GiB after the outstanding portfolio.

Verification is bound to repository-relative path, byte size, nanosecond
modification time, SHA-256, HDF5-open status, verifier version and source
commit. A plain 64-character sidecar is never accepted as sufficient proof.
Hashes may be reused only when the full bound verification record still
matches the file. The tracked `stage81a1b_download_events.jsonl` is an
append-only, hash-chained event stream; the deterministic
`stage81a1b_download_ledger.json` is derived from it and does not replace the
event history.

Run from the repository root in the Windows `sea-ad-jepa-v3` environment:

```powershell
conda run -n sea-ad-jepa-v3 python scripts/v4/stage81a1b_acquire_official_sea_ad.py --mode all
```

For a catalog-only validation:

```powershell
conda run -n sea-ad-jepa-v3 python scripts/v4/stage81a1b_acquire_official_sea_ad.py --mode catalog
```

For bounded live HEAD verification of every frozen open object:

```powershell
conda run -n sea-ad-jepa-v3 python scripts/v4/stage81a1b_acquire_official_sea_ad.py --mode discover
```

The downloader can be resumed by repeating the same command. WSL may be used
for transport when direct exFAT writes are slow, but tracked outputs always
contain repository-relative logical paths and never serialize `/mnt/d`, drive
letters, or junction details.

## Regulatory preservation amendment

Four evidence lineages remain separate:

1. Stage27C/35C expression/module graph: historical baseline and annotation.
2. Stage51 STRING graph: generic interaction control or annotation.
3. Stage75-79 TF-target graph: soft v4B prior candidate with matched controls.
4. Motif, enhancer, ATAC and cisTarget evidence: evidence features and prior
   provenance.

The 96 frozen Stage75 edges are copied into a versioned integration table.
Motif support, direct/extended motif annotation, chromatin evidence,
proximity-only peak-to-gene support, RNA coactivity, predicted coactivity sign,
and experimental or causal direction are represented separately. Coactivity
sign is never relabeled as activation or repression. No old graph is rebuilt.

New SEA-AD RNA/ATAC availability augments these records. It does not erase the
GSE174367 or cisTarget lineages and does not establish edge-level SEA-AD
regulation without an official linked product.

## Release lineage

The official AWS README and Multiregion 2026 repository govern release
precedence. June 2026 MTG and DFC/PFC/A9 objects supersede the earlier release
for production candidacy, while old local objects remain byte-preserved for v3
reproducibility. The official `mixup_investigation_02-14-2025.csv` is registered
as the donor/library correction authority; no donor swap is inferred from
partial identifiers or expression similarity. Old/new comparison is bounded to
shape, feature IDs, donor IDs, index samples and schema fields.

The correction CSV is parsed as a table and validated by exact `ar_id`, source
region, original donor and corrected donor fields against the downloaded
release metadata. Path existence alone is not a passing check, and partial
identifier matching is prohibited.

Compatibility is reported row by row as `compatible_present`,
`absent_from_final_nuclei`, or `conflicting_present`. A correction library that
is absent from a consolidated final-nuclei object remains registered from the
official correction authority but is not treated as either confirmed or
contradicted by that object. Any library that is present under a donor other
than the exact predicted corrected donor is a hard failure. Preserved v3
evidence hashes are cached only with matching repository-relative path, byte
size, modification time, and SHA-256 bindings so repeated finalization does not
rehash unchanged large files.

## Identity and metadata audit

Stage81A1B records exact official donor, specimen, library, run, region,
method, section and cell/nucleus identifier fields when they exist. A
long-form crosswalk aggregates exact observed identity combinations without
loading expression matrices. Missing specimen or section fields remain
explicitly unresolved; placeholder strings are forbidden.

Each June 2026 regional `final-nuclei_metadata` CSV is cataloged by official
key, size, ETag and last-modified value. Schema comparison reads only the first
CSV line and closes the response. Data rows are not consumed. The CSVs remain
undownloaded when required identity, QC and taxonomy fields already exist in
the corresponding H5AD `obs`; all-nuclei and donor-level duplicate matrices
remain excluded.

Matrix semantics are recorded structurally for every acquired H5AD: shape,
X encoding/dtype, sparse or dense representation, raw/layers, count-like
layers, normalization and log-transform fields, feature and observation
identifier fields, methods, donors, regions, sections, coordinates and `obsm`
keys. Expression matrices are never dense-loaded.

## Multiome claim boundary

RNA cells labeled `10xMulti` and the processed MTG ATAC matrix establish that
both modalities are present. They do not establish paired cells by
themselves. Stage81A1B compares exact official observation identifiers and
records separately:

- `multiome_rna_cells_present`;
- `processed_atac_matrix_present`;
- `exact_rna_atac_barcode_linkage_verified`;
- `paired_multiome_contract_ready`;
- the exact linkage evidence and limitations.

No barcode trimming, partial matching or inferred pairing is allowed. Even
when exact pairing is available, it is modality provenance rather than
edge-level regulatory evidence.

## Stage81A1C boundary

Stage81A1B records, but does not download, a planning registry for eight
official GEO series: GSE178317, GSE175721, GSE301119, GSE293118, GSE311359,
GSE254205, GSE241858 and GSE240609. Their roles distinguish direct microglial
Perturb-seq from myeloid auxiliary, regulatory-element, genotype/context and
bulk validation evidence. No GEO data are acquired in this SEA-AD stage.

## Pathology firewall

Pathology-bearing local metadata is registered as sealed post-hoc evaluation
material. This stage does not read pathology values or distributions. Any
future use remains governed by the Stage81A0 pathology firewall.

## Interpretation

Stage81A1B establishes acquisition, identity, and compatibility provenance.
It does not establish a validated GRN, causal regulation, perturbation
response, spatial interaction, therapeutic effect, or biological model
performance.
