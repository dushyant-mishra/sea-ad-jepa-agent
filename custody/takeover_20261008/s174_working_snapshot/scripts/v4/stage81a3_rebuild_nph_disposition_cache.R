#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 4L) {
  stop(paste(
    "Usage: stage81a3_rebuild_nph_disposition_cache.R",
    "<annotations_dir> <organized_dir> <detail_csv_gz> <summary_csv>"
  ))
}

suppressPackageStartupMessages(library(qs))
suppressPackageStartupMessages(library(SingleCellExperiment))

annotation_dir <- normalizePath(args[[1]], mustWork = TRUE)
organized_dir <- normalizePath(args[[2]], mustWork = TRUE)
detail_path <- args[[3]]
summary_path <- args[[4]]
annotation_files <- sort(list.files(
  annotation_dir, pattern = "_Final_anno[.]qs$", full.names = TRUE
))
source_files <- sort(list.files(
  organized_dir, pattern = "[.]qs$", full.names = TRUE
))
if (length(annotation_files) != 7L || length(source_files) != 7L) {
  stop("Expected exactly seven annotation and seven source QS objects")
}

final_parts <- list()
for (path in annotation_files) {
  frame <- qread(path)
  required <- c("sample", "ds_batch", "anno_batch")
  missing <- setdiff(required, names(frame))
  if (length(missing)) {
    stop(sprintf("Missing annotation fields in %s: %s", basename(path), paste(missing, collapse = ",")))
  }
  frame <- frame[frame$ds_batch == "human_NPH", required, drop = FALSE]
  final_parts[[length(final_parts) + 1L]] <- frame
}
final <- do.call(rbind, final_parts)
if (anyDuplicated(final$sample)) stop("Final NPH annotation cell identifiers are not globally unique")
final_index <- setNames(seq_len(nrow(final)), final$sample)
matched_final <- rep(FALSE, nrow(final))

dir.create(dirname(detail_path), recursive = TRUE, showWarnings = FALSE)
dir.create(dirname(summary_path), recursive = TRUE, showWarnings = FALSE)
detail_connection <- gzfile(detail_path, open = "wt")
writeLines(paste(c(
  "source_object", "source_study", "source_cell_id", "standardized_cell_id",
  "donor_id", "source_matrix_membership", "final_annotation_membership",
  "disposition", "evidence_field_or_source_file", "foundation_eligibility",
  "exclusion_reason"
), collapse = ","), detail_connection)

summary_rows <- list()
all_source_ids <- character()
for (path in source_files) {
  object <- qread(path)
  if (!is(object, "SingleCellExperiment") || !"counts" %in% assayNames(object)) {
    stop(sprintf("Invalid NPH source object: %s", basename(path)))
  }
  source_ids <- colnames(object)
  standardized_ids <- paste0("human_NPH_", source_ids)
  if (anyDuplicated(source_ids)) stop(sprintf("Duplicate source cell identifiers in %s", basename(path)))
  metadata <- as.data.frame(colData(object))
  required <- c("dataset", "status", "anno_batch")
  missing <- setdiff(required, names(metadata))
  if (length(missing)) {
    stop(sprintf("Missing source metadata in %s: %s", basename(path), paste(missing, collapse = ",")))
  }
  hit <- unname(final_index[standardized_ids])
  retained <- !is.na(hit)
  matched_final[hit[retained]] <- TRUE
  final_donor <- rep(NA_character_, length(source_ids))
  final_donor[retained] <- as.character(final$anno_batch[hit[retained]])
  source_donor <- as.character(metadata$anno_batch)
  standardized_source_donor <- paste0("human_", source_donor)
  donor <- ifelse(retained, final_donor, standardized_source_donor)
  donor_mismatch <- retained & !is.na(source_donor) & source_donor != "" & standardized_source_donor != final_donor
  disposition <- ifelse(retained, "retained_with_final_annotation", "missing_required_annotation")
  disposition[donor_mismatch] <- "source_annotation_mismatch"
  eligible <- disposition == "retained_with_final_annotation"
  reason <- ifelse(
    eligible, "",
    ifelse(
      disposition == "source_annotation_mismatch",
      "exact source and final donor identifiers disagree",
      "source cell has no exact final NPH annotation membership; no QC cause inferred"
    )
  )
  detail <- data.frame(
    source_object = basename(path), source_study = "NPH52",
    source_cell_id = source_ids, standardized_cell_id = standardized_ids,
    donor_id = donor, source_matrix_membership = TRUE,
    final_annotation_membership = retained, disposition = disposition,
    evidence_field_or_source_file = ifelse(
      retained,
      "exact human_NPH_ namespace prefix plus sample membership in *_Final_anno.qs",
      "exact human_NPH_ namespace prefix anti-join against ds_batch == human_NPH final annotations"
    ),
    foundation_eligibility = eligible, exclusion_reason = reason,
    stringsAsFactors = FALSE
  )
  write.table(
    detail, file = detail_connection, sep = ",", row.names = FALSE,
    col.names = FALSE, quote = TRUE, na = ""
  )
  counts <- as.data.frame(table(disposition), stringsAsFactors = FALSE)
  names(counts) <- c("disposition", "cell_count")
  counts$source_object <- basename(path)
  summary_rows[[length(summary_rows) + 1L]] <- counts[c("source_object", "disposition", "cell_count")]
  all_source_ids <- c(all_source_ids, source_ids)
  rm(object, detail)
  gc(verbose = FALSE)
}

close(detail_connection)
if (anyDuplicated(all_source_ids)) stop("NPH source cell identifiers overlap across source objects")
if (!all(matched_final)) stop(sprintf("%d final NPH annotations have no exact source cell", sum(!matched_final)))
summary <- do.call(rbind, summary_rows)
totals <- aggregate(cell_count ~ disposition, data = summary, FUN = sum)
totals$source_object <- "ALL_SOURCE_OBJECTS"
summary <- rbind(summary, totals[c("source_object", "disposition", "cell_count")])
summary <- summary[order(summary$source_object, summary$disposition), ]
write.csv(summary, summary_path, row.names = FALSE, quote = TRUE, na = "")

grand_total <- sum(totals$cell_count)
retained_total <- sum(totals$cell_count[totals$disposition == "retained_with_final_annotation"])
if (grand_total != 957659L || retained_total != 892828L) {
  stop(sprintf("Unexpected NPH totals: source=%d retained=%d", grand_total, retained_total))
}
message(sprintf(
  "NPH exact anti-join PASS: source=%d retained=%d excluded=%d",
  grand_total, retained_total, grand_total - retained_total
))
