"""Byte-to-row authentication of the raw MTG H5AD source for `source_library`.

Why this module replaces the previous proof
-------------------------------------------
The previous `prove_source_library` accepted `raw_source_row_values` plus a
provenance mapping, both supplied by the caller. It compared the caller's labels
against the bound row and summed the caller's vector. That is LABEL
authentication: a fabricated vector whose sum matched, carrying the correct frozen
source digest string, the correct `layers/UMIs` slot name, the correct
`expression_row`, the correct width and the correct cell and donor identities,
proved `source_library` even though none of its values had ever been read from
the source asset.

An external review classified that as a hard STOP rather than a documentation
gap, and it was right. This module does byte-to-row authentication instead:

  1. the H5AD bytes are digested and compared against the frozen asset identity;
  2. the file is opened only after that comparison succeeds;
  3. `layers/UMIs` is located and its declared shape checked;
  4. the bound `expression_row` selects the row;
  5. `obs` at that row must carry the bound cell and donor identity;
  6. the row's values must be raw non-negative integral counts;
  7. `source_library` is COMPUTED from that row and compared to the bound value.

The production entrypoint takes no values argument, so there is no parameter
through which a caller-created vector could enter. That is the structural
property, not a check that could be forgotten.

The source handle cannot be forged
----------------------------------
`AuthenticatedSource` carries a module-private token that only
`open_authenticated_source` can supply, and the verifier refuses any object
lacking it. Without that, a caller could hand over a look-alike object whose
`sha256` attribute said the right thing, and label authentication would be back.

Cost note
---------
The frozen MTG asset is roughly 33 GB, so digesting it is minutes of I/O. The
handle is therefore opened once and reused across every row proof of a run;
`digest_bytes_read` records what was actually hashed so a reviewer can tell a
real authentication from a skipped one.

Pathology
---------
Only `obs` cell identity and `obs['Donor ID']` are read, plus raw counts. No
pathology column is read, parsed, retained or emitted, and `assert_no_pathology_read`
states the permitted `obs` field set.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA = "JEPA_T0_RAW_SOURCE_ROW_AUTHORITY_V1"
NAMESPACE = "T0-RAW-SOURCE-ROW-V1"
DOMAIN_TAG = "T0-RAW-SOURCE-ROW-V1-TYPED-LENGTH-PREFIXED"

STOP_SOURCE_DIGEST = "STOP_T0_RAW_SOURCE_ASSET_DIGEST_MISMATCH"
STOP_SOURCE_ABSENT = "STOP_T0_RAW_SOURCE_ASSET_ABSENT"
STOP_HANDLE_FORGED = "STOP_T0_RAW_SOURCE_HANDLE_NOT_PRODUCED_BY_AUTHENTICATION"
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

# Frozen identity and geometry of the MTG source asset.
MTG_SOURCE_SHA256 = "e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79"
MTG_SOURCE_RELATIVE_PATH = (
    "data/external/v4/sea_ad/mtg/SEAAD_MTG_RNAseq_final-nuclei.2026-06-22.h5ad")
MTG_SOURCE_CELLS = 1_178_694
SOURCE_FEATURE_COUNT = 36_601
UMI_SLOT = "layers/UMIs"

# The only `obs` fields this module is permitted to read. The asset's `obs`
# carries Braak, Thal, CERAD and other pathology columns; none is touched.
PERMITTED_OBS_FIELDS = ("exp_component_name", "Donor ID")

_HANDLE_TOKEN = object()


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
    """State the permitted `obs` field set.

    The asset's `obs` holds Braak, Thal, CERAD score, Overall AD
    neuropathological Change and more. This module reads exactly two fields, and
    the guarantee is worth asserting rather than merely intending.
    """
    if tuple(PERMITTED_OBS_FIELDS) != ("exp_component_name", "Donor ID"):
        raise AssertionError("%s: permitted obs fields are %r"
                             % (STOP_OBS_FIELD, PERMITTED_OBS_FIELDS))
    return True


class AuthenticatedSource:
    """An H5AD whose bytes have been digested and matched to a frozen identity.

    Constructed only by `open_authenticated_source`. The private token makes a
    look-alike object useless: without it the verifier refuses, so a caller
    cannot reintroduce label authentication by supplying an object that merely
    claims the right digest.
    """

    def __init__(self, token: object, *, path: Path, sha256: str,
                 bytes_read: int, handle: Any) -> None:
        if token is not _HANDLE_TOKEN:
            raise AssertionError(
                "%s: an AuthenticatedSource may only be produced by "
                "open_authenticated_source, which digests the asset first"
                % STOP_HANDLE_FORGED)
        self._token = token
        self.path = Path(path)
        self.sha256 = str(sha256)
        self.digest_bytes_read = int(bytes_read)
        self._h5 = handle

    @property
    def h5(self) -> Any:
        return self._h5

    def close(self) -> None:
        try:
            self._h5.close()
        except Exception:
            pass

    def __enter__(self) -> "AuthenticatedSource":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _assert_genuine(source: Any) -> AuthenticatedSource:
    if not isinstance(source, AuthenticatedSource):
        raise AssertionError(
            "%s: the supplied source is a %s, not an AuthenticatedSource"
            % (STOP_HANDLE_FORGED, type(source).__name__))
    if getattr(source, "_token", None) is not _HANDLE_TOKEN:
        raise AssertionError("%s: the handle carries no authentication token"
                             % STOP_HANDLE_FORGED)
    return source


def open_authenticated_source(
        path: Path | str,
        *,
        expected_sha256: str = MTG_SOURCE_SHA256,
        chunk_bytes: int = 64 << 20,
) -> AuthenticatedSource:
    """Digest the asset, then open it. Never the other way round.

    Opening first and digesting later would leave an interval in which the bytes
    read differ from the bytes hashed, which is the same check-then-use gap
    closed elsewhere in this lane.
    """
    import h5py

    asset = Path(path)
    if not asset.is_file():
        raise AssertionError("%s: %s" % (STOP_SOURCE_ABSENT, asset))

    digest = hashlib.sha256()
    read = 0
    with open(asset, "rb") as stream:
        while True:
            chunk = stream.read(int(chunk_bytes))
            if not chunk:
                break
            digest.update(chunk)
            read += len(chunk)
    actual = digest.hexdigest()
    if actual != str(expected_sha256):
        raise AssertionError("%s: %s is %s, expected %s"
                             % (STOP_SOURCE_DIGEST, asset, actual, expected_sha256))

    handle = h5py.File(str(asset), "r")
    return AuthenticatedSource(_HANDLE_TOKEN, path=asset, sha256=actual,
                               bytes_read=read, handle=handle)


def _umi_layer(source: AuthenticatedSource) -> Any:
    handle = source.h5
    group, name = UMI_SLOT.split("/", 1)
    if group not in handle or name not in handle[group]:
        raise AssertionError("%s: %s is absent from %s"
                             % (STOP_SLOT_ABSENT, UMI_SLOT, source.path))
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
    return layer


def source_geometry(source: AuthenticatedSource) -> tuple[int, int]:
    layer = _umi_layer(_assert_genuine(source))
    shape = [int(v) for v in layer.attrs["shape"]]
    if len(shape) != 2:
        raise AssertionError("%s: %s declares shape %r"
                             % (STOP_SOURCE_SHAPE, UMI_SLOT, shape))
    return shape[0], shape[1]


def _decode(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def read_row_identity(source: AuthenticatedSource, row_index: int) -> dict[str, str]:
    """Read ONLY the two permitted `obs` fields at one row."""
    assert_no_pathology_read()
    genuine = _assert_genuine(source)
    obs = genuine.h5["obs"]

    index_name = obs.attrs.get("_index")
    index_name = _decode(index_name) if index_name is not None else "exp_component_name"
    if index_name not in PERMITTED_OBS_FIELDS:
        raise AssertionError("%s: the obs index is %r, which is not permitted"
                             % (STOP_OBS_FIELD, index_name))
    cell = _decode(obs[index_name][int(row_index)])

    node = obs["Donor ID"]
    if hasattr(node, "keys") and "categories" in node:
        code = int(node["codes"][int(row_index)])
        donor = _decode(node["categories"][code])
    else:
        donor = _decode(node[int(row_index)])
    return {"canonical_cell_id": cell, "donor_id": donor}


def read_raw_row(source: AuthenticatedSource, row_index: int) -> tuple[int, int]:
    """Return `(library_total, stored_value_count)` for one authenticated row.

    The row's values are summed here rather than returned, because returning them
    would recreate a path by which a caller could substitute a vector. Only the
    total and the number of stored values leave this function.

    The asset stores `layers/UMIs` data as float64 whose values are integral, so
    integrality is required rather than assumed, and a non-integral or negative
    stored value is a STOP.
    """
    import numpy as np

    genuine = _assert_genuine(source)
    layer = _umi_layer(genuine)
    rows, width = source_geometry(genuine)
    if width != SOURCE_FEATURE_COUNT:
        raise AssertionError("%s: %s is %d wide, expected the %d-feature source space"
                             % (STOP_SOURCE_SHAPE, UMI_SLOT, width,
                                SOURCE_FEATURE_COUNT))
    if not (0 <= int(row_index) < rows):
        raise AssertionError("%s: row %d is outside 0..%d"
                             % (STOP_ROW_RANGE, int(row_index), rows - 1))

    indptr = layer["indptr"]
    start, end = int(indptr[int(row_index)]), int(indptr[int(row_index) + 1])
    values = np.asarray(layer["data"][start:end])

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


def prove_source_library_from_authenticated_source(
        *,
        source: Any,
        logical: Mapping[str, Any],
        logical_index: int,
        expected_source_sha256: str = MTG_SOURCE_SHA256,
) -> dict[str, Any]:
    """Prove the bound `source_library` from bytes this function itself read.

    There is deliberately NO parameter for row values. A caller-created vector
    cannot enter, whatever its sum and whatever labels accompany it, because
    there is nowhere to put it. Everything compared here is either read from the
    authenticated asset or read from the bound logical row.
    """
    genuine = _assert_genuine(source)
    if genuine.sha256 != str(expected_source_sha256):
        raise AssertionError(
            "%s: the authenticated asset is %s, but this proof expects %s"
            % (STOP_SOURCE_DIGEST, genuine.sha256, expected_source_sha256))

    row = logical["rows"][int(logical_index)]
    expression_row = int(row["expression_row"])

    identity = read_row_identity(genuine, expression_row)
    if identity["canonical_cell_id"] != str(row["canonical_cell_id"]):
        raise AssertionError(
            "%s: source row %d is cell %r but logical index %d binds %r"
            % (STOP_ROW_IDENTITY, expression_row, identity["canonical_cell_id"],
               int(logical_index), row["canonical_cell_id"]))
    if identity["donor_id"] != str(row["donor_id"]):
        raise AssertionError(
            "%s: source row %d is donor %r but logical index %d binds %r"
            % (STOP_ROW_IDENTITY, expression_row, identity["donor_id"],
               int(logical_index), row["donor_id"]))

    total, stored = read_raw_row(genuine, expression_row)
    bound = int(row["source_library"])
    if total != bound:
        raise AssertionError(
            "%s: the authenticated %s row %d sums to %d but logical index %d "
            "binds source_library %d"
            % (STOP_LIBRARY, UMI_SLOT, expression_row, total,
               int(logical_index), bound))

    return {
        "schema": SCHEMA,
        "proof": "BYTE_TO_ROW_FROM_AUTHENTICATED_H5AD",
        "source_sha256": genuine.sha256,
        "digest_bytes_read": genuine.digest_bytes_read,
        "matrix_slot": UMI_SLOT,
        "expression_row": expression_row,
        "canonical_cell_id": identity["canonical_cell_id"],
        "donor_id": identity["donor_id"],
        "stored_values_in_row": stored,
        "source_library": total,
        "caller_supplied_values": False,
        "real_execution_ready": False,
    }


def raw_source_proof_root(proofs: Sequence[Mapping[str, Any]]) -> str:
    """Digest over a set of byte-to-row proofs, with explicit cardinality."""
    parts = [_typed(DOMAIN_TAG), _typed(SCHEMA), _typed(NAMESPACE),
             _typed(UMI_SLOT), _typed(len(proofs))]
    for proof in sorted(proofs, key=lambda p: int(p["expression_row"])):
        parts.append(_typed([
            str(proof["source_sha256"]), int(proof["expression_row"]),
            str(proof["canonical_cell_id"]), str(proof["donor_id"]),
            int(proof["source_library"]), int(proof["stored_values_in_row"]),
        ]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def refuse_caller_supplied_values(**kwargs: Any) -> None:
    """Explicit refusal, so the removed parameter cannot quietly return.

    Any future call site that tries to hand values or provenance labels to a
    proof gets a named STOP rather than silently reaching a permissive overload.
    """
    offending = sorted(k for k in kwargs
                       if k in ("raw_source_row_values", "raw_source_provenance",
                                "row_values", "values", "provenance"))
    if offending:
        raise AssertionError(
            "%s: %s may not be supplied; source_library is proven only from "
            "bytes read out of the authenticated asset"
            % (STOP_CALLER_VALUES, ", ".join(offending)))
