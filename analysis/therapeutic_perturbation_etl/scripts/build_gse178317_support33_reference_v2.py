#!/usr/bin/env python3
"""DEVELOPMENT-only same-experiment matched-well support-qualified comparison."""
import argparse
import csv
import hashlib
import io
import json
import math
import statistics
from pathlib import Path

SOURCE_SHA256 = "fff45935c994d3fbce3293a9ddc53bce3acaa9507040e1ceb79ef19e8418a7e0"
SUPPORT_BLOB_SHA1 = "04cddbfbad075aff5db536858e84079d4292d4f0"
COLUMNS = ["target_gene", "n_cells", "n_lanes", "engagement_log2fc",
           "engagement_sd_across_lanes", "ref_log2fc", "ref_fdr"]

class Stop(ValueError):
    pass

def require(condition, why):
    if not condition:
        raise Stop(why)

def ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    result = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[i]] == values[order[j]]:
            j += 1
        for k in range(i, j):
            result[order[k]] = (i + j + 1) / 2.0
        i = j
    return result

def corr(x, y):
    require(len(x) == len(y) and len(x) >= 3, "insufficient paired values")
    a, b = statistics.mean(x), statistics.mean(y)
    xx = sum((v-a)**2 for v in x)
    yy = sum((v-b)**2 for v in y)
    require(xx > 0 and yy > 0, "constant observations")
    return sum((v-a)*(w-b) for v,w in zip(x,y)) / math.sqrt(xx*yy)

def compare(source_text, receipt, expected=(35,33,37,39)):
    require(receipt.get("schema") == "GSE178317_GUIDE_ASSIGNMENT_V2"
            and receipt.get("verdict") == "PASS_LANE_SUPPORT_ONLY"
            and receipt.get("prospective_confirmation_eligible") is False
            and receipt.get("guide_identity_independently_verified") is False,
            "receipt scope or schema drift")
    b = receipt.get("verdict_basis", {})
    require([b.get(k) for k in ("min_cells_per_usable_target", "min_paired_lanes",
                               "min_target_and_ntc_cells_per_lane")] == [40,3,10],
            "threshold drift")
    n = b.get("ntc_cells_by_lane", {})
    require(set(n) == {"L1","L2","L3","L4"} and all(type(x) is int and x >= 10 for x in n.values())
            and sum(n.values()) == receipt.get("ntc_cells")
            and set(b.get("ntc_supported_lanes",[])) == set(n),
            "NTC lane support drift")
    support = b.get("target_lane_support", {})
    require(len(support) == expected[3] and "NTC" not in support, "target census drift")
    eligible = set()
    for target, s in support.items():
        c = s.get("cells_by_lane", {})
        require(set(c) == set(n) and all(type(v) is int and v >= 0 for v in c.values())
                and sum(c.values()) == s.get("assigned_cells"), "bad cell census: "+target)
        paired = {lane for lane in n if c[lane] >= 10 and n[lane] >= 10}
        passed = s["assigned_cells"] >= 40 and len(paired) >= 3
        require(set(s.get("paired_lanes",[])) == paired
                and s.get("lane_support_sufficient") is passed,
                "bad paired-lane support: "+target)
        if passed:
            eligible.add(target)
    require(len(eligible) == expected[2] == b.get("usable_targets"),
            "supported target census drift")
    reader = csv.DictReader(io.StringIO(source_text))
    require(reader.fieldnames == COLUMNS, "comparison columns drift")
    rows = list(reader)
    ids = [r["target_gene"] for r in rows]
    require(len(rows) == expected[0] and len(set(ids)) == len(ids)
            and all(ids) and set(ids) <= set(support), "historical target join drift")
    for row in rows:
        try:
            values = [float(row[k]) for k in ("engagement_log2fc","ref_log2fc","ref_fdr")]
        except (ValueError, TypeError) as e:
            raise Stop("invalid effect or FDR") from e
        require(all(math.isfinite(v) for v in values) and 0 <= values[2] <= 1,
                "nonfinite effect or invalid FDR")
    good = [r for r in rows if r["target_gene"] in eligible]
    require(len(good) == expected[1], "support-qualified intersection count drift")
    own = [float(r["engagement_log2fc"]) for r in good]
    ref = [float(r["ref_log2fc"]) for r in good]
    require(statistics.median(ref) != 0, "median magnitude ratio undefined")
    hits = [r for r in good if float(r["ref_fdr"]) < 0.05]
    nonsig = [r for r in good if float(r["ref_fdr"]) >= 0.05]
    summary = {
        "schema":"GSE178317_SUPPORT33_REFERENCE_COMPARISON_V2",
        "scope":"DEVELOPMENT_SAME_EXPERIMENT_MATCHED_WELL_SUPPORT_ONLY",
        "n_historical_comparable":len(rows), "n_support_qualified":len(good),
        "excluded_targets":sorted(set(ids)-set(r["target_gene"] for r in good)),
        "qualified_targets":sorted(r["target_gene"] for r in good),
        "direction_agree":sum(x<0 and y<0 for x,y in zip(own,ref)),
        "pearson_r":corr(own,ref), "spearman_rho":corr(ranks(own),ranks(ref)),
        "median_ours":statistics.median(own),
        "median_reference":statistics.median(ref),
        "ratio_of_median_absolute_effects":abs(statistics.median(own))/abs(statistics.median(ref)),
        "reference_hits":len(hits), "reference_nonsignificant":len(nonsig),
        "hits_both_negative":sum(float(r["engagement_log2fc"])<0 and float(r["ref_log2fc"])<0 for r in hits),
        "hits_spearman":corr(ranks([float(r["engagement_log2fc"]) for r in hits]),
                             ranks([float(r["ref_log2fc"]) for r in hits])) if len(hits)>2 else None,
        "nonsignificant_median_abs_ours":statistics.median(abs(float(r["engagement_log2fc"])) for r in nonsig),
        "nonsignificant_median_abs_reference":statistics.median(abs(float(r["ref_log2fc"])) for r in nonsig),
        "nonsignificant_targets_are_known_biological_nulls":False,
        "independent_validation":False, "independent_biological_replication":False,
        "biological_uncertainty_estimable":False, "prospective_confirmation_authorized":False,
        "jepa_prediction_used":False, "training_authorized":False,
        "therapeutic_ranking":False}
    return good,summary

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--comparison-csv",required=True)
    ap.add_argument("--support-receipt",required=True)
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()
    out=Path(a.out_dir)
    require(not out.exists(),"refuse occupied output directory")
    src=Path(a.comparison_csv).read_bytes()
    sup=Path(a.support_receipt).read_bytes()
    source_hash=hashlib.sha256(src).hexdigest()
    # Exact Git blob pin for the already-reviewed 16 KB receipt, not a prefix.
    git_blob=hashlib.sha1(b"blob "+str(len(sup)).encode()+bytes([0])+sup).hexdigest()
    require(source_hash==SOURCE_SHA256 and git_blob==SUPPORT_BLOB_SHA1,
            "source digest or reviewed support-receipt blob drift")
    good, result=compare(src.decode("utf-8-sig"),json.loads(sup))
    result["source_csv_sha256"]=source_hash
    result["support_receipt_sha256"]=hashlib.sha256(sup).hexdigest()
    result["reviewed_parent_commit"]="4213dd73e9a017daf776e898c6c7c68edf345f7a"
    out.mkdir(parents=True,exist_ok=False)
    csv_out=out/"gse178317_support33_reference_v2.csv"
    with csv_out.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(good)
    result["output_csv_sha256"]=hashlib.sha256(csv_out.read_bytes()).hexdigest()
    (out/"gse178317_support33_reference_receipt_v2.json").write_text(
        json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+chr(10),encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
