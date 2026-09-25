"""Adversarial suite for the GSE301119 donor-aware R producer (self-audit S7).

The R producer validates identity, not merely shape. This suite proves each of
those validations actually fires, by building small synthetic pseudobulk RDS
objects with the same schema as the authenticated ones and damaging exactly one
thing at a time.

Every fixture must make the producer exit NONZERO. Exit status is asserted, not
message text.

The two load-bearing cases are:

  * `test_column_permutation_rejected` — v1 checked only `ncol(counts) ==
    nrow(meta)`, so permuting the count columns relative to the metadata would
    have passed silently and silently mismatched every guide to the wrong group;
  * `test_input_digest_mismatch_rejected` — v1 never verified the input RDS
    digest at all.

Each fixture writes its own provenance manifest, so the digest check has
something to verify against; the digest-mismatch test deliberately writes a
wrong one.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCER = os.path.join(REPO, "analysis", "therapeutic_perturbation_etl",
                        "scripts", "r", "build_gse301119_donor_aware_transcriptome_v2.R")
RSCRIPT = "D:/R-4.6.1/bin/x64/Rscript.exe"
RLIB = "D:/jepa_rlib46"

r_available = os.path.exists(RSCRIPT) and os.path.exists(RLIB)

# R snippet that builds a minimal valid pseudobulk pair, then applies a named
# mutation. Kept in one place so every fixture differs by exactly one line.
BUILD_R = r'''
.libPaths("%(rlib)s")
mut  <- "%(mut)s"
out  <- "%(dir)s"
dir.create(out, recursive = TRUE, showWarnings = FALSE)

mk <- function(mod) {
  feats  <- c("GENEA", "GENEB", "TGT1", "TGT2")
  gd     <- c("TGT1_g1||D1","TGT1_g2||D1","TGT1_g1||D2","TGT1_g2||D2",
              "nt1||D1","nt2||D1","nt1||D2","nt2||D2")
  # fixed split, not regex: "||" needs no escaping this way, and an escaping
  # slip here silently produced a donor column holding the whole key, which the
  # positive control caught.
  parts <- strsplit(gd, "||", fixed = TRUE)
  meta <- data.frame(
    guide_donor    = gd,
    guide_identity = vapply(parts, function(x) x[1], character(1)),
    donor          = vapply(parts, function(x) x[2], character(1)),
    Gene_Targeted  = c(rep("TGT1", 4), rep("", 4)),
    crispr         = c(rep("Perturbed", 4), rep("NT", 4)),
    n_cells        = rep(50L, 8),
    total_counts   = rep(400L, 8),
    stringsAsFactors = FALSE)
  set.seed(1)
  cnt <- matrix(as.numeric(sample(20:80, length(feats) * nrow(meta), TRUE)),
                nrow = length(feats), dimnames = list(feats, gd))

  if (mut == "column_permutation")  cnt <- cnt[, c(2,1,3,4,5,6,7,8), drop = FALSE]
  if (mut == "duplicate_feature")   { feats[2] <- "GENEA"; rownames(cnt) <- feats }
  if (mut == "duplicate_key")       { meta$guide_donor[2] <- meta$guide_donor[1]
                                      colnames(cnt) <- meta$guide_donor }
  if (mut == "donor_label")         { meta$donor[1] <- "D3"
                                      meta$guide_donor <- paste0(meta$guide_identity,"||",meta$donor)
                                      colnames(cnt) <- meta$guide_donor }
  if (mut == "no_nt_for_donor")     { meta$crispr[meta$crispr=="NT" & meta$donor=="D2"] <- "Perturbed"
                                      meta$Gene_Targeted[meta$crispr=="Perturbed" & meta$Gene_Targeted==""] <- "TGT1" }
  if (mut == "zero_depth_nt")       cnt[, meta$crispr == "NT" & meta$donor == "D1"] <- 0
  if (mut == "negative_count")      cnt[1, 1] <- -5
  if (mut == "non_integer")         cnt[1, 1] <- 3.5
  if (mut == "non_finite")          cnt[1, 1] <- NA_real_
  if (mut == "unexpected_role")     meta$crispr[1] <- "MYSTERY"

  libsz <- colSums(cnt)
  if (mut == "libsize_disagrees")   libsz <- libsz + 1

  feat_out <- rownames(cnt)
  # drift the MATRIX rownames only, leaving `features` at the original labels,
  # so rownames(counts) != features is genuinely violated
  if (mut == "rowname_drift") rownames(cnt)[2] <- "GENEZ"

  list(schema = "GSE301119_GUIDE_DONOR_RAW_PSEUDOBULK_V1",
       features = feat_out, gd_meta = meta, counts = cnt,
       library_size = libsz)
}

for (mod in c("CRISPRi", "CRISPRa"))
  saveRDS(mk(mod), file.path(out, sprintf("%%s_guide_donor_raw_counts.rds", mod)))

man <- list(heavyweight_outputs_on_local_disk = list())
for (mod in c("CRISPRi", "CRISPRa")) {
  f <- file.path(out, sprintf("%%s_guide_donor_raw_counts.rds", mod))
  d <- if (mut == "digest_mismatch") paste(rep("0", 64), collapse = "")
       else digest::digest(file = f, algo = "sha256")
  man$heavyweight_outputs_on_local_disk[[basename(f)]] <- list(sha256 = d)
}
writeLines(jsonlite::toJSON(man, auto_unbox = TRUE), file.path(out, "manifest.json"))
cat("FIXTURE_OK\n")
'''


def build_fixture(tmp, mutation):
    d = os.path.join(tmp, "pb").replace("\\", "/")
    script = os.path.join(tmp, "mk.R")
    with open(script, "w") as fh:
        fh.write(BUILD_R % {"rlib": RLIB, "mut": mutation, "dir": d})
    r = subprocess.run([RSCRIPT, script], capture_output=True, text=True)
    if "FIXTURE_OK" not in r.stdout:
        raise RuntimeError("fixture build failed: " + (r.stdout + r.stderr)[-600:])
    return d


def run_producer(pb_dir, out_dir):
    return subprocess.run(
        [RSCRIPT, PRODUCER, "--pseudobulk-dir", pb_dir,
         "--out-dir", out_dir.replace("\\", "/"),
         "--provenance-manifest", os.path.join(pb_dir, "manifest.json").replace("\\", "/"),
         "--rlib", RLIB], capture_output=True, text=True).returncode


pytestmark = pytest.mark.skipif(
    not r_available, reason="R 4.6.1 / jepa_rlib46 not on this machine")


def test_positive_control_healthy_fixture_exits_zero():
    with tempfile.TemporaryDirectory() as tmp:
        assert run_producer(build_fixture(tmp, "none"),
                            os.path.join(tmp, "out")) == 0


@pytest.mark.parametrize("mutation", [
    "column_permutation",    # v1 would have passed this silently
    "rowname_drift",
    "duplicate_feature",
    "duplicate_key",
    "donor_label",
    "no_nt_for_donor",
    "zero_depth_nt",
    "negative_count",
    "non_integer",
    "non_finite",
    "unexpected_role",
    "libsize_disagrees",
    "digest_mismatch",       # v1 never checked this at all
])
def test_mutation_rejected(mutation):
    with tempfile.TemporaryDirectory() as tmp:
        assert run_producer(build_fixture(tmp, mutation),
                            os.path.join(tmp, "out")) != 0, \
            f"producer accepted a fixture damaged by {mutation}"


def test_occupied_output_directory_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        pb = build_fixture(tmp, "none")
        out = os.path.join(tmp, "out")
        os.makedirs(out)
        with open(os.path.join(out, "prior.json"), "w") as fh:
            fh.write("{}")
        assert run_producer(pb, out) != 0


def test_missing_provenance_manifest_rejected():
    """Input digests must be bound; an absent manifest cannot be waved through."""
    with tempfile.TemporaryDirectory() as tmp:
        pb = build_fixture(tmp, "none")
        os.remove(os.path.join(pb, "manifest.json"))
        assert run_producer(pb, os.path.join(tmp, "out")) != 0


def test_donor_wise_matrices_are_persisted():
    """Required for independent reproduction; v1 stored only the cross-donor mean."""
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "out")
        assert run_producer(build_fixture(tmp, "none"), out) == 0
        with open(os.path.join(out, "gse301119_donor_aware_receipt_v2.json")) as fh:
            rec = json.load(fh)
        assert rec["donor_wise_matrices_persisted"] is True
        assert rec["guide_level_variance_computed"] is False
        assert rec["population_standard_error_produced"] is False
        assert rec["crispri_crispra_pooled"] is False
        for mod in ("CRISPRi", "CRISPRa"):
            assert os.path.exists(
                os.path.join(out, f"{mod}_donor_aware_effects_v2.rds"))
