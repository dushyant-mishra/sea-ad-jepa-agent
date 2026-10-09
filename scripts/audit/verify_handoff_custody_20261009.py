#!/usr/bin/env python3
"""Verify 2026-10-09 JEPA handoff custody assets and TD34 exact-panel genealogy.

This script performs byte-level checks only. It does not authorize target selection,
training, Stage 4, protected-data opening, representation freeze, or production EMA.
"""
from __future__ import annotations
import argparse, csv, hashlib, io, json, sys, zipfile
from pathlib import Path
import numpy as np

EXPECTED = {
    "FOUNDATION_CALIBRATION_BUNDLE_20260824.zip": {
        "bytes": 410278055,
        "sha256": "07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444",
    },
    "FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001": {
        "bytes": 303979881,
        "sha256": "b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e",
    },
    "FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002": {
        "bytes": 303979880,
        "sha256": "5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875",
    },
}
EXPECTED_REASSEMBLED = {
    "bytes": 607959761,
    "sha256": "63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7",
}
EXPECTED_OBS = {
    "bytes": 227532,
    "sha256": "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537",
    "shape": [42, 41238],
}
EXPECTED_PANELS = [
    "45414005bf84af3d85a2bdd5062f8c00b0163872a2f95848efaa8a55d89f4976",
    "c34ec8a677c688501a5b5a4a1ab2d2d02c06610fe9f42e4c94ea973acbe2ce44",
    "b7b863962dda2d68ef9c66b0b88d2ad7a0ea1578241b40dc25a3bfc2cf9b7e56",
    "df5aa4d410d6f51fbcf7796ced7093d2ad807cca398ce36d9e6512651ef6a0d5",
]
EXPECTED_VECTORS = {
    "sorted_common_support": "a4095c0e70141cacbcb940a2455480e9666452de4d41875360e9b4573c05a4f4",
    "td25_hash_ordered_17186": "48b311c8abe1c25912277c2c4aaafb595035649ab7e3929bed5655167bd8a310",
    "first_2048": "13616d28a3e0c1e517b8b465e19e4ce7d209fc9e796391c041519fdcf1542b12",
}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def hash_concat(paths: list[Path]) -> tuple[int, str]:
    h = hashlib.sha256()
    total = 0
    for path in paths:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
                h.update(chunk)
                total += len(chunk)
    return total, h.hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("asset_dir", nargs="?", default="/mnt/data")
    ap.add_argument("--json-out")
    args = ap.parse_args()
    root = Path(args.asset_dir)
    result = {"status": "PASS", "checks": {}, "authority": {
        "target_winner": "NONE",
        "representation_winner": "NONE",
        "real_training": "OFF",
        "stage4": "NOT_AUTHORIZED",
    }}

    for name, exp in EXPECTED.items():
        p = root / name
        got = {"exists": p.exists()}
        if p.exists():
            got["bytes"] = p.stat().st_size
            got["sha256"] = sha256_file(p)
            got["matches"] = got["bytes"] == exp["bytes"] and got["sha256"] == exp["sha256"]
        result["checks"][name] = got
        if not got.get("matches", False):
            result["status"] = "FAIL"

    part_paths = [
        root / "FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001",
        root / "FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002",
    ]
    nbytes, digest = hash_concat(part_paths)
    reassembly = {
        "bytes": nbytes,
        "sha256": digest,
        "matches_expected": nbytes == EXPECTED_REASSEMBLED["bytes"] and digest == EXPECTED_REASSEMBLED["sha256"],
    }
    result["checks"]["41k_reassembly"] = reassembly
    if not reassembly["matches_expected"]:
        result["status"] = "FAIL"

    ledger_path = root / "FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv"
    if ledger_path.exists():
        rows = list(csv.DictReader(io.StringIO(ledger_path.read_text(encoding="utf-8-sig"))))
        ledger = {r["file"]: r for r in rows}
        full = ledger.get("FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip")
        result["checks"]["41k_ledger"] = {
            "expected_reassembled_bytes": int(full["bytes"]) if full else None,
            "expected_reassembled_sha256": full["sha256"].lower() if full else None,
            "matches_streamed_reassembly": bool(full) and int(full["bytes"]) == nbytes and full["sha256"].lower() == digest,
        }
        if not result["checks"]["41k_ledger"]["matches_streamed_reassembly"]:
            result["status"] = "FAIL"

    cal = root / "FOUNDATION_CALIBRATION_BUNDLE_20260824.zip"
    with zipfile.ZipFile(cal) as z:
        obs_names = [n for n in z.namelist() if n.endswith("FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz")]
        if len(obs_names) != 1:
            raise RuntimeError(f"expected one observation-state NPZ, found {len(obs_names)}")
        obs_bytes = z.read(obs_names[0])
        obs_sha = hashlib.sha256(obs_bytes).hexdigest()
        npz = np.load(io.BytesIO(obs_bytes), allow_pickle=False)
        states = npz["states"]
        addresses = npz["molecular_address_index"].astype(np.int32)
        common = addresses[np.all(states == 1, axis=0)].astype(np.int32)
        common_sorted = np.sort(common).astype(np.int32)
        ordered = np.array(
            sorted(common.tolist(), key=lambda x: hashlib.sha256(f"TD25|{int(x)}".encode()).digest()),
            dtype=np.int32,
        )
        panel_hashes = [
            hashlib.sha256(ordered[i * 512:(i + 1) * 512].tobytes()).hexdigest()
            for i in range(4)
        ]
        vector_hashes = {
            "sorted_common_support": hashlib.sha256(common_sorted.tobytes()).hexdigest(),
            "td25_hash_ordered_17186": hashlib.sha256(ordered.tobytes()).hexdigest(),
            "first_2048": hashlib.sha256(ordered[:2048].tobytes()).hexdigest(),
        }
        td34 = {
            "member": obs_names[0],
            "member_bytes": len(obs_bytes),
            "member_sha256": obs_sha,
            "states_shape": list(states.shape),
            "common_support_count": int(common.size),
            "panel_hashes": panel_hashes,
            "vector_hashes": vector_hashes,
            "matches": (
                len(obs_bytes) == EXPECTED_OBS["bytes"]
                and obs_sha == EXPECTED_OBS["sha256"]
                and list(states.shape) == EXPECTED_OBS["shape"]
                and common.size == 17186
                and panel_hashes == EXPECTED_PANELS
                and vector_hashes == EXPECTED_VECTORS
            ),
        }
        result["checks"]["td34_exact_panel_binding"] = td34
        if not td34["matches"]:
            result["status"] = "FAIL"

    payload = json.dumps(result, indent=2, sort_keys=True)
    print(payload)
    if args.json_out:
        Path(args.json_out).write_text(payload + "\n", encoding="utf-8")
    return 0 if result["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
