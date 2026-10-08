#!/usr/bin/env python3
"""Explain the S174 rebuild's G1 shortfall. Read-only, TRAIN-only, inside the authorized rebuild.

G1 as frozen compared every rebuilt row with an independent re-read that maps genes by looking their
Ensembl ID up as a registry address ID. The frozen Stage81A2R provenance also maps some source IDs to a
DIFFERENT address (alternate-locus, antisense and readthrough IDs assigned to a canonical gene), which a
direct registry lookup cannot resolve. This script tests whether that accounts for every disagreement:

  E1  on addresses no remapped source ID reaches, the rebuilt cache equals the direct re-read exactly
  E2  on remapped addresses, each rebuilt count equals the physical count of the column whose var ID is the
      remapped source ID, checked directly from the provenance row (a path independent of the rebuild)
  E3  every G1 disagreement falls on a remapped address
If E1, E2 and E3 all hold, every rebuilt entry is accounted for; if any fails, the rebuild is wrong.
It changes nothing; it does not amend the frozen gate. That decision belongs to the owner.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "results/v77/S174_REBUILD_G1_EXPLANATION_V1.json"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> None:
    import h5py
    import pandas as pd
    from scipy import sparse
    RB = _load("s174_rebuild", HERE / "rebuild_s174_train_cache.py")
    P = _load("s174_probe", HERE / "probe_v77_s174_cache_axis.py")
    fr = json.loads(RB.FREEZE.read_text(encoding="utf-8"))
    _, _, fam, led, _ = RB.tables()
    prov = pd.read_csv(RB.PROVENANCE, usecols=["source_dataset_id", "source_exact_ensembl_id", "molecular_address_id",
                                               "molecular_address_index"], low_memory=False)
    reg = pd.read_csv(RB.REGISTRY, usecols=["molecular_address_index", "molecular_address_id"])
    ensg2addr = dict(zip(reg.molecular_address_id.astype(str), reg.molecular_address_index.astype(int)))
    rows, ok = [], dict(E1=True, E2=True, E3=True)
    for m in fr["matrices"]:
        mid, study, s = m["matrix_id"], m["study"], m["stem"]
        f = prov[prov.source_dataset_id.eq(RB.FAMILY[study])]
        remap = f[f.source_exact_ensembl_id.astype(str) != f.molecular_address_id.astype(str)]
        remap_id2addr = dict(zip(remap.source_exact_ensembl_id.astype(str), remap.molecular_address_index.astype(int)))
        ledger_ids = set(led.loc[led.matrix_id.astype(str).eq(mid), "source_exact_ensembl_id"].astype(str))
        remapped_addr = {a for i, a in remap_id2addr.items() if i not in ledger_ids}
        zn = np.load(RB.NEW_CACHE / f"{s}.counts.npz", allow_pickle=False)
        Xn = sparse.csr_matrix((zn["data"], zn["indices"], zn["indptr"]), shape=tuple(zn["shape"]))
        cells = np.load(RB.NEW_CACHE / f"{s}.meta.npz", allow_pickle=False)["cell_id"].astype(str)
        e1 = [0, 0]; e2 = [0, 0]; mism_total = mism_remapped = 0
        with h5py.File(RB.SOURCE / m["source"]["path"], "r") as h:
            var_ids = RB.h5_strings(h["var"], RB.VAR_ID_COLUMN[study])
            col2addr, excluded = RB.id_join_map(var_ids, fam[study]["id2addr"], ledger_ids)
            coll = RB.collision_addresses(var_ids, fam[study]["id2addr"], excluded)
            remap_cols = {j: remap_id2addr[str(v)] for j, v in enumerate(var_ids)
                          if str(v) in remap_id2addr and str(v) not in ledger_ids}
            obs = RB.h5_strings(h["obs"], "exp_component_name")
            where = {c: i for i, c in enumerate(obs)}
            node = h[m["slot"]]
            ip = node["indptr"]
            for r, cid in enumerate(cells):
                er = where[cid]
                lo, hi = int(ip[er]), int(ip[er + 1])
                idx, val = node["indices"][lo:hi], node["data"][lo:hi]
                pred_id, _, amb = P.predict(idx, val, var_ids, ensg2addr, {})
                new_row = {int(a): int(v) for a, v in zip(Xn.getrow(r).indices, Xn.getrow(r).data)}
                keys = (set(new_row) | {a for a in pred_id if a not in coll}) - amb - coll
                for k in keys:
                    same = new_row.get(k, 0) == pred_id.get(k, 0)
                    if not same:
                        mism_total += 1
                        mism_remapped += int(k in remapped_addr)
                    if k not in remapped_addr:
                        e1[0] += int(same); e1[1] += 1
                direct = {}
                for j, v in zip(idx, val):
                    a = remap_cols.get(int(j))
                    if a is not None and int(round(float(v))):
                        direct[a] = direct.get(a, 0) + int(round(float(v)))
                for a in remapped_addr & (set(direct) | set(new_row)):
                    e2[0] += int(new_row.get(a, 0) == direct.get(a, 0)); e2[1] += 1
        row = dict(matrix_id=mid, study=study, remapped_source_ids=len(remap_id2addr),
                   remapped_addresses_outside_ledger=len(remapped_addr),
                   E1_agreement=e1[0] / max(e1[1], 1), E1_entries=e1[1],
                   E2_agreement=(e2[0] / e2[1]) if e2[1] else None, E2_entries=e2[1],
                   g1_mismatches=mism_total, g1_mismatches_on_remapped_addresses=mism_remapped)
        ok["E1"] &= row["E1_agreement"] == 1.0
        ok["E2"] &= row["E2_agreement"] in (None, 1.0)
        ok["E3"] &= mism_total == mism_remapped
        rows.append(row)
        print(mid, {k: v for k, v in row.items() if k.startswith(("E", "g1"))}, flush=True)
    rec = dict(schema="S174_REBUILD_G1_EXPLANATION_V1",
               frozen_gate_G1="FAILED as frozen (SEA-AD 0.9990-0.9992); this record does not amend it",
               checks=ok, all_explained=all(ok.values()),
               reading=("if all_explained, every G1 disagreement is a source ID the frozen provenance assigns to "
                        "another gene's address, and every such entry equals its physical count"),
               matrices=rows, code_sha256=RB.sha256_file(Path(__file__)))
    RB.write_json(OUT, rec)
    print("EXPLANATION", ok, "ALL EXPLAINED" if rec["all_explained"] else "NOT EXPLAINED")


if __name__ == "__main__":
    main()
