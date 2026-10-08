# v3 public external dataset schema audit v1

## 1. Executive summary

Stage 26B inspected small GEO series-matrix metadata and supplementary file listings for candidate public datasets. No SRA, FASTQ, BAM, or large raw sequencing payloads were downloaded. This is not external validation and does not alter evidence levels.

## 2. Dataset-by-dataset schema summary

- `GSE157827` (`gse157827`): role=`external_projection_holdout_candidate`, level=`cell_level`, downloaded=['GSE157827_series_matrix.txt.gz'], holdout=True
- `GSE147528` (`gse147528`): role=`external_projection_holdout_candidate`, level=`cell_level`, downloaded=['GSE147528_series_matrix.txt.gz'], holdout=True
- `GSE203206` (`gse203206`): role=`bulk_external_stress_test`, level=`bulk_sample_level`, downloaded=['GSE203206_series_matrix.txt.gz'], holdout=True
- `GSE98969` (`gse98969`): role=`self_supervised_pretraining_candidate`, level=`cell_level`, downloaded=['GSE98969_series_matrix.txt.gz'], holdout=False
- `GSE127893` (`gse127893`): role=`subseries_review_required`, level=`unknown`, downloaded=['GSE127893_series_matrix.txt.gz'], holdout=False
- `GSE181279` (`gse181279`): role=`peripheral_immune_plausibility`, level=`cell_level`, downloaded=['GSE181279_series_matrix.txt.gz'], holdout=False
- `GSE174367` (`gse174367`): role=`plausibility_projection_only`, level=`cell_level`, downloaded=['GSE174367_series_matrix.txt.gz'], holdout=False
- `GSE138852` (`gse138852`): role=`plausibility_projection_only`, level=`cell_level`, downloaded=['GSE138852_series_matrix.txt.gz'], holdout=False

## 3. Metadata columns found

- `GSE127893`: {'sample': ['geo_accession; sample; title; cell'], 'donor': [], 'diagnosis': ['disease; control; ad'], 'cell_type': [], 'gene': []}
- `GSE138852`: {'sample': ['geo_accession; sample; title'], 'donor': ['individual'], 'diagnosis': ['disease; control; ad'], 'cell_type': [], 'gene': []}
- `GSE147528`: {'sample': ['geo_accession; sample; title; barcode; cell'], 'donor': [], 'diagnosis': ['disease; control; ad'], 'cell_type': [], 'gene': ['gene']}
- `GSE157827`: {'sample': ['geo_accession; sample; title; barcode; cell'], 'donor': [], 'diagnosis': ['diagnosis; ad'], 'cell_type': [], 'gene': ['gene; features.tsv']}
- `GSE174367`: {'sample': ['geo_accession; sample; title; cell'], 'donor': [], 'diagnosis': ['control; ad'], 'cell_type': [], 'gene': []}
- `GSE181279`: {'sample': ['geo_accession; sample; title; barcode; cell'], 'donor': [], 'diagnosis': ['disease; ad'], 'cell_type': [], 'gene': ['gene; features.tsv']}
- `GSE203206`: {'sample': ['geo_accession; sample; title'], 'donor': ['subject'], 'diagnosis': ['control; ad'], 'cell_type': [], 'gene': []}
- `GSE98969`: {'sample': ['geo_accession; sample; title'], 'donor': [], 'diagnosis': ['control; ad'], 'cell_type': [], 'gene': []}

## 4. Gene identifier compatibility

Gene identifier compatibility is inferred from downloaded metadata and supplementary filenames only. Full count matrices may still require features.tsv/H5 inspection in a future approved integration stage.

## 5. Donor/sample/cell mapping compatibility

Series-matrix metadata commonly exposes sample-level fields. Donor-level harmonization must be audited before any dataset is used for training or final reporting.

## 6. Which datasets can support pseudobulk construction

Candidates: none confirmed from schema metadata alone

## 7. Which datasets can support microglia/PVM extraction

Candidates: GSE98969, GSE181279, GSE174367, GSE138852

## 8. Which datasets can support external projection/stress testing

Holdout/stress-test candidates: GSE157827, GSE147528, GSE203206
GSE157827 and GSE147528 remain external holdout candidates unless explicitly reclassified. GSE203206 is a bulk sample-level stress-test candidate.

## 9. Which datasets can support pretraining or auxiliary supervision

Pretraining candidates: GSE98969
Auxiliary supervision/plausibility candidates: GSE181279

## 10. Which datasets should not be used until reviewed

Review-required candidates: GSE127893
GSE127893 must undergo subseries review before any raw/SRA or large supplemental download.

## 11. Recommended next integration stage

- For holdout candidates, freeze them out of training and model selection.
- For any approved integration dataset, download processed matrices only, inspect features/barcodes/matrix dimensions, and map genes to the 2,957-gene universe.
- For mouse datasets, add mouse-to-human ortholog mapping before use.
- For GSE174367/GSE138852, keep use limited to plausibility/projection context because they were already used in v1/v2.

No v3 training, graph neural model, model selection, evidence change, or external validation was run.
