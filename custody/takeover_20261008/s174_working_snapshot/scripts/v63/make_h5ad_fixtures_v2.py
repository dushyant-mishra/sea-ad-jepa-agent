#!/usr/bin/env python3
"""Synthetic .h5ad fixtures for qualifying h5ad_schema_probe_v2.

Fixtures A and B are reproduced from make_fixtures.py v1.0 (preserved as
make_fixtures_v1_0_as_received.py) with the SAME generator, SAME seed and SAME
call order, so the v1.0 receipts remain directly comparable to v2 receipts on
identical bytes. Fixture C is new.

  A  exact barcode namespace, log-normalised X plus an integer layers/counts,
     one donor with ZERO microglia (D01), one planted donor-label MISMATCH.
  B  DIFFERENT barcode conventions (RNA "D00_000123" vs ATAC "D00#000123"),
     integer counts in X, no planted mismatch. This is the fixture v1.0 got
     wrong: it reported 0 paired microglia against a planted truth of 35.
  C  NEW. Realistic 10x naming with the sample qualifier on OPPOSITE SIDES of
     the barcode:
         RNA   NABEC_1234_AAACGAAAGCAGAGCT-1
         ATAC  AAACGAAAGCAGAGCT-1_NABEC_1234
     Exact overlap is zero, but the composite (sample, raw_barcode) diagnostic
     should recover the pairing -- and must still NOT be authoritative by
     default. C also uses the spelled-out label "Microglia" rather than "MG",
     and deliberately reuses the SAME raw barcodes across two samples, which is
     the collision hazard that makes prefix-stripping alone unsafe.

Every fixture writes its planted truth so a test can assert recovery rather than
merely assert that the probe ran.
"""
from __future__ import annotations

import json
import sys

import anndata as ad
import numpy as np
import pandas as pd
import scipy.sparse as sp

rng = np.random.default_rng(1)


def build(prefix, n_per_donor, mg_per_donor, raw_in_x, atac_sep="_", mismatch=True,
          frac_shared=0.9, outdir="."):
    """Verbatim generator from v1.0, with an outdir parameter added."""
    donors = [f"D{i:02d}" for i in range(len(n_per_donor))]
    cohorts = ["NABEC" if i % 2 == 0 else "HBCC" for i in range(len(donors))]
    obs = []
    for d, c, n, m in zip(donors, cohorts, n_per_donor, mg_per_donor):
        ct = ["MG"] * m + list(rng.choice(["ExN", "InN", "Oligo", "Astro", "OPC", "VC"], n - m))
        for j, t in enumerate(ct):
            obs.append((f"{d}_{j:06d}", t, d, c))
    obs = pd.DataFrame(obs, columns=["bc", "cell_type", "sample_id", "cohort"]).set_index("bc")
    obs["age"] = rng.integers(15, 100, len(obs))
    obs["sex"] = rng.choice(["M", "F"], len(obs))
    obs["PMI"] = rng.uniform(5, 40, len(obs))
    obs["seq_batch"] = "b1"
    for c in ["cell_type", "sample_id", "cohort", "sex"]:
        obs[c] = obs[c].astype("category")
    counts = sp.random(len(obs), 300, density=0.05, format="csr", random_state=1,
                       data_rvs=lambda k: rng.integers(1, 20, k)).astype(np.float32)
    rna = ad.AnnData(X=counts.copy(), obs=obs.copy(),
                     var=pd.DataFrame(index=[f"GENE{i}" for i in range(300)]))
    if not raw_in_x:
        lib = np.asarray(counts.sum(1)).ravel()
        lib[lib == 0] = 1
        norm = sp.diags(1e6 / lib) @ counts
        norm.data = np.log1p(norm.data)
        rna.X = norm.astype(np.float32)
        rna.layers["counts"] = counts
    keep = rng.random(len(obs)) < frac_shared
    aobs = obs[keep].copy()
    if atac_sep != "_":
        aobs.index = [i.replace("_", atac_sep) for i in aobs.index]
    if mismatch and atac_sep == "_":
        aobs["sample_id"] = aobs["sample_id"].astype(str)
        aobs.iloc[0, aobs.columns.get_loc("sample_id")] = "WRONG"
        aobs["sample_id"] = aobs["sample_id"].astype("category")
    peaks = sp.random(len(aobs), 500, density=0.03, format="csr", random_state=2,
                      data_rvs=lambda k: rng.integers(1, 4, k)).astype(np.float32)
    atac = ad.AnnData(X=peaks, obs=aobs,
                      var=pd.DataFrame(index=[f"chr1:{i*1000}-{i*1000+500}" for i in range(500)]))
    rna.write_h5ad(f"{outdir}/{prefix}_rna.h5ad")
    atac.write_h5ad(f"{outdir}/{prefix}_atac.h5ad")
    return {"n_rna": len(obs), "n_atac": int(keep.sum()),
            "shared": int(keep.sum()) if atac_sep == "_" else 0,
            "mg_total": int(sum(mg_per_donor)),
            "mg_paired": int(((obs.cell_type == "MG").values & keep).sum()),
            "mg_per_donor": dict(zip(donors, mg_per_donor))}


def build_c(outdir="."):
    """Realistic 10x naming, sample qualifier on opposite sides, colliding barcodes."""
    bases = np.array(list("ACGT"))
    samples = ["NABEC_1234", "HBCC_5678"]
    n_per = 300
    mg_per = [60, 25]
    # The SAME raw barcode strings are reused across both samples on purpose: a
    # barcode-only match would fuse nuclei from different donors.
    raw = [f"{''.join(rng.choice(bases, 16))}-1" for _ in range(n_per)]
    rows, atac_rows = [], []
    keep_mask = []
    for si, (s, m) in enumerate(zip(samples, mg_per)):
        ct = ["Microglia"] * m + list(rng.choice(["ExN", "InN", "Oligo", "Astro"], n_per - m))
        coh = "NABEC" if si == 0 else "HBCC"
        k = rng.random(n_per) < 0.85
        keep_mask.extend(k.tolist())
        for j, t in enumerate(ct):
            rows.append((f"{s}_{raw[j]}", t, s, coh))
            if k[j]:
                atac_rows.append((f"{raw[j]}_{s}", t, s, coh))
    obs = pd.DataFrame(rows, columns=["bc", "cell_type", "sample_id", "cohort"]).set_index("bc")
    aobs = pd.DataFrame(atac_rows, columns=["bc", "cell_type", "sample_id", "cohort"]).set_index("bc")
    for df in (obs, aobs):
        df["age"] = rng.integers(15, 100, len(df))
        df["sex"] = rng.choice(["M", "F"], len(df))
        df["PMI"] = rng.uniform(5, 40, len(df))
        for c in ["cell_type", "sample_id", "cohort", "sex"]:
            df[c] = df[c].astype("category")
    counts = sp.random(len(obs), 200, density=0.05, format="csr", random_state=3,
                       data_rvs=lambda k: rng.integers(1, 20, k)).astype(np.float32)
    ad.AnnData(X=counts, obs=obs,
               var=pd.DataFrame(index=[f"GENE{i}" for i in range(200)])
               ).write_h5ad(f"{outdir}/C_rna.h5ad")
    peaks = sp.random(len(aobs), 300, density=0.03, format="csr", random_state=4,
                      data_rvs=lambda k: rng.integers(1, 4, k)).astype(np.float32)
    ad.AnnData(X=peaks, obs=aobs,
               var=pd.DataFrame(index=[f"chr2:{i*1000}-{i*1000+500}" for i in range(300)])
               ).write_h5ad(f"{outdir}/C_atac.h5ad")
    mg_paired = int(((obs.cell_type == "Microglia").values
                     & np.array(keep_mask, dtype=bool)).sum())
    return {"n_rna": len(obs), "n_atac": len(aobs), "shared_exact": 0,
            "shared_composite": len(aobs),
            "mg_total": int(sum(mg_per)), "mg_paired": mg_paired,
            "mg_per_donor": dict(zip(samples, mg_per)),
            "note": "raw barcodes deliberately collide across the two samples"}


def main(outdir="."):
    t = {}
    t["A"] = build("A", [400, 300, 500, 250], [40, 0, 75, 12], raw_in_x=False, outdir=outdir)
    t["B"] = build("B", [200, 200], [10, 30], raw_in_x=True, atac_sep="#",
                   mismatch=False, outdir=outdir)
    t["C"] = build_c(outdir)
    with open(f"{outdir}/truth_v2.json", "w") as fh:
        json.dump(t, fh, indent=1)
    print(json.dumps(t, indent=1))
    return t


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
