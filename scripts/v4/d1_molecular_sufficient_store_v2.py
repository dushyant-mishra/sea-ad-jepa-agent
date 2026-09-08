#!/usr/bin/env python3
"""Sparse on-disk molecular sufficient-statistic store for D1 V2.

One pass over the exact aligned expression shards computes all D1 discovery
objects simultaneously. Only genuinely address-dependent terms are stored:

  sum_x[g]
  sum_score_expression[j,g]

Measured mass, sum_score and sum_score_squared are *not* redundantly stored as
J x 41,238 arrays. Observation state is constant within an operator, so those
terms are exactly reconstructed from compact donor x operator score moments and
the frozen operator-address measurement mask.

The store keeps donor and operator molecular sufficient statistics. Global and
source statistics are exact sums of donor stores, because the full-fit metadata
requires each lawful donor to belong to one source family.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import scipy.sparse as sp

from d1_expression_reader_v2 import PortableExpressionReader
from d1_score_archive_v2 import ArchivedScoreSource
from d1_teacher_state_archive_v2 import ArchivedStrataSource
from d1_real_data_derivation_core_v1 import (
    MEASURED_SCALAR,
    assert_donor_primary_masses,
    derive_donor_operator_weights,
)

SCHEMA = "D1_MOLECULAR_SUFFICIENT_STORE_V2"
MANIFEST_NAME = "D1_MOLECULAR_SUFFICIENT_STORE_V2.json"
COMPACT_NAME = "D1_MOLECULAR_STRATUM_MOMENTS_V2.npz"
STOP_STORE_INVALID = "STOP_D1_V2_MOLECULAR_STORE_INVALID"
STOP_STORE_DRIFT = "STOP_D1_V2_MOLECULAR_STORE_DRIFT"
STOP_STORE_ALIGNMENT = "STOP_D1_V2_MOLECULAR_STORE_ALIGNMENT"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(payload: Any) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def payload_root(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def _safe_token(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _sparse_crossproducts(
    expression: sp.csr_matrix, scores: np.ndarray, weights: np.ndarray
) -> tuple[sp.csc_matrix, sp.csc_matrix]:
    """Return sum_x and sum(score*x) with float64 accumulation."""
    x = expression.tocsr()
    s = np.asarray(scores, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64).reshape(-1)
    if x.shape[0] != s.shape[0] or s.shape[0] != w.size:
        raise ValueError(f"{STOP_STORE_INVALID}: expression/score/weight rows")
    if np.any(w < 0) or not np.all(np.isfinite(w)) or not np.all(np.isfinite(s)):
        raise ValueError(f"{STOP_STORE_INVALID}: score/weight")
    weighted_scores = s * w[:, None]
    sum_sx_dense = np.asarray(x.T.dot(weighted_scores), dtype=np.float64).T
    sum_x_dense = np.asarray(x.T.dot(w), dtype=np.float64).reshape(1, -1)
    # Exact zeros stay sparse. A measured all-zero address is distinguished later
    # by the operator measurement mask, not by forcing a stored numeric zero.
    return (
        sp.csc_matrix(sum_x_dense),
        sp.csc_matrix(sum_sx_dense),
    )


def materialize_molecular_store(
    *,
    teacher_archive_dir: Path | str,
    score_archive_dir: Path | str,
    score_archive_root_sha256: str,
    expression_reader: PortableExpressionReader,
    expression_location_manifest_sha256: str,
    population_audit_root_sha256: str,
    output_dir: Path | str,
) -> dict[str, Any]:
    teacher = ArchivedStrataSource(teacher_archive_dir)
    score_source = ArchivedScoreSource(score_archive_dir)
    score_manifest_root = str(
        score_source.manifest.get("score_archive_root_sha256") or "")
    if score_manifest_root != str(score_archive_root_sha256):
        raise ValueError(f"{STOP_STORE_DRIFT}: score archive root")
    teacher_root = str(teacher.manifest.get("archive_root_sha256") or "")
    if score_source.manifest.get("teacher_archive_root_sha256") != teacher_root:
        raise ValueError(f"{STOP_STORE_DRIFT}: teacher/score archive binding")
    if teacher.strata() != score_source.strata():
        raise ValueError(f"{STOP_STORE_ALIGNMENT}: teacher/score strata")
    program_ids = list(score_source.program_ids)
    J = len(program_ids)
    A = int(expression_reader.observation["states"].shape[1])
    if J <= 0 or A <= 0:
        raise ValueError(f"{STOP_STORE_INVALID}: program/address dimensions")

    counts = {
        (str(e["donor_id"]), int(e["operator_index"])): int(e["rows"])
        for e in teacher.manifest["entries"]
    }
    weights = derive_donor_operator_weights(counts)
    assert_donor_primary_masses(weights)

    strata = teacher.strata()
    donor_names = sorted({d for d, _ in strata})
    operator_names = sorted({o for _, o in strata})
    donor_source: dict[str, str] = {}
    donor_sum_x: dict[str, sp.csc_matrix] = {
        d: sp.csc_matrix((1, A), dtype=np.float64) for d in donor_names
    }
    donor_sum_sx: dict[str, sp.csc_matrix] = {
        d: sp.csc_matrix((J, A), dtype=np.float64) for d in donor_names
    }

    destination = Path(output_dir)
    if destination.exists():
        raise FileExistsError(f"{STOP_STORE_INVALID}: output exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(
        prefix=destination.name + ".tmp.", dir=destination.parent))

    compact_rows = []
    operator_entries = []
    total_rows = 0
    try:
        # Operator-major traversal loads each physical sparse counts shard once.
        by_operator: dict[int, list[str]] = {}
        for donor, operator in strata:
            by_operator.setdefault(int(operator), []).append(str(donor))

        for operator in sorted(by_operator):
            operator_sum_x = sp.csc_matrix((1, A), dtype=np.float64)
            operator_sum_sx = sp.csc_matrix((J, A), dtype=np.float64)
            for donor in sorted(set(by_operator[operator])):
                key = (donor, operator)
                expected_ids = teacher.cell_ids(donor, operator)
                expression = expression_reader.load_sparse_stratum(
                    donor_id=donor, operator_index=operator,
                    expected_cell_ids=expected_ids)
                scores = np.asarray(score_source.load(donor, operator), dtype=np.float64)
                if scores.shape != (len(expected_ids), J):
                    raise ValueError(f"{STOP_STORE_ALIGNMENT}: score rows/width {key}")
                if expression["canonical_cell_id"] != expected_ids:
                    raise ValueError(f"{STOP_STORE_ALIGNMENT}: expression cell order {key}")
                expected_n = int(counts[key])
                if len(expected_ids) != expected_n:
                    raise ValueError(f"{STOP_STORE_ALIGNMENT}: row count {key}")
                cell_weight = float(weights["cell_weight_a_dc"][key])
                w = np.full(expected_n, cell_weight, dtype=np.float64)
                sum_x, sum_sx = _sparse_crossproducts(
                    expression["expression_csr"], scores, w)
                operator_sum_x = operator_sum_x + sum_x
                operator_sum_sx = operator_sum_sx + sum_sx
                donor_sum_x[donor] = donor_sum_x[donor] + sum_x
                donor_sum_sx[donor] = donor_sum_sx[donor] + sum_sx

                source = str(expression["source"])
                if donor in donor_source and donor_source[donor] != source:
                    raise ValueError(
                        f"{STOP_STORE_ALIGNMENT}: donor {donor} crosses sources "
                        f"{donor_source[donor]} and {source}")
                donor_source[donor] = source
                compact_rows.append({
                    "donor_id": donor,
                    "source": source,
                    "operator_index": int(operator),
                    "rows": expected_n,
                    "weight_mass": float(w.sum()),
                    "score_sum": np.sum(scores * w[:, None], axis=0),
                    "score_squared_sum": np.sum(
                        scores * scores * w[:, None], axis=0),
                })
                total_rows += expected_n

            x_path = temporary / f"operator_{operator:02d}.sum_x.npz"
            sx_path = temporary / f"operator_{operator:02d}.sum_sx.npz"
            sp.save_npz(x_path, operator_sum_x, compressed=True)
            sp.save_npz(sx_path, operator_sum_sx, compressed=True)
            operator_entries.append({
                "operator_index": int(operator),
                "sum_x_file": x_path.name,
                "sum_x_sha256": sha256_file(x_path),
                "sum_sx_file": sx_path.name,
                "sum_sx_sha256": sha256_file(sx_path),
            })
            expression_reader.release_operator(operator)

        donor_entries = []
        for donor in donor_names:
            if donor not in donor_source:
                raise ValueError(f"{STOP_STORE_ALIGNMENT}: donor {donor} has no source")
            token = _safe_token("donor", donor)
            x_path = temporary / f"{token}.sum_x.npz"
            sx_path = temporary / f"{token}.sum_sx.npz"
            sp.save_npz(x_path, donor_sum_x[donor], compressed=True)
            sp.save_npz(sx_path, donor_sum_sx[donor], compressed=True)
            donor_entries.append({
                "donor_id": donor,
                "source": donor_source[donor],
                "sum_x_file": x_path.name,
                "sum_x_sha256": sha256_file(x_path),
                "sum_sx_file": sx_path.name,
                "sum_sx_sha256": sha256_file(sx_path),
            })

        compact_rows.sort(key=lambda r: (r["donor_id"], r["operator_index"]))
        score_sum = np.stack([r["score_sum"] for r in compact_rows], axis=0)
        score_squared_sum = np.stack(
            [r["score_squared_sum"] for r in compact_rows], axis=0)
        np.savez(
            temporary / COMPACT_NAME,
            donor_id=np.asarray([r["donor_id"] for r in compact_rows]),
            source=np.asarray([r["source"] for r in compact_rows]),
            operator_index=np.asarray(
                [r["operator_index"] for r in compact_rows], dtype=np.int32),
            rows=np.asarray([r["rows"] for r in compact_rows], dtype=np.int64),
            weight_mass=np.asarray(
                [r["weight_mass"] for r in compact_rows], dtype=np.float64),
            score_sum=score_sum.astype(np.float64),
            score_squared_sum=score_squared_sum.astype(np.float64),
        )
        compact_sha = sha256_file(temporary / COMPACT_NAME)

        manifest = {
            "schema": SCHEMA,
            "status": "FROZEN_DATA_ONLY_SUFFICIENT_STORE",
            "teacher_archive_root_sha256": teacher_root,
            "score_archive_root_sha256": str(score_archive_root_sha256),
            "derivation_root_sha256": score_source.manifest["derivation_root_sha256"],
            "teacher_checkpoint_sha256": teacher.manifest["teacher_checkpoint_sha256"],
            "readout_contract_sha256": teacher.manifest["readout_contract_sha256"],
            "expression_location_manifest_sha256":
                str(expression_location_manifest_sha256),
            "population_audit_root_sha256": str(population_audit_root_sha256),
            "observation_state_sha256": expression_reader.observation["sha256"],
            "program_ids": program_ids,
            "programs": J,
            "addresses": A,
            "rows": total_rows,
            "strata": len(compact_rows),
            "donors": len(donor_names),
            "operators": len(operator_names),
            "sources": sorted(set(donor_source.values())),
            "compact_file": COMPACT_NAME,
            "compact_sha256": compact_sha,
            "donor_entries": donor_entries,
            "operator_entries": operator_entries,
            "storage_semantics": {
                "sum_x": "sparse float64 weighted sum of normalized expression",
                "sum_sx": "sparse float64 weighted sum of program_score * expression",
                "mass_sum_s_sum_s2":
                    "reconstructed exactly from compact stratum moments and "
                    "operator MEASURED_SCALAR masks",
                "measured_zero": "retained as estimable numeric zero",
                "structurally_unmeasured": "excluded by observation-state mask",
            },
        }
        manifest["molecular_store_root_sha256"] = payload_root(manifest)
        (temporary / MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n")
        os.replace(temporary, destination)
        return manifest
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def verify_molecular_store(
    store_dir: Path | str,
    *,
    expected_score_archive_root: str | None = None,
    expected_population_audit_root: str | None = None,
) -> dict[str, Any]:
    root = Path(store_dir)
    path = root / MANIFEST_NAME
    if not path.is_file():
        raise FileNotFoundError(f"{STOP_STORE_INVALID}: missing manifest")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != SCHEMA:
        raise ValueError(f"{STOP_STORE_INVALID}: schema")
    body = dict(payload)
    claimed = str(body.pop("molecular_store_root_sha256", ""))
    if payload_root(body) != claimed:
        raise ValueError(f"{STOP_STORE_DRIFT}: root")
    if expected_score_archive_root is not None and payload.get(
        "score_archive_root_sha256") != expected_score_archive_root:
        raise ValueError(f"{STOP_STORE_DRIFT}: score archive root")
    if expected_population_audit_root is not None and payload.get(
        "population_audit_root_sha256") != expected_population_audit_root:
        raise ValueError(f"{STOP_STORE_DRIFT}: population audit root")
    compact = root / str(payload["compact_file"])
    if sha256_file(compact) != str(payload["compact_sha256"]):
        raise ValueError(f"{STOP_STORE_DRIFT}: compact moments")
    for collection in ("donor_entries", "operator_entries"):
        for entry in payload.get(collection, []):
            for prefix in ("sum_x", "sum_sx"):
                file_path = root / str(entry[f"{prefix}_file"])
                if sha256_file(file_path) != str(entry[f"{prefix}_sha256"]):
                    raise ValueError(
                        f"{STOP_STORE_DRIFT}: {collection} {prefix} "
                        f"{entry.get('donor_id', entry.get('operator_index'))}")
    compact_data = np.load(compact, allow_pickle=False)
    if compact_data["score_sum"].shape != (
        int(payload["strata"]), int(payload["programs"])
    ):
        raise ValueError(f"{STOP_STORE_INVALID}: compact score_sum shape")
    if int(np.sum(compact_data["rows"])) != int(payload["rows"]):
        raise ValueError(f"{STOP_STORE_INVALID}: row total")
    if len(payload["donor_entries"]) != int(payload["donors"]):
        raise ValueError(f"{STOP_STORE_INVALID}: donor total")
    if len(payload["operator_entries"]) != int(payload["operators"]):
        raise ValueError(f"{STOP_STORE_INVALID}: operator total")
    return {
        "terminal": "PASS_D1_V2_MOLECULAR_SUFFICIENT_STORE",
        "molecular_store_root_sha256": claimed,
        "rows": int(payload["rows"]),
        "strata": int(payload["strata"]),
        "programs": int(payload["programs"]),
        "addresses": int(payload["addresses"]),
    }


class MolecularStore:
    def __init__(self, store_dir: Path | str, observation_states: np.ndarray) -> None:
        self.root = Path(store_dir)
        self.manifest = json.loads(
            (self.root / MANIFEST_NAME).read_text(encoding="utf-8"))
        if self.manifest.get("schema") != SCHEMA:
            raise ValueError(f"{STOP_STORE_INVALID}: schema")
        self.program_ids = [str(x) for x in self.manifest["program_ids"]]
        self.J = int(self.manifest["programs"])
        self.A = int(self.manifest["addresses"])
        self.observation_states = np.asarray(observation_states, dtype=np.uint8)
        if self.observation_states.shape != (42, self.A):
            raise ValueError(f"{STOP_STORE_INVALID}: observation-state shape")
        compact = np.load(
            self.root / self.manifest["compact_file"], allow_pickle=False)
        self.donor_id = np.asarray(compact["donor_id"]).astype(str)
        self.source = np.asarray(compact["source"]).astype(str)
        self.operator_index = np.asarray(compact["operator_index"], dtype=np.int64)
        self.rows = np.asarray(compact["rows"], dtype=np.int64)
        self.weight_mass = np.asarray(compact["weight_mass"], dtype=np.float64)
        self.score_sum = np.asarray(compact["score_sum"], dtype=np.float64)
        self.score_squared_sum = np.asarray(
            compact["score_squared_sum"], dtype=np.float64)
        self._donor = {
            str(e["donor_id"]): e for e in self.manifest["donor_entries"]
        }
        self._operator = {
            int(e["operator_index"]): e for e in self.manifest["operator_entries"]
        }

    def donors(self) -> list[str]:
        return sorted(self._donor)

    def operators(self) -> list[int]:
        return sorted(self._operator)

    def sources(self) -> list[str]:
        return sorted(set(self.source.tolist()))

    def _load_pair(self, entry: Mapping[str, Any]) -> tuple[sp.csc_matrix, sp.csc_matrix]:
        return (
            sp.load_npz(self.root / str(entry["sum_x_file"])).tocsc(),
            sp.load_npz(self.root / str(entry["sum_sx_file"])).tocsc(),
        )

    def donor_sparse(self, donor: str) -> tuple[sp.csc_matrix, sp.csc_matrix]:
        return self._load_pair(self._donor[str(donor)])

    def operator_sparse(self, operator: int) -> tuple[sp.csc_matrix, sp.csc_matrix]:
        return self._load_pair(self._operator[int(operator)])

    def stratum_indices(
        self, *, donor: str | None = None, operator: int | None = None,
        source: str | None = None,
    ) -> np.ndarray:
        mask = np.ones(self.donor_id.size, dtype=bool)
        if donor is not None:
            mask &= self.donor_id == str(donor)
        if operator is not None:
            mask &= self.operator_index == int(operator)
        if source is not None:
            mask &= self.source == str(source)
        return np.flatnonzero(mask)

    def reconstruct_masked_score_moments(
        self, indices: Sequence[int], *, address_slice: slice | None = None,
    ) -> dict[str, np.ndarray]:
        idx = np.asarray(indices, dtype=np.int64)
        if idx.size == 0:
            raise ValueError(f"{STOP_STORE_INVALID}: empty group")
        sl = address_slice if address_slice is not None else slice(0, self.A)
        width = len(range(*sl.indices(self.A)))
        mass = np.zeros(width, dtype=np.float64)
        sum_s = np.zeros((self.J, width), dtype=np.float64)
        sum_s2 = np.zeros((self.J, width), dtype=np.float64)
        for i in idx:
            op = int(self.operator_index[i])
            measured = (
                self.observation_states[op, sl] == MEASURED_SCALAR
            ).astype(np.float64)
            mass += float(self.weight_mass[i]) * measured
            sum_s += self.score_sum[i][:, None] * measured[None, :]
            sum_s2 += self.score_squared_sum[i][:, None] * measured[None, :]
        return {"mass": mass, "sum_s": sum_s, "sum_s2": sum_s2}

    def donor_source(self, donor: str) -> str:
        return str(self._donor[str(donor)]["source"])
