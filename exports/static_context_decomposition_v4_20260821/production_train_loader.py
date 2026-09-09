"""Frozen FOUNDATION TRAIN loader for the 41,238-address JEPA v4 contract.

The corrected sparse shards are deterministic materializations of the physical
TRAIN sources.  Observation state is carried separately from numeric values;
zero is therefore a legal measured scalar and never denotes missingness.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import scipy.sparse as sp

ROOT = Path(r"D:\Jepa project")
AUTH = Path(r"D:\Jepa project-stage81a3r-20260814")
CACHE = ROOT / "data/cache/stage81a3r_corrected_real_train"
RESULTS = ROOT / "results/v4"
AUTH_RESULTS = AUTH / "results/v4"
ADDRESS_COUNT = 41_238
SEMANTIC_HASH = "5fc4c03eeaf4b4aa69a46502df163851613585e0c6c38e65c4a2e87ab4bfc7ff"
PINNED_MANIFEST_SHA256 = "2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328"
STRUCTURALLY_UNMEASURED = np.uint8(0)
MEASURED_SCALAR = np.uint8(1)
MEASURED_COLLISION_UNRESOLVED = np.uint8(2)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ProductionTrainLoader:
    """Hash-addressed loader emitting values plus explicit observation states."""

    def __init__(self) -> None:
        registry_path = RESULTS / "stage81a2r_foundation_molecular_address_registry_candidate.csv"
        self.registry = pd.read_csv(registry_path)
        if len(self.registry) != ADDRESS_COUNT or str(self.registry.registry_semantic_hash.iloc[0]) != SEMANTIC_HASH:
            raise RuntimeError("frozen address authority mismatch")
        self.inputs = {
            "registry": registry_path,
            "support": RESULTS / "stage81a2r_foundation_molecular_address_measurement_support_candidate.csv.gz",
            "collision": AUTH_RESULTS / "stage81a3r_expression_materialization_collision_ledger.csv.gz",
            "supplemental": AUTH_RESULTS / "stage81a3r_scalar_mapping_unregistered_collisions.csv",
            "asset_registry": RESULTS / "stage81a2_canonical_asset_registry.csv",
            "nph_sample_manifest": ROOT / "data/processed/v4/stage81a3/stage81a3_nph_sample_manifest.csv",
            "foundation_split_registry": RESULTS / "stage81a2_split_registry.csv",
        }
        support = pd.read_csv(self.inputs["support"])
        collision = pd.read_csv(self.inputs["collision"], low_memory=False)
        supplemental = pd.read_csv(self.inputs["supplemental"])
        blocked = set(zip(collision.matrix_id.astype(str), collision.molecular_address_id.astype(str)))
        blocked.update(zip(supplemental.matrix_id.astype(str), supplemental.molecular_address_id.astype(str)))
        self.states: dict[str, np.ndarray] = {}
        for matrix_id, group in support.groupby("matrix_id", sort=False):
            ordered = group.sort_values("molecular_address_index")
            if ordered.molecular_address_id.astype(str).tolist() != self.registry.molecular_address_id.astype(str).tolist():
                raise RuntimeError(f"address order mismatch: {matrix_id}")
            measured = ordered.measured_address.astype(bool).to_numpy()
            unresolved = np.fromiter(((str(matrix_id), str(a)) in blocked for a in ordered.molecular_address_id), bool, ADDRESS_COUNT)
            state = np.full(ADDRESS_COUNT, STRUCTURALLY_UNMEASURED, dtype=np.uint8)
            state[measured] = MEASURED_SCALAR
            state[unresolved] = MEASURED_COLLISION_UNRESOLVED
            self.states[str(matrix_id)] = state
        self.items = self._inventory()
        pinned_path = Path(__file__).resolve().with_name("production_loader_manifest.json")
        if not pinned_path.exists() or sha256(pinned_path) != PINNED_MANIFEST_SHA256:
            raise RuntimeError("immutable production loader manifest missing or changed")
        import json
        self.verify_pinned_manifest(json.loads(pinned_path.read_text(encoding="utf-8")))

    def _inventory(self) -> list[dict[str, Any]]:
        assets = pd.read_csv(RESULTS / "stage81a2_canonical_asset_registry.csv")
        rows = []
        phase = assets[assets.study_id.isin(["HVS", "SEA_AD"]) & assets.foundation_eligible].sort_values("dataset_id")
        matrix_ids = phase.dataset_id.astype(str).tolist()
        manifest = pd.read_csv(ROOT / "data/processed/v4/stage81a3/stage81a3_nph_sample_manifest.csv")
        matrix_ids += ["NPH52::matrix::" + x for x in sorted(manifest.source_object.astype(str).unique())]
        for operator_index, matrix_id in enumerate(matrix_ids):
            stem = hashlib.sha256(f"corrected|{matrix_id}".encode()).hexdigest()[:16]
            counts, meta = CACHE / f"{stem}.counts.npz", CACHE / f"{stem}.meta.npz"
            if not counts.exists() or not meta.exists():
                raise RuntimeError(f"missing corrected TRAIN shard: {matrix_id}")
            rows.append({"operator_index": operator_index, "matrix_id": matrix_id, "counts": counts, "meta": meta})
        if len(rows) != 42 or set(matrix_ids) != set(self.states):
            raise RuntimeError("operator closure mismatch")
        return rows

    def cell_table(self) -> pd.DataFrame:
        rows = []
        for item in self.items:
            meta = np.load(item["meta"], allow_pickle=False)
            if set(meta.files) != {"donor_id", "cell_id", "broad_cell_class", "source_library"}:
                raise RuntimeError("unexpected metadata surface")
            for local_row in range(len(meta["cell_id"])):
                rows.append({"operator_index": item["operator_index"], "matrix_id": item["matrix_id"],
                    "local_row": local_row, "donor_id": str(meta["donor_id"][local_row]),
                    "cell_id": str(meta["cell_id"][local_row]), "broad_cell_class": str(meta["broad_cell_class"][local_row]),
                    "source_library": int(meta["source_library"][local_row])})
        return pd.DataFrame(rows)

    def load(self, selected: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        values = np.zeros((len(selected), ADDRESS_COUNT), np.float32)
        states = np.zeros((len(selected), ADDRESS_COUNT), np.uint8)
        for item in self.items:
            local = selected[selected.operator_index.eq(item["operator_index"])]
            if local.empty:
                continue
            counts = sp.load_npz(item["counts"]).tocsr()
            rows = local.local_row.to_numpy(np.int64)
            destinations = local.loader_row.to_numpy(np.int64)
            scalar = self.states[item["matrix_id"]] == MEASURED_SCALAR
            if counts[:, ~scalar].nnz:
                raise RuntimeError("numeric value outside MEASURED_SCALAR")
            matrix = counts[rows].astype(np.float32)
            library = local.source_library.to_numpy(np.float32)
            normalized = matrix.multiply((10_000.0 / np.maximum(library, 1.0))[:, None]).tocsr()
            normalized.data = np.log1p(normalized.data)
            values[destinations] = normalized.toarray()
            states[destinations] = self.states[item["matrix_id"]]
        return values, states

    def manifest(self) -> dict[str, Any]:
        return {"schema": "foundation-train-loader-v1", "semantic_hash": SEMANTIC_HASH,
            "address_count": ADDRESS_COUNT, "state_codes": {"STRUCTURALLY_UNMEASURED": 0,
            "MEASURED_SCALAR": 1, "MEASURED_COLLISION_UNRESOLVED": 2},
            "authority_hashes": {name: sha256(path) for name, path in self.inputs.items()},
            "shards": [{"matrix_id": x["matrix_id"], "counts_sha256": sha256(x["counts"]),
                "meta_sha256": sha256(x["meta"])} for x in self.items]}

    def verify_pinned_manifest(self, pinned: dict[str, Any]) -> None:
        current = self.manifest()
        if current != pinned:
            raise RuntimeError("production TRAIN authority/shard manifest drift")
