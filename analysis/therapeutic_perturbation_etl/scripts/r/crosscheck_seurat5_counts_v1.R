#!/usr/bin/env Rscript
# Independent count-layer parity check for the GSE301119 attribute-only reader.
#
# Run in the historical Stage81 SeuratObject >=5 environment. This compares the
# public SeuratObject accessor with the exact sparse payload used by the
# attribute-only ETL. It does not train JEPA or inspect FULL104.

suppressPackageStartupMessages(library(SeuratObject))

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) stop("usage: crosscheck_seurat5_counts_v1.R <object.rds> <out.csv>")
path <- normalizePath(args[[1]], mustWork = TRUE)
out <- args[[2]]

x <- readRDS(path)
if (!inherits(x, "Seurat")) stop("object is not Seurat")
if (packageVersion("SeuratObject") < "5.0.0") stop("SeuratObject >=5 required")

official <- LayerData(x[["RNA"]], layer = "counts")
if (!inherits(official, "sparseMatrix")) stop("official count layer is not sparse")

a <- attributes(x)
rna <- a$assays[["RNA"]]
ra <- attributes(rna)
raw <- ra$layers[["counts"]]
features <- attr(ra$features, "dimnames")[[1]]
cells <- attr(ra$cells, "dimnames")[[1]]

same_dim <- identical(as.integer(dim(official)), as.integer(attr(raw, "Dim")))
same_features <- identical(rownames(official), features)
same_cells <- identical(colnames(official), cells)

# Compare canonical CSC representations exactly, not just totals.
off <- as(official, "dgCMatrix")
same_i <- identical(as.integer(off@i), as.integer(attr(raw, "i")))
same_p <- identical(as.integer(off@p), as.integer(attr(raw, "p")))
same_x <- identical(as.numeric(off@x), as.numeric(attr(raw, "x")))
same_colsum <- identical(as.numeric(colSums(off)), as.numeric(colSums(raw)))
same_rowsum <- identical(as.numeric(rowSums(off)), as.numeric(rowSums(raw)))

pass <- all(same_dim, same_features, same_cells, same_i, same_p, same_x,
            same_colsum, same_rowsum)
row <- data.frame(
  source_path = path,
  seurat_object_version = as.character(packageVersion("SeuratObject")),
  n_features = nrow(off),
  n_cells = ncol(off),
  nnz = length(off@x),
  same_dim = same_dim,
  same_features = same_features,
  same_cells = same_cells,
  same_i = same_i,
  same_p = same_p,
  same_x = same_x,
  same_colsum = same_colsum,
  same_rowsum = same_rowsum,
  exact_count_layer_parity = pass,
  stringsAsFactors = FALSE
)
dir.create(dirname(out), recursive = TRUE, showWarnings = FALSE)
tmp <- paste0(out, ".tmp")
write.csv(row, tmp, row.names = FALSE)
if (!file.rename(tmp, out)) stop("atomic promotion failed")
if (!pass) stop("attribute-only count reader differs from SeuratObject LayerData")
cat("PASS_GSE301119_SEURAT5_ATTRIBUTE_COUNT_PARITY\n")
