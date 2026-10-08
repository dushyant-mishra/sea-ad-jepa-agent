#!/usr/bin/env python3
"""Metadata-only FOUNDATION atlas and prospective 25k+25k sample freeze.

No expression matrix is opened. Mixed HVS/SEA authorities are filtered by the
frozen FOUNDATION TRAIN donor registry before rows are persisted.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exports" / "foundation_corpus_discovery_v1"
DB = OUT / "foundation_metadata_rows.sqlite"
SEED = "FOUNDATION_CORPUS_DISCOVERY_V1_20260824"
SAMPLE_N = 25_000
sys.path.insert(0, str(ROOT / "scripts" / "v4"))
sys.path.insert(0, str(ROOT / "exports" / "static_context_decomposition_v4_20260821"))
from production_train_loader import (  # noqa: E402
    MEASURED_COLLISION_UNRESOLVED, MEASURED_SCALAR, STRUCTURALLY_UNMEASURED,
    ProductionTrainLoader,
)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def h64(*parts: object) -> int:
    b = "|".join(map(str, parts)).encode()
    return int.from_bytes(hashlib.sha256(b).digest()[:8], "big") & ((1 << 63) - 1)


def clean(values: np.ndarray) -> np.ndarray:
    return np.asarray(["" if x is None else (x.decode("utf-8") if isinstance(x, (bytes, np.bytes_)) else str(x)) for x in values], dtype=object)


def read_h5_vector(group: h5py.Group, name: str) -> np.ndarray:
    node = group[name]
    if isinstance(node, h5py.Group) and "codes" in node and "categories" in node:
        codes = np.asarray(node["codes"])
        cats = clean(np.asarray(node["categories"]))
        return np.asarray([cats[int(c)] if int(c) >= 0 else "" for c in codes], object)
    values = np.asarray(node)
    return np.asarray([v.decode("utf-8") if isinstance(v, (bytes, np.bytes_)) else str(v) for v in values], object)


def gini(x: np.ndarray) -> float:
    x = np.sort(np.asarray(x, float))
    if len(x) == 0 or x.sum() == 0:
        return 0.0
    return float((2 * np.arange(1, len(x) + 1) - len(x) - 1).dot(x) / (len(x) * x.sum()))


def largest_remainder(counts: dict[str, int], total: int) -> dict[str, int]:
    # Donor-primary: every donor receives one cell, then remaining capacity is
    # proportional to empirical cell abundance.
    remainder_total = total - len(counts)
    if remainder_total < 0:
        raise RuntimeError("sample smaller than donor count")
    denom = sum(counts.values())
    raw = {k: remainder_total * v / denom for k, v in counts.items()}
    q = {k: 1 + int(np.floor(v)) for k, v in raw.items()}
    for k in sorted(counts, key=lambda z: (-(raw[z] - q[z]), h64(SEED, "remainder", z))):
        if sum(q.values()) >= total:
            break
        q[k] += 1
    return q


def initialize_db() -> sqlite3.Connection:
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("""CREATE TABLE cells(
      source TEXT, matrix_id TEXT, operator_index INTEGER, local_row INTEGER,
      donor_id TEXT, partition TEXT, cell_id TEXT, native_class TEXT,
      broad_class TEXT, support_fingerprint TEXT, stable_key INTEGER,
      in_original_t1 INTEGER, cell_id_hash INTEGER,
      PRIMARY KEY(matrix_id, local_row))""")
    return con


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg_path = ROOT / "configs/v4/stage81a3_foundation_heterogeneity_reality_audit.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    asset_path = ROOT / cfg["inputs"]["assets"]
    split_path = ROOT / "exports/contextual_biology_v6r5a_20260822/reader_donor_split.csv"
    old_path = ROOT / "exports/prod41k_teacher_t1_20260823/t1_encoder_fit_inventory.csv"
    assets = pd.read_csv(asset_path)
    split = pd.read_csv(split_path).astype(str)
    part = dict(zip(split.donor_id, split.reader_partition))
    fit = {d for d, p in part.items() if p == "reader_fit"}
    held = {d for d, p in part.items() if p != "reader_fit"}
    if len(fit) != 104 or len(held) != 45 or fit & held:
        raise RuntimeError("frozen 104/45 firewall mismatch")
    old = pd.read_csv(old_path, usecols=["matrix_id", "cell_id"], dtype=str)
    old_ids = set(zip(old.matrix_id, old.cell_id))

    loader = ProductionTrainLoader()
    operator = loader.cell_table()[["operator_index", "matrix_id"]].drop_duplicates()
    opmap = dict(zip(operator.matrix_id.astype(str), operator.operator_index.astype(int)))
    support = {}
    support_counts = {}
    for matrix_id, state in loader.states.items():
        support[matrix_id] = hashlib.sha256(np.asarray(state, np.uint8).tobytes()).hexdigest()
        support_counts[matrix_id] = {
            "measured_scalar_addresses": int(np.count_nonzero(state == MEASURED_SCALAR)),
            "structurally_unmeasured_addresses": int(np.count_nonzero(state == STRUCTURALLY_UNMEASURED)),
            "collision_unresolved_addresses": int(np.count_nonzero(state == MEASURED_COLLISION_UNRESOLVED)),
        }

    con = initialize_db()
    insert = "INSERT INTO cells VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)"
    matrix_audit = []
    for a in assets.itertuples(index=False):
        study = str(a.study_id)
        if study not in {"HVS", "SEA_AD"} or str(a.foundation_eligible).lower() != "true":
            continue
        matrix_id = str(a.dataset_id)
        if matrix_id not in opmap:
            raise RuntimeError(f"matrix absent from current 42-operator authority: {matrix_id}")
        path = ROOT / str(a.matrix_path_or_object)
        allowed = cfg["allowed_metadata"][study]
        with h5py.File(path, "r") as f:
            obs = f["obs"]
            donors = clean(read_h5_vector(obs, allowed["donor"]))
            cell_field = allowed["cell_id"]
            cells = clean(read_h5_vector(obs, cell_field)) if cell_field in obs else clean(read_h5_vector(obs, "_index"))
            broad_field = allowed["broad_class"] if allowed["broad_class"] in obs else allowed["broad_class_fallback"]
            broad = clean(read_h5_vector(obs, broad_field))
            native = clean(read_h5_vector(obs, allowed["broad_class_fallback"])) if allowed["broad_class_fallback"] in obs else np.full(len(cells), "", object)
        idx = np.flatnonzero(np.isin(donors, list(part)))
        rows = []
        for i in idx:
            donor, cell = str(donors[i]), str(cells[i])
            rows.append((study, matrix_id, opmap[matrix_id], int(i), donor, part[donor], cell,
                         str(native[i]), str(broad[i]), support[matrix_id],
                         h64(matrix_id, int(i), cell), int((matrix_id, cell) in old_ids), h64(study, cell)))
            if len(rows) >= 50_000:
                con.executemany(insert, rows); con.commit(); rows.clear()
        if rows:
            con.executemany(insert, rows); con.commit()
        matrix_audit.append({"source": study, "matrix_id": matrix_id, "train_rows": int(len(idx)), "fit_rows": int(np.isin(donors[idx], list(fit)).sum())})

    nph_path = ROOT / cfg["inputs"]["nph_disposition"]
    nph = pd.read_csv(nph_path, dtype=str)
    nph["local_row"] = nph.groupby("source_object", sort=False).cumcount()
    ok = nph.foundation_eligibility.str.lower().eq("true") & nph.donor_id.isin(part)
    nph = nph.loc[ok]
    for obj, g in nph.groupby("source_object", sort=True):
        matrix_id = f"NPH52::matrix::{obj}"
        native = obj.split("_", 1)[0]
        rows = []
        for r in g.itertuples(index=False):
            donor, cell = str(r.donor_id), str(r.source_cell_id)
            rows.append(("NPH52", matrix_id, opmap[matrix_id], int(r.local_row), donor, part[donor], cell,
                         native, "", support[matrix_id], h64(matrix_id, int(r.local_row), cell),
                         int((matrix_id, cell) in old_ids), h64("NPH52", cell)))
            if len(rows) >= 50_000:
                con.executemany(insert, rows); con.commit(); rows.clear()
        if rows:
            con.executemany(insert, rows); con.commit()
        matrix_audit.append({"source": "NPH52", "matrix_id": matrix_id, "train_rows": len(g), "fit_rows": int(g.donor_id.isin(fit).sum())})

    con.executescript("""CREATE INDEX ix_partition ON cells(partition);
      CREATE INDEX ix_donor ON cells(donor_id); CREATE INDEX ix_matrix ON cells(matrix_id);
      CREATE INDEX ix_native ON cells(native_class); CREATE INDEX ix_broad ON cells(broad_class);
      CREATE INDEX ix_old ON cells(in_original_t1);""")
    con.commit()

    def query(sql: str, args=()) -> pd.DataFrame:
        return pd.read_sql_query(sql, con, params=args)

    tables = {
        "source": "source", "operator": "matrix_id", "donor": "donor_id",
        "native_class": "native_class", "broad_class": "broad_class",
        "source_x_donor": "source, donor_id", "source_x_operator": "source, matrix_id",
        "source_x_native_class": "source, native_class", "operator_x_native_class": "matrix_id, native_class",
        "donor_x_native_class": "donor_id, native_class", "donor_x_operator": "donor_id, matrix_id",
    }
    table_files = {}
    for name, cols in tables.items():
        frame = query(f"SELECT {cols}, COUNT(*) AS cell_count, SUM(in_original_t1) AS original_t1_cells FROM cells WHERE partition='reader_fit' GROUP BY {cols} ORDER BY cell_count DESC")
        p = OUT / f"FOUNDATION_METADATA_{name.upper()}.csv"
        frame.to_csv(p, index=False, lineterminator="\n")
        table_files[p.name] = {"rows": len(frame), "sha256": sha(p)}
    context = query("SELECT partition, source, COUNT(*) cell_count, COUNT(DISTINCT donor_id) donor_count FROM cells GROUP BY partition,source ORDER BY partition,source")
    context_path = OUT / "FOUNDATION_METADATA_ALL149_CONTEXT.csv"
    context.to_csv(context_path, index=False, lineterminator="\n")
    table_files[context_path.name] = {"rows": len(context), "sha256": sha(context_path)}

    donor_counts = dict(query("SELECT donor_id,COUNT(*) n FROM cells WHERE partition='reader_fit' GROUP BY donor_id").itertuples(index=False, name=None))
    if len(donor_counts) != 104:
        raise RuntimeError("atlas does not contain exactly 104 fit donors")
    quotas = largest_remainder(donor_counts, SAMPLE_N)
    # Natural sample: exact donor-proportional quotas and minimum deterministic hash.
    heaps: dict[str, list[tuple[int, tuple]]] = defaultdict(list)
    cur = con.execute("SELECT source,matrix_id,operator_index,local_row,donor_id,cell_id,native_class,broad_class,support_fingerprint,stable_key,in_original_t1 FROM cells WHERE partition='reader_fit' AND in_original_t1=0")
    for row in cur:
        donor = row[4]; score = h64(SEED, "A", row[9]); item = (-score, row)
        heap = heaps[donor]; q = quotas[donor]
        if len(heap) < q: heapq.heappush(heap, item)
        elif q and item > heap[0]: heapq.heapreplace(heap, item)
    selected_a = [row for heap in heaps.values() for _, row in heap]
    if len(selected_a) != SAMPLE_N:
        raise RuntimeError("natural sample size failure")
    akeys = {r[9] for r in selected_a}

    # Coverage sample: first cover every observed metadata/support stratum, then
    # water-fill donors with deterministic unique cells. Never reads expression.
    winners = {}
    donor_candidates: dict[str, list[tuple[int, tuple]]] = defaultdict(list)
    cur = con.execute("SELECT source,matrix_id,operator_index,local_row,donor_id,cell_id,native_class,broad_class,support_fingerprint,stable_key,in_original_t1 FROM cells WHERE partition='reader_fit' AND in_original_t1=0")
    for row in cur:
        if row[9] in akeys: continue
        stratum = (row[0], row[1], row[6], row[7], row[8])
        score = h64(SEED, "B-stratum", row[9])
        if stratum not in winners or score < winners[stratum][0]: winners[stratum] = (score, row)
        heap = donor_candidates[row[4]]; item = (-h64(SEED, "B-fill", row[9]), row)
        if len(heap) < 500: heapq.heappush(heap, item)
        elif item > heap[0]: heapq.heapreplace(heap, item)
    selected_b = {r[9]: r for _, r in winners.values()}
    # donor-primary round-robin fill; availability, not source balancing, controls remainder.
    ordered = {d: [r for _, r in sorted(h, reverse=True)] for d, h in donor_candidates.items()}
    pos = Counter()
    donors = sorted(ordered, key=lambda d: h64(SEED, "B-donor", d))
    while len(selected_b) < SAMPLE_N:
        progress = False
        for d in donors:
            while pos[d] < len(ordered[d]):
                r = ordered[d][pos[d]]; pos[d] += 1
                if r[9] not in selected_b:
                    selected_b[r[9]] = r; progress = True; break
            if len(selected_b) >= SAMPLE_N: break
        if not progress: raise RuntimeError("coverage sample candidate exhaustion")

    columns = ["source", "matrix_id", "operator_index", "local_row", "donor_id", "cell_id", "native_class", "broad_class", "support_fingerprint", "stable_key", "in_original_t1"]
    def sample_frame(label: str, rows: list[tuple]) -> pd.DataFrame:
        f = pd.DataFrame(rows, columns=columns)
        f.insert(0, "sample", label)
        f.insert(1, "sample_row", np.arange(len(f), dtype=np.int64))
        f["selection_seed"] = SEED
        f["expression_read_before_freeze"] = False
        return f
    freeze = pd.concat([sample_frame("A_NATURAL_MIXTURE", sorted(selected_a, key=lambda r: h64(SEED, "A-order", r[9]))),
                        sample_frame("B_COVERAGE_DISCOVERY", sorted(selected_b.values(), key=lambda r: h64(SEED, "B-order", r[9])))], ignore_index=True)
    if freeze.stable_key.nunique() != 2 * SAMPLE_N or freeze.in_original_t1.sum() != 0:
        raise RuntimeError("sample disjointness/original-cache exclusion failure")
    freeze_path = OUT / "FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv"
    freeze.to_csv(freeze_path, index=False, lineterminator="\n")

    total = int(query("SELECT COUNT(*) n FROM cells WHERE partition='reader_fit'").iloc[0, 0])
    all_total = int(query("SELECT COUNT(*) n FROM cells").iloc[0, 0])
    old_total = int(query("SELECT SUM(in_original_t1) n FROM cells WHERE partition='reader_fit'").iloc[0, 0])
    duplicate_cell_ids = query("SELECT source,cell_id,COUNT(*) n FROM cells WHERE partition='reader_fit' GROUP BY source,cell_id HAVING n>1")
    duplicate_keys = query("SELECT stable_key,COUNT(*) n FROM cells WHERE partition='reader_fit' GROUP BY stable_key HAVING n>1")
    missing = query("SELECT source, SUM(native_class='') missing_native, SUM(broad_class='') missing_broad, COUNT(*) n FROM cells WHERE partition='reader_fit' GROUP BY source")
    sizes = {k: query(f"SELECT COUNT(*) n FROM cells WHERE partition='reader_fit' GROUP BY {v}").n.to_numpy() for k, v in {"donor":"donor_id","operator":"matrix_id","native_class":"native_class"}.items()}
    freeze_meta = {
        "schema": "foundation-discovery-sample-freeze-v1", "selection_seed": SEED,
        "frozen_before_selected_expression_read": True, "sample_a_rows": SAMPLE_N, "sample_b_rows": SAMPLE_N,
        "samples_disjoint": True, "original_t1_excluded": True,
        "sample_a": "donor-proportional largest-remainder quotas; deterministic minimum hash; empirical source/operator/class mixture retained within donor",
        "sample_b": "one deterministic representative per observed source/operator/native/broad/support stratum, then deterministic donor-primary round-robin fill",
        "manifest": {"path": freeze_path.name, "sha256": sha(freeze_path)},
        "controlling_inputs": {str(p.relative_to(ROOT)): sha(p) for p in [cfg_path, asset_path, split_path, old_path]},
        "firewalls": {"fit_donors": 104, "heldout_donors_metadata_only": 45, "heldout_expression_read": False, "dev_expression_read": False, "sealed_expression_read": False, "pathology_read": False},
    }
    freeze_json = OUT / "FOUNDATION_DISCOVERY_SAMPLE_FREEZE.json"
    freeze_json.write_text(json.dumps(freeze_meta, indent=2) + "\n")
    atlas = {
        "schema": "foundation-metadata-atlas-v1", "fit104_cells": total, "all149_train_cells": all_total,
        "fit_donors": 104, "heldout_donors_metadata_context_only": 45, "operators": 42,
        "original_t1_rows_exactly_matched": old_total, "original_t1_fraction_of_fit_inventory": old_total / total,
        "duplicates": {"source_scoped_cell_ids": len(duplicate_cell_ids), "stable_keys": len(duplicate_keys)},
        "missing_annotations": missing.to_dict("records"),
        "size_distributions": {k: {"min": int(v.min()), "q25": float(np.quantile(v,.25)), "median": float(np.median(v)), "q75": float(np.quantile(v,.75)), "max": int(v.max()), "gini": gini(v)} for k,v in sizes.items()},
        "support_counts_by_operator": support_counts, "matrix_audit": matrix_audit,
        "machine_tables": table_files, "database": {"path": DB.name, "sha256": sha(DB)},
        "controlling_inputs": freeze_meta["controlling_inputs"], "firewalls": freeze_meta["firewalls"],
    }
    atlas_json = OUT / "FOUNDATION_METADATA_ATLAS.json"
    atlas_json.write_text(json.dumps(atlas, indent=2) + "\n")
    md = f"""# FOUNDATION metadata atlas

The primary 104-donor training-design population contains **{total:,} cells** across 42 operators and 104 donors. The separate all-149 TRAIN metadata context contains **{all_total:,} cells**; expression from the 45 heldout donors was not read.

The original T1 cache matches {old_total:,} rows ({old_total/total:.4%}) of the fit inventory. Unequal abundance is described, not treated as a defect. Donor/operator/native-class Gini coefficients are {gini(sizes['donor']):.3f}, {gini(sizes['operator']):.3f}, and {gini(sizes['native_class']):.3f}.

Exact cross-tabs are the `FOUNDATION_METADATA_*.csv` files. The SQLite authority contains row-level lawful metadata only. Native source taxonomies remain source-native; blank values mean unavailable, not a fabricated common class. Stable-key and source-scoped cell-ID duplicate counts are {len(duplicate_keys)} and {len(duplicate_cell_ids)}. Completely absent combinations can be derived exactly from the published marginal/cross-tab tables; unobserved combinations were not materialized as millions of zero rows.

The two 25,000-cell manifests were selected from metadata and stable IDs only, are disjoint, and exclude the old T1 cache. Their manifest was hashed before any selected expression read.
"""
    (OUT / "FOUNDATION_METADATA_ATLAS.md").write_text(md, encoding="utf-8")
    print(json.dumps({"fit104": total, "all149": all_total, "old": old_total, "freeze_sha256": sha(freeze_path), "db_bytes": DB.stat().st_size}, indent=2))


if __name__ == "__main__":
    main()
