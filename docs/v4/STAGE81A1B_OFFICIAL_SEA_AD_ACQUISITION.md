# Stage81A1B Official SEA-AD Acquisition

Stage81A1B acquires the smallest consolidated official processed portfolio
needed to close the pre-vocabulary cross-modal contract. It does not train a
model, freeze the 4,096-gene vocabulary, freeze a donor split, construct a
graph, or inspect pathology values.

## Authoritative sources

The catalog is restricted to Allen Institute SEA-AD Open Data on AWS and the
official AD Knowledge Portal study record. The June 2026 SEA-AD README marks
the older MTG/PFC release as deprecated and identifies the multiregion release
as its replacement. PFC/A9 is published under `PFC/RNAseq` with `DFC` object
names.

The bounded portfolio contains:

- MTG final-nuclei RNA, release 2026-06-22;
- PFC/A9 final-nuclei RNA, release 2026-06-22;
- MTG final-nuclei ATAC, release 2024-12-06;
- the combined MTG MERFISH AnnData object, release 2024-12-11.

All-nuclei copies, donor-level duplicates, raw sequence files, raw microscopy,
and duplicate MERFISH objects are excluded. The local 2024 MTG RNA object is
preserved as an official historical source, not overwritten.

## Download safety

Each remote object has a recorded URL, size, ETag and release. Downloads use a
`.part` file and resumable `curl`, enforce the remote byte count, compute a
local SHA-256, open HDF5 read-only, and rename only after size verification.
An existing object with a different size is never overwritten. Download
destinations must be ignored by Git, and the storage preflight reserves at
least 750 GiB after the outstanding portfolio.

Run from the repository root in the Windows `sea-ad-jepa-v3` environment:

```powershell
conda run -n sea-ad-jepa-v3 python scripts/v4/stage81a1b_acquire_official_sea_ad.py --mode all
```

For a catalog-only validation:

```powershell
conda run -n sea-ad-jepa-v3 python scripts/v4/stage81a1b_acquire_official_sea_ad.py --mode catalog
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

## Pathology firewall

Pathology-bearing local metadata is registered as sealed post-hoc evaluation
material. This stage does not read pathology values or distributions. Any
future use remains governed by the Stage81A0 pathology firewall.

## Interpretation

Stage81A1B establishes acquisition, identity, and compatibility provenance.
It does not establish a validated GRN, causal regulation, perturbation
response, spatial interaction, therapeutic effect, or biological model
performance.
