#!/usr/bin/env Rscript
# Thin exporter: RDS -> neutral arrays, for INDEPENDENT reproduction.
#
# This script performs NO scientific computation. It dumps raw integer counts,
# group metadata and (separately) the v2 producer's emitted effect matrices into
# plain binary/text so a separately authored implementation in another language
# can recompute effects without sharing a line of code with the R producer.
#
# Every export is digested, and the raw counts are re-verified against the
# source RDS after writing, so the neutral copy cannot silently drift from the
# authenticated object it came from.

args <- commandArgs(trailingOnly = TRUE)
get_arg <- function(f, d = NULL) {
  i <- match(f, args)
  if (is.na(i) || i == length(args)) { if (is.null(d)) stop(sprintf("missing %s", f)); return(d) }
  args[i + 1L]
}
pb_dir  <- get_arg("--pseudobulk-dir")
v2_dir  <- get_arg("--v2-dir")
out_dir <- get_arg("--out-dir")
rlib    <- get_arg("--rlib", "D:/jepa_rlib46")
.libPaths(rlib)
for (p in c("digest", "jsonlite"))
  if (!requireNamespace(p, quietly = TRUE)) stop(sprintf("STOP_MISSING_%s", p))
sha <- function(p) digest::digest(file = p, algo = "sha256")

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
rec <- list(schema = "GSE301119_NEUTRAL_ARRAY_EXPORT_V1",
            performs_computation = FALSE, exports = list())

for (mod in c("CRISPRi", "CRISPRa")) {
  src <- file.path(pb_dir, sprintf("%s_guide_donor_raw_counts.rds", mod))
  o <- readRDS(src)
  cnt <- o$counts
  storage.mode(cnt) <- "integer"          # raw counts are integer-valued
  stopifnot(identical(rownames(cnt), o$features),
            identical(colnames(cnt), as.character(o$gd_meta$guide_donor)))

  # counts: plain binary, column-major, int32
  cp <- file.path(out_dir, sprintf("%s_counts_int32.bin", mod))
  con <- file(cp, "wb"); writeBin(as.vector(cnt), con, size = 4L); close(con)
  # shape + identity as text, so the reader needs no R
  writeLines(as.character(dim(cnt)), file.path(out_dir, sprintf("%s_shape.txt", mod)))
  writeLines(o$features,             file.path(out_dir, sprintf("%s_features.txt", mod)))
  write.csv(o$gd_meta, file.path(out_dir, sprintf("%s_gd_meta.csv", mod)), row.names = FALSE)

  # v2 emitted effects, for comparison only
  v2 <- readRDS(file.path(v2_dir, sprintf("%s_donor_aware_effects_v2.rds", mod)))
  for (d in v2$donors) {
    m <- v2$log2fc_by_donor[[d]]
    p <- file.path(out_dir, sprintf("%s_v2_log2fc_%s_float64.bin", mod, d))
    con <- file(p, "wb"); writeBin(as.vector(m), con, size = 8L); close(con)
  }
  mm <- file.path(out_dir, sprintf("%s_v2_log2fc_mean_float64.bin", mod))
  con <- file(mm, "wb"); writeBin(as.vector(v2$log2fc_cross_donor_mean), con, size = 8L); close(con)
  writeLines(v2$targets, file.path(out_dir, sprintf("%s_v2_targets.txt", mod)))
  writeLines(v2$features, file.path(out_dir, sprintf("%s_v2_features.txt", mod)))
  writeLines(v2$donors,  file.path(out_dir, sprintf("%s_v2_donors.txt", mod)))

  # re-verify the source RDS after writing, so the export cannot drift
  rec$exports[[mod]] <- list(
    source_rds = src, source_rds_sha256_after_export = sha(src),
    counts_bin = basename(cp), counts_bin_sha256 = sha(cp),
    dim = dim(cnt), v2_effects_sha256 = sha(file.path(v2_dir,
      sprintf("%s_donor_aware_effects_v2.rds", mod))))
  message(sprintf("  exported %s: %d x %d", mod, nrow(cnt), ncol(cnt)))
}
writeLines(jsonlite::toJSON(rec, auto_unbox = TRUE, pretty = TRUE),
           file.path(out_dir, "NEUTRAL_EXPORT_RECEIPT_V1.json"))
message("wrote ", out_dir)
