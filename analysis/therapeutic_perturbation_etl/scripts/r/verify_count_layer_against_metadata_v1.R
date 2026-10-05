#!/usr/bin/env Rscript
# Independent verification of the attribute-only count reader WITHOUT SeuratObject >= 5.
#
# Why this exists: the PR #81 parity checker requires SeuratObject >= 5, which is
# not installed on this machine (only 4.1.0 is present). That check is therefore
# NOT_EXECUTED here and must not be reported as passed.
#
# This is a different, independent route to the same question. Seurat 5.4.0 computed
# nCount_RNA and nFeature_RNA when it BUILT the object and stored them in meta.data.
# Those fields were produced by the official implementation, not by us. If the
# attribute-only reader's per-cell column sums and nonzero counts reproduce them
# EXACTLY, the sparse count payload is being decoded correctly.
#
# This is a real external oracle: the values come from the producing software and
# are carried inside the file, independent of how we read the matrix.
#
# Reads counts only. No JEPA, no FULL104, no training.

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 3) stop("usage: <object.rds> <out.csv> <tag>")
path <- normalizePath(args[[1]], mustWork = TRUE)
out <- args[[2]]; tag <- args[[3]]

x <- readRDS(path)
a <- attributes(x)
md <- a$meta.data
rna <- a$assays[["RNA"]]
ra <- attributes(rna)
L <- ra$layers[["counts"]]

# NB: the class attribute carries a `package` attribute, so identical() against a
# bare string is False even when the class IS dgCMatrix. Compare as character.
if (!identical(as.character(attr(L, "class")), "dgCMatrix")) {
  stop(paste("expected dgCMatrix count layer, found:",
             paste(as.character(attr(L, "class")), collapse = ",")))
}

Dim <- attr(L, "Dim"); i <- attr(L, "i"); p <- attr(L, "p"); xv <- attr(L, "x")
features <- attr(ra$features, "dimnames")[[1]]
cells <- attr(ra$cells, "dimnames")[[1]]

stopifnot(Dim[1] == length(features), Dim[2] == length(cells),
          identical(rownames(md), cells))

ncell <- Dim[2]
col_sum <- numeric(ncell)
col_nnz <- integer(ncell)
for (c in seq_len(ncell)) {
  lo <- p[c] + 1L; hi <- p[c + 1L]
  if (hi >= lo) {
    v <- xv[lo:hi]
    col_sum[c] <- sum(v)
    col_nnz[c] <- sum(v > 0)
  }
}

# The external oracle: fields written by Seurat 5.4.0 itself.
oracle_count <- as.numeric(md$nCount_RNA)
oracle_feat  <- as.numeric(md$nFeature_RNA)

exact_count <- identical(as.numeric(col_sum), oracle_count)
exact_feat  <- identical(as.numeric(col_nnz), oracle_feat)
max_abs_count <- max(abs(col_sum - oracle_count))
max_abs_feat  <- max(abs(col_nnz - oracle_feat))
n_mismatch_count <- sum(col_sum != oracle_count)
n_mismatch_feat  <- sum(col_nnz != oracle_feat)

integral <- all(xv == floor(xv))
nonneg <- all(xv >= 0)

pass <- exact_count && exact_feat && integral && nonneg

row <- data.frame(
  tag = tag, source_path = path,
  oracle = "Seurat_5.4.0_meta.data_nCount_RNA_and_nFeature_RNA",
  seuratobject_ge5_available = FALSE,
  n_features = Dim[1], n_cells = Dim[2], nnz = length(xv),
  colsums_exactly_match_nCount_RNA = exact_count,
  colnnz_exactly_match_nFeature_RNA = exact_feat,
  n_cells_mismatched_count = n_mismatch_count,
  n_cells_mismatched_nfeature = n_mismatch_feat,
  max_abs_diff_count = max_abs_count,
  max_abs_diff_nfeature = max_abs_feat,
  counts_integral = integral, counts_nonnegative = nonneg,
  attribute_reader_verified = pass,
  stringsAsFactors = FALSE
)
dir.create(dirname(out), recursive = TRUE, showWarnings = FALSE)
tmp <- paste0(out, ".tmp")
write.csv(row, tmp, row.names = FALSE)
if (!file.rename(tmp, out)) stop("atomic promotion failed")

cat(tag, "cells:", Dim[2], " nnz:", length(xv), "\n")
cat(tag, "colSums == nCount_RNA exactly:", exact_count,
    " mismatched cells:", n_mismatch_count, " max|diff|:", max_abs_count, "\n")
cat(tag, "colNNZ == nFeature_RNA exactly:", exact_feat,
    " mismatched cells:", n_mismatch_feat, " max|diff|:", max_abs_feat, "\n")
if (!pass) stop("attribute-only count reader disagrees with the object's own metadata")
cat("PASS_ATTRIBUTE_READER_VERIFIED_AGAINST_PRODUCER_METADATA\n")
