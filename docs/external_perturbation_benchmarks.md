# External Perturbation Benchmarks

The SEA-AD model is trained on observational human brain data. To test whether its model-implied counterfactuals reflect real intervention biology, we need public datasets where genes or pathways were actually perturbed.

The benchmark question is:

```text
If JEPA predicts that perturbing a gene/module changes cell state,
does a real CRISPR or drug perturbation dataset show a matching response?
```

## Benchmark 1: Perturb-seq

Perturb-seq combines pooled CRISPR perturbations with single-cell RNA-seq. It is the best match for testing gene-network causal predictions.

### Kampmann Lab iPSC-Derived Microglia CRISPRi/a CROP-seq

Use case:

```text
biology-matched external benchmark for microglia state perturbations
```

Why it matters:

```text
K562 validates the benchmark plumbing; iPSC-derived microglia test the disease-relevant cell type.
```

The strongest near-term biological pivot is the Kampmann Lab human iPSC-derived microglia CRISPRi/a platform. The associated Nature Neuroscience publication is listed by the Kampmann Lab as **"A CRISPRi/a platform in human iPSC-derived microglia uncovers regulators of disease states"**. The lab also hosts a **Microglia Analysis** resource page with RNA-seq and CROP-seq analysis scripts/notebooks.

Reference/access:

- Kampmann Lab microglia analysis page: https://kampmannlab.ucsf.edu/article/microglia-analysis
- Kampmann Lab publication listing: https://kampmannlab.ucsf.edu/selected-publications
- Publication DOI page via PubMed link from Kampmann Lab: https://pubmed.ncbi.nlm.nih.gov/35915164/

How to use it:

```text
1. Locate processed CROP-seq count matrices or analysis objects from the linked resource.
2. Confirm perturbation labels and control labels.
3. Align shared genes to the SEA-AD JEPA input space.
4. Run benchmark_perturbseq_streaming.py on microglia-relevant targets.
5. Compare input_erasure and predictive counterfactual modes.
```

Best first targets:

```text
P2RY12
CX3CR1
TREM2
APOE
C1QA / C1QB / C1QC
TYROBP
```

Interpretation:

```text
This is the first external perturbation benchmark that can plausibly validate microglia-specific Alzheimer's hypotheses.
```

Current local status:

```text
GEO accession: GSE178317
Downloaded locally:
  data/raw/kampmann_gse178317/GSE178317_RAW.tar
  data/raw/kampmann_gse178317/drager_2022_supplementary_tables.xlsx
Extracted schema-inspection files:
  GSM5387652_iTF_Microglia_10X_Lane1_filtered_feature_bc_matrix.h5
  GSM5387656_iTF_Microglia_sgRNAenrichment_Lane1_filtered_feature_bc_matrix.h5
```

Important access finding:

```text
The public GEO H5 files provide Cell Ranger count matrices.
The final per-cell sgRNA assignments are not exposed as a simple metadata table in GEO.
The paper states that sgRNA assignment used a separate mapping workflow and demux/z-score filtering.
```

This means the first automated benchmark should not force the existing cell-level streaming script onto these files. Instead, the repo now includes a DEG-vector benchmark:

```text
scripts/benchmark_kampmann_deg_alignment.py
```

This script compares SEA-AD JEPA digital CRISPRi shifts against the published CROP-seq target-gene differential expression vectors from Supplementary Table 9.

Targets available in the Dräger/Kampmann CROP-seq DEG table include:

```text
CSF1R
INPP5D
TGFBR2
CDK8
CDK12
MED1
NDUFA8
NDUFS5
```

Targets not perturbed in this public CROP-seq screen include:

```text
P2RY12
CX3CR1
TREM2
APOE
C1QA / C1QB / C1QC
TYROBP
F13A1
```

First benchmark results:

```text
input_erasure:
  CSF1R   cosine -0.515   Spearman -0.488
  TGFBR2  cosine -0.269   Spearman -0.270
  CDK8    cosine -0.510   Spearman -0.425
  CDK12   cosine  0.350   Spearman  0.311

predictive:
  CSF1R   cosine -0.616   Spearman -0.587
  TGFBR2  cosine -0.402   Spearman -0.399
  CDK8    cosine -0.543   Spearman -0.493
  CDK12   cosine  0.288   Spearman  0.258
```

Interpretation:

```text
This is a real biology-matched stress test, and the current v1 model does not yet align broadly with observed iPSC-microglia perturbation responses.
That is a useful negative/partial result: it motivates module-level perturbation, CRISPRi-aware scaling, stronger cross-domain alignment, and eventually JEPA v2.
```

### Replogle et al. Genome-Scale Perturb-seq

Use case:

```text
large-scale single-gene perturbation benchmark
```

Why it matters:

```text
known CRISPR perturbation -> observed transcriptomic response
```

The Replogle genome-scale Perturb-seq paper reports genome-scale transcriptional effects of genetic perturbations and lists processed data access through the GWPS portal and raw sequencing through SRA BioProject PRJNA831566. The paper also points to analysis code and related guide-calling tools.

Reference/access:

- Paper/data access notes: https://pmc.ncbi.nlm.nih.gov/articles/PMC9380471/
- Processed data listed by the paper: http://gwps.wi.mit.edu

How to use it:

```text
1. Train JEPA on control cells.
2. Run digital knockout for a target gene.
3. Compare predicted knockout latent state to the real CRISPR knockout state.
4. Score with cosine similarity, DEG overlap, or module-response correlation.
```

### Norman et al. Combinatorial Perturb-seq

Use case:

```text
single-gene and combinatorial perturbation benchmark
```

Why it matters:

```text
tests whether the model captures interaction effects, not just one-gene effects
```

The Norman et al. study used Perturb-seq to manipulate gene pairs and measure rich single-cell phenotypes. It is useful for checking whether predicted module interactions match observed combinatorial effects.

Reference/access:

- Paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC6746554/
- GEO accession noted by scPerturb and other benchmark papers: `GSE133344`
- Codebase listed in Replogle et al.: https://github.com/thomasmaxwellnorman/Perturbseq_GI

How to use it:

```text
1. Predict single-gene effects.
2. Predict pairwise or module-level effects.
3. Compare predicted non-additivity to observed combinatorial perturbation response.
```

### scPerturb Harmonized Collection

Use case:

```text
practical multi-dataset access layer
```

Why it matters:

```text
many perturbation datasets are harmonized and documented in one resource
```

The scPerturb resource aggregates and harmonizes many single-cell perturbation datasets. Its paper lists accessions for Norman, Replogle, Srivatsan/sci-Plex, and many other perturbation studies.

Reference/access:

- scPerturb paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC12220817/

## Benchmark 2: Drug Perturbation scRNA-seq

Drug data tests pharmacologic perturbations rather than clean genetic knockouts.

### sci-Plex

Use case:

```text
drug and dose response benchmark
```

Why it matters:

```text
chemical perturbations often hit pathways/modules rather than single genes
```

sci-Plex profiles single-cell transcriptional responses to many drug perturbations. It is useful for testing whether module-level digital perturbations align with real drug-induced state shifts.

Reference/access:

- scPerturb lists Srivatsan/Trapnell 2020 as `GSE139944`: https://pmc.ncbi.nlm.nih.gov/articles/PMC12220817/

How to use it:

```text
1. Map drugs to known targets/pathways.
2. Compare drug-induced expression shifts to JEPA-predicted module perturbations.
3. Ask whether drugs targeting a predicted AT8 driver module move cells in the expected latent direction.
```

## Benchmark 3: Multimodal Morphology Perturbation

### JUMP Cell Painting

Use case:

```text
image/morphology perturbation benchmark
```

Why it matters:

```text
future multimodal JEPA should connect molecular state to morphology
```

JUMP Cell Painting is useful once the project adds imaging encoders. It can test whether genetic or chemical perturbations produce morphology shifts consistent with transcriptomic/module predictions.

How to use it later:

```text
1. Train image encoder on Cell Painting morphology.
2. Align morphology perturbation state with transcriptomic/module state.
3. Test whether predicted module perturbations match real image phenotypes.
```

## Near-Term Benchmark Choice

The best immediate benchmark is:

```text
Kampmann Lab iPSC-derived microglia CRISPRi/a CROP-seq
```

Why:

```text
closest cell-type match for SEA-AD Microglia-PVM biology
more relevant to P2RY12, CX3CR1, TREM2, APOE, complement, and DAM/homeostatic modules
better biological validation target than K562
```

The second choice is:

```text
Norman et al. Perturb-seq via GSE133344 or the Perturbseq_GI resources
```

Why:

```text
smaller and more tractable than genome-scale Replogle
has single and combinatorial perturbations
well suited for testing digital knockout and latent interaction logic
useful if the microglia CROP-seq objects are not immediately easy to automate
```

The third choice is:

```text
Replogle genome-scale Perturb-seq
```

Why:

```text
strong scale and gene coverage
already works as a local K562 benchmark after downloading the GWPS H5AD
best used as engineering validation rather than microglia biology validation
```

## Benchmark Metrics

For each perturbation:

```text
predicted effect = JEPA digital knockout state - control state
observed effect  = real perturbation state - control state
```

Score:

```text
cosine similarity of effect vectors
Spearman correlation of gene/module deltas
overlap of top differentially expressed genes
module-response correlation
nearest-neighbor retrieval of the true perturbation
```

Success looks like:

```text
the true perturbation ranks above matched random perturbations
predicted module direction agrees with observed perturbation direction
top predicted genes/modules are enriched in real perturbation DEGs
```

## Important Caveat

SEA-AD is human brain tissue. Many perturbation benchmarks are K562, RPE1, cancer, or other cell-line systems. These are not perfect biological matches. They are best used to validate the **causal machinery** first:

```text
Can the JEPA framework recover known perturbation effects when ground truth interventions exist?
```

After that, the same methods can be applied more cautiously to SEA-AD for Alzheimer disease hypothesis generation.
