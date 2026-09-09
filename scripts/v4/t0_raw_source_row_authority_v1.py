"""Population-wide byte-to-row authority for MTG raw `source_library`.

Production semantics
--------------------
The production operation owns the source path, opens it once, hashes that exact
open file object, rewinds the same object, and gives that same object to h5py.
There is no caller-created authenticated handle and no caller-supplied row-value
parameter.  The 33 GB asset is therefore hashed once per run and all accepted
logical rows are proved through the same authenticated source.

The proof is population-wide: every B2 logical row is checked against
`layers/UMIs[expression_row]`, the H5 `obs` cell and donor identities, and the
full raw-row integer sum.  The resulting root binds the B2 logical root, closure
root, feature root, source digest, source geometry, exact proof cardinality and
each proof in logical-population order.

Pathology
---------
Only the cell identity field and `Donor ID` are read from `obs`, plus raw UMI
counts.  No pathology field is read, parsed, retained or emitted.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA = "JEPA_T0_RAW_SOURCE_ROW_AUTHORITY_V2"
NAMESPACE = "T0-RAW-SOURCE-ROW-V2"
DOMAIN_TAG = "T0-RAW-SOURCE-ROW-V2-TYPED-LENGTH-PREFIXED"

STOP_SOURCE_DIGEST = "STOP_T0_RAW_SOURCE_ASSET_DIGEST_MISMATCH"
STOP_SOURCE_ABSENT = "STOP_T0_RAW_SOURCE_ASSET_ABSENT"
STOP_SOURCE_CHANGED = "STOP_T0_RAW_SOURCE_ASSET_CHANGED_DURING_PROOF"
STOP_SLOT_ABSENT = "STOP_T0_RAW_SOURCE_UMI_LAYER_ABSENT"
STOP_SLOT_ENCODING = "STOP_T0_RAW_SOURCE_UMI_LAYER_NOT_CSR"
STOP_SOURCE_SHAPE = "STOP_T0_RAW_SOURCE_SHAPE_MISMATCH"
STOP_ROW_RANGE = "STOP_T0_RAW_SOURCE_ROW_OUT_OF_RANGE"
STOP_ROW_IDENTITY = "STOP_T0_RAW_SOURCE_ROW_IDENTITY_MISMATCH"
STOP_COUNTS = "STOP_T0_RAW_SOURCE_COUNTS_NOT_NONNEGATIVE_INTEGERS"
STOP_LIBRARY = "STOP_T0_RAW_SOURCE_LIBRARY_NOT_PROVEN_FROM_AUTHENTICATED_ROW"
STOP_OBS_FIELD = "STOP_T0_RAW_SOURCE_OBS_FIELD_NOT_PERMITTED"
STOP_FIELD_SCHEMA = "STOP_T0_RAW_SOURCE_FIELD_SCHEMA_VIOLATION"
STOP_CALLER_VALUES = "STOP_T0_RAW_SOURCE_CALLER_SUPPLIED_VALUES_REFUSED"
STOP_LOGICAL_ROOT = "STOP_T0_RAW_SOURCE_LOGICAL_ROOT_NOT_EXTERNALLY_BOUND"
STOP_PROOF_ROOT = "STOP_T0_RAW_SOURCE_PROOF_ROOT_MISMATCH"
STOP_PROOF_COUNT = "STOP_T0_RAW_SOURCE_PROOF_POPULATION_NOT_COMPLETE"

MTG_SOURCE_SHA256 = "e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79"
MTG_SOURCE_RELATIVE_PATH = (
    "data/external/v4/sea_ad/mtg/SEAAD_MTG_RNAseq_final-nuclei.2026-06-22.h5ad")
MTG_SOURCE_CELLS = 1_178_694
SOURCE_FEATURE_COUNT = 36_601
PRODUCTION_LOGICAL_ROWS = 20_804
UMI_SLOT = "layers/UMIs"
PERMITTED_OBS_FIELDS = ("exp_component_name", "Donor ID")


def _typed(value: Any) -> bytes:
    if isinstance(value, bool):
        tag, payload = b"b", (b"1" if value else b"0")
    elif isinstance(value, int):
        tag, payload = b"i", str(int(value)).encode("ascii")
    elif isinstance(value, str):
        tag, payload = b"s", value.encode("utf-8")
    elif isinstance(value, (tuple, list)):
        tag = b"l"
        payload = b"%d:%s" % (len(value), b"".join(_typed(v) for v in value))
    else:
        raise AssertionError("%s: cannot frame %r" % (STOP_FIELD_SCHEMA, type(value)))
    return b"%s%d:%s" % (tag, len(payload), payload)


def assert_no_pathology_read() -> bool:
    if tuple(PERMITTED_OBS_FIELDS) != ("exp_component_name", "Donor ID"):
        raise AssertionError("%s: permitted obs fields are %r"
                             % (STOP_OBS_FIELD, PERMITTED_OBS_FIELDS))
    return True


def refuse_caller_supplied_values(**kwargs: Any) -> None:
    offending = sorted(k for k in kwargs
                       if k in ("raw_source_row_values", "raw_source_provenance",
                                "row_values", "values", "provenance", "source"))
    if offending:
        raise AssertionError(
            "%s: %s may not be supplied; production source_library proof owns "
            "the source path and reads the authenticated H5 bytes itself"
            % (STOP_CALLER_VALUES, ", ".join(offending)))


def _decode(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def _obs_value(node: Any, row_index: int) -> str:
    """Read one AnnData obs value in categorical or direct-array form."""
    if hasattr(node, "keys") and "codes" in node and "categories" in node:
        code = int(node["codes"][int(row_index)])
        if code < 0:
            return ""
        categories = node["categories"]
        if code >= len(categories):
            raise AssertionError(
                "%s: categorical code %d is outside 0..%d"
                % (STOP_FIELD_SCHEMA, code, len(categories) - 1))
        return _decode(categories[code])
    return _decode(node[int(row_index)])


def _umi_layer(handle: Any) -> Any:
    group, name = UMI_SLOT.split("/", 1)
    if group not in handle or name not in handle[group]:
        raise AssertionError("%s: %s is absent" % (STOP_SLOT_ABSENT, UMI_SLOT))
    layer = handle[group][name]
    encoding = layer.attrs.get("encoding-type")
    encoding = (encoding.decode() if isinstance(encoding, bytes)
                else str(encoding) if encoding is not None else "")
    if encoding != "csr_matrix":
        raise AssertionError("%s: %s declares encoding %r, expected csr_matrix"
                             % (STOP_SLOT_ENCODING, UMI_SLOT, encoding))
    for member in ("data", "indices", "indptr"):
        if member not in layer:
            raise AssertionError("%s: %s lacks %r"
                                 % (STOP_SLOT_ENCODING, UMI_SLOT, member))
    if "shape" not in layer.attrs:
        raise AssertionError("%s: %s has no shape attribute"
                             % (STOP_SOURCE_SHAPE, UMI_SLOT))
    return layer


def _source_geometry(handle: Any) -> tuple[int, int]:
    layer = _umi_layer(handle)
    shape = [int(v) for v in layer.attrs["shape"]]
    if len(shape) != 2:
        raise AssertionError("%s: %s declares shape %r"
                             % (STOP_SOURCE_SHAPE, UMI_SLOT, shape))
    rows, width = shape
    if len(layer["indptr"]) != rows + 1:
        raise AssertionError(
            "%s: indptr length %d does not equal source rows+1=%d"
            % (STOP_SOURCE_SHAPE, len(layer["indptr"]), rows + 1))
    return rows, width


def _read_row_identity(handle: Any, row_index: int) -> dict[str, str]:
    assert_no_pathology_read()
    if "obs" not in handle:
        raise AssertionError("%s: H5AD has no obs group" % STOP_FIELD_SCHEMA)
    obs = handle["obs"]
    index_name = obs.attrs.get("_index")
    index_name = (_decode(index_name) if index_name is not None
                  else "exp_component_name")
    if index_name != "exp_component_name":
        raise AssertionError(
            "%s: the cell identity index is %r, expected exp_component_name"
            % (STOP_OBS_FIELD, index_name))
    if index_name not in obs or "Donor ID" not in obs:
        raise AssertionError(
            "%s: required obs identity fields are absent" % STOP_FIELD_SCHEMA)
    return {
        "canonical_cell_id": _obs_value(obs[index_name], row_index),
        "donor_id": _obs_value(obs["Donor ID"], row_index),
    }


def _read_raw_row(handle: Any, row_index: int,
                  *, source_rows: int, source_width: int) -> tuple[int, int]:
    import numpy as np

    if source_width != SOURCE_FEATURE_COUNT:
        raise AssertionError(
            "%s: %s is %d wide, expected %d"
            % (STOP_SOURCE_SHAPE, UMI_SLOT, source_width, SOURCE_FEATURE_COUNT))
    if not (0 <= int(row_index) < int(source_rows)):
        raise AssertionError("%s: row %d is outside 0..%d"
                             % (STOP_ROW_RANGE, int(row_index),
                                int(source_rows) - 1))
    layer = _umi_layer(handle)
    indptr = layer["indptr"]
    start, end = int(indptr[int(row_index)]), int(indptr[int(row_index) + 1])
    if not (0 <= start <= end <= len(layer["data"])):
        raise AssertionError(
            "%s: invalid CSR slice %d:%d for row %d"
            % (STOP_SOURCE_SHAPE, start, end, int(row_index)))
    cols = np.asarray(layer["indices"][start:end])
    values = np.asarray(layer["data"][start:end])
    if len(cols) != len(values):
        raise AssertionError(
            "%s: CSR indices/data lengths differ at row %d"
            % (STOP_SOURCE_SHAPE, int(row_index)))
    if cols.size:
        if np.any(cols < 0) or np.any(cols >= int(source_width)):
            raise AssertionError(
                "%s: row %d contains an out-of-range source column"
                % (STOP_SOURCE_SHAPE, int(row_index)))
    if values.size:
        if not np.isfinite(values).all():
            raise AssertionError("%s: row %d holds a non-finite value"
                                 % (STOP_COUNTS, int(row_index)))
        if np.any(values < 0):
            raise AssertionError("%s: row %d holds a negative value"
                                 % (STOP_COUNTS, int(row_index)))
        if np.any(np.floor(values) != values):
            raise AssertionError("%s: row %d holds a non-integral value"
                                 % (STOP_COUNTS, int(row_index)))
    total = int(np.rint(values).sum()) if values.size else 0
    return total, int(end - start)


def _stream_sha256(stream: Any, *, chunk_bytes: int) -> tuple[str, int]:
    stream.seek(0)
    digest = hashlib.sha256()
    read = 0
    while True:
        chunk = stream.read(int(chunk_bytes))
        if not chunk:
            break
        digest.update(chunk)
        read += len(chunk)
    return digest.hexdigest(), read


def _proof_root(authority: Mapping[str, Any]) -> str:
    proofs = authority["proofs"]
    parts = [
        _typed(DOMAIN_TAG), _typed(SCHEMA), _typed(NAMESPACE),
        _typed(str(authority["source_sha256"])),
        _typed(int(authority["source_cells"])),
        _typed(int(authority["source_features"])),
        _typed(str(authority["logical_row_authority_root_sha256"])),
        _typed(str(authority["population_closure_root_sha256"])),
        _typed(str(authority["feature_authority_root_sha256"])),
        _typed(int(authority["proof_count"])),
    ]
    for proof in proofs:
        parts.append(_typed([
            int(proof["logical_index"]),
            int(proof["expression_row"]),
            str(proof["canonical_cell_id"]),
            str(proof["donor_id"]),
            int(proof["source_library"]),
            int(proof["stored_values_in_row"]),
        ]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def _build_population_raw_source_authority(
        *,
        source_path: Path | str,
        logical: Mapping[str, Any],
        expected_logical_root_sha256: str,
        expected_population_closure_root_sha256: str,
        expected_feature_authority_root_sha256: str,
        expected_source_sha256: str,
        expected_source_cells: int,
        expected_source_features: int,
        expected_logical_rows: int,
        chunk_bytes: int = 64 << 20,
) -> dict[str, Any]:
    """Fixture-capable implementation; public production wrapper freezes geometry."""
    import h5py
    import t0_v20_row_count_authority_v1 as rc

    rc.assert_row_authority_lawful(
        logical=logical,
        expected_logical_row_authority_root_sha256=expected_logical_root_sha256,
        expected_feature_authority_root_sha256=expected_feature_authority_root_sha256,
        expected_population_closure_root_sha256=(
            expected_population_closure_root_sha256),
    )
    if len(logical["rows"]) != int(expected_logical_rows):
        raise AssertionError(
            "%s: logical authority holds %d rows, expected %d"
            % (STOP_PROOF_COUNT, len(logical["rows"]), int(expected_logical_rows)))

    asset = Path(source_path)
    if not asset.is_file():
        raise AssertionError("%s: %s" % (STOP_SOURCE_ABSENT, asset))

    proofs_by_index: dict[int, dict[str, Any]] = {}
    with open(asset, "rb") as stream:
        before = os.fstat(stream.fileno())
        actual_sha, bytes_read = _stream_sha256(
            stream, chunk_bytes=int(chunk_bytes))
        if actual_sha != str(expected_source_sha256):
            raise AssertionError(
                "%s: %s is %s, expected %s"
                % (STOP_SOURCE_DIGEST, asset, actual_sha,
                   expected_source_sha256))

        # Important: h5py consumes the same already-open file object that was
        # hashed above.  No second pathname open exists.
        stream.seek(0)
        with h5py.File(stream, "r") as handle:
            source_rows, source_width = _source_geometry(handle)
            if source_rows != int(expected_source_cells) or                     source_width != int(expected_source_features):
                raise AssertionError(
                    "%s: source geometry is %d x %d, expected %d x %d"
                    % (STOP_SOURCE_SHAPE, source_rows, source_width,
                       int(expected_source_cells), int(expected_source_features)))

            # Physical H5 row order is the cheapest traversal order.  Each proof
            # still carries logical_index and the final authority is restored to
            # logical-population order before hashing.
            schedule = sorted(
                range(len(logical["rows"])),
                key=lambda i: int(logical["rows"][i]["expression_row"]))
            for logical_index in schedule:
                row = logical["rows"][logical_index]
                if int(row["logical_index"]) != int(logical_index):
                    raise AssertionError(
                        "%s: row %d declares logical_index %r"
                        % (STOP_FIELD_SCHEMA, logical_index,
                           row["logical_index"]))
                expression_row = int(row["expression_row"])
                identity = _read_row_identity(handle, expression_row)
                if identity["canonical_cell_id"] != str(row["canonical_cell_id"]):
                    raise AssertionError(
                        "%s: source row %d is cell %r but logical index %d binds %r"
                        % (STOP_ROW_IDENTITY, expression_row,
                           identity["canonical_cell_id"], logical_index,
                           row["canonical_cell_id"]))
                if identity["donor_id"] != str(row["donor_id"]):
                    raise AssertionError(
                        "%s: source row %d is donor %r but logical index %d binds %r"
                        % (STOP_ROW_IDENTITY, expression_row,
                           identity["donor_id"], logical_index,
                           row["donor_id"]))

                total, stored = _read_raw_row(
                    handle, expression_row,
                    source_rows=source_rows, source_width=source_width)
                bound = int(row["source_library"])
                if total != bound:
                    raise AssertionError(
                        "%s: authenticated %s row %d sums to %d but logical "
                        "index %d binds source_library %d"
                        % (STOP_LIBRARY, UMI_SLOT, expression_row, total,
                           logical_index, bound))
                proofs_by_index[logical_index] = {
                    "logical_index": int(logical_index),
                    "expression_row": expression_row,
                    "canonical_cell_id": identity["canonical_cell_id"],
                    "donor_id": identity["donor_id"],
                    "source_library": total,
                    "stored_values_in_row": stored,
                }

        after = os.fstat(stream.fileno())
        identity_before = (before.st_dev, before.st_ino, before.st_size,
                           getattr(before, "st_mtime_ns", None),
                           getattr(before, "st_ctime_ns", None))
        identity_after = (after.st_dev, after.st_ino, after.st_size,
                          getattr(after, "st_mtime_ns", None),
                          getattr(after, "st_ctime_ns", None))
        if identity_before != identity_after:
            raise AssertionError(
                "%s: source file identity/metadata changed while it was being "
                "proved" % STOP_SOURCE_CHANGED)

    if set(proofs_by_index) != set(range(len(logical["rows"]))):
        raise AssertionError(
            "%s: proved %d/%d logical rows"
            % (STOP_PROOF_COUNT, len(proofs_by_index), len(logical["rows"])))
    proofs = tuple(proofs_by_index[i] for i in range(len(logical["rows"])))
    authority = {
        "schema": SCHEMA,
        "namespace": NAMESPACE,
        "source_sha256": actual_sha,
        "digest_bytes_read": int(bytes_read),
        "source_cells": int(expected_source_cells),
        "source_features": int(expected_source_features),
        "matrix_slot": UMI_SLOT,
        "logical_row_authority_root_sha256": str(expected_logical_root_sha256),
        "population_closure_root_sha256": str(
            expected_population_closure_root_sha256),
        "feature_authority_root_sha256": str(
            expected_feature_authority_root_sha256),
        "proof_count": len(proofs),
        "proofs": proofs,
        "caller_supplied_values": False,
        "pathology_values_read": False,
        "real_execution_ready": False,
    }
    authority["raw_source_proof_root_sha256"] = _proof_root(authority)
    return authority


def build_population_raw_source_authority(
        *,
        source_path: Path | str,
        logical: Mapping[str, Any],
        expected_logical_root_sha256: str,
        expected_population_closure_root_sha256: str,
        expected_feature_authority_root_sha256: str,
        expected_source_sha256: str = MTG_SOURCE_SHA256,
        chunk_bytes: int = 64 << 20,
) -> dict[str, Any]:
    """Production population proof: fixed real-asset and 20,804-row geometry."""
    return _build_population_raw_source_authority(
        source_path=source_path,
        logical=logical,
        expected_logical_root_sha256=expected_logical_root_sha256,
        expected_population_closure_root_sha256=(
            expected_population_closure_root_sha256),
        expected_feature_authority_root_sha256=(
            expected_feature_authority_root_sha256),
        expected_source_sha256=expected_source_sha256,
        expected_source_cells=MTG_SOURCE_CELLS,
        expected_source_features=SOURCE_FEATURE_COUNT,
        expected_logical_rows=PRODUCTION_LOGICAL_ROWS,
        chunk_bytes=chunk_bytes,
    )


def assert_population_raw_source_authority_lawful(
        *,
        authority: Mapping[str, Any],
        logical: Mapping[str, Any],
        expected_raw_source_proof_root_sha256: str,
        expected_logical_root_sha256: str,
        expected_population_closure_root_sha256: str,
        expected_feature_authority_root_sha256: str,
        expected_source_sha256: str = MTG_SOURCE_SHA256,
        expected_proof_count: int = PRODUCTION_LOGICAL_ROWS,
) -> dict[str, Any]:
    """Establish stored == recomputed == externally expected for the proof root."""
    import t0_v20_row_count_authority_v1 as rc

    rc.assert_row_authority_lawful(
        logical=logical,
        expected_logical_row_authority_root_sha256=expected_logical_root_sha256,
        expected_feature_authority_root_sha256=expected_feature_authority_root_sha256,
        expected_population_closure_root_sha256=(
            expected_population_closure_root_sha256),
    )
    if authority.get("schema") != SCHEMA:
        raise AssertionError("%s: schema is %r"
                             % (STOP_FIELD_SCHEMA, authority.get("schema")))
    if authority.get("real_execution_ready") is not False or             authority.get("pathology_values_read") is not False or             authority.get("caller_supplied_values") is not False:
        raise AssertionError("%s: authority flags are unlawful"
                             % STOP_FIELD_SCHEMA)
    for field, expected in (
            ("source_sha256", expected_source_sha256),
            ("logical_row_authority_root_sha256", expected_logical_root_sha256),
            ("population_closure_root_sha256",
             expected_population_closure_root_sha256),
            ("feature_authority_root_sha256",
             expected_feature_authority_root_sha256)):
        if str(authority.get(field)) != str(expected):
            raise AssertionError(
                "%s: %s is %r, externally expected %r"
                % (STOP_LOGICAL_ROOT, field, authority.get(field), expected))

    proofs = authority.get("proofs")
    if not isinstance(proofs, (tuple, list)):
        raise AssertionError("%s: proofs are absent" % STOP_FIELD_SCHEMA)
    if int(authority.get("proof_count", -1)) != len(proofs) or             len(proofs) != int(expected_proof_count) or             len(proofs) != len(logical["rows"]):
        raise AssertionError(
            "%s: proof_count=%r proofs=%d expected=%d logical_rows=%d"
            % (STOP_PROOF_COUNT, authority.get("proof_count"), len(proofs),
               int(expected_proof_count), len(logical["rows"])))

    for index, proof in enumerate(proofs):
        row = logical["rows"][index]
        expected = {
            "logical_index": int(index),
            "expression_row": int(row["expression_row"]),
            "canonical_cell_id": str(row["canonical_cell_id"]),
            "donor_id": str(row["donor_id"]),
            "source_library": int(row["source_library"]),
        }
        for field, value in expected.items():
            if proof.get(field) != value:
                raise AssertionError(
                    "%s: proof %d %s=%r, logical authority binds %r"
                    % (STOP_ROW_IDENTITY, index, field, proof.get(field), value))
        if int(proof.get("stored_values_in_row", -1)) < 0:
            raise AssertionError(
                "%s: proof %d has invalid stored-value count"
                % (STOP_FIELD_SCHEMA, index))

    recomputed = _proof_root(authority)
    stored = authority.get("raw_source_proof_root_sha256")
    if str(stored) != recomputed:
        raise AssertionError(
            "%s: stored root %r recomputes to %s"
            % (STOP_PROOF_ROOT, stored, recomputed))
    if recomputed != str(expected_raw_source_proof_root_sha256):
        raise AssertionError(
            "%s: recomputed root %s, externally expected %s"
            % (STOP_PROOF_ROOT, recomputed,
               expected_raw_source_proof_root_sha256))
    return {
        "raw_source_proof_root_sha256": recomputed,
        "proof_count": len(proofs),
        "source_sha256": str(authority["source_sha256"]),
    }


# Synthetic tests may exercise row semantics without the 33 GB production
# geometry through this private helper only.
def _build_population_raw_source_authority_fixture(**kwargs: Any) -> dict[str, Any]:
    return _build_population_raw_source_authority(**kwargs)
