#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 6L) {
  stop(paste(
    "Usage: stage81a3_extract_nph_sample.R <organized_dir> <sample_manifest_csv>",
    "<canonical_gene_registry_csv> <vocabulary_csv> <cells_csv_gz> <nonzero_csv_gz>"
  ))
}

suppressPackageStartupMessages(library(qs))
suppressPackageStartupMessages(library(SingleCellExperiment))

organized_dir <- normalizePath(args[[1]], mustWork = TRUE)
sample_manifest <- read.csv(args[[2]], stringsAsFactors = FALSE)
gene_registry <- read.csv(args[[3]], stringsAsFactors = FALSE)
vocabulary <- read.csv(args[[4]], stringsAsFactors = FALSE)
vocabulary_ids <- unique(vocabulary$canonical_ensembl_gene_id)
source_files <- sort(list.files(organized_dir, pattern = "[.]qs$", full.names = TRUE))
if (length(source_files) != 7L) stop("Expected seven exact NPH source QS objects")

cells_connection <- gzfile(args[[5]], open = "wt")
nonzero_connection <- gzfile(args[[6]], open = "wt")
writeLines(paste(c(
  "cell_id", "source_dataset_id", "source_object", "source", "broad_cell_class",
  "donor_id", "sampling_score", "raw_library_total"
), collapse = ","), cells_connection)
writeLines(paste(c(
  "cell_id", "canonical_ensembl_gene_id", "raw_count", "transformed_expression"
), collapse = ","), nonzero_connection)

written_cells <- 0L
for (path in source_files) {
  source_object <- basename(path)
  requested <- sample_manifest[sample_manifest$source_object == source_object, , drop = FALSE]
  if (!nrow(requested)) next
  object <- qread(path)
  counts <- assay(object, "counts")
  columns <- match(requested$source_cell_id, colnames(object))
  if (anyNA(columns)) stop(sprintf("Requested NPH cells missing from %s", source_object))
  source_key <- paste0("NPH52::", source_object)
  mapping <- gene_registry[
    gene_registry$source_dataset_id == source_key &
      gene_registry$mapping_status == "exact" &
      gene_registry$canonical_ensembl_gene_id %in% vocabulary_ids,
    , drop = FALSE
  ]
  feature_rows <- as.integer(mapping$source_feature_id) + 1L
  if (any(rownames(object)[feature_rows] != mapping$source_feature_symbol)) {
    stop(sprintf("NPH feature-order mapping mismatch in %s", source_object))
  }
  selected <- counts[, columns, drop = FALSE]
  library_total <- Matrix::colSums(selected)
  if (any(library_total <= 0)) stop(sprintf("Zero-library sampled NPH cell in %s", source_object))
  vocabulary_block <- counts[feature_rows, columns, drop = FALSE]
  cells <- data.frame(
    cell_id = requested$cell_id, source_dataset_id = requested$source_dataset_id,
    source_object = source_object, source = "NPH52",
    broad_cell_class = requested$broad_cell_class, donor_id = requested$donor_id,
    sampling_score = requested$sampling_score, raw_library_total = as.numeric(library_total),
    stringsAsFactors = FALSE
  )
  write.table(cells, cells_connection, sep = ",", row.names = FALSE, col.names = FALSE, quote = TRUE, na = "")
  for (column_index in seq_along(columns)) {
    vector <- vocabulary_block[, column_index, drop = FALSE]
    nonzero_rows <- which(vector[, 1] > 0)
    if (!length(nonzero_rows)) next
    raw <- as.numeric(vector[nonzero_rows, 1])
    values <- data.frame(
      cell_id = requested$cell_id[[column_index]],
      canonical_ensembl_gene_id = mapping$canonical_ensembl_gene_id[nonzero_rows],
      raw_count = raw,
      transformed_expression = log1p(raw * 10000 / library_total[[column_index]]),
      stringsAsFactors = FALSE
    )
    write.table(values, nonzero_connection, sep = ",", row.names = FALSE, col.names = FALSE, quote = TRUE, na = "")
  }
  written_cells <- written_cells + nrow(requested)
  rm(object, counts, selected, vocabulary_block)
  gc(verbose = FALSE)
}

close(cells_connection)
close(nonzero_connection)
if (written_cells != nrow(sample_manifest)) {
  stop(sprintf("NPH cache cell count mismatch: wrote=%d requested=%d", written_cells, nrow(sample_manifest)))
}
message(sprintf("Stage81A3 NPH bounded extraction PASS: cells=%d", written_cells))
