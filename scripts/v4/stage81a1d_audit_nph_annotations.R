#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 5) {
  stop("Usage: stage81a1d_audit_nph_annotations.R <annotations_dir> <organized_nph_dir> <donors_csv> <summary_csv> <matrix_csv>")
}

suppressPackageStartupMessages(library(qs))
suppressPackageStartupMessages(library(SingleCellExperiment))
annotation_dir <- normalizePath(args[[1]], mustWork = TRUE)
organized_dir <- normalizePath(args[[2]], mustWork = TRUE)
files <- sort(list.files(annotation_dir, pattern = "_Final_anno[.]qs$", full.names = TRUE))
if (length(files) != 7) {
  stop(sprintf("Expected seven annotation qs files, found %d", length(files)))
}

nph_parts <- list()
non_nph_rows <- 0L
for (path in files) {
  frame <- qread(path)
  required <- c("sample", "ds_batch", "anno_batch", "anno_condition", "anno_region", "anno_age", "anno_sex")
  missing <- setdiff(required, names(frame))
  if (length(missing)) {
    stop(sprintf("Missing fields in %s: %s", basename(path), paste(missing, collapse = ",")))
  }
  keep <- frame$ds_batch == "human_NPH"
  non_nph_rows <- non_nph_rows + sum(!keep)
  part <- frame[keep, required, drop = FALSE]
  part$cell_class_file <- basename(path)
  nph_parts[[length(nph_parts) + 1L]] <- part
}

nph <- do.call(rbind, nph_parts)
if (anyDuplicated(nph$sample)) {
  stop("NPH cell identifiers are not unique across annotation objects")
}
if (!identical(sort(unique(nph$anno_region)), "PFC")) {
  stop("NPH annotation region is not exactly PFC")
}

donor_metadata <- unique(nph[c("anno_batch", "anno_condition", "anno_age", "anno_sex")])
if (anyDuplicated(donor_metadata$anno_batch)) {
  stop("Conflicting source metadata exist for an NPH donor")
}
cell_counts <- as.data.frame(table(nph$anno_batch), stringsAsFactors = FALSE)
names(cell_counts) <- c("anno_batch", "cell_count")
donors <- merge(donor_metadata, cell_counts, by = "anno_batch", sort = TRUE)
names(donors) <- c("donor_id", "pathology_group", "age", "sex", "cell_count")
donors <- donors[order(donors$donor_id), ]

groups <- table(donors$pathology_group)
source_files <- sort(list.files(organized_dir, pattern = "[.]qs$", full.names = TRUE))
if (length(source_files) != 7) {
  stop(sprintf("Expected seven exact NPH source objects, found %d", length(source_files)))
}
matrix_rows <- list()
feature_reference <- NULL
all_cells <- character()
for (path in source_files) {
  object <- qread(path)
  if (!is(object, "SingleCellExperiment")) {
    stop(sprintf("NPH source object is not SingleCellExperiment: %s", basename(path)))
  }
  if (!identical(assayNames(object), "counts")) {
    stop(sprintf("NPH source object does not contain exactly one counts assay: %s", basename(path)))
  }
  features <- rownames(object)
  if (is.null(feature_reference)) {
    feature_reference <- features
  } else if (!identical(features, feature_reference)) {
    stop(sprintf("NPH feature order differs in %s", basename(path)))
  }
  cells <- colnames(object)
  if (anyDuplicated(cells)) {
    stop(sprintf("Duplicate cells within %s", basename(path)))
  }
  all_cells <- c(all_cells, cells)
  column_data <- as.data.frame(colData(object))
  required_columns <- c("dataset", "status", "anno_batch")
  if (length(setdiff(required_columns, names(column_data)))) {
    stop(sprintf("Missing exact donor/status fields in %s", basename(path)))
  }
  matrix_rows[[length(matrix_rows) + 1L]] <- data.frame(
    source_object = basename(path),
    n_features = nrow(object),
    n_cells = ncol(object),
    assay_name = "counts",
    assay_class = class(assay(object, "counts"))[[1]],
    feature_identifier_type = "gene_symbol",
    donor_count = length(unique(column_data$dataset)),
    pathology_group_count = length(unique(column_data$status)),
    matrix_orientation = "gene_rows_by_cell_columns",
    stringsAsFactors = FALSE
  )
  rm(object)
  gc(verbose = FALSE)
}
if (anyDuplicated(all_cells)) {
  stop("NPH cell identifiers overlap across source cell-class objects")
}
matrix_audit <- do.call(rbind, matrix_rows)

summary <- data.frame(
  source_qs_count = length(files),
  nph_cell_count = nrow(nph),
  nph_unique_cell_count = length(unique(nph$sample)),
  nph_donor_count = nrow(donors),
  pathology_negative_donor_count = unname(groups[["Ctrl"]]),
  amyloid_positive_donor_count = unname(groups[["Abeta"]]),
  amyloid_tau_positive_donor_count = unname(groups[["AbetaTau"]]),
  integrated_non_nph_annotation_row_count = non_nph_rows,
  exact_nph_source_object_count = nrow(matrix_audit),
  matrix_nph_cell_count = sum(matrix_audit$n_cells),
  matrix_unique_nph_cell_count = length(unique(all_cells)),
  matrix_feature_count = length(feature_reference),
  matrix_exact_feature_order_shared = TRUE,
  matrix_semantics = "sparse_published_counts",
  nph_region = "PFC",
  donor_field = "anno_batch",
  pathology_field = "anno_condition",
  study_filter = "ds_batch == human_NPH",
  stringsAsFactors = FALSE
)

write.csv(donors, args[[3]], row.names = FALSE, quote = TRUE, na = "")
write.csv(summary, args[[4]], row.names = FALSE, quote = TRUE, na = "")
write.csv(matrix_audit, args[[5]], row.names = FALSE, quote = TRUE, na = "")
