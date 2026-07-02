from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def build_microglia_pvm_composition_features(h5ad_path: str | Path) -> pd.DataFrame:
    import anndata as ad

    adata = ad.read_h5ad(str(h5ad_path), backed="r")
    obs = adata.obs.copy()
    if "Donor ID" not in obs.columns:
        return pd.DataFrame()
    obs["Donor ID"] = obs["Donor ID"].astype(str)
    out = pd.DataFrame(index=sorted(obs["Donor ID"].unique()))
    out.index.name = "Donor ID"
    out["composition_total_cells"] = obs.groupby("Donor ID").size().reindex(out.index).fillna(0).astype(float)
    for col in ["Subclass", "Supertype", "Class", "Brain Region"]:
        if col not in obs.columns:
            continue
        counts = pd.crosstab(obs["Donor ID"], obs[col].astype(str))
        counts = counts.reindex(out.index).fillna(0)
        props = counts.div(counts.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
        for value in counts.columns:
            safe = str(value).replace(" ", "_").replace("/", "_").replace("-", "_").replace(".", "_")
            out[f"composition_count_{col}_{safe}"] = counts[value].astype(float)
            out[f"composition_prop_{col}_{safe}"] = props[value].astype(float)
    if "Continuous Pseudo-progression Score" in obs.columns:
        score = pd.to_numeric(obs["Continuous Pseudo-progression Score"], errors="coerce")
        tmp = pd.DataFrame({"Donor ID": obs["Donor ID"].to_numpy(), "score": score.to_numpy()})
        agg = tmp.groupby("Donor ID")["score"].agg(["mean", "median", "std", "min", "max"])
        agg = agg.reindex(out.index)
        for col in agg.columns:
            out[f"composition_pseudoprogression_{col}"] = agg[col].astype(float)
    return out.reset_index()
