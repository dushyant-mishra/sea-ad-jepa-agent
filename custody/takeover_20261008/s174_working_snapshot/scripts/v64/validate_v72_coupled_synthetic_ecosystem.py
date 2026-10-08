#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path, gz=False):
    opener = gzip.open if gz else open
    with opener(path, "rt", newline="") as fh:
        return list(csv.DictReader(fh))


def validate(root: Path) -> list[str]:
    e = []
    obs, truth = root/"observable_raw", root/"hidden_truth"
    if not obs.is_dir(): return ["MISSING_OBSERVABLE_ROOT"]
    if not truth.is_dir(): e.append("MISSING_TRUTH_ROOT")

    for p in obs.rglob("*"):
        if p.is_file() and "truth" in p.name.lower():
            e.append(f"TRUTH_FIREWALL_PATH:{p.relative_to(obs)}")

    required = [
        "FULL104_like/rna_counts.npz",
        "NIH_CARD_STAGE4_like/metacells.npz",
        "NIH_CARD_STAGE4_like/pair_ledger.csv",
        "NIH_CARD_STAGE4_like/control_selection_audit.csv",
        "NIH_CARD_STAGE4_like/overlapping_5kb_windows.bed.csv",
        "GSE214979_SCENICPLUS_like/submitted_multiome.npz",
        "GSE214979_SCENICPLUS_like/fragments.tsv.gz",
        "GSE214979_SCENICPLUS_like/barcode_to_donor.csv",
        "MORABITO_like/rna.npz",
        "MORABITO_like/atac.npz",
        "SEAAD_MULTIOME_like/paired.npz",
        "PERTURBATION_like/cell_guide_umi_counts.npz",
        "SPATIAL_like/panel_counts.npz",
        "ECOSYSTEM_MANIFEST.json",
        "DIGESTS.json",
    ]
    for rel in required:
        if not (obs/rel).exists(): e.append(f"MISSING_REQUIRED:{rel}")

    if e:
        return e

    full = np.load(obs/"FULL104_like/rna_counts.npz", allow_pickle=False)
    if full["counts"].shape != full["availability"].shape:
        e.append("FULL104_AVAILABILITY_SHAPE_MISMATCH")
    if np.any(full["counts"][full["availability"] == 0] != 0):
        e.append("STRUCTURAL_MISSINGNESS_STORAGE_MISMATCH")
    if not np.any(full["availability"] == 0):
        e.append("NO_STRUCTURAL_MISSINGNESS_POSITIVE_CONTROL")

    pairs = read_csv(obs/"NIH_CARD_STAGE4_like/pair_ledger.csv")
    for r in pairs:
        if r["control_policy"] != "PROMOTER_FIXED_DISTAL_MATCHED_CONTROL":
            e.append(f"BAD_CONTROL_POLICY:{r['edge_id']}")
        ls, le = int(r["linked_start"]), int(r["linked_end"])
        cs, ce = int(r["control_start"]), int(r["control_end"])
        if not (ce <= ls or le <= cs):
            e.append(f"CONTROL_OVERLAPS_LINKED:{r['edge_id']}")
        ld, cd = abs(int(r["linked_distance"])), abs(int(r["control_distance"]))
        if abs(cd-ld) > max(.10*ld, 10_000):
            e.append(f"CONTROL_DISTANCE_MISMATCH:{r['edge_id']}")
        if r["linked_accessible"] != "1" or r["control_accessible"] != "1":
            e.append(f"ASYMMETRIC_ACCESSIBILITY:{r['edge_id']}")

    selection = read_csv(obs/"NIH_CARD_STAGE4_like/control_selection_audit.csv")
    if not any(r["status"] == "TRIM_NO_ADMISSIBLE_CONTROL" for r in selection):
        e.append("NO_TRIM_NO_ADMISSIBLE_CONTROL_POSITIVE_CONTROL")
    selected_ids = {r["edge_id"] for r in selection if r["status"] == "SELECTED"}
    ledger_ids = {r["edge_id"] for r in pairs}
    if selected_ids != ledger_ids:
        e.append("CONTROL_SELECTION_LEDGER_MISMATCH")

    wins = read_csv(obs/"NIH_CARD_STAGE4_like/overlapping_5kb_windows.bed.csv")
    multi_overlap = False
    for i,a in enumerate(wins):
        hits = 0
        as_, ae = int(a["start"]), int(a["end"])
        probe = (as_ + ae)//2
        for b in wins:
            if int(b["start"]) <= probe < int(b["end"]):
                hits += 1
        if hits > 1:
            multi_overlap = True
            break
    if not multi_overlap:
        e.append("NO_MULTI_OVERLAP_STAGE4_POSITIVE_CONTROL")

    bmap = read_csv(obs/"GSE214979_SCENICPLUS_like/barcode_to_donor.csv")
    suffix_donors = defaultdict(set)
    barcode_donor = {}
    for r in bmap:
        barcode_donor[r["barcode"]] = r["donor"]
        suffix_donors[r["barcode"].rsplit("-",1)[-1]].add(r["donor"])
    if not any(len(v) > 1 for v in suffix_donors.values()):
        e.append("NO_SUFFIX_COLLISION_POSITIVE_CONTROL")
    with gzip.open(obs/"GSE214979_SCENICPLUS_like/fragments.tsv.gz","rt") as fh:
        for i,line in enumerate(fh):
            f = line.rstrip("\n").split("\t")
            if len(f) < 4 or f[3] not in barcode_donor:
                e.append("FRAGMENT_BARCODE_NOT_IN_AUTHORITY")
                break
            if i > 5000:
                break

    mr = np.load(obs/"MORABITO_like/rna.npz", allow_pickle=False)
    ma = np.load(obs/"MORABITO_like/atac.npz", allow_pickle=False)
    if set(mr["cells"].tolist()) & set(ma["cells"].tolist()):
        e.append("MORABITO_FAKE_CELL_PAIRING")

    sea = np.load(obs/"SEAAD_MULTIOME_like/paired.npz", allow_pickle=False)
    if sea["rna"].shape[1] != sea["atac"].shape[1] or sea["rna"].shape[1] != len(sea["cells"]):
        e.append("SEAAD_PAIRING_AXIS_MISMATCH")

    digests = json.loads((obs/"DIGESTS.json").read_text())
    for rel, expected in digests.items():
        p = obs/rel
        if not p.exists():
            e.append(f"DIGEST_TARGET_MISSING:{rel}")
        elif sha256_file(p) != expected:
            e.append(f"DIGEST_MISMATCH:{rel}")

    manifest = json.loads((obs/"ECOSYSTEM_MANIFEST.json").read_text())
    expected_ds = {
        "FULL104_like","NIH_CARD_STAGE4_like","GSE214979_SCENICPLUS_like",
        "MORABITO_like","SEAAD_MULTIOME_like","PERTURBATION_like","SPATIAL_like"
    }
    if set(manifest.get("datasets", [])) != expected_ds:
        e.append("DATASET_SET_MISMATCH")
    if manifest.get("forbidden_truth_fields_present_in_manifest") is not False:
        e.append("OBSERVABLE_MANIFEST_TRUTH_EXPOSURE")

    return e


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    a = ap.parse_args(argv)
    errors = validate(Path(a.root))
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    print("PASS: V72 coupled synthetic ecosystem invariants")


if __name__ == "__main__":
    main()
