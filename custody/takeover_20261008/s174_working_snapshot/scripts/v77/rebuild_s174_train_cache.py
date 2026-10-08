#!/usr/bin/env python3
"""S174 repair: rebuild the real TRAIN cache by a fresh gene-ID join from the physical H5AD columns.

Owner-authorized on 2026-10-07 as a separate real-data lane (not PR #228). TRAIN only. No TEST, no
pathology-dependent selection, no mutation, no training, no model fitting. The defective positional
map (family source_feature_index applied to physical columns) is never used to build anything; it is
computed only to characterize the old cache. The old cache is never modified.

THE JOIN. Physical column j of an HVS or SEA-AD matrix carries the gene var[j] (HVS: var _index, SEA-AD:
var gene_ids). Its address is the family provenance row whose source_exact_ensembl_id equals var[j]:
the frozen Stage81A2R identity decision, applied by identifier, never by position.

COLLISIONS, explicit. A physical column is excluded, never summed, and its (matrix, address) recorded
as MEASURED_COLLISION_UNRESOLVED when (a) its gene is listed for that matrix in the frozen Stage81A3R
collision ledger, matched by Ensembl ID, or (b) two physical columns of the matrix reach one address.
Columns whose gene has no family provenance row are unmapped and counted. The 682 SEA-AD columns the
decoder had to drop were contaminated by the positional map; by identifier their genes come back
unless they are genuine collisions, and the receipts count both.

CELLS. Exactly the old cache's cells, by cell ID, in the old order, so every comparison is cell-matched.
Every donor is checked TRAIN in the split registry. NPH shards are carried over byte-identically:
NPH52 was built by a separate physical per-object path and verified not to share the defect (9d30ef62).

MODES
  freeze  value-blind: cells, TRAIN check, var identifiers, the join and collision plan, hashes of every
          input, the old cache and every source file, and the code SHA. Reads no count.
  build   refuses unless the freeze is committed and the code and inputs are unchanged; writes the new
          cache (same file names as the old, so load_real reads it unchanged) and a build receipt.
  verify  identity and value gates, then old-against-new receipts. Gates:
          G1 every rebuilt row equals an independent re-read through the S174 probe's own ID join
          G2 the validated decoder applied to the old cache agrees with the rebuilt cache >= 0.99
             wherever a decoder exists
          G3 per-cell library totals equal the old cache's source_library
          G4 NPH shards byte-identical to the old ones
          G5 every cell's donor is TRAIN
          The old cache is also re-characterized per matrix (POS against the old map) as a description,
          not a gate. The rebuilt cache may be used only if every gate passes.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = Path("D:/Jepa project")
OLD_CACHE = SOURCE / "data/cache/stage81a3r_corrected_real_train"
NEW_CACHE = SOURCE / "data/cache/s174_rebuilt_real_train_v1"
REGISTRY = SOURCE / "results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv"
PROVENANCE = SOURCE / "results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz"
ASSETS = SOURCE / "results/v4/stage81a2_canonical_asset_registry.csv"
SEMANTICS = SOURCE / "results/v4/stage81a2_matrix_semantics_contract.csv"
SPLIT = SOURCE / "results/v4/stage81a2_split_registry.csv"
LEDGER = Path("D:/Jepa project-stage81a3r-20260814/results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz")
DECODER_DIRS = (Path("D:/jepa_v5_outputs_20260925/l4_decoder_all"), Path("D:/jepa_v5_outputs_20260925/l4_decoder_v2"))
FREEZE = ROOT / "results/v77/S174_REBUILD_FREEZE_V1.json"
BUILD = ROOT / "results/v77/S174_REBUILD_BUILD_RECEIPT_V1.json"
VERIFY = ROOT / "results/v77/S174_REBUILD_VERIFY_AND_COMPARISON_V1.json"
N_ADDR = 41238
VAR_ID_COLUMN = {"HVS": "_index", "SEA_AD": "gene_ids"}
FAMILY = {"HVS": "HVS_COMMON", "SEA_AD": "SEA_AD_COMMON"}
DECODER_FLOOR = 0.99
MARKERS = ("SNAP25", "SLC17A7", "GAD1", "MBP", "PLP1", "MOBP", "GFAP", "AQP4", "P2RY12", "CSF1R", "CX3CR1",
           "PDGFRA", "APOE")


# ------------------------------------------------------------------------ pure, tested logic

def id_join_map(var_ids, family_id_to_addr: dict, ledger_ids: set):
    """Physical column -> address by identifier, with collisions excluded and recorded.
    Returns (col2addr, excluded) where excluded maps column -> reason."""
    col2addr, excluded, reach = {}, {}, {}
    for j, gid in enumerate(var_ids):
        gid = str(gid)
        if gid in ledger_ids:
            excluded[j] = "LEDGER_COLLISION"
            continue
        a = family_id_to_addr.get(gid)
        if a is None:
            excluded[j] = "UNMAPPED"
            continue
        reach.setdefault(a, []).append(j)
    for a, cols in reach.items():
        if len(cols) == 1:
            col2addr[cols[0]] = a
        else:
            for j in cols:
                excluded[j] = "JOIN_COLLISION"
    return col2addr, excluded


def build_row(indices, values, col2addr: dict):
    """One cache row from one physical row. The library is every count in the row, as the old builder had it."""
    row, total = {}, 0
    for j, v in zip(indices, values):
        v = int(round(float(v)))
        if v < 0:
            raise ValueError("negative count")
        total += v
        a = col2addr.get(int(j))
        if a is not None and v:
            row[a] = v
    return row, total


def collision_addresses(var_ids, family_id_to_addr: dict, excluded: dict) -> set:
    """Addresses left MEASURED_COLLISION_UNRESOLVED: those reached only by excluded collision columns."""
    out = set()
    for j, why in excluded.items():
        if why in ("LEDGER_COLLISION", "JOIN_COLLISION"):
            a = family_id_to_addr.get(str(var_ids[j]))
            if a is not None:
                out.add(a)
    return out


# ----------------------------------------------------------------------------------- helpers

def sha256_file(p: Path, chunk: int = 1 << 24) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def write_json(path: Path, obj) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, indent=1) + "\n")


def git(*a) -> str:
    return subprocess.run(["git", *a], capture_output=True, text=True, cwd=ROOT).stdout.strip()


def stem(matrix_id: str) -> str:
    return hashlib.sha256(f"corrected|{matrix_id}".encode()).hexdigest()[:16]


def h5_strings(grp, name: str) -> np.ndarray:
    import h5py
    if name == "_index":
        name = grp.attrs.get("_index", "_index")
        name = name.decode() if isinstance(name, bytes) else str(name)
    obj = grp[name]
    vals = obj["categories"][:][obj["codes"][:]] if isinstance(obj, h5py.Group) else obj[:]
    return np.array([v.decode() if isinstance(v, bytes) else str(v) for v in vals], dtype=object)


def tables():
    import pandas as pd
    assets, sem = pd.read_csv(ASSETS), pd.read_csv(SEMANTICS)
    phase_a = assets[assets.study_id.isin(["HVS", "SEA_AD"]) & assets.foundation_eligible].sort_values("dataset_id")
    prov = pd.read_csv(PROVENANCE, usecols=["source_dataset_id", "source_feature_index", "source_exact_ensembl_id",
                                            "molecular_address_index"], low_memory=False)
    fam = {}
    for study, key in FAMILY.items():
        f = prov[prov.source_dataset_id.eq(key)]
        fam[study] = dict(id2addr=dict(zip(f.source_exact_ensembl_id.astype(str), f.molecular_address_index.astype(int))),
                          pos=dict(zip(f.source_feature_index.astype(int), f.molecular_address_index.astype(int))),
                          n_rows=int(len(f)), n_ids=int(f.source_exact_ensembl_id.nunique()))
    led = pd.read_csv(LEDGER, usecols=["matrix_id", "source_feature_index", "source_exact_ensembl_id"], low_memory=False)
    split = pd.read_csv(SPLIT)
    tr = split[(split.split_domain == "foundation") & (split.split == "train")]
    train = {str(s): {str(v).split("::", 1)[-1] for v in g.canonical_person_id} for s, g in tr.groupby("study_id")}
    return phase_a, sem, fam, led, train


def nph_stems():
    out = []
    for f in sorted(glob.glob(str(OLD_CACHE / "*.counts.npz"))):
        s = Path(f).name.split(".")[0]
        out.append(s)
    return out


# --------------------------------------------------------------------------------------- freeze

def freeze() -> None:
    import h5py
    phase_a, sem, fam, led, train = tables()
    h5_stems, mats = set(), []
    for r in phase_a.itertuples(index=False):
        mid, study = str(r.dataset_id), str(r.study_id)
        s = stem(mid)
        h5_stems.add(s)
        meta = np.load(OLD_CACHE / f"{s}.meta.npz", allow_pickle=False)
        cells, donors = meta["cell_id"].astype(str).tolist(), meta["donor_id"].astype(str).tolist()
        slot = str(sem[sem.dataset_id.eq(mid)].matrix_slot.iloc[0])
        src = SOURCE / str(r.matrix_path_or_object)
        with h5py.File(src, "r") as f:
            var_ids = h5_strings(f["var"], VAR_ID_COLUMN[study])
        ledger_ids = set(led.loc[led.matrix_id.astype(str).eq(mid), "source_exact_ensembl_id"].astype(str))
        col2addr, excluded = id_join_map(var_ids, fam[study]["id2addr"], ledger_ids)
        old_blocked = set(led.loc[led.matrix_id.astype(str).eq(mid), "source_feature_index"].astype(int))
        pos = {j: a for j, a in fam[study]["pos"].items() if j not in old_blocked}
        moved = sum(1 for j, a in col2addr.items() if pos.get(j) != a)
        mats.append(dict(
            matrix_id=mid, study=study, stem=s, slot=slot, source=dict(path=str(r.matrix_path_or_object),
                                                                       bytes=src.stat().st_size, sha256=sha256_file(src)),
            old_cache=dict(counts_sha256=sha256_file(OLD_CACHE / f"{s}.counts.npz"),
                           meta_sha256=sha256_file(OLD_CACHE / f"{s}.meta.npz")),
            cells=len(cells), cell_ids_sha256=hashlib.sha256("|".join(cells).encode()).hexdigest(),
            all_donors_train=bool(all(d in train.get(study, set()) for d in donors)),
            var_features=int(len(var_ids)), mapped_columns=len(col2addr),
            excluded=dict(Counter(excluded.values())),
            collision_addresses=len(collision_addresses(var_ids, fam[study]["id2addr"], excluded)),
            old_positional_blocked=len(old_blocked),
            mapped_columns_whose_address_differs_from_the_old_positional_map=moved))
        print(mid, "mapped", len(col2addr), "excluded", dict(Counter(excluded.values())), "moved", moved,
              "train", mats[-1]["all_donors_train"], flush=True)
    if not all(m["all_donors_train"] for m in mats):
        sys.exit("STOP: a cell's donor is not TRAIN")
    nph = [s for s in nph_stems() if s not in h5_stems]
    if len(nph) != 7 or len(mats) != 35:
        sys.exit(f"STOP: expected 35 H5 matrices and 7 NPH shards, found {len(mats)} and {len(nph)}")
    rec = dict(
        schema="S174_REBUILD_FREEZE_V1", status="FROZEN__NO_COUNT_READ",
        authorization=("owner, 2026-10-07: full TRAIN cache rebuild by a fresh gene-ID join from physical H5AD columns; "
                       "decoder kept as an independent cross-check; collisions explicit; recover the 682 SEA-AD columns "
                       "where possible; no TEST, pathology-dependent selection, mutation, training or model fitting; "
                       "freeze hashes and code SHA before execution; old-against-new receipts; separate lane from PR #228"),
        lane=dict(branch=git("rev-parse", "--abbrev-ref", "HEAD"), stacked_on="claude/v77-synthetic-premise-custody-20261005@976d2be6"),
        old_cache=str(OLD_CACHE), new_cache=str(NEW_CACHE),
        policy=dict(join="physical var identifier -> family provenance source_exact_ensembl_id -> molecular_address_index",
                    never_used="the family source_feature_index applied to physical columns",
                    collisions=("excluded, never summed; recorded as MEASURED_COLLISION_UNRESOLVED; ledger collisions "
                                "matched by Ensembl ID plus any join collision"),
                    cells="exactly the old cache's cells in the old order", nph="carried over byte-identically",
                    library="every count in the physical row, as the old builder computed it"),
        matrices=mats,
        nph_shards=[dict(stem=s, counts_sha256=sha256_file(OLD_CACHE / f"{s}.counts.npz"),
                         meta_sha256=sha256_file(OLD_CACHE / f"{s}.meta.npz")) for s in nph],
        inputs={str(p): sha256_file(p) for p in (REGISTRY, PROVENANCE, ASSETS, SEMANTICS, SPLIT, LEDGER)},
        decoders={str(d / f.name): sha256_file(f) for d in DECODER_DIRS for f in sorted(d.glob("decoder_*.npz"))},
        gates=["G1 rebuilt rows equal an independent re-read through the S174 probe's ID join",
               f"G2 decoded old cache agrees with the rebuilt cache >= {DECODER_FLOOR} wherever a decoder exists",
               "G3 per-cell library totals equal the old source_library", "G4 NPH shards byte-identical",
               "G5 every donor TRAIN"],
        code=dict(path="scripts/v77/rebuild_s174_train_cache.py",
                  sha256=sha256_file(ROOT / "scripts/v77/rebuild_s174_train_cache.py"), head=git("rev-parse", "HEAD")),
        governance=["TRAIN only", "obs read: exp_component_name only", "no pathology field read",
                    "no TEST, mutation, training or model fitting"])
    write_json(FREEZE, rec)
    print("freeze written", FREEZE, "| H5 matrices", len(mats), "| NPH shards", len(nph))


# ---------------------------------------------------------------------------------------- build

def _guard(fr: dict) -> None:
    if git("status", "--porcelain", "--untracked-files=no", "--", "scripts/v77/rebuild_s174_train_cache.py"):
        sys.exit("STOP: the rebuild script has uncommitted changes")
    if sha256_file(ROOT / "scripts/v77/rebuild_s174_train_cache.py") != fr["code"]["sha256"]:
        sys.exit("STOP: the rebuild script differs from the frozen one")
    if not git("ls-files", "--", FREEZE.relative_to(ROOT).as_posix()):
        sys.exit("STOP: the freeze is not committed")
    drift = [p for p, h in fr["inputs"].items() if sha256_file(Path(p)) != h]
    if drift:
        sys.exit(f"STOP: inputs changed since the freeze: {drift}")


def build() -> None:
    import h5py
    from scipy import sparse
    fr = json.loads(FREEZE.read_text(encoding="utf-8"))
    _guard(fr)
    _, _, fam, led, _ = tables()
    NEW_CACHE.mkdir(parents=True, exist_ok=True)
    if any(NEW_CACHE.iterdir()):
        sys.exit(f"STOP: {NEW_CACHE} is not empty; a rebuild never overwrites")
    receipts = []
    for m in fr["matrices"]:
        mid, study, s = m["matrix_id"], m["study"], m["stem"]
        if sha256_file(OLD_CACHE / f"{s}.counts.npz") != m["old_cache"]["counts_sha256"]:
            sys.exit(f"STOP: old cache shard {s} changed")
        if (SOURCE / m["source"]["path"]).stat().st_size != m["source"]["bytes"]:
            sys.exit(f"STOP: source {m['source']['path']} changed size")
        meta = np.load(OLD_CACHE / f"{s}.meta.npz", allow_pickle=False)
        cells = meta["cell_id"].astype(str)
        ledger_ids = set(led.loc[led.matrix_id.astype(str).eq(mid), "source_exact_ensembl_id"].astype(str))
        with h5py.File(SOURCE / m["source"]["path"], "r") as f:
            var_ids = h5_strings(f["var"], VAR_ID_COLUMN[study])
            col2addr, excluded = id_join_map(var_ids, fam[study]["id2addr"], ledger_ids)
            obs = h5_strings(f["obs"], "exp_component_name")
            where = {c: i for i, c in enumerate(obs)}
            node = f[m["slot"]]
            ip = node["indptr"]
            rows, cols, data, totals = [], [], [], []
            for out_r, cid in enumerate(cells):
                if cid not in where:
                    sys.exit(f"STOP: cell {cid} absent from {m['source']['path']}")
                er = where[cid]
                lo, hi = int(ip[er]), int(ip[er + 1])
                row, total = build_row(node["indices"][lo:hi], node["data"][lo:hi], col2addr)
                totals.append(total)
                for a, v in row.items():
                    rows.append(out_r); cols.append(a); data.append(v)
        X = sparse.csr_matrix((np.asarray(data, dtype=np.int32), (rows, cols)), shape=(len(cells), N_ADDR), dtype=np.int32)
        X.sort_indices()
        sparse.save_npz(NEW_CACHE / f"{s}.counts.npz", X, compressed=True)
        np.savez_compressed(NEW_CACHE / f"{s}.meta.npz", donor_id=meta["donor_id"], cell_id=meta["cell_id"],
                            broad_cell_class=meta["broad_cell_class"], source_library=np.asarray(totals, dtype=np.int64))
        receipts.append(dict(matrix_id=mid, stem=s, rows=len(cells), nnz=int(X.nnz),
                             counts_sha256=sha256_file(NEW_CACHE / f"{s}.counts.npz"),
                             meta_sha256=sha256_file(NEW_CACHE / f"{s}.meta.npz")))
        print("built", mid, X.shape, X.nnz, flush=True)
    for n in fr["nph_shards"]:
        for kind in ("counts", "meta"):
            src, dst = OLD_CACHE / f"{n['stem']}.{kind}.npz", NEW_CACHE / f"{n['stem']}.{kind}.npz"
            if sha256_file(src) != n[f"{kind}_sha256"]:
                sys.exit(f"STOP: NPH shard {src.name} changed")
            shutil.copyfile(src, dst)
    write_json(BUILD, dict(schema="S174_REBUILD_BUILD_RECEIPT_V1", freeze=dict(path=FREEZE.relative_to(ROOT).as_posix(),
                                                                                  sha256=sha256_file(FREEZE)),
                           new_cache=str(NEW_CACHE), h5_shards=receipts, nph_shards_copied=len(fr["nph_shards"]),
                           code_sha256=sha256_file(ROOT / "scripts/v77/rebuild_s174_train_cache.py"),
                           head=git("rev-parse", "HEAD")))
    print("build receipt written", BUILD)


# --------------------------------------------------------------------------------------- verify

def verify() -> None:
    import h5py
    import importlib.util
    import pandas as pd
    from scipy import sparse
    fr = json.loads(FREEZE.read_text(encoding="utf-8"))
    bd = json.loads(BUILD.read_text(encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("s174_probe", HERE / "probe_v77_s174_cache_axis.py")
    P = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(P)
    _, _, fam, led, train = tables()
    reg = pd.read_csv(REGISTRY, usecols=["molecular_address_index", "molecular_address_id", "symbol"])
    ensg2addr = dict(zip(reg.molecular_address_id.astype(str), reg.molecular_address_index.astype(int)))
    sym2addr = dict(zip(reg.symbol.astype(str), reg.molecular_address_index.astype(int)))
    decoders = {}
    for d in DECODER_DIRS:
        for f in d.glob("decoder_*.npz"):
            key = f.name[len("decoder_"):-len(".npz")].replace("__", "::")
            if key not in decoders:
                z = np.load(f, allow_pickle=False)
                decoders[key] = dict(zip(z["block_column"].astype(int), z["true_address"].astype(int)))
    per, gates = [], dict(G1=True, G2=True, G3=True, G4=True, G5=True, G6=True)
    for b in bd["h5_shards"]:          # G6: the cache verified is the cache the build receipt describes
        gates["G6"] &= (sha256_file(NEW_CACHE / f"{b['stem']}.counts.npz") == b["counts_sha256"]
                        and sha256_file(NEW_CACHE / f"{b['stem']}.meta.npz") == b["meta_sha256"])
    marker_tab = []
    for m in fr["matrices"]:
        mid, study, s = m["matrix_id"], m["study"], m["stem"]
        load = lambda c, k: np.load(c / f"{s}.{k}.npz", allow_pickle=False)
        zo, zn, mo, mn = load(OLD_CACHE, "counts"), load(NEW_CACHE, "counts"), load(OLD_CACHE, "meta"), load(NEW_CACHE, "meta")
        Xo = sparse.csr_matrix((zo["data"], zo["indices"], zo["indptr"]), shape=tuple(zo["shape"]))
        Xn = sparse.csr_matrix((zn["data"], zn["indices"], zn["indptr"]), shape=tuple(zn["shape"]))
        ledger_ids = set(led.loc[led.matrix_id.astype(str).eq(mid), "source_exact_ensembl_id"].astype(str))
        old_blocked = set(led.loc[led.matrix_id.astype(str).eq(mid), "source_feature_index"].astype(int))
        pos = {j: a for j, a in fam[study]["pos"].items() if j not in old_blocked}
        g1 = [0, 0]; pos_old = [0, 0]; g2 = [0, 0]
        with h5py.File(SOURCE / m["source"]["path"], "r") as f:
            var_ids = h5_strings(f["var"], VAR_ID_COLUMN[study])
            _, excluded = id_join_map(var_ids, fam[study]["id2addr"], ledger_ids)
            coll = collision_addresses(var_ids, fam[study]["id2addr"], excluded)
            obs = h5_strings(f["obs"], "exp_component_name")
            where = {c: i for i, c in enumerate(obs)}
            node = f[m["slot"]]
            ip = node["indptr"]
            for r, cid in enumerate(mn["cell_id"].astype(str)):
                er = where[cid]
                lo, hi = int(ip[er]), int(ip[er + 1])
                pred_id, pred_pos, amb = P.predict(node["indices"][lo:hi], node["data"][lo:hi], var_ids, ensg2addr, pos)
                new_row = {int(a): int(v) for a, v in zip(Xn.getrow(r).indices, Xn.getrow(r).data)}
                old_row = {int(a): int(v) for a, v in zip(Xo.getrow(r).indices, Xo.getrow(r).data)}
                space_new = set(new_row) | {a for a in pred_id if a not in coll}
                a_, t_ = P.agreement(new_row, pred_id, amb | coll, space_new)
                g1[0] += a_; g1[1] += t_
                a_, t_ = P.agreement(old_row, pred_pos, set(), set(pos.values()))
                pos_old[0] += a_; pos_old[1] += t_
                dec = decoders.get(mid)
                if dec:
                    decoded = {}
                    for a, v in old_row.items():
                        t = dec.get(a)
                        if t is not None:
                            decoded[t] = decoded.get(t, 0) + v
                    dspace = (set(decoded) | set(new_row)) & set(dec.values())
                    a_, t_ = P.agreement(decoded, new_row, coll, dspace)
                    g2[0] += a_; g2[1] += t_
        g1f = g1[0] / max(g1[1], 1)
        g2f = (g2[0] / g2[1]) if g2[1] else None
        g3 = bool(np.array_equal(mo["source_library"], mn["source_library"]))
        g5 = bool(all(d in train.get(study, set()) for d in mn["donor_id"].astype(str)))
        gates["G1"] &= g1f == 1.0
        gates["G2"] &= (g2f is None) or g2f >= DECODER_FLOOR
        gates["G3"] &= g3
        gates["G5"] &= g5
        cls = mn["broad_cell_class"].astype(str)
        for mk in MARKERS:
            a = sym2addr.get(mk)
            if a is None:
                continue
            for c in sorted(set(cls)):
                idx = np.flatnonzero(cls == c)
                marker_tab.append(dict(matrix_id=mid, marker=mk, broad_cell_class=c, cells=int(len(idx)),
                                       detected_old=float((Xo[idx, a].toarray() > 0).mean()),
                                       detected_new=float((Xn[idx, a].toarray() > 0).mean())))
        per.append(dict(matrix_id=mid, study=study, rows=int(Xn.shape[0]), nnz_old=int(Xo.nnz), nnz_new=int(Xn.nnz),
                        G1_agreement=g1f, G1_entries=g1[1], G2_decoder_agreement=g2f, G2_entries=g2[1],
                        G3_library_equal=g3, G5_train=g5, old_cache_matches_old_positional_map=pos_old[0] / max(pos_old[1], 1),
                        old_positional_entries=pos_old[1], collision_addresses=len(coll),
                        addresses_with_any_count_old=int((np.asarray(Xo.sum(0)).ravel() > 0).sum()),
                        addresses_with_any_count_new=int((np.asarray(Xn.sum(0)).ravel() > 0).sum())))
        print(mid, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in per[-1].items() if k.startswith(("G", "old_cache"))}, flush=True)
    for n in fr["nph_shards"]:
        for kind in ("counts", "meta"):
            gates["G4"] &= sha256_file(NEW_CACHE / f"{n['stem']}.{kind}.npz") == n[f"{kind}_sha256"]
    rec = dict(schema="S174_REBUILD_VERIFY_AND_COMPARISON_V1",
               freeze_sha256=sha256_file(FREEZE), build_receipt_sha256=sha256_file(BUILD), gates=gates,
               all_gates_pass=all(gates.values()),
               use_rule="the rebuilt cache may be used only if every gate passes",
               per_matrix=per, markers=marker_tab,
               code_sha256=sha256_file(ROOT / "scripts/v77/rebuild_s174_train_cache.py"), head=git("rev-parse", "HEAD"))
    write_json(VERIFY, rec)
    print("GATES", gates, "ALL PASS" if rec["all_gates_pass"] else "FAIL")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("freeze", "build", "verify"))
    a = ap.parse_args()
    {"freeze": freeze, "build": build, "verify": verify}[a.mode]()


if __name__ == "__main__":
    main()
