#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os
from pathlib import Path

S174_HASHES = {
    "hvs_counts_example_1": "645df92bab23d274048c4d7fa15b55a13ec5c2f5daadde0531aa807d2712aade",
    "hvs_meta_example_1": "60147fc84f0c39003d3ce4c6609b0f7ceba95eec0d4bca71404ecaf21220fa9a",
    "hvs_counts_example_2": "6b1f86c3bbf375750e3335d1a3e598a8c3cc174e1cefb61acf7908642f8ebfe0",
}
TEXT_SUFFIXES = {'.py','.cpp','.json','.stdout','.out','.csv','.md','.txt','.yaml','.yml'}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def inspect_npz(path: Path):
    import numpy as np
    z = np.load(path, allow_pickle=True)
    out = {"keys": list(z.files)}
    for k in z.files:
        a = z[k]
        out.setdefault("arrays", {})[k] = {
            "shape": list(getattr(a, "shape", ())),
            "dtype": str(getattr(a, "dtype", "")),
        }
    if "global_row" in z.files:
        a = z["global_row"]
        out["global_row"] = {
            "n": int(a.size),
            "min": int(a.min()),
            "max": int(a.max()),
            "unique": int(len(set(map(int, a.tolist())))),
        }
    if "operator" in z.files:
        out["operator_unique_n"] = int(len(set(map(int, z["operator"].tolist()))))
    if "source_library" in z.files:
        out["source_library_unique_n"] = int(len(set(map(int, z["source_library"].tolist()))))
    return out

def main():
    root = Path(os.environ.get("S174_AUDIT_ROOT", "/mnt/data/s174_audit"))
    rar = Path(os.environ.get("S174_RAR", "/mnt/data/s174_library/s174_rebuilt_real_train_v1.rar"))
    td = root / "td"
    stage_zip = root / "stage81a3r_corrected_real_train.zip"
    td_zip = root / "JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip"
    discovery = root / "full104_discovery_subset.npz"

    required = [rar, stage_zip, td_zip, discovery, td / "td50_HVS.npz", td / "td50_NPH52.npz", td / "td50_SEA_AD.npz"]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise SystemExit("missing required paths: " + json.dumps(missing))

    assets = []
    for label, p in [
        ("s174_rar", rar),
        ("older_corrected_train_zip", stage_zip),
        ("td41_td58_zip", td_zip),
        ("discovery_subset_npz", discovery),
        ("td50_HVS", td / "td50_HVS.npz"),
        ("td50_NPH52", td / "td50_NPH52.npz"),
        ("td50_SEA_AD", td / "td50_SEA_AD.npz"),
    ]:
        assets.append({"label": label, "path": str(p), "bytes": p.stat().st_size, "sha256": sha256(p)})

    text_hits = []
    text_files = []
    for p in sorted(td.iterdir()):
        if not p.is_file() or p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        b = p.read_bytes()
        text_files.append({"name": p.name, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
        s = b.decode("utf-8", "ignore")
        for needle in ["S174", "s174", "S174_REBUILD_BUILD_RECEIPT_V1", *S174_HASHES.values()]:
            if needle in s:
                text_hits.append({"file": p.name, "needle": needle})

    td50 = {name: inspect_npz(td / name) for name in ["td50_HVS.npz", "td50_NPH52.npz", "td50_SEA_AD.npz"]}
    result = {
        "audit": "S174_TD_DOWNSTREAM_JOIN_V1",
        "physical_assets": assets,
        "recovered_td_text_file_count": len(text_files),
        "s174_join_marker_hits_in_recovered_td_text": text_hits,
        "s174_join_marker_hit_count": len(text_hits),
        "td50_introspection": td50,
        "stage_adjudication": {
            "TD56": "HISTORICAL_RELATIONAL_EVIDENCE__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY",
            "TD57B": "HISTORICAL_PROSPECTIVE_SUCCESS__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY",
            "TD59": "TD59_STATISTIC_REPRODUCED__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_PRODUCTION_LOCALITY_OR_TRAINING_AUTHORITY",
        },
        "terminal": "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED",
    }
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
