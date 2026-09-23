# Independent public-source review: GSE240609 bulk expression V2

Date: September 23, 2026
Parent: PR #77 @ `3e293a43e4d6dfb6bba85eaf188bdbbe5ecb2821`.
Physical sample counts: **NOT rerun** in this review lane. All original V1 outputs remain immutable.

## Independent metadata authority

Original [NCBI GEO GSE240609 series](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE240609)
public sample titles independently establish this exact four-sample 2×2:

| GEO accession | GEO public title | Neuron genotype | Microglia genotype | PR77 producer file SHA-256 |
|---|---|---|---|---|
| GSM7703564 | APOE3CH-WT | WT | APOE3 Christchurch | `f61d1ba45877aca810a962c59bb7e5fece5448c5bc23fe69b921dfc12d1615be` |
| GSM7703567 | APOE3CH-PSEN1 | PSEN1 mutant | APOE3 Christchurch | `b7d48bdf0987c888d1563d3ea6da4fcedd817b3ede3d1bcd49439ce4748058e3` |
| GSM7703569 | APOE3-WT | WT | APOE3 | `46db9651d4792bf193eb470827daab4a05f22c11368c054ccb0fab105483ada9` |
| GSM7703571 | APOE3-PSEN1 | PSEN1 mutant | APOE3 | `28cbe1b2b5d3dcdcf0085de59b351b41cc91c6cc8cfd6c78f03b6512c1ea9198` |

The public GEO series design independently says these RNA measurements were from
**CD11b-bead purified microglia isolated AFTER 10 days of neuron–microglia
coculture**, not an unfractionated mixed-coculture transcriptome. The existing V1
producer describes its measured material as `neuron_microglia_coculture`, which
misrepresents the sampled cell compartment. It is nevertheless a
**coculture-CONDITIONED microglial response**, not evidence of an intrinsic
microglial cell-autonomous genetic effect. A single experimental sample per
genotype cross means no biological standard error is estimable.

V1's sample assignments *happen to match* all four independently displayed
GEO public titles, but its code inferred PSEN from a filename substring and
silently chose WT otherwise, and inferred Christchurch from substring variants
and chose APOE3 otherwise. The dict keyed on genotype cross silently overwrote
duplicates and skipped missing cells. A file with an unknown name or a missing
design cell could therefore produce plausible-looking mislabeled results.
We classify this as **FAIL-OPEN implementation even though the known V1 samples
were assigned consistently with public metadata**.

## V2 fail-closed source and experimental-unit gates

* Introduce a reviewed exact public GSM→GEO-title→neuron genotype→microglia
  genotype table, separately bound to the four whole-file PR77 source SHA roots.
* Require exactly those four filenames, full raw-file SHA match and all four
  unique factorial design cells BEFORE the V2 producer opens the raw matrices
  or creates any output.
* Require both GSE241858 source-file raw SHA roots before writing V2 bulk results.
* Prevent overwriting original V1 results; require a new empty output directory.
* Preserve clone-level replicate averaging and the two-clone-per-genotype limit
  in the separate TREM2 genotype×cytokine study.
* Output `CD11B_PURIFIED_MICROGLIA_AFTER_NEURON_COCULTURE` in GSE240609
  metadata and keep one-per-condition uncertainty unestimable.

Source-file SHA roots here derive from PR77's physical producer receipts;
this code cannot independently reauthenticate the original bytes until V2
is physically rerun on Claude's GPU-connected machine. CI exercises the
real V2 early STOP gate with synthetic bytes and checks the lightweight
committed V1 sample identity table against independently retrieved GEO titles.

**Next:** Claude runs the V2 physical producer in a NEW directory and
independently checks original raw-file digests, original gene order and
four-sample descriptive effect equivalence with V1. Any changed numerical
effect requires an explanation; sample biological labels and material should
now be public-GEO anchored.

Status:
`V2_CPU_AND_PUBLIC_METADATA_REVIEW_ONLY__PHYSICAL_RERUN_NOT_EXECUTED`
`TRAINING=OFF | N1=UNOPENED | PROTECTED_OUTCOMES=UNOPENED`
