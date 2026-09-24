# GSE301119 intervention-effect extraction, attribute-only (no SeuratObject).
#
# Why attribute-only: the objects are Seurat 5.4.0 / Assay5. The only Seurat on
# this machine is 4.1.1 / SeuratObject 4.1.0, which does NOT define Assay5 --
# it loads the object but dim() returns empty rather than erroring, so v4
# accessors would silently produce wrong results. Reading the serialized payload
# directly is the sound route here, not a workaround.
#
# Produces guide-level pseudobulk BEFORE any target-level aggregation, so guide
# and replicate structure is preserved. Effects are measured against the study's
# own non-targeting controls, within donor. Nothing here is simulated and no
# JEPA prediction is involved.

args <- commandArgs(trailingOnly = TRUE)
path <- args[[1]]; outdir <- args[[2]]; tag <- args[[3]]
dir.create(outdir, recursive = TRUE, showWarnings = FALSE)

x  <- readRDS(path)
a  <- attributes(x)
md <- a$meta.data
rna <- a$assays[["RNA"]]
ra  <- attributes(rna)

features <- attr(ra$features, "dimnames")[[1]]
cells    <- attr(ra$cells, "dimnames")[[1]]
L <- ra$layers[["counts"]]

cat(tag, "layer class:", paste(attr(L, "class"), collapse = ","), "\n")
Dim <- attr(L, "Dim")
stopifnot(Dim[1] == length(features), Dim[2] == length(cells))
stopifnot(identical(rownames(md), cells))
stopifnot(!anyDuplicated(features), !anyDuplicated(cells))

i <- attr(L, "i"); p <- attr(L, "p"); xv <- attr(L, "x")
cat(tag, "nnz:", length(xv), " genes:", Dim[1], " cells:", Dim[2], "\n")
stopifnot(all(xv == floor(xv)), all(xv >= 0))   # raw integer counts only

ncell <- Dim[2]; ngene <- Dim[1]

# Column (cell) group sums over a CSC matrix, without densifying.
group_pseudobulk <- function(group_of_cell, levels_) {
  g <- match(group_of_cell, levels_)
  out <- matrix(0, nrow = ngene, ncol = length(levels_))
  for (c in seq_len(ncell)) {
    lo <- p[c] + 1L; hi <- p[c + 1L]
    if (hi >= lo) {
      rows <- i[lo:hi] + 1L
      out[rows, g[c]] <- out[rows, g[c]] + xv[lo:hi]
    }
  }
  rownames(out) <- features; colnames(out) <- levels_
  out
}

md$guide_identity <- as.character(md$guide_identity)
md$Gene_Targeted  <- as.character(md$Gene_Targeted)
md$donor          <- as.character(md$donor)
md$crispr         <- as.character(md$crispr)
stopifnot(all(nzchar(md$guide_identity)), all(nzchar(md$Gene_Targeted)),
          all(nzchar(md$donor)), all(nzchar(md$crispr)))
stopifnot(setequal(unique(md$crispr), c("NT", "Perturbed")))
stopifnot(setequal(unique(md$donor), c("D1", "D2")))

# A guide identity must have one immutable target and CRISPR role across cells.
# The historical reader summarized these fields, but downstream ETL must fail
# rather than silently taking the first row if a guide's annotation drifts.
guide_target_n <- tapply(md$Gene_Targeted, md$guide_identity,
                         function(z) length(unique(z)))
guide_role_n <- tapply(md$crispr, md$guide_identity,
                       function(z) length(unique(z)))
stopifnot(all(guide_target_n == 1L), all(guide_role_n == 1L))

# --- guide x donor pseudobulk: the pre-aggregation unit ---------------------
md$gd <- paste(md$guide_identity, md$donor, sep = "||")
gd_levels <- sort(unique(md$gd))
cat(tag, "guide x donor groups:", length(gd_levels), "\n")
PB <- group_pseudobulk(md$gd, gd_levels)

key <- do.call(rbind, strsplit(gd_levels, "||", fixed = TRUE))
gd_meta <- data.frame(
  guide_donor = gd_levels,
  guide_identity = key[, 1],
  donor = key[, 2],
  stringsAsFactors = FALSE
)
m <- match(gd_meta$guide_identity, md$guide_identity)
gd_meta$Gene_Targeted <- md$Gene_Targeted[m]
gd_meta$crispr <- md$crispr[m]
gd_meta$n_cells <- as.integer(table(factor(md$gd, levels = gd_levels)))
gd_meta$total_counts <- colSums(PB)

write.csv(gd_meta, file.path(outdir, paste0(tag, "_guide_donor_meta.csv")), row.names = FALSE)

# CPM on the guide x donor pseudobulk; log2(cpm+1) for effect estimation.
cpm <- sweep(PB, 2, pmax(colSums(PB), 1), "/") * 1e6
lg  <- log2(cpm + 1)

# Keep the guide-level matrix but only for the targeted genes plus a bounded
# set, to keep the committed artifact small; the full matrix stays on disk.
saveRDS(list(
          schema = "GSE301119_GUIDE_DONOR_RAW_PSEUDOBULK_V1",
          features = features,
          gd_meta = gd_meta,
          counts = PB,
          library_size = colSums(PB)),
        file.path(outdir, paste0(tag, "_guide_donor_raw_counts.rds")))
saveRDS(list(
          schema = "GSE301119_GUIDE_DONOR_LOGCPM_V1",
          normalization = "log2(CPM+1)_within_guide_donor_pseudobulk",
          features = features,
          gd_meta = gd_meta,
          logcpm = lg),
        file.path(outdir, paste0(tag, "_guide_donor_logcpm.rds")))

# --- target-level effects vs non-targeting control, within donor ------------
donors <- sort(unique(gd_meta$donor))
targets <- sort(unique(gd_meta$Gene_Targeted[gd_meta$crispr == "Perturbed"]))
cat(tag, "donors:", paste(donors, collapse = ","), " perturbed targets:", length(targets), "\n")

rows <- list(); k <- 0
for (d in donors) {
  nt_idx <- which(gd_meta$donor == d & gd_meta$crispr == "NT")
  if (!length(nt_idx)) next
  nt_mean <- rowMeans(lg[, nt_idx, drop = FALSE])
  for (tg in targets) {
    idx <- which(gd_meta$donor == d & gd_meta$crispr == "Perturbed" &
                   gd_meta$Gene_Targeted == tg)
    if (!length(idx)) next
    # target engagement: the targeted gene's own response, if it is measured
    gi <- match(tg, features)
    per_guide <- if (is.na(gi)) rep(NA_real_, length(idx)) else lg[gi, idx] - nt_mean[gi]
    k <- k + 1
    rows[[k]] <- data.frame(
      study = "GSE301119", assay_object = tag, donor = d, target_gene = tg,
      target_gene_measured = !is.na(gi),
      n_guides = length(idx),
      n_cells = sum(gd_meta$n_cells[idx]),
      n_nt_guides = length(nt_idx),
      n_nt_cells = sum(gd_meta$n_cells[nt_idx]),
      target_log2fc_mean = if (is.na(gi)) NA_real_ else mean(per_guide),
      target_log2fc_sd = if (is.na(gi) || length(idx) < 2) NA_real_ else sd(per_guide),
      target_log2fc_se = if (is.na(gi) || length(idx) < 2) NA_real_
                         else sd(per_guide) / sqrt(length(idx)),
      stringsAsFactors = FALSE
    )
  }
}
eff <- do.call(rbind, rows)
write.csv(eff, file.path(outdir, paste0(tag, "_target_engagement.csv")), row.names = FALSE)
cat(tag, "target-engagement rows:", nrow(eff), "\n")
cat("EFFECTS_OK\n")
