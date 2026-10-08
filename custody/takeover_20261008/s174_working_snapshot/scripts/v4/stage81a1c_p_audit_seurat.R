#!/usr/bin/env Rscript

suppressPackageStartupMessages(library(SeuratObject))

args <- commandArgs(trailingOnly = TRUE)
project <- if (length(args) >= 1) normalizePath(args[[1]], mustWork = TRUE) else getwd()
output <- if (length(args) >= 2) args[[2]] else "results/v4/stage81a1c_p_seurat_object_audit.csv"
output_path <- file.path(project, output)
root <- file.path(project, "data/external/v4/perturbation/GSE301119")
files <- sort(list.files(root, pattern = "\\.rds$", full.names = TRUE))

if (length(files) != 2) {
  stop(sprintf("Expected exactly two GSE301119 RDS objects, found %d", length(files)))
}

collapse_values <- function(values) {
  paste(sort(unique(as.character(values[!is.na(values)]))), collapse = ";")
}

rows <- lapply(files, function(path) {
  object <- readRDS(path)
  metadata <- object[[]]
  required <- c("guide_identity", "Gene_Targeted", "donor", "crispr")
  missing <- setdiff(required, colnames(metadata))
  guide_values <- as.character(metadata$guide_identity)
  control <- grepl("(^|[_ -])(ntc|non.?target|control|safe)", guide_values, ignore.case = TRUE)
  layers <- unlist(lapply(Assays(object), function(assay) {
    paste0(assay, ":", paste(Layers(object[[assay]]), collapse = "+"))
  }))
  pass <- inherits(object, "Seurat") && length(missing) == 0 && sum(control, na.rm = TRUE) > 0

  data.frame(
    accession = "GSE301119",
    source_path = substring(normalizePath(path), nchar(project) + 2),
    object_class = paste(class(object), collapse = ";"),
    n_features = nrow(object),
    n_cells = ncol(object),
    assays = paste(Assays(object), collapse = ";"),
    default_assay = DefaultAssay(object),
    assay_layers = paste(layers, collapse = ";"),
    metadata_columns = paste(colnames(metadata), collapse = ";"),
    n_guide_identities = length(unique(guide_values)),
    n_target_genes = length(unique(as.character(metadata$Gene_Targeted))),
    n_non_targeting_control_cells = sum(control, na.rm = TRUE),
    n_non_targeting_control_guides = length(unique(guide_values[control])),
    donor_count = length(unique(as.character(metadata$donor))),
    donor_values = collapse_values(metadata$donor),
    crispr_values = collapse_values(metadata$crispr),
    missing_required_metadata = paste(missing, collapse = ";"),
    r_version = paste(R.version$major, R.version$minor, sep = "."),
    seurat_object_version = as.character(packageVersion("SeuratObject")),
    expression_matrix_materialized = FALSE,
    full_object_audit_pass = pass,
    stringsAsFactors = FALSE
  )
})

result <- do.call(rbind, rows)
if (!all(result$full_object_audit_pass)) {
  stop("One or more Seurat objects failed the full-object audit")
}
dir.create(dirname(output_path), recursive = TRUE, showWarnings = FALSE)
temporary <- paste0(output_path, ".tmp")
write.csv(result, temporary, row.names = FALSE, na = "")
if (!file.rename(temporary, output_path)) {
  stop("Atomic promotion of Seurat audit output failed")
}
cat(sprintf("Wrote: %s\n", output_path))
cat(sprintf("Seurat objects audited: %d\n", nrow(result)))
