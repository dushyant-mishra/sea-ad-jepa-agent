#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 4L) {
  stop(paste(
    "Usage: stage81a3r_materialize_corrected_nph_train_sample.R",
    "<worktree> <source_project> <output_root> <source_object_id>"
  ))
}

suppressPackageStartupMessages(library(Matrix))
suppressPackageStartupMessages(library(qs))
suppressPackageStartupMessages(library(SingleCellExperiment))

worktree <- normalizePath(args[[1]], mustWork = TRUE)
source_project <- normalizePath(args[[2]], mustWork = TRUE)
output_root <- normalizePath(args[[3]], mustWork = FALSE)
source_object <- args[[4]]
dir.create(output_root, recursive = TRUE, showWarnings = FALSE)

derivative <- file.path(
  source_project, "data/processed/v4/stage81a2r/nph52_physical_split/TRAIN",
  sub("[.]qs$", ".TRAIN.full_features.qs", source_object)
)
if (!file.exists(derivative)) stop("Physical TRAIN derivative missing")

sample_manifest <- read.csv(
  file.path(source_project, "data/processed/v4/stage81a3/stage81a3_nph_sample_manifest.csv"),
  stringsAsFactors = FALSE
)
requested <- sample_manifest[sample_manifest$source_object == source_object, , drop = FALSE]
if (nrow(requested) == 0L) stop("Frozen pilot sample IDs missing")

provenance <- read.csv(
  gzfile(file.path(source_project, "results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz")),
  stringsAsFactors = FALSE
)
source_id <- paste0("NPH52::", source_object)
mapping <- provenance[provenance$source_dataset_id == source_id, c(
  "source_feature_index", "molecular_address_index", "molecular_address_id"
), drop = FALSE]

collision_ledger <- read.csv(
  gzfile(file.path(worktree, "results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz")),
  stringsAsFactors = FALSE
)
matrix_id <- paste0("NPH52::matrix::", source_object)
blocked_rows <- collision_ledger$source_feature_index[collision_ledger$matrix_id == matrix_id]
supplemental <- read.csv(
  file.path(worktree, "results/v4/stage81a3r_scalar_mapping_unregistered_collisions.csv"),
  stringsAsFactors = FALSE
)
supplemental <- supplemental[supplemental$matrix_id == matrix_id, , drop = FALSE]
if (nrow(supplemental)) {
  blocked_rows <- c(
    blocked_rows,
    as.integer(unlist(strsplit(supplemental$source_feature_indices, "[|]", fixed = FALSE)))
  )
}
mapping <- mapping[!(mapping$source_feature_index %in% blocked_rows), , drop = FALSE]
if (anyDuplicated(mapping$source_feature_index)) stop("Duplicate source feature mapping remains")
if (anyDuplicated(mapping$molecular_address_index)) stop("Many-to-one scalar mapping remains after masking")

object <- qread(derivative)
if (!identical(colnames(colData(object)), c("source_cell_id", "source_donor_id"))) {
  stop("Unexpected physical TRAIN derivative metadata")
}
columns <- match(requested$source_cell_id, colnames(object))
if (anyNA(columns)) stop("Frozen sampled cell is absent from physical TRAIN derivative")
if (!identical(as.character(colData(object)$source_donor_id[columns]), as.character(requested$donor_id))) {
  stop("Frozen sampled donor identity changed")
}

source_counts <- assay(object, "counts")
source_library <- as.numeric(colSums(source_counts[, columns, drop = FALSE]))
local <- t(source_counts[mapping$source_feature_index + 1L, columns, drop = FALSE])
triplet <- summary(local)
materialized <- sparseMatrix(
  i = triplet$i,
  j = mapping$molecular_address_index[triplet$j] + 1L,
  x = triplet$x,
  dims = c(nrow(local), 41238L),
  giveCsparse = TRUE
)

stem <- sub("[.]qs$", "", source_object)
matrix_path <- file.path(output_root, paste0(stem, ".corrected_train_counts.mtx"))
metadata_path <- file.path(output_root, paste0(stem, ".corrected_train_metadata.csv"))
writeMM(materialized, matrix_path)
write.csv(data.frame(
  cell_id = as.character(colData(object)$source_cell_id[columns]),
  donor_id = as.character(colData(object)$source_donor_id[columns]),
  broad_cell_class = sub("_data.*$", "", source_object),
  source_library = source_library,
  stringsAsFactors = FALSE
), metadata_path, row.names = FALSE, quote = TRUE)

message(sprintf(
  "Corrected NPH materialization PASS: %s cells=%d scalar_addresses=%d nnz=%d",
  source_object, nrow(materialized), nrow(mapping), nnzero(materialized)
))
