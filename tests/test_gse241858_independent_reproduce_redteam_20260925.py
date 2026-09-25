"""Adversarial suite for the GSE241858 independent reproducer (audit P1-6).

Every fixture damages exactly ONE thing and requires
`independent_reproduce_gse241858_bulk_v1.py` to exit NONZERO. Exit status is
asserted, not message text.

`test_positive_control_undamaged_fixture_reproduces` is the POSITIVE CONTROL and
must PASS with exit 0. Without it a suite of rejections proves nothing: a script
that exited nonzero unconditionally would satisfy every other test here.

The two scientifically load-bearing cases are:

  * `test_clone_flattened_log2fc_rejected` -- a producer that treated the
    within-clone replicates as independent units. The fixture mirrors the real
    unbalanced cytokine cell (clone CTRL_A contributes one LPS replicate, clone
    CTRL_B two), which is the only place the point estimates differ. The balanced
    baseline arm cannot catch this, and the test proves the comparator does.
  * `test_replicate_level_se_rejected` -- the same error expressed in the
    standard error, where three replicates per clone masquerade as three
    biological units and shrink every interval.

The fixture's expected effects are computed by a small reference implementation
inside this module. It is a THIRD implementation, deliberately independent of
both the producer and the reproducer; the positive control is what establishes
that the three agree before any rejection is believed.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import os
import shutil
import subprocess
import sys

import numpy as np
import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "analysis", "therapeutic_perturbation_etl", "scripts",
                      "independent_reproduce_gse241858_bulk_v1.py")

BASELINE_SAMPLES = ["CTRL_A_1", "CTRL_A_2", "CTRL_A_3",
                    "CTRL_B_1", "CTRL_B_2", "CTRL_B_3",
                    "R47H_A_1", "R47H_A_2", "R47H_A_3",
                    "R47H_B_1", "R47H_B_2", "R47H_B_3"]
# The real cytokine column order, including the unbalanced CTRL_A LPS cell that
# has one replicate where every other cell has two.
CYTOKINE_SAMPLES = ["CTRL_A_1_UNTR", "CTRL_A_2_UNTR", "CTRL_A_1_IFN", "CTRL_A_2_IFN",
                    "CTRL_A_2_LPS",
                    "CTRL_B_1_UNTR", "CTRL_B_2_UNTR", "CTRL_B_1_IFN", "CTRL_B_2_IFN",
                    "CTRL_B_1_LPS", "CTRL_B_2_LPS",
                    "R47H_A_1_UNTR", "R47H_A_2_UNTR", "R47H_A_1_IFN", "R47H_A_2_IFN",
                    "R47H_A_1_LPS", "R47H_A_2_LPS",
                    "R47H_B_1_UNTR", "R47H_B_2_UNTR", "R47H_B_1_IFN", "R47H_B_2_IFN",
                    "R47H_B_1_LPS", "R47H_B_2_LPS"]

N_GENES = 40                      # gene N_GENES-1 is all-zero: assayed, undetected
EFFECT_FIELDS = ["study", "arm", "assay", "system", "contrast", "gene_id_namespace",
                 "gene_id", "gene_symbol", "log2fc", "se_clone_level",
                 "n_numerator_clone_units", "n_denominator_clone_units",
                 "experimental_unit", "note"]
IDENTITY_FIELDS = ["study", "arm", "sample_id", "genotype", "clone", "replicate",
                   "treatment", "total_counts", "file", "file_sha256"]

CONTRASTS = [
    ("R47H_vs_CTRL_baseline", "baseline",
     lambda u: u["genotype"] == "R47H", lambda u: u["genotype"] == "CTRL"),
    ("IFN_vs_UNTR_in_CTRL", "cytokine",
     lambda u: u["treatment"] == "IFN" and u["genotype"] == "CTRL",
     lambda u: u["treatment"] == "UNTR" and u["genotype"] == "CTRL"),
    ("IFN_vs_UNTR_in_R47H", "cytokine",
     lambda u: u["treatment"] == "IFN" and u["genotype"] == "R47H",
     lambda u: u["treatment"] == "UNTR" and u["genotype"] == "R47H"),
    ("LPS_vs_UNTR_in_CTRL", "cytokine",
     lambda u: u["treatment"] == "LPS" and u["genotype"] == "CTRL",
     lambda u: u["treatment"] == "UNTR" and u["genotype"] == "CTRL"),
    ("LPS_vs_UNTR_in_R47H", "cytokine",
     lambda u: u["treatment"] == "LPS" and u["genotype"] == "R47H",
     lambda u: u["treatment"] == "UNTR" and u["genotype"] == "R47H"),
    ("R47H_vs_CTRL_untreated", "cytokine",
     lambda u: u["genotype"] == "R47H" and u["treatment"] == "UNTR",
     lambda u: u["genotype"] == "CTRL" and u["treatment"] == "UNTR"),
]


# --------------------------------------------------------------------- helpers
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_sample(s):
    geno = "R47H" if s.startswith("R47H") else "CTRL"
    parts = s.split("_")
    treat = parts[3] if len(parts) == 4 else "BASELINE"
    return {"sample_id": s, "genotype": geno, "clone": f"{geno}_{parts[1]}",
            "replicate": int(parts[2]), "treatment": treat}


def synth_counts(samples, seed):
    """Deterministic integer counts; last gene is all-zero (assayed, undetected)."""
    rng = np.random.default_rng(seed)
    x = rng.integers(1, 5000, size=(len(samples), N_GENES)).astype(np.float64)
    x[:, N_GENES - 1] = 0.0
    return x


def write_matrix(path, samples, entrez, symbols, counts):
    with gzip.open(path, "wt", newline="") as fh:
        fh.write("\t".join(["ENTREZID", "SYMBOL"] + list(samples)) + "\n")
        for i in range(len(entrez)):
            fh.write("\t".join([entrez[i], symbols[i]]
                               + [str(int(v)) for v in counts[:, i]]) + "\n")


def ref_logcpm(counts):
    lib = np.maximum(counts.sum(axis=1, keepdims=True), 1.0)
    return np.log2(counts / lib * 1e6 + 1.0)


def ref_units(lg, meta):
    keys = [(m["clone"], m["treatment"]) for m in meta]
    uniq = sorted(set(keys))
    rows, umeta = [], []
    for u in uniq:
        idx = [i for i, k in enumerate(keys) if k == u]
        rows.append(lg[idx].mean(axis=0))
        umeta.append({"clone": u[0], "treatment": u[1],
                      "genotype": "R47H" if u[0].startswith("R47H") else "CTRL"})
    return np.vstack(rows), umeta


def ref_effect(mat, umeta, num, den):
    ni = [i for i, u in enumerate(umeta) if num(u)]
    di = [i for i, u in enumerate(umeta) if den(u)]
    d = mat[ni].mean(axis=0) - mat[di].mean(axis=0)
    se = np.sqrt(mat[ni].var(axis=0, ddof=1) / len(ni)
                 + mat[di].var(axis=0, ddof=1) / len(di))
    return d, se, len(ni), len(di)


def build_effects(arm_data, clone_blind_lfc=False, clone_blind_se=False):
    """Producer-style effect rows. The two flags reproduce the clone-blind error."""
    rows = []
    for name, arm, num, den in CONTRASTS:
        d = arm_data[arm]
        lfc, se, nn, nd = ref_effect(d["units"], d["umeta"], num, den)
        if clone_blind_lfc or clone_blind_se:
            flat_lfc, flat_se, fn, fd = ref_effect(d["lg"], d["meta"], num, den)
            if clone_blind_lfc:
                lfc, nn, nd = flat_lfc, fn, fd
            if clone_blind_se:
                se = flat_se
        for k in np.flatnonzero(d["detected"]):
            rows.append({
                "study": "GSE241858", "arm": arm, "assay": "bulk_RNAseq",
                "system": "iPSC-derived microglia", "contrast": name,
                "gene_id_namespace": "ENTREZID", "gene_id": d["entrez"][k],
                "gene_symbol": d["symbols"][k],
                "log2fc": round(float(lfc[k]), 6),
                "se_clone_level": round(float(se[k]), 6),
                "n_numerator_clone_units": nn, "n_denominator_clone_units": nd,
                "experimental_unit": "iPSC clone", "note": "fixture"})
    return rows


def write_csv(path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def build_fixture(root):
    """Write a coherent, undamaged fixture into `root`; return its arm data."""
    os.makedirs(root, exist_ok=True)
    bs = list(BASELINE_SAMPLES)
    cs = list(CYTOKINE_SAMPLES)
    entrez = [str(i + 1) for i in range(N_GENES)]
    symbols = [f"G{i + 1}" for i in range(N_GENES)]

    arm_data, identity = {}, []
    for arm, samples, seed in (("baseline", bs, 11), ("cytokine", cs, 22)):
        counts = synth_counts(samples, seed)
        path = os.path.join(root, f"{arm}.txt.gz")
        write_matrix(path, samples, entrez, symbols, counts)
        meta = [parse_sample(s) for s in samples]
        lg = ref_logcpm(counts)
        units, umeta = ref_units(lg, meta)
        arm_data[arm] = {"path": path, "counts": counts, "meta": meta, "lg": lg,
                         "units": units, "umeta": umeta, "entrez": entrez,
                         "symbols": symbols, "detected": counts.sum(axis=0) > 0}
        digest = sha256_file(path)
        for m, tot in zip(meta, counts.sum(axis=1)):
            identity.append({"study": "GSE241858", "arm": arm, **m,
                             "total_counts": int(tot),
                             "file": os.path.basename(path), "file_sha256": digest})

    write_csv(os.path.join(root, "effects.csv"), EFFECT_FIELDS, build_effects(arm_data))
    write_csv(os.path.join(root, "identity.csv"), IDENTITY_FIELDS, identity)
    return arm_data


def run(root, skip_root_check=True, out_name="out"):
    out = os.path.join(root, out_name)
    if os.path.exists(out):
        shutil.rmtree(out)
    cmd = [sys.executable, SCRIPT,
           "--baseline-counts", os.path.join(root, "baseline.txt.gz"),
           "--cytokine-counts", os.path.join(root, "cytokine.txt.gz"),
           "--producer-effects", os.path.join(root, "effects.csv"),
           "--producer-sample-identity", os.path.join(root, "identity.csv"),
           "--out-dir", out]
    if skip_root_check:
        cmd.append("--skip-source-root-check")
    return subprocess.run(cmd, capture_output=True, text=True)


def rewrite_matrix_lines(path, fn):
    """Apply `fn(list_of_lines) -> list_of_lines` to a gzipped matrix in place."""
    with gzip.open(path, "rt", newline="") as fh:
        lines = fh.read().splitlines()
    out = fn(lines)
    with gzip.open(path, "wt", newline="") as fh:
        fh.write("\n".join(out) + "\n")


@pytest.fixture()
def fx(tmp_path):
    root = str(tmp_path / "fx")
    data = build_fixture(root)
    return root, data


# --------------------------------------------------------------- POSITIVE CONTROL
def test_positive_control_undamaged_fixture_reproduces(fx):
    """POSITIVE CONTROL. Without this, every rejection below is untrustworthy."""
    root, _ = fx
    r = run(root)
    assert r.returncode == 0, f"positive control failed:\n{r.stdout}\n{r.stderr}"
    assert "IMPLEMENTATION_REPRODUCED" in r.stdout
    assert "DISAGREE" not in r.stdout


def test_positive_control_controls_all_fired(fx):
    """The reproducer's own controls must report as fired on a clean fixture."""
    root, _ = fx
    r = run(root)
    assert r.returncode == 0
    assert "sign control (reversed contrast negates exactly): True" in r.stdout
    assert "distinguishable=True" in r.stdout


# ------------------------------------------------- the clone-structure defences
def test_clone_flattened_log2fc_rejected(fx):
    """Replicates treated as independent units. Only the UNBALANCED cell shows it."""
    root, data = fx
    write_csv(os.path.join(root, "effects.csv"), EFFECT_FIELDS,
              build_effects(data, clone_blind_lfc=True))
    assert run(root).returncode != 0


def test_replicate_level_se_rejected(fx):
    """Clone-level SE replaced by a replicate-level SE: fabricated replication."""
    root, data = fx
    write_csv(os.path.join(root, "effects.csv"), EFFECT_FIELDS,
              build_effects(data, clone_blind_se=True))
    assert run(root).returncode != 0


def test_clone_unit_counts_overstated_rejected(fx):
    """n_numerator_clone_units claiming 6 units where there are 2."""
    root, data = fx
    rows = build_effects(data)
    for row in rows:
        row["n_numerator_clone_units"] = 6
    write_csv(os.path.join(root, "effects.csv"), EFFECT_FIELDS, rows)
    assert run(root).returncode != 0


# ------------------------------------------------------- degenerate raw inputs
def test_empty_group_rejected(fx):
    """Every CTRL column removed from the baseline arm: the contrast has no denominator."""
    root, _ = fx
    def drop_ctrl(lines):
        cols = lines[0].split("\t")
        keep = [0, 1] + [i for i, c in enumerate(cols)
                         if i >= 2 and not c.startswith("CTRL")]
        return ["\t".join([ln.split("\t")[i] for i in keep]) for ln in lines]
    rewrite_matrix_lines(os.path.join(root, "baseline.txt.gz"), drop_ctrl)
    r = run(root)
    assert r.returncode != 0
    assert "EMPTY_GROUP" in (r.stdout + r.stderr)


def test_missing_sample_rejected(fx):
    """One sample column dropped from the count matrix but kept in the identity table."""
    root, _ = fx
    def drop(lines):
        return ["\t".join(p.split("\t")[:-1]) for p in lines]
    rewrite_matrix_lines(os.path.join(root, "baseline.txt.gz"), drop)
    assert run(root).returncode != 0


def test_duplicated_gene_id_rejected(fx):
    root, _ = fx
    def dup(lines):
        out = list(lines)
        parts = out[2].split("\t")
        parts[0] = out[1].split("\t")[0]      # second gene reuses the first ENTREZID
        out[2] = "\t".join(parts)
        return out
    rewrite_matrix_lines(os.path.join(root, "baseline.txt.gz"), dup)
    r = run(root)
    assert r.returncode != 0
    assert "DUPLICATE_GENE_ID" in (r.stdout + r.stderr)


def test_negative_count_rejected(fx):
    root, _ = fx
    def neg(lines):
        out = list(lines)
        parts = out[1].split("\t")
        parts[2] = "-5"
        out[1] = "\t".join(parts)
        return out
    rewrite_matrix_lines(os.path.join(root, "cytokine.txt.gz"), neg)
    r = run(root)
    assert r.returncode != 0
    assert "NEGATIVE_COUNT" in (r.stdout + r.stderr)


def test_non_integer_count_rejected(fx):
    root, _ = fx
    def frac(lines):
        out = list(lines)
        parts = out[1].split("\t")
        parts[2] = "12.5"
        out[1] = "\t".join(parts)
        return out
    rewrite_matrix_lines(os.path.join(root, "baseline.txt.gz"), frac)
    r = run(root)
    assert r.returncode != 0
    assert "NONINTEGER" in (r.stdout + r.stderr)


def test_ragged_row_rejected(fx):
    root, _ = fx
    def ragged(lines):
        out = list(lines)
        out[3] = "\t".join(out[3].split("\t")[:-2])
        return out
    rewrite_matrix_lines(os.path.join(root, "baseline.txt.gz"), ragged)
    r = run(root)
    assert r.returncode != 0
    assert "RAGGED_ROW" in (r.stdout + r.stderr)


def test_unparsed_sample_id_rejected(fx):
    """A column label outside the declared CTRL/R47H x clone x replicate grammar."""
    root, _ = fx
    def relabel(lines):
        out = list(lines)
        cols = out[0].split("\t")
        cols[2] = "WILDTYPE_1"
        out[0] = "\t".join(cols)
        return out
    rewrite_matrix_lines(os.path.join(root, "baseline.txt.gz"), relabel)
    r = run(root)
    assert r.returncode != 0
    assert "UNPARSED_SAMPLE_ID" in (r.stdout + r.stderr)


def test_unexpected_header_rejected(fx):
    root, _ = fx
    def rehead(lines):
        out = list(lines)
        out[0] = out[0].replace("ENTREZID", "GENE", 1)
        return out
    rewrite_matrix_lines(os.path.join(root, "baseline.txt.gz"), rehead)
    r = run(root)
    assert r.returncode != 0
    assert "UNEXPECTED_HEADER" in (r.stdout + r.stderr)


def test_permuted_sample_columns_rejected(fx):
    """Count columns rotated relative to their header labels: every sample mislabelled."""
    root, _ = fx
    def permute(lines):
        out = [lines[0]]
        for ln in lines[1:]:
            parts = ln.split("\t")
            vals = parts[2:]
            out.append("\t".join(parts[:2] + vals[6:] + vals[:6]))
        return out
    rewrite_matrix_lines(os.path.join(root, "baseline.txt.gz"), permute)
    r = run(root)
    assert r.returncode != 0
    assert "DISAGREE" in r.stdout


# ------------------------------------------------------ damaged producer output
def test_perturbed_log2fc_rejected(fx):
    root, data = fx
    rows = build_effects(data)
    rows[0]["log2fc"] = round(float(rows[0]["log2fc"]) + 0.01, 6)
    write_csv(os.path.join(root, "effects.csv"), EFFECT_FIELDS, rows)
    r = run(root)
    assert r.returncode != 0
    assert "DISAGREE" in r.stdout


def test_undetected_gene_emitted_rejected(fx):
    """The all-zero gene must not appear: it is assayed but undetected."""
    root, data = fx
    rows = build_effects(data)
    ghost = dict(rows[0])
    ghost["gene_id"] = str(N_GENES)
    ghost["gene_symbol"] = f"G{N_GENES}"
    rows.append(ghost)
    write_csv(os.path.join(root, "effects.csv"), EFFECT_FIELDS, rows)
    assert run(root).returncode != 0


def test_gene_symbol_mismatch_rejected(fx):
    root, data = fx
    rows = build_effects(data)
    rows[0]["gene_symbol"] = "NOT_THE_RIGHT_SYMBOL"
    write_csv(os.path.join(root, "effects.csv"), EFFECT_FIELDS, rows)
    assert run(root).returncode != 0


def test_identity_library_size_mismatch_rejected(fx):
    root, data = fx
    with open(os.path.join(root, "identity.csv"), newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    rows[0]["total_counts"] = int(rows[0]["total_counts"]) + 1
    write_csv(os.path.join(root, "identity.csv"), IDENTITY_FIELDS, rows)
    assert run(root).returncode != 0


def test_source_byte_root_check_fires(fx):
    """Run WITHOUT the fixture escape hatch: a synthetic matrix is not the GEO file."""
    root, _ = fx
    r = run(root, skip_root_check=False)
    assert r.returncode != 0
    assert "SOURCE_ROOT_MISMATCH" in (r.stdout + r.stderr)


def test_existing_output_dir_refused(fx):
    """A populated output directory must stop the run rather than overwrite it."""
    root, _ = fx
    out = os.path.join(root, "out")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "stale.json"), "w") as fh:
        fh.write("{}")
    cmd = [sys.executable, SCRIPT,
           "--baseline-counts", os.path.join(root, "baseline.txt.gz"),
           "--cytokine-counts", os.path.join(root, "cytokine.txt.gz"),
           "--producer-effects", os.path.join(root, "effects.csv"),
           "--producer-sample-identity", os.path.join(root, "identity.csv"),
           "--out-dir", out, "--skip-source-root-check"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode != 0
    assert "OUTPUT_EXISTS" in (r.stdout + r.stderr)
