#!/usr/bin/env Rscript
# Donor-aware transcriptome-wide development ETL for GSE301119 primary macrophages.
#
# Consumes the already-qualified guide x donor raw pseudobulk (PR #81 producer,
# independently reproduced at normalization delta 0.0 and engagement delta ~5e-15
# against a declared 1e-9 tolerance) and produces transcriptome-wide effects that
# respect the actual experimental units.
#
# Design decisions, fixed here rather than discovered from the results:
#
#   * The biological unit is the DONOR. There are two. Cells are not donors and
#     guides are not donors. No population standard error is produced from n=2;
#     each donor's value is reported separately and their spread is labelled
#     descriptive.
#
#   * CRISPRi and CRISPRa are SEPARATE STRATA and are never pooled. They are
#     opposite interventions on the same gene list.
#
#   * Raw integer counts are summed across a target's guides WITHIN a donor
#     before normalisation. Averaging per-guide log ratios instead would weight
#     a 6-cell guide equally with a 200-cell guide.
#
#   * Controls are DONOR-MATCHED. A target in donor D1 is contrasted against
#     non-targeting guides from D1, never from D2, so donor is not confounded
#     with perturbation.
#
#   * Guide-level support is preserved per donor. Where a target has fewer than
#     two guides in a donor, within-donor guide variance is NOT estimable and is
#     recorded as such rather than as zero. PR #91 identifies CRISPRa HEXA as
#     exactly this case.
#
#   * Missingness is explicit. A gene absent from the 36,601-feature space is
#     STRUCTURALLY_UNMEASURED. A gene present with zero counts in the compared
#     groups is ASSAYED_UNDETECTED. These are different facts and are never
#     collapsed to zero effect.
#
# This is development ETL. No predictor is fitted, no therapy is ranked, and two
# donors do not license a population or in-brain generalization claim.

suppressWarnings(suppressMessages({
  args <- commandArgs(trailingOnly = TRUE)
}))

get_arg <- function(flag, default = NULL) {
  i <- match(flag, args)
  if (is.na(i) || i == length(args)) {
    if (is.null(default)) stop(sprintf("missing required argument %s", flag))
    return(default)
  }
  args[i + 1L]
}

in_dir   <- get_arg("--pseudobulk-dir")
out_dir  <- get_arg("--out-dir")
rlib     <- get_arg("--rlib", "D:/jepa_rlib46")
.libPaths(rlib)

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

# ---- declared before inspecting any effect -------------------------------
PSEUDOCOUNT    <- 1.0     # log2(CPM + 1)
MIN_CELLS_UNIT <- 10L     # cells required for a (target, donor) unit
N_DONORS_REQ   <- 2L      # both donors required for a cross-donor mean
TOP_K          <- 25L     # genes reported per direction per target

sha256_file <- function(p) {
  if (!requireNamespace("digest", quietly = TRUE)) return(NA_character_)
  digest::digest(file = p, algo = "sha256")
}

message("R: ", R.version.string)
message("library: ", rlib)

modalities <- c("CRISPRi", "CRISPRa")
summary_rows <- list()
top_rows     <- list()
receipt_mod  <- list()

for (mod in modalities) {
  rds <- file.path(in_dir, sprintf("%s_guide_donor_raw_counts.rds", mod))
  message("\n=== ", mod, " : ", rds)
  obj <- readRDS(rds)
  stopifnot(identical(obj$schema, "GSE301119_GUIDE_DONOR_RAW_PSEUDOBULK_V1"))
  counts <- obj$counts                # genes x guide_donor, raw integers
  feats  <- obj$features
  meta   <- obj$gd_meta
  stopifnot(nrow(counts) == length(feats), ncol(counts) == nrow(meta))
  if (any(counts < 0)) stop("negative counts in pseudobulk")
  if (any(counts != floor(counts))) stop("non-integer raw counts in pseudobulk")

  donors  <- sort(unique(as.character(meta$donor)), method = "radix")
  targets <- sort(unique(as.character(meta$Gene_Targeted[meta$crispr == "Perturbed"])), method = "radix")
  message(sprintf("  %d genes x %d guide-donor groups | donors %s | %d targets",
                  nrow(counts), ncol(counts), paste(donors, collapse=","),
                  length(targets)))

  # donor-matched non-targeting reference, aggregated at raw-count level
  nt_logcpm <- list(); nt_cells <- list(); nt_guides <- list()
  for (d in donors) {
    k <- which(meta$crispr == "NT" & meta$donor == d)
    if (!length(k)) stop(sprintf("no NT controls for donor %s", d))
    raw <- rowSums(counts[, k, drop = FALSE])
    nt_logcpm[[d]] <- log2(raw / sum(raw) * 1e6 + PSEUDOCOUNT)
    nt_cells[[d]]  <- sum(meta$n_cells[k])
    nt_guides[[d]] <- length(k)
  }
  message(sprintf("  NT controls: %s",
                  paste(sprintf("%s=%d guides/%d cells", donors,
                                unlist(nt_guides[donors]),
                                unlist(nt_cells[donors])), collapse="  ")))

  # per-donor log2FC for every target, then the cross-donor mean
  lfc_mat <- matrix(NA_real_, nrow = length(feats), ncol = length(targets),
                    dimnames = list(feats, targets))
  for (ti in seq_along(targets)) {
    tg <- targets[ti]
    per_donor <- list(); gpd <- integer(0); cpd <- integer(0)
    for (d in donors) {
      k <- which(meta$crispr == "Perturbed" &
                 meta$Gene_Targeted == tg & meta$donor == d)
      cells <- if (length(k)) sum(meta$n_cells[k]) else 0L
      gpd <- c(gpd, length(k)); cpd <- c(cpd, cells)
      if (!length(k) || cells < MIN_CELLS_UNIT) next
      raw <- rowSums(counts[, k, drop = FALSE])
      per_donor[[d]] <- log2(raw / sum(raw) * 1e6 + PSEUDOCOUNT) - nt_logcpm[[d]]
    }
    names(gpd) <- donors; names(cpd) <- donors
    n_don <- length(per_donor)
    if (n_don >= 1L) {
      lfc <- Reduce(`+`, per_donor) / n_don
      if (n_don == N_DONORS_REQ) lfc_mat[, ti] <- lfc
    } else {
      lfc <- rep(NA_real_, length(feats))
    }

    # target engagement: the perturbed gene measured on itself
    r <- match(tg, feats)
    eng <- if (is.na(r)) NA_real_ else lfc[r]
    eng_by_donor <- if (is.na(r)) rep(NA_real_, length(donors))
                    else vapply(donors, function(d)
                      if (!is.null(per_donor[[d]])) per_donor[[d]][r] else NA_real_,
                      numeric(1))
    own_row <- if (is.na(r)) "STRUCTURALLY_UNMEASURED" else {
      tot <- sum(vapply(donors, function(d) {
        k <- which(meta$crispr == "Perturbed" &
                   meta$Gene_Targeted == tg & meta$donor == d)
        if (length(k)) sum(counts[r, k]) else 0
      }, numeric(1)))
      if (tot > 0) "ASSAYED_DETECTED" else "ASSAYED_UNDETECTED"
    }

    summary_rows[[length(summary_rows) + 1L]] <- data.frame(
      modality = mod, target_gene = tg,
      donors_with_unit = n_don,
      guides_D1 = gpd[[1]], guides_D2 = gpd[[2]],
      cells_D1  = cpd[[1]], cells_D2  = cpd[[2]],
      guide_variance_estimable = all(gpd >= 2L),
      cross_donor_mean_estimable = (n_don == N_DONORS_REQ),
      own_gene_status = own_row,
      engagement_log2fc = eng,
      engagement_D1 = eng_by_donor[[1]], engagement_D2 = eng_by_donor[[2]],
      engagement_donor_range = if (all(is.finite(eng_by_donor)))
        abs(diff(eng_by_donor)) else NA_real_,
      stringsAsFactors = FALSE)

    if (n_don == N_DONORS_REQ) {
      ord <- order(lfc)
      pick <- c(head(ord, TOP_K), tail(ord, TOP_K))
      top_rows[[length(top_rows) + 1L]] <- data.frame(
        modality = mod, target_gene = tg, gene_symbol = feats[pick],
        log2fc_vs_donor_matched_NT = round(lfc[pick], 5),
        stringsAsFactors = FALSE)
    }
    if (ti %% 40 == 0) message(sprintf("    %d/%d targets", ti, length(targets)))
  }

  # measured-gene mask over the perturbed groups of this modality
  pk <- which(meta$crispr == "Perturbed")
  detected <- rowSums(counts[, pk, drop = FALSE]) > 0
  mat_path <- file.path(out_dir, sprintf("%s_donor_aware_log2fc_matrix.rds", mod))
  saveRDS(list(schema = "GSE301119_DONOR_AWARE_LOG2FC_V1",
               modality = mod, features = feats, targets = targets,
               log2fc = lfc_mat, gene_detected_in_perturbed = detected,
               donors = donors), mat_path)

  receipt_mod[[mod]] <- list(
    guide_donor_groups = ncol(counts),
    genes_assayed = nrow(counts),
    genes_detected_in_perturbed = sum(detected),
    genes_assayed_undetected = sum(!detected),
    donors = donors,
    targets = length(targets),
    nt_guides_by_donor = unlist(nt_guides[donors]),
    nt_cells_by_donor  = unlist(nt_cells[donors]),
    total_cells = sum(meta$n_cells),
    log2fc_matrix_path = mat_path,
    log2fc_matrix_bytes = file.info(mat_path)$size,
    log2fc_matrix_sha256 = sha256_file(mat_path))
  message(sprintf("  wrote %s (%s bytes)", basename(mat_path),
                  format(file.info(mat_path)$size, big.mark = ",")))
}

sm <- do.call(rbind, summary_rows)
tp <- do.call(rbind, top_rows)
s_path <- file.path(out_dir, "gse301119_donor_aware_target_summary_v1.csv")
t_path <- file.path(out_dir, "gse301119_donor_aware_top_effects_v1.csv")
write.csv(sm, s_path, row.names = FALSE)
write.csv(tp, t_path, row.names = FALSE)

receipt <- list(
  schema = "GSE301119_DONOR_AWARE_TRANSCRIPTOME_ETL_V1",
  scope = "DEVELOPMENT_ETL_TWO_DONORS_NOT_POPULATION_GENERALIZABLE",
  biological_unit = "donor",
  n_biological_donors = 2L,
  population_standard_error_produced = FALSE,
  crispri_crispra_pooled = FALSE,
  controls = "donor-matched non-targeting guides, aggregated at raw-count level",
  declared_before_inspection = list(
    pseudocount = PSEUDOCOUNT, min_cells_per_unit = MIN_CELLS_UNIT,
    donors_required_for_cross_donor_mean = N_DONORS_REQ,
    aggregation = paste("raw integer counts summed across a target's guides",
                        "within a donor BEFORE normalisation, so a 6-cell guide",
                        "does not weigh equally with a 200-cell guide")),
  missingness_semantics = list(
    structurally_unmeasured = "gene absent from the 36,601-feature space",
    assayed_undetected = "gene present with zero counts in the compared groups",
    never_collapsed_to_zero_effect = TRUE),
  modalities = receipt_mod,
  target_summary_csv = s_path,
  top_effects_csv = t_path,
  jepa_prediction_used = FALSE,
  training_authorized = FALSE,
  therapeutic_ranking = FALSE,
  r_version = R.version.string,
  seurat_object_version = as.character(tryCatch(
    packageVersion("SeuratObject"), error = function(e) NA)))

writeLines(jsonlite::toJSON(receipt, auto_unbox = TRUE, pretty = TRUE, na = "null"),
           file.path(out_dir, "gse301119_donor_aware_receipt_v1.json"))

message("\n=== SUMMARY ===")
for (mod in modalities) {
  s <- sm[sm$modality == mod, ]
  message(sprintf("  %-8s targets %d | cross-donor estimable %d | guide-variance estimable %d",
                  mod, nrow(s), sum(s$cross_donor_mean_estimable),
                  sum(s$guide_variance_estimable)))
  ng <- s$target_gene[!s$guide_variance_estimable]
  if (length(ng)) message(sprintf("           guide variance NOT estimable: %s",
                                  paste(ng, collapse = ", ")))
  e <- s$engagement_log2fc[is.finite(s$engagement_log2fc)]
  message(sprintf("           engagement measured %d | median %.4f | own-gene status %s",
                  length(e), median(e),
                  paste(names(table(s$own_gene_status)), table(s$own_gene_status),
                        sep="=", collapse=" ")))
}
message("\nwrote ", s_path)
message("wrote ", t_path)
