# v2.2 CELLxGENE Alignment Stats

This report summarizes public CELLxGENE cohorts filtered to microglia and aligned to the fixed 2,957-gene Graph-JEPA topology.

Missing genes are zero-filled. The master Graph-JEPA gene order and graph topology are not modified.

| Dataset | Microglia | Donors | Matched Genes | Overlap | Disease Counts | Tissue Counts | Assay Counts |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| rexach_cross_dementia | 21575 | 40 | 2837/2957 | 0.959 | Alzheimer disease: 7213; progressive supranuclear palsy: 5506; Pick disease: 5251; normal: 3605 | insular cortex: 16976; Brodmann (1909) area 4: 3511; primary visual cortex: 1088 | 10x 3' v3: 16976; 10x 3' v2: 4599 |
| olah_live_microglia | 16099 | 17 | 2846/2957 | 0.962 | Alzheimer disease: 14086; temporal lobe epilepsy: 2013 | dorsolateral prefrontal cortex: 14086; temporal cortex: 2013 | 10x 3' v2: 16099 |

## Outputs

### rexach_cross_dementia

- input: `data\external\cellxgene\rexach_cross_dementia.h5ad`
- aligned output: `data\processed\v2_alignment\rexach_cross_dementia_microglia_jepa_aligned.h5ad`
- missing genes: `data\processed\v2_alignment\rexach_cross_dementia_missing_genes.txt`

### olah_live_microglia

- input: `data\external\cellxgene\olah_live_microglia.h5ad`
- aligned output: `data\processed\v2_alignment\olah_live_microglia_microglia_jepa_aligned.h5ad`
- missing genes: `data\processed\v2_alignment\olah_live_microglia_missing_genes.txt`
