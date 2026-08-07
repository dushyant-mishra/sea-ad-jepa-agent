#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (!(length(args) %in% c(4L, 5L, 7L))) {
  stop(paste(
    "Usage: stage81a2_audit_nph_freeze.R",
    "<annotations_dir> <organized_dir> <detail_csv_gz> <summary_csv>",
    "[feature_csv_gz [split_registry_csv donor_gene_stats_csv_gz]]"
  ))
}

suppressPackageStartupMessages(library(qs))
suppressPackageStartupMessages(library(SingleCellExperiment))

annotation_dir <- normalizePath(args[[1]], mustWork = TRUE)
organized_dir <- normalizePath(args[[2]], mustWork = TRUE)
detail_path <- args[[3]]
summary_path <- args[[4]]

annotation_files <- sort(list.files(
  annotation_dir,
  pattern = "_Final_anno[.]qs$",
  full.names = TRUE
))
source_files <- sort(list.files(
  organized_dir,
  pattern = "[.]qs$",
  full.names = TRUE
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
  frame$annotation_object <- basename(path)
  final_parts[[length(final_parts) + 1L]] <- frame
}
final <- do.call(rbind, final_parts)
if (anyDuplicated(final$sample)) {
  stop("Final NPH annotation cell identifiers are not globally unique")
}
final_index <- setNames(seq_len(nrow(final)), final$sample)
matched_final <- rep(FALSE, nrow(final))

dir.create(dirname(detail_path), recursive = TRUE, showWarnings = FALSE)
dir.create(dirname(summary_path), recursive = TRUE, showWarnings = FALSE)
detail_connection <- gzfile(detail_path, open = "wt")
on.exit(close(detail_connection), add = TRUE)
writeLines(paste(c(
  "source_object", "source_study", "source_cell_id", "standardized_cell_id",
  "donor_id", "source_matrix_membership", "final_annotation_membership",
  "disposition", "evidence_field_or_source_file", "foundation_eligibility",
  "exclusion_reason"
), collapse = ","), detail_connection)

summary_rows <- list()
feature_rows <- list()
all_source_ids <- character()
for (path in source_files) {
  object <- qread(path)
  if (!is(object, "SingleCellExperiment") || !"counts" %in% assayNames(object)) {
    stop(sprintf("Invalid NPH source object: %s", basename(path)))
  }
  source_ids <- colnames(object)
  standardized_ids <- paste0("human_NPH_", source_ids)
  if (anyDuplicated(source_ids)) {
    stop(sprintf("Duplicate source cell identifiers in %s", basename(path)))
  }
  metadata <- as.data.frame(colData(object))
  required <- c("dataset", "status", "anno_batch")
  missing <- setdiff(required, names(metadata))
  if (length(missing)) {
    stop(sprintf("Missing source metadata in %s: %s", basename(path), paste(missing, collapse = ",")))
  }
  hit <- match(standardized_ids, final$sample)
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
    eligible,
    "",
    ifelse(
      disposition == "source_annotation_mismatch",
      "exact source and final donor identifiers disagree",
      "source cell has no exact final NPH annotation membership; no QC cause inferred"
    )
  )
  detail <- data.frame(
    source_object = basename(path),
    source_study = "NPH52",
    source_cell_id = source_ids,
    standardized_cell_id = standardized_ids,
    donor_id = donor,
    source_matrix_membership = TRUE,
    final_annotation_membership = retained,
    disposition = disposition,
    evidence_field_or_source_file = ifelse(
      retained,
      "exact human_NPH_ namespace prefix plus sample membership in *_Final_anno.qs",
      "exact human_NPH_ namespace prefix anti-join against ds_batch == human_NPH final annotations"
    ),
    foundation_eligibility = eligible,
    exclusion_reason = reason,
    stringsAsFactors = FALSE
  )
  write.table(
    detail,
    file = detail_connection,
    sep = ",",
    row.names = FALSE,
    col.names = FALSE,
    quote = TRUE,
    na = ""
  )
  counts <- as.data.frame(table(disposition), stringsAsFactors = FALSE)
  names(counts) <- c("disposition", "cell_count")
  counts$source_object <- basename(path)
  summary_rows[[length(summary_rows) + 1L]] <- counts[c("source_object", "disposition", "cell_count")]
  if (length(args) >= 5L) {
    feature_rows[[length(feature_rows) + 1L]] <- data.frame(
      source_object = basename(path),
      source_feature_index = seq_len(nrow(object)) - 1L,
      source_feature_symbol = rownames(object),
      source_feature_type = "Gene Expression",
      stringsAsFactors = FALSE
    )
  }
  all_source_ids <- c(all_source_ids, source_ids)
  rm(object, detail)
  gc(verbose = FALSE)
}

if (anyDuplicated(all_source_ids)) {
  stop("NPH source cell identifiers overlap across source objects")
}
if (!all(matched_final)) {
  stop(sprintf("%d final NPH annotations have no exact source cell", sum(!matched_final)))
}

summary <- do.call(rbind, summary_rows)
totals <- aggregate(cell_count ~ disposition, data = summary, FUN = sum)
totals$source_object <- "ALL_SOURCE_OBJECTS"
summary <- rbind(summary, totals[c("source_object", "disposition", "cell_count")])
summary <- summary[order(summary$source_object, summary$disposition), ]
write.csv(summary, summary_path, row.names = FALSE, quote = TRUE, na = "")
if (length(args) >= 5L) {
  feature_connection <- gzfile(args[[5]], open = "wt")
  write.csv(do.call(rbind, feature_rows), feature_connection, row.names = FALSE, quote = TRUE, na = "")
  close(feature_connection)
}

if (length(args) == 7L) {
  split_registry <- read.csv(args[[6]], stringsAsFactors = FALSE)
  train_donors <- split_registry$canonical_person_id[
    split_registry$cohort == "NPH_Ctrl" & split_registry$split == "train"
  ]
  train_donors <- sub("^NPH52::", "", train_donors)
  if (length(train_donors) != 19L) {
    stop(sprintf("Expected 19 NPH control training donors, found %d", length(train_donors)))
  }
  all_features <- sort(unique(unlist(lapply(source_files, function(path) {
    object <- qread(path)
    features <- rownames(object)
    rm(object)
    gc(verbose = FALSE)
    features
  }))))
  donor_sum <- matrix(0, nrow = length(all_features), ncol = length(train_donors),
                      dimnames = list(all_features, train_donors))
  donor_detection <- donor_sum
  donor_measured_cell_count <- donor_sum
  class_coverage <- integer(length(all_features))
  names(class_coverage) <- all_features
  sample_cap <- 16L
  for (path in source_files) {
    object <- qread(path)
    counts <- assay(object, "counts")
    metadata <- as.data.frame(colData(object))
    standardized_donor <- paste0("human_", as.character(metadata$anno_batch))
    standardized_cell <- paste0("human_NPH_", colnames(object))
    retained <- standardized_cell %in% final$sample
    feature_index <- match(rownames(object), all_features)
    class_detected <- rep(FALSE, nrow(object))
    for (donor in train_donors) {
      columns <- which(retained & standardized_donor == donor)
      if (!length(columns)) next
      if (length(columns) > sample_cap) {
        columns <- columns[unique(round(seq(1, length(columns), length.out = sample_cap)))]
      }
      block <- counts[, columns, drop = FALSE]
      library_size <- Matrix::colSums(block)
      if (any(library_size <= 0)) {
        stop(sprintf("Zero-library selected NPH cell in %s for %s", basename(path), donor))
      }
      transformed <- block %*% Matrix::Diagonal(x = 10000 / library_size)
      transformed@x <- log1p(transformed@x)
      donor_sum[feature_index, donor] <- donor_sum[feature_index, donor] + Matrix::rowSums(transformed)
      donor_detection[feature_index, donor] <- donor_detection[feature_index, donor] + Matrix::rowSums(block > 0)
      donor_measured_cell_count[feature_index, donor] <- donor_measured_cell_count[feature_index, donor] + length(columns)
      class_detected <- class_detected | Matrix::rowSums(block > 0) > 0
    }
    class_coverage[feature_index[class_detected]] <- class_coverage[feature_index[class_detected]] + 1L
    rm(object, counts)
    gc(verbose = FALSE)
  }
  observed <- donor_measured_cell_count > 0
  donor_mean <- donor_sum
  donor_detect <- donor_detection
  donor_mean[observed] <- donor_sum[observed] / donor_measured_cell_count[observed]
  donor_detect[observed] <- donor_detection[observed] / donor_measured_cell_count[observed]
  donor_mean[!observed] <- NA_real_
  donor_detect[!observed] <- NA_real_
  gene_stats <- data.frame(
    source_feature_symbol = all_features,
    training_donors_measured = rowSums(observed),
    donor_balanced_detection_rate = rowMeans(donor_detect, na.rm = TRUE),
    donor_balanced_mean_log1p = rowMeans(donor_mean, na.rm = TRUE),
    donor_balanced_expression_variability = apply(donor_mean, 1, stats::var, na.rm = TRUE),
    broad_class_objects_detected = unname(class_coverage[all_features]),
    sample_cap_per_donor_class_object = sample_cap,
    normalization_target = 10000,
    expression_transform = "per_cell_library_size_normalize_then_log1p",
    detection_definition = "raw_counts_greater_than_zero",
    donor_aggregation = "actual_selected_cell_weighted_with_source_measurement_mask",
    stringsAsFactors = FALSE
  )
  stats_connection <- gzfile(args[[7]], open = "wt")
  write.csv(gene_stats, stats_connection, row.names = FALSE, quote = TRUE, na = "")
  close(stats_connection)
}

grand_total <- sum(totals$cell_count)
retained_total <- sum(totals$cell_count[totals$disposition == "retained_with_final_annotation"])
if (grand_total != 957659L || retained_total != 892828L) {
  stop(sprintf("Unexpected NPH totals: source=%d retained=%d", grand_total, retained_total))
}
message(sprintf(
  "NPH exact anti-join PASS: source=%d retained=%d excluded=%d",
  grand_total,
  retained_total,
  grand_total - retained_total
))
