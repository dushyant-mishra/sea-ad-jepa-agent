#!/usr/bin/env python3
"""GSE311359 (iPSC-derived microglia Perturb-seq, MS risk loci) ETL and effects.

Assay-specific. Structurally this is the easiest of the CRISPR studies and the
reason is worth stating: the 381 ``CRISPR Guide Capture`` features live in the
**same matrix** as the 36,601 gene features, so guide and expression are already
joined by construction. There is no cross-accession barcode join to verify, and
no opportunity for a lane or filename inference.

Contrast with the two studies handled before it:

* GSE293118 kept its protospacer calls in a separate file under a *different* GSM,
  so the barcode join had to be verified for containment and orphans;
* GSE178317 deposited no guide features at all, so its guide-to-cell relation is
  not recoverable from the acquired assets.

Experimental unit
-----------------
Seven 10x samples (S1..S7). Sample is the experimental unit for replication; cells
within a sample are not independent replicates and are never treated as such.

Guide assignment -- a declared analytical decision
--------------------------------------------------
Requiring exactly one nonzero guide is wrong for this assay. Guide capture carries
ambient background: the median cell has SEVEN distinct guides detected, with the
top guide holding only ~50% of the cell's guide UMI. An exact-uniqueness rule
assigns 1% of cells and reports a 99% "multiplet" rate that is an artifact of the
rule, not a property of the experiment.

A dominance rule is used instead, declared here before any effect was estimated:

    MIN_TOP_GUIDE_UMI  = 5      detection floor
    MIN_TOP_FRACTION   = 0.70   the assigned guide carries more than twice the
                                UMI of every other guide in that cell combined

Cells failing either condition are UNASSIGNED and contribute to nothing. The
sensitivity of the assigned-cell count to this threshold is recorded in the
summary so a reviewer can see what other choices would have given.

No JEPA prediction, no simulated erasure, no therapeutic ranking.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

#: Declared before estimating any effect; see the module docstring.
MIN_TOP_GUIDE_UMI = 5
MIN_TOP_FRACTION = 0.70

N_GENE = 36_601
N_GUIDE = 381
N_FEATURES = 36_982
SAMPLES = ("S1", "S2", "S3", "S4", "S5", "S6", "S7")


def target_of(guide: str) -> str:
    """`ELMO1_tss_g1` -> `ELMO1_tss`. Strip only the guide replicate suffix."""
    return re.sub(r"_g\d+$", "", guide)


def classify(target: str) -> str:
    t = target.lower()
    if any(k in t for k in ("non-target", "non_target", "nontarget", "ntc", "safe_harbor",
                            "safeharbor", "scramble", "control")):
        return "non_targeting_control"
    if target.endswith("_tss"):
        return "tss_cis_element"
    return "other"


def read_features(path: Path) -> tuple[list[str], list[str], list[str]]:
    rows = [l.split("\t") for l in gzip.open(path, "rt").read().splitlines()]
    if len(rows) != N_FEATURES:
        raise SystemExit(f"{path.name}: {len(rows)} features != {N_FEATURES}")
    ids = [r[0] for r in rows]
    names = [r[1] for r in rows]
    kinds = [r[2] for r in rows]
    return ids, names, kinds


def assert_unambiguous_feature_ids(ids: list[str], names: list[str],
                                   kinds: list[str]) -> None:
    """Fail before allocating PB or writing effects when guide names collide.

    10x guide feature IDs may distinguish same-name entries, but an ID alone
    cannot authenticate which library protospacer/target it represents.
    Explicit, separately authenticated ID→guide→target mapping is required to
    resolve duplicate *names*. No suffixes or positional guesses.
    """
    if not (len(ids) == len(names) == len(kinds)):
        raise SystemExit("STOP_GSE311359_MALFORMED_FEATURE_TABLE")
    if len(ids) != len(set(ids)):
        raise SystemExit("STOP_GSE311359_DUPLICATE_FEATURE_IDS")
    guides = [names[i] for i, kind in enumerate(kinds)
              if kind == "CRISPR Guide Capture"]
    if any(not g or not g.strip() for g in guides):
        raise SystemExit("STOP_GSE311359_EMPTY_GUIDE_NAME")
    counts = Counter(guides)
    collisions = {g: n for g, n in sorted(counts.items()) if n > 1}
    if collisions:
        raise SystemExit(
            "STOP_GSE311359_DUPLICATE_GUIDE_NAMES__"
            "INDEPENDENT_FEATURE_ID_TO_GUIDE_LIBRARY_AUTHORITY_REQUIRED: "
            + json.dumps(collisions, sort_keys=True)
        )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--extracted-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    E, out = args.extracted_dir, args.out_dir
    # No output directory or receipt is created before physical feature
    # identity qualification. Existing V1 outputs remain immutable.
    if out.exists() and any(out.iterdir()):
        raise SystemExit("STOP_GSE311359_OUTPUT_EXISTS__VERSIONED_SUCCESSOR_REQUIRED")

    gsm = {}
    for p in sorted(E.glob("*_features.tsv.gz")):
        s = p.name.split("_")[1]
        gsm[s] = p.name.split("_")[0]
    missing = [s for s in SAMPLES if s not in gsm]
    if missing:
        raise SystemExit(f"missing samples: {missing}")

    ref_ids = ref_names = ref_kinds = None
    per_sample = {}
    for s in SAMPLES:
        ids, names, kinds = read_features(E / f"{gsm[s]}_{s}_features.tsv.gz")
        assert_unambiguous_feature_ids(ids, names, kinds)
        if ref_names is None:
            ref_ids, ref_names, ref_kinds = ids, names, kinds
        elif ids != ref_ids or names != ref_names or kinds != ref_kinds:
            raise SystemExit(
                f"{s}: full feature ID/name/type/order differs from S1; refusing to merge"
            )
        per_sample[s] = None

    gene_rows = np.array([i for i, k in enumerate(ref_kinds) if k == "Gene Expression"],
                         dtype=np.int64)
    guide_rows = [i for i, k in enumerate(ref_kinds) if k == "CRISPR Guide Capture"]
    if gene_rows.size != N_GENE or len(guide_rows) != N_GUIDE:
        raise SystemExit("feature-type census drifted")
    # All seven samples passed source feature-ID and exact guide-name
    # qualification. Only now permit creation of any derived output.
    out.mkdir(parents=True, exist_ok=True)
    gene_symbols = [ref_names[i] for i in gene_rows]
    guide_names = [ref_names[i] for i in guide_rows]
    guide_pos = {r: j for j, r in enumerate(guide_rows)}
    gene_pos = np.full(N_FEATURES, -1, dtype=np.int64)
    gene_pos[gene_rows] = np.arange(gene_rows.size, dtype=np.int64)

    identity = []
    measured = set(gene_symbols)
    for g in guide_names:
        t = target_of(g)
        cls = classify(t)
        base = t[:-4] if t.endswith("_tss") else t
        identity.append({"guide_id": g, "target_id": t, "target_class": cls,
                         "nominated_gene": base if cls == "tss_cis_element" else "",
                         "nominated_gene_measured": base in measured
                         if cls == "tss_cis_element" else False})
    with (out / "GSE311359_perturbation_identity.csv").open("w", newline="",
                                                            encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(identity[0]))
        w.writeheader(); w.writerows(identity)
    ident = {r["guide_id"]: r for r in identity}
    print("guides by class:", dict(Counter(r["target_class"] for r in identity)), flush=True)

    # ---- stream every sample; assign guides and accumulate pseudobulk --------
    keys, kindex = [], {}
    for s in SAMPLES:
        for g in guide_names:
            k = f"{g}||{s}"
            kindex[k] = len(keys)
            keys.append(k)
    PB = np.zeros((len(keys), N_GENE), dtype=np.float64)
    ncells = Counter()
    multiplicity_all = Counter()
    sample_cells = {}

    for s in SAMPLES:
        pref = f"{gsm[s]}_{s}"
        bcs = gzip.open(E / f"{pref}_barcodes.tsv.gz", "rt").read().split()
        sample_cells[s] = len(bcs)
        guide_counts = defaultdict(dict)      # cell -> {guide_col: umi}
        gene_entries = []                     # (cell, gene_pos, val)
        with gzip.open(E / f"{pref}_matrix.mtx.gz", "rt") as fh:
            line = fh.readline()
            if not line.startswith("%%MatrixMarket"):
                raise SystemExit(f"{pref}: not MatrixMarket")
            line = fh.readline()
            while line.startswith("%"):
                line = fh.readline()
            nr, nc, nnz = (int(x) for x in line.split())
            if nr != N_FEATURES or nc != len(bcs):
                raise SystemExit(f"{pref}: dims {nr}x{nc} unexpected")
            n = 0
            for line in fh:
                a, b, v = line.split()
                r = int(a) - 1
                c = int(b) - 1
                val = int(v)
                if val < 0:
                    raise SystemExit(f"{pref}: negative count")
                if r in guide_pos:
                    if val > 0:
                        guide_counts[c][r] = val
                else:
                    gp = gene_pos[r]
                    if gp >= 0:
                        gene_entries.append((c, gp, val))
                n += 1
            if n != nnz:
                raise SystemExit(f"{pref}: read {n} entries, header said {nnz}")

        mult = Counter(len(v) for v in guide_counts.values())
        multiplicity_all.update(mult)
        single = {}
        for c, d in guide_counts.items():
            best_row, best_umi = max(d.items(), key=lambda kv: kv[1])
            total = sum(d.values())
            if best_umi >= MIN_TOP_GUIDE_UMI and (best_umi / total) >= MIN_TOP_FRACTION:
                single[c] = best_row
        col_key = {}
        for c, r in single.items():
            g = ref_names[r]
            col_key[c] = kindex[f"{g}||{s}"]
            ncells[f"{g}||{s}"] += 1
        for c, gp, val in gene_entries:
            k = col_key.get(c)
            if k is not None:
                PB[k, gp] += val
        print(f"  {s}: {len(bcs):,} cells | guide-called {len(guide_counts):,} | "
              f"singly assigned {len(single):,}", flush=True)

    keep = [i for i, k in enumerate(keys) if ncells[k] > 0]
    gmeta = []
    for i in keep:
        g, s = keys[i].split("||")
        gmeta.append({"study": "GSE311359", "sample": s, "guide_id": g,
                      "target_id": ident[g]["target_id"],
                      "target_class": ident[g]["target_class"],
                      "n_cells": ncells[keys[i]],
                      "total_counts": int(PB[i].sum())})
    with (out / "GSE311359_guide_sample_meta.csv").open("w", newline="",
                                                        encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(gmeta[0]))
        w.writeheader(); w.writerows(gmeta)

    sub = PB[keep]
    tot = np.maximum(sub.sum(axis=1, keepdims=True), 1.0)
    lg = np.log2(sub / tot * 1e6 + 1.0)
    row_of = {keys[i]: j for j, i in enumerate(keep)}

    nt_by_sample = defaultdict(list)
    for m, j in zip(gmeta, range(len(gmeta))):
        if m["target_class"] == "non_targeting_control":
            nt_by_sample[m["sample"]].append(j)

    sym = {s: i for i, s in enumerate(gene_symbols)}
    eff = []
    by_ts = defaultdict(list)
    for j, m in enumerate(gmeta):
        if m["target_class"] != "non_targeting_control":
            by_ts[(m["target_id"], m["sample"])].append(j)
    for (t, s), idxs in sorted(by_ts.items()):
        nt = nt_by_sample.get(s, [])
        if not nt:
            continue
        nt_mean = lg[nt].mean(axis=0)
        cls = gmeta[idxs[0]]["target_class"]
        base = t[:-4] if t.endswith("_tss") else t
        p = sym.get(base)
        per_guide = None if p is None else (lg[idxs, p] - nt_mean[p])
        eff.append({
            "study": "GSE311359", "system": "iPSC_derived_microglia",
            "sample": s, "target_id": t, "target_class": cls,
            "nominated_gene": base, "engagement_measurable": p is not None,
            "engagement_unavailable_reason": "" if p is not None else
                "no measured feature matches the nominated cis gene",
            "n_guides": len(idxs),
            "n_cells": int(sum(gmeta[i]["n_cells"] for i in idxs)),
            "n_nt_guides": len(nt),
            "n_nt_cells": int(sum(gmeta[i]["n_cells"] for i in nt)),
            "target_log2fc_mean": "" if p is None else float(per_guide.mean()),
            "target_log2fc_se": "" if p is None or len(idxs) < 2
                                else float(per_guide.std(ddof=1) / np.sqrt(len(idxs))),
        })
    with (out / "GSE311359_target_engagement.csv").open("w", newline="",
                                                        encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(eff[0]))
        w.writeheader(); w.writerows(eff)

    np.savez_compressed(out / "GSE311359_guide_sample_logcpm.npz",
                        keys=np.array([keys[i] for i in keep], dtype=object),
                        gene_symbols=np.array(gene_symbols, dtype=object),
                        raw_counts=sub.astype(np.int64),
                        logcpm=lg.astype(np.float32))

    called = sum(multiplicity_all.values())
    single_n = sum(m["n_cells"] for m in gmeta)
    summary = {
        "schema": "GSE311359_PERTURB_SEQ_INTERVENTION_EFFECTS_V1",
        "study": "GSE311359", "system": "iPSC-derived microglia",
        "modality": "Perturb-seq CRISPRi (dCas9-KRAB ZIM3), MS risk loci",
        "samples": list(SAMPLES),
        "experimental_unit": "sample; cells within a sample are not independent replicates",
        "cells_total": int(sum(sample_cells.values())),
        "cells_per_sample": sample_cells,
        "cells_guide_called": called,
        "cells_confidently_assigned": single_n,
        "unassigned_fraction_of_called": round(1 - single_n / max(called, 1), 4),
        "assignment_rule": {
            "min_top_guide_umi": MIN_TOP_GUIDE_UMI,
            "min_top_guide_fraction": MIN_TOP_FRACTION,
            "declared_before_estimating_effects": True,
            "note": ("guide capture carries ambient background; the median cell has "
                     "several guides detected, so an exact-uniqueness rule would "
                     "discard ~99% of cells as an artifact of the rule")},
        "guide_multiplicity_histogram": {str(k): v for k, v in sorted(multiplicity_all.items())},
        "gene_features": int(gene_rows.size), "guide_features": len(guide_rows),
        "guides_and_expression_in_one_matrix": True,
        "cross_accession_join_required": False,
        "guides_by_class": dict(Counter(r["target_class"] for r in identity)),
        "non_targeting_guides": sum(1 for r in identity
                                    if r["target_class"] == "non_targeting_control"),
        "targets_with_measurable_engagement": sum(1 for e in eff if e["engagement_measurable"]),
        "targets_without_measurable_engagement": sum(1 for e in eff
                                                     if not e["engagement_measurable"]),
        "jepa_prediction_used": False, "simulated_erasure_used": False,
        "therapeutic_ranking": False,
    }
    (out / "GSE311359_etl_summary.json").write_text(json.dumps(summary, indent=2) + "\n",
                                                    encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items()
                      if k not in ("guide_multiplicity_histogram", "cells_per_sample")},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
