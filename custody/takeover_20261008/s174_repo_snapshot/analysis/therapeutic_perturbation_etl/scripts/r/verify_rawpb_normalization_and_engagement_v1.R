#!/usr/bin/env Rscript
# Independent reproduction of normalization and target engagement from the saved
# RAW integer pseudobulk, and comparison against the previously committed tables.
#
# Tolerance is declared BEFORE looking at the result, as the project requires.
# Both sides are log2(CPM+1) in IEEE double from the same integer counts, so the
# only admissible difference is floating-point reassociation. 1e-9 is generous for
# that and far tighter than any biologically meaningful difference; anything larger
# means the two paths are not computing the same quantity.
TOL_LOGCPM <- 1e-9
TOL_LOG2FC <- 1e-9

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 4) stop("usage: <rawpb_dir> <prior_engagement_csv> <out_csv> <tag>")
dir <- args[[1]]; prior_path <- args[[2]]; out <- args[[3]]; tag <- args[[4]]

raw <- readRDS(file.path(dir, paste0(tag, "_guide_donor_raw_counts.rds")))
nrm <- readRDS(file.path(dir, paste0(tag, "_guide_donor_logcpm.rds")))

stopifnot(identical(raw$schema, "GSE301119_GUIDE_DONOR_RAW_PSEUDOBULK_V1"))
stopifnot(identical(nrm$schema, "GSE301119_GUIDE_DONOR_LOGCPM_V1"))
stopifnot(identical(raw$features, nrm$features))
stopifnot(identical(raw$gd_meta$guide_donor, nrm$gd_meta$guide_donor))

PB <- raw$counts
stopifnot(is.matrix(PB), all(PB >= 0), all(PB == floor(PB)))

# ---- independently recompute log2(CPM+1) from the raw integers ---------------
lib <- pmax(colSums(PB), 1)
recomputed <- log2(sweep(PB, 2, lib, "/") * 1e6 + 1)
delta <- abs(recomputed - nrm$logcpm)
max_delta <- max(delta)
n_over <- sum(delta > TOL_LOGCPM)
norm_ok <- (max_delta <= TOL_LOGCPM)

# library sizes stored alongside the raw counts must agree with the counts
lib_ok <- identical(as.numeric(raw$library_size), as.numeric(colSums(PB)))

cat(tag, "normalization: max|delta| =", format(max_delta, scientific = TRUE),
    " cells over tol:", n_over, " ok:", norm_ok, "\n")

# ---- independently recompute target engagement -------------------------------
gm <- raw$gd_meta
features <- raw$features
lg <- recomputed                     # use OUR recomputation, not the stored one
donors <- sort(unique(gm$donor))
targets <- sort(unique(gm$Gene_Targeted[gm$crispr == "Perturbed"]))

rows <- list(); k <- 0
for (d in donors) {
  nt <- which(gm$donor == d & gm$crispr == "NT")
  if (!length(nt)) next
  nt_mean <- rowMeans(lg[, nt, drop = FALSE])
  for (tg in targets) {
    idx <- which(gm$donor == d & gm$crispr == "Perturbed" & gm$Gene_Targeted == tg)
    if (!length(idx)) next
    gi <- match(tg, features)
    k <- k + 1
    rows[[k]] <- data.frame(
      donor = d, target_gene = tg,
      measured = !is.na(gi),
      log2fc = if (is.na(gi)) NA_real_ else mean(lg[gi, idx] - nt_mean[gi]),
      n_guides = length(idx),
      stringsAsFactors = FALSE)
  }
}
mine <- do.call(rbind, rows)

prior <- read.csv(prior_path, stringsAsFactors = FALSE)
key_m <- paste(mine$donor, mine$target_gene, sep = "||")
key_p <- paste(prior$donor, prior$target_gene, sep = "||")
common <- intersect(key_m, key_p)

im <- match(common, key_m); ip <- match(common, key_p)
a <- mine$log2fc[im]
b <- suppressWarnings(as.numeric(prior$target_log2fc_mean[ip]))
both <- !is.na(a) & !is.na(b)
d_fc <- abs(a[both] - b[both])
max_fc <- if (any(both)) max(d_fc) else NA_real_
n_fc_over <- if (any(both)) sum(d_fc > TOL_LOG2FC) else 0L
eng_ok <- (!is.na(max_fc) && max_fc <= TOL_LOG2FC)

# measured-flag agreement, and identical row coverage
cover_ok <- (length(common) == nrow(mine)) && (length(common) == nrow(prior))
meas_ok <- identical(mine$measured[im], prior$target_gene_measured[ip] == "True" |
                       prior$target_gene_measured[ip] == TRUE)
guides_ok <- identical(as.integer(mine$n_guides[im]), as.integer(prior$n_guides[ip]))

cat(tag, "engagement: rows compared", length(common), " max|delta log2FC| =",
    format(max_fc, scientific = TRUE), " over tol:", n_fc_over,
    " coverage_ok:", cover_ok, " guides_ok:", guides_ok, "\n")

pass <- norm_ok && lib_ok && eng_ok && cover_ok && guides_ok
row <- data.frame(
  tag = tag,
  declared_tol_logcpm = TOL_LOGCPM, declared_tol_log2fc = TOL_LOG2FC,
  n_features = nrow(PB), n_guide_donor_groups = ncol(PB),
  raw_counts_integral = TRUE,
  library_size_matches_counts = lib_ok,
  max_abs_delta_logcpm = max_delta, n_values_over_tol_logcpm = n_over,
  normalization_reproduced = norm_ok,
  engagement_rows_compared = length(common),
  max_abs_delta_log2fc = max_fc, n_over_tol_log2fc = n_fc_over,
  engagement_reproduced = eng_ok,
  row_coverage_identical = cover_ok,
  measured_flag_identical = meas_ok,
  guide_counts_identical = guides_ok,
  verification_pass = pass,
  stringsAsFactors = FALSE)

dir.create(dirname(out), recursive = TRUE, showWarnings = FALSE)
tmp <- paste0(out, ".tmp"); write.csv(row, tmp, row.names = FALSE)
if (!file.rename(tmp, out)) stop("atomic promotion failed")
if (!pass) stop(paste(tag, "independent reproduction FAILED"))
cat("PASS_RAWPB_NORMALIZATION_AND_ENGAGEMENT_REPRODUCED\n")
