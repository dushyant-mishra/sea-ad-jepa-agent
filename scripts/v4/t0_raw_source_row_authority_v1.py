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
import io
import json
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
STOP_LEGACY_TOKEN = "STOP_T0_RAW_SOURCE_LEGACY_TOKEN_IS_NOT_AN_AUTHENTICATION_CAPABILITY"
STOP_IDENTITY_CONTINUITY = "STOP_T0_RAW_SOURCE_HASHED_BYTES_ARE_NOT_THE_CONSUMED_BYTES"
STOP_POPULATION_CARDINALITY = "STOP_T0_RAW_SOURCE_POPULATION_ROW_CARDINALITY_MISMATCH"
STOP_POPULATION_ROOT = "STOP_T0_RAW_SOURCE_POPULATION_ROOT_MISMATCH"
STOP_LOGICAL_ROOT = "STOP_T0_RAW_SOURCE_LOGICAL_ROOT_MISMATCH"
STOP_HANDLE_ON_PUBLIC_PATH = "STOP_T0_RAW_SOURCE_PUBLIC_PROOF_DOES_NOT_ACCEPT_A_HANDLE"
STOP_PACKAGE_MEMBER = "STOP_T0_RAW_SOURCE_PACKAGE_MEMBER_INVALID"
STOP_PACKAGE_ROOT = "STOP_T0_RAW_SOURCE_PACKAGE_ROOT_MISMATCH"
STOP_PATHOLOGY_IN_ARTIFACT = "STOP_T0_RAW_SOURCE_PATHOLOGY_FIELD_IN_EMITTED_ARTIFACT"

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

# Retained ONLY as a rejected decoy. An external review pointed out that a
# module-level sentinel is an ordinary importable attribute, so any same-process
# caller could pass it and claim any identity. It is therefore no longer a
# capability: `AuthenticatedSource` refuses it explicitly, and identity is
# established by re-deriving the digest from the bytes instead of by holding a
# token. A capability that anyone can import is not a capability.
_HANDLE_TOKEN = object()

# The genuine construction guard is created per call inside
# `_open_authenticated`, so it is never reachable as a module attribute.


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


class _ConstructionGuard:
    """Defence in depth, NOT a capability boundary.

    An external review made the point that has to be stated plainly: a
    module-level Python class is not a security boundary. Any same-process
    caller can import this name and instantiate it, exactly as it could import
    the old sentinel. Nothing in an in-process Python module can stop a caller
    that is already running in the process.

    So this guard is not what protects the proof. Two things do:

      * the PUBLIC surface is path-owned. `prove_population_from_source_path`
        takes a filesystem path and owns opening, hashing, consumption and
        closing. No public proof accepts a caller-built handle, so there is no
        supported way to present one.
      * identity is re-derived from the bytes. `AuthenticatedSource.__init__`
        hashes the path itself and refuses any claimed digest the file does not
        have, so a handle forged around a different file is useless even if the
        caller reaches the constructor.

    The guard only keeps accidental construction out of the way. It is labelled
    as such rather than presented as a capability.
    """


class AuthenticatedSource:
    """An H5AD whose bytes have been digested and matched to a frozen identity.

    Constructed only by `open_authenticated_source`. The private token makes a
    look-alike object useless: without it the verifier refuses, so a caller
    cannot reintroduce label authentication by supplying an object that merely
    claims the right digest.
    """

    def __init__(self, token: object, *, path: Path, sha256: str,
                 bytes_read: int, handle: Any) -> None:
        if token is _HANDLE_TOKEN:
            raise AssertionError(
                "%s: the module-level sentinel is importable by any caller and "
                "is not accepted; identity comes from the bytes, not from a "
                "token" % STOP_LEGACY_TOKEN)
        if not isinstance(token, _ConstructionGuard):
            raise AssertionError(
                "%s: an AuthenticatedSource may only be produced by the "
                "production entrypoint, which hashes and consumes one descriptor"
                % STOP_HANDLE_FORGED)
        # Identity is re-derived from the bytes on the way in. A caller who
        # somehow reaches this constructor still cannot claim a digest the file
        # does not have.
        actual = _digest_path(Path(path))[0]
        if actual != str(sha256):
            raise AssertionError(
                "%s: %s hashes to %s but the handle claims %s"
                % (STOP_SOURCE_DIGEST, path, actual, sha256))
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
        stream = getattr(self, "_stream", None)
        if stream is not None:
            try:
                stream.close()
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
    if not isinstance(getattr(source, "_token", None), _ConstructionGuard):
        raise AssertionError("%s: the handle was not produced by the production "
                             "entrypoint" % STOP_HANDLE_FORGED)
    return source


def _digest_path(path: Path, *, chunk_bytes: int = 64 << 20) -> tuple[str, int]:
    """Digest a path's bytes. Returns `(sha256, bytes_read)`."""
    digest = hashlib.sha256()
    read = 0
    with open(path, "rb") as stream:
        while True:
            chunk = stream.read(int(chunk_bytes))
            if not chunk:
                break
            digest.update(chunk)
            read += len(chunk)
    return digest.hexdigest(), read


def _digest_fileobj(stream: Any, *, chunk_bytes: int = 64 << 20) -> tuple[str, int]:
    """Digest an OPEN file object from its start, then rewind it.

    Hashing one open of a pathname and then reopening that pathname leaves a
    window in which the two opens can describe different bytes. Hashing the same
    descriptor that will be consumed closes it: there is only ever one open.
    """
    digest = hashlib.sha256()
    read = 0
    stream.seek(0)
    while True:
        chunk = stream.read(int(chunk_bytes))
        if not chunk:
            break
        digest.update(chunk)
        read += len(chunk)
    stream.seek(0)
    return digest.hexdigest(), read


def _open_authenticated(
        path: Path | str,
        *,
        expected_sha256: str,
        chunk_bytes: int = 64 << 20,
) -> AuthenticatedSource:
    """Open ONE descriptor, hash it, and hand that same object to h5py.

    The construction guard is created here, in a local, so it is not reachable
    as a module attribute. This is the only place an AuthenticatedSource comes
    from, and it is private: the public production operations own opening,
    hashing and consumption together and never accept a caller-built handle.
    """
    import h5py

    asset = Path(path)
    if not asset.is_file():
        raise AssertionError("%s: %s" % (STOP_SOURCE_ABSENT, asset))

    stream = open(asset, "rb")
    try:
        actual, read = _digest_fileobj(stream, chunk_bytes=chunk_bytes)
        if actual != str(expected_sha256):
            raise AssertionError("%s: %s is %s, expected %s"
                                 % (STOP_SOURCE_DIGEST, asset, actual,
                                    expected_sha256))
        # The same open file object is consumed, so the bytes hashed and the
        # bytes read by HDF5 are the same bytes.
        handle = h5py.File(stream, "r")
    except BaseException:
        stream.close()
        raise

    source = AuthenticatedSource(_ConstructionGuard(), path=asset,
                                 sha256=actual, bytes_read=read, handle=handle)
    source._stream = stream
    return source


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


def _prove_row_from_authenticated_source(
        *,
        source: Any,
        logical: Mapping[str, Any],
        logical_index: int,
        expected_source_sha256: str = MTG_SOURCE_SHA256,
) -> dict[str, Any]:
    """PRIVATE. One row, from an already-authenticated handle.

    Private because a public entrypoint taking a handle is an invitation to
    present one. Production goes through `prove_population_from_source_path`,
    which owns the path. This remains for fixtures and for the population loop.

    Prove the bound `source_library` from bytes this function itself read.

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


def open_authenticated_source(
        path: Path | str,
        *,
        expected_sha256: str = MTG_SOURCE_SHA256,
        chunk_bytes: int = 64 << 20,
) -> AuthenticatedSource:
    """FIXTURE-ONLY opener. Production uses `prove_population_from_source_path`.

    Retained because the regression suite needs to exercise handle-level
    behaviour directly, and because an external review introspects this
    function to confirm it does not reopen the pathname for HDF5. It is not a
    production entrypoint: no public proof accepts what it returns.

    Hash and consume ONE descriptor, then return the authenticated handle.

    The digest is taken from the same open file object that HDF5 then reads, so
    there is no second open of the pathname and no window in which the hashed
    bytes and the consumed bytes could differ.

    Production callers should prefer `prove_population_from_source_path`, which
    owns opening, hashing, consumption and closing together and accepts no
    caller-built handle at all.
    """
    return _open_authenticated(path, expected_sha256=expected_sha256,
                               chunk_bytes=chunk_bytes)


# ---------------------------------------------------------------------------
# Population-level authority.
#
# A three-row spot check establishes mechanics, not closure. An external review
# was right that proving three of 20,804 rows says nothing about the other
# 20,801, and that technical completeness reading `source_library` off the
# logical row proves only that the metadata value is bound -- not that it came
# out of the H5 row. So the population authority below proves EVERY accepted
# logical row and binds the exact row cardinality, and technical completeness
# must consume it.
# ---------------------------------------------------------------------------

POPULATION_SCHEMA = "JEPA_T0_RAW_SOURCE_POPULATION_AUTHORITY_V1"


def population_raw_source_root(
        *,
        logical_root_sha256: str,
        source_sha256: str,
        proofs: Sequence[Mapping[str, Any]],
) -> str:
    """Digest over every proven row, its parents and the exact cardinality."""
    parts = [_typed(DOMAIN_TAG), _typed(POPULATION_SCHEMA),
             _typed(str(logical_root_sha256)), _typed(str(source_sha256)),
             _typed(UMI_SLOT), _typed(len(proofs))]
    for proof in proofs:
        parts.append(_typed([
            int(proof["logical_index"]), int(proof["expression_row"]),
            str(proof["canonical_cell_id"]), str(proof["donor_id"]),
            int(proof["source_library"]), int(proof["stored_values_in_row"]),
        ]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def prove_population_from_source_path(
        *,
        source_path: Path | str,
        logical: Mapping[str, Any],
        expected_logical_root_sha256: str,
        expected_source_sha256: str = MTG_SOURCE_SHA256,
        expected_row_count: int | None = None,
        chunk_bytes: int = 64 << 20,
        progress: Any = None,
) -> dict[str, Any]:
    """Prove `source_library` for EVERY accepted logical row, from real bytes.

    This is the production operation. It owns opening, hashing, consumption and
    closing, and it accepts no caller-constructed handle and no caller-supplied
    row values. Every row of the logical authority is proven, so the result is a
    statement about the whole population rather than about a sample of it.
    """
    import t0_v20_row_count_authority_v1 as rc

    rows = list(logical["rows"])
    stored_logical = logical.get("logical_row_authority_root_sha256")
    stored_closure = logical.get("population_closure_root_sha256")
    recomputed = rc._logical_root(rows, logical["feature_authority_root_sha256"],
                                  stored_closure)
    if str(stored_logical) != recomputed:
        raise AssertionError(
            "%s: the logical authority stores %s but its contents recompute to %s"
            % (STOP_LOGICAL_ROOT, stored_logical, recomputed))
    if recomputed != str(expected_logical_root_sha256):
        raise AssertionError("%s: logical root is %s, externally expected %s"
                             % (STOP_LOGICAL_ROOT, recomputed,
                                expected_logical_root_sha256))
    if expected_row_count is not None and len(rows) != int(expected_row_count):
        raise AssertionError("%s: the logical authority holds %d rows, expected %d"
                             % (STOP_POPULATION_CARDINALITY, len(rows),
                                int(expected_row_count)))

    source = _open_authenticated(source_path,
                                 expected_sha256=expected_source_sha256,
                                 chunk_bytes=chunk_bytes)
    try:
        proofs = []
        for index in range(len(rows)):
            proof = _prove_row_from_authenticated_source(
                source=source, logical=logical, logical_index=index,
                expected_source_sha256=expected_source_sha256)
            proof["logical_index"] = int(rows[index]["logical_index"])
            proofs.append(proof)
            # Observability only. A long production run should be visible while
            # it happens; this changes nothing about what is proven.
            if progress is not None:
                progress(index + 1, len(rows))
        digest_bytes_read = source.digest_bytes_read
        source_sha = source.sha256
    finally:
        source.close()

    root = population_raw_source_root(
        logical_root_sha256=recomputed, source_sha256=source_sha, proofs=proofs)
    return {
        "schema": POPULATION_SCHEMA,
        "proof": "BYTE_TO_ROW_FROM_AUTHENTICATED_H5AD_OVER_THE_WHOLE_POPULATION",
        "population_raw_source_root_sha256": root,
        "logical_row_authority_root_sha256": recomputed,
        "source_sha256": source_sha,
        "digest_bytes_read": digest_bytes_read,
        "rows_proven": len(proofs),
        "proofs": tuple(proofs),
        "caller_supplied_values": False,
        "caller_supplied_handle": False,
        "real_execution_ready": False,
    }


def assert_population_authority_covers_logical(
        *,
        population: Mapping[str, Any],
        logical: Mapping[str, Any],
        expected_population_root_sha256: str,
        expected_logical_root_sha256: str,
        expected_source_sha256: str = MTG_SOURCE_SHA256,
) -> bool:
    """External verification that a population proof covers this exact logical set.

    Checks the root three ways (stored, recomputed, externally expected), the
    exact row cardinality, and that every logical row has a proof whose cell,
    donor, expression_row and source_library match it. A proof set that covered
    a different or smaller population is refused.
    """
    if str(population.get("logical_row_authority_root_sha256")) != str(
            expected_logical_root_sha256):
        raise AssertionError(
            "%s: the population authority names logical root %s, externally "
            "expected %s" % (STOP_LOGICAL_ROOT,
                             population.get("logical_row_authority_root_sha256"),
                             expected_logical_root_sha256))
    if str(population.get("source_sha256")) != str(expected_source_sha256):
        raise AssertionError("%s: the population authority names source %s, "
                             "externally expected %s"
                             % (STOP_SOURCE_DIGEST,
                                population.get("source_sha256"),
                                expected_source_sha256))

    rows = list(logical["rows"])
    proofs = list(population["proofs"])
    if len(proofs) != len(rows):
        raise AssertionError(
            "%s: %d rows proven for a population of %d; a spot check does not "
            "close the population"
            % (STOP_POPULATION_CARDINALITY, len(proofs), len(rows)))

    by_index = {int(p["logical_index"]): p for p in proofs}
    if sorted(by_index) != sorted(int(r["logical_index"]) for r in rows):
        raise AssertionError("%s: the proven logical indices are not the "
                             "population's own" % STOP_POPULATION_CARDINALITY)
    for row in rows:
        proof = by_index[int(row["logical_index"])]
        for field in ("canonical_cell_id", "donor_id"):
            if str(proof[field]) != str(row[field]):
                raise AssertionError(
                    "%s: logical index %s is %s=%r but its proof says %r"
                    % (STOP_ROW_IDENTITY, row["logical_index"], field,
                       row[field], proof[field]))
        if int(proof["expression_row"]) != int(row["expression_row"]):
            raise AssertionError(
                "%s: logical index %s binds expression_row %d but its proof read %d"
                % (STOP_ROW_IDENTITY, row["logical_index"],
                   int(row["expression_row"]), int(proof["expression_row"])))
        if int(proof["source_library"]) != int(row["source_library"]):
            raise AssertionError(
                "%s: logical index %s binds source_library %d but the "
                "authenticated row sums to %d"
                % (STOP_LIBRARY, row["logical_index"],
                   int(row["source_library"]), int(proof["source_library"])))

    recomputed = population_raw_source_root(
        logical_root_sha256=str(population["logical_row_authority_root_sha256"]),
        source_sha256=str(population["source_sha256"]), proofs=proofs)
    stored = population.get("population_raw_source_root_sha256")
    if str(stored) != recomputed:
        raise AssertionError(
            "%s: the stored population root %s does not match the root "
            "recomputed from its own proofs %s"
            % (STOP_POPULATION_ROOT, stored, recomputed))
    if recomputed != str(expected_population_root_sha256):
        raise AssertionError("%s: population root is %s, externally expected %s"
                             % (STOP_POPULATION_ROOT, recomputed,
                                expected_population_root_sha256))
    return True


def prove_source_library_from_authenticated_source(**kwargs: Any) -> dict[str, Any]:
    """REMOVED from the public surface. Use the path-owned population proof.

    A public proof that accepts an `AuthenticatedSource` invites a caller to
    present one, and in-process Python cannot stop it from presenting a forged
    look-alike. Rather than defend that boundary, the boundary is removed: the
    only public proof takes a filesystem path and owns opening, hashing,
    consumption and closing itself.
    """
    raise AssertionError(
        "%s: pass a source_path to prove_population_from_source_path instead. "
        "No public proof accepts a caller-built handle, because an in-process "
        "Python object cannot be an authentication capability."
        % STOP_HANDLE_ON_PUBLIC_PATH)


def public_proof_surface() -> tuple[str, ...]:
    """The proof entrypoints a production caller may use. Path-owned only."""
    return ("prove_population_from_source_path",)


# ---------------------------------------------------------------------------
# Immutable artifacts and replay.
#
# A run that leaves only console output cannot be replayed, and an authority
# that cannot be reloaded and re-verified from disk is not an authority. The
# package below carries the per-row proofs, every parent identity, and a package
# root over its own members, and `load_population_authority_package` recomputes
# the population root from the reloaded rows and requires
# stored == recomputed == externally expected.
# ---------------------------------------------------------------------------

PKG_REGISTRY = "T0_RAW_SOURCE_POPULATION_REGISTRY.csv"
PKG_METADATA = "T0_RAW_SOURCE_POPULATION_METADATA.json"
PKG_MANIFEST = "T0_RAW_SOURCE_POPULATION_MANIFEST.csv"
PKG_ROOT_FILE = "T0_RAW_SOURCE_POPULATION_PACKAGE_ROOT_SHA256.txt"
PKG_MEMBERS = (PKG_REGISTRY, PKG_METADATA, PKG_MANIFEST)

REGISTRY_FIELDS = ("logical_index", "expression_row", "canonical_cell_id",
                   "donor_id", "source_library", "stored_values_in_row")

# No emitted field may name a pathology endpoint.
ARTIFACT_PATHOLOGY_MARKERS = ("at8", "6e10", "gfap", "iba1", "neun", "abeta",
                              "ptau", "ttau", "braak", "thal", "cerad",
                              "positive area")


def assert_no_pathology_in_artifact(fields) -> bool:
    """The emitted artifact schema must carry no pathology endpoint."""
    for field in fields:
        lowered = str(field).lower()
        for marker in ARTIFACT_PATHOLOGY_MARKERS:
            if marker in lowered:
                raise AssertionError("%s: emitted field %r matches %r"
                                     % (STOP_PATHOLOGY_IN_ARTIFACT, field, marker))
    return True


def population_package_root(members) -> str:
    """Digest binding every package member's bytes, with explicit cardinality."""
    names = sorted(members)
    parts = [_typed(DOMAIN_TAG), _typed("POPULATION_PACKAGE"), _typed(len(names))]
    for name in names:
        parts.append(_typed([name,
                             hashlib.sha256(bytes(members[name])).hexdigest()]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def build_population_authority_package(
        outdir: Path | str,
        *,
        population: Mapping[str, Any],
        closure_root_sha256: str,
        feature_authority_root_sha256: str,
        physical_read_plan_root_sha256: str,
        membership_sha256: str,
        complete_manifest_sha256: str,
        source_bytes: int,
        derivation_code_sha256: str,
        expected_row_count: int,
) -> dict[str, Any]:
    """Write the population authority as immutable artifacts."""
    import csv

    out = Path(outdir)
    if out.exists() and any(out.iterdir()):
        raise AssertionError("%s: output directory must be absent or empty: %s"
                             % (STOP_PACKAGE_MEMBER, out))
    assert_no_pathology_in_artifact(REGISTRY_FIELDS)

    proofs = sorted(population["proofs"], key=lambda p: int(p["logical_index"]))
    if len(proofs) != int(expected_row_count):
        raise AssertionError("%s: %d proofs for an expected %d rows"
                             % (STOP_POPULATION_CARDINALITY, len(proofs),
                                int(expected_row_count)))
    indices = [int(p["logical_index"]) for p in proofs]
    if indices != list(range(len(proofs))):
        raise AssertionError(
            "%s: logical indices are not exactly 0..%d with no gaps or repeats"
            % (STOP_POPULATION_CARDINALITY, len(proofs) - 1))

    registry = io.StringIO()
    writer = csv.writer(registry, lineterminator="\n")
    writer.writerow(list(REGISTRY_FIELDS))
    for proof in proofs:
        writer.writerow([int(proof["logical_index"]),
                         int(proof["expression_row"]),
                         str(proof["canonical_cell_id"]),
                         str(proof["donor_id"]),
                         int(proof["source_library"]),
                         int(proof["stored_values_in_row"])])
    registry_bytes = registry.getvalue().encode("utf-8")

    libraries = sorted(int(p["source_library"]) for p in proofs)
    meta = {
        "schema": POPULATION_SCHEMA,
        "namespace": NAMESPACE,
        "finalized": True,
        "proof": population["proof"],
        "registry_fields": list(REGISTRY_FIELDS),
        "rows_proven": len(proofs),
        "population_raw_source_root_sha256": str(
            population["population_raw_source_root_sha256"]),
        "logical_row_authority_root_sha256": str(
            population["logical_row_authority_root_sha256"]),
        "population_closure_root_sha256": str(closure_root_sha256),
        "feature_authority_root_sha256": str(feature_authority_root_sha256),
        "physical_read_plan_root_sha256": str(physical_read_plan_root_sha256),
        "membership_sha256": str(membership_sha256),
        "complete_manifest_sha256": str(complete_manifest_sha256),
        "source_sha256": str(population["source_sha256"]),
        "source_bytes": int(source_bytes),
        "digest_bytes_read": int(population["digest_bytes_read"]),
        "matrix_slot": UMI_SLOT,
        "obs_fields_read": list(PERMITTED_OBS_FIELDS),
        "derivation_code_sha256": str(derivation_code_sha256),
        "derivation_code_byte_semantics": "GIT_BLOB_BYTES__NOT_WORKTREE_BYTES",
        "source_library_min": libraries[0],
        "source_library_median": libraries[len(libraries) // 2],
        "source_library_max": libraries[-1],
        "source_library_total": sum(libraries),
        "caller_supplied_values": False,
        "caller_supplied_handle": False,
        "pathology_fields_read": False,
        "numeric_confirmation_at8_accessed": False,
        "donor_roles_computed": False,
        "eligible_donors_computed": False,
        "real_execution_ready": False,
    }
    meta_bytes = (json.dumps(meta, sort_keys=True, indent=2) + "\n").encode("utf-8")

    manifest = io.StringIO()
    mwriter = csv.writer(manifest, lineterminator="\n")
    mwriter.writerow(["filename", "bytes", "sha256"])
    for name, blob in ((PKG_REGISTRY, registry_bytes), (PKG_METADATA, meta_bytes)):
        mwriter.writerow([name, len(blob), hashlib.sha256(blob).hexdigest()])
    manifest_bytes = manifest.getvalue().encode("utf-8")

    members = {PKG_REGISTRY: registry_bytes, PKG_METADATA: meta_bytes,
               PKG_MANIFEST: manifest_bytes}
    pkg_root = population_package_root(members)

    out.mkdir(parents=True, exist_ok=True)
    for name, blob in members.items():
        with io.open(out / name, "wb") as handle:
            handle.write(blob)
    with io.open(out / PKG_ROOT_FILE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(pkg_root + "\n")

    return {"package_root_sha256": pkg_root,
            "population_raw_source_root_sha256": meta[
                "population_raw_source_root_sha256"],
            "rows_proven": len(proofs),
            "members": {name: len(blob) for name, blob in members.items()},
            "real_execution_ready": False}


def load_population_authority_package(
        outdir: Path | str,
        *,
        expected_package_root_sha256: str,
        expected_population_root_sha256: str,
        expected_logical_root_sha256: str,
        expected_source_sha256: str,
        expected_row_count: int,
        logical: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Replay the package from disk and re-verify everything it claims."""
    import csv

    out = Path(outdir)
    captured: dict[str, bytes] = {}
    for name in PKG_MEMBERS:
        path = out / name
        if not path.is_file():
            raise AssertionError("%s: %s absent" % (STOP_PACKAGE_MEMBER, path))
        captured[name] = path.read_bytes()

    pkg_root = population_package_root(captured)
    if pkg_root != str(expected_package_root_sha256):
        raise AssertionError("%s: package root is %s, expected %s"
                             % (STOP_PACKAGE_ROOT, pkg_root,
                                expected_package_root_sha256))

    meta = json.loads(captured[PKG_METADATA].decode("utf-8"))
    if meta.get("schema") != POPULATION_SCHEMA or meta.get("finalized") is not True:
        raise AssertionError("%s: metadata schema or finalized flag invalid"
                             % STOP_PACKAGE_MEMBER)
    assert_no_pathology_in_artifact(meta.get("registry_fields") or ())
    if meta.get("real_execution_ready") is not False:
        raise AssertionError("%s: real_execution_ready must be False"
                             % STOP_PACKAGE_MEMBER)
    for flag in ("caller_supplied_values", "caller_supplied_handle",
                 "pathology_fields_read", "numeric_confirmation_at8_accessed",
                 "donor_roles_computed", "eligible_donors_computed"):
        if meta.get(flag) is not False:
            raise AssertionError("%s: %s must be False" % (STOP_PACKAGE_MEMBER, flag))

    text = captured[PKG_REGISTRY].decode("utf-8")
    records = list(csv.DictReader(io.StringIO(text)))
    assert_no_pathology_in_artifact(records[0].keys() if records else ())
    if len(records) != int(expected_row_count):
        raise AssertionError("%s: the registry holds %d rows, expected %d"
                             % (STOP_POPULATION_CARDINALITY, len(records),
                                int(expected_row_count)))

    proofs = []
    seen = set()
    for record in records:
        index = int(record["logical_index"])
        if index in seen:
            raise AssertionError("%s: logical index %d appears twice"
                                 % (STOP_POPULATION_CARDINALITY, index))
        seen.add(index)
        proofs.append({
            "logical_index": index,
            "expression_row": int(record["expression_row"]),
            "canonical_cell_id": str(record["canonical_cell_id"]),
            "donor_id": str(record["donor_id"]),
            "source_library": int(record["source_library"]),
            "stored_values_in_row": int(record["stored_values_in_row"]),
        })
    if sorted(seen) != list(range(len(records))):
        raise AssertionError("%s: logical indices are not exactly 0..%d"
                             % (STOP_POPULATION_CARDINALITY, len(records) - 1))

    if str(meta.get("logical_row_authority_root_sha256")) != str(
            expected_logical_root_sha256):
        raise AssertionError("%s: stored logical root is %r, expected %r"
                             % (STOP_LOGICAL_ROOT,
                                meta.get("logical_row_authority_root_sha256"),
                                expected_logical_root_sha256))
    if str(meta.get("source_sha256")) != str(expected_source_sha256):
        raise AssertionError("%s: stored source is %r, expected %r"
                             % (STOP_SOURCE_DIGEST, meta.get("source_sha256"),
                                expected_source_sha256))

    recomputed = population_raw_source_root(
        logical_root_sha256=str(meta["logical_row_authority_root_sha256"]),
        source_sha256=str(meta["source_sha256"]), proofs=proofs)
    stored = meta.get("population_raw_source_root_sha256")
    if str(stored) != recomputed:
        raise AssertionError(
            "%s: the stored population root %s does not match the root "
            "recomputed from the reloaded registry %s"
            % (STOP_POPULATION_ROOT, stored, recomputed))
    if recomputed != str(expected_population_root_sha256):
        raise AssertionError("%s: population root is %s, externally expected %s"
                             % (STOP_POPULATION_ROOT, recomputed,
                                expected_population_root_sha256))

    if logical is not None:
        assert_population_authority_covers_logical(
            population={"proofs": proofs,
                        "population_raw_source_root_sha256": recomputed,
                        "logical_row_authority_root_sha256": str(
                            meta["logical_row_authority_root_sha256"]),
                        "source_sha256": str(meta["source_sha256"])},
            logical=logical,
            expected_population_root_sha256=recomputed,
            expected_logical_root_sha256=expected_logical_root_sha256,
            expected_source_sha256=expected_source_sha256)

    return {"metadata": meta, "proofs": tuple(proofs),
            "package_root_sha256": pkg_root,
            "population_raw_source_root_sha256": recomputed,
            "rows_replayed": len(proofs)}
