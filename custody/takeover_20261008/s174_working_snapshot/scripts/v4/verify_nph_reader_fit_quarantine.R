#!/usr/bin/env Rscript

# Fresh-process verifier. This script has no code path to the original mixed
# NPH derivatives and opens only the newly created reader-fit-only assets.

args <- commandArgs(trailingOnly=TRUE)
if (length(args) != 2L) stop("usage: <project-root> <staging-envelope>")
.libPaths(c(file.path(args[[1]], ".r-library"), .libPaths()))
suppressPackageStartupMessages(library(digest))
suppressPackageStartupMessages(library(qs))
suppressPackageStartupMessages(library(SingleCellExperiment))
project <- normalizePath(args[[1]],mustWork=TRUE)
staging <- normalizePath(args[[2]],mustWork=TRUE)
package <- file.path(staging,"FULL104_EXPRESSION_INTERFACE_V8")

reader_path <- file.path(project,"exports/contextual_biology_v6r5a_20260822/reader_donor_split.csv")
reader_sha <- digest(reader_path,algo="sha256",file=TRUE)
if (reader_sha != "efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511") stop("reader split authority hash mismatch")
reader <- read.csv(reader_path,stringsAsFactors=FALSE)
fit_donors <- sort(reader$donor_id[reader$reader_partition == "reader_fit" & grepl("^human_NPH_",reader$donor_id)])
protected <- c("human_NPH_1025","human_NPH_878")

package_expected <- read.csv(gzfile(file.path(package,"NPH_READER_FIT_EXPECTED_LINEAGE.csv.gz")),stringsAsFactors=FALSE)
meta <- file.path(project,"outputs/full104_v014_20260826/01_full104_metadata_adapter")
meta_manifest_path <- file.path(meta,"FULL104_ADAPTER_SHA256_MANIFEST.csv")
if (digest(meta_manifest_path,algo="sha256",file=TRUE) != "54e4ba5b60e9c5d3ff23a307df03576f45ac725f3b71642888500a469ebdbc74") stop("metadata manifest external hash mismatch")
meta_manifest <- read.csv(meta_manifest_path,stringsAsFactors=FALSE)
verify_meta_file <- function(relative) {
  row <- meta_manifest[meta_manifest$path == relative,,drop=FALSE]
  if (nrow(row) != 1L) stop("metadata manifest row missing")
  path <- file.path(meta,relative)
  if (!file.exists(path) || file.info(path)$size != row$bytes[[1]] || digest(path,algo="sha256",file=TRUE) != row$sha256[[1]]) stop("frozen metadata artifact authentication failed")
  path
}
index <- read.csv(verify_meta_file("FULL104_ROW_LINEAGE.csv"),stringsAsFactors=FALSE)
index <- index[index$source == "NPH52",,drop=FALSE]
if (nrow(index) != 7L || !identical(sort(index$operator_index),35:41)) stop("independent NPH lineage index mismatch")
authority_parts <- lapply(seq_len(nrow(index)),function(i) {
  x <- read.csv(gzfile(verify_meta_file(index$path[[i]])),stringsAsFactors=FALSE)
  x[,c("operator_index","matrix_id","donor_id","canonical_cell_id","source_row","row_locator")]
})
expected <- do.call(rbind,authority_parts);expected <- expected[order(expected$operator_index,expected$source_row),,drop=FALSE]
package_expected <- package_expected[order(package_expected$operator_index,package_expected$source_row),names(expected),drop=FALSE]
if (!identical(package_expected,expected)) stop("package expected lineage differs from independently authenticated frozen shards")
manifest <- read.csv(file.path(package,"NPH_READER_FIT_DERIVATIVE_MANIFEST.csv"),stringsAsFactors=FALSE)
if (nrow(manifest) != 7L || !identical(sort(manifest$operator_index),35:41)) stop("derivative manifest geometry mismatch")
verified <- list(); observed_cells <- character(); observed_donors <- character()
for (i in seq_len(nrow(manifest))) {
  row <- manifest[i,,drop=FALSE]
  derivative <- normalizePath(file.path(package,row$derivative_relative_path[[1]]),mustWork=TRUE)
  package_key <- paste0(tolower(gsub("\\\\","/",normalizePath(package))),"/")
  derivative_key <- tolower(gsub("\\\\","/",derivative))
  if (!startsWith(derivative_key,package_key)) stop("derivative escaped package")
  if (file.info(derivative)$size != row$derivative_size_bytes[[1]] || digest(derivative,algo="sha256",file=TRUE) != row$derivative_sha256[[1]]) stop("fit-only derivative hash mismatch")
  object <- qread(derivative)
  cells <- as.character(colnames(object)); donors <- as.character(colData(object)$source_donor_id)
  exp_rows <- expected[expected$operator_index == row$operator_index[[1]],,drop=FALSE]
  if (!identical(cells,as.character(exp_rows$canonical_cell_id)) || !identical(donors,as.character(exp_rows$donor_id))) stop("fresh derivative/lineage mismatch")
  if (any(donors %in% protected) || any(!(donors %in% fit_donors)) || anyDuplicated(cells)) stop("protected, non-fit, or duplicate derivative row")
  observed_cells <- c(observed_cells,cells); observed_donors <- c(observed_donors,donors)
  verified[[length(verified)+1L]] <- data.frame(operator_index=row$operator_index[[1]],matrix_id=row$matrix_id[[1]],cell_count=length(cells),donor_count=length(unique(donors)),derivative_sha256=row$derivative_sha256[[1]],lineage_exact=TRUE,protected_absent=TRUE,stringsAsFactors=FALSE)
  rm(object,cells,donors);gc(verbose=FALSE)
}
if (length(observed_cells) != 236476L || anyDuplicated(observed_cells) || length(unique(observed_donors)) != 17L || !identical(sort(unique(observed_donors)),fit_donors)) stop("fresh verification global totals mismatch")
if (!setequal(observed_cells,expected$canonical_cell_id) || length(observed_cells) != nrow(expected)) stop("fresh verification has extra or missing lineage rows")
write.csv(do.call(rbind,verified),file.path(package,"NPH_READER_FIT_FRESH_PROCESS_VERIFICATION.csv"),row.names=FALSE,quote=TRUE)
status <- c(
  '{','  "status": "PASS_NPH_READER_FIT_PHYSICAL_FIREWALL",','  "fresh_process": true,',
  '  "opened_original_mixed_nph_assets": false,','  "derivatives": 7,','  "fit_donors": 17,','  "fit_cells": 236476,',
  '  "human_NPH_1025_absent": true,','  "human_NPH_878_absent": true,','  "lineage_exact_no_extra_missing": true,',
  '  "frozen_lineage_shards_independently_authenticated_and_reopened": true,',
  '  "phase2_started": false','}'
)
writeLines(status,file.path(package,"NPH_READER_FIT_FRESH_PROCESS_STATUS.json"),useBytes=TRUE)
cat("PASS_NPH_READER_FIT_PHYSICAL_FIREWALL\n")
