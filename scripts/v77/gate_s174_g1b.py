#!/usr/bin/env python3
"""S174 rebuild, successor gate G1b. The frozen G1 FAILED as pre-registered and stays failed; G1b is a
new gate, authorized by the owner on 2026-10-07, frozen before it is run, and decides whether the rebuilt
cache may be used for the V77 replays.

G1b passes only if every requirement holds exactly:
  R1  every HVS entry matches the simple independent ID re-read exactly
  R2  every SEA-AD entry on an address outside the remap set matches the re-read exactly
  R3  every remapped case outside the collision ledger equals the physical count of the source column that
      the frozen provenance assigns to that address
  R4  100% of disagreements with the simple re-read lie in the pre-existing remap set
  R5  zero unexplained discrepancies (R1-R4 and R6 hold, and the re-read reaches no address twice outside
      the collision policy)
  R6  collision-excluded genes stay excluded, never summed: at every collision address the rebuilt value is
      exactly the count of the single non-excluded column mapped there, or zero
  R7  the rebuilt cache's bytes are identical to the artifact the build receipt describes
The remap set is fixed from the frozen provenance file alone: source Ensembl ID different from the address
ID. Remapped IDs that the collision ledger excludes are checked under R6, not R3.
The comparison space for R1, R2 and R4 is the union of addresses either side holds as nonzero, minus
collision addresses (R6) and minus addresses the re-read reaches from two columns (R5).

MODES
  freeze  no count is read: the remap set, the cache hashes, the definition and the code SHA
  run     refuses unless the freeze is committed and the code and cache are unchanged; then checks
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FREEZE = ROOT / "results/v77/S174_REBUILD_G1B_FREEZE_V1.json"
RESULT = ROOT / "results/v77/S174_REBUILD_G1B_RESULT_V1.json"
REQUIREMENTS = {
    "R1": "every HVS entry matches the simple independent ID re-read exactly",
    "R2": "every SEA-AD entry outside the remap set matches the re-read exactly",
    "R3": "every remapped case outside the ledger equals the physical count of its provenance-assigned source column",
    "R4": "100% of disagreements with the simple re-read lie in the pre-existing remap set",
    "R5": "zero unexplained discrepancies",
    "R6": "collision-excluded genes stay excluded, never summed",
    "R7": "rebuilt cache bytes identical to the built artifact",
}


# ------------------------------------------------------------------------------- pure logic

def check_cell(new_row: dict, reread: dict, reread_amb: set, coll_addr: set, remapped_addr: set,
               remap_direct: dict, collision_expected: dict) -> dict:
    """Counters for one cell; see the module docstring for the definitions."""
    space = (set(new_row) | set(reread)) - reread_amb - coll_addr
    dis = {k for k in space if new_row.get(k, 0) != reread.get(k, 0)}
    remap_keys = remapped_addr & (set(new_row) | set(remap_direct))
    return dict(
        entries=len(space),
        disagreements=len(dis),
        disagreements_outside_remap=len(dis - remapped_addr),
        entries_outside_remap=len(space - remapped_addr),
        remap_checked=len(remap_keys),
        remap_wrong=sum(new_row.get(a, 0) != remap_direct.get(a, 0) for a in remap_keys),
        collision_checked=len(coll_addr),
        collision_wrong=sum(new_row.get(a, 0) != collision_expected.get(a, 0) for a in coll_addr),
        reread_ambiguity_outside_collisions=len(reread_amb - coll_addr))


def add(total: dict, part: dict) -> dict:
    for k, v in part.items():
        total[k] = total.get(k, 0) + v
    return total


def requirements_hold(per_matrix: list[dict], hashes_equal: bool) -> dict:
    """per_matrix: [{'study': ..., **summed check_cell counters}]"""
    hvs = [m for m in per_matrix if m["study"] == "HVS"]
    sea = [m for m in per_matrix if m["study"] == "SEA_AD"]
    r = dict(
        R1=bool(hvs) and all(m["disagreements"] == 0 and m["reread_ambiguity_outside_collisions"] == 0 for m in hvs),
        R2=bool(sea) and all(m["disagreements_outside_remap"] == 0 for m in sea),
        R3=all(m["remap_wrong"] == 0 for m in per_matrix),
        R4=all(m["disagreements_outside_remap"] == 0 for m in per_matrix),
        R6=all(m["collision_wrong"] == 0 for m in per_matrix),
        R7=bool(hashes_equal))
    r["R5"] = all(r[k] for k in ("R1", "R2", "R3", "R4", "R6")) and all(
        m["reread_ambiguity_outside_collisions"] == 0 for m in per_matrix)
    return r


# ---------------------------------------------------------------------------------- helpers

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def git(*a) -> str:
    return subprocess.run(["git", *a], capture_output=True, text=True, cwd=ROOT).stdout.strip()


def remap_table(RB):
    import pandas as pd
    prov = pd.read_csv(RB.PROVENANCE, usecols=["source_dataset_id", "source_exact_ensembl_id", "molecular_address_id",
                                               "molecular_address_index"], low_memory=False)
    out = {}
    for study, fam in RB.FAMILY.items():
        f = prov[prov.source_dataset_id.eq(fam)]
        rm = f[f.source_exact_ensembl_id.astype(str) != f.molecular_address_id.astype(str)]
        out[study] = dict(zip(rm.source_exact_ensembl_id.astype(str), rm.molecular_address_index.astype(int)))
    return out


# ------------------------------------------------------------------------------------ modes

def freeze() -> None:
    RB = _load("s174_rebuild", HERE / "rebuild_s174_train_cache.py")
    bd = json.loads(RB.BUILD.read_text(encoding="utf-8"))
    remap = remap_table(RB)
    _, _, _, led, _ = RB.tables()
    per = []
    for m in json.loads(RB.FREEZE.read_text(encoding="utf-8"))["matrices"]:
        ledger_ids = set(led.loc[led.matrix_id.astype(str).eq(m["matrix_id"]), "source_exact_ensembl_id"].astype(str))
        ids = remap[m["study"]]
        per.append(dict(matrix_id=m["matrix_id"], study=m["study"], remapped_ids=len(ids),
                        remapped_ids_in_ledger=sum(i in ledger_ids for i in ids),
                        remapped_ids_checked_under_R3=sum(i not in ledger_ids for i in ids)))
    cache_now = {b["stem"]: dict(counts=RB.sha256_file(RB.NEW_CACHE / f"{b['stem']}.counts.npz"),
                                 meta=RB.sha256_file(RB.NEW_CACHE / f"{b['stem']}.meta.npz")) for b in bd["h5_shards"]}
    built = {b["stem"]: dict(counts=b["counts_sha256"], meta=b["meta_sha256"]) for b in bd["h5_shards"]}
    if cache_now != built:
        sys.exit("STOP: the rebuilt cache already differs from its build receipt")
    remap_listing = sorted(f"{s}|{i}|{a}" for s, d in remap.items() for i, a in d.items())
    rec = dict(
        schema="S174_REBUILD_G1B_FREEZE_V1", status="FROZEN__NO_COUNT_READ",
        authorization=("owner, 2026-10-07: frozen G1 failed as pre-registered and stays failed; successor gate G1b "
                       "frozen prospectively; if the explanatory checks pass G1b exactly, the rebuilt cache is "
                       "authorized for the planned V77 replays. The 353 historical-ID-to-different-symbol mappings are "
                       "followed as frozen and flagged separately; nothing is tuned on replay outcomes"),
        g1_as_frozen="FAILED (SEA-AD 0.9990-0.9992); not amended",
        requirements=REQUIREMENTS,
        comparison_space=("union of addresses either side holds as nonzero, minus collision addresses (checked under R6) "
                          "and minus addresses the re-read reaches from two columns (R5)"),
        remap_set=dict(definition="frozen provenance rows whose source Ensembl ID differs from the address ID",
                       counts={s: len(d) for s, d in remap.items()},
                       listing_sha256=hashlib.sha256("\n".join(remap_listing).encode()).hexdigest(),
                       provenance_sha256=RB.sha256_file(RB.PROVENANCE)),
        per_matrix=per,
        rebuilt_cache=dict(build_receipt_sha256=RB.sha256_file(RB.BUILD), shards=built),
        code=dict(path="scripts/v77/gate_s174_g1b.py", sha256=RB.sha256_file(HERE / "gate_s174_g1b.py"),
                  head=git("rev-parse", "HEAD")))
    RB.write_json(FREEZE, rec)
    print("G1b frozen", FREEZE, "| remap counts", rec["remap_set"]["counts"])


def run() -> None:
    import h5py
    import numpy as np
    import pandas as pd
    from scipy import sparse
    RB = _load("s174_rebuild", HERE / "rebuild_s174_train_cache.py")
    P = _load("s174_probe", HERE / "probe_v77_s174_cache_axis.py")
    fz = json.loads(FREEZE.read_text(encoding="utf-8"))
    if not git("ls-files", "--", FREEZE.relative_to(ROOT).as_posix()):
        sys.exit("STOP: the G1b freeze is not committed")
    if git("status", "--porcelain", "--untracked-files=no", "--", "scripts/v77/gate_s174_g1b.py") or \
            RB.sha256_file(HERE / "gate_s174_g1b.py") != fz["code"]["sha256"]:
        sys.exit("STOP: the gate script differs from the frozen one")
    hashes_equal = all(RB.sha256_file(RB.NEW_CACHE / f"{s}.counts.npz") == h["counts"] and
                       RB.sha256_file(RB.NEW_CACHE / f"{s}.meta.npz") == h["meta"]
                       for s, h in fz["rebuilt_cache"]["shards"].items())
    remap = remap_table(RB)
    _, _, fam, led, _ = RB.tables()
    reg = pd.read_csv(RB.REGISTRY, usecols=["molecular_address_index", "molecular_address_id"])
    ensg2addr = dict(zip(reg.molecular_address_id.astype(str), reg.molecular_address_index.astype(int)))
    per = []
    for m in json.loads(RB.FREEZE.read_text(encoding="utf-8"))["matrices"]:
        mid, study, s = m["matrix_id"], m["study"], m["stem"]
        ledger_ids = set(led.loc[led.matrix_id.astype(str).eq(mid), "source_exact_ensembl_id"].astype(str))
        rm = {i: a for i, a in remap[study].items() if i not in ledger_ids}
        remapped_addr = set(rm.values())
        zn = np.load(RB.NEW_CACHE / f"{s}.counts.npz", allow_pickle=False)
        Xn = sparse.csr_matrix((zn["data"], zn["indices"], zn["indptr"]), shape=tuple(zn["shape"]))
        cells = np.load(RB.NEW_CACHE / f"{s}.meta.npz", allow_pickle=False)["cell_id"].astype(str)
        total = {}
        with h5py.File(RB.SOURCE / m["source"]["path"], "r") as h:
            var_ids = RB.h5_strings(h["var"], RB.VAR_ID_COLUMN[study])
            col2addr, excluded = RB.id_join_map(var_ids, fam[study]["id2addr"], ledger_ids)
            coll = RB.collision_addresses(var_ids, fam[study]["id2addr"], excluded)
            keep_at = {}
            for j, a in col2addr.items():
                if a in coll:
                    keep_at.setdefault(a, []).append(j)
            remap_cols = {j: rm[str(v)] for j, v in enumerate(var_ids) if str(v) in rm}
            obs = RB.h5_strings(h["obs"], "exp_component_name")
            where = {c: i for i, c in enumerate(obs)}
            node = h[m["slot"]]
            ip = node["indptr"]
            for r, cid in enumerate(cells):
                er = where[cid]
                lo, hi = int(ip[er]), int(ip[er + 1])
                idx = np.asarray(node["indices"][lo:hi]); val = np.asarray(node["data"][lo:hi])
                reread, _, amb = P.predict(idx, val, var_ids, ensg2addr, {})
                cnt = {int(j): int(round(float(v))) for j, v in zip(idx, val)}
                new_row = {int(a): int(v) for a, v in zip(Xn.getrow(r).indices, Xn.getrow(r).data)}
                direct = {}
                for j, a in remap_cols.items():
                    if cnt.get(j, 0):
                        direct[a] = direct.get(a, 0) + cnt[j]
                coll_expected = {a: sum(cnt.get(j, 0) for j in keep_at.get(a, [])) for a in coll}
                add(total, check_cell(new_row, reread, amb, coll, remapped_addr, direct, coll_expected))
        per.append(dict(matrix_id=mid, study=study, cells=int(len(cells)), **total))
        print(mid, {k: total[k] for k in ("entries", "disagreements", "disagreements_outside_remap", "remap_checked",
                                          "remap_wrong", "collision_wrong", "reread_ambiguity_outside_collisions")},
              flush=True)
    req = requirements_hold(per, hashes_equal)
    rec = dict(schema="S174_REBUILD_G1B_RESULT_V1", freeze=dict(path=FREEZE.relative_to(ROOT).as_posix(),
                                                                 sha256=RB.sha256_file(FREEZE)),
               requirements=req, G1b_pass=all(req.values()), per_matrix=per,
               consequence=("rebuilt cache AUTHORIZED for the planned V77 replays" if all(req.values()) else
                            "rebuilt cache NOT authorized"),
               g1_as_frozen="FAILED; unchanged", code_sha256=RB.sha256_file(HERE / "gate_s174_g1b.py"),
               head=git("rev-parse", "HEAD"))
    RB.write_json(RESULT, rec)
    print("G1b", req, "PASS" if rec["G1b_pass"] else "FAIL")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("freeze", "run"))
    a = ap.parse_args()
    freeze() if a.mode == "freeze" else run()


if __name__ == "__main__":
    main()
