#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (!(length(args) %in% c(4L, 5L))) {
  stop(paste(
    "Usage: stage81a3r_audit_nph_collision_count_vectors.R",
    "<source_project> <physical_split_root> <pair_output_csv> <mass_output_csv> [source_object_id]"
  ))
}

suppressPackageStartupMessages(library(Matrix))
suppressPackageStartupMessages(library(qs))
suppressPackageStartupMessages(library(SingleCellExperiment))

source_project <- normalizePath(args[[1]], mustWork = TRUE)
split_root <- normalizePath(args[[2]], mustWork = TRUE)
pair_output <- args[[3]]
mass_output <- args[[4]]
collision_path <- file.path(source_project, "results/v4/stage81a2r_within_matrix_mapping_collisions_candidate.csv")
sample_path <- file.path(source_project, "data/processed/v4/stage81a3/stage81a3_nph_sample_manifest.csv")

collisions <- read.csv(collision_path, stringsAsFactors = FALSE)
collisions <- collisions[grepl("^NPH52::matrix::", collisions$matrix_id), , drop = FALSE]
sample_manifest <- read.csv(sample_path, stringsAsFactors = FALSE)
train_files <- sort(list.files(file.path(split_root, "TRAIN"), pattern = "[.]TRAIN[.]full_features[.]qs$", full.names = TRUE))
if (length(train_files) != 7L) stop("Expected seven physical TRAIN NPH objects")
if (length(args) == 5L) {
  requested_object <- args[[5]]
  requested_derivative <- sub("[.]qs$", ".TRAIN.full_features.qs", requested_object)
  train_files <- train_files[basename(train_files) == requested_derivative]
  if (length(train_files) != 1L) stop("Requested physical TRAIN NPH object missing")
}

pair_rows <- list()
mass_rows <- list()
safe_correlation <- function(left, right) {
  n <- ncol(left)
  sx <- sum(left)
  sy <- sum(right)
  sxx <- sum(left * left)
  syy <- sum(right * right)
  sxy <- sum(left * right)
  numerator <- n * sxy - sx * sy
  denominator <- sqrt(max(n * sxx - sx * sx, 0) * max(n * syy - sy * sy, 0))
  if (denominator > 0) numerator / denominator else NA_real_
}

for (path in train_files) {
  derivative_name <- basename(path)
  source_object <- sub("[.]TRAIN[.]full_features[.]qs$", ".qs", derivative_name)
  matrix_id <- paste0("NPH52::matrix::", source_object)
  local_collisions <- collisions[collisions$matrix_id == matrix_id, , drop = FALSE]
  requested <- sample_manifest[sample_manifest$source_object == source_object, , drop = FALSE]
  object <- qread(path)
  if (!identical(colnames(colData(object)), c("source_cell_id", "source_donor_id"))) {
    stop(sprintf("Unexpected TRAIN derivative metadata in %s", derivative_name))
  }
  columns <- match(requested$source_cell_id, colnames(object))
  if (anyNA(columns)) stop(sprintf("Bounded TRAIN sample missing from %s", derivative_name))
  counts <- assay(object, "counts")[, columns, drop = FALSE]
  participating <- sort(unique(unlist(strsplit(local_collisions$source_feature_indices, "[|]", fixed = FALSE))))
  participating <- as.integer(participating) + 1L
  collision_mass <- if (length(participating)) sum(counts[participating, , drop = FALSE]) else 0
  total_mass <- sum(counts)
  mass_rows[[length(mass_rows) + 1L]] <- data.frame(
    operator_family = "NPH52",
    matrix_id = matrix_id,
    bounded_train_cells = ncol(counts),
    source_feature_rows = nrow(counts),
    collision_source_rows = length(participating),
    total_source_count_mass = as.numeric(total_mass),
    collision_source_count_mass = as.numeric(collision_mass),
    collision_source_count_mass_fraction = if (total_mass > 0) as.numeric(collision_mass / total_mass) else NA_real_,
    stringsAsFactors = FALSE
  )

  for (record_index in seq_len(nrow(local_collisions))) {
    record <- local_collisions[record_index, , drop = FALSE]
    indices_zero <- as.integer(strsplit(record$source_feature_indices, "[|]", fixed = FALSE)[[1]])
    combinations <- combn(seq_along(indices_zero), 2L)
    symbols <- strsplit(record$raw_symbols, "[|]", fixed = FALSE)[[1]]
    raw_ids <- strsplit(record$raw_ids, "[|]", fixed = FALSE)[[1]]
    for (pair_index in seq_len(ncol(combinations))) {
      left_index <- combinations[1L, pair_index]
      right_index <- combinations[2L, pair_index]
      left <- counts[indices_zero[[left_index]] + 1L, , drop = FALSE]
      right <- counts[indices_zero[[right_index]] + 1L, , drop = FALSE]
      pair_rows[[length(pair_rows) + 1L]] <- data.frame(
        operator_family = "NPH52",
        matrix_id = matrix_id,
        molecular_address_id = record$canonical_ensembl_gene_id,
        source_feature_index_a = indices_zero[[left_index]],
        source_feature_index_b = indices_zero[[right_index]],
        raw_source_feature_id_a = raw_ids[[left_index]],
        raw_source_feature_id_b = raw_ids[[right_index]],
        raw_symbol_a = symbols[[left_index]],
        raw_symbol_b = symbols[[right_index]],
        bounded_train_cells = ncol(counts),
        exact_count_vector_equality = nnzero(left - right) == 0L,
        fraction_cells_both_nonzero = as.numeric(sum((left != 0) * (right != 0)) / ncol(counts)),
        row_total_count_a = as.numeric(sum(left)),
        row_total_count_b = as.numeric(sum(right)),
        pearson_correlation = safe_correlation(left, right),
        stringsAsFactors = FALSE
      )
    }
  }
  rm(object, counts)
  gc(verbose = FALSE)
}

pairs <- if (length(pair_rows)) do.call(rbind, pair_rows) else data.frame()
mass <- do.call(rbind, mass_rows)
pairs <- pairs[order(pairs$matrix_id, pairs$molecular_address_id, pairs$source_feature_index_a, pairs$source_feature_index_b), ]
mass <- mass[order(mass$matrix_id), ]
write.csv(pairs, pair_output, row.names = FALSE, quote = TRUE, na = "")
write.csv(mass, mass_output, row.names = FALSE, quote = TRUE, na = "")
message(sprintf("NPH collision diagnostics PASS: pairs=%d operators=%d", nrow(pairs), nrow(mass)))
