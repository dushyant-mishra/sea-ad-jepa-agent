#!/usr/bin/env Rscript

# One-time, explicitly authorized data-hygiene splitter.
# This is the sole production code allowed to deserialize the mixed NPH TRAIN
# derivatives. It performs identity-only donor filtering and no expression
# summaries, fitting, normalization, filtering, or scientific calculations.

args <- commandArgs(trailingOnly=TRUE)
if (length(args) != 2L) stop("usage: <project-root> <staging-envelope>")
.libPaths(c(file.path(args[[1]], ".r-library"), .libPaths()))
suppressPackageStartupMessages(library(digest))
suppressPackageStartupMessages(library(qs))
suppressPackageStartupMessages(library(SingleCellExperiment))

project <- normalizePath(args[[1]], mustWork=TRUE)
staging <- normalizePath(args[[2]], mustWork=TRUE)
package <- file.path(staging,"FULL104_EXPRESSION_INTERFACE_V8")
derivative_dir <- file.path(package,"nph_reader_fit_derivatives")
if (dir.exists(derivative_dir)) stop("quarantine derivative directory already exists; never resume a split attempt")
dir.create(derivative_dir,recursive=TRUE,showWarnings=FALSE)

reader_path <- file.path(project,"exports/contextual_biology_v6r5a_20260822/reader_donor_split.csv")
reader_expected_sha <- "efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511"
reader_actual_sha <- digest(reader_path,algo="sha256",file=TRUE)
if (!identical(reader_actual_sha,reader_expected_sha)) stop("reader split authority hash mismatch")
reader <- read.csv(reader_path,stringsAsFactors=FALSE)
fit_donors <- sort(reader$donor_id[reader$reader_partition == "reader_fit" & grepl("^human_NPH_",reader$donor_id)])
protected_donors <- sort(reader$donor_id[reader$reader_partition != "reader_fit" & grepl("^human_NPH_",reader$donor_id)])
if (length(fit_donors) != 17L || !identical(protected_donors,c("human_NPH_1025","human_NPH_878"))) stop("NPH reader authority mismatch")

meta <- file.path(project,"outputs/full104_v014_20260826/01_full104_metadata_adapter")
index <- read.csv(file.path(meta,"FULL104_ROW_LINEAGE.csv"),stringsAsFactors=FALSE)
index <- index[index$source == "NPH52",,drop=FALSE]
if (nrow(index) != 7L || !identical(sort(index$operator_index),35:41)) stop("NPH lineage shard geometry mismatch")
expected_parts <- lapply(seq_len(nrow(index)),function(i) {
  x <- read.csv(gzfile(file.path(meta,index$path[[i]])),stringsAsFactors=FALSE)
  if (any(x$reader_partition != "reader_fit") || any(x$foundation_split != "foundation/train") || any(x$eligibility_status != "LAWFUL_READER_FIT")) stop("protected or ineligible row in fit lineage")
  x[,c("operator_index","matrix_id","donor_id","canonical_cell_id","source_row","row_locator")]
})
expected <- do.call(rbind,expected_parts)
expected <- expected[order(expected$operator_index,expected$source_row),,drop=FALSE]
if (nrow(expected) != 236476L || length(unique(expected$donor_id)) != 17L || !identical(sort(unique(expected$donor_id)),fit_donors)) stop("NPH frozen fit-lineage authority mismatch")
if (anyDuplicated(expected$canonical_cell_id) || anyDuplicated(expected$row_locator)) stop("duplicate frozen fit-lineage identity")
write.csv(expected,gzfile(file.path(package,"NPH_READER_FIT_EXPECTED_LINEAGE.csv.gz")),row.names=FALSE,quote=TRUE)
disposition <- read.csv(gzfile(file.path(project,"data/processed/v4/stage81a3/stage81a3_nph_disposition_detail.csv.gz")),stringsAsFactors=FALSE)

exact_path <- file.path(project,"data/processed/v4/stage81a2r/nph52_physical_split/nph52_physical_split_exactness_manifest.csv")
exact <- read.csv(exact_path,stringsAsFactors=FALSE)
manifest_rows <- list()
authority_prefix <- "/mnt/d/Jepa project/"

for (operator_index in 35:41) {
  exp_rows <- expected[expected$operator_index == operator_index,,drop=FALSE]
  matrix_id <- unique(exp_rows$matrix_id)
  if (length(matrix_id) != 1L) stop("operator does not resolve to one NPH object")
  object_name <- sub("^NPH52::matrix::","",matrix_id)
  source <- exact[exact$source_object_id == object_name & exact$partition == "TRAIN",,drop=FALSE]
  if (nrow(source) != 1L || tolower(as.character(source$exact_lossless_subset_pass[[1]])) != "true") stop("mixed derivative authority mismatch")
  authority_path <- as.character(source$derivative_path[[1]])
  if (!startsWith(authority_path,authority_prefix)) stop("mixed derivative outside canonical authority prefix")
  relative <- substring(authority_path,nchar(authority_prefix)+1L)
  mixed_path <- normalizePath(file.path(project,relative),mustWork=TRUE)
  if (file.info(mixed_path)$size != as.numeric(source$derivative_size_bytes[[1]]) || digest(mixed_path,algo="sha256",file=TRUE) != as.character(source$derivative_sha256[[1]])) stop("mixed derivative authentication failed")

  # AUTHORIZED EXCEPTION BEGINS. No assay/value access occurs before filtering.
  mixed <- qread(mixed_path)
  donor_identity <- as.character(colData(mixed)$source_donor_id)
  cell_identity <- as.character(colnames(mixed))
  keep <- donor_identity %in% fit_donors
  fit_only <- mixed[,keep,drop=FALSE]
  rm(mixed,donor_identity,cell_identity,keep)
  gc(verbose=FALSE)
  # AUTHORIZED EXCEPTION ENDS for this object: only fit expression remains.

  fit_cells <- as.character(colnames(fit_only))
  fit_cell_donors <- as.character(colData(fit_only)$source_donor_id)
  fit_disposition <- disposition[disposition$source_object == object_name & disposition$donor_id %in% fit_donors,,drop=FALSE]
  lawful_disposition <- fit_disposition[tolower(as.character(fit_disposition$foundation_eligibility)) == "true",,drop=FALSE]
  quarantined_disposition <- fit_disposition[tolower(as.character(fit_disposition$foundation_eligibility)) == "false",,drop=FALSE]
  if (nrow(lawful_disposition)+nrow(quarantined_disposition) != nrow(fit_disposition)) stop("unrecognized fit-donor disposition state")
  if (!setequal(as.character(lawful_disposition$source_cell_id),as.character(exp_rows$canonical_cell_id)) || nrow(lawful_disposition) != nrow(exp_rows)) stop("lawful disposition differs from frozen lineage")
  if (anyDuplicated(fit_cells) || !setequal(fit_cells,as.character(fit_disposition$source_cell_id)) || length(fit_cells) != nrow(fit_disposition)) stop("donor-filtered derivative differs from frozen disposition")
  excluded_cells <- setdiff(fit_cells,as.character(exp_rows$canonical_cell_id))
  if (!setequal(excluded_cells,as.character(quarantined_disposition$source_cell_id)) || length(excluded_cells) != nrow(quarantined_disposition)) stop("excluded fit-donor cells are not exactly the frozen quarantine")
  canonical_order <- match(as.character(exp_rows$canonical_cell_id),fit_cells)
  if (anyNA(canonical_order) || !identical(fit_cell_donors[canonical_order],as.character(exp_rows$donor_id))) stop("fit-only derivative donor/cell identity mismatch")
  fit_only <- fit_only[,canonical_order,drop=FALSE]
  fit_cells <- fit_cells[canonical_order]
  fit_cell_donors <- fit_cell_donors[canonical_order]
  if (!identical(fit_cells,as.character(exp_rows$canonical_cell_id))) stop("canonical lineage reorder failed")
  if (any(fit_cell_donors %in% protected_donors) || any(!(fit_cell_donors %in% fit_donors))) stop("protected donor survived quarantine split")

  output_name <- sub("[.]qs$",".READER_FIT_ONLY.full_features.qs",object_name)
  temporary <- file.path(derivative_dir,paste0(output_name,".partial"))
  final <- file.path(derivative_dir,output_name)
  qsave(fit_only,temporary,preset="high",nthreads=1L)
  rm(fit_only,fit_cells,fit_cell_donors)
  gc(verbose=FALSE)
  if (!file.rename(temporary,final)) stop("atomic derivative rename failed")
  manifest_rows[[length(manifest_rows)+1L]] <- data.frame(
    operator_index=operator_index,matrix_id=matrix_id,source_object_id=object_name,
    derivative_relative_path=file.path("nph_reader_fit_derivatives",output_name),
    derivative_size_bytes=file.info(final)$size,derivative_sha256=digest(final,algo="sha256",file=TRUE),
    cell_count=nrow(exp_rows),donor_count=length(unique(exp_rows$donor_id)),feature_count=as.integer(source$feature_count[[1]]),
    reader_partition="reader_fit",foundation_split="foundation/train",stringsAsFactors=FALSE)
}

manifest <- do.call(rbind,manifest_rows)
if (nrow(manifest) != 7L || sum(manifest$cell_count) != 236476L) stop("fit-only derivative manifest totals mismatch")
write.csv(manifest,file.path(package,"NPH_READER_FIT_DERIVATIVE_MANIFEST.csv"),row.names=FALSE,quote=TRUE)
provenance <- c(
  '{',
  '  "schema": "full104-nph-reader-fit-quarantine-v1",',
  '  "authorization": "ITERATIVE_QUARANTINED_NPH_ENGINEERING_RETRIES_AUTHORIZED_UNTIL_CLEAN_PASS",',
  '  "status": "QUARANTINE_SPLIT_COMPLETE_AWAITING_FRESH_PROCESS_VERIFICATION",',
  paste0('  "reader_split_sha256": "',reader_actual_sha,'",'),
  '  "protected_expression_transiently_deserialized_in_quarantined_splitter": true,',
  '  "protected_expression_used_for_any_derived_quantity": false,',
  '  "protected_expression_summarized_inspected_cached_logged_or_exported": false,',
  '  "identity_only_filter": "authenticated reader_fit donor, then frozen lawful canonical-cell allowlist; excluded cells exactly equal frozen foundation_eligibility=false disposition",',
  '  "derivatives": 7,',
  '  "fit_donors": 17,',
  '  "fit_cells": 236476,',
  '  "phase2_started": false,',
  '  "scientific_parameter_selected": false',
  '}'
)
writeLines(provenance,file.path(package,"NPH_QUARANTINE_SPLIT_PROVENANCE.json"),useBytes=TRUE)
cat("QUARANTINE_SPLIT_COMPLETE_AWAITING_FRESH_PROCESS_VERIFICATION\n")
