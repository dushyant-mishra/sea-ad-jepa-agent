#!/usr/bin/env python3
"""Outcome-blind schema probe for paired RNA/ATAC .h5ad files (NIH-CARD Catching 2026).

Answers three execution questions without loading full matrices:
  1. What does each matrix slot (.X, .layers/*, .raw/X) contain: raw integer counts or transformed values?
  2. Do RNA and ATAC share a nucleus barcode namespace, and do donor labels agree on shared barcodes?
  3. How many microglia nuclei are there per donor (and per cohort)?

Exposure statement: reads obs/var metadata and a bounded sample (default 20,000) of stored matrix
values per slot to test integer-ness. It computes NO relationship between RNA and ATAC values.

Works on local paths, or on URLs via fsspec HTTP range requests (reads only the bytes it needs,
if the server supports ranges; otherwise download the files first).

Usage:
  python h5ad_schema_probe.py --rna final_rna_data.h5ad --atac final_atac_data.h5ad --out receipt.json
Optional: --celltype-col NAME --donor-col NAME --cohort-col NAME --sample-values N
"""
import argparse, json, re, sys, time
import numpy as np
import h5py

TOOL_VERSION = "1.0.0"
CELLTYPE_CANDIDATES = ["cell_type", "celltype", "cell_types", "cellType", "annotation", "annot",
                       "major_celltype", "broad_celltype", "cell_type_broad", "label", "leiden_celltype"]
DONOR_CANDIDATES = ["sample_id", "sample", "Sample", "Sample_ID", "donor", "donor_id", "individual",
                    "individualID", "subject", "subject_id", "batch_sample"]
COHORT_CANDIDATES = ["cohort", "Cohort", "study", "dataset"]
COVARIATE_PATTERNS = {"age": r"age", "sex": r"sex|gender", "pmi": r"pmi|post.?mortem",
                      "cohort": r"cohort", "batch": r"batch|seq", "brain_bank": r"bank",
                      "ancestry": r"ancestr|race|popul"}
MICROGLIA_RE = re.compile(r"(^mg$|^mg[_\- ]|microgli)", re.I)


def open_h5(path):
    if re.match(r"^https?://", path):
        import fsspec
        fobj = fsspec.open(path, "rb", block_size=4 * 1024 * 1024).open()
        return h5py.File(fobj, "r")
    return h5py.File(path, "r")


def _decode(arr):
    arr = np.asarray(arr)
    if arr.dtype.kind in ("S", "O"):
        return np.array([x.decode() if isinstance(x, bytes) else str(x) for x in arr], dtype=object)
    return arr


def read_column(obs, name):
    """Read one obs/var column, handling modern categorical groups and legacy __categories."""
    node = obs[name]
    if isinstance(node, h5py.Group):
        if "categories" in node and "codes" in node:
            cats = _decode(node["categories"][()])
            codes = node["codes"][()]
            out = np.empty(len(codes), dtype=object)
            out[codes >= 0] = cats[codes[codes >= 0]]
            out[codes < 0] = None
            return out
        if "values" in node:  # nullable arrays (anndata >= 0.10): values + mask
            vals = _decode(node["values"][()]).astype(object)
            if "mask" in node:
                vals[node["mask"][()].astype(bool)] = None
            return vals
        raise ValueError(f"unrecognised column group {name}")
    vals = node[()]
    legacy = obs.get("__categories")
    if legacy is not None and name in legacy:
        cats = _decode(legacy[name][()])
        out = np.empty(len(vals), dtype=object)
        out[vals >= 0] = cats[vals[vals >= 0]]
        return out
    return _decode(vals)


def frame_index(grp):
    idx_name = grp.attrs.get("_index", "_index")
    if isinstance(idx_name, bytes):
        idx_name = idx_name.decode()
    return read_column(grp, idx_name), idx_name


def list_columns(grp, idx_name):
    cols = [k for k in grp.keys() if k not in (idx_name, "__categories")]
    order = grp.attrs.get("column-order")
    if order is not None and len(order):
        cols = [c.decode() if isinstance(c, bytes) else str(c) for c in order]
    return cols


def pick(cols, override, candidates):
    if override:
        if override not in cols:
            raise SystemExit(f"column '{override}' not found; available: {cols}")
        return override
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None


def matrix_info(node, n_sample, rng):
    info = {}
    if isinstance(node, h5py.Dataset):
        info["storage"] = "dense"
        info["shape"] = list(node.shape)
        info["dtype"] = str(node.dtype)
        rows = min(node.shape[0], max(1, n_sample // max(1, node.shape[1]) + 1))
        vals = node[:rows].ravel()[:n_sample]
    else:
        enc = node.attrs.get("encoding-type", node.attrs.get("h5sparse_format", "unknown"))
        info["storage"] = enc.decode() if isinstance(enc, bytes) else str(enc)
        shape = node.attrs.get("shape", node.attrs.get("h5sparse_shape"))
        info["shape"] = [int(s) for s in shape] if shape is not None else None
        data = node["data"]
        info["dtype"] = str(data.dtype)
        info["nnz"] = int(data.shape[0])
        if data.shape[0] == 0:
            vals = np.array([])
        else:
            # contiguous blocks from several positions: cheap over HTTP, avoids only-first-rows bias
            k = 8
            block = max(1, n_sample // k)
            starts = np.unique(rng.integers(0, max(1, data.shape[0] - block), size=k))
            vals = np.concatenate([data[s:s + block] for s in starts])
    vals = np.asarray(vals, dtype=np.float64)
    if vals.size:
        nonzero = vals[vals != 0]
        frac_nonint = float(np.mean(np.abs(nonzero - np.round(nonzero)) > 1e-6)) if nonzero.size else 0.0
        info["sampled_values"] = int(vals.size)
        info["sample_min"] = float(vals.min())
        info["sample_max"] = float(vals.max())
        info["sample_fraction_nonzero_noninteger"] = frac_nonint
        info["sample_has_negative"] = bool((vals < 0).any())
        if frac_nonint == 0.0 and not info["sample_has_negative"]:
            verdict = "LOOKS_LIKE_RAW_INTEGER_COUNTS"
        elif info["sample_max"] < 20 and not info["sample_has_negative"]:
            verdict = "LOOKS_LIKE_LOG_TRANSFORMED"
        else:
            verdict = "NONINTEGER_NOT_LOG_LIKE_CHECK_MANUALLY"
        info["verdict"] = verdict
    return info


def probe_file(path, n_sample, rng):
    f = open_h5(path)
    out = {"path": path, "top_level_keys": sorted(f.keys())}
    obs_index, obs_idx_name = frame_index(f["obs"])
    var_index, var_idx_name = frame_index(f["var"])
    out["n_obs"] = int(len(obs_index))
    out["n_var"] = int(len(var_index))
    out["obs_index_unique"] = bool(len(set(obs_index)) == len(obs_index))
    out["obs_index_examples"] = [str(x) for x in obs_index[:3]]
    out["var_index_examples"] = [str(x) for x in var_index[:5]]
    out["obs_columns"] = list_columns(f["obs"], obs_idx_name)
    out["var_columns"] = list_columns(f["var"], var_idx_name)
    slots = {}
    if "X" in f:
        slots["X"] = matrix_info(f["X"], n_sample, rng)
    if "layers" in f:
        for k in f["layers"].keys():
            slots[f"layers/{k}"] = matrix_info(f["layers"][k], n_sample, rng)
    if "raw" in f and "X" in f["raw"]:
        slots["raw/X"] = matrix_info(f["raw"]["X"], n_sample, rng)
        if "var" in f["raw"]:
            out["raw_n_var"] = int(len(frame_index(f["raw"]["var"])[0]))
    out["matrix_slots"] = slots
    out["raw_count_slots"] = [k for k, v in slots.items() if v.get("verdict") == "LOOKS_LIKE_RAW_INTEGER_COUNTS"]
    return f, obs_index, out


def covariate_presence(cols):
    found = {}
    for key, pat in COVARIATE_PATTERNS.items():
        found[key] = [c for c in cols if re.search(pat, c, re.I)]
    return found


def barcode_overlap(rna_idx, atac_idx):
    rs, as_ = set(map(str, rna_idx)), set(map(str, atac_idx))
    inter = rs & as_
    res = {"n_rna": len(rs), "n_atac": len(as_), "n_shared_exact": len(inter),
           "frac_rna_in_atac": len(inter) / max(1, len(rs)), "frac_atac_in_rna": len(inter) / max(1, len(as_))}
    if len(inter) < 0.5 * min(len(rs), len(as_)):
        # diagnose prefix/suffix convention differences without assuming which one is right
        def core(x):
            return re.split(r"[_:#]", x)[-1] if re.search(r"[_:#]", x) else x
        rc, ac = {core(x) for x in rs}, {core(x) for x in as_}
        res["n_shared_after_stripping_prefix"] = len(rc & ac)
        res["note"] = ("exact overlap low; the stripped-prefix count alone does NOT prove pairing, because raw "
                       "10x barcodes repeat across samples. Match on (sample, barcode) instead.")
    return res, inter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rna", required=True)
    ap.add_argument("--atac", required=True)
    ap.add_argument("--out", default="nihcard_schema_receipt.json")
    ap.add_argument("--celltype-col")
    ap.add_argument("--donor-col")
    ap.add_argument("--cohort-col")
    ap.add_argument("--sample-values", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    t0 = time.time()
    receipt = {"tool": "h5ad_schema_probe", "tool_version": TOOL_VERSION,
               "exposure": "metadata + bounded value sample per slot; no RNA-ATAC relationship computed"}

    frna, rna_idx, rinfo = probe_file(a.rna, a.sample_values, rng)
    fatac, atac_idx, ainfo = probe_file(a.atac, a.sample_values, rng)
    receipt["rna"], receipt["atac"] = rinfo, ainfo

    ov, shared = barcode_overlap(rna_idx, atac_idx)
    receipt["barcode_overlap"] = ov

    cols = rinfo["obs_columns"]
    ct_col = pick(cols, a.celltype_col, CELLTYPE_CANDIDATES)
    dn_col = pick(cols, a.donor_col, DONOR_CANDIDATES)
    co_col = pick(cols, a.cohort_col, COHORT_CANDIDATES)
    receipt["columns_used"] = {"celltype": ct_col, "donor": dn_col, "cohort": co_col}
    receipt["rna_covariate_columns_found"] = covariate_presence(cols)

    if dn_col and dn_col in ainfo["obs_columns"] and len(shared) > 0:
        rd = dict(zip(map(str, rna_idx), read_column(frna["obs"], dn_col)))
        ad = dict(zip(map(str, atac_idx), read_column(fatac["obs"], dn_col)))
        mism = sum(1 for b in shared if str(rd[b]) != str(ad[b]))
        receipt["donor_label_agreement_on_shared"] = {"n_checked": len(shared), "n_mismatch": int(mism)}
    else:
        receipt["donor_label_agreement_on_shared"] = "NOT_CHECKED (donor column absent from ATAC obs or no shared barcodes)"

    if ct_col and dn_col:
        ct = read_column(frna["obs"], ct_col)
        dn = read_column(frna["obs"], dn_col)
        labels = sorted({str(x) for x in ct if x is not None})
        mg_labels = [l for l in labels if MICROGLIA_RE.search(l)]
        receipt["celltype_labels"] = labels
        receipt["microglia_labels_matched"] = mg_labels
        is_mg = np.isin(ct.astype(str), mg_labels)
        in_atac = np.isin(np.asarray(rna_idx, dtype=str), np.asarray(list(shared), dtype=str)) if shared else np.zeros(len(ct), bool)
        donors, counts = np.unique(dn[is_mg].astype(str), return_counts=True)
        _, counts_paired = np.unique(dn[is_mg & in_atac].astype(str), return_counts=True) if (is_mg & in_atac).any() else (None, np.array([]))
        all_donors = np.unique(dn.astype(str))
        per = {d: 0 for d in all_donors}
        per.update(dict(zip(donors, counts.tolist())))
        vals = np.array(list(per.values()))
        receipt["microglia"] = {
            "n_total_rna": int(is_mg.sum()),
            "n_total_paired_with_atac": int((is_mg & in_atac).sum()),
            "n_donors": int(len(all_donors)),
            "per_donor_quantiles": {q: float(np.quantile(vals, q)) for q in (0, 0.1, 0.25, 0.5, 0.75, 0.9, 1)},
            "donors_below": {str(t): int((vals < t).sum()) for t in (20, 50, 100, 200)},
            "per_donor_counts": {k: int(v) for k, v in sorted(per.items())},
        }
        if co_col:
            co = read_column(frna["obs"], co_col).astype(str)
            donor_cohort = {}
            for d, c in zip(dn.astype(str), co):
                donor_cohort.setdefault(d, c)
            by = {}
            for d, n in per.items():
                by.setdefault(donor_cohort.get(d, "NA"), []).append(n)
            receipt["microglia"]["by_cohort"] = {c: {"n_donors": len(v), "median_per_donor": float(np.median(v)),
                                                     "total": int(sum(v))} for c, v in by.items()}
    else:
        receipt["microglia"] = f"NOT_COMPUTED: celltype col={ct_col}, donor col={dn_col}; rerun with --celltype-col/--donor-col"

    receipt["elapsed_seconds"] = round(time.time() - t0, 1)
    with open(a.out, "w") as fh:
        json.dump(receipt, fh, indent=2, default=str)
    s = receipt
    print(f"RNA  slots: {[(k, v.get('verdict')) for k, v in s['rna']['matrix_slots'].items()]}")
    print(f"ATAC slots: {[(k, v.get('verdict')) for k, v in s['atac']['matrix_slots'].items()]}")
    print(f"barcodes: shared {ov['n_shared_exact']} | RNA {ov['n_rna']} | ATAC {ov['n_atac']}")
    if isinstance(s["microglia"], dict):
        m = s["microglia"]
        print(f"microglia: {m['n_total_rna']} total, {m['n_total_paired_with_atac']} paired, "
              f"median/donor {m['per_donor_quantiles'][0.5]:.0f}, donors<50: {m['donors_below']['50']}")
    else:
        print(s["microglia"])
    print(f"receipt -> {a.out}")


if __name__ == "__main__":
    main()
