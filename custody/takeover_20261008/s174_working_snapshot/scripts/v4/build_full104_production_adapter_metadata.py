#!/usr/bin/env python3
"""Build the metadata-only FULL104 row locator from frozen source lineage.

This module never imports ProductionTrainLoader and never accesses an expression
matrix node. HVS/SEA-AD are enumerated from H5AD ``obs`` metadata only; NPH52 is
enumerated from the frozen disposition and physical-source manifests.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import sqlite3
from collections import Counter
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import yaml


EXPECTED_SOURCE_CELLS = {"HVS": 198_718, "NPH52": 236_476, "SEA_AD": 4_118_213}
EXPECTED_TOTAL = 4_553_407
EXPECTED_OPERATORS = 42
EXPECTED_FIT_DONORS = 104
EXPECTED_NPH_PHYSICAL_TRAIN = 288_116
EXPECTED_NPH_QUARANTINED_ALL149 = 22_715
STATE_NAMES = ["STRUCTURALLY_UNMEASURED", "MEASURED_SCALAR", "MEASURED_COLLISION_UNRESOLVED"]

ROW_COLUMNS = [
    "source", "operator_index", "matrix_id", "donor_id", "canonical_donor_id", "canonical_cell_id",
    "source_path", "source_row", "row_locator", "locator_kind",
    "eligibility_status", "reader_partition", "foundation_split",
    "observation_support_reference", "operator_state_sha256",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def clean(values: np.ndarray) -> np.ndarray:
    return np.asarray([
        "" if value is None else (
            value.decode("utf-8") if isinstance(value, (bytes, np.bytes_)) else str(value)
        ) for value in values
    ], dtype=object)


def read_h5_vector(obs: h5py.Group, name: str) -> np.ndarray:
    node = obs[name]
    if isinstance(node, h5py.Group) and "codes" in node and "categories" in node:
        codes = np.asarray(node["codes"])
        categories = clean(np.asarray(node["categories"]))
        return np.asarray([categories[int(code)] if int(code) >= 0 else "" for code in codes], dtype=object)
    return clean(np.asarray(node))


def project_relative(root: Path, raw_path: str) -> str:
    normalized = raw_path.replace("\\", "/")
    prefix = "/mnt/d/Jepa project/"
    if normalized.startswith(prefix):
        normalized = normalized[len(prefix):]
    candidate = Path(normalized)
    if candidate.is_absolute():
        try:
            return candidate.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            raise RuntimeError(f"source path is outside project authority: {raw_path}")
    return candidate.as_posix()


def deterministic_gzip_writer(path: Path):
    raw = path.open("wb")
    gz = gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=6, mtime=0)
    text = io.TextIOWrapper(gz, encoding="utf-8", newline="")
    return raw, gz, text, csv.writer(text, lineterminator="\n")


class Full104ProductionAdapter:
    """Metadata-only full-corpus row enumerator with fail-closed reconciliation."""

    def __init__(self, root: Path, out: Path):
        self.root = root.resolve()
        self.out = out.resolve()
        if self.out.exists():
            raise FileExistsError(self.out)
        self.out.mkdir(parents=True)
        self.shard_dir = self.out / "FULL104_ROW_LINEAGE_SHARDS"
        self.shard_dir.mkdir()

        self.paths = {
            "config": self.root / "configs/v4/stage81a3_foundation_heterogeneity_reality_audit.yaml",
            "assets": self.root / "results/v4/stage81a2_canonical_asset_registry.csv",
            "foundation_split": self.root / "results/v4/stage81a2_split_registry.csv",
            "reader_split": self.root / "exports/contextual_biology_v6r5a_20260822/reader_donor_split.csv",
            "operator_state": self.root / "exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz",
            "support_by_operator": self.root / "exports/foundation_corpus_discovery_v1/FOUNDATION_SUPPORT_BY_OPERATOR.csv",
            "donor_operator_authority": self.root / "exports/foundation_corpus_discovery_v1/FOUNDATION_METADATA_DONOR_X_OPERATOR.csv",
            "independent_atlas": self.root / "exports/foundation_corpus_discovery_v1/FOUNDATION_METADATA_ATLAS.json",
            "independent_rows": self.root / "exports/foundation_corpus_discovery_v1/foundation_metadata_rows.sqlite",
            "independent_inventory": self.root / "exports/prod41k_teacher_t1_20260823/T1_INVENTORY_EXPANSION_FEASIBILITY.json",
            "nph_disposition": self.root / "data/processed/v4/stage81a3/stage81a3_nph_disposition_detail.csv.gz",
            "nph_source_manifest": self.root / "data/processed/v4/stage81a2r/nph52_physical_split/nph52_physical_split_source_manifest.csv",
            "nph_exactness": self.root / "data/processed/v4/stage81a2r/nph52_physical_split/nph52_physical_split_exactness_manifest.csv",
        }
        missing = [str(path) for path in self.paths.values() if not path.is_file()]
        if missing:
            raise FileNotFoundError(missing)

        self.input_hashes = {key: sha256(path) for key, path in self.paths.items()}
        self.cfg = yaml.safe_load(self.paths["config"].read_text(encoding="utf-8"))
        self.reader = pd.read_csv(self.paths["reader_split"], dtype=str)
        counts = self.reader.reader_partition.value_counts().to_dict()
        if counts != {"reader_fit": 104, "reader_oracle": 23, "reader_validation": 22}:
            raise RuntimeError(f"reader donor firewall mismatch: {counts}")
        self.fit = set(self.reader.loc[self.reader.reader_partition.eq("reader_fit"), "donor_id"])
        self.held = set(self.reader.loc[~self.reader.reader_partition.eq("reader_fit"), "donor_id"])
        if self.fit & self.held:
            raise RuntimeError("reader-fit and protected TRAIN donors overlap")

        split = pd.read_csv(self.paths["foundation_split"], dtype=str)
        foundation_train = split[
            split.split_domain.eq("foundation") & split.split.eq("train")
        ].copy()
        foundation_train["source_donor_id"] = foundation_train.canonical_person_id.str.split("::", n=1).str[-1]
        if (
            len(foundation_train) != 149
            or foundation_train.source_donor_id.nunique() != 149
            or set(foundation_train.source_donor_id) != set(self.reader.donor_id)
        ):
            raise RuntimeError("reader split is not exactly the 149 FOUNDATION TRAIN donor set")
        if not foundation_train.pathology_used_for_foundation_split.str.lower().eq("false").all():
            raise RuntimeError("pathology contaminated the foundation split authority")
        self.fit_source_authority = dict(zip(foundation_train.source_donor_id, foundation_train.study_id))
        self.canonical_donor = dict(zip(foundation_train.source_donor_id, foundation_train.canonical_person_id))
        self.expected_source_donors = Counter(self.fit_source_authority[d] for d in self.fit)

        states_npz = np.load(self.paths["operator_state"], allow_pickle=False)
        if states_npz["states"].shape != (42, 41_238):
            raise RuntimeError("observation-state authority geometry mismatch")
        if states_npz["state_names"].astype(str).tolist() != STATE_NAMES:
            raise RuntimeError("observation-state names/ordering mismatch")
        operator_indices = states_npz["operator_index"].astype(int)
        if operator_indices.tolist() != list(range(42)):
            raise RuntimeError("operator indices are not exactly 0..41")
        matrix_ids = states_npz["matrix_id"].astype(str)
        if len(set(matrix_ids)) != 42:
            raise RuntimeError("operator matrix identifiers are not unique")
        self.operator_map = dict(zip(matrix_ids, operator_indices))
        self.state_hash = {
            matrix_id: hashlib.sha256(np.asarray(states_npz["states"][op], np.uint8).tobytes()).hexdigest()
            for matrix_id, op in self.operator_map.items()
        }
        self.support_ref = (
            "exports/foundation_calibration_bundle_20260824/support/"
            "FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"
            f"@sha256={self.input_hashes['operator_state']}"
        )

        self.aggregate = Counter()
        self.source_totals = Counter()
        self.observed_donor_source = {}
        self.shards = []
        self.total_rows = 0

        self.seen_db_path = self.out / "_ROW_IDENTITY_CHECK.sqlite"
        self.seen_db = sqlite3.connect(self.seen_db_path)
        self.seen_db.execute("PRAGMA journal_mode=OFF")
        self.seen_db.execute("PRAGMA synchronous=OFF")
        self.seen_db.execute(
            "CREATE TABLE seen(source TEXT, cell_id TEXT, PRIMARY KEY(source,cell_id)) WITHOUT ROWID"
        )

    def _record_identities(self, source: str, cell_ids: np.ndarray) -> None:
        try:
            self.seen_db.executemany(
                "INSERT INTO seen VALUES(?,?)",
                ((source, str(cell)) for cell in cell_ids),
            )
            self.seen_db.commit()
        except sqlite3.IntegrityError as exc:
            raise RuntimeError(f"duplicate source-scoped canonical cell identifier in {source}") from exc

    def _write_shard(
        self,
        source: str,
        matrix_id: str,
        donor_ids: np.ndarray,
        cell_ids: np.ndarray,
        source_rows: np.ndarray,
        source_path: str,
        locator_kind: str,
    ) -> None:
        if matrix_id not in self.operator_map:
            raise RuntimeError(f"matrix absent from 42-operator observation authority: {matrix_id}")
        if not (len(donor_ids) == len(cell_ids) == len(source_rows)):
            raise RuntimeError("row-vector length mismatch")
        if len(np.unique(source_rows)) != len(source_rows):
            raise RuntimeError(f"duplicate source row locator: {matrix_id}")
        if not np.all(np.diff(source_rows.astype(np.int64)) > 0):
            raise RuntimeError(f"source row locators are not strictly increasing: {matrix_id}")
        if not set(map(str, donor_ids)).issubset(self.fit):
            raise RuntimeError(f"non-reader-fit donor admitted: {matrix_id}")

        for donor in set(map(str, donor_ids)):
            expected_source = self.fit_source_authority[donor]
            if expected_source != source:
                raise RuntimeError(f"donor/source mismatch: {donor} expected {expected_source}, saw {source}")
            prior = self.observed_donor_source.setdefault(donor, source)
            if prior != source:
                raise RuntimeError(f"donor spans sources: {donor}")

        self._record_identities(source, cell_ids)
        op = self.operator_map[matrix_id]
        shard_path = self.shard_dir / f"part-operator-{op:02d}.csv.gz"
        raw, gz, text, writer = deterministic_gzip_writer(shard_path)
        writer.writerow(ROW_COLUMNS)
        for donor, cell, row in zip(donor_ids, cell_ids, source_rows):
            donor = str(donor); cell = str(cell); row = int(row)
            writer.writerow([
                source, op, matrix_id, donor, self.canonical_donor[donor], cell, source_path, row,
                f"{matrix_id}#{row}", locator_kind, "LAWFUL_READER_FIT",
                "reader_fit", "foundation/train", f"{self.support_ref}#operator={op}",
                self.state_hash[matrix_id],
            ])
            self.aggregate[(donor, matrix_id)] += 1
        text.flush(); text.detach(); gz.close(); raw.close()

        count = len(source_rows)
        self.source_totals[source] += count
        self.total_rows += count
        self.shards.append({
            "shard_id": f"operator-{op:02d}", "source": source,
            "operator_index": op, "matrix_id": matrix_id, "row_count": count,
            "source_path": source_path, "locator_kind": locator_kind,
            "first_source_row": int(source_rows[0]) if count else None,
            "last_source_row": int(source_rows[-1]) if count else None,
            "path": shard_path.relative_to(self.out).as_posix(),
            "bytes": shard_path.stat().st_size, "sha256": sha256(shard_path),
            "operator_state_sha256": self.state_hash[matrix_id],
        })

    def enumerate_h5ad_sources(self) -> None:
        assets = pd.read_csv(self.paths["assets"], dtype=str)
        eligible = assets[
            assets.study_id.isin(["HVS", "SEA_AD"])
            & assets.foundation_eligible.str.lower().eq("true")
        ].copy()
        if len(eligible) != 35 or eligible.dataset_id.nunique() != 35:
            raise RuntimeError("HVS/SEA-AD foundation asset set is not exactly 35 unique matrices")
        if eligible.dataset_id.str.contains("immune", case=False, regex=False).any():
            raise RuntimeError("SEA-AD immune/specialization duplicate admitted as an independent asset")
        if set(eligible.dataset_id) != {
            matrix_id for matrix_id in self.operator_map if not matrix_id.startswith("NPH52::")
        }:
            raise RuntimeError("HVS/SEA-AD asset set differs from operator-state authority")

        for asset in eligible.sort_values("dataset_id").itertuples(index=False):
            source = str(asset.study_id)
            matrix_id = str(asset.dataset_id)
            source_path = Path(str(asset.matrix_path_or_object)).as_posix()
            physical = self.root / source_path
            if not physical.is_file():
                raise FileNotFoundError(physical)
            allowed = self.cfg["allowed_metadata"][source]
            with h5py.File(physical, "r") as handle:
                if "obs" not in handle:
                    raise RuntimeError(f"H5AD missing obs metadata: {source_path}")
                obs = handle["obs"]
                donors = read_h5_vector(obs, allowed["donor"])
                cell_field = allowed["cell_id"] if allowed["cell_id"] in obs else "_index"
                cell_ids = read_h5_vector(obs, cell_field)
            if len(donors) != int(asset.n_obs) or len(cell_ids) != int(asset.n_obs):
                raise RuntimeError(f"asset obs length mismatch: {matrix_id}")
            selected = np.flatnonzero(np.isin(donors, list(self.fit)))
            self._write_shard(
                source, matrix_id, donors[selected], cell_ids[selected], selected.astype(np.int64),
                source_path, "h5ad_obs_row",
            )

    def enumerate_nph52(self) -> dict:
        exact = pd.read_csv(self.paths["nph_exactness"], dtype=str)
        train = exact[exact.partition.eq("TRAIN")].copy()
        if len(train) != 7 or not train.exact_lossless_subset_pass.str.lower().eq("true").all():
            raise RuntimeError("NPH52 physical TRAIN exactness authority mismatch")
        physical_train_total = int(train.cell_count.astype(int).sum())
        if physical_train_total != EXPECTED_NPH_PHYSICAL_TRAIN:
            raise RuntimeError(f"NPH52 physical TRAIN total mismatch: {physical_train_total}")

        source_manifest = pd.read_csv(self.paths["nph_source_manifest"], dtype=str)
        if len(source_manifest) != 7 or source_manifest.source_object_id.nunique() != 7:
            raise RuntimeError("NPH52 source-object manifest mismatch")
        source_paths = dict(zip(source_manifest.source_object_id, source_manifest.source_path))

        disposition = pd.read_csv(self.paths["nph_disposition"], dtype=str)
        disposition["source_row"] = disposition.groupby("source_object", sort=False).cumcount()
        lawful_all149 = disposition[
            disposition.foundation_eligibility.str.lower().eq("true")
            & disposition.donor_id.isin(set(self.reader.donor_id))
        ]
        lawful_all149_total = len(lawful_all149)
        quarantined = physical_train_total - lawful_all149_total
        if quarantined != EXPECTED_NPH_QUARANTINED_ALL149:
            raise RuntimeError(
                f"NPH52 quarantined-row count mismatch: {quarantined}; "
                f"physical={physical_train_total}, lawful_all149={lawful_all149_total}"
            )
        selected = lawful_all149[lawful_all149.donor_id.isin(self.fit)].copy()

        expected_objects = {
            matrix_id.removeprefix("NPH52::matrix::")
            for matrix_id in self.operator_map if matrix_id.startswith("NPH52::")
        }
        if set(selected.source_object) != expected_objects or set(source_paths) != expected_objects:
            raise RuntimeError("NPH52 source-object set differs from operator authority")
        for source_object, group in selected.groupby("source_object", sort=True):
            matrix_id = f"NPH52::matrix::{source_object}"
            rel_source = project_relative(self.root, source_paths[source_object])
            if not (self.root / rel_source).is_file():
                raise FileNotFoundError(self.root / rel_source)
            group = group.sort_values("source_row")
            self._write_shard(
                "NPH52", matrix_id,
                group.donor_id.astype(str).to_numpy(),
                group.source_cell_id.astype(str).to_numpy(),
                group.source_row.astype(np.int64).to_numpy(),
                rel_source, "nph52_source_object_row",
            )
        return {
            "physical_train_rows": physical_train_total,
            "lawful_all149_rows": lawful_all149_total,
            "quarantined_rows_not_admitted": quarantined,
            "fit104_rows": len(selected),
        }

    @staticmethod
    def _aggregate_frame(counter: Counter) -> pd.DataFrame:
        return pd.DataFrame([
            {"donor_id": donor, "matrix_id": matrix_id, "cell_count": count}
            for (donor, matrix_id), count in counter.items()
        ]).sort_values(["donor_id", "matrix_id"]).reset_index(drop=True)

    def reconcile(self, nph_audit: dict) -> dict:
        observed = self._aggregate_frame(self.aggregate)
        authority = pd.read_csv(self.paths["donor_operator_authority"], dtype={"donor_id": str, "matrix_id": str})
        authority = authority[["donor_id", "matrix_id", "cell_count"]].copy()
        authority["cell_count"] = authority.cell_count.astype(np.int64)
        authority = authority.sort_values(["donor_id", "matrix_id"]).reset_index(drop=True)
        merged = authority.merge(observed, on=["donor_id", "matrix_id"], how="outer", suffixes=("_authority", "_observed"), indicator=True)
        mismatched = merged[
            merged._merge.ne("both")
            | merged.cell_count_authority.fillna(-1).ne(merged.cell_count_observed.fillna(-1))
        ]

        with sqlite3.connect(self.paths["independent_rows"]) as con:
            independent = pd.read_sql_query(
                "SELECT donor_id,matrix_id,COUNT(*) cell_count FROM cells "
                "WHERE partition='reader_fit' GROUP BY donor_id,matrix_id",
                con,
            ).sort_values(["donor_id", "matrix_id"]).reset_index(drop=True)
            independent_total = int(pd.read_sql_query(
                "SELECT COUNT(*) n FROM cells WHERE partition='reader_fit'", con
            ).iloc[0, 0])
        independent["cell_count"] = independent.cell_count.astype(np.int64)
        independent_match = authority.equals(independent)

        source_totals = {source: int(self.source_totals[source]) for source in sorted(self.source_totals)}
        observed_donor_set = set(self.observed_donor_source)
        observed_source_donors = Counter(self.observed_donor_source.values())
        shard_ops = {int(shard["operator_index"]) for shard in self.shards}
        uniqueness_rows = int(self.seen_db.execute("SELECT COUNT(*) FROM seen").fetchone()[0])

        failures = []
        if len(mismatched): failures.append(f"donor_operator_mismatches={len(mismatched)}")
        if not independent_match: failures.append("independent_sqlite_aggregate_mismatch")
        if independent_total != EXPECTED_TOTAL: failures.append(f"independent_total={independent_total}")
        if self.total_rows != EXPECTED_TOTAL: failures.append(f"total={self.total_rows}")
        if source_totals != EXPECTED_SOURCE_CELLS: failures.append(f"source_totals={source_totals}")
        if observed_donor_set != self.fit: failures.append("fit_donor_set_mismatch")
        if observed_source_donors != self.expected_source_donors: failures.append(
            f"source_donor_composition observed={dict(observed_source_donors)} expected={dict(self.expected_source_donors)}"
        )
        if len(self.shards) != EXPECTED_OPERATORS or shard_ops != set(range(EXPECTED_OPERATORS)):
            failures.append("operator_set_mismatch")
        if uniqueness_rows != self.total_rows: failures.append(
            f"source_scoped_cell_identity_count={uniqueness_rows} total={self.total_rows}"
        )
        if nph_audit["quarantined_rows_not_admitted"] != EXPECTED_NPH_QUARANTINED_ALL149:
            failures.append("NPH_quarantine_mismatch")

        mismatch_path = self.out / "FULL104_METADATA_MISMATCHES.csv"
        mismatched.to_csv(mismatch_path, index=False, lineterminator="\n")
        return {
            "schema": "full104-metadata-reconciliation-v1",
            "status": "PASS_FULL104_PRODUCTION_SCOPE_RECONCILED" if not failures else "STOP_FULL104_METADATA_DISCREPANCY",
            "expression_read": False,
            "h5ad_groups_accessed": ["obs"],
            "expression_nodes_accessed": [],
            "fit_donors": len(observed_donor_set),
            "fit_donor_set_exact": observed_donor_set == self.fit,
            "source_fit_donors_derived": dict(sorted(observed_source_donors.items())),
            "source_fit_donors_authority_derived": dict(sorted(self.expected_source_donors.items())),
            "operators": len(shard_ops),
            "operator_set_exact_0_to_41": shard_ops == set(range(42)),
            "source_cells": source_totals,
            "total_cells": self.total_rows,
            "donor_operator_rows": len(observed),
            "donor_operator_authority_rows": len(authority),
            "donor_operator_mismatch_rows": len(mismatched),
            "independent_sqlite_aggregate_exact": independent_match,
            "independent_sqlite_total": independent_total,
            "source_scoped_cell_ids_unique": uniqueness_rows == self.total_rows,
            "unique_source_scoped_cell_ids": uniqueness_rows,
            "NPH52": nph_audit,
            "heldout_train_expression_read": False,
            "dev_expression_read": False,
            "sealed_expression_read": False,
            "pathology_read": False,
            "SEA_AD_immune_specialization_admitted": False,
            "failures": failures,
            "mismatch_table": mismatch_path.name,
        }

    def finalize(self) -> dict:
        self.enumerate_h5ad_sources()
        nph_audit = self.enumerate_nph52()
        reconciliation = self.reconcile(nph_audit)
        self.seen_db.close()
        self.seen_db_path.unlink()

        shard_manifest = pd.DataFrame(self.shards).sort_values("operator_index")
        shard_manifest.to_csv(self.out / "FULL104_ROW_LINEAGE.csv", index=False, lineterminator="\n")
        (self.out / "FULL104_METADATA_RECONCILIATION.json").write_text(
            json.dumps(reconciliation, indent=2) + "\n", encoding="utf-8"
        )
        provenance = {
            "schema": "full104-production-adapter-provenance-v1",
            "status": reconciliation["status"],
            "adapter_class": "Full104ProductionAdapter",
            "adapter_source": "scripts/v4/build_full104_production_adapter_metadata.py",
            "independent_of_production_train_loader_cell_table": True,
            "enumeration": {
                "HVS_SEA_AD": "direct H5AD obs metadata from exact foundation-eligible asset-registry paths",
                "NPH52": "frozen disposition rows plus exact physical source-object manifest",
                "aggregate_authority_not_used_to_create_rows": True,
                "row_shards": "42 deterministic gzip CSV shards, one per physical operator",
            },
            "row_schema": ROW_COLUMNS,
            "observation_semantics": {
                "state_names": STATE_NAMES,
                "measured_zero_is_evidence": True,
                "authority_path": self.paths["operator_state"].relative_to(self.root).as_posix(),
                "authority_sha256": self.input_hashes["operator_state"],
            },
            "controlling_inputs": {
                key: {"path": path.relative_to(self.root).as_posix(), "sha256": self.input_hashes[key]}
                for key, path in self.paths.items()
            },
            "firewall": {
                "reader_fit_only": True, "reader_fit_donors": 104,
                "reader_validation_expression_read": False,
                "reader_oracle_expression_read": False,
                "dev_expression_read": False, "sealed_expression_read": False,
                "pathology_read": False,
            },
        }
        (self.out / "FULL104_ADAPTER_PROVENANCE.json").write_text(
            json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
        )

        code_path = Path(__file__).resolve()
        manifest_rows = []
        for path in sorted(self.out.rglob("*")):
            if not path.is_file() or path.name == "FULL104_ADAPTER_SHA256_MANIFEST.csv":
                continue
            if path.name == "_ROW_IDENTITY_CHECK.sqlite":
                continue
            manifest_rows.append({
                "path": path.relative_to(self.out).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
        manifest_rows.append({
            "path": code_path.relative_to(self.root).as_posix(),
            "bytes": code_path.stat().st_size,
            "sha256": sha256(code_path),
        })
        pd.DataFrame(manifest_rows).sort_values("path").to_csv(
            self.out / "FULL104_ADAPTER_SHA256_MANIFEST.csv", index=False, lineterminator="\n"
        )
        if reconciliation["status"] != "PASS_FULL104_PRODUCTION_SCOPE_RECONCILED":
            raise RuntimeError(json.dumps(reconciliation, indent=2))
        return reconciliation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    adapter = Full104ProductionAdapter(args.project_root, args.out)
    result = adapter.finalize()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
