#!/usr/bin/env python3
"""Outcome-blind schema probe for paired RNA/ATAC .h5ad files -- VERSION 2, FAIL-CLOSED.

Successor to h5ad_schema_probe.py v1.0.0, which is preserved unmodified alongside
this file as h5ad_schema_probe_v1_0_as_received.py (sha256
8e6dc7b634b1bcad0486c2e933c37ad61b94080f1ad19e8e2dfe8c556c2250c8). v1.0 history is
not rewritten.

WHY A SUCCESSOR EXISTS -- the v1.0 qualification defect
-------------------------------------------------------
On fixture B the RNA index is "D00_000123" and the ATAC index is "D00#000123".
v1.0 correctly reported zero exact overlap and correctly warned that stripping the
prefix is unsafe, but it then reported

    "n_total_paired_with_atac": 0

when the planted truth was 35. Zero is a *measurement*; the truth here is that the
measurement could not be made. v1.0 could not distinguish

    "the barcode namespaces do not line up, so pairing is UNRESOLVED"
from
    "these nuclei genuinely have no ATAC partner".

Those two states have opposite consequences for a qualification decision, and a
receipt that renders them identically is not fail-closed.

WHAT v2 DOES DIFFERENTLY
------------------------
1. Pairing has an explicit STATE, decided against a predeclared threshold:
     PAIRING_RESOLVED_EXACT        exact overlap >= HIGH_OVERLAP_MIN of the smaller set
     PAIRING_NAMESPACE_UNRESOLVED  below that
2. In the UNRESOLVED state every pairing-dependent quantity is reported as JSON
   null with an accompanying status string. NEVER as 0.
3. The (sample, raw_barcode) composite match is computed as a DIAGNOSTIC in both
   states. It never becomes the authoritative pairing basis unless the operator
   passes --trust-composite-pairing, and when they do, the receipt records that
   the basis was operator-asserted rather than observed.
4. Donor-label agreement across shared nuclei is a QUALIFICATION REQUIREMENT:
   zero mismatches, and "not checkable" is not a pass.
5. Matrix-slot language is softened. An integer-valued nonnegative matrix is a
   COUNT_LIKE_INTEGER_MATRIX. Calling it raw or CellBender-corrected requires
   independent metadata this probe does not have and does not pretend to have.
6. A top-level `qualification` block and `probe_status` make the receipt
   fail-closed: a consumer can tell at a glance whether the probe succeeded,
   without re-deriving it from the body.

Also repaired from v1.0, found by reading rather than reported:
  - per-donor PAIRED microglia counts were computed and then discarded (the
    `counts_paired` variable was assigned and never used). They are now reported.
  - dense-matrix sampling read only the leading rows, the exact first-rows bias
    the sparse branch's own comment says it avoids. Now sampled across the matrix.
  - per-donor quantile keys were floats, so the in-memory receipt and the
    JSON-round-tripped receipt had different key types and `[0.5]` raised
    KeyError after reloading. Keys are strings now.
  - a celltype column with no microglia-matching label produced an empty match
    list and then a silent zero. It now raises a status.

EXPOSURE. Reads obs/var metadata and a bounded sample of stored matrix values per
slot to test integer-ness. Computes NO relationship between RNA and ATAC values.
No biological outcome is opened.

Usage:
  python h5ad_schema_probe_v2.py --rna rna.h5ad --atac atac.h5ad --out receipt.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time

import h5py
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TOOL_VERSION = "2.1.0"
SUPERSEDES = "2.0.0 (which superseded 1.0.0)"

# Predeclared, before any real file is read. Exact overlap must reach this
# fraction of the SMALLER index for pairing to count as resolved.
HIGH_OVERLAP_MIN = 0.50

CELLTYPE_CANDIDATES = ["cell_type", "celltype", "cell_types", "cellType", "annotation",
                       "annot", "major_celltype", "broad_celltype", "cell_type_broad",
                       "label", "leiden_celltype"]
DONOR_CANDIDATES = ["sample_id", "sampleid", "sample", "Sample", "Sample_ID", "SampleID",
                    "donor", "donorid", "donor_id", "individual", "individualID",
                    "subject", "subject_id", "batch_sample"]
COHORT_CANDIDATES = ["cohort", "Cohort", "study", "dataset"]
COVARIATE_PATTERNS = {"age": r"age", "sex": r"sex|gender", "pmi": r"pmi|post.?mortem",
                      "cohort": r"cohort", "batch": r"batch|seq", "brain_bank": r"bank",
                      "ancestry": r"ancestr|race|popul"}
MICROGLIA_RE = re.compile(r"(^mg$|^mg[_\- ]|microgli|^micro$)", re.I)
# 10x cell barcodes are 16 bp; allow 14-18 plus an optional -1 lane suffix.
TENX_BC_RE = re.compile(r"([ACGTN]{14,18})(-\d+)?", re.I)


#: populated when a remote file is opened, so the receipt can report exactly how
#: many HTTP requests were made and what fraction of each file was transferred.
REMOTE_READERS = {}


def open_h5(path):
    """Local path, or an HTTP(S) URL read by byte range.

    fsspec's HTTP backend is tried first, but it requires aiohttp, which cannot
    be imported in some environments (a broken interpreter certificate store
    raises ssl.SSLError at import). The fallback is a small requests+certifi
    range reader, which is what actually runs here.
    """
    if re.match(r"^https?://", path):
        try:
            import fsspec
            fobj = fsspec.open(path, "rb", block_size=4 * 1024 * 1024).open()
            return h5py.File(fobj, "r")
        except Exception:
            from http_range_file_v1 import HTTPRangeFile
            rdr = HTTPRangeFile(path)
            REMOTE_READERS[path] = rdr
            return h5py.File(rdr, "r")
    return h5py.File(path, "r")


def _decode(arr):
    arr = np.asarray(arr)
    if arr.dtype.kind in ("S", "O"):
        return np.array([x.decode() if isinstance(x, bytes) else str(x) for x in arr],
                        dtype=object)
    return arr


def read_column(obs, name):
    """One obs/var column, handling modern categorical groups, nullable arrays and
    the legacy __categories layout."""
    node = obs[name]
    if isinstance(node, h5py.Group):
        if "categories" in node and "codes" in node:
            cats = _decode(node["categories"][()])
            codes = node["codes"][()]
            out = np.empty(len(codes), dtype=object)
            out[codes >= 0] = cats[codes[codes >= 0]]
            out[codes < 0] = None
            return out
        if "values" in node:
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
    if idx_name not in grp:
        raise SystemExit(f"STOP_NO_INDEX: frame has no '{idx_name}' dataset; keys={list(grp.keys())[:10]}")
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


def raw_barcode(x: str) -> str:
    """The cell-barcode part of an index entry, for the composite DIAGNOSTIC only.

    Prefers an actual 10x-looking DNA barcode; falls back to the last delimited
    token. Both are guesses about a naming convention, which is exactly why the
    result of this function is never authoritative on its own -- raw 10x barcodes
    repeat across samples, so a match here is not evidence of a shared nucleus
    unless it is qualified by sample.
    """
    m = TENX_BC_RE.search(x)
    if m:
        return m.group(0).upper()
    return re.split(r"[_:#|]", x)[-1]


def matrix_info(node, n_sample, rng):
    info = {}
    if isinstance(node, h5py.Dataset):
        info["storage"] = "dense"
        info["shape"] = list(node.shape)
        info["dtype"] = str(node.dtype)
        # v1.0 read only node[:rows] -- the leading-rows bias the sparse branch
        # explicitly avoids. Sample row blocks from across the matrix instead.
        nrow, ncol = (node.shape + (1,))[:2]
        per = max(1, n_sample // max(1, ncol))
        k = min(8, max(1, nrow))
        starts = np.unique(rng.integers(0, max(1, nrow), size=k))
        chunks = [np.asarray(node[s:min(s + max(1, per // k), nrow)]).ravel() for s in starts]
        vals = np.concatenate(chunks)[:n_sample] if chunks else np.array([])
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
            k = 8
            block = max(1, n_sample // k)
            starts = np.unique(rng.integers(0, max(1, data.shape[0] - block), size=k))
            vals = np.concatenate([data[s:s + block] for s in starts])
    vals = np.asarray(vals, dtype=np.float64)
    if vals.size:
        nonzero = vals[vals != 0]
        frac_nonint = (float(np.mean(np.abs(nonzero - np.round(nonzero)) > 1e-6))
                       if nonzero.size else 0.0)
        info["sampled_values"] = int(vals.size)
        info["sample_min"] = float(vals.min())
        info["sample_max"] = float(vals.max())
        info["sample_fraction_nonzero_noninteger"] = frac_nonint
        info["sample_has_negative"] = bool((vals < 0).any())
        if frac_nonint == 0.0 and not info["sample_has_negative"]:
            # SOFTENED from v1.0's LOOKS_LIKE_RAW_INTEGER_COUNTS. Integer-valued and
            # nonnegative is all that was observed. Whether the slot holds raw counts,
            # CellBender-corrected counts, or integer-rounded something else cannot be
            # decided from values alone and needs independent metadata.
            verdict = "COUNT_LIKE_INTEGER_MATRIX"
        elif info["sample_max"] < 20 and not info["sample_has_negative"]:
            verdict = "NONINTEGER_LOG_LIKE"
        else:
            verdict = "NONINTEGER_NOT_LOG_LIKE_CHECK_MANUALLY"
        info["verdict"] = verdict
        info["verdict_note"] = (
            "COUNT_LIKE_INTEGER_MATRIX means integer-valued and nonnegative in the "
            "sampled values ONLY. It does not establish raw or CellBender-corrected "
            "provenance; that requires independent metadata.")
    return info


def probe_file(path, n_sample, rng):
    f = open_h5(path)
    out = {"path": path, "top_level_keys": sorted(f.keys())}
    if not re.match(r"^https?://", path) and os.path.exists(path):
        out["bytes"] = os.path.getsize(path)
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
    out["count_like_slots"] = [k for k, v in slots.items()
                               if v.get("verdict") == "COUNT_LIKE_INTEGER_MATRIX"]
    return f, obs_index, out


def covariate_presence(cols):
    return {key: [c for c in cols if re.search(pat, c, re.I)]
            for key, pat in COVARIATE_PATTERNS.items()}


def assess_pairing(rna_idx, atac_idx, rna_sample=None, atac_sample=None):
    """Decide the pairing state and compute the composite diagnostic.

    Returns (pairing_dict, shared_set_or_None). shared is None whenever the state
    is UNRESOLVED, so that downstream code CANNOT silently treat an unresolved
    namespace as an empty intersection -- which is precisely the v1.0 defect.
    """
    rs = list(map(str, rna_idx))
    as_ = list(map(str, atac_idx))
    rset, aset = set(rs), set(as_)
    inter = rset & aset
    smaller = max(1, min(len(rset), len(aset)))
    frac_small = len(inter) / smaller
    p = {
        "n_rna": len(rset), "n_atac": len(aset), "n_shared_exact": len(inter),
        "frac_of_smaller_shared": round(frac_small, 6),
        "threshold_frac_of_smaller": HIGH_OVERLAP_MIN,
        "frac_rna_in_atac": round(len(inter) / max(1, len(rset)), 6),
        "frac_atac_in_rna": round(len(inter) / max(1, len(aset)), 6),
    }
    resolved = frac_small >= HIGH_OVERLAP_MIN
    p["state"] = "PAIRING_RESOLVED_EXACT" if resolved else "PAIRING_NAMESPACE_UNRESOLVED"

    # Composite (sample, raw_barcode) DIAGNOSTIC. Computed in both states; never
    # authoritative on its own.
    diag = {"computable": False,
            "why": "donor/sample column absent from one or both files"}
    if rna_sample is not None and atac_sample is not None:
        rk = {(str(s), raw_barcode(b)) for s, b in zip(rna_sample, rs)}
        ak = {(str(s), raw_barcode(b)) for s, b in zip(atac_sample, as_)}
        ck = rk & ak
        diag = {
            "computable": True,
            "n_rna_composite_keys": len(rk),
            "n_atac_composite_keys": len(ak),
            "n_shared_composite": len(ck),
            "frac_of_smaller_shared": round(len(ck) / max(1, min(len(rk), len(ak))), 6),
            "would_resolve": bool(len(ck) / max(1, min(len(rk), len(ak))) >= HIGH_OVERLAP_MIN),
            "AUTHORITATIVE": False,
            "why_not_authoritative": (
                "raw 10x barcodes repeat across samples and the sample qualifier is "
                "taken from a column whose correspondence between the two files has "
                "not been independently established. A composite match is consistent "
                "with shared nuclei; it is not evidence of them. Pass "
                "--trust-composite-pairing to assert it deliberately."),
        }
    p["composite_diagnostic"] = diag
    p["basis_used_for_counts"] = "EXACT_INDEX" if resolved else "NONE__UNRESOLVED"
    if not resolved:
        p["note"] = (
            "Exact overlap is below the predeclared threshold, so nucleus pairing is "
            "UNRESOLVED. Pairing-dependent quantities are reported as null, NOT as "
            "zero: this probe cannot distinguish an unmatched namespace from genuinely "
            "unpaired nuclei, and reporting zero would assert the second.")
    return p, (inter if resolved else None)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rna", required=True)
    ap.add_argument("--atac", required=True)
    ap.add_argument("--out", default="nihcard_schema_receipt_v2.json")
    ap.add_argument("--celltype-col")
    ap.add_argument("--donor-col")
    ap.add_argument("--cohort-col")
    ap.add_argument("--donor-col-atac",
                    help="donor column in the ATAC file when it differs from RNA's")
    ap.add_argument("--sample-values", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--trust-composite-pairing", action="store_true",
                    help="OPERATOR ASSERTION. Use the (sample, raw_barcode) composite "
                         "match as the authoritative pairing basis when the exact "
                         "namespace is unresolved. Recorded in the receipt as asserted, "
                         "not observed. Off by default.")
    a = ap.parse_args(argv)
    rng = np.random.default_rng(a.seed)
    t0 = time.time()
    receipt = {
        "tool": "h5ad_schema_probe",
        "tool_version": TOOL_VERSION,
        "supersedes": SUPERSEDES,
        "exposure": ("obs/var metadata plus a bounded sample of stored matrix values "
                     "per slot; NO RNA-ATAC relationship computed; no biological "
                     "outcome opened"),
    }

    frna, rna_idx, rinfo = probe_file(a.rna, a.sample_values, rng)
    fatac, atac_idx, ainfo = probe_file(a.atac, a.sample_values, rng)
    receipt["rna"], receipt["atac"] = rinfo, ainfo

    cols = rinfo["obs_columns"]
    ct_col = pick(cols, a.celltype_col, CELLTYPE_CANDIDATES)
    dn_col = pick(cols, a.donor_col, DONOR_CANDIDATES)
    co_col = pick(cols, a.cohort_col, COHORT_CANDIDATES)
    receipt["columns_used"] = {"celltype": ct_col, "donor": dn_col, "cohort": co_col}
    receipt["rna_covariate_columns_found"] = covariate_presence(cols)
    receipt["atac_covariate_columns_found"] = covariate_presence(ainfo["obs_columns"])

    # The two files need NOT use the same column name for donor. NIH-CARD is a
    # live example: RNA carries "SampleID" and ATAC carries "sample_id". Resolving
    # one name for both would silently skip the donor-agreement check -- which is
    # a QUALIFICATION REQUIREMENT, so skipping it must never happen quietly.
    dn_col_atac = pick(ainfo["obs_columns"], a.donor_col_atac, DONOR_CANDIDATES)
    receipt["columns_used"]["donor_atac"] = dn_col_atac
    receipt["columns_used"]["donor_column_names_differ_between_files"] = bool(
        dn_col and dn_col_atac and dn_col != dn_col_atac)
    rna_donor = read_column(frna["obs"], dn_col) if dn_col else None
    atac_donor = read_column(fatac["obs"], dn_col_atac) if dn_col_atac else None

    pairing, shared = assess_pairing(rna_idx, atac_idx, rna_donor, atac_donor)
    if shared is None and a.trust_composite_pairing and \
            pairing["composite_diagnostic"].get("computable"):
        rk = {(str(s), raw_barcode(str(b))): str(b) for s, b in zip(rna_donor, rna_idx)}
        ak = {(str(s), raw_barcode(str(b))) for s, b in zip(atac_donor, atac_idx)}
        shared = {v for k, v in rk.items() if k in ak}
        pairing["basis_used_for_counts"] = "COMPOSITE_SAMPLE_BARCODE__OPERATOR_ASSERTED"
        pairing["operator_assertion"] = (
            "--trust-composite-pairing was passed. Pairing counts below rest on an "
            "ASSERTED convention, not an observed shared namespace.")
    receipt["pairing"] = pairing

    # Donor-label agreement -- a qualification requirement, and 'not checkable' is
    # not a pass.
    if shared is not None and rna_donor is not None and atac_donor is not None:
        rd = dict(zip(map(str, rna_idx), rna_donor))
        ad = dict(zip(map(str, atac_idx), atac_donor))
        checkable = [b for b in shared if b in rd and b in ad]
        mism = sum(1 for b in checkable if str(rd[b]) != str(ad[b]))
        receipt["donor_label_agreement_on_shared"] = {
            "checked": True, "n_checked": len(checkable), "n_mismatch": int(mism),
            "consistent": bool(mism == 0)}
    else:
        why = ("pairing unresolved" if shared is None
               else "donor column unresolved in one or both files")
        receipt["donor_label_agreement_on_shared"] = {
            "checked": False, "consistent": None,
            "status": f"NOT_CHECKABLE__{why.upper().replace(' ', '_')}"}

    # Microglia
    mg_status = None
    if ct_col and dn_col:
        ct = read_column(frna["obs"], ct_col)
        dn = np.asarray([str(x) for x in rna_donor], dtype=object)
        labels = sorted({str(x) for x in ct if x is not None})
        mg_labels = [l for l in labels if MICROGLIA_RE.search(l)]
        receipt["celltype_labels"] = labels
        receipt["microglia_labels_matched"] = mg_labels
        if not mg_labels:
            mg_status = "NO_MICROGLIA_LABEL_MATCHED__INSPECT_celltype_labels"
            receipt["microglia"] = {"status": mg_status}
        else:
            is_mg = np.isin(np.asarray([str(x) for x in ct], dtype=object), mg_labels)
            all_donors = sorted(set(dn.tolist()))
            per = {d: 0 for d in all_donors}
            for d, m in zip(dn.tolist(), is_mg.tolist()):
                if m:
                    per[d] += 1
            vals = np.array([per[d] for d in all_donors])
            mg = {
                "n_total_rna": int(is_mg.sum()),
                "n_donors": len(all_donors),
                "per_donor_counts": {k: int(v) for k, v in per.items()},
                "per_donor_quantiles": {str(q): float(np.quantile(vals, q))
                                        for q in (0, 0.1, 0.25, 0.5, 0.75, 0.9, 1)},
                "donors_below": {str(t): int((vals < t).sum()) for t in (20, 50, 100, 200)},
                "donors_with_zero_microglia": [d for d in all_donors if per[d] == 0],
            }
            if shared is None:
                # THE v1.0 DEFECT, FIXED. null, never 0.
                mg["n_total_paired_with_atac"] = None
                mg["per_donor_paired_counts"] = None
                mg["paired_status"] = "PAIRING_NAMESPACE_UNRESOLVED"
            else:
                sh = set(shared)
                in_atac = np.asarray([str(b) in sh for b in rna_idx], dtype=bool)
                perp = {d: 0 for d in all_donors}
                for d, m in zip(dn.tolist(), (is_mg & in_atac).tolist()):
                    if m:
                        perp[d] += 1
                mg["n_total_paired_with_atac"] = int((is_mg & in_atac).sum())
                # v1.0 computed this and threw it away.
                mg["per_donor_paired_counts"] = {k: int(v) for k, v in perp.items()}
                mg["paired_status"] = "PAIRED_COUNTS_FROM_" + pairing["basis_used_for_counts"]
            if co_col:
                co = np.asarray([str(x) for x in read_column(frna["obs"], co_col)],
                                dtype=object)
                donor_cohort = {}
                for d, c in zip(dn.tolist(), co.tolist()):
                    donor_cohort.setdefault(d, c)
                by = {}
                for d in all_donors:
                    by.setdefault(donor_cohort.get(d, "NA"), []).append(per[d])
                mg["by_cohort"] = {c: {"n_donors": len(v),
                                       "median_per_donor": float(np.median(v)),
                                       "total": int(sum(v))} for c, v in by.items()}
            receipt["microglia"] = mg
    else:
        mg_status = f"NOT_COMPUTED: celltype col={ct_col}, donor col={dn_col}"
        receipt["microglia"] = {"status": mg_status}

    # Fail-closed qualification block.
    mgd = receipt.get("microglia", {})
    q = {
        "pairing_resolved": pairing["state"] == "PAIRING_RESOLVED_EXACT",
        "pairing_basis": pairing["basis_used_for_counts"],
        "donor_labels_consistent": receipt["donor_label_agreement_on_shared"].get("consistent"),
        "microglia_counts_available": isinstance(mgd, dict) and "n_total_rna" in mgd,
        "paired_microglia_available": isinstance(mgd, dict)
                                      and mgd.get("n_total_paired_with_atac") is not None,
    }
    q["QUALIFIED_FOR_PAIRED_USE"] = bool(
        q["pairing_resolved"] and q["donor_labels_consistent"] is True
        and q["microglia_counts_available"] and q["paired_microglia_available"])
    q["rule"] = ("QUALIFIED_FOR_PAIRED_USE requires an exactly resolved namespace, ZERO "
                 "donor-label mismatches across shared nuclei, and available microglia "
                 "and paired-microglia counts. An operator-asserted composite basis does "
                 "NOT satisfy pairing_resolved.")
    receipt["qualification"] = q
    receipt["probe_status"] = "PROBE_OK" if q["QUALIFIED_FOR_PAIRED_USE"] else "PROBE_INCOMPLETE"
    if REMOTE_READERS:
        receipt["remote_read"] = {k: v.stats() for k, v in REMOTE_READERS.items()}
    receipt["elapsed_seconds"] = round(time.time() - t0, 1)

    with open(a.out, "w") as fh:
        json.dump(receipt, fh, indent=2, default=str)
    with open(a.out, "rb") as fh:
        receipt_sha = hashlib.sha256(fh.read()).hexdigest()

    print(f"RNA  slots: {[(k, v.get('verdict')) for k, v in rinfo['matrix_slots'].items()]}")
    print(f"ATAC slots: {[(k, v.get('verdict')) for k, v in ainfo['matrix_slots'].items()]}")
    print(f"pairing: {pairing['state']}  exact-shared {pairing['n_shared_exact']} "
          f"({pairing['frac_of_smaller_shared']:.3f} of smaller; threshold {HIGH_OVERLAP_MIN})")
    cd = pairing["composite_diagnostic"]
    if cd.get("computable"):
        print(f"composite DIAGNOSTIC (not authoritative): shared {cd['n_shared_composite']} "
              f"would_resolve={cd['would_resolve']}")
    if isinstance(mgd, dict) and "n_total_rna" in mgd:
        paired = mgd["n_total_paired_with_atac"]
        print(f"microglia: {mgd['n_total_rna']} total, paired "
              f"{'UNRESOLVED (null)' if paired is None else paired}, "
              f"median/donor {mgd['per_donor_quantiles']['0.5']:.0f}, "
              f"donors<50 {mgd['donors_below']['50']}")
    else:
        print(f"microglia: {mgd.get('status')}")
    print(f"probe_status: {receipt['probe_status']}  "
          f"QUALIFIED_FOR_PAIRED_USE={q['QUALIFIED_FOR_PAIRED_USE']}")
    print(f"receipt -> {a.out}  sha256 {receipt_sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
