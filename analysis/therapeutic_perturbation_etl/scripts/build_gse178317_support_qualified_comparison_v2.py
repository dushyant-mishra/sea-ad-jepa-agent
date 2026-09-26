#!/usr/bin/env python3
"""GSE178317 support-qualified SAME-EXPERIMENT DEVELOPMENT comparison V2.

Recalculate from the immutable historical 35-target table and reviewed matched-
lane support receipt. Neither file is overwritten. No biological SE, independent
replication, prospective confirmation, or JEPA model outcome is established.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
import statistics
from pathlib import Path

SOURCE_COMPARISON_SHA256 = "fff45935c994d3fbce3293a9ddc53bce3acaa9507040e1ceb79ef19e8418a7e0"
SOURCE_SUPPORT_GIT_BLOB_SHA1 = "04cddbfbad075aff5db536858e84079d4292d4f0"
SOURCE_COMMIT = "67981c8ef6e158d865470e70bca81cbe289be3dd"
LANES = ("L1", "L2", "L3", "L4")
COLUMNS = ("target_gene", "n_cells", "n_lanes", "engagement_log2fc",
           "engagement_sd_across_lanes", "ref_log2fc", "ref_fdr")

class QualificationError(ValueError):
    pass

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()

def load_inputs(comparison: Path, support: Path):
    c, s = comparison.read_bytes(), support.read_bytes()
    if digest(c) != SOURCE_COMPARISON_SHA256:
        raise QualificationError("STOP: historical comparison CSV SHA256 changed")
    if git_blob_sha(s) != SOURCE_SUPPORT_GIT_BLOB_SHA1:
        raise QualificationError("STOP: reviewed support receipt Git blob changed")
    try:
        text = c.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise QualificationError("STOP: historical CSV schema changed")
        rows = list(reader)
        receipt = json.loads(s)
    except (UnicodeDecodeError, json.JSONDecodeError, csv.Error) as exc:
        raise QualificationError("STOP: malformed source data") from exc
    return rows, receipt, digest(c), digest(s)

def numeric(row, key):
    try:
        v = float(row[key])
    except (KeyError, ValueError, TypeError) as exc:
        raise QualificationError("STOP: invalid numeric field " + key) from exc
    if not math.isfinite(v):
        raise QualificationError("STOP: nonfinite " + key)
    return v

def rank(values):
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    out = [0.0] * len(values)
    k = 0
    while k < len(indexed):
        j = k + 1
        while j < len(indexed) and indexed[j][1] == indexed[k][1]:
            j += 1
        avg_rank = (k + 1 + j) / 2
        for idx, _ in indexed[k:j]:
            out[idx] = avg_rank
        k = j
    return out

def pearson(x, y):
    if len(x) != len(y) or len(x) < 3:
        raise QualificationError("STOP: insufficient correlation support")
    xm, ym = statistics.mean(x), statistics.mean(y)
    dx = [z-xm for z in x]
    dy = [z-ym for z in y]
    vx, vy = sum(z*z for z in dx), sum(z*z for z in dy)
    if vx <= 0 or vy <= 0:
        raise QualificationError("STOP: degenerate correlation")
    return sum(a*b for a,b in zip(dx,dy)) / math.sqrt(vx * vy)

def calculate(rows, support):
    if support.get("schema") != "GSE178317_GUIDE_ASSIGNMENT_V2":
        raise QualificationError("STOP: wrong support receipt schema")
    if support.get("verdict") != "PASS_LANE_SUPPORT_ONLY" or support.get("prospective_confirmation_eligible") is not False:
        raise QualificationError("STOP: wrong qualification scope")
    basis = support["verdict_basis"]
    if (basis.get("min_cells_per_usable_target"), basis.get("min_paired_lanes"),
        basis.get("min_target_and_ntc_cells_per_lane"), basis.get("min_usable_targets")) != (40,3,10,30):
        raise QualificationError("STOP: support rule changed")
    if set(basis["ntc_cells_by_lane"]) != set(LANES) or not all(
        type(basis["ntc_cells_by_lane"][l]) is int and basis["ntc_cells_by_lane"][l] >= 10 for l in LANES
    ):
        raise QualificationError("STOP: NTC lane census invalid")
    all_support = basis["target_lane_support"]
    if len(all_support) != 39 or len(rows) != 35:
        raise QualificationError("STOP: historical target universe changed")
    admissible = set()
    for target, entry in all_support.items():
        counts = entry["cells_by_lane"]
        if set(counts) != set(LANES) or not all(type(v) is int and v >= 0 for v in counts.values()):
            raise QualificationError("STOP: malformed lane cell census")
        if sum(counts.values()) != entry["assigned_cells"]:
            raise QualificationError("STOP: assigned-cell census mismatch")
        paired = [lane for lane in LANES if counts[lane] >= 10 and basis["ntc_cells_by_lane"][lane] >= 10]
        if paired != entry["paired_lanes"]:
            raise QualificationError("STOP: paired lane inconsistency")
        qualifies = entry["assigned_cells"] >= 40 and len(paired) >= 3
        if qualifies != entry["lane_support_sufficient"]:
            raise QualificationError("STOP: support flag inconsistency")
        if qualifies:
            admissible.add(target)
    if len(admissible) != basis["usable_targets"] or len(admissible) != 37:
        raise QualificationError("STOP: global support count differs")
    # Preflight the *whole* target keyset before any row-level geometry check;
    # a duplicate must never be disguised by the first row's mismatched census.
    names = [r.get("target_gene") for r in rows]
    if not all(names) or len(set(names)) != len(names):
        raise QualificationError("STOP: empty or duplicate comparison target")
    if not set(names).issubset(all_support):
        raise QualificationError("STOP: unknown comparison target")
    seen = set()
    qualified, excluded = [], []
    for row in rows:
        target = row["target_gene"]
        if not target or target in seen or target not in all_support:
            raise QualificationError("STOP: duplicate/unknown target")
        seen.add(target)
        entry = all_support[target]
        expected_cells = sum(entry["cells_by_lane"][l] for l in entry["paired_lanes"])
        if numeric(row, "n_cells") != expected_cells or numeric(row, "n_lanes") != len(entry["paired_lanes"]):
            raise QualificationError("STOP: comparison row contradicts matched-lane receipt")
        numeric(row, "engagement_log2fc")
        numeric(row, "ref_log2fc")
        numeric(row, "ref_fdr")
        if target in admissible:
            qualified.append(row)
        else:
            excluded.append(target)
    if len(qualified) != 33 or set(excluded) != {"AARS", "LSM6"}:
        raise QualificationError("STOP: not the expected matched-well 33-target universe")
    qualified.sort(key=lambda r: r["target_gene"])
    our = [numeric(r,"engagement_log2fc") for r in qualified]
    ref = [numeric(r,"ref_log2fc") for r in qualified]
    hits = [r for r in qualified if numeric(r,"ref_fdr") < .05]
    nonsig = [r for r in qualified if numeric(r,"ref_fdr") >= .05]
    med_ours, med_ref = statistics.median(our), statistics.median(ref)
    if med_ref == 0:
        raise QualificationError("STOP: zero reference median")
    result = {
        "schema": "GSE178317_SUPPORT_QUALIFIED_REFERENCE_COMPARISON_V2",
        "scope": "DEVELOPMENT_SAME_EXPERIMENT_MATCHED_WELL_SUPPORT_ONLY",
        "targets_historical": len(rows), "targets_support_qualified": len(qualified),
        "excluded_nonqualified_targets": sorted(excluded),
        "direction_agreement": {
            "both_negative": sum(a < 0 and b < 0 for a,b in zip(our,ref)),
            "denominator": len(qualified),
        },
        "pearson_r": pearson(our, ref), "spearman_rho": pearson(rank(our),rank(ref)),
        "median_log2fc_ours": med_ours, "median_log2fc_reference": med_ref,
        "magnitude_ratio_of_medians": med_ours/med_ref,
        "reference_significant_fdr_lt_0_05": len(hits),
        "reference_nonsignificant_fdr_ge_0_05": len(nonsig),
        "nonsignificant_median_abs_log2fc_ours": statistics.median(
            abs(numeric(r,"engagement_log2fc")) for r in nonsig),
        "nonsignificant_median_abs_log2fc_reference": statistics.median(
            abs(numeric(r,"ref_log2fc")) for r in nonsig),
        "biological_uncertainty_estimable": False,
        "independent_validation": False,
        "independent_biological_replication": False,
        "prospective_confirmation_eligible": False,
        "jepa_prediction_used": False,
        "therapeutic_ranking": False,
    }
    return qualified, result

def run(comparison: Path, support: Path, out_dir: Path):
    if out_dir.exists():
        raise QualificationError("STOP: refuse occupied output directory")
    rows, receipt, comparison_sha, support_sha = load_inputs(comparison, support)
    qualified, summary = calculate(rows, receipt)
    out_dir.mkdir(parents=True, exist_ok=False)
    csv_path = out_dir/"gse178317_support_qualified_reference_comparison_v2.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(qualified)
    summary["provenance"] = {
        "source_commit": SOURCE_COMMIT,
        "historical_comparison_csv_sha256": comparison_sha,
        "matched_well_support_receipt_sha256": support_sha,
        "matched_well_support_receipt_git_blob_sha1": SOURCE_SUPPORT_GIT_BLOB_SHA1,
        "output_csv_sha256": digest(csv_path.read_bytes()),
    }
    receipt_path=out_dir/"gse178317_support_qualified_reference_comparison_receipt_v2.json"
    receipt_path.write_text(json.dumps(summary, indent=2, allow_nan=False)+"\n",encoding="utf-8")
    if summary["direction_agreement"]["denominator"] != 33:
        raise QualificationError("STOP: postcondition failed")
    return summary

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison",required=True,type=Path)
    parser.add_argument("--support-receipt",required=True,type=Path)
    parser.add_argument("--out-dir",required=True,type=Path)
    a=parser.parse_args()
    try:
        result=run(a.comparison,a.support_receipt,a.out_dir)
    except (QualificationError, OSError, KeyError, TypeError) as exc:
        parser.exit(2,str(exc)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
