#!/usr/bin/env Rscript
# GSE301119 donor-aware transcriptome ETL v2 -- hardened per audit finding P0-4.
#
# v1 defects, all fixed here:
#   * validated only matrix DIMENSIONS, never rownames==features or
#     colnames==meta$guide_donor, so a column permutation would pass silently;
#   * did not check unique feature IDs, unique guide x donor keys, expected
#     donor labels, donor/control membership, or non-empty libraries;
#   * did not verify the input RDS SHA-256 at all;
#   * created and wrote its output directory BEFORE validation, and overwrote
#     prior matrices and receipts;
#   * sha256_file() returned NA when the digest package was absent, silently
#     producing a receipt with no digests;
#   * reported a cross-donor estimate even when only one donor qualified;
#   * named a guide-COUNT flag `guide_variance_estimable` although no variance
#     was ever computed;
#   * persisted only the cross-donor mean matrix plus donor-wise OWN-GENE
#     engagement, which makes independent reproduction of per-donor effects
#     impossible.
#
# v2 validates every identity and numeric constraint first, writes into a fresh
# temporary directory, and publishes atomically only after all checks pass.

args <- commandArgs(trailingOnly = TRUE)
get_arg <- function(flag, default = NULL) {
  i <- match(flag, args)
  if (is.na(i) || i == length(args)) {
    if (is.null(default)) stop(sprintf("missing required argument %s", flag))
    return(default)
  }
  args[i + 1L]
}

in_dir    <- get_arg("--pseudobulk-dir")
out_dir   <- get_arg("--out-dir")
rlib      <- get_arg("--rlib", "D:/jepa_rlib46")
manifest  <- get_arg("--provenance-manifest")
.libPaths(rlib)

# A missing digest package must STOP, not yield NA digests.
for (pkg in c("digest", "jsonlite")) {
  if (!requireNamespace(pkg, quietly = TRUE))
    stop(sprintf("STOP_REQUIRED_DEPENDENCY_MISSING: %s; refusing to emit a receipt without digests", pkg))
}
sha256_file <- function(p) digest::digest(file = p, algo = "sha256")

# ---- declared before inspecting any effect -------------------------------
PSEUDOCOUNT      <- 1.0
MIN_CELLS_UNIT   <- 10L
EXPECTED_DONORS  <- c("D1", "D2")
EXPECTED_ROLES   <- c("Perturbed", "NT")
TOP_K            <- 25L

if (dir.exists(out_dir) && length(list.files(out_dir)) > 0L)
  stop("STOP_GSE301119_V2_OUTPUT_EXISTS__NEW_VERSIONED_DIR_REQUIRED")

# Expected input digests, from the authenticated raw-pseudobulk manifest.
expected_sha <- list()
if (!is.null(manifest) && file.exists(manifest)) {
  m <- jsonlite::fromJSON(manifest, simplifyVector = FALSE)
  for (nm in names(m$heavyweight_outputs_on_local_disk))
    expected_sha[[nm]] <- m$heavyweight_outputs_on_local_disk[[nm]]$sha256
} else {
  stop("STOP_PROVENANCE_MANIFEST_REQUIRED: input digests cannot be unbound")
}

validate <- function(obj, mod, rds_path) {
  fail <- character(0)
  add <- function(x) fail <<- c(fail, x)

  if (!identical(obj$schema, "GSE301119_GUIDE_DONOR_RAW_PSEUDOBULK_V1"))
    add("schema mismatch")
  cnt <- obj$counts; feats <- obj$features; meta <- obj$gd_meta

  # identity, not merely shape
  if (is.null(rownames(cnt)))       add("counts has no rownames")
  else if (!identical(rownames(cnt), feats))
    add("rownames(counts) != features (row identity drift)")
  if (is.null(colnames(cnt)))       add("counts has no colnames")
  else if (!identical(colnames(cnt), as.character(meta$guide_donor)))
    add("colnames(counts) != gd_meta$guide_donor (column permutation)")

  if (anyDuplicated(feats))                    add("duplicate feature IDs")
  if (anyDuplicated(meta$guide_donor))         add("duplicate guide x donor keys")
  if (nrow(cnt) != length(feats))              add("feature count mismatch")
  if (ncol(cnt) != nrow(meta))                 add("group count mismatch")

  don <- sort(unique(as.character(meta$donor)), method = "radix")
  if (!identical(don, EXPECTED_DONORS))
    add(sprintf("donor labels %s != expected %s",
                paste(don, collapse=","), paste(EXPECTED_DONORS, collapse=",")))
  if (any(is.na(meta$donor)) || any(meta$donor == ""))  add("empty donor label")
  roles <- sort(unique(as.character(meta$crispr)))
  if (!all(roles %in% EXPECTED_ROLES))
    add(sprintf("unexpected role(s): %s", paste(setdiff(roles, EXPECTED_ROLES), collapse=",")))

  # every donor must carry NT controls, else contrasts are not donor-matched
  for (d in EXPECTED_DONORS) {
    k <- which(meta$crispr == "NT" & meta$donor == d)
    if (!length(k)) add(sprintf("no NT controls for donor %s", d))
    else if (sum(colSums(cnt[, k, drop = FALSE])) <= 0)
      add(sprintf("zero-depth NT library for donor %s", d))
  }

  # numeric constraints
  if (any(!is.finite(cnt)))       add("non-finite counts (NA/NaN/Inf)")
  if (any(cnt < 0))               add("negative counts")
  if (any(cnt != floor(cnt)))     add("non-integer raw counts")
  ls <- colSums(cnt)
  if (any(ls <= 0))               add(sprintf("%d zero-depth libraries", sum(ls <= 0)))
  if (!is.null(obj$library_size) &&
      !isTRUE(all.equal(unname(ls), unname(obj$library_size))))
    add("library_size disagrees with colSums(counts)")

  # authenticated input digest
  base <- basename(rds_path)
  if (!is.null(expected_sha[[base]])) {
    actual <- sha256_file(rds_path)
    if (!identical(actual, expected_sha[[base]]))
      add(sprintf("input digest mismatch for %s", base))
  } else add(sprintf("no expected digest registered for %s", base))

  if (length(fail))
    stop(sprintf("STOP_GSE301119_V2_VALIDATION_FAILED [%s]:\n  %s",
                 mod, paste(fail, collapse = "\n  ")))
  invisible(TRUE)
}

# Write into a staging directory; publish atomically at the very end.
stage <- paste0(out_dir, ".staging-", Sys.getpid())
if (dir.exists(stage)) unlink(stage, recursive = TRUE)
dir.create(stage, recursive = TRUE)

modalities <- c("CRISPRi", "CRISPRa")
summary_rows <- list(); top_rows <- list(); receipt_mod <- list()

for (mod in modalities) {
  rds <- file.path(in_dir, sprintf("%s_guide_donor_raw_counts.rds", mod))
  message("\n=== ", mod, " === ", rds)
  obj <- readRDS(rds)
  validate(obj, mod, rds)
  message("  validation PASS")

  counts <- obj$counts; feats <- obj$features; meta <- obj$gd_meta
  donors <- EXPECTED_DONORS
  targets <- sort(unique(as.character(meta$Gene_Targeted[meta$crispr == "Perturbed"])), method = "radix")

  nt_logcpm <- list(); nt_cells <- list(); nt_guides <- list()
  for (d in donors) {
    k <- which(meta$crispr == "NT" & meta$donor == d)
    raw <- rowSums(counts[, k, drop = FALSE])
    nt_logcpm[[d]] <- log2(raw / sum(raw) * 1e6 + PSEUDOCOUNT)
    nt_cells[[d]] <- sum(meta$n_cells[k]); nt_guides[[d]] <- length(k)
  }

  # donor-wise matrices, persisted so per-donor effects are reproducible
  donor_mat <- lapply(donors, function(d)
    matrix(NA_real_, nrow = length(feats), ncol = length(targets),
           dimnames = list(feats, targets)))
  names(donor_mat) <- donors
  mean_mat <- matrix(NA_real_, nrow = length(feats), ncol = length(targets),
                     dimnames = list(feats, targets))

  for (ti in seq_along(targets)) {
    tg <- targets[ti]; per_donor <- list(); gpd <- integer(0); cpd <- integer(0)
    for (d in donors) {
      k <- which(meta$crispr == "Perturbed" &
                 meta$Gene_Targeted == tg & meta$donor == d)
      cells <- if (length(k)) sum(meta$n_cells[k]) else 0L
      gpd <- c(gpd, length(k)); cpd <- c(cpd, cells)
      if (!length(k) || cells < MIN_CELLS_UNIT) next
      raw <- rowSums(counts[, k, drop = FALSE])
      e <- log2(raw / sum(raw) * 1e6 + PSEUDOCOUNT) - nt_logcpm[[d]]
      per_donor[[d]] <- e
      donor_mat[[d]][, ti] <- e
    }
    names(gpd) <- donors; names(cpd) <- donors
    n_don <- length(per_donor)
    if (n_don == 2L) mean_mat[, ti] <- (per_donor[[donors[1]]] + per_donor[[donors[2]]]) / 2

    r <- match(tg, feats)
    eng_d <- vapply(donors, function(d)
      if (!is.null(per_donor[[d]]) && !is.na(r)) per_donor[[d]][r] else NA_real_,
      numeric(1))
    # a single qualifying donor is DONOR-SPECIFIC, never a cross-donor estimate
    eng_scope <- if (n_don == 2L) "CROSS_DONOR_MEAN"
                 else if (n_don == 1L) paste0("DONOR_SPECIFIC_", names(per_donor)[1])
                 else "NOT_ESTIMABLE"
    eng <- if (n_don == 2L) mean(eng_d, na.rm = TRUE)
           else if (n_don == 1L) eng_d[[which(!is.na(eng_d))[1]]] else NA_real_

    own <- if (is.na(r)) "STRUCTURALLY_UNMEASURED" else {
      tot <- sum(vapply(donors, function(d) {
        k <- which(meta$crispr == "Perturbed" &
                   meta$Gene_Targeted == tg & meta$donor == d)
        if (length(k)) sum(counts[r, k]) else 0 }, numeric(1)))
      if (tot > 0) "ASSAYED_DETECTED" else "ASSAYED_UNDETECTED" }

    summary_rows[[length(summary_rows) + 1L]] <- data.frame(
      modality = mod, target_gene = tg, donors_with_unit = n_don,
      guides_D1 = gpd[[1]], guides_D2 = gpd[[2]],
      cells_D1 = cpd[[1]], cells_D2 = cpd[[2]],
      # renamed: this is a guide COUNT flag, no variance is computed
      guide_count_support_ge2_both_donors = all(gpd >= 2L),
      guide_level_variance_computed = FALSE,
      engagement_scope = eng_scope,
      own_gene_status = own,
      engagement_log2fc = eng,
      engagement_D1 = eng_d[[1]], engagement_D2 = eng_d[[2]],
      stringsAsFactors = FALSE)

    if (n_don == 2L) {
      ord <- order(mean_mat[, ti]); pick <- c(head(ord, TOP_K), tail(ord, TOP_K))
      top_rows[[length(top_rows) + 1L]] <- data.frame(
        modality = mod, target_gene = tg, gene_symbol = feats[pick],
        log2fc_vs_donor_matched_NT = round(mean_mat[pick, ti], 6),
        stringsAsFactors = FALSE)
    }
  }

  pk <- which(meta$crispr == "Perturbed")
  detected <- rowSums(counts[, pk, drop = FALSE]) > 0
  mp <- file.path(stage, sprintf("%s_donor_aware_effects_v2.rds", mod))
  saveRDS(list(schema = "GSE301119_DONOR_AWARE_EFFECTS_V2", modality = mod,
               features = feats, targets = targets, donors = donors,
               log2fc_by_donor = donor_mat,     # <- required for independent reproduction
               log2fc_cross_donor_mean = mean_mat,
               nt_logcpm_by_donor = nt_logcpm,
               gene_detected_in_perturbed = detected), mp)

  receipt_mod[[mod]] <- list(
    source_rds = rds, source_rds_sha256 = sha256_file(rds),
    guide_donor_groups = ncol(counts), genes_assayed = nrow(counts),
    genes_detected_in_perturbed = sum(detected),
    genes_assayed_undetected = sum(!detected),
    targets = length(targets), total_cells = sum(meta$n_cells),
    nt_guides_by_donor = unlist(nt_guides[donors]),
    nt_cells_by_donor = unlist(nt_cells[donors]),
    effects_rds = basename(mp), effects_rds_bytes = file.info(mp)$size,
    effects_rds_sha256 = sha256_file(mp))
  message(sprintf("  wrote %s", basename(mp)))
}

sm <- do.call(rbind, summary_rows); tp <- do.call(rbind, top_rows)
write.csv(sm, file.path(stage, "gse301119_donor_aware_target_summary_v2.csv"), row.names = FALSE)
write.csv(tp, file.path(stage, "gse301119_donor_aware_top_effects_v2.csv"), row.names = FALSE)

receipt <- list(
  schema = "GSE301119_DONOR_AWARE_TRANSCRIPTOME_ETL_V2",
  supersedes = "build_gse301119_donor_aware_transcriptome_v1.R",
  scope = "DEVELOPMENT_ETL_TWO_DONORS_NOT_POPULATION_GENERALIZABLE",
  biological_unit = "donor", n_biological_donors = 2L,
  population_standard_error_produced = FALSE,
  guide_level_variance_computed = FALSE,
  guide_count_flag_is_not_variance = paste(
    "guide_count_support_ge2_both_donors counts guides; it does NOT measure",
    "guide-level variance, which is not computed anywhere in this producer"),
  crispri_crispra_pooled = FALSE,
  validation_performed_before_any_output = TRUE,
  atomic_publish = TRUE,
  declared_before_inspection = list(
    pseudocount = PSEUDOCOUNT, min_cells_per_unit = MIN_CELLS_UNIT,
    expected_donors = EXPECTED_DONORS),
  donor_wise_matrices_persisted = TRUE,
  modalities = receipt_mod,
  r_version = R.version.string,
  seurat_object_version = as.character(packageVersion("SeuratObject")),
  jepa_prediction_used = FALSE, training_authorized = FALSE,
  therapeutic_ranking = FALSE)
writeLines(jsonlite::toJSON(receipt, auto_unbox = TRUE, pretty = TRUE, na = "null"),
           file.path(stage, "gse301119_donor_aware_receipt_v2.json"))

# atomic publish
if (dir.exists(out_dir)) unlink(out_dir, recursive = TRUE)
ok <- file.rename(stage, out_dir)
if (!ok) stop("STOP_ATOMIC_PUBLISH_FAILED")

message("\n=== SUMMARY ===")
for (mod in modalities) {
  s <- sm[sm$modality == mod, ]
  message(sprintf("  %-8s targets %d | cross-donor %d | donor-specific %d | not estimable %d",
                  mod, nrow(s), sum(s$engagement_scope == "CROSS_DONOR_MEAN"),
                  sum(grepl("^DONOR_SPECIFIC", s$engagement_scope)),
                  sum(s$engagement_scope == "NOT_ESTIMABLE")))
  e <- s$engagement_log2fc[is.finite(s$engagement_log2fc)]
  message(sprintf("           engagement %d | median %.4f | guide-count support>=2 both donors: %d",
                  length(e), median(e), sum(s$guide_count_support_ge2_both_donors)))
}
message("\npublished ", out_dir)
