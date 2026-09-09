"""Dataset-bound technical-input evidence for T0.

This module exists to prevent a correct-looking set of authority-root strings
from travelling beside caller-created source_library or Q_DETECT inputs.

Production evidence is derived from the frozen dataset substrate itself:

* SEA-AD MTG H5AD: exact authenticated raw CSR row at expression_row;
* Phase2 materialized block: exact authenticated CSR row at block-local row_index;
* B1 T0 projection: exact 35,076 molecular-address indices;
* B2 closure/logical/physical roots: all externally verified before extraction.

No pathology value is read and real_execution_ready remains False.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

import t0_v20_feature_projection_authority_v1 as fp
import t0_v20_row_count_authority_v1 as rc

SCHEMA = "JEPA_T0_DATASET_BOUND_TECHNICAL_INPUT_EVIDENCE_V1"
NAMESPACE = "T0-DATASET-BOUND-TECHNICAL-INPUT-EVIDENCE-V1"
DOMAIN_TAG = "T0-DATASET-BOUND-TECHNICAL-INPUT-EVIDENCE-V1-TYPED"

EXPECTED_TARGET_CELLS = 20_804
EXPECTED_CANDIDATE_DONORS = 46
EXPECTED_PROJECTED_FEATURES = 35_076

STOP_PARENT = "STOP_T0_TECHNICAL_EVIDENCE_PARENT_AUTHORITY_MISMATCH"
STOP_COUNTS = "STOP_T0_TECHNICAL_EVIDENCE_COUNTS_PAYLOAD_INVALID"
STOP_PROJECTION = "STOP_T0_TECHNICAL_EVIDENCE_PROJECTION_INVALID"
STOP_DONOR_SET = "STOP_T0_TECHNICAL_EVIDENCE_DONOR_SET_MISMATCH"
STOP_ROOT = "STOP_T0_TECHNICAL_EVIDENCE_ROOT_MISMATCH"
STOP_SCHEMA = "STOP_T0_TECHNICAL_EVIDENCE_SCHEMA_INVALID"
STOP_PATH = "STOP_T0_TECHNICAL_EVIDENCE_COUNTS_PATH_INVALID"


def _typed(value: Any) -> bytes:
    if isinstance(value, bool):
        tag, payload = b"b", (b"1" if value else b"0")
    elif isinstance(value, int):
        tag, payload = b"i", str(value).encode("ascii")
    elif isinstance(value, str):
        tag, payload = b"s", value.encode("utf-8")
    elif isinstance(value, (list, tuple)):
        tag = b"l"
        payload = b"".join(_typed(v) for v in value)
        payload = str(len(value)).encode("ascii") + b":" + payload
    else:
        raise AssertionError("%s: cannot frame %s"
                             % (STOP_SCHEMA, type(value).__name__))
    return tag + str(len(payload)).encode("ascii") + b":" + payload


def _safe_child(root: Path, relative: str) -> Path:
    rel = Path(str(relative))
    if rel.is_absolute() or ".." in rel.parts:
        raise AssertionError("%s: %r is not a repository-relative block path"
                             % (STOP_PATH, relative))
    base = root.resolve()
    candidate = (base / rel).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise AssertionError("%s: %r escapes counts root"
                             % (STOP_PATH, relative)) from exc
    return candidate


def _projection_indices(
    feature_authority: Mapping[str, Any],
    *,
    expected_feature_authority_root_sha256: str,
    expected_projection_root_sha256: str,
) -> tuple[int, ...]:
    verified = fp.assert_feature_authority_lawful(
        feature_authority,
        expected_feature_authority_root_sha256=(
            expected_feature_authority_root_sha256),
        expected_projection_root_sha256=expected_projection_root_sha256)
    if int(verified["features"]) != EXPECTED_PROJECTED_FEATURES:
        raise AssertionError("%s: feature authority has %d rows, expected %d"
                             % (STOP_PROJECTION, int(verified["features"]),
                                EXPECTED_PROJECTED_FEATURES))
    rows = feature_authority["projection"]
    indices = tuple(int(row["molecular_address_index"]) for row in rows)
    if len(indices) != EXPECTED_PROJECTED_FEATURES:
        raise AssertionError("%s: projection length mismatch" % STOP_PROJECTION)
    if len(set(indices)) != len(indices):
        raise AssertionError("%s: projection contains duplicate address indices"
                             % STOP_PROJECTION)
    if any(index < 0 or index >= rc.ADDRESS_SPACE_SIZE for index in indices):
        raise AssertionError("%s: projection index outside 41,238-address space"
                             % STOP_PROJECTION)
    return indices


def _verify_b2_chain(
    *,
    closure: Mapping[str, Any],
    logical: Mapping[str, Any],
    physical_plan: Mapping[str, Any],
    expected_closure_root_sha256: str,
    expected_logical_root_sha256: str,
    expected_physical_root_sha256: str,
    expected_membership_sha256: str,
    expected_block_manifest_sha256: str,
    expected_feature_authority_root_sha256: str,
) -> None:
    rc.assert_closure_lawful(
        closure=closure,
        expected_closure_root_sha256=expected_closure_root_sha256,
        expected_membership_sha256=expected_membership_sha256,
        expected_block_manifest_sha256=expected_block_manifest_sha256)
    rc.assert_row_authority_lawful(
        logical=logical,
        expected_logical_row_authority_root_sha256=expected_logical_root_sha256,
        expected_feature_authority_root_sha256=(
            expected_feature_authority_root_sha256),
        expected_population_closure_root_sha256=expected_closure_root_sha256)
    rc.assert_physical_plan_lawful(
        plan=physical_plan,
        expected_physical_root_sha256=expected_physical_root_sha256,
        expected_logical_root_sha256=expected_logical_root_sha256,
        logical=logical)


def evidence_root(evidence: Mapping[str, Any]) -> str:
    parents = evidence["parents"]
    parts = [_typed(DOMAIN_TAG), _typed(SCHEMA), _typed(NAMESPACE)]
    for name in (
        "population_closure_root_sha256",
        "logical_row_authority_root_sha256",
        "physical_read_plan_root_sha256",
        "feature_authority_root_sha256",
        "projection_root_sha256",
        "membership_sha256",
        "block_manifest_sha256",
        "mtg_source_sha256",
    ):
        parts.append(_typed([name, str(parents[name])]))
    rows = evidence["rows"]
    parts.append(_typed(len(rows)))
    for row in rows:
        parts.append(_typed([
            int(row["logical_index"]),
            str(row["canonical_cell_id"]),
            str(row["donor_id"]),
            int(row["source_library"]),
            int(row["projected_nonzero_count"]),
        ]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def derive_dataset_bound_evidence(
    *,
    closure: Mapping[str, Any],
    logical: Mapping[str, Any],
    physical_plan: Mapping[str, Any],
    feature_authority: Mapping[str, Any],
    counts_root: Path | str,
    mtg_h5_path: Path | str,
    candidate_donors: Sequence[str],
    expected_closure_root_sha256: str,
    expected_logical_root_sha256: str,
    expected_physical_root_sha256: str,
    expected_feature_authority_root_sha256: str,
    expected_projection_root_sha256: str,
    expected_membership_sha256: str,
    expected_block_manifest_sha256: str,
    expected_mtg_source_sha256: str = rc.MTG_SOURCE_SHA256,
    expected_target_cells: int = EXPECTED_TARGET_CELLS,
    expected_candidate_donors: int = EXPECTED_CANDIDATE_DONORS,
) -> dict[str, Any]:
    """Derive every technical input directly from authenticated dataset bytes."""

    _verify_b2_chain(
        closure=closure, logical=logical, physical_plan=physical_plan,
        expected_closure_root_sha256=expected_closure_root_sha256,
        expected_logical_root_sha256=expected_logical_root_sha256,
        expected_physical_root_sha256=expected_physical_root_sha256,
        expected_membership_sha256=expected_membership_sha256,
        expected_block_manifest_sha256=expected_block_manifest_sha256,
        expected_feature_authority_root_sha256=(
            expected_feature_authority_root_sha256))
    projection = _projection_indices(
        feature_authority,
        expected_feature_authority_root_sha256=(
            expected_feature_authority_root_sha256),
        expected_projection_root_sha256=expected_projection_root_sha256)
    projection_set = set(projection)

    logical_rows = logical["rows"]
    if len(logical_rows) != int(expected_target_cells):
        raise AssertionError("%s: logical authority has %d target cells, expected %d"
                             % (STOP_SCHEMA, len(logical_rows),
                                int(expected_target_cells)))
    if [int(row["logical_index"]) for row in logical_rows] != list(
            range(len(logical_rows))):
        raise AssertionError("%s: logical rows are not in exact logical-index order"
                             % STOP_SCHEMA)

    donors = tuple(sorted({str(row["donor_id"]) for row in logical_rows},
                          key=lambda d: d.encode("utf-8")))
    expected_donor_set = tuple(sorted({str(d) for d in candidate_donors},
                                      key=lambda d: d.encode("utf-8")))
    if donors != expected_donor_set or len(donors) != int(expected_candidate_donors):
        raise AssertionError(
            "%s: logical donors=%d candidate donors=%d expected=%d"
            % (STOP_DONOR_SET, len(donors), len(expected_donor_set),
               int(expected_candidate_donors)))

    libraries = rc.prove_source_libraries_from_authenticated_h5_path(
        logical=logical, source_path=mtg_h5_path,
        expected_source_sha256=expected_mtg_source_sha256)

    geometry = closure.get("block_geometry")
    if not isinstance(geometry, Mapping) or not geometry:
        raise AssertionError("%s: closure has no bound block_geometry"
                             % STOP_PARENT)

    by_path: dict[str, list[int]] = {}
    for row in logical_rows:
        by_path.setdefault(str(row["counts_path"]), []).append(
            int(row["logical_index"]))

    root = Path(counts_root)
    result_rows: list[dict[str, Any]] = []
    for counts_path in sorted(by_path, key=lambda p: p.encode("utf-8")):
        indices_for_payload = by_path[counts_path]
        first = logical_rows[indices_for_payload[0]]
        block_key = str(first["block_key"])
        block_geometry = geometry.get(block_key)
        if not isinstance(block_geometry, Mapping):
            raise AssertionError("%s: no geometry for %s"
                                 % (STOP_PARENT, block_key))
        if str(block_geometry["counts_path"]) != counts_path:
            raise AssertionError("%s: geometry/logical counts path mismatch for %s"
                                 % (STOP_PARENT, block_key))

        payload_path = _safe_child(root, counts_path)
        if not payload_path.is_file():
            raise AssertionError("%s: counts payload absent: %s"
                                 % (STOP_COUNTS, payload_path))
        payload = payload_path.read_bytes()
        actual = hashlib.sha256(payload).hexdigest()
        expected_digest = str(block_geometry["counts_sha256"])
        if actual != expected_digest:
            raise AssertionError("%s: %s hashes to %s, expected %s"
                                 % (STOP_COUNTS, counts_path, actual,
                                    expected_digest))

        parsed = rc._parse_csr_counts(payload)
        rows_n, width = (int(parsed["shape"][0]), int(parsed["shape"][1]))
        if rows_n != int(block_geometry["rows"]):
            raise AssertionError("%s: %s rows=%d manifest=%d"
                                 % (STOP_COUNTS, block_key, rows_n,
                                    int(block_geometry["rows"])))
        if width != rc.ADDRESS_SPACE_SIZE:
            raise AssertionError("%s: %s width=%d expected=%d"
                                 % (STOP_COUNTS, block_key, width,
                                    rc.ADDRESS_SPACE_SIZE))
        if len(parsed["data"]) != int(block_geometry["nnz"]):
            raise AssertionError("%s: %s nnz=%d manifest=%d"
                                 % (STOP_COUNTS, block_key, len(parsed["data"]),
                                    int(block_geometry["nnz"])))

        indptr = parsed["indptr"]
        columns = parsed["indices"]
        values = parsed["data"]
        for logical_index in indices_for_payload:
            row = logical_rows[logical_index]
            if str(row["block_key"]) != block_key:
                raise AssertionError("%s: one counts payload maps to multiple block keys"
                                     % STOP_PARENT)
            block_row = int(row["row_index"])
            if not (0 <= block_row < rows_n):
                raise AssertionError("%s: block row %d out of bounds for %s"
                                     % (STOP_COUNTS, block_row, block_key))
            start, end = int(indptr[block_row]), int(indptr[block_row + 1])
            seen_nonzero: set[int] = set()
            for offset in range(start, end):
                column = int(columns[offset])
                value = float(values[offset])
                if (not value.is_integer()) or value < 0:
                    raise AssertionError(
                        "%s: %s row %d column %d has invalid count %r"
                        % (STOP_COUNTS, block_key, block_row, column,
                           values[offset]))
                if value != 0 and column in projection_set:
                    seen_nonzero.add(column)
            result_rows.append({
                "logical_index": logical_index,
                "canonical_cell_id": str(row["canonical_cell_id"]),
                "donor_id": str(row["donor_id"]),
                "source_library": int(libraries[logical_index]),
                "projected_nonzero_count": len(seen_nonzero),
            })

    result_rows.sort(key=lambda row: int(row["logical_index"]))
    if len(result_rows) != len(logical_rows):
        raise AssertionError("%s: derived %d rows for %d logical rows"
                             % (STOP_SCHEMA, len(result_rows),
                                len(logical_rows)))

    evidence = {
        "schema": SCHEMA,
        "namespace": NAMESPACE,
        "parents": {
            "population_closure_root_sha256": str(expected_closure_root_sha256),
            "logical_row_authority_root_sha256": str(expected_logical_root_sha256),
            "physical_read_plan_root_sha256": str(expected_physical_root_sha256),
            "feature_authority_root_sha256": str(
                expected_feature_authority_root_sha256),
            "projection_root_sha256": str(expected_projection_root_sha256),
            "membership_sha256": str(expected_membership_sha256),
            "block_manifest_sha256": str(expected_block_manifest_sha256),
            "mtg_source_sha256": str(expected_mtg_source_sha256),
        },
        "source_relative_path": rc.MTG_SOURCE_RELATIVE_PATH,
        "matrix_slot": rc.MTG_SOURCE_MATRIX_SLOT,
        "source_shape": list(rc.MTG_SOURCE_SHAPE),
        "projected_features": EXPECTED_PROJECTED_FEATURES,
        "rows": result_rows,
        "row_count": len(result_rows),
        "donor_count": len(donors),
        "pathology_values_read": False,
        "real_execution_ready": False,
    }
    evidence["evidence_root_sha256"] = evidence_root(evidence)
    return evidence


def assert_evidence_lawful(
    evidence: Mapping[str, Any],
    *,
    expected_evidence_root_sha256: str,
    expected_parent_roots: Mapping[str, str],
) -> bool:
    if evidence.get("schema") != SCHEMA or evidence.get("namespace") != NAMESPACE:
        raise AssertionError("%s: wrong schema/namespace" % STOP_SCHEMA)
    if evidence.get("real_execution_ready") is not False:
        raise AssertionError("%s: real_execution_ready must remain False"
                             % STOP_SCHEMA)
    if evidence.get("pathology_values_read") is not False:
        raise AssertionError("%s: pathology_values_read must be False"
                             % STOP_SCHEMA)
    parents = evidence.get("parents")
    if not isinstance(parents, Mapping):
        raise AssertionError("%s: parents absent" % STOP_SCHEMA)
    for name, expected in expected_parent_roots.items():
        if str(parents.get(name)) != str(expected):
            raise AssertionError("%s: %s=%r expected=%r"
                                 % (STOP_PARENT, name, parents.get(name),
                                    expected))
    recomputed = evidence_root(evidence)
    if str(evidence.get("evidence_root_sha256")) != recomputed:
        raise AssertionError("%s: stored root differs from recomputation"
                             % STOP_ROOT)
    if recomputed != str(expected_evidence_root_sha256):
        raise AssertionError("%s: evidence root=%s expected=%s"
                             % (STOP_ROOT, recomputed,
                                expected_evidence_root_sha256))
    return True
