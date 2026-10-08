#!/usr/bin/env Rscript
# Dump the feature (row) names of an NPH52 .qs derivative, in object order.
#
# The FULL104 Level-4 gene-identity defect turns on ONE question per source:
# does the provenance table's `source_feature_index` enumerate the source
# object's own feature order, or some other order? For the HDF5 sources that
# question is answerable from Python. NPH52 is an R `.qs` SingleCellExperiment,
# so its feature axis has to come out of R.
#
# This script does nothing but read the object and write its rownames in order.
# It deliberately does not touch counts, so it cannot be a route to expression
# data, and it is cheap enough to re-run as a check rather than trusting a
# cached copy.
#
# The `qs` package needs Rcpp, RcppParallel, RApiSerialize and stringfish. On
# this machine `qs` and its C++ helpers live in the project's .r-library while
# Rcpp lives in the user library, so BOTH paths must be supplied.
#
# usage: Rscript dump_nph52_feature_names_v1.R <lib1> <lib2> <input.qs> <out.txt>

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 4L) {
  stop("usage: <libpath1> <libpath2> <input.qs> <out.txt>")
}
.libPaths(c(args[[1]], args[[2]], .libPaths()))
suppressMessages(library(qs))

obj <- qread(args[[3]])

# Take the axis from the SAME expression the materializer indexes, which is
# assay(object, "counts") - see materialize_full104_phase2_nph_blocks.R:
#   counts <- assay(object, "counts")
#   local  <- t(counts[mapping$source_feature_index + 1L, columns[take], ])
# Asking `rownames(obj)` instead is not equivalent: with SingleCellExperiment
# attached, S4 dispatch on the container returned NULL here while the assay
# carried the 33,441 feature names. Verifying a different axis than the one the
# materializer indexes would prove nothing about the materializer.
suppressMessages(library(SummarizedExperiment))
mat <- assay(obj, "counts")
rn <- rownames(mat)
if (is.null(rn) || !length(rn)) {
  rn <- rownames(obj)
}
if (is.null(rn) || !length(rn)) {
  stop("neither assay(obj,'counts') nor the object carries rownames; the ",
       "feature axis cannot be established")
}
cat("assay_dim:", paste(dim(mat), collapse = " x "), "\n")
if (anyDuplicated(rn)) {
  stop("duplicate feature names; positional verification would be ambiguous")
}
cat("class:", paste(class(obj), collapse = ","), "\n")
cat("n_features:", length(rn), "\n")
cat("first10:", paste(head(rn, 10), collapse = " | "), "\n")
writeLines(rn, args[[4]])
cat("wrote", length(rn), "feature names\n")
