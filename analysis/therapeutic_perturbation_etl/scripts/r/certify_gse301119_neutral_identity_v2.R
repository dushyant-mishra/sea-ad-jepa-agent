#!/usr/bin/env Rscript
# Separate fail-closed attestation of an EXISTING GSE301119 neutral export.
# Reconstruct all four exported files from the authenticated original raw RDS
# and require exact byte agreement. No perturbation effect is recomputed;
# neither scientific independence nor biological replication is claimed.
#
# Emit ONLY a versioned small JSON receipt into a NEW output directory.
# This is a GPU-laptop physical source check, not an assertion it ran in CI.
args <- commandArgs(trailingOnly = TRUE)
get_arg <- function(flag, default = NULL) {
  pos <- match(flag, args)
  if (is.na(pos) || pos == length(args)) {
    if (is.null(default)) stop(sprintf("STOP_MISSING_%s", flag))
    return(default)
  }
  args[pos + 1L]
}
raw_dir <- get_arg("--pseudobulk-dir")
neutral <- get_arg("--neutral-dir")
out_dir <- get_arg("--out-dir")
rlib <- get_arg("--rlib", "D:/jepa_rlib46")
.libPaths(c(rlib, .libPaths()))
for (pkg in c("digest", "jsonlite")) {
  if (!requireNamespace(pkg, quietly = TRUE)) stop(paste0("STOP_MISSING_", pkg))
}
sha <- function(p) digest::digest(file = p, algo = "sha256")
expected <- c(
  CRISPRi = "e796504f41ddd65f3a5b72699d12431ce664974e0860ecb255858bd084283549",
  CRISPRa = "9fe028f508ce33a8c968ab05c363c345135b0b6227db4476838c70fb9d874d90"
)
v1_path <- file.path(neutral, "NEUTRAL_EXPORT_RECEIPT_V1.json")
if (!file.exists(v1_path)) stop("STOP_MISSING_V1_NEUTRAL_EXPORT_RECEIPT")
v1 <- jsonlite::fromJSON(v1_path, simplifyVector = FALSE)
if (!identical(v1$schema, "GSE301119_NEUTRAL_ARRAY_EXPORT_V1"))
  stop("STOP_WRONG_V1_NEUTRAL_EXPORT_SCHEMA")
if (file.exists(out_dir) || dir.exists(out_dir))
  stop("STOP_CERTIFICATION_OUTPUT_EXISTS")
stage <- paste0(out_dir, ".staging-", Sys.getpid())
if (dir.exists(stage)) stop("STOP_CERTIFICATION_STAGING_EXISTS")

certify <- function() {
  dir.create(stage, recursive = TRUE, showWarnings = FALSE)
  on.exit(unlink(stage, recursive = TRUE), add = TRUE)
  record <- list(
    schema = "GSE301119_NEUTRAL_IDENTITY_CERTIFICATION_V2",
    status = "PHYSICAL_SOURCE_IDENTITY_ATTESTATION_ONLY_NOT_SCIENTIFIC_REPRODUCTION",
    v1_export_receipt_sha256 = sha(v1_path),
    file_validation = list(), protected_outcome_opened = FALSE,
    training_authorized = FALSE, therapeutic_ranking = FALSE
  )
  for (mod in c("CRISPRi", "CRISPRa")) {
    src <- file.path(raw_dir, paste0(mod, "_guide_donor_raw_counts.rds"))
    if (!file.exists(src) || !identical(sha(src), unname(expected[[mod]])))
      stop(paste0("STOP_AUTHENTICATED_SOURCE_RDS_MISMATCH_", mod))
    e <- v1$exports[[mod]]
    if (is.null(e) || !identical(e$source_rds_sha256_after_export, unname(expected[[mod]])))
      stop(paste0("STOP_V1_RECEIPT_SOURCE_MISMATCH_", mod))
    obj <- readRDS(src)
    if (!identical(obj$schema, "GSE301119_GUIDE_DONOR_RAW_PSEUDOBULK_V1"))
      stop(paste0("STOP_ORIGINAL_RDS_SCHEMA_MISMATCH_", mod))
    cnt <- obj$counts
    meta <- obj$gd_meta
    if (!identical(rownames(cnt), obj$features) ||
        !identical(colnames(cnt), as.character(meta$guide_donor)) ||
        anyDuplicated(obj$features) > 0 ||
        anyDuplicated(meta$guide_donor) > 0 ||
        !identical(sort(unique(as.character(meta$donor))), c("D1", "D2")) ||
        !all(c("Perturbed", "NT") %in% meta$crispr) ||
        any(is.na(meta$n_cells)) || any(meta$n_cells < 0) ||
        any(!is.finite(cnt)) || any(cnt < 0) || any(cnt != floor(cnt)))
      stop(paste0("STOP_ORIGINAL_RDS_IDENTITY_INVALID_", mod))
    if (!identical(as.integer(dim(cnt)), as.integer(unlist(e$dim))))
      stop(paste0("STOP_SOURCE_DIM_MISMATCH_", mod))
    storage.mode(cnt) <- "integer"
    paths <- list(
      counts_bin = file.path(neutral, paste0(mod, "_counts_int32.bin")),
      shape = file.path(neutral, paste0(mod, "_shape.txt")),
      features = file.path(neutral, paste0(mod, "_features.txt")),
      gd_meta = file.path(neutral, paste0(mod, "_gd_meta.csv"))
    )
    for (nm in names(paths))
      if (!file.exists(paths[[nm]]))
        stop(paste0("STOP_MISSING_NEUTRAL_", mod, "_", nm))
    tmp <- lapply(names(paths), function(nm) tempfile(pattern = paste0(mod, "-", nm, "-"), tmpdir = stage))
    names(tmp) <- names(paths)
    on.exit(unlink(unlist(tmp)), add = TRUE)
    con <- file(tmp$counts_bin, "wb")
    writeBin(as.vector(cnt), con, size = 4L, endian = "little")
    close(con)
    writeLines(as.character(dim(cnt)), tmp$shape)
    writeLines(obj$features, tmp$features)
    write.csv(meta, tmp$gd_meta, row.names = FALSE)
    verified <- list()
    for (nm in names(paths)) {
      actual <- sha(paths[[nm]])
      if (!identical(actual, sha(tmp[[nm]])))
        stop(paste0("STOP_RDS_VS_NEUTRAL_IDENTITY_MISMATCH_", mod, "_", nm))
      verified[[nm]] <- actual
    }
    if (!identical(verified$counts_bin, e$counts_bin_sha256))
      stop(paste0("STOP_COUNT_BIN_V1_RECEIPT_MISMATCH_", mod))
    # Rehash original RDS after whole-file read and identity reconstruction.
    if (!identical(sha(src), unname(expected[[mod]])))
      stop(paste0("STOP_SOURCE_RDS_CHANGED_DURING_CERTIFICATION_", mod))
    record$file_validation[[mod]] <- list(
      source_rds_sha256 = unname(expected[[mod]]),
      dim = as.integer(dim(cnt)),
      exported_file_sha256 = verified,
      equality = "ALL_FOUR_NEUTRAL_EXPORT_FILES_RECONSTRUCTED_BYTE_IDENTICAL_FROM_ORIGINAL_RDS"
    )
    unlink(unlist(tmp))
  }
  record_path <- file.path(stage, "NEUTRAL_EXPORT_IDENTITY_CERTIFICATION_V2.json")
  writeLines(jsonlite::toJSON(record, auto_unbox = TRUE, pretty = TRUE), record_path)
  if (!file.rename(stage, out_dir)) stop("STOP_ATOMIC_CERTIFICATION_PUBLISH")
  cat("PASS_AUTHENTICATED_NEUTRAL_IDENTITY_METADATA_ONLY ", out_dir, "\n")
}
certify()
