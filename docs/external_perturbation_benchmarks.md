# External Perturbation Benchmarks

The SEA-AD model is trained on observational human brain data. To test whether its model-implied counterfactuals reflect real intervention biology, we need public datasets where genes or pathways were actually perturbed.

The benchmark question is:

```text
If JEPA predicts that perturbing a gene/module changes cell state,
does a real CRISPR or drug perturbation dataset show a matching response?
```

## Benchmark 1: Perturb-seq

Perturb-seq combines pooled CRISPR perturbations with single-cell RNA-seq. It is the best match for testing gene-network causal predictions.

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
Norman et al. Perturb-seq via GSE133344 or the Perturbseq_GI resources
```

Why:

```text
smaller and more tractable than genome-scale Replogle
has single and combinatorial perturbations
well suited for testing digital knockout and latent interaction logic
```

The second choice is:

```text
Replogle genome-scale Perturb-seq
```

Why:

```text
stronger scale and gene coverage
better for broad gene-level validation after the benchmark code is stable
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
