"""T0 V20 pathology-blind feature-projection authority.

Turns the accepted V20 feature split into an ordered projection over the frozen
41,238-address space, so a later reader can pull exactly the right columns in
exactly the right order.

The split's own row order is the authority. Address-index order is a different
projection over the same genes, and the two genuinely differ, so the projection
root is computed over the split ordering and any re-sort produces a different
root rather than a silently equivalent one.

Two traps found earlier in this lane are refused by construction. The frozen
`molecular_address_index` from the Stage81A2R registry is the only column index
this module will emit; the provenance table's own per-source feature position is
never consulted, because four of four spot checks showed it landing on unrelated
genes and a module that read it would project the wrong columns. And tracked
authorities are resolved from Git blob bytes at an explicit pinned commit, never
from platform-transformed worktree bytes, with the object's existence confirmed
before any digest is taken so a failed lookup can never be mistaken for the
digest of empty bytes.

Nothing here reads pathology, and nothing here authorizes real T0 execution.
"""

from __future__ import annotations

import csv
import hashlib
import io
import subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "JEPA_T0_V20_FEATURE_PROJECTION_AUTHORITY_V1"
NAMESPACE = "T0-V20-FEATURE-PROJECTION-V1"

ADDRESS_SPACE_SIZE = 41_238
AUTHORIZED_FEATURE_ROLES = ("SCORING", "COHERENCE_HOLDOUT")
MEASURED_STATUS = "addressable_measured_zero_or_nonzero_at_runtime"

STOP_PINNED_PATH = "STOP_T0_S2_PINNED_PATH_NOT_CANONICAL"
STOP_PINNED_ABSENT = "STOP_T0_S2_PINNED_OBJECT_ABSENT"
STOP_PINNED_IRREGULAR = "STOP_T0_S2_PINNED_OBJECT_NOT_REGULAR_FILE"
STOP_PINNED_DIGEST = "STOP_T0_S2_PINNED_BLOB_DIGEST_MISMATCH"
STOP_SPLIT_COLUMNS = "STOP_T0_S2_SPLIT_COLUMNS_UNEXPECTED"
STOP_SPLIT_DUPLICATE = "STOP_T0_S2_SPLIT_ADDRESS_NOT_UNIQUE"
STOP_ROLE = "STOP_T0_S2_FEATURE_ROLE_NOT_AUTHORIZED"
STOP_REGISTRY_COLUMNS = "STOP_T0_S2_REGISTRY_COLUMNS_UNEXPECTED"
STOP_REGISTRY_INJECTIVE = "STOP_T0_S2_REGISTRY_INDEX_NOT_INJECTIVE"
STOP_NOT_IN_REGISTRY = "STOP_T0_S2_ADDRESS_NOT_IN_REGISTRY"
STOP_INDEX_RANGE = "STOP_T0_S2_ADDRESS_INDEX_OUT_OF_RANGE"
STOP_NO_SUPPORT = "STOP_T0_S2_NO_SUPPORT_ROWS_FOR_MATRIX"
STOP_NOT_MEASURED = "STOP_T0_S2_FEATURE_NOT_MEASURED"


def canonical_relative_path(relative: Any) -> str | None:
    """One accepted spelling of a repository-relative path, or None.

    Same rule the checkpoint validator uses: a declaration is an identity, not
    a query. Rejects NUL, backslash, any colon (pathspec magic and Windows
    drives alike) and any empty, `.` or `..` component, which also excludes
    absolute and UNC forms.
    """
    if not isinstance(relative, str) or not relative:
        return None
    if any(character in relative for character in ("\x00", "\\", ":")):
        return None
    if any(part in ("", ".", "..") for part in relative.split("/")):
        return None
    return relative


def _git_text(repo: Path, *args: str) -> str | None:
    completed = subprocess.run(
        ["git", "-c", "safe.directory=*", "-C", str(repo), *args],
        capture_output=True, text=True, check=False)
    if completed.returncode:
        return None
    return completed.stdout.strip()


def _git_binary(repo: Path, *args: str) -> bytes | None:
    completed = subprocess.run(
        ["git", "-c", "safe.directory=*", "-C", str(repo), *args],
        capture_output=True, check=False)
    if completed.returncode:
        return None
    return completed.stdout


def resolve_pinned_blob(
    repo: Path | str, commit: str, relative: str, expected_sha256: str
) -> bytes:
    """Return the exact Git object payload for *relative* at *commit*.

    Existence is confirmed before anything is hashed, so a failed lookup cannot
    be digested as empty bytes. Payloads are read in binary, because text-mode
    newline translation would rewrite a blob and change its digest.
    """
    canonical = canonical_relative_path(relative)
    if canonical is None:
        raise AssertionError("%s: %r is not a canonical repository-relative path"
                             % (STOP_PINNED_PATH, relative))
    listing = _git_text(Path(repo), "--literal-pathspecs", "ls-tree", "--full-tree",
                        str(commit), "--", canonical)
    if not listing:
        raise AssertionError("%s: %s is not present at %s"
                             % (STOP_PINNED_ABSENT, canonical, commit))
    head, _, path = listing.partition("\t")
    fields = head.split()
    if len(fields) != 3 or path.strip('"') != canonical:
        raise AssertionError("%s: %s did not resolve to itself at %s"
                             % (STOP_PINNED_ABSENT, canonical, commit))
    mode, object_type, oid = fields
    if object_type != "blob" or mode not in ("100644", "100755"):
        raise AssertionError("%s: %s is %s mode %s"
                             % (STOP_PINNED_IRREGULAR, canonical, object_type, mode))
    if _git_text(Path(repo), "cat-file", "-e", oid) is None:
        raise AssertionError("%s: object %s for %s is unreadable"
                             % (STOP_PINNED_ABSENT, oid, canonical))
    payload = _git_binary(Path(repo), "cat-file", "blob", oid)
    if payload is None:
        raise AssertionError("%s: object %s for %s is unreadable"
                             % (STOP_PINNED_ABSENT, oid, canonical))
    actual = hashlib.sha256(payload).hexdigest()
    if actual != str(expected_sha256):
        raise AssertionError("%s: %s at %s is %s, expected %s"
                             % (STOP_PINNED_DIGEST, canonical, commit, actual,
                                expected_sha256))
    return payload


def _rows(payload: bytes) -> tuple[list[str], list[dict[str, str]]]:
    handle = io.StringIO(bytes(payload).decode("utf-8-sig"))
    reader = csv.DictReader(handle)
    columns = list(reader.fieldnames or [])
    return columns, [dict(record) for record in reader]


def projection_root(projection: Sequence[Mapping[str, Any]]) -> str:
    """Canonical digest over the ordered projection.

    Order-sensitive by construction: the split ordering is the science, so a
    re-sorted projection must not be able to produce the same root.
    """
    digest = hashlib.sha256()
    digest.update(b"T0_V20_FEATURE_PROJECTION_V1")
    for row in projection:
        digest.update(b"|")
        digest.update(str(row["split_row_index"]).encode("utf-8"))
        digest.update(b"\x1f")
        digest.update(str(row["molecular_address_id"]).encode("utf-8"))
        digest.update(b"\x1f")
        digest.update(str(row["molecular_address_index"]).encode("utf-8"))
        digest.update(b"\x1f")
        digest.update(str(row["feature_role"]).encode("utf-8"))
    return digest.hexdigest()


def build_feature_projection(
    *,
    split_bytes: bytes,
    registry_bytes: bytes,
    support_bytes: bytes,
    matrix_id: str,
    address_space_size: int = ADDRESS_SPACE_SIZE,
) -> dict[str, Any]:
    """Project the frozen split onto frozen address indices, in split order."""
    split_columns, split_rows = _rows(split_bytes)
    for required in ("molecular_address_id", "feature_role"):
        if required not in split_columns:
            raise AssertionError("%s: %r absent from the split header"
                                 % (STOP_SPLIT_COLUMNS, required))

    addresses = [str(row["molecular_address_id"]).strip() for row in split_rows]
    if len(set(addresses)) != len(addresses):
        raise AssertionError("%s: %d split rows carry %d distinct addresses"
                             % (STOP_SPLIT_DUPLICATE, len(addresses), len(set(addresses))))
    roles = [str(row["feature_role"]).strip() for row in split_rows]
    unauthorized = sorted({role for role in roles if role not in AUTHORIZED_FEATURE_ROLES})
    if unauthorized:
        raise AssertionError("%s: %r are not in %r"
                             % (STOP_ROLE, unauthorized, list(AUTHORIZED_FEATURE_ROLES)))

    registry_columns, registry_rows = _rows(registry_bytes)
    for required in ("molecular_address_index", "molecular_address_id"):
        if required not in registry_columns:
            raise AssertionError("%s: %r absent from the registry header"
                                 % (STOP_REGISTRY_COLUMNS, required))
    index_by_address: dict[str, int] = {}
    seen_indices: set[int] = set()
    for record in registry_rows:
        address = str(record["molecular_address_id"]).strip()
        index = int(str(record["molecular_address_index"]).strip())
        if address in index_by_address or index in seen_indices:
            raise AssertionError(
                "%s: the registry maps address %s or index %d more than once"
                % (STOP_REGISTRY_INJECTIVE, address, index))
        index_by_address[address] = index
        seen_indices.add(index)

    support_columns, support_rows = _rows(support_bytes)
    for required in ("matrix_id", "molecular_address_id", "measured_address"):
        if required not in support_columns:
            raise AssertionError("%s: %r absent from the support header"
                                 % (STOP_REGISTRY_COLUMNS, required))
    measured_addresses = set()
    support_row_count = 0
    for record in support_rows:
        if str(record["matrix_id"]).strip() != str(matrix_id):
            continue
        support_row_count += 1
        if str(record["measured_address"]).strip() == "True":
            measured_addresses.add(str(record["molecular_address_id"]).strip())
    if support_row_count == 0:
        raise AssertionError("%s: the support table carries no rows for %r"
                             % (STOP_NO_SUPPORT, matrix_id))

    projection = []
    for split_row_index, record in enumerate(split_rows):
        address = str(record["molecular_address_id"]).strip()
        if address not in index_by_address:
            raise AssertionError("%s: split row %d names %s"
                                 % (STOP_NOT_IN_REGISTRY, split_row_index, address))
        index = index_by_address[address]
        if index < 0 or index >= int(address_space_size):
            raise AssertionError("%s: %s maps to index %d outside 0..%d"
                                 % (STOP_INDEX_RANGE, address, index,
                                    int(address_space_size) - 1))
        if address not in measured_addresses:
            raise AssertionError("%s: %s is not measured in %r"
                                 % (STOP_NOT_MEASURED, address, matrix_id))
        projection.append({
            "split_row_index": split_row_index,
            "molecular_address_id": address,
            "molecular_address_index": index,
            "feature_role": str(record["feature_role"]).strip(),
        })

    role_counts: dict[str, int] = {}
    for row in projection:
        role_counts[row["feature_role"]] = role_counts.get(row["feature_role"], 0) + 1

    return {
        "schema": SCHEMA,
        "namespace": NAMESPACE,
        "matrix_id": str(matrix_id),
        "address_space_size": int(address_space_size),
        "projection": projection,
        "projected_feature_count": len(projection),
        "role_counts": dict(sorted(role_counts.items())),
        "projection_root_sha256": projection_root(projection),
        "split_sha256": hashlib.sha256(split_bytes).hexdigest(),
        "registry_sha256": hashlib.sha256(registry_bytes).hexdigest(),
        "support_sha256": hashlib.sha256(support_bytes).hexdigest(),
        "ordering": "EXACT_SPLIT_ROW_ORDER__NOT_ADDRESS_INDEX_ORDER",
        "real_execution_ready": False,
    }


def assert_projection_lawful(
    built: Mapping[str, Any], *, expected_projection_root_sha256: str
) -> dict[str, Any]:
    """Re-verify a projection against an externally supplied root."""
    recomputed = projection_root(built["projection"])
    if recomputed != str(expected_projection_root_sha256):
        raise AssertionError(
            "STOP_T0_S2_PROJECTION_ROOT_MISMATCH: %s is not the expected %s"
            % (recomputed, expected_projection_root_sha256))
    indices = [row["molecular_address_index"] for row in built["projection"]]
    if len(set(indices)) != len(indices):
        raise AssertionError("STOP_T0_S2_PROJECTION_INDEX_NOT_UNIQUE")
    if [row["split_row_index"] for row in built["projection"]] != list(range(len(indices))):
        raise AssertionError("STOP_T0_S2_PROJECTION_SPLIT_ORDER_BROKEN")
    return {"projection_root_sha256": recomputed, "features": len(indices)}
