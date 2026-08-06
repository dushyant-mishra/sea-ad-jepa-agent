#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3) {
  stop("Usage: stage81a1d_audit_nph_annotations.R <annotations_dir> <donors_csv> <summary_csv>")
}

suppressPackageStartupMessages(library(qs))
annotation_dir <- normalizePath(args[[1]], mustWork = TRUE)
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
summary <- data.frame(
  source_qs_count = length(files),
  nph_cell_count = nrow(nph),
  nph_unique_cell_count = length(unique(nph$sample)),
  nph_donor_count = nrow(donors),
  pathology_negative_donor_count = unname(groups[["Ctrl"]]),
  amyloid_positive_donor_count = unname(groups[["Abeta"]]),
  amyloid_tau_positive_donor_count = unname(groups[["AbetaTau"]]),
  integrated_non_nph_annotation_row_count = non_nph_rows,
  nph_region = "PFC",
  donor_field = "anno_batch",
  pathology_field = "anno_condition",
  study_filter = "ds_batch == human_NPH",
  stringsAsFactors = FALSE
)

write.csv(donors, args[[2]], row.names = FALSE, quote = TRUE, na = "")
write.csv(summary, args[[3]], row.names = FALSE, quote = TRUE, na = "")
