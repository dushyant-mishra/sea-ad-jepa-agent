#!/usr/bin/env python3
"""V79 Bayesian synthetic-geometry lane: the information firewall.

Every read of cell metadata in this lane goes through `load_cell_design`, which opens only the
allowlisted fields of the corrected S174 TRAIN meta shards and the V78 shard-to-operator bridge.
Anything on the denylist fails closed, by field name or by path. Gene identity is never read: the
corrected cache columns are already molecular-address indices, and addresses are used internally
only to align matrices. Every artifact meant for the synthetic generator passes `scrub` first,
which refuses gene, address or target identity.

Lane authority: TRAIN_ONLY__BAYESIAN_DATASET_GEOMETRY__NON_TARGET__NON_TRAINING__NON_PROMOTING
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

LANE_TERMINAL = "TRAIN_ONLY__BAYESIAN_DATASET_GEOMETRY__NON_TARGET__NON_TRAINING__NON_PROMOTING"

# Cell metadata fields this lane may read from the corrected cache meta shards. cell_id is used only to
# check row identity and is never written to any output.
ALLOWED_META_FIELDS = ("cell_id", "donor_id", "broad_cell_class", "source_library")
# Shard-level fields from the V78 bridge: which observation operator and which source a shard is.
ALLOWED_BRIDGE_FIELDS = ("stem", "operator_index", "source", "matrix_id")
# Split registry columns read to prove TRAIN-only scope. No other column is read.
ALLOWED_SPLIT_COLUMNS = ("split_domain", "study_id", "canonical_person_id", "split")

# Field names that must never be read or written in this lane (case-insensitive substring match).
DENY_FIELD_PATTERNS = (
    "patholog", "braak", "cerad", "thal", "adnc", "apoe", "diagnos", "dementia", "cognit", "alzheimer",
    "at8", "amyloid", "tau_", "ptau", "mmse", "case_control", "disease", "outcome", "clinical",
    "td56", "td57", "td58", "td59", "td60", "td_panel", "panel_member", "target_rank", "target_score",
    "scenic", "eregulon", "nott", "atac", "nih_card", "marker_program", "gene_symbol", "symbol",
    "ensembl", "ensg", "feature_name",
)
# Paths that must never be opened in this lane.
DENY_PATH_PATTERNS = (
    "morabito", "/test/", "_test_split", "sealed", "/dev/", "target_discovery", "td_relational",
    "scenic", "nott", "nih_card", "pathology", "protected",
)

# Frozen broad-class harmonization. The corrected TRAIN meta carries source-specific vocabularies; this
# maps every label to one of three broad classes by standard taxonomy. An unknown label fails closed.
BROAD_CLASSES = ("GABAergic", "Glutamatergic", "NonNeuronal")
CLASS_MAP = {
    "Neuronal: GABAergic": "GABAergic", "Neuronal: Glutamatergic": "Glutamatergic",
    "Non-neuronal and Non-neural": "NonNeuronal",
    "ExN": "Glutamatergic", "InN": "GABAergic",
    "Astro": "NonNeuronal", "Endo": "NonNeuronal", "MG": "NonNeuronal", "OPC": "NonNeuronal", "Oligo": "NonNeuronal",
    "STR D1 MSNSubclass": "GABAergic", "STR D2 MSNSubclass": "GABAergic", "STR Hybrid MSNSubclass": "GABAergic",
    "CN ST18 GABASubclass": "GABAergic", "CN LAMP5-CXCL14 GABASubclass": "GABAergic",
    "Sst ChodlSubclass": "GABAergic", "VipSubclass": "GABAergic",
    "AstrocyteSubclass": "NonNeuronal", "OPCSubclass": "NonNeuronal", "Microglia-PVMSubclass": "NonNeuronal",
    "OligodendrocyteSubclass": "NonNeuronal", "EndothelialSubclass": "NonNeuronal",
    "EpendymalSubclass": "NonNeuronal", "VLMCSubclass": "NonNeuronal",
}
CANONICAL_LABELS = ("Neuronal: GABAergic", "Neuronal: Glutamatergic", "Non-neuronal and Non-neural")

# Identity patterns that must never appear in a synthetic-consumable artifact.
_IDENTITY_PATTERNS = (re.compile(r"ENS[A-Z]*G\d{6,}"), re.compile(r"molecular_address", re.I),
                      re.compile(r"address_ind", re.I), re.compile(r"gene_id", re.I), re.compile(r"symbol", re.I),
                      re.compile(r"\bTD\d{2}", re.I), re.compile(r"panel", re.I), re.compile(r"target", re.I))


class FirewallError(RuntimeError):
    pass


def denied_field(name: str) -> bool:
    n = name.lower()
    return any(p in n for p in DENY_FIELD_PATTERNS)


def check_path(path) -> Path:
    p = Path(path)
    s = p.as_posix().lower()
    if any(x in s for x in DENY_PATH_PATTERNS):
        raise FirewallError(f"path denied by the V79 firewall: {p}")
    return p


def read_meta_shard(path) -> dict:
    """Open one meta shard and return only allowlisted fields. Any extra field is ignored unread; a
    denied field name present in the file is an error (the shard is not what this lane expects)."""
    p = check_path(path)
    with np.load(p, allow_pickle=False) as z:
        present = list(z.files)
        bad = [f for f in present if denied_field(f)]
        if bad:
            raise FirewallError(f"meta shard {p.name} carries denied fields {bad}")
        missing = [f for f in ALLOWED_META_FIELDS if f not in present]
        if missing:
            raise FirewallError(f"meta shard {p.name} lacks allowlisted fields {missing}")
        return {f: z[f] for f in ALLOWED_META_FIELDS}


def harmonize_class(labels) -> np.ndarray:
    out = []
    for lab in labels:
        if lab not in CLASS_MAP:
            raise FirewallError(f"unknown broad_cell_class label {lab!r}; the frozen map must be extended first")
        out.append(CLASS_MAP[lab])
    return np.asarray(out)


def load_bridge(bridge_path) -> list[dict]:
    rows = json.loads(check_path(bridge_path).read_text(encoding="utf-8"))["rows"]
    return [{k: r[k] for k in ALLOWED_BRIDGE_FIELDS} for r in rows]


def load_cell_design(cache_root, bridge_path) -> dict:
    """The cell-level design of the corrected TRAIN cache: one row per cell, allowlisted fields only."""
    root = check_path(cache_root)
    cols = {k: [] for k in ("donor_id", "raw_class", "source_library", "operator", "source", "stem", "row")}
    for r in sorted(load_bridge(bridge_path), key=lambda r: r["operator_index"]):
        m = read_meta_shard(root / f"{r['stem']}.meta.npz")
        n = len(m["cell_id"])
        if len(set(m["cell_id"].tolist())) != n:
            raise FirewallError(f"duplicate cell_id inside shard {r['stem']}")
        cols["donor_id"] += m["donor_id"].astype(str).tolist()
        cols["raw_class"] += m["broad_cell_class"].astype(str).tolist()
        cols["source_library"] += m["source_library"].astype(np.int64).tolist()
        cols["operator"] += [int(r["operator_index"])] * n
        cols["source"] += [r["source"]] * n
        cols["stem"] += [r["stem"]] * n
        cols["row"] += list(range(n))
    d = {k: np.asarray(v) for k, v in cols.items()}
    d["broad_class"] = harmonize_class(d["raw_class"])
    d["canonical_label"] = np.isin(d["raw_class"], CANONICAL_LABELS)
    return d


def _walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield f"{path}.{k}", str(k)
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def scrub(artifact: dict) -> dict:
    """Refuse a synthetic-consumable artifact that carries gene, address, target or protected identity.
    Returns the artifact unchanged when it is clean; never edits it into compliance."""
    hits = []
    for where, text in _walk(artifact):
        if denied_field(text) or any(p.search(text) for p in _IDENTITY_PATTERNS):
            hits.append((where, text[:80]))
    if hits:
        raise FirewallError(f"synthetic-consumable artifact carries identity: {hits[:10]}")
    return artifact
