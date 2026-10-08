#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2L) {
  stop("Usage: stage81a1d_audit_geo_rds.R OUTPUT.tsv INPUT.rds.gz [...]")
}

output_path <- args[[1L]]
input_paths <- args[-1L]
suppressPackageStartupMessages(library(Matrix))
suppressPackageStartupMessages(library(SeuratObject))

open_published_rds <- function(path) {
  first <- gzfile(path, open = "rb")
  on.exit(try(close(first), silent = TRUE), add = TRUE)
  magic <- readBin(first, what = "raw", n = 2L)
  close(first)

  if (identical(as.integer(magic), c(31L, 139L))) {
    outer <- gzfile(path, open = "rb")
    nested <- gzcon(outer)
    on.exit(try(close(nested), silent = TRUE), add = TRUE)
    return(list(object = readRDS(nested), compression_layers = 2L))
  }
  list(object = readRDS(gzfile(path, open = "rb")), compression_layers = 1L)
}

audit_one <- function(path) {
  loaded <- open_published_rds(path)
  object <- loaded$object
  dimensions <- dim(object)
  if (length(dimensions) != 2L) {
    stop(sprintf("Expected two-dimensional R object: %s", basename(path)))
  }
  row_ids <- rownames(object)
  column_ids <- colnames(object)
  if (is.null(row_ids) || is.null(column_ids)) {
    stop(sprintf("Missing row or column identifiers: %s", basename(path)))
  }
  data.frame(
    source_file = basename(path),
    object_class = paste(class(object), collapse = "|"),
    n_features = as.integer(dimensions[[1L]]),
    n_observations = as.integer(dimensions[[2L]]),
    row_ids_unique = !anyDuplicated(row_ids),
    column_ids_unique = !anyDuplicated(column_ids),
    row_id_example = paste(utils::head(row_ids, 3L), collapse = "|"),
    column_id_example = paste(utils::head(column_ids, 3L), collapse = "|"),
    compression_layers = loaded$compression_layers,
    stringsAsFactors = FALSE,
    check.names = FALSE
  )
}

rows <- vector("list", length(input_paths))
for (index in seq_along(input_paths)) {
  message(sprintf("RDS audit %d/%d: %s", index, length(input_paths), basename(input_paths[[index]])))
  rows[[index]] <- audit_one(input_paths[[index]])
  gc(verbose = FALSE)
}

result <- do.call(rbind, rows)
result <- result[order(result$source_file), , drop = FALSE]
dir.create(dirname(output_path), recursive = TRUE, showWarnings = FALSE)
temporary <- paste0(output_path, ".tmp")
utils::write.table(
  result,
  file = temporary,
  sep = "\t",
  quote = TRUE,
  row.names = FALSE,
  col.names = TRUE,
  na = ""
)
if (!file.rename(temporary, output_path)) {
  stop(sprintf("Could not finalize RDS audit: %s", output_path))
}
