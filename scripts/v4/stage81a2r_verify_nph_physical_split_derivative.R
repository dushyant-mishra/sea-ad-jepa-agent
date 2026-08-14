#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3L) {
  stop("Usage: stage81a2r_verify_nph_physical_split_derivative.R <expected_csv> <partition> <verified_csv>")
}

suppressPackageStartupMessages(library(digest))
suppressPackageStartupMessages(library(Matrix))
suppressPackageStartupMessages(library(qs))
suppressPackageStartupMessages(library(SingleCellExperiment))

expected <- read.csv(args[[1]], stringsAsFactors = FALSE)
expected <- expected[expected$partition == args[[2]], , drop = FALSE]
if (nrow(expected) != 1L) stop("Expected derivative row missing")
path <- expected$derivative_path[[1]]
object <- qread(path)
counts <- assay(object, "counts")
hash_character <- function(values) digest(as.character(values), algo = "sha256", serialize = TRUE)
hash_sparse <- function(value) digest(
  list(class = class(value), Dim = value@Dim, p = value@p, i = value@i, x = value@x),
  algo = "sha256",
  serialize = TRUE
)
actual <- data.frame(
  source_object_id = expected$source_object_id,
  partition = expected$partition,
  derivative_path = normalizePath(path, winslash = "/", mustWork = TRUE),
  derivative_sha256 = digest(file = path, algo = "sha256", serialize = FALSE),
  derivative_size_bytes = file.info(path)$size,
  cell_count = ncol(object),
  feature_count = nrow(object),
  cell_id_order_sha256 = hash_character(colnames(object)),
  feature_id_order_sha256 = hash_character(rownames(object)),
  row_data_sha256 = digest(rowData(object), algo = "sha256", serialize = TRUE),
  sparse_count_sha256 = hash_sparse(counts),
  count_class = class(counts)[[1]],
  count_storage_type = typeof(counts@x),
  retained_column_metadata = paste(colnames(colData(object)), collapse = "|"),
  exact_lossless_subset_pass = TRUE,
  stringsAsFactors = FALSE
)
checks <- c(
  actual$cell_count == expected$expected_cell_count,
  actual$feature_count == expected$expected_feature_count,
  actual$cell_id_order_sha256 == expected$expected_cell_id_order_sha256,
  actual$feature_id_order_sha256 == expected$expected_feature_id_order_sha256,
  actual$row_data_sha256 == expected$expected_row_data_sha256,
  actual$sparse_count_sha256 == expected$expected_sparse_count_sha256,
  actual$count_class == expected$expected_count_class,
  actual$count_storage_type == expected$expected_count_storage_type,
  actual$retained_column_metadata == expected$retained_column_metadata
)
if (!all(checks)) stop("Derivative exactness verification failed")
write.csv(actual, args[[3]], row.names = FALSE, quote = TRUE)
message(sprintf("NPH derivative verification PASS: %s %s", actual$source_object_id, actual$partition))
