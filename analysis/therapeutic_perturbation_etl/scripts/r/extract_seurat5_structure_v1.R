# Attribute-only extraction from a Seurat v5 .rds with NO SeuratObject present.
# Every access uses attr()/base indexing so no S4 method dispatch is triggered,
# which is what pulled in the missing SeuratObject in the first probe.
args <- commandArgs(trailingOnly=TRUE)
path <- args[[1]]; outdir <- args[[2]]; tag <- args[[3]]
dir.create(outdir, recursive=TRUE, showWarnings=FALSE)
x <- readRDS(path)
a <- attributes(x)

md <- a$meta.data
write.csv(cbind(cell_barcode=rownames(md), md), file.path(outdir, paste0(tag, "_meta.csv")),
          row.names=FALSE, quote=TRUE)
cat(tag, "meta rows:", nrow(md), " cols:", ncol(md), "\n")

rna <- a$assays[["RNA"]]
ra  <- attributes(rna)

feat <- ra$features
fdn  <- attr(feat, "dimnames")
features <- if (!is.null(fdn)) fdn[[1]] else NULL
cat(tag, "features:", length(features), "\n")
writeLines(as.character(features), file.path(outdir, paste0(tag, "_features.txt")))

cellsobj <- ra$cells
cdn <- attr(cellsobj, "dimnames")
cellnames <- if (!is.null(cdn)) cdn[[1]] else NULL
cat(tag, "cells:", length(cellnames), "\n")
writeLines(as.character(cellnames), file.path(outdir, paste0(tag, "_cells.txt")))

lay <- ra$layers
cat(tag, "layers:", paste(names(lay), collapse=", "), "\n")
for (nm in names(lay)) {
  L <- lay[[nm]]
  d <- attr(L, "Dim")
  dn <- attr(L, "Dimnames")
  cat(tag, "layer", nm, "Dim:", paste(d, collapse=" x "),
      " has_rownames:", !is.null(dn) && !is.null(dn[[1]]),
      " nnz:", length(attr(L, "x")), "\n")
  if (!is.null(dn) && !is.null(dn[[1]])) {
    writeLines(as.character(dn[[1]]), file.path(outdir, paste0(tag, "_", nm, "_rownames.txt")))
  }
}
cat("EXTRACT_OK\n")
