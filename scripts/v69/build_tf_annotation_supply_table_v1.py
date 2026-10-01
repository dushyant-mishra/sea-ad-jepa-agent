#!/usr/bin/env python3
"""V69 control C1 denominator: per-TF motif-annotation supply.

A TF that has many motifs annotated to it gets many chances to be called enriched.
Any claim that a TF is "strong" must therefore be made WITHIN its annotation-supply
stratum, not against the whole TF list. This producer builds that denominator from
the pinned motif-to-TF annotation table alone -- it reads no expression, no
accessibility, no network and no outcome, so it can be built before any network
exists and cannot be contaminated by one.

Supply is counted at three strictness levels, because "annotated to" is not one
thing in the cisTarget annotation table:
  direct        -- the motif is directly annotated to this TF
  orthology     -- inferred from an orthologous gene in another species
  similarity    -- inferred from a similar motif
A TF strong only at the loosest level is a materially weaker claim than one strong
at the direct level, and the strata keep that difference visible.

Strata are assigned by QUANTILE of direct supply among TFs, so the stratification
is defined by the resource's own distribution rather than by a hand-picked cut.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

N_STRATA = 5  # quintiles; CONVENTION, declared before any network exists


def utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def ordered_digest(items) -> str:
    h = hashlib.sha256()
    for i, s in enumerate(items):
        h.update(str(i).encode()); h.update(b"\x1f")
        h.update(str(s).encode()); h.update(b"\x1e")
    return h.hexdigest()


class FailClosed(Exception):
    def __init__(self, status, **detail):
        super().__init__(status)
        self.status = status
        self.detail = detail


def classify_evidence(df: pd.DataFrame) -> pd.Series:
    """Direct / orthology / similarity, from the annotation table's own columns."""
    desc = df["description"].astype(str).str.lower()
    has_ortho = df["orthologous_gene_name"].astype(str).str.lower().ne("none") & \
        df["orthologous_gene_name"].notna()
    has_sim = df["similar_motif_id"].astype(str).str.lower().ne("none") & \
        df["similar_motif_id"].notna()
    out = pd.Series("direct", index=df.index, dtype=object)
    out[has_sim] = "similarity"
    out[has_ortho] = "orthology"
    out[has_ortho & has_sim] = "orthology_and_similarity"
    # the table states direct annotation explicitly for the strongest class
    out[desc.str.contains("gene is directly annotated", na=False)] = "direct"
    return out


def build(annotation_path: Path, out_dir: Path) -> dict:
    required = ["motif_id", "gene_name", "description",
                "orthologous_gene_name", "similar_motif_id"]
    df = pd.read_csv(annotation_path, sep="\t", low_memory=False)
    # The cisTarget annotation table writes its header as a '#'-prefixed comment
    # line, so the first column arrives named '#motif_id'. Strip the marker rather
    # than skipping the header, which would silently lose every column name.
    df = df.rename(columns={c: c.lstrip("#") for c in df.columns})
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise FailClosed("FAIL__ANNOTATION_TABLE_COLUMNS_ABSENT",
                         missing_columns=missing, observed_columns=list(df.columns))
    if df.empty:
        raise FailClosed("FAIL__ANNOTATION_TABLE_EMPTY")

    df["evidence_class"] = classify_evidence(df)
    df["gene_name"] = df["gene_name"].astype(str)

    g = df.groupby("gene_name")
    supply = pd.DataFrame({
        "n_annotation_rows": g.size(),
        "n_distinct_motifs_any_evidence": g["motif_id"].nunique(),
    })
    for cls in ("direct", "orthology", "similarity", "orthology_and_similarity"):
        sub = df[df["evidence_class"] == cls]
        supply["n_distinct_motifs_" + cls] = sub.groupby("gene_name")["motif_id"].nunique()
    supply = supply.fillna(0).astype(int).reset_index().rename(
        columns={"gene_name": "tf_gene_symbol"})
    supply = supply.sort_values("tf_gene_symbol").reset_index(drop=True)

    # Quantile strata on DIRECT supply. Ties are kept in the same stratum, so the
    # stratum count can be smaller than N_STRATA when the distribution is lumpy;
    # that is reported rather than forced.
    direct = supply["n_distinct_motifs_direct"].to_numpy()
    ranks = pd.Series(direct).rank(method="average", pct=True)
    supply["annotation_supply_stratum"] = np.minimum(
        (ranks * N_STRATA).apply(np.ceil).astype(int), N_STRATA)
    supply.loc[direct == 0, "annotation_supply_stratum"] = 0  # no direct evidence at all

    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "V69_TF_MOTIF_ANNOTATION_SUPPLY_V1.csv"
    supply.to_csv(p, index=False)

    strat_counts = supply["annotation_supply_stratum"].value_counts().sort_index()
    if supply["annotation_supply_stratum"].nunique() < 2:
        raise FailClosed("FAIL__ANNOTATION_SUPPLY_HAS_NO_USABLE_STRATIFICATION",
                         n_strata_observed=int(supply["annotation_supply_stratum"].nunique()))

    return {
        "schema": "V69_TF_MOTIF_ANNOTATION_SUPPLY_V1",
        "built_utc": utcnow(),
        "purpose": ("Denominator for control C1. A TF may be called strong only if it "
                    "remains in the top tier WITHIN its annotation-supply stratum."),
        "annotation_table_path": str(annotation_path),
        "annotation_table_sha256": sha256_file(annotation_path),
        "n_annotation_rows": int(len(df)),
        "n_distinct_motifs_in_table": int(df["motif_id"].nunique()),
        "n_tfs": int(len(supply)),
        "evidence_class_counts": {k: int(v) for k, v in
                                  df["evidence_class"].value_counts().items()},
        "direct_supply_distribution": {
            "min": int(direct.min()), "median": float(np.median(direct)),
            "mean": float(direct.mean()), "max": int(direct.max()),
            "n_tfs_with_zero_direct": int((direct == 0).sum()),
        },
        "n_strata_requested": N_STRATA,
        "stratum_sizes": {str(k): int(v) for k, v in strat_counts.items()},
        "stratum_definition": ("Quantile of the number of DISTINCT motifs directly "
                               "annotated to the TF. Stratum 0 holds TFs with no direct "
                               "annotation at all. CONVENTION: quintiles, declared before "
                               "any network exists; not externally calibrated."),
        "reads_no_expression_accessibility_network_or_outcome": True,
        "output_path": str(p),
        "output_sha256": sha256_file(p),
        "ordered_tf_digest": ordered_digest(supply["tf_gene_symbol"].tolist()),
        "status": "PASS__ANNOTATION_SUPPLY_TABLE_BUILT",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--annotation", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--receipt", required=True)
    a = ap.parse_args(argv)
    try:
        r = build(Path(a.annotation), Path(a.out_dir))
    except FailClosed as e:
        r = {"schema": "V69_TF_MOTIF_ANNOTATION_SUPPLY_V1",
             "status": e.status, **e.detail}
    Path(a.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(a.receipt).write_text(json.dumps(r, indent=2) + "\n")
    print(json.dumps(r, indent=2)[:4000])
    return 0 if str(r["status"]).startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
