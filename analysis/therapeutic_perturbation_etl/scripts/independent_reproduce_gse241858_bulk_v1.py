#!/usr/bin/env python3
"""Independent recomputation of GSE241858 genotype-by-cytokine effects (audit P1-6).

Separate implementation, not a refactor of
`build_bulk_disease_context_effects_v2.py`. Every quantity below is recomputed
from the two authenticated GEO count matrices; nothing is read back from the
producer except the numbers being checked.

Recomputed here:

  * per-sample library sizes from the raw count columns;
  * log2(CPM + 1) per sample;
  * the clone-level mean profile for every (clone, treatment) cell;
  * each contrast's clone-level mean difference;
  * the clone-level standard error, from the CLONE units, not the replicates;
  * detected-anywhere status per gene, per arm.

The experimental unit, and why this is the whole point
-----------------------------------------------------
GSE241858 edited two independent iPSC **clones** per genotype and then took
several replicates inside each clone. Those within-clone replicates are the same
cell line measured again; they are not independent biology. The declared method
therefore averages within (clone, treatment) FIRST and treats the clone as the
unit, so there are two units per genotype, not six.

A reproducer that quietly treated all replicates as independent would inflate
the apparent replication threefold and shrink every standard error. Because the
baseline arm happens to be balanced (3 replicates in every clone), that error is
INVISIBLE in the baseline point estimate -- the two means coincide exactly. It is
visible in two places, and this script checks both:

  * the baseline standard error (2 clone units vs 6 flat replicates);
  * the cytokine LPS-in-CTRL point estimate, where clone CTRL_A contributes one
    LPS replicate and clone CTRL_B contributes two, so clone-averaging and
    replicate-flattening genuinely disagree.

Both are run as controls BEFORE the comparison is believed. If flattening the
clone structure did not change the answer, this comparator could not tell a
clone-aware producer from a clone-blind one, and its agreement would mean
nothing.

Declared before running, per the qualification contract: comparison tolerance is
`max |delta| <= 1e-9` on every compared cell. Both sides are IEEE double derived
from the same integers, so anything larger is a real disagreement. The tolerance
is NOT widened if it fails; instead the stricter round-consistency check runs --
`round(independent_value, stored_decimals)` must equal the stored value on every
row -- exactly as in `independent_reproduce_gse254205_bulk_v1.py`.

Float summation order follows the source column order, which is the only
canonical choice; deliberately permuting it would inject last-ulp noise that is
not a scientific disagreement.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

PSEUDOCOUNT = 1.0
TOLERANCE = 1e-9
# The producer writes log2fc and se_clone_level rounded to this many decimals.
STORED_DECIMALS = 6

# Byte roots of the two authenticated GEO matrices, frozen by PR77 and re-checked
# by the producer. Verified here independently before any number is computed.
SOURCE_ROOTS = {
    "baseline": "2c7811e25e6283dbb9f0149e71c7dea55e00d9a20ed279d4b7bbe5f8bd049496",
    "cytokine": "50f1e487226a491009a62a0f362e20b41871118a964ebeebf3f28a97e3dd2a03",
}

SAMPLE_RE = re.compile(r"^(CTRL|R47H)_([AB])_(\d+)(?:_(UNTR|IFN|LPS))?$")

# (contrast name, arm, numerator predicate, denominator predicate)
CONTRAST_SPEC = [
    ("R47H_vs_CTRL_baseline", "baseline",
     lambda u: u["genotype"] == "R47H",
     lambda u: u["genotype"] == "CTRL"),
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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_sample_id(sample: str) -> dict:
    """CTRL_A_1 / R47H_B_2_IFN -> genotype, clone, replicate, treatment."""
    m = SAMPLE_RE.match(sample)
    if not m:
        raise SystemExit(f"STOP_UNPARSED_SAMPLE_ID:{sample}")
    geno, clone_letter, rep, treat = m.groups()
    return {"sample_id": sample, "genotype": geno,
            "clone": f"{geno}_{clone_letter}", "replicate": int(rep),
            "treatment": treat or "BASELINE"}


def read_count_matrix(path: Path):
    """Return (sample_ids, entrez_ids, symbols, counts[samples x genes])."""
    with gzip.open(path, "rt", newline="") as fh:
        header = fh.readline().rstrip("\r\n")
        sep = "\t" if "\t" in header else ","
        cols = header.split(sep)
        if cols[0] != "ENTREZID" or cols[1] != "SYMBOL":
            raise SystemExit(f"STOP_UNEXPECTED_HEADER:{path.name}:{cols[:2]}")
        entrez, symbols, rows = [], [], []
        for line in fh:
            line = line.rstrip("\r\n")
            if not line:
                continue
            parts = line.split(sep)
            if len(parts) != len(cols):
                raise SystemExit(f"STOP_RAGGED_ROW:{path.name}:{parts[0]}")
            entrez.append(parts[0])
            symbols.append(parts[1])
            rows.append([float(x) for x in parts[2:]])
    counts = np.asarray(rows, dtype=np.float64).T          # samples x genes
    if not np.all(np.isfinite(counts)):
        raise SystemExit(f"STOP_NONFINITE_COUNT:{path.name}")
    if np.any(counts < 0):
        raise SystemExit(f"STOP_NEGATIVE_COUNT:{path.name}")
    if len(set(entrez)) != len(entrez):
        raise SystemExit(f"STOP_DUPLICATE_GENE_ID:{path.name}")
    return cols[2:], entrez, symbols, counts


def log_cpm(counts: np.ndarray) -> np.ndarray:
    """log2(CPM + 1), library size floored at 1 so an empty library cannot divide by zero."""
    lib = np.maximum(counts.sum(axis=1, keepdims=True), 1.0)
    return np.log2(counts / lib * 1e6 + PSEUDOCOUNT)


def clone_units(logcpm: np.ndarray, meta: list[dict]):
    """Average within (clone, treatment). Returns (unit_matrix, unit_meta)."""
    keys = [(m["clone"], m["treatment"]) for m in meta]
    uniq = sorted(set(keys))
    rows, umeta = [], []
    for clone, treat in uniq:
        idx = [i for i, k in enumerate(keys) if k == (clone, treat)]
        rows.append(logcpm[idx].mean(axis=0))
        umeta.append({"clone": clone, "treatment": treat,
                      "genotype": "R47H" if clone.startswith("R47H") else "CTRL",
                      "n_within_clone_replicates": len(idx)})
    return np.vstack(rows), umeta


def difference(unit_mat, umeta, num_pred, den_pred):
    """Clone-level mean difference and clone-level SE. SE is NaN below 2 units."""
    ni = [i for i, u in enumerate(umeta) if num_pred(u)]
    di = [i for i, u in enumerate(umeta) if den_pred(u)]
    if not ni or not di:
        return None
    delta = unit_mat[ni].mean(axis=0) - unit_mat[di].mean(axis=0)
    if len(ni) > 1 and len(di) > 1:
        se = np.sqrt(unit_mat[ni].var(axis=0, ddof=1) / len(ni)
                     + unit_mat[di].var(axis=0, ddof=1) / len(di))
    else:
        se = np.full(delta.shape, np.nan)
    return delta, se, len(ni), len(di)


def flat_difference(logcpm, meta, num_pred, den_pred):
    """The clone-BLIND version: every replicate treated as an independent unit.

    Used only as a control. This is the estimator the design forbids; the point
    is to show it gives a different answer, so that agreement with the
    clone-aware one is informative.
    """
    ni = [i for i, m in enumerate(meta) if num_pred(m)]
    di = [i for i, m in enumerate(meta) if den_pred(m)]
    if not ni or not di:
        return None
    delta = logcpm[ni].mean(axis=0) - logcpm[di].mean(axis=0)
    se = np.sqrt(logcpm[ni].var(axis=0, ddof=1) / len(ni)
                 + logcpm[di].var(axis=0, ddof=1) / len(di))
    return delta, se, len(ni), len(di)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline-counts", type=Path, required=True)
    ap.add_argument("--cytokine-counts", type=Path, required=True)
    ap.add_argument("--producer-effects", type=Path, required=True)
    ap.add_argument("--producer-sample-identity", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--skip-source-root-check", action="store_true",
                    help="fixtures only; never used for the recorded run")
    a = ap.parse_args()

    if a.out_dir.exists() and any(a.out_dir.iterdir()):
        raise SystemExit("STOP_INDEPENDENT_GSE241858_OUTPUT_EXISTS")

    inputs = {"baseline_counts": a.baseline_counts,
              "cytokine_counts": a.cytokine_counts,
              "producer_effects": a.producer_effects,
              "producer_sample_identity": a.producer_sample_identity}
    digests = {k: sha256_file(v) for k, v in inputs.items()}
    if not a.skip_source_root_check:
        for arm, key in (("baseline", "baseline_counts"), ("cytokine", "cytokine_counts")):
            if digests[key] != SOURCE_ROOTS[arm]:
                raise SystemExit(f"STOP_GSE241858_{arm.upper()}_SOURCE_ROOT_MISMATCH")

    a.out_dir.mkdir(parents=True, exist_ok=True)

    arms = {}
    integrality = {}
    for arm, path in (("baseline", a.baseline_counts), ("cytokine", a.cytokine_counts)):
        samples, entrez, symbols, counts = read_count_matrix(path)
        meta = [parse_sample_id(s) for s in samples]
        integrality[arm] = bool(np.all(counts == np.rint(counts)))
        if not integrality[arm]:
            raise SystemExit(f"STOP_NONINTEGER_RAW_COUNT:{arm}")
        lg = log_cpm(counts)
        detected = counts.sum(axis=0) > 0
        unit_mat, umeta = clone_units(lg, meta)
        arms[arm] = {"samples": samples, "entrez": entrez, "symbols": symbols,
                     "counts": counts, "meta": meta, "logcpm": lg,
                     "detected": detected, "unit_mat": unit_mat, "umeta": umeta}
        print(f"  [{arm}] samples {len(samples)} | genes {len(entrez)} | "
              f"detected {int(detected.sum())} | clone-treatment units {len(umeta)}")
        print(f"  [{arm}] units: " + ", ".join(
            f"{u['clone']}/{u['treatment']}:n={u['n_within_clone_replicates']}"
            for u in umeta))

    # ------------------------------------------------------------------ controls
    # 1. Sign control: a reversed contrast must come out exactly negated.
    base = arms["baseline"]
    fwd = difference(base["unit_mat"], base["umeta"],
                     lambda u: u["genotype"] == "R47H", lambda u: u["genotype"] == "CTRL")
    rev = difference(base["unit_mat"], base["umeta"],
                     lambda u: u["genotype"] == "CTRL", lambda u: u["genotype"] == "R47H")
    sign_ok = bool(np.max(np.abs(fwd[0] + rev[0])) <= TOLERANCE)
    print(f"\n  sign control (reversed contrast negates exactly): {sign_ok}")
    if not sign_ok:
        raise SystemExit("STOP_COMPARATOR_CANNOT_DETECT_REVERSED_CONTRAST")

    # 2. Clone-awareness control, point estimate. Uses the UNBALANCED cytokine
    #    LPS-in-CTRL cell (CTRL_A contributes 1 LPS replicate, CTRL_B 2), where
    #    clone-averaging and replicate-flattening genuinely differ.
    cyt = arms["cytokine"]
    lps_num = lambda u: u["treatment"] == "LPS" and u["genotype"] == "CTRL"
    lps_den = lambda u: u["treatment"] == "UNTR" and u["genotype"] == "CTRL"
    clone_lps = difference(cyt["unit_mat"], cyt["umeta"], lps_num, lps_den)
    flat_lps = flat_difference(cyt["logcpm"], cyt["meta"], lps_num, lps_den)
    det_c = cyt["detected"]
    lfc_gap = float(np.max(np.abs(clone_lps[0][det_c] - flat_lps[0][det_c])))
    clone_blind_distinguishable = lfc_gap > TOLERANCE
    print(f"  clone-awareness control (LPS_vs_UNTR_in_CTRL, unbalanced cell):")
    print(f"    clone units {clone_lps[2]}v{clone_lps[3]} | "
          f"flat replicates {flat_lps[2]}v{flat_lps[3]}")
    print(f"    max|clone-aware - clone-blind| log2fc = {lfc_gap:.6e} -> "
          f"distinguishable={clone_blind_distinguishable}")
    if not clone_blind_distinguishable:
        raise SystemExit("STOP_COMPARATOR_CANNOT_DETECT_CLONE_BLINDNESS")

    # 3. Clone-awareness control, standard error. The BALANCED baseline arm hides
    #    clone-blindness in the point estimate; it shows up in the SE.
    flat_base = flat_difference(base["logcpm"], base["meta"],
                                lambda m: m["genotype"] == "R47H",
                                lambda m: m["genotype"] == "CTRL")
    det_b = base["detected"]
    base_lfc_gap = float(np.max(np.abs(fwd[0][det_b] - flat_base[0][det_b])))
    base_se_gap = float(np.max(np.abs(fwd[1][det_b] - flat_base[1][det_b])))
    print(f"  balanced-arm control (R47H_vs_CTRL_baseline):")
    print(f"    max|d log2fc| clone-aware vs flat = {base_lfc_gap:.6e} "
          f"(expected ~0: balanced design hides it)")
    print(f"    max|d SE|     clone-aware vs flat = {base_se_gap:.6e} "
          f"(SE is where clone-blindness shows)")
    se_control_ok = base_se_gap > TOLERANCE
    if not se_control_ok:
        raise SystemExit("STOP_SE_CONTROL_CANNOT_DISTINGUISH_CLONE_UNITS")

    # ------------------------------------------------- independent recomputation
    mine = {}
    unit_counts = {}
    for name, arm, num_pred, den_pred in CONTRAST_SPEC:
        d = arms[arm]
        got = difference(d["unit_mat"], d["umeta"], num_pred, den_pred)
        if got is None:
            raise SystemExit(f"STOP_CONTRAST_HAS_EMPTY_GROUP:{name}")
        mine[name] = {"arm": arm, "lfc": got[0], "se": got[1],
                      "n_num": got[2], "n_den": got[3]}
        unit_counts[name] = {"n_numerator_clone_units": got[2],
                             "n_denominator_clone_units": got[3]}

    # gene index per arm; the two arms carry the same ENTREZ namespace but are
    # indexed separately because detection is computed within arm.
    gidx = {arm: {g: i for i, g in enumerate(arms[arm]["entrez"])} for arm in arms}

    # ------------------------------------------- compare against producer output
    seen = {n: 0 for n in mine}
    dmax = {n: 0.0 for n in mine}
    semax = {n: 0.0 for n in mine}
    round_exact_lfc = {n: 0 for n in mine}
    round_exact_se = {n: 0 for n in mine}
    se_rows = {n: 0 for n in mine}
    round_violations = []
    missing_gene = unknown_contrast = arm_mismatch = 0
    unit_count_mismatch = []
    symbol_mismatch = 0
    undetected_emitted = 0

    with a.producer_effects.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            name = row["contrast"]
            if name not in mine:
                unknown_contrast += 1
                continue
            arm = mine[name]["arm"]
            if row["arm"] != arm:
                arm_mismatch += 1
                continue
            g = row["gene_id"]
            if g not in gidx[arm]:
                missing_gene += 1
                continue
            j = gidx[arm][g]
            if not arms[arm]["detected"][j]:
                undetected_emitted += 1
            if row.get("gene_symbol") != arms[arm]["symbols"][j]:
                symbol_mismatch += 1
            if (int(row["n_numerator_clone_units"]) != mine[name]["n_num"]
                    or int(row["n_denominator_clone_units"]) != mine[name]["n_den"]):
                if len(unit_count_mismatch) < 8:
                    unit_count_mismatch.append(
                        {"contrast": name, "gene": g,
                         "stored": [row["n_numerator_clone_units"],
                                    row["n_denominator_clone_units"]],
                         "mine": [mine[name]["n_num"], mine[name]["n_den"]]})
            seen[name] += 1

            stored_lfc = float(row["log2fc"])
            my_lfc = float(mine[name]["lfc"][j])
            dmax[name] = max(dmax[name], abs(stored_lfc - my_lfc))
            # Fixed declared precision, not a count of characters after the ".":
            # "-3.9e-05" would yield 5 and manufacture a false violation.
            if float(round(my_lfc, STORED_DECIMALS)) == stored_lfc:
                round_exact_lfc[name] += 1
            elif len(round_violations) < 8:
                round_violations.append({"field": "log2fc", "contrast": name,
                                         "gene": g, "stored": row["log2fc"],
                                         "mine": repr(my_lfc)})

            raw_se = row.get("se_clone_level")
            my_se = float(mine[name]["se"][j])
            if raw_se not in (None, "", "NA"):
                se_rows[name] += 1
                stored_se = float(raw_se)
                semax[name] = max(semax[name], abs(stored_se - my_se))
                if float(round(my_se, STORED_DECIMALS)) == stored_se:
                    round_exact_se[name] += 1
                elif len(round_violations) < 8:
                    round_violations.append({"field": "se_clone_level",
                                             "contrast": name, "gene": g,
                                             "stored": raw_se, "mine": repr(my_se)})
            elif np.isfinite(my_se):
                # producer withheld an SE that IS estimable -- a real disagreement
                if len(round_violations) < 8:
                    round_violations.append({"field": "se_clone_level",
                                             "contrast": name, "gene": g,
                                             "stored": "<blank>", "mine": repr(my_se)})

    # ------------------------------------- compare the producer sample identity
    id_rows = 0
    lib_mismatch = []
    my_lib = {}
    for arm in arms:
        for m, tot in zip(arms[arm]["meta"], arms[arm]["counts"].sum(axis=1)):
            my_lib[(arm, m["sample_id"])] = int(tot)
    with a.producer_sample_identity.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            id_rows += 1
            key = (row["arm"], row["sample_id"])
            if key not in my_lib:
                lib_mismatch.append({"sample": key, "reason": "absent_from_source"})
            elif int(row["total_counts"]) != my_lib[key]:
                lib_mismatch.append({"sample": key, "stored": row["total_counts"],
                                     "mine": my_lib[key]})
    identity_ok = (not lib_mismatch) and id_rows == len(my_lib)

    # ----------------------------------------------------------------- verdicts
    full_precision_ok = (max(dmax.values()) <= TOLERANCE
                         and max(semax.values()) <= TOLERANCE)
    rounding_fully_explains = (
        not round_violations
        and all(round_exact_lfc[n] == seen[n] for n in seen)
        and all(round_exact_se[n] == se_rows[n] for n in seen))
    structural_ok = (missing_gene == 0 and unknown_contrast == 0
                     and arm_mismatch == 0 and symbol_mismatch == 0
                     and undetected_emitted == 0 and not unit_count_mismatch
                     and identity_ok and all(v > 0 for v in seen.values()))
    ok = structural_ok and (full_precision_ok or rounding_fully_explains)

    receipt = {
        "schema": "GSE241858_BULK_INDEPENDENT_REPRODUCTION_V1",
        "verdict": ("IMPLEMENTATION_REPRODUCED_TO_FULL_PRECISION"
                    if (structural_ok and full_precision_ok)
                    else "IMPLEMENTATION_REPRODUCED_TO_STORED_PRECISION" if ok
                    else "DISAGREE"),
        "audit_item": "P1-6 INDEPENDENT_PHYSICAL_RECOMPUTATION",
        "study": "GSE241858",
        "design": ("TREM2 R47H vs CTRL iPSC-derived microglia, 2 independent "
                   "clones per genotype, baseline arm plus IFN/LPS cytokine arm"),
        "experimental_unit": "iPSC clone",
        "clone_aware": True,
        "declared_tolerance": TOLERANCE,
        "declared_tolerance_met_at_full_precision": bool(full_precision_ok),
        "rounding_fully_explains_every_delta": bool(rounding_fully_explains),
        "stored_decimals": STORED_DECIMALS,
        "precision_limitation": (
            "the producer writes log2fc and se_clone_level rounded to 6 decimals, "
            "so the declared 1e-9 tolerance is NOT testable against its CSV. The "
            "tolerance was not widened. Every delta is instead required to be "
            "exactly explained by rounding: round(independent_value, 6) must "
            "equal the stored value on every row. Verifying at 1e-9 requires the "
            "producer to emit full precision."),
        "controls": {
            "sign_control_reversed_contrast_negates": sign_ok,
            "clone_blindness_detectable_in_point_estimate": bool(clone_blind_distinguishable),
            "max_abs_gap_clone_aware_minus_clone_blind_lfc_LPS_in_CTRL": lfc_gap,
            "balanced_arm_lfc_gap_clone_aware_minus_flat": base_lfc_gap,
            "balanced_arm_se_gap_clone_aware_minus_flat": base_se_gap,
            "se_control_distinguishes_clone_units": bool(se_control_ok),
            "control_note": (
                "the baseline arm is balanced at 3 replicates per clone, so a "
                "clone-blind point estimate coincides with the clone-aware one "
                "there; clone-blindness is detectable in the baseline STANDARD "
                "ERROR and in the UNBALANCED cytokine LPS-in-CTRL point estimate, "
                "both of which are checked before the comparison is believed"),
        },
        "rows_compared_per_contrast": seen,
        "max_abs_delta_log2fc": {k: float(v) for k, v in dmax.items()},
        "max_abs_delta_se_clone_level": {k: float(v) for k, v in semax.items()},
        "rows_with_se_compared": se_rows,
        "rows_where_round_to_stored_decimals_matches_exactly_log2fc": round_exact_lfc,
        "rows_where_round_to_stored_decimals_matches_exactly_se": round_exact_se,
        "rounding_violations_sample": round_violations,
        "clone_units_per_contrast": unit_counts,
        "clone_unit_count_mismatches_sample": unit_count_mismatch,
        "per_arm": {
            arm: {
                "samples": len(arms[arm]["samples"]),
                "genes_parsed": len(arms[arm]["entrez"]),
                "genes_detected": int(arms[arm]["detected"].sum()),
                "genes_assayed_undetected": int((~arms[arm]["detected"]).sum()),
                "clone_treatment_units": len(arms[arm]["umeta"]),
                "raw_counts_all_integral": integrality[arm],
                "unit_replicate_counts": {
                    f"{u['clone']}/{u['treatment']}": u["n_within_clone_replicates"]
                    for u in arms[arm]["umeta"]},
                "library_sizes": {m["sample_id"]: int(t) for m, t in
                                  zip(arms[arm]["meta"],
                                      arms[arm]["counts"].sum(axis=1))},
            } for arm in arms},
        "structural": {
            "genes_in_producer_absent_from_source": missing_gene,
            "unknown_contrasts_in_producer_output": unknown_contrast,
            "arm_label_mismatches": arm_mismatch,
            "gene_symbol_mismatches": symbol_mismatch,
            "rows_emitted_for_undetected_genes": undetected_emitted,
            "sample_identity_rows": id_rows,
            "sample_identity_library_mismatches": lib_mismatch,
            "sample_identity_reproduced": identity_ok,
        },
        "not_a_v1_v2_parity_check": (
            "V1==V2 shows V2 changed no number; it does not show either was "
            "right. This recomputes from the authenticated GEO count matrices."),
        "implementation": ("python, independently authored; recomputes library "
                           "sizes, log2(CPM+1), clone-level unit means, contrast "
                           "differences, clone-level SE and per-arm detection "
                           "from the two GEO count matrices"),
        "float_order_note": ("summation follows source column order, the only "
                             "canonical choice; permuting it would inject "
                             "last-ulp noise that is not a disagreement"),
        "depth_susceptibility_screen_note": (
            "an earlier depth check measured the worst within-contrast library "
            "ratio at 1.370x, so this study is NOT susceptible to the depth "
            "artifact that invalidated GSE301119. That is a SUSCEPTIBILITY "
            "SCREEN, not scientific effect qualification. Nothing here qualifies "
            "these effects biologically."),
        "biological_qualification": "NOT_QUALIFIED_THIS_IS_IMPLEMENTATION_REPRODUCTION_ONLY",
        "input_sha256": digests,
        "source_byte_roots_verified": not a.skip_source_root_check,
        "jepa_prediction_used": False,
        "training_authorized": False,
        "therapeutic_ranking": False,
    }

    rp = a.out_dir / "GSE241858_BULK_INDEPENDENT_REPRODUCTION_V1.json"
    rp.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    print("\n=== comparison against the producer's emitted effects ===")
    for k in sorted(dmax):
        print(f"  {k:26s} rows {seen[k]:>7,}  max|d log2fc| {dmax[k]:.6e}  "
              f"max|d se| {semax[k]:.6e}")
    print(f"  genes in producer absent from source : {missing_gene}")
    print(f"  unknown contrasts / arm mismatches   : {unknown_contrast} / {arm_mismatch}")
    print(f"  gene symbol mismatches               : {symbol_mismatch}")
    print(f"  rows emitted for undetected genes    : {undetected_emitted}")
    print(f"  sample identity reproduced           : {identity_ok} ({id_rows} rows)")
    print(f"  declared 1e-9 met at full precision  : {full_precision_ok}")
    print(f"  rounding explains EVERY delta        : {rounding_fully_explains}")
    for k in sorted(seen):
        print(f"    {k:26s} lfc exact-on-round {round_exact_lfc[k]:,}/{seen[k]:,}"
              f"  se exact-on-round {round_exact_se[k]:,}/{se_rows[k]:,}")
    if round_violations:
        print("  violations (first few):")
        for v in round_violations:
            print("   ", v)
    print(f"\n=== VERDICT: {receipt['verdict']} ===")
    print(f"wrote {rp}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
