#!/usr/bin/env python3
"""Lane A+F: SEA-AD exact assay-origin audit and public cross-modal feasibility.

Chain built here, per FULL104 SEA-AD nucleus:

    FULL104 selection_row
      -> FULL104 row-lineage canonical_cell_id (= SEA-AD obs/exp_component_name)
      -> library identity (library token inside exp_component_name, plus obs/library_prep)
      -> assay origin  {SINGLEOME_RNA | MULTIOME_GEX | UNKNOWN}
      -> paired ATAC identity, if and only if the identical identifier is present
         in the public processed ATAC obs index with method == 10xMulti.

Governance: identity and provenance only. No expression value, no accessibility
value, no pathology field is read. The identity firewall is applied to every
column list BEFORE any join.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import h5py

sys.path.insert(0, str(Path(__file__).resolve().parent))
from laneAF_identity_firewall_v1 import (  # noqa: E402
    ForbiddenFieldError,
    assert_identity_only,
    forbidden_columns,
)

PROJECT = Path(r"D:/Jepa project")
LINEAGE_DIR = PROJECT / "outputs/full104_v014_20260826/01_full104_metadata_adapter"
LINEAGE_INDEX = LINEAGE_DIR / "FULL104_ROW_LINEAGE.csv"
SHARD_DIR = LINEAGE_DIR / "FULL104_ROW_LINEAGE_SHARDS"
ATAC_PATH = PROJECT / "data/external/v4/sea_ad/snatac/SEAAD_MTG_ATACseq_final-nuclei.2024-12-06.h5ad"
PRIOR_LINK_MANIFEST = PROJECT / "data/external/v4/sea_ad/manifests/mtg_exact_rna_atac_barcode_links.csv.gz"
SELECTION_MANIFEST = (
    PROJECT
    / "outputs/full104_v014_20260826/03_phase2_state_derivation_v1/metadata_selection_level4"
    / "PHASE2_METADATA_SELECTION_LEVEL4.csv.gz"
)
# Declared by the Level-4 materialization contract that the downstream consumers pin.
SELECTION_MANIFEST_SHA256 = "edec0fe29d1425ecbe9fa889a610c4ce18621ae060c8144866315db57c3fc62b"
SELECTION_IDENTITY_COLUMNS = ("selection_row", "source", "operator_index", "matrix_id", "donor_id", "canonical_cell_id")

# Columns this lane reads out of any SEA-AD h5ad obs. Nothing else is touched.
RNA_OBS_FIELDS = ("method", "library_prep", "Donor ID", "Brain Region")
ATAC_OBS_FIELDS = ("method", "library_prep", "Donor ID", "Brain Region")

MULTIOME_METHODS = frozenset({"10xMulti"})
SINGLEOME_RNA_METHODS = frozenset({"10Xv3.1", "10xV3.1_HT"})

CLASS_MULTIOME = "MULTIOME_GEX"
CLASS_SINGLEOME = "SINGLEOME_RNA"
CLASS_UNKNOWN = "UNKNOWN"


def sha256_file(path: Path, *, chunk: int = 8 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def decode(values) -> list[str]:
    return [v.decode("utf-8") if isinstance(v, bytes) else str(v) for v in values]


def read_obs_column(obs: h5py.Group, name: str) -> list[str]:
    node = obs[name]
    if isinstance(node, h5py.Dataset):
        return decode(node[...])
    if {"categories", "codes"}.issubset(set(node.keys())):
        categories = decode(node["categories"][...])
        codes = node["codes"][...]
        return [categories[int(c)] if int(c) >= 0 else "" for c in codes]
    raise RuntimeError("unsupported obs encoding for column " + repr(name))


def frame_index_name(frame: h5py.Group) -> str:
    key = frame.attrs.get("_index", "_index")
    if isinstance(key, bytes):
        key = key.decode()
    return str(key)


def library_token(cell_id: str) -> str:
    """Second hyphen-delimited field of a SEA-AD exp_component_name.

    Format is <barcode>-<library token>-<suffix>, and the suffix itself may
    contain hyphens (e.g. ...-NY-TX4091-2), so only the first two splits count.
    """
    first = cell_id.find("-")
    if first < 0:
        return ""
    second = cell_id.find("-", first + 1)
    if second < 0:
        return ""
    return cell_id[first + 1 : second]


def library_prefix(token: str) -> str:
    return token.split("_", 1)[0] if token else ""


def read_lineage_index() -> list[dict[str, str]]:
    with LINEAGE_INDEX.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def selection_row_offsets(index_rows: list[dict[str, str]]) -> tuple[dict[int, int], int]:
    """Global FULL104 selection_row offset for each operator_index.

    FULL104 rows are the concatenation of the 42 per-operator shards in
    ascending operator_index order; selection_row is the 0-based position in
    that concatenation. This is verified against an independent artifact rather
    than assumed (see the myeloid-panel positive control in the test module).
    """
    ordered = sorted(index_rows, key=lambda r: int(r["operator_index"]))
    offsets: dict[int, int] = {}
    running = 0
    for row in ordered:
        offsets[int(row["operator_index"])] = running
        running += int(row["row_count"])
    return offsets, running


def read_shard(operator_index: int) -> dict[str, list]:
    path = SHARD_DIR / ("part-operator-%02d.csv.gz" % operator_index)
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        hits = forbidden_columns(header)
        if hits:
            raise ForbiddenFieldError(
                "lineage shard " + path.name + " carries forbidden columns: " + repr(hits)
            )
        cell_ids: list[str] = []
        donors: list[str] = []
        source_rows: list[int] = []
        for record in reader:
            cell_ids.append(record["canonical_cell_id"])
            donors.append(record["donor_id"])
            source_rows.append(int(record["source_row"]))
    return {"cell_id": cell_ids, "donor_id": donors, "source_row": source_rows}


def load_atac_multiome_index() -> tuple[dict[str, int], dict[str, object]]:
    with h5py.File(ATAC_PATH, "r") as handle:
        obs = handle["obs"]
        index_name = frame_index_name(obs)
        requested = [index_name] + list(ATAC_OBS_FIELDS)
        assert_identity_only(requested, context="atac_obs_request")
        identifiers = read_obs_column(obs, index_name)
        methods = read_obs_column(obs, "method")
        donors = read_obs_column(obs, "Donor ID")
        libraries = read_obs_column(obs, "library_prep")
        regions = read_obs_column(obs, "Brain Region")
        var = handle["var"]
        var_index_name = frame_index_name(var)
        var_node = var[var_index_name]
        var_count = int(var_node.shape[0]) if isinstance(var_node, h5py.Dataset) else None
        var_example = None
        if isinstance(var_node, h5py.Dataset) and var_count:
            var_example = decode(var_node[0:3])
        exposure = {
            "obs_field_count": len(list(obs.keys())),
            "obs_field_names": sorted(obs.keys()),
            "obs_index_field": index_name,
            "n_obs_total": len(identifiers),
            "var_index_field": var_index_name,
            "var_feature_count": var_count,
            "var_index_example": var_example,
            "var_field_names": sorted(var.keys()),
            "x_encoding": str(handle["X"].attrs.get("encoding-type", "")) if "X" in handle else None,
            "x_shape": [int(v) for v in handle["X"].attrs.get("shape", [])] if "X" in handle else None,
            "obsm_keys": sorted(handle["obsm"].keys()) if "obsm" in handle else [],
            "layers_keys": sorted(handle["layers"].keys()) if "layers" in handle else [],
        }
    method_counts = Counter(methods)
    multiome_rows: dict[str, int] = {}
    multiome_donor: dict[str, str] = {}
    multiome_library: dict[str, str] = {}
    for position, (identifier, method) in enumerate(zip(identifiers, methods)):
        if method in MULTIOME_METHODS:
            multiome_rows[identifier] = position
            multiome_donor[identifier] = donors[position]
            multiome_library[identifier] = libraries[position]
    meta: dict[str, object] = {
        "atac_path": str(ATAC_PATH),
        "atac_method_counts": dict(sorted(method_counts.items())),
        "atac_multiome_nuclei": len(multiome_rows),
        "atac_duplicate_identifiers": len(identifiers) - len(set(identifiers)),
        "atac_donor_count_all": len(set(donors)),
        "atac_region_values": sorted(set(regions)),
        "atac_library_count_all": len(set(libraries)),
        "atac_multiome_donor_count": len(set(multiome_donor.values())),
        "atac_multiome_library_count": len(set(multiome_library.values())),
        "exposure": exposure,
    }
    return multiome_rows, meta


def attach_selection_rows(wanted: set) -> tuple[dict, dict]:
    """Resolve the AUTHORITATIVE FULL104 selection_row for a set of cell ids.

    selection_row is defined by the Level-4 Phase-2 metadata selection manifest
    (a donor-rank ordered nested ladder), NOT by the order in which the 42
    per-operator lineage shards concatenate. Deriving it from shard order gives
    the wrong answer for essentially every row; that is what the myeloid-panel
    positive control in the test module exists to catch.
    """
    observed_sha = sha256_file(SELECTION_MANIFEST)
    if observed_sha != SELECTION_MANIFEST_SHA256:
        raise RuntimeError(
            "selection manifest sha256 mismatch: observed "
            + observed_sha
            + " expected "
            + SELECTION_MANIFEST_SHA256
        )
    header_checked = False
    resolved: dict = {}
    duplicates: dict = {}
    seaad_rows = 0
    total_rows = 0
    with gzip.open(SELECTION_MANIFEST, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        for name in SELECTION_IDENTITY_COLUMNS:
            if name not in header:
                raise RuntimeError("selection manifest lacks required identity column " + name)
        assert_identity_only(list(SELECTION_IDENTITY_COLUMNS), context="selection_manifest_identity_projection")
        header_checked = True
        i_sel = header.index("selection_row")
        i_src = header.index("source")
        i_cell = header.index("canonical_cell_id")
        for row in reader:
            total_rows += 1
            if row[i_src] != "SEA_AD":
                continue
            seaad_rows += 1
            cell = row[i_cell]
            if cell in wanted:
                if cell in resolved:
                    duplicates[cell] = duplicates.get(cell, 1) + 1
                else:
                    resolved[cell] = int(row[i_sel])
    if not header_checked:
        raise RuntimeError("selection manifest header was never validated")
    stats = {
        "selection_manifest_path": str(SELECTION_MANIFEST),
        "selection_manifest_declared_sha256": SELECTION_MANIFEST_SHA256,
        "selection_manifest_observed_sha256": observed_sha,
        "selection_manifest_sha256_verified": True,
        "selection_manifest_total_rows": total_rows,
        "selection_manifest_seaad_rows": seaad_rows,
        "requested_cell_ids": len(wanted),
        "resolved_cell_ids": len(resolved),
        "unresolved_cell_ids": len(wanted) - len(resolved),
        "duplicate_cell_ids_in_manifest": len(duplicates),
    }
    return resolved, stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit-regions", default="")
    parser.add_argument("--hash-sources", action="store_true")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()

    index_rows = read_lineage_index()
    offsets, full104_total_rows = selection_row_offsets(index_rows)
    seaad_ops = [r for r in index_rows if r["source"] == "SEA_AD"]
    if args.limit_regions:
        keep = set(args.limit_regions.split(","))
        seaad_ops = [r for r in seaad_ops if r["matrix_id"] in keep]
    seaad_ops.sort(key=lambda r: int(r["operator_index"]))

    atac_multiome_rows, atac_meta = load_atac_multiome_index()
    print("[atac] multiome nuclei=%d" % len(atac_multiome_rows), flush=True)

    per_cell_rows: list[list] = []
    region_summary: list[dict] = []
    prefix_by_method: Counter = Counter()
    declared_regions: list[str] = []
    alignment_failures: list[str] = []
    global_counts: Counter = Counter()
    paired_donors: set = set()
    paired_libraries: Counter = Counter()
    paired_regions: Counter = Counter()
    multiome_donors: set = set()
    multiome_libraries: set = set()
    paired_by_matrix: Counter = Counter()
    total_mismatches = 0

    for record in seaad_ops:
        operator_index = int(record["operator_index"])
        matrix_id = record["matrix_id"]
        h5_path = PROJECT / record["source_path"]
        shard = read_shard(operator_index)
        n_rows = len(shard["cell_id"])
        if n_rows != int(record["row_count"]):
            raise RuntimeError(matrix_id + ": shard row count mismatch")
        offset = offsets[operator_index]

        with h5py.File(h5_path, "r") as handle:
            obs = handle["obs"]
            index_name = frame_index_name(obs)
            available = set(obs.keys())
            requested = [index_name] + [f for f in RNA_OBS_FIELDS if f in available]
            assert_identity_only(requested, context="rna_obs_request::" + matrix_id)
            obs_ids = read_obs_column(obs, index_name)
            obs_method = read_obs_column(obs, "method") if "method" in available else None
            obs_library = read_obs_column(obs, "library_prep") if "library_prep" in available else None
            obs_region = read_obs_column(obs, "Brain Region") if "Brain Region" in available else None

        declared = obs_method is not None
        if declared:
            declared_regions.append(matrix_id)

        counts: Counter = Counter()
        mismatches = 0
        first_mismatch = None
        region_paired = 0
        region_libraries: set = set()
        region_prefix_counts: Counter = Counter()

        for position in range(n_rows):
            source_row = shard["source_row"][position]
            cell_id = shard["cell_id"][position]
            if obs_ids[source_row] != cell_id:
                mismatches += 1
                if first_mismatch is None:
                    first_mismatch = matrix_id + "#" + str(source_row)
                continue
            token = library_token(cell_id)
            region_prefix_counts[library_prefix(token)] += 1
            if declared:
                method = obs_method[source_row]
                prefix_by_method[(library_prefix(token), method)] += 1
                if method in MULTIOME_METHODS:
                    assay = CLASS_MULTIOME
                elif method in SINGLEOME_RNA_METHODS:
                    assay = CLASS_SINGLEOME
                else:
                    assay = CLASS_UNKNOWN
                evidence = "DECLARED_OBS_METHOD"
            else:
                method = ""
                assay = CLASS_UNKNOWN
                evidence = "NO_DECLARED_METHOD_FIELD"
            counts[(assay, evidence)] += 1
            if assay == CLASS_MULTIOME:
                multiome_donors.add(shard["donor_id"][position])
                library_value = obs_library[source_row] if obs_library else token
                multiome_libraries.add(library_value)
                atac_row = atac_multiome_rows.get(cell_id)
                if atac_row is not None:
                    region_paired += 1
                    paired_donors.add(shard["donor_id"][position])
                    paired_libraries[library_value] += 1
                    paired_regions[obs_region[source_row] if obs_region else matrix_id] += 1
                    region_libraries.add(library_value)
                    paired_by_matrix[matrix_id] += 1
                    per_cell_rows.append(
                        [
                            -1,  # authoritative selection_row attached after the scan
                            matrix_id,
                            shard["donor_id"][position],
                            cell_id,
                            token,
                            library_value,
                            method,
                            CLASS_MULTIOME,
                            evidence,
                            cell_id,
                            atac_row,
                        ]
                    )

        total_mismatches += mismatches
        if mismatches:
            alignment_failures.append(
                matrix_id + ": " + str(mismatches) + " positional mismatches; first=" + str(first_mismatch)
            )

        region_summary.append(
            {
                "matrix_id": matrix_id,
                "operator_index": operator_index,
                "selection_row_offset": offset,
                "full104_rows": n_rows,
                "h5ad_path": record["source_path"],
                "h5ad_obs_rows": len(obs_ids),
                "declares_obs_method": declared,
                "positional_mismatches": mismatches,
                "library_prefix_counts": dict(sorted(region_prefix_counts.items())),
                "assay_counts": {a + "|" + e: c for (a, e), c in sorted(counts.items())},
                "exact_paired_atac_cells": region_paired,
                "paired_libraries": len(region_libraries),
            }
        )
        for key, value in counts.items():
            global_counts[key] += value
        print(
            "[%s] rows=%d declared=%s mismatch=%d paired=%d t=%.0fs"
            % (matrix_id, n_rows, declared, mismatches, region_paired, time.time() - started),
            flush=True,
        )

    prefix_to_methods: dict[str, set] = defaultdict(set)
    for (prefix, method), _count in prefix_by_method.items():
        prefix_to_methods[prefix].add(method)
    prefix_rule_deterministic = bool(prefix_to_methods) and all(
        len(v) == 1 for v in prefix_to_methods.values()
    )
    prefix_rule = {p: sorted(v)[0] for p, v in prefix_to_methods.items() if len(v) == 1}

    total_seaad = sum(global_counts.values())
    multiome_total = sum(c for (a, _e), c in global_counts.items() if a == CLASS_MULTIOME)
    singleome_total = sum(c for (a, _e), c in global_counts.items() if a == CLASS_SINGLEOME)
    unknown_total = sum(c for (a, _e), c in global_counts.items() if a == CLASS_UNKNOWN)
    paired_total = len(per_cell_rows)

    prior_link_rows = 0
    prior_link_ids: set = set()
    if PRIOR_LINK_MANIFEST.exists():
        with gzip.open(PRIOR_LINK_MANIFEST, "rt", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                prior_link_rows += 1
                prior_link_ids.add(row["rna_cell_id"])

    ours = set(r[3] for r in per_cell_rows)

    selection_map, selection_stats = attach_selection_rows(ours)
    for row in per_cell_rows:
        row[0] = selection_map.get(row[3], -1)
    unresolved_selection = sum(1 for r in per_cell_rows if r[0] < 0)
    if selection_stats["duplicate_cell_ids_in_manifest"]:
        raise RuntimeError("cell identifier is not unique in the FULL104 selection manifest")
    if unresolved_selection:
        raise RuntimeError(
            str(unresolved_selection) + " paired cells have no FULL104 selection_row; refusing to emit"
        )

    source_hashes = {}
    if args.hash_sources:
        for path in [LINEAGE_INDEX, PRIOR_LINK_MANIFEST, SELECTION_MANIFEST]:
            source_hashes[str(path)] = sha256_file(path)

    unresolved = multiome_total - paired_total
    controlled_flag = (
        "SEAAD_EXACT_PAIRING_REQUIRES_CONTROLLED_METADATA" if unresolved > 0 else "NOT_REQUIRED"
    )

    report = {
        "schema": "laneAF-seaad-assay-origin-audit-v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "full104_total_rows": full104_total_rows,
        "full104_seaad_rows_declared_by_lineage": sum(int(r["row_count"]) for r in seaad_ops),
        "full104_seaad_cells_checked": total_seaad,
        "positional_alignment_failures": alignment_failures,
        "positional_alignment_pass": not alignment_failures,
        "exact_public_metadata_matches": total_seaad,
        "positional_mismatch_cells": total_mismatches,
        "assay_counts_by_class_and_evidence": {
            a + "|" + e: c for (a, e), c in sorted(global_counts.items())
        },
        "singleome_rna_cells": singleome_total,
        "multiome_gex_cells": multiome_total,
        "unknown_assay_cells": unknown_total,
        "exact_paired_atac_cells": paired_total,
        "ambiguous_cells": 0,
        "unmatched_multiome_gex_cells": unresolved,
        "paired_subset_donor_count": len(paired_donors),
        "multiome_gex_donor_count": len(multiome_donors),
        "multiome_gex_library_count": len(multiome_libraries),
        "paired_subset_region_distribution": dict(sorted(paired_regions.items())),
        "paired_subset_library_count": len(paired_libraries),
        "paired_subset_library_distribution": dict(sorted(paired_libraries.items())),
        "paired_by_source_matrix": dict(sorted(paired_by_matrix.items())),
        "library_prefix_rule_deterministic_on_declared_regions": prefix_rule_deterministic,
        "library_prefix_to_declared_method": prefix_rule,
        "library_prefix_method_contingency": {
            p + "|" + m: c for (p, m), c in sorted(prefix_by_method.items())
        },
        "regions_declaring_obs_method": sorted(declared_regions),
        "regions_not_declaring_obs_method": sorted(
            r["matrix_id"] for r in seaad_ops if r["matrix_id"] not in declared_regions
        ),
        "atac_reference": atac_meta,
        "prior_manifest_path": str(PRIOR_LINK_MANIFEST),
        "prior_manifest_rows": prior_link_rows,
        "prior_manifest_overlap_with_full104_paired": len(ours & prior_link_ids),
        "prior_manifest_not_in_full104_paired": len(prior_link_ids - ours),
        "full104_paired_not_in_prior_manifest": len(ours - prior_link_ids),
        "controlled_metadata_flag": controlled_flag,
        "join_keys": {
            "full104_to_seaad_rna": "FULL104_ROW_LINEAGE shard (matrix_id, source_row) -> h5ad obs positional row; verified row-by-row by canonical_cell_id == obs/exp_component_name",
            "rna_to_assay_origin": "h5ad obs/method (declared): 10xMulti | 10Xv3.1 | 10xV3.1_HT",
            "full104_selection_row": "PHASE2_METADATA_SELECTION_LEVEL4.csv.gz canonical_cell_id -> selection_row; this manifest, not the lineage shard order, defines selection_row",
            "rna_to_atac": "exact string equality obs/exp_component_name (RNA) == obs/index (ATAC), both restricted to method == 10xMulti; no barcode transformation, no partial matching",
        },
        "selection_row_authority": selection_stats,
        "source_hashes": source_hashes,
        "wall_seconds": round(time.time() - started, 1),
    }

    (out / "SEAAD_ASSAY_ORIGIN_AUDIT_V1.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    with (out / "SEAAD_REGION_SUMMARY_V1.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "matrix_id",
            "operator_index",
            "selection_row_offset",
            "full104_rows",
            "h5ad_path",
            "h5ad_obs_rows",
            "declares_obs_method",
            "positional_mismatches",
            "library_prefix_counts",
            "assay_counts",
            "exact_paired_atac_cells",
            "paired_libraries",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in region_summary:
            writer.writerow(
                {k: (json.dumps(v, sort_keys=True) if isinstance(v, dict) else v) for k, v in row.items()}
            )

    header = [
        "selection_row",
        "matrix_id",
        "donor_id",
        "cell_id",
        "library_token",
        "library_prep",
        "method",
        "assay_origin",
        "assay_origin_evidence",
        "atac_cell_id",
        "atac_row",
    ]
    assert_identity_only(header, context="paired_cell_export")
    with gzip.open(
        out / "SEAAD_FULL104_EXACT_PAIRED_CELLS_V1.csv.gz", "wt", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(sorted(per_cell_rows))

    slim = {
        k: v
        for k, v in report.items()
        if k
        not in {
            "library_prefix_method_contingency",
            "atac_reference",
            "paired_subset_library_distribution",
        }
    }
    print(json.dumps(slim, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
