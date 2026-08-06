# Stage81A1C-P Processed Perturbation Acquisition

Stage81A1C-P re-verifies eight official GEO studies and acquires only their
processed supplementary files and compact SOFT metadata. GEO archives named
`RAW.tar` are accepted only when the GEO record describes them as processed
supplementary matrices; every archive is opened and rejected if it contains
FASTQ, BAM, CRAM or SRA members.

Dataset roles remain separate. GSE178317 is the direct iTF-microglia CROP-seq
training candidate. GSE175721 is an organoid amyloid-context validation study.
GSE301119 is primary-macrophage auxiliary evidence. GSE293118 is an HMC3
regulatory-element screen. GSE311359 is an iPSC-microglia MS-risk auxiliary
study. GSE254205, GSE241858 and GSE240609 are genotype, pharmacology or bulk
mechanistic validation sources.

RDS files receive byte, hash and R-serialization signature validation. The two
GSE301119 objects also require a full read-only audit with R 4.4.3 and
`SeuratObject`: object class, dimensions, assays, metadata schema, guide and
target identities, donor fields, CRISPR mode and non-targeting controls are
verified without materializing an expression matrix. This does not convert the
objects into training-ready matrices.

Run:

```powershell
docker run --rm `
  -v stage81-r-library:/usr/local/lib/R/site-library `
  -v "${PWD}:/workspace" -w /workspace `
  rocker/r-ver:4.4.3 `
  Rscript scripts/v4/stage81a1c_p_audit_seurat.R /workspace

conda run -n sea-ad-jepa-v3 python scripts/v4/stage81a1c_p_acquire_perturbation.py --mode all
```

There is no fixed stage download-volume cap or fixed free-space reserve. The
preflight reports capacity and requires only that the selected assets fit on
the drive. Exact source identity, processed-only selection and duplicate
avoidance still apply. This stage does not train a controller, force perturbed
genes into a vocabulary, or make causal or therapeutic claims.
