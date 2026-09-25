"""Adversarial suite for the GSE240609 independent reproducer (audit P1-6).

Every fixture damages exactly ONE thing and requires
`independent_reproduce_gse240609_bulk_v1.py` to exit NONZERO. Exit status is
asserted, not message text.

`test_positive_control_undamaged_fixture_reproduces` is the POSITIVE CONTROL and
must PASS with exit 0. Without it a suite of rejections proves nothing.

The load-bearing cases here are the two ways this study is easiest to get wrong:

  * the headerless files. The first physical line is the A1BG gene row, not a
    header. A parser that consumes it yields 27,153 genes and shifts every gene
    label by one row -- silently, since the shape still looks plausible. A prior
    pass made exactly this error. `test_gene_count_27153_rejected` and
    `test_prepended_header_rejected` cover both directions of that trap.
  * fabricated replication. There is ONE sample per 2x2 design cell, so
    biological uncertainty is not estimable. A standard error here would describe
    sequencing noise in a single library and would be read as replication that
    does not exist. Three tests require the reproducer to reject it.

The fixture's expected effects come from a small reference implementation in this
module -- a third implementation, independent of producer and reproducer. The
positive control establishes that the three agree before any rejection counts.
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
                      "independent_reproduce_gse240609_bulk_v1.py")

# Declared in the reproducer: the first physical line is a GENE ROW.
N_GENES = 27154
FIRST_GENE = "A1BG"
MATERIAL = "CD11B_PURIFIED_MICROGLIA_AFTER_NEURON_COCULTURE"

# The four real GEO filenames; the design cell is derived from them.
FILES = {
    "GSM7703564_45229_14048iN_APOEChurchMG_gene_counts.txt.gz": ("WT", "APOE3ch"),
    "GSM7703567_45232_14048PSEN_iN_APOECHurchMG_gene_counts.txt.gz": ("PSEN", "APOE3ch"),
    "GSM7703569_45227_14048iN_APOE3MG_gene_counts.txt.gz": ("WT", "APOE3"),
    "GSM7703571_45230_14048PSEN_iN_APOE3MG_gene_counts.txt.gz": ("PSEN", "APOE3"),
}

EFFECT_FIELDS = ["study", "assay", "material", "contrast", "neuron_genotype",
                 "gene_id_namespace", "gene_id", "log2fc", "se", "n_numerator",
                 "n_denominator", "uncertainty_estimable", "note"]
IDENTITY_FIELDS = ["study", "gsm", "geo_title", "geo_series_url", "file",
                   "file_sha256", "neuron_genotype", "microglia_genotype",
                   "material", "sample_unit", "biological_uncertainty_estimable"]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def gene_names():
    """A1BG first -- exactly as in the deposited headerless files."""
    return [FIRST_GENE] + [f"GENE{i:06d}" for i in range(1, N_GENES)]


def ref_logcpm(counts):
    lib = np.maximum(counts.sum(axis=1, keepdims=True), 1.0)
    return np.log2(counts / lib * 1e6 + 1.0)


def write_counts(path, genes, vals):
    with gzip.open(path, "wt", newline="") as fh:
        for g, v in zip(genes, vals):
            fh.write(f"{g}\t{int(v)}\n")


def build_fixture(root, files=None):
    """Write a coherent, undamaged fixture into `root`."""
    counts_dir = os.path.join(root, "counts")
    os.makedirs(counts_dir, exist_ok=True)
    genes = gene_names()
    spec = FILES if files is None else files
    names = sorted(spec)

    rng = np.random.default_rng(7)
    mat = rng.integers(1, 4000, size=(len(names), N_GENES)).astype(np.float64)
    mat[:, -1] = 0.0                       # assayed but undetected everywhere
    for i, n in enumerate(names):
        write_counts(os.path.join(counts_dir, n), genes, mat[i])

    lg = ref_logcpm(mat)
    detected = mat.sum(axis=0) > 0
    cells = {spec[n]: i for i, n in enumerate(names)}

    rows = []
    for neuron in sorted({g[0] for g in spec.values()}):
        a, b = cells.get((neuron, "APOE3ch")), cells.get((neuron, "APOE3"))
        if a is None or b is None:
            continue
        d = lg[a] - lg[b]
        for k in np.flatnonzero(detected):
            rows.append({
                "study": "GSE240609", "assay": "bulk_RNAseq", "material": MATERIAL,
                "contrast": f"APOE3ch_vs_APOE3_microglia_in_{neuron}_neurons",
                "neuron_genotype": neuron, "gene_id_namespace": "SYMBOL",
                "gene_id": genes[k], "log2fc": round(float(d[k]), 6), "se": "",
                "n_numerator": 1, "n_denominator": 1,
                "uncertainty_estimable": False, "note": "fixture"})
    write_csv(os.path.join(root, "effects.csv"), EFFECT_FIELDS, rows)

    identity = []
    for i, n in enumerate(names):
        neuron, micro = spec[n]
        identity.append({
            "study": "GSE240609", "gsm": n.split("_")[0], "geo_title": "fixture",
            "geo_series_url": "fixture",
            "file": n, "file_sha256": sha256_file(os.path.join(counts_dir, n)),
            "neuron_genotype": neuron, "microglia_genotype": micro,
            "material": MATERIAL,
            "sample_unit": "one original sample per genotype cross",
            "biological_uncertainty_estimable": False})
    write_csv(os.path.join(root, "identity.csv"), IDENTITY_FIELDS, identity)
    return {"genes": genes, "counts_dir": counts_dir, "names": names,
            "rows": rows, "identity": identity}


def write_csv(path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def refresh_identity_digests(root, fixture):
    """Recompute the identity table's file digests after a count file is edited."""
    ident = fixture["identity"]
    for row in ident:
        row["file_sha256"] = sha256_file(os.path.join(fixture["counts_dir"], row["file"]))
    write_csv(os.path.join(root, "identity.csv"), IDENTITY_FIELDS, ident)


def run(root, fixture, skip_root_check=True):
    out = os.path.join(root, "out")
    if os.path.exists(out):
        shutil.rmtree(out)
    cmd = [sys.executable, SCRIPT,
           "--counts-dir", fixture["counts_dir"],
           "--producer-effects", os.path.join(root, "effects.csv"),
           "--producer-sample-identity", os.path.join(root, "identity.csv"),
           "--out-dir", out]
    if skip_root_check:
        cmd.append("--skip-source-root-check")
    return subprocess.run(cmd, capture_output=True, text=True)


def rewrite_lines(path, fn):
    with gzip.open(path, "rt", newline="") as fh:
        lines = fh.read().splitlines()
    with gzip.open(path, "wt", newline="") as fh:
        fh.write("\n".join(fn(lines)) + "\n")


@pytest.fixture(scope="module")
def pristine(tmp_path_factory):
    root = str(tmp_path_factory.mktemp("gse240609_pristine"))
    return root, build_fixture(root)


@pytest.fixture()
def fx(tmp_path, pristine):
    """A private copy of the pristine fixture, so each test damages only its own."""
    src, meta = pristine
    root = str(tmp_path / "fx")
    shutil.copytree(src, root, ignore=shutil.ignore_patterns("out"))
    local = dict(meta)
    local["counts_dir"] = os.path.join(root, "counts")
    local["identity"] = [dict(r) for r in meta["identity"]]
    local["rows"] = [dict(r) for r in meta["rows"]]
    return root, local


# --------------------------------------------------------------- POSITIVE CONTROL
def test_positive_control_undamaged_fixture_reproduces(fx):
    """POSITIVE CONTROL. Without this, every rejection below is untrustworthy."""
    root, meta = fx
    r = run(root, meta)
    assert r.returncode == 0, f"positive control failed:\n{r.stdout}\n{r.stderr}"
    assert "IMPLEMENTATION_REPRODUCED" in r.stdout
    assert "DISAGREE" not in r.stdout


def test_positive_control_a1bg_retained_and_controls_fired(fx):
    """27,154 genes, A1BG kept as a gene row, and the header-bug control fires."""
    root, meta = fx
    r = run(root, meta)
    assert r.returncode == 0
    assert f"genes parsed {N_GENES} (expected {N_GENES})" in r.stdout
    assert f"first gene '{FIRST_GENE}'" in r.stdout
    assert f"header-consuming={N_GENES - 1}" in r.stdout
    assert "A1BG retained=True dropped-by-bug=True" in r.stdout
    assert "detectable=True" in r.stdout


# ------------------------------------------------------ the headerless-file trap
def test_gene_count_27153_rejected(fx):
    """A1BG dropped from every file: 27,153 genes is the signature of the bug."""
    root, meta = fx
    for n in meta["names"]:
        rewrite_lines(os.path.join(meta["counts_dir"], n), lambda L: L[1:])
    refresh_identity_digests(root, meta)
    r = run(root, meta)
    assert r.returncode != 0
    assert "GENE_COUNT_MISMATCH" in (r.stdout + r.stderr)
    assert f"got {N_GENES - 1}" in (r.stdout + r.stderr)


def test_prepended_header_rejected(fx):
    """A header line added where the format declares none. It must not be consumed.

    Either refusal is correct and both are fail-closed: the textual value trips
    the count parser before the row tally is reached, so the stop may name the
    unparseable value rather than the 27,155 row count. What must NOT happen is a
    silent skip of the first line, which is the bug this whole guard exists for.
    """
    root, meta = fx
    for n in meta["names"]:
        rewrite_lines(os.path.join(meta["counts_dir"], n),
                      lambda L: ["gene\tcount"] + L)
    refresh_identity_digests(root, meta)
    r = run(root, meta)
    assert r.returncode != 0
    blob = r.stdout + r.stderr
    assert "UNPARSEABLE_COUNT" in blob or "GENE_COUNT_MISMATCH" in blob, blob


def test_first_gene_not_a1bg_rejected(fx):
    root, meta = fx
    for n in meta["names"]:
        rewrite_lines(os.path.join(meta["counts_dir"], n),
                      lambda L: [L[0].replace(FIRST_GENE, "ZZZFAKE", 1)] + L[1:])
    refresh_identity_digests(root, meta)
    r = run(root, meta)
    assert r.returncode != 0
    assert "FIRST_GENE_NOT" in (r.stdout + r.stderr)


# ------------------------------------------------- fabricated-replication guards
def test_fabricated_se_rejected(fx):
    """n=1 per design cell: any numeric standard error is fabricated replication."""
    root, meta = fx
    rows = [dict(r) for r in meta["rows"]]
    rows[0]["se"] = 0.123456
    write_csv(os.path.join(root, "effects.csv"), EFFECT_FIELDS, rows)
    assert run(root, meta).returncode != 0


def test_fabricated_replicate_count_rejected(fx):
    root, meta = fx
    rows = [dict(r) for r in meta["rows"]]
    rows[0]["n_numerator"] = 3
    write_csv(os.path.join(root, "effects.csv"), EFFECT_FIELDS, rows)
    assert run(root, meta).returncode != 0


def test_uncertainty_estimable_true_rejected(fx):
    root, meta = fx
    rows = [dict(r) for r in meta["rows"]]
    rows[0]["uncertainty_estimable"] = True
    write_csv(os.path.join(root, "effects.csv"), EFFECT_FIELDS, rows)
    assert run(root, meta).returncode != 0


def test_identity_claiming_uncertainty_estimable_rejected(fx):
    root, meta = fx
    ident = [dict(r) for r in meta["identity"]]
    ident[0]["biological_uncertainty_estimable"] = True
    write_csv(os.path.join(root, "identity.csv"), IDENTITY_FIELDS, ident)
    assert run(root, meta).returncode != 0


# ------------------------------------------------------- degenerate raw inputs
def test_missing_sample_rejected(fx):
    """One of the four design cells absent: the 2x2 is no longer complete."""
    root, meta = fx
    os.remove(os.path.join(meta["counts_dir"], meta["names"][0]))
    r = run(root, meta)
    assert r.returncode != 0
    assert "DESIGN_CELL" in (r.stdout + r.stderr)


def test_duplicated_gene_id_rejected(fx):
    root, meta = fx
    n = meta["names"][0]
    rewrite_lines(os.path.join(meta["counts_dir"], n),
                  lambda L: [L[0]] + [L[0].split("\t")[0] + "\t5"] + L[2:])
    refresh_identity_digests(root, meta)
    r = run(root, meta)
    assert r.returncode != 0
    assert "DUPLICATE_GENE_ID" in (r.stdout + r.stderr)


def test_negative_count_rejected(fx):
    root, meta = fx
    n = meta["names"][0]
    rewrite_lines(os.path.join(meta["counts_dir"], n),
                  lambda L: [f"{FIRST_GENE}\t-3"] + L[1:])
    refresh_identity_digests(root, meta)
    r = run(root, meta)
    assert r.returncode != 0
    assert "NEGATIVE_COUNT" in (r.stdout + r.stderr)


def test_non_integer_count_rejected(fx):
    root, meta = fx
    n = meta["names"][0]
    rewrite_lines(os.path.join(meta["counts_dir"], n),
                  lambda L: [f"{FIRST_GENE}\t12.5"] + L[1:])
    refresh_identity_digests(root, meta)
    r = run(root, meta)
    assert r.returncode != 0
    assert "NONINTEGER" in (r.stdout + r.stderr)


def test_gene_order_differs_between_files_rejected(fx):
    """Same genes, different order: the merge would silently mismatch every row."""
    root, meta = fx
    n = meta["names"][1]
    rewrite_lines(os.path.join(meta["counts_dir"], n),
                  lambda L: [L[0]] + L[2:3] + L[1:2] + L[3:])
    refresh_identity_digests(root, meta)
    r = run(root, meta)
    assert r.returncode != 0
    assert "GENE_ORDER_DIFFERS" in (r.stdout + r.stderr)


def test_swapped_sample_contents_rejected(fx):
    """APOE3ch and APOE3 libraries exchanged: the contrast inverts, labels do not."""
    root, meta = fx
    a = os.path.join(meta["counts_dir"],
                     "GSM7703564_45229_14048iN_APOEChurchMG_gene_counts.txt.gz")
    b = os.path.join(meta["counts_dir"],
                     "GSM7703569_45227_14048iN_APOE3MG_gene_counts.txt.gz")
    tmp = a + ".swap"
    os.replace(a, tmp); os.replace(b, a); os.replace(tmp, b)
    refresh_identity_digests(root, meta)
    r = run(root, meta)
    assert r.returncode != 0
    assert "DISAGREE" in r.stdout


# ------------------------------------------------------ damaged producer output
def test_perturbed_log2fc_rejected(fx):
    root, meta = fx
    rows = [dict(r) for r in meta["rows"]]
    rows[0]["log2fc"] = round(float(rows[0]["log2fc"]) + 0.01, 6)
    write_csv(os.path.join(root, "effects.csv"), EFFECT_FIELDS, rows)
    r = run(root, meta)
    assert r.returncode != 0
    assert "DISAGREE" in r.stdout


def test_undetected_gene_emitted_rejected(fx):
    """The all-zero gene is assayed but undetected and must not be emitted."""
    root, meta = fx
    rows = [dict(r) for r in meta["rows"]]
    ghost = dict(rows[0])
    ghost["gene_id"] = meta["genes"][-1]
    rows.append(ghost)
    write_csv(os.path.join(root, "effects.csv"), EFFECT_FIELDS, rows)
    assert run(root, meta).returncode != 0


def test_identity_genotype_disagreement_rejected(fx):
    """The identity table contradicting the filename-derived design cell."""
    root, meta = fx
    ident = [dict(r) for r in meta["identity"]]
    ident[0]["neuron_genotype"] = "PSEN" if ident[0]["neuron_genotype"] == "WT" else "WT"
    write_csv(os.path.join(root, "identity.csv"), IDENTITY_FIELDS, ident)
    assert run(root, meta).returncode != 0


def test_material_label_mismatch_rejected(fx):
    """Relabelling the material as an intrinsic microglial assay."""
    root, meta = fx
    rows = [dict(r) for r in meta["rows"]]
    for row in rows:
        row["material"] = "INTRINSIC_MICROGLIA"
    write_csv(os.path.join(root, "effects.csv"), EFFECT_FIELDS, rows)
    assert run(root, meta).returncode != 0


def test_source_byte_root_check_fires(fx):
    """Run WITHOUT the fixture escape hatch: synthetic files are not the GEO files."""
    root, meta = fx
    r = run(root, meta, skip_root_check=False)
    assert r.returncode != 0
    assert "SOURCE_ROOT_MISMATCH" in (r.stdout + r.stderr)


def test_existing_output_dir_refused(fx):
    root, meta = fx
    out = os.path.join(root, "out")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "stale.json"), "w") as fh:
        fh.write("{}")
    cmd = [sys.executable, SCRIPT,
           "--counts-dir", meta["counts_dir"],
           "--producer-effects", os.path.join(root, "effects.csv"),
           "--producer-sample-identity", os.path.join(root, "identity.csv"),
           "--out-dir", out, "--skip-source-root-check"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode != 0
    assert "OUTPUT_EXISTS" in (r.stdout + r.stderr)
