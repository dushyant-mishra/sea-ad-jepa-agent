#!/usr/bin/env python3
"""Independent recomputation of GSE240609 coculture effects (audit P1-6).

Separate implementation, not a refactor of
`build_bulk_disease_context_effects_v2.py`. Every quantity is recomputed from
the four authenticated GEO per-sample count files.

What this study is, and what it therefore cannot support
--------------------------------------------------------
GSE240609 is a 2x2: neuron genotype (WT vs PSEN) crossed with microglia genotype
(APOE3 vs APOE3-Christchurch), with **one sample per design cell**. Four samples,
four cells, no replication anywhere. Differences between conditions are
computable. Biological uncertainty is **not estimable** -- there is no second
observation of any cell to estimate it from.

This reproducer therefore computes descriptive differences only. It emits no
standard error and no p-value, and it actively REQUIRES the producer to have
emitted none either: any row carrying a numeric `se`, or claiming
`uncertainty_estimable` true, or claiming n > 1 on either side, is recorded as a
disagreement. A standard error here would describe sequencing noise inside a
single library and would be read as biological replication that does not exist.

The measured material is CD11b-purified microglia recovered AFTER neuron
coculture, so a difference is a property of the coculture, not a cell-autonomous
microglial effect.

The headerless-file trap
------------------------
The four count files have **no header**. The first physical line is a real gene
row -- `A1BG`, with 71 counts in GSM7703564 and 63 in GSM7703571. A parser that
assumes a header consumes A1BG, yields 27,153 genes instead of 27,154, and
shifts the entire gene axis by one row, silently mislabelling every gene. A
prior pass made exactly this error.

This script asserts the gene count is 27,154 and that A1BG is present as a gene
row, and it runs a positive control that recomputes the contrast under the
header-consuming parse and REQUIRES it to disagree with the producer -- so that
agreement with the correct parse is informative rather than coincidental.

Declared before running: comparison tolerance is `max |delta| <= 1e-9` on every
compared cell. The tolerance is NOT widened if it fails; the stricter
round-consistency check runs instead -- `round(independent_value, 6)` must equal
the stored value on every row -- exactly as in
`independent_reproduce_gse254205_bulk_v1.py`.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

PSEUDOCOUNT = 1.0
TOLERANCE = 1e-9
STORED_DECIMALS = 6

# Declared before running. The first physical line is a gene row, not a header.
EXPECTED_GENES = 27154
EXPECTED_FIRST_GENE = "A1BG"

EXPECTED_MATERIAL = "CD11B_PURIFIED_MICROGLIA_AFTER_NEURON_COCULTURE"

# Byte roots frozen in the producer's public GEO sample authority. Re-verified
# here independently before any number is computed.
SOURCE_ROOTS = {
    "GSM7703564_45229_14048iN_APOEChurchMG_gene_counts.txt.gz":
        "f61d1ba45877aca810a962c59bb7e5fece5448c5bc23fe69b921dfc12d1615be",
    "GSM7703567_45232_14048PSEN_iN_APOECHurchMG_gene_counts.txt.gz":
        "b7d48bdf0987c888d1563d3ea6da4fcedd817b3ede3d1bcd49439ce4748058e3",
    "GSM7703569_45227_14048iN_APOE3MG_gene_counts.txt.gz":
        "46db9651d4792bf193eb470827daab4a05f22c11368c054ccb0fab105483ada9",
    "GSM7703571_45230_14048PSEN_iN_APOE3MG_gene_counts.txt.gz":
        "28cbe1b2b5d3dcdcf0085de59b351b41cc91c6cc8cfd6c78f03b6512c1ea9198",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_provenance(script_path):
    """Self-measured execution provenance. Never estimated: UNMEASURED if unknown."""
    import subprocess
    repo = Path(script_path).resolve().parent
    out = {"executing_script": Path(script_path).name,
           "executing_script_sha256": sha256_file(Path(script_path))}
    for key, args in (("git_commit", ["rev-parse", "HEAD"]),
                      ("git_status_porcelain", ["status", "--porcelain"])):
        try:
            r = subprocess.run(["git", "-C", str(repo)] + args,
                               capture_output=True, text=True, timeout=30)
            out[key] = r.stdout.strip() if r.returncode == 0 else "UNMEASURED"
        except Exception:
            out[key] = "UNMEASURED"
    status = out["git_status_porcelain"]
    out["worktree_clean_at_execution"] = (
        "UNMEASURED" if status == "UNMEASURED" else status == "")
    return out


def genotypes_from_filename(name: str) -> dict:
    """Derive the design cell from the GEO filename, independently of the producer.

    `GSM7703567_45232_14048PSEN_iN_APOECHurchMG_gene_counts.txt.gz`
      -> neuron PSEN, microglia APOE3ch.

    The deposited filenames spell Christchurch inconsistently ("APOEChurch" vs
    "APOECHurch"), so the match is case-insensitive. Derivation is checked
    against the producer's GEO-title-derived identity table afterwards; a
    disagreement is a stop, not a warning.
    """
    low = name.lower()
    neuron = "PSEN" if "psen" in low else "WT"
    if "church" in low:
        microglia = "APOE3ch"
    elif "apoe3mg" in low:
        microglia = "APOE3"
    else:
        raise SystemExit(f"STOP_UNRESOLVED_MICROGLIA_GENOTYPE:{name}")
    return {"neuron_genotype": neuron, "microglia_genotype": microglia}


def read_headerless_counts(path: Path, consume_first_line: bool = False):
    """Parse a headerless `gene<TAB>count` file.

    `consume_first_line=True` reproduces the header-consuming BUG on purpose and
    is used only by the positive control.
    """
    with gzip.open(path, "rt", newline="") as fh:
        lines = fh.read().splitlines()
    lines = [ln for ln in lines if ln.strip()]
    if consume_first_line:
        lines = lines[1:]
    genes, vals = [], []
    for ln in lines:
        sep = "\t" if "\t" in ln else ","
        parts = ln.split(sep)
        if len(parts) < 2:
            raise SystemExit(f"STOP_MALFORMED_ROW:{path.name}:{ln[:40]}")
        genes.append(parts[0])
        try:
            vals.append(float(parts[-1]))
        except ValueError:
            # A textual value here is how a header line announces itself in a
            # file declared to have none. Refuse rather than raise a traceback.
            raise SystemExit(
                f"STOP_UNPARSEABLE_COUNT:{path.name}:{parts[-1]!r} -- these files "
                f"are headerless and every line must be a gene row")
    arr = np.asarray(vals, dtype=np.float64)
    if not np.all(np.isfinite(arr)):
        raise SystemExit(f"STOP_NONFINITE_COUNT:{path.name}")
    if np.any(arr < 0):
        raise SystemExit(f"STOP_NEGATIVE_COUNT:{path.name}")
    if len(set(genes)) != len(genes):
        raise SystemExit(f"STOP_DUPLICATE_GENE_ID:{path.name}")
    if not np.all(arr == np.rint(arr)):
        raise SystemExit(f"STOP_NONINTEGER_RAW_COUNT:{path.name}")
    return genes, arr


def log_cpm(counts: np.ndarray) -> np.ndarray:
    lib = np.maximum(counts.sum(axis=1, keepdims=True), 1.0)
    return np.log2(counts / lib * 1e6 + PSEUDOCOUNT)


def load_all(counts_dir: Path, consume_first_line: bool = False):
    files = sorted(counts_dir.glob("*gene_counts.txt.gz"))
    if not files:
        raise SystemExit(f"STOP_NO_COUNT_FILES:{counts_dir}")
    genes0, mat, meta = None, [], []
    for p in files:
        genes, vals = read_headerless_counts(p, consume_first_line)
        if genes0 is None:
            genes0 = genes
            if not consume_first_line:
                if len(genes) != EXPECTED_GENES:
                    raise SystemExit(
                        f"STOP_GENE_COUNT_MISMATCH:expected {EXPECTED_GENES} "
                        f"got {len(genes)} in {p.name} -- the first line is a "
                        f"GENE ROW, not a header")
                if genes[0] != EXPECTED_FIRST_GENE:
                    raise SystemExit(
                        f"STOP_FIRST_GENE_NOT_{EXPECTED_FIRST_GENE}:{genes[0]}")
        elif genes != genes0:
            raise SystemExit(f"STOP_GENE_ORDER_DIFFERS:{p.name}")
        mat.append(vals)
        meta.append({"file": p.name, "gsm": p.name.split("_")[0],
                     **genotypes_from_filename(p.name)})
    return genes0, np.vstack(mat), meta, files


def contrast_rows(logcpm, meta):
    """Descriptive difference per neuron context. No SE: n=1 per design cell."""
    cells = {(m["neuron_genotype"], m["microglia_genotype"]): i
             for i, m in enumerate(meta)}
    if len(cells) != len(meta):
        raise SystemExit("STOP_DESIGN_CELL_COLLISION")
    if len(cells) != 4:
        raise SystemExit(f"STOP_EXPECTED_4_DESIGN_CELLS_GOT_{len(cells)}")
    out = {}
    for neuron in sorted({m["neuron_genotype"] for m in meta}):
        a = cells.get((neuron, "APOE3ch"))
        b = cells.get((neuron, "APOE3"))
        if a is None or b is None:
            raise SystemExit(f"STOP_MISSING_GENOTYPE_DESIGN_CELL:{neuron}")
        out[f"APOE3ch_vs_APOE3_microglia_in_{neuron}_neurons"] = logcpm[a] - logcpm[b]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--counts-dir", type=Path, required=True)
    ap.add_argument("--producer-effects", type=Path, required=True)
    ap.add_argument("--producer-sample-identity", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--skip-source-root-check", action="store_true",
                    help="fixtures only; never used for the recorded run")
    a = ap.parse_args()

    if a.out_dir.exists() and any(a.out_dir.iterdir()):
        raise SystemExit("STOP_INDEPENDENT_GSE240609_OUTPUT_EXISTS")

    genes, counts, meta, files = load_all(a.counts_dir)
    digests = {p.name: sha256_file(p) for p in files}
    if not a.skip_source_root_check:
        if set(digests) != set(SOURCE_ROOTS):
            raise SystemExit(f"STOP_UNEXPECTED_FILE_SET:{sorted(digests)}")
        for n, d in digests.items():
            if d != SOURCE_ROOTS[n]:
                raise SystemExit(f"STOP_SOURCE_ROOT_MISMATCH:{n}")
    digests["producer_effects"] = sha256_file(a.producer_effects)
    digests["producer_sample_identity"] = sha256_file(a.producer_sample_identity)

    a.out_dir.mkdir(parents=True, exist_ok=True)

    n_genes = len(genes)
    lg = log_cpm(counts)
    detected = counts.sum(axis=0) > 0
    libs = {m["gsm"]: int(t) for m, t in zip(meta, counts.sum(axis=1))}

    print(f"  samples {counts.shape[0]} | genes parsed {n_genes} "
          f"(expected {EXPECTED_GENES}) | first gene {genes[0]!r}")
    print(f"  library sizes: {libs}")
    print(f"  detected anywhere {int(detected.sum())} | assayed-undetected "
          f"{int((~detected).sum())}")
    for m in meta:
        print(f"    {m['gsm']}  neuron={m['neuron_genotype']:4s} "
              f"microglia={m['microglia_genotype']}")

    mine = contrast_rows(lg, meta)

    # ------------------------------------------------------------------ controls
    # POSITIVE CONTROL: the correct parse must agree with the producer, and it is
    # asserted below. It is stated explicitly so that the rejections that follow
    # are trustworthy -- a suite where nothing can pass proves nothing.
    #
    # 1. Sign control: exchanging numerator and denominator must negate exactly.
    cells = {(m["neuron_genotype"], m["microglia_genotype"]): i
             for i, m in enumerate(meta)}
    rev = lg[cells[("WT", "APOE3")]] - lg[cells[("WT", "APOE3ch")]]
    fwd = mine["APOE3ch_vs_APOE3_microglia_in_WT_neurons"]
    sign_ok = bool(np.max(np.abs(rev + fwd)) <= TOLERANCE)
    print(f"\n  sign control (reversed contrast negates exactly): {sign_ok}")
    if not sign_ok:
        raise SystemExit("STOP_COMPARATOR_CANNOT_DETECT_REVERSED_CONTRAST")

    # 2. A1BG control: recompute under the header-consuming parse and require the
    #    answer to DIFFER. If it did not, the comparator could not tell a correct
    #    parse from the off-by-one that shifts every gene label.
    bug_genes, bug_counts, bug_meta, _ = load_all(a.counts_dir, consume_first_line=True)
    bug_lg = log_cpm(bug_counts)
    bug = contrast_rows(bug_lg, bug_meta)
    a1bg_in_correct = genes[0] == EXPECTED_FIRST_GENE
    a1bg_dropped_by_bug = EXPECTED_FIRST_GENE not in bug_genes
    n = min(len(genes), len(bug_genes))
    shift_gap = float(np.max(np.abs(
        mine["APOE3ch_vs_APOE3_microglia_in_WT_neurons"][:n]
        - bug["APOE3ch_vs_APOE3_microglia_in_WT_neurons"][:n])))
    header_bug_detectable = (len(bug_genes) == EXPECTED_GENES - 1
                             and a1bg_dropped_by_bug and shift_gap > TOLERANCE)
    print(f"  A1BG control: genes correct={n_genes} header-consuming={len(bug_genes)} "
          f"| A1BG retained={a1bg_in_correct} dropped-by-bug={a1bg_dropped_by_bug}")
    print(f"    max|correct - header-consuming| log2fc = {shift_gap:.6e} -> "
          f"detectable={header_bug_detectable}")
    if not header_bug_detectable:
        raise SystemExit("STOP_COMPARATOR_CANNOT_DETECT_HEADER_CONSUMING_PARSE")

    # ------------------------------------------- compare against producer output
    gi = {g: i for i, g in enumerate(genes)}
    seen = {k: 0 for k in mine}
    dmax = {k: 0.0 for k in mine}
    round_exact = {k: 0 for k in mine}
    round_violations = []
    missing_gene = unknown_contrast = 0
    undetected_emitted = 0
    material_mismatch = 0
    neuron_label_mismatch = 0
    # Fabricated-replication guard: any numeric SE, any n>1, any claim that
    # uncertainty is estimable, is a scientific disagreement, not a rounding one.
    fabricated_se = 0
    fabricated_n = 0
    fabricated_estimable = 0
    fabricated_sample = []

    with a.producer_effects.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            name = row["contrast"]
            if name not in mine:
                unknown_contrast += 1
                continue
            g = row["gene_id"]
            if g not in gi:
                missing_gene += 1
                continue
            j = gi[g]
            if not detected[j]:
                undetected_emitted += 1
            if row.get("material") != EXPECTED_MATERIAL:
                material_mismatch += 1
            if not name.endswith(f"_in_{row.get('neuron_genotype')}_neurons"):
                neuron_label_mismatch += 1

            se_raw = (row.get("se") or "").strip()
            if se_raw not in ("", "NA"):
                fabricated_se += 1
                if len(fabricated_sample) < 8:
                    fabricated_sample.append({"contrast": name, "gene": g,
                                              "field": "se", "value": se_raw})
            try:
                if int(row.get("n_numerator", 1)) != 1 or int(row.get("n_denominator", 1)) != 1:
                    fabricated_n += 1
                    if len(fabricated_sample) < 8:
                        fabricated_sample.append(
                            {"contrast": name, "gene": g, "field": "n",
                             "value": [row.get("n_numerator"), row.get("n_denominator")]})
            except ValueError:
                fabricated_n += 1
            if str(row.get("uncertainty_estimable", "False")).strip().lower() != "false":
                fabricated_estimable += 1
                if len(fabricated_sample) < 8:
                    fabricated_sample.append(
                        {"contrast": name, "gene": g, "field": "uncertainty_estimable",
                         "value": row.get("uncertainty_estimable")})

            seen[name] += 1
            stored = float(row["log2fc"])
            my = float(mine[name][j])
            dmax[name] = max(dmax[name], abs(stored - my))
            # Fixed declared precision, not a character count after the ".":
            # "-3.9e-05" would yield 5 and manufacture a false violation.
            if float(round(my, STORED_DECIMALS)) == stored:
                round_exact[name] += 1
            elif len(round_violations) < 8:
                round_violations.append({"contrast": name, "gene": g,
                                         "stored": row["log2fc"], "mine": repr(my)})

    # ------------------------------------- compare the producer sample identity
    id_rows = 0
    identity_mismatch = []
    my_by_gsm = {m["gsm"]: m for m in meta}
    with a.producer_sample_identity.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            id_rows += 1
            gsm = row["gsm"]
            if gsm not in my_by_gsm:
                identity_mismatch.append({"gsm": gsm, "reason": "absent_from_source"})
                continue
            m = my_by_gsm[gsm]
            if (row["neuron_genotype"] != m["neuron_genotype"]
                    or row["microglia_genotype"] != m["microglia_genotype"]):
                identity_mismatch.append({
                    "gsm": gsm, "reason": "genotype_disagreement",
                    "stored": [row["neuron_genotype"], row["microglia_genotype"]],
                    "mine_from_filename": [m["neuron_genotype"], m["microglia_genotype"]]})
            if row.get("file_sha256") != digests.get(row.get("file")):
                identity_mismatch.append({"gsm": gsm, "reason": "file_sha256_disagreement"})
            if str(row.get("biological_uncertainty_estimable", "")).strip().lower() != "false":
                identity_mismatch.append({"gsm": gsm, "reason": "claims_uncertainty_estimable"})
    identity_ok = (not identity_mismatch) and id_rows == len(meta)

    # ----------------------------------------------------------------- verdicts
    full_precision_ok = max(dmax.values()) <= TOLERANCE
    rounding_fully_explains = (not round_violations
                               and all(round_exact[k] == seen[k] for k in seen))
    no_fabricated_replication = (fabricated_se == 0 and fabricated_n == 0
                                 and fabricated_estimable == 0)
    structural_ok = (missing_gene == 0 and unknown_contrast == 0
                     and undetected_emitted == 0 and material_mismatch == 0
                     and neuron_label_mismatch == 0 and identity_ok
                     and no_fabricated_replication
                     and n_genes == EXPECTED_GENES
                     and all(v > 0 for v in seen.values()))
    ok = structural_ok and (full_precision_ok or rounding_fully_explains)

    receipt = {
        "schema": "GSE240609_BULK_INDEPENDENT_REPRODUCTION_V1",
        "verdict": ("IMPLEMENTATION_REPRODUCED_TO_FULL_PRECISION"
                    if (structural_ok and full_precision_ok)
                    else "IMPLEMENTATION_REPRODUCED_TO_STORED_PRECISION" if ok
                    else "DISAGREE"),
        "audit_item": "P1-6 INDEPENDENT_PHYSICAL_RECOMPUTATION",
        "study": "GSE240609",
        "design": ("2x2 neuron genotype (WT/PSEN) x microglia genotype "
                   "(APOE3/APOE3ch), ONE sample per design cell"),
        "replicates_per_design_cell": 1,
        "uncertainty_estimable": False,
        "uncertainty_note": (
            "one sample per design cell: differences are descriptive only. No "
            "standard error and no p-value is computed here, and the producer is "
            "REQUIRED to have emitted none. A within-sample SE would describe "
            "sequencing noise in a single library and would read as biological "
            "replication that does not exist."),
        "material": EXPECTED_MATERIAL,
        "interpretation_limit": (
            "RNA is from CD11b-purified microglia recovered AFTER neuron "
            "coculture, so a difference is a property of the coculture and not a "
            "cell-autonomous microglial effect."),
        "declared_tolerance": TOLERANCE,
        "declared_tolerance_met_at_full_precision": bool(full_precision_ok),
        "rounding_fully_explains_every_delta": bool(rounding_fully_explains),
        "stored_decimals": STORED_DECIMALS,
        "precision_limitation": (
            "the producer writes log2fc rounded to 6 decimals, so the declared "
            "1e-9 tolerance is NOT testable against its CSV. The tolerance was "
            "not widened. Every delta is instead required to be exactly explained "
            "by rounding: round(independent_value, 6) must equal the stored value "
            "on every row."),
        "controls": {
            "sign_control_reversed_contrast_negates": sign_ok,
            "genes_parsed": n_genes,
            "expected_genes": EXPECTED_GENES,
            "gene_count_assertion_held": n_genes == EXPECTED_GENES,
            "first_physical_line_is_gene_row": a1bg_in_correct,
            "first_gene": genes[0],
            "header_consuming_parse_gene_count": len(bug_genes),
            "header_consuming_parse_drops_A1BG": bool(a1bg_dropped_by_bug),
            "max_abs_gap_correct_minus_header_consuming_lfc": shift_gap,
            "header_bug_detectable_by_this_comparator": bool(header_bug_detectable),
            "control_note": (
                "the four count files are headerless; the first physical line is "
                "the A1BG gene row (71 counts in GSM7703564, 63 in GSM7703571). "
                "Consuming it as a header yields 27,153 genes and shifts every "
                "gene label by one. The comparator is shown to detect that before "
                "its agreement is believed."),
        },
        "fabricated_replication_guard": {
            "rows_with_numeric_se": fabricated_se,
            "rows_with_n_greater_than_one": fabricated_n,
            "rows_claiming_uncertainty_estimable": fabricated_estimable,
            "sample": fabricated_sample,
            "passed": bool(no_fabricated_replication),
        },
        "samples": int(counts.shape[0]),
        "library_sizes": libs,
        "genes_detected_anywhere": int(detected.sum()),
        "genes_assayed_undetected": int((~detected).sum()),
        "design_cells": {f"{m['neuron_genotype']}|{m['microglia_genotype']}": m["gsm"]
                         for m in meta},
        "rows_compared_per_contrast": seen,
        "max_abs_delta_log2fc": {k: float(v) for k, v in dmax.items()},
        "rows_where_round_to_stored_decimals_matches_exactly": round_exact,
        "rounding_violations_sample": round_violations,
        "structural": {
            "genes_in_producer_absent_from_source": missing_gene,
            "unknown_contrasts_in_producer_output": unknown_contrast,
            "rows_emitted_for_undetected_genes": undetected_emitted,
            "material_label_mismatches": material_mismatch,
            "neuron_label_mismatches": neuron_label_mismatch,
            "sample_identity_rows": id_rows,
            "sample_identity_mismatches": identity_mismatch,
            "sample_identity_reproduced": identity_ok,
        },
        "not_a_v1_v2_parity_check": (
            "V1==V2 shows V2 changed no number; it does not show either was "
            "right. This recomputes from the four authenticated GEO count files."),
        "implementation": ("python, independently authored; derives the design "
                           "cell from the GEO filename, recomputes library sizes, "
                           "log2(CPM+1), per-context differences and detection"),
        "identity_derivation_note": (
            "the design cell is derived here from the GEO filename and then "
            "required to agree with the producer's GEO-title-derived identity "
            "table; a disagreement is a stop, not a warning."),
        "depth_susceptibility_screen_note": (
            "an earlier depth check measured the worst within-contrast library "
            "ratio at 1.2509x, so this study is NOT susceptible to the depth "
            "artifact that invalidated GSE301119. That is a SUSCEPTIBILITY "
            "SCREEN, not scientific effect qualification. Nothing here qualifies "
            "these effects biologically."),
        "biological_qualification": "NOT_QUALIFIED_THIS_IS_IMPLEMENTATION_REPRODUCTION_ONLY",
        "execution_provenance": git_provenance(__file__),
        "input_sha256": digests,
        "source_byte_roots_verified": not a.skip_source_root_check,
        "jepa_prediction_used": False,
        "training_authorized": False,
        "therapeutic_ranking": False,
    }

    rp = a.out_dir / "GSE240609_BULK_INDEPENDENT_REPRODUCTION_V1.json"
    rp.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    print("\n=== comparison against the producer's emitted effects ===")
    for k in sorted(dmax):
        print(f"  {k:48s} rows {seen[k]:>7,}  max|d log2fc| {dmax[k]:.6e}")
    print(f"  genes in producer absent from source : {missing_gene}")
    print(f"  unknown contrasts                    : {unknown_contrast}")
    print(f"  rows emitted for undetected genes    : {undetected_emitted}")
    print(f"  material / neuron label mismatches   : {material_mismatch} / "
          f"{neuron_label_mismatch}")
    print(f"  fabricated replication (se/n/flag)   : {fabricated_se} / "
          f"{fabricated_n} / {fabricated_estimable}")
    print(f"  sample identity reproduced           : {identity_ok} ({id_rows} rows)")
    print(f"  declared 1e-9 met at full precision  : {full_precision_ok}")
    print(f"  rounding explains EVERY delta        : {rounding_fully_explains}")
    for k in sorted(seen):
        print(f"    {k:48s} exact-on-round {round_exact[k]:,}/{seen[k]:,}")
    if round_violations:
        print("  violations (first few):")
        for v in round_violations:
            print("   ", v)
    print(f"\n=== VERDICT: {receipt['verdict']} ===")
    print(f"wrote {rp}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
