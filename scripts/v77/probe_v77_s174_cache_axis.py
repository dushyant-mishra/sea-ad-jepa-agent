#!/usr/bin/env python3
"""S174 axis probe. Does the Stage81A3R real-TRAIN cache hold each gene's count at that gene's
address, or at the address the harmonized-rank provenance assigns to the physical column?

READ-ONLY, TRAIN-only, pathology-blind. A small probe authorized by the owner on 2026-10-07, not a
rebuild. Two modes:
  prepare  value-blind. Selects the cells from the cache's cell and donor identifiers only, checks
           that every donor is TRAIN, resolves the markers in the registry, hashes every input and
           writes the pre-registration. It reads no count.
  run      reads the frozen cells' rows from the cache and from the source H5AD, compares them and
           classifies the result with the rule below.
From an H5AD it reads obs/exp_component_name (to find each cell), the var Ensembl column and the count
rows of the selected cells. Nothing else, and never a pathology field.

HYPOTHESES for a cache entry (cell, address a):
  ID   the entry is the count of the gene whose Ensembl ID maps to a (no defect)
  POS  the entry is the count of the physical column p with source_to_address[p] == a, where
       source_to_address is the builder's own map: the family provenance keyed by
       source_feature_index, without the builder's collision-blocked features (S174)
DECISION RULE, declared before any count is read:
  S174_VALUE_VERIFIED                 POS agreement >= 0.99 and ID agreement < 0.50 in every matrix
  CACHE_CORRECT__S174_NEEDS_REVISION  ID agreement >= 0.99 and POS agreement < 0.50 in every matrix
  INCONCLUSIVE__STOP                  anything else
0.99 is the decoder's agreement floor fixed on 2026-09-27; 0.50 is declared here. Agreement is exact
integer equality over the union of addresses that the cache or the hypothesis holds as nonzero,
excluding addresses the ID map reaches from more than one physical column. The decoder cross-check
(the cache decoded by the 2026-09-27 decoder, against ID) is reported beside the verdict, not in it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

SOURCE = Path("D:/Jepa project")
CACHE = SOURCE / "data/cache/stage81a3r_corrected_real_train"
REGISTRY = SOURCE / "results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv"
PROVENANCE = SOURCE / "results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz"
ASSETS = SOURCE / "results/v4/stage81a2_canonical_asset_registry.csv"
SEMANTICS = SOURCE / "results/v4/stage81a2_matrix_semantics_contract.csv"
SPLIT = SOURCE / "results/v4/stage81a2_split_registry.csv"
LEDGER = Path("D:/Jepa project-stage81a3r-20260814/results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz")
DECODERS = Path("D:/jepa_v5_outputs_20260925/l4_decoder_all")
DECODER_JSON = DECODERS / "FULL104_LEVEL4_COLUMN_DECODER_V1.json"

PROBE_SEED = 20261007
CELLS_PER_MATRIX = 12
MATRICES = ("HVS::c5e9db26-7b51-4290-b721-dd540ac906b1", "sea_ad_mtg_rna_final_2026", "sea_ad_pfc_a9_rna_final_2026")
MARKERS = ("SNAP25", "SLC17A7", "GAD1", "MBP", "PLP1", "MOBP", "GFAP", "AQP4", "P2RY12", "CSF1R", "CX3CR1",
           "PDGFRA", "CLDN5", "APOE")
FLOOR = 0.99
OTHER_CEILING = 0.50
VERDICTS = ("S174_VALUE_VERIFIED", "CACHE_CORRECT__S174_NEEDS_REVISION", "INCONCLUSIVE__STOP")


# --------------------------------------------------------------------------- pure decision logic

def predict(indices, values, var_ensg, ensg2addr: dict, s2a: dict):
    """The two hypotheses' cache rows for one source row, and the addresses the ID map reaches twice."""
    pred_id, pred_pos, hits = {}, {}, {}
    for j, v in zip(indices, values):
        j, v = int(j), int(round(float(v)))
        if v == 0:
            continue
        a = ensg2addr.get(str(var_ensg[j]))
        if a is not None:
            pred_id[a] = pred_id.get(a, 0) + v
            hits[a] = hits.get(a, 0) + 1
        b = s2a.get(j)
        if b is not None:
            pred_pos[b] = v
    return pred_id, pred_pos, {a for a, n in hits.items() if n > 1}


def agreement(cache_row: dict, pred: dict, excluded: set, allowed: set) -> tuple[int, int]:
    """Exact agreement over the addresses either side holds as nonzero, restricted to the addresses
    the cache could hold at all (the image of the builder's map), minus excluded ones."""
    keys = ((set(cache_row) | set(pred)) & allowed) - excluded
    agree = sum(int(cache_row.get(k, 0) == pred.get(k, 0)) for k in keys)
    return agree, len(keys)


def classify(per_matrix: list[dict]) -> str:
    """per_matrix: [{'agree_id': frac, 'agree_pos': frac}, ...]"""
    if per_matrix and all(m["agree_pos"] >= FLOOR and m["agree_id"] < OTHER_CEILING for m in per_matrix):
        return VERDICTS[0]
    if per_matrix and all(m["agree_id"] >= FLOOR and m["agree_pos"] < OTHER_CEILING for m in per_matrix):
        return VERDICTS[1]
    return VERDICTS[2]


# ------------------------------------------------------------------------------------- helpers

def sha256_file(p: Path, chunk: int = 1 << 24) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def write_json(path: Path, obj) -> None:
    """UTF-8 with LF line endings. Path.write_text(newline=...) needs Python 3.10; CI runs 3.9."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, indent=1) + "\n")


def git(*a) -> str:
    return subprocess.run(["git", *a], capture_output=True, text=True, cwd=ROOT).stdout.strip()


def cache_stem(matrix_id: str) -> str:
    return hashlib.sha256(f"corrected|{matrix_id}".encode()).hexdigest()[:16]


def h5_strings(grp, name: str) -> np.ndarray:
    import h5py
    if name == "_index":
        name = grp.attrs.get("_index", "_index")
        name = name.decode() if isinstance(name, bytes) else str(name)
    obj = grp[name]
    if isinstance(obj, h5py.Group):
        cats, codes = obj["categories"][:], obj["codes"][:]
        vals = cats[codes]
    else:
        vals = obj[:]
    return np.array([v.decode() if isinstance(v, bytes) else str(v) for v in vals], dtype=object)


def load_maps(matrix_id: str, study: str):
    import pandas as pd
    reg = pd.read_csv(REGISTRY, usecols=["molecular_address_index", "molecular_address_id", "symbol"])
    ensg2addr = dict(zip(reg.molecular_address_id.astype(str), reg.molecular_address_index.astype(int)))
    addr2sym = dict(zip(reg.molecular_address_index.astype(int), reg.symbol.astype(str)))
    prov = pd.read_csv(PROVENANCE, usecols=["source_dataset_id", "source_feature_index", "molecular_address_index"],
                       low_memory=False)
    fam = prov[prov.source_dataset_id.eq("HVS_COMMON" if study == "HVS" else "SEA_AD_COMMON")]
    led = pd.read_csv(LEDGER, usecols=["matrix_id", "source_feature_index"], low_memory=False)
    blocked = set(led.loc[led.matrix_id.astype(str).eq(matrix_id), "source_feature_index"].astype(int))
    fam = fam[~fam.source_feature_index.astype(int).isin(blocked)]
    s2a = dict(zip(fam.source_feature_index.astype(int), fam.molecular_address_index.astype(int)))
    return reg, ensg2addr, addr2sym, s2a, len(blocked)


def asset_rows():
    import pandas as pd
    a, s = pd.read_csv(ASSETS), pd.read_csv(SEMANTICS)
    out = {}
    for mid in MATRICES:
        r = a[a.dataset_id.eq(mid)].iloc[0]
        out[mid] = dict(study=str(r.study_id), h5ad=str(r.matrix_path_or_object),
                        slot=str(s[s.dataset_id.eq(mid)].matrix_slot.iloc[0]))
    return out


# --------------------------------------------------------------------------------------- modes

def prepare(out: Path) -> None:
    import pandas as pd
    dec = json.loads(DECODER_JSON.read_text(encoding="utf-8"))["matrices"]
    split = pd.read_csv(SPLIT)
    tr = split[(split.split_domain == "foundation") & (split.split == "train")]
    train = {str(s): {str(v).split("::", 1)[-1] for v in g.canonical_person_id} for s, g in tr.groupby("study_id")}
    reg = pd.read_csv(REGISTRY, usecols=["molecular_address_index", "molecular_address_id", "symbol"])
    markers = []
    for sym in MARKERS:
        hit = reg[reg.symbol.astype(str).eq(sym)]
        markers.append(dict(symbol=sym, ensembl=str(hit.molecular_address_id.iloc[0]) if len(hit) else None,
                            address=int(hit.molecular_address_index.iloc[0]) if len(hit) else None,
                            registry_rows=int(len(hit))))
    assets = asset_rows()
    mats = []
    for k, mid in enumerate(MATRICES):
        info, stem = assets[mid], cache_stem(mid)
        meta_p, counts_p = CACHE / f"{stem}.meta.npz", CACHE / f"{stem}.counts.npz"
        meta = np.load(meta_p, allow_pickle=False)
        cell_id, donor_id = meta["cell_id"].astype(str), meta["donor_id"].astype(str)
        rows = sorted(np.random.default_rng([PROBE_SEED, k]).choice(len(cell_id), CELLS_PER_MATRIX, replace=False).tolist())
        donors = [donor_id[r] for r in rows]
        h5 = SOURCE / info["h5ad"]
        dec_key = mid
        mats.append(dict(
            matrix_id=mid, study=info["study"], cache_stem=stem,
            cache_files={meta_p.name: sha256_file(meta_p), counts_p.name: sha256_file(counts_p)},
            cache_rows_total=int(len(cell_id)), selected_cache_rows=rows,
            cell_ids=[cell_id[r] for r in rows], donor_ids=donors,
            all_donors_train=bool(all(d in train.get(info["study"], set()) for d in donors)),
            h5ad=dict(path=info["h5ad"], bytes=h5.stat().st_size, sha256=sha256_file(h5)),
            count_slot=info["slot"], var_ensembl_column=dec[dec_key]["source_ensembl_column"],
            decoder=dict(file=f"decoder_{mid.replace('::', '__')}.npz",
                         sha256=sha256_file(DECODERS / f"decoder_{mid.replace('::', '__')}.npz"),
                         status=dec[dec_key]["status"])))
        print(mid, "rows", rows, "train", mats[-1]["all_donors_train"], flush=True)
    if not all(m["all_donors_train"] for m in mats):
        sys.exit("STOP: a selected cell's donor is not TRAIN")
    rec = dict(
        schema="V77_S174_CACHE_AXIS_PROBE_PREREGISTRATION_V1",
        status="PROSPECTIVE__NO_COUNT_READ",
        authorization=("owner, 2026-10-07: small read-only TRAIN probe; a few dozen cells; 1 HVS + 2 SEA-AD "
                       "matrices; cells on the V77 calibration path; cache against direct H5AD reads by Ensembl ID; "
                       "named markers; no pathology, TEST, mutation or training; full rebuild NOT authorized"),
        why_these_cells=("every cache row is a cell the V77 real calibration read (load_real reads every shard), so "
                         "any cache row is on the calibration path; rows are a seeded draw over row positions"),
        hypotheses=dict(ID="the entry is the count of the gene whose Ensembl ID maps to the address",
                        POS=("the entry is the count of the physical column the builder's source_feature_index map "
                             "sends to the address (S174)")),
        decision_rule={VERDICTS[0]: f"POS >= {FLOOR} and ID < {OTHER_CEILING} in every matrix",
                       VERDICTS[1]: f"ID >= {FLOOR} and POS < {OTHER_CEILING} in every matrix",
                       VERDICTS[2]: "anything else"},
        rule_reading=("'agree' means the cache equals the H5AD count of the same gene by Ensembl ID with no decoding "
                      "step; the decoder cross-check is reported beside the verdict, not in it"),
        constants=dict(probe_seed=PROBE_SEED, cells_per_matrix=CELLS_PER_MATRIX, floor=FLOOR,
                       other_ceiling=OTHER_CEILING, floor_origin="decoder DECODE_AGREEMENT_FLOOR, 2026-09-27"),
        matrices=mats, markers=markers,
        inputs={str(p): sha256_file(p) for p in (REGISTRY, PROVENANCE, ASSETS, SEMANTICS, SPLIT, LEDGER, DECODER_JSON)},
        fields_read_from_h5ad=["obs/exp_component_name", "the var Ensembl column", "count rows of the selected cells"],
        governance=["read-only; TRAIN donors only, checked against the split registry", "no pathology field is read",
                    "no TEST, no mutation, no training, no rebuild"],
        code=dict(path="scripts/v77/probe_v77_s174_cache_axis.py",
                  sha256=sha256_file(ROOT / "scripts/v77/probe_v77_s174_cache_axis.py"), head=git("rev-parse", "HEAD")))
    write_json(out, rec)
    print("pre-registration written", out)


def run(prereg_path: Path, out: Path) -> None:
    import h5py
    from scipy import sparse
    pre = json.loads(prereg_path.read_text(encoding="utf-8"))
    code_now = sha256_file(ROOT / "scripts/v77/probe_v77_s174_cache_axis.py")
    if git("status", "--porcelain", "--untracked-files=no", "--", "scripts/v77/probe_v77_s174_cache_axis.py"):
        sys.exit("STOP: the probe script has uncommitted changes")
    if not git("ls-files", "--", prereg_path.relative_to(ROOT).as_posix()):
        sys.exit("STOP: the pre-registration is not committed")
    drift = [p for p, h in pre["inputs"].items() if sha256_file(Path(p)) != h]
    if drift:
        sys.exit(f"STOP: inputs changed since pre-registration: {drift}")
    per, cells_out, marker_rows = [], [], []
    for m in pre["matrices"]:
        mid, study = m["matrix_id"], m["study"]
        for name, h in m["cache_files"].items():
            if sha256_file(CACHE / name) != h:
                sys.exit(f"STOP: cache shard {name} changed")
        reg, ensg2addr, addr2sym, s2a, n_blocked = load_maps(mid, study)
        dz = np.load(DECODERS / m["decoder"]["file"], allow_pickle=False)
        col2true = dict(zip(dz["block_column"].astype(int), dz["true_address"].astype(int)))
        cache_space, decoded_space = set(s2a.values()), set(col2true.values())
        z = np.load(CACHE / f"{m['cache_stem']}.counts.npz", allow_pickle=False)
        C = sparse.csr_matrix((z["data"], z["indices"], z["indptr"]), shape=tuple(z["shape"]))
        h5 = SOURCE / m["h5ad"]["path"]
        tot = dict(id=[0, 0], pos=[0, 0], dec=[0, 0])
        with h5py.File(h5, "r") as f:
            obs_cells = h5_strings(f["obs"], "exp_component_name")
            where = {c: i for i, c in enumerate(obs_cells)}
            var_ensg = h5_strings(f["var"], m["var_ensembl_column"])
            node = f[m["count_slot"]]
            ip = node["indptr"]
            pos_gene = {b: str(var_ensg[j]) for j, b in s2a.items() if j < len(var_ensg)}
            ensg2sym = dict(zip(reg.molecular_address_id.astype(str), reg.symbol.astype(str)))
            for r, cid in zip(m["selected_cache_rows"], m["cell_ids"]):
                if cid not in where:
                    sys.exit(f"STOP: cell {cid} not found in {h5.name}")
                er = where[cid]
                lo, hi = int(ip[er]), int(ip[er + 1])
                idx, val = node["indices"][lo:hi], node["data"][lo:hi]
                pred_id, pred_pos, amb = predict(idx, val, var_ensg, ensg2addr, s2a)
                row = C.getrow(r)
                cache_row = {int(a): int(v) for a, v in zip(row.indices, row.data) if v}
                decoded = {}
                for a, v in cache_row.items():
                    t = col2true.get(a)
                    if t is not None:
                        decoded[t] = decoded.get(t, 0) + v
                ai, ti = agreement(cache_row, pred_id, amb, cache_space)
                ap, tp = agreement(cache_row, pred_pos, set(), cache_space)
                ad, td = agreement(decoded, pred_id, amb, decoded_space)
                for key, (x, y) in (("id", (ai, ti)), ("pos", (ap, tp)), ("dec", (ad, td))):
                    tot[key][0] += x
                    tot[key][1] += y
                cells_out.append(dict(matrix_id=mid, cache_row=r, cell_id=cid, h5ad_row=er,
                                      entries_id=ti, agree_id=ai, entries_pos=tp, agree_pos=ap,
                                      entries_decoded=td, agree_decoded=ad, id_ambiguous_addresses=len(amb)))
                for mk in pre["markers"]:
                    a = mk["address"]
                    if a is None:
                        continue
                    held = pos_gene.get(a)
                    held_addr = ensg2addr.get(held) if held else None
                    marker_rows.append(dict(
                        matrix_id=mid, cell_id=cid, marker=mk["symbol"], marker_ensembl=mk["ensembl"],
                        h5ad_count_of_marker=int(pred_id.get(a, 0)), cache_count_at_marker_address=int(cache_row.get(a, 0)),
                        gene_the_cache_holds_there_under_POS=(ensg2sym.get(held, held) if held else None),
                        h5ad_count_of_that_gene=(int(pred_id.get(held_addr, 0)) if held_addr is not None else None)))
        per.append(dict(matrix_id=mid, cells=len(m["cell_ids"]), blocked_features=n_blocked,
                        agree_id=tot["id"][0] / max(tot["id"][1], 1), entries_id=tot["id"][1],
                        agree_pos=tot["pos"][0] / max(tot["pos"][1], 1), entries_pos=tot["pos"][1],
                        agree_decoded=tot["dec"][0] / max(tot["dec"][1], 1), entries_decoded=tot["dec"][1]))
        print(mid, {k: round(v, 4) for k, v in per[-1].items() if k.startswith("agree")}, flush=True)
    verdict = classify(per)
    rec = dict(schema="V77_S174_CACHE_AXIS_PROBE_RESULT_V1", preregistration=dict(
                   path=prereg_path.relative_to(ROOT).as_posix(), sha256=sha256_file(prereg_path)),
               verdict=verdict, per_matrix=per, per_cell=cells_out, markers=marker_rows,
               code=dict(sha256=code_now, equals_preregistered=code_now == pre["code"]["sha256"],
                         head=git("rev-parse", "HEAD")),
               h5ad_hashes_note=("source H5AD files were hashed at pre-registration; this run checks every other input "
                                 "and every cache shard by SHA-256 and the H5AD files by size"),
               h5ad_sizes_unchanged=all((SOURCE / m["h5ad"]["path"]).stat().st_size == m["h5ad"]["bytes"]
                                        for m in pre["matrices"]),
               governance=pre["governance"])
    write_json(out, rec)
    print("VERDICT", verdict)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("prepare", "run"))
    ap.add_argument("--prereg", type=Path, default=ROOT / "results/v77/V77_S174_CACHE_AXIS_PROBE_PREREGISTRATION_V1.json")
    ap.add_argument("--out", type=Path, default=ROOT / "results/v77/V77_S174_CACHE_AXIS_PROBE_RESULT_V1.json")
    a = ap.parse_args()
    if a.mode == "prepare":
        prepare(a.prereg)
    else:
        run(a.prereg, a.out)


if __name__ == "__main__":
    main()
