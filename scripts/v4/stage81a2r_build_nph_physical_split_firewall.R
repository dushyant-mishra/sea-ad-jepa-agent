#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3L) {
  stop(paste(
    "Usage: stage81a2r_build_nph_physical_split_firewall.R",
    "<source_project> <output_root> <source_object_id>"
  ))
}

suppressPackageStartupMessages(library(digest))
suppressPackageStartupMessages(library(Matrix))
suppressPackageStartupMessages(library(qs))
suppressPackageStartupMessages(library(S4Vectors))
suppressPackageStartupMessages(library(SingleCellExperiment))

source_project <- normalizePath(args[[1]], mustWork = TRUE)
output_root <- normalizePath(args[[2]], mustWork = TRUE)
source_object_id <- args[[3]]
split_path <- file.path(source_project, "results/v4/stage81a2_split_registry.csv")
source_root <- file.path(
  source_project,
  "data/processed/v4/stage81a1d/sealed/nph52_organized/organized_data/Human/brain/snRNA/NPH"
)
matrix_audit_path <- file.path(
  source_project,
  "data/processed/v4/stage81a1d/sealed/nph52_exact_matrix_audit.csv"
)
source_manifest_path <- file.path(output_root, "nph52_physical_split_source_manifest.csv")

split <- read.csv(split_path, stringsAsFactors = FALSE)
foundation <- split[split$split_domain == "foundation", , drop = FALSE]
expected_totals <- c(train = 149L, development = 19L, sealed_holdout = 19L)
actual_totals <- table(factor(foundation$split, levels = names(expected_totals)))
if (!identical(as.integer(actual_totals), as.integer(expected_totals))) {
  stop("Frozen 149/19/19 foundation split contract mismatch")
}
pathology_split_flag <- tolower(as.character(foundation$pathology_used_for_foundation_split))
if (any(pathology_split_flag %in% c("true", "1", "yes"))) stop("Frozen split reports pathology use")
partition_labels <- c(train = "TRAIN", development = "DEV", sealed_holdout = "SEALED")
donors <- lapply(names(partition_labels), function(name) {
  value <- foundation$canonical_person_id[foundation$study_id == "NPH52" & foundation$split == name]
  sub("^NPH52::", "", value)
})
names(donors) <- unname(partition_labels)
if (!identical(vapply(donors, length, integer(1)), c(TRAIN = 19L, DEV = 3L, SEALED = 3L))) {
  stop("Frozen NPH 19/3/3 split contract mismatch")
}
if (length(unique(unlist(donors))) != sum(vapply(donors, length, integer(1)))) {
  stop("Frozen NPH donor split overlap")
}

split_sha256 <- digest(file = split_path, algo = "sha256", serialize = FALSE)
source_manifest <- read.csv(source_manifest_path, stringsAsFactors = FALSE)
if (nrow(source_manifest) != 7L || any(source_manifest$frozen_split_manifest_sha256 != split_sha256)) {
  stop("Pre-qread source manifest or frozen split hash mismatch")
}
manifest_row <- source_manifest[source_manifest$source_object_id == source_object_id, , drop = FALSE]
if (nrow(manifest_row) != 1L) stop("Requested source object absent from pre-qread manifest")
path <- file.path(source_root, source_object_id)
if (!file.exists(path) || file.info(path)$size != manifest_row$source_size_bytes) {
  stop("Authoritative source object size changed after manifest construction")
}
matrix_audit <- read.csv(matrix_audit_path, stringsAsFactors = FALSE)
expected <- matrix_audit[matrix_audit$source_object == source_object_id, , drop = FALSE]
if (nrow(expected) != 1L) stop("Source matrix contract missing")

hash_character <- function(values) digest(as.character(values), algo = "sha256", serialize = TRUE)
hash_sparse <- function(value) {
  if (!inherits(value, "dgCMatrix")) stop("Counts are not dgCMatrix")
  digest(
    list(class = class(value), Dim = value@Dim, p = value@p, i = value@i, x = value@x),
    algo = "sha256",
    serialize = TRUE
  )
}
hash_row_data <- function(value) digest(value, algo = "sha256", serialize = TRUE)

message(sprintf("INGESTION qread exactly once: %s", source_object_id))
object <- qread(path)
if (!inherits(object, "SingleCellExperiment")) stop("Invalid source object")
if (!identical(assayNames(object), "counts")) stop("Unexpected source assays")
counts <- assay(object, "counts")
if (!inherits(counts, "dgCMatrix")) stop("Unexpected count class")
if (nrow(object) != expected$n_features || ncol(object) != expected$n_cells) {
  stop("Source dimensions changed")
}
if (!("anno_batch" %in% colnames(colData(object)))) stop("Stable donor field anno_batch missing")
pathology_pattern <- "path|diagn|braak|cerad|amyloid|abeta|tau|disease"
pathology_schema_detected <- any(grepl(pathology_pattern, colnames(colData(object)), ignore.case = TRUE))
source_donor <- paste0("human_", as.character(colData(object)$anno_batch))
source_cell <- colnames(object)
if (anyNA(source_donor) || any(source_donor == "human_")) stop("Missing source donor identity")
if (anyDuplicated(source_cell)) stop("Duplicate source cell IDs")
row_data <- rowData(object)
expected_rows <- list()

for (partition in names(donors)) {
  columns <- which(source_donor %in% donors[[partition]])
  source_subset <- counts[, columns, drop = FALSE]
  derivative <- SingleCellExperiment(
    assays = list(counts = source_subset),
    rowData = row_data,
    colData = DataFrame(
      source_cell_id = source_cell[columns],
      source_donor_id = source_donor[columns]
    )
  )
  rownames(derivative) <- rownames(object)
  colnames(derivative) <- source_cell[columns]
  destination_dir <- file.path(output_root, partition)
  dir.create(destination_dir, recursive = TRUE, showWarnings = FALSE)
  destination <- file.path(
    destination_dir,
    sub("[.]qs$", paste0(".", partition, ".full_features.qs"), source_object_id)
  )
  temporary <- paste0(destination, ".part")
  if (file.exists(temporary)) unlink(temporary)
  expected_rows[[length(expected_rows) + 1L]] <- data.frame(
    source_object_id = source_object_id,
    partition = partition,
    derivative_path = normalizePath(destination, winslash = "/", mustWork = FALSE),
    expected_cell_count = ncol(derivative),
    expected_feature_count = nrow(derivative),
    expected_cell_id_order_sha256 = hash_character(colnames(derivative)),
    expected_feature_id_order_sha256 = hash_character(rownames(derivative)),
    expected_row_data_sha256 = hash_row_data(rowData(derivative)),
    expected_sparse_count_sha256 = hash_sparse(assay(derivative, "counts")),
    expected_count_class = class(assay(derivative, "counts"))[[1]],
    expected_count_storage_type = typeof(assay(derivative, "counts")@x),
    retained_column_metadata = "source_cell_id|source_donor_id",
    pathology_bytes_transiently_deserialized_in_ingestion_boundary = pathology_schema_detected,
    stringsAsFactors = FALSE
  )
  qsave(derivative, temporary, preset = "high", nthreads = 4)
  if (file.exists(destination)) unlink(destination)
  if (!file.rename(temporary, destination)) stop("Atomic derivative rename failed")
  rm(derivative, source_subset)
  gc(verbose = FALSE)
}

expected_manifest_dir <- file.path(output_root, "expected")
dir.create(expected_manifest_dir, recursive = TRUE, showWarnings = FALSE)
write.csv(
  do.call(rbind, expected_rows),
  file.path(expected_manifest_dir, paste0(source_object_id, ".expected.csv")),
  row.names = FALSE,
  quote = TRUE
)
message(sprintf("NPH physical split write PASS: %s", source_object_id))
