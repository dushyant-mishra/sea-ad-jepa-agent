#!/usr/bin/env python3
"""Audit diagnostic (read-only): detected-count changes by source in the replacement G6 output (ff4a21f9).

Not a biological analysis, and not a rerun of G6. Inputs are already-produced G6 material only:
- the metadata NPZ, read from a SHA-256-verified copy outside the immutable namespace;
- MANIFEST.json, for the per-matrix mapping diagnostics G6 itself recorded;
- G6_RECEIPT.json, for its detected_changed_rows.

The five namespace files are hashed before and after against G6_NAMESPACE_SHA256.txt, so the diagnostic proves it
changed nothing.

Definitions (G6 code at ff4a21f9, materialize_td_relational_corrected_sampleA_v2.py):
  detected_corrected (HVS/SEA)  = count of nonzero physical entries whose column maps to a molecular address
  detected_historical           = TD50 historical sentinel detected count for the row's global_row
  NPH52 pass-through            : detected_corrected := detected_historical, so a change is impossible by construction
  detected_changed_rows         = sum(detected_historical != detected_corrected)

Usage: python detected_count_source_breakdown.py <G6 namespace dir> <run_record dir> <audit out dir> [<Macha freeze>]
The optional Macha freeze (PR259 S174_REBUILD_FREEZE_V1.json, pinned 240b2b71...) adds its per-matrix
column-mapping fields summarized by source. These are descriptive context, not a tested mechanism.
"""
import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

import numpy as np

META = "TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def recorded_hashes(run_record: Path) -> dict:
    out = {}
    for line in (run_record / "G6_NAMESPACE_SHA256.txt").read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 2 and len(parts[0]) == 64:
            out[parts[1].lstrip("*")] = parts[0]
    return out


def namespace_state(ns: Path) -> dict:
    return {p.name: sha(p) for p in sorted(ns.iterdir()) if p.is_file()}


def q(v: np.ndarray) -> dict:
    if v.size == 0:
        return {"n": 0}
    qs = [0.0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1.0]
    return {"n": int(v.size), "mean": float(v.mean()),
            **{f"q{int(p * 100):02d}": float(np.quantile(v, p)) for p in qs}}


def main() -> None:
    ns, run_record, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    recorded = recorded_hashes(run_record)
    before = namespace_state(ns)
    if before != recorded:
        raise SystemExit(f"STOP: namespace differs from the post-run record before the diagnostic: {before} vs {recorded}")

    copy = out / ("COPY_" + META)
    shutil.copyfile(ns / META, copy)
    if sha(copy) != recorded[META]:
        raise SystemExit("STOP: metadata copy hash differs from the recorded G6 hash")
    with np.load(copy, allow_pickle=False) as z:
        m = {k: np.asarray(z[k]) for k in z.files}
    receipt = json.loads((ns / "G6_RECEIPT.json").read_text(encoding="utf-8"))
    manifest = json.loads((ns / "MANIFEST.json").read_text(encoding="utf-8"))

    source = m["source"].astype(str)
    det_c = m["detected_corrected"].astype(np.int64)
    det_h = m["detected_historical"].astype(np.int64)
    changed = det_c != det_h
    delta = det_c - det_h
    by_source = {}
    for s in sorted(set(source.tolist())):
        sel = source == s
        ch = sel & changed
        d = delta[ch]
        rel = d / np.maximum(det_h[ch], 1)
        by_source[s] = {
            "rows": int(sel.sum()), "changed_rows": int(ch.sum()), "unchanged_rows": int((sel & ~changed).sum()),
            "changed_delta_corrected_minus_historical": q(d.astype(float)),
            "changed_relative_delta": q(rel.astype(float)),
            "changed_sign": {"corrected_lower": int((d < 0).sum()), "corrected_higher": int((d > 0).sum())},
            "detected_historical_all_rows": q(det_h[sel].astype(float)),
            "detected_corrected_all_rows": q(det_c[sel].astype(float)),
        }
    unchanged_sea = np.where((source == "SEA_AD") & ~changed)[0]
    exceptions = [{"sample_row_position": int(i), "global_row": int(m["global_row"][i]), "operator_index": int(m["operator"][i]),
                   "cell_id": str(m["cell_id"][i]), "detected_historical": int(det_h[i]), "detected_corrected": int(det_c[i]),
                   "source_library": int(m["source_library"][i])} for i in unchanged_sea]
    # G6's own per-matrix identifier-mapping diagnostics (recorded in MANIFEST.json), aggregated by study
    excluded_by_study = {}
    for d in manifest["mapping_diagnostics"]:
        agg = excluded_by_study.setdefault(d["study"], Counter())
        agg.update(d["excluded"])
    sea = source == "SEA_AD"
    nonpos = np.where(sea & (delta <= 0))[0]
    nonpositive_rows = [{"sample_row_position": int(i), "global_row": int(m["global_row"][i]),
                         "operator_index": int(m["operator"][i]), "detected_historical": int(det_h[i]),
                         "detected_corrected": int(det_c[i]), "delta": int(delta[i]),
                         "source_library": int(m["source_library"][i])} for i in nonpos]
    rank = lambda v: np.argsort(np.argsort(v, kind="mergesort"), kind="mergesort").astype(float)
    spearman = float(np.corrcoef(rank(delta[sea]), rank(det_h[sea]))[0, 1]) if sea.sum() > 2 else None
    freeze_summary = None
    if len(sys.argv) > 4:
        fz_path = Path(sys.argv[4])
        fz = json.loads(fz_path.read_text(encoding="utf-8"))
        used = set(zip(source.tolist(), m["operator"].astype(int).tolist()))
        freeze_summary = {"freeze_sha256": sha(fz_path), "by_study": {}}
        for mat in fz["matrices"]:
            st = str(mat.get("study"))
            agg = freeze_summary["by_study"].setdefault(st, Counter())
            agg["matrices"] += 1
            for k in ("var_features", "mapped_columns", "collision_addresses", "old_positional_blocked",
                      "mapped_columns_whose_address_differs_from_the_old_positional_map", "cells"):
                agg[k] += int(mat.get(k) or 0)
            for k, v in (mat.get("excluded") or {}).items():
                agg["excluded_" + k] += int(v)
        freeze_summary["by_study"] = {k: dict(v) for k, v in freeze_summary["by_study"].items()}
    after = namespace_state(ns)
    copy.unlink()
    res = {
        "schema": "TD_G6_FF4A21F9_DETECTED_COUNT_SOURCE_BREAKDOWN_AUDIT_V1",
        "label": "POST_EXECUTION_AUDIT_DIAGNOSTIC__READ_ONLY__NOT_BIOLOGY__NO_G7_AUTHORITY",
        "inputs": {"meta_npz_sha256": recorded[META], "receipt_sha256": recorded["G6_RECEIPT.json"],
                   "manifest_sha256": recorded["MANIFEST.json"], "read_from": "a SHA-256-verified copy (deleted after use)"},
        "definitions": __doc__.split("Definitions")[1].split("Usage")[0].strip(),
        "receipt_detected_changed_rows": receipt["detected_changed_rows"],
        "recomputed_detected_changed_rows": int(changed.sum()),
        "recomputed_equals_receipt": int(changed.sum()) == receipt["detected_changed_rows"],
        "by_source": by_source,
        "sea_ad_unchanged_rows": exceptions,
        "g6_mapping_diagnostics_excluded_by_study": {k: dict(v) for k, v in excluded_by_study.items()},
        "sea_ad_nonpositive_delta_rows": nonpositive_rows,
        "sea_ad_spearman_delta_vs_detected_historical": spearman,
        "macha_freeze_mapping_fields_by_study": freeze_summary,
        "namespace_hashes_before": before, "namespace_hashes_after": after,
        "namespace_unchanged": before == after == recorded,
    }
    (out / "DETECTED_COUNT_SOURCE_BREAKDOWN.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("receipt_detected_changed_rows", "recomputed_detected_changed_rows",
                                           "namespace_unchanged")}, indent=1))
    for s, v in by_source.items():
        print(s, "rows", v["rows"], "changed", v["changed_rows"], "unchanged", v["unchanged_rows"],
              "delta", {k: v["changed_delta_corrected_minus_historical"].get(k) for k in ("q00", "q50", "q100", "mean")},
              "sign", v["changed_sign"])
    print("SEA_AD unchanged rows:", exceptions)
    print("excluded by study:", res["g6_mapping_diagnostics_excluded_by_study"])


if __name__ == "__main__":
    main()
