"""Per-donor IMMUNE support-count authority for T0.

Why this exists
---------------
`t0_donor_role_authority_v2` and `t0_discovery_confirmation_split_v2` consume a
`cells` column per donor, and evaluate the frozen tail-measurability flag as
`cells >= 80` against it. Until now that column was handed to the role builder as
an informal frame with no authority behind it, which left the tail flag resting
on an unbound number.

Which population `cells` counts matters, and getting it wrong is silent. It is the
accepted broad-IMMUNE support count -- 46 donors summing to exactly 20,804, a mean
near 452 -- and NOT the 638,150 all-op31 count. Against the all-op31 count every
donor would clear the 80-cell floor trivially and the tail flag would carry no
information at all.

Scope of the 80-cell floor
--------------------------
The floor governs TAIL MEASURABILITY ONLY. The frozen role code says so in terms:
tail measurability "must not influence the parent-state donor roles". So this
authority reports `cells` and the derived `tail_measurable` flag, and neither may
enter parent eligibility or split assignment. `tail_measurable` is recorded here
as an outcome for audit; the split is computed without it.

Pathology
---------
Nothing here reads, parses or emits any pathology value. It is a cell count.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "JEPA_T0_IMMUNE_SUPPORT_COUNT_AUTHORITY_V1"
NAMESPACE = "T0-IMMUNE-SUPPORT-COUNT-V1"
DOMAIN_TAG = "T0-IMMUNE-SUPPORT-COUNT-V1-TYPED-LENGTH-PREFIXED"

REGISTRY = "T0_IMMUNE_SUPPORT_COUNT_REGISTRY.csv"
METADATA = "T0_IMMUNE_SUPPORT_COUNT_METADATA.json"
MANIFEST = "T0_IMMUNE_SUPPORT_COUNT_MANIFEST.csv"
ROOT_FILE = "T0_IMMUNE_SUPPORT_COUNT_PACKAGE_ROOT_SHA256.txt"
MEMBERS = (REGISTRY, METADATA, MANIFEST)

STOP_MEMBERSHIP_DIGEST = "STOP_T0_SUPPORT_MEMBERSHIP_DIGEST_MISMATCH"
STOP_COLUMNS = "STOP_T0_SUPPORT_REQUIRED_COLUMN_ABSENT"
STOP_OPERATOR = "STOP_T0_SUPPORT_OPERATOR_MISMATCH"
STOP_MATRIX = "STOP_T0_SUPPORT_MATRIX_MISMATCH"
STOP_DUPLICATE_CELL = "STOP_T0_SUPPORT_DUPLICATE_CELL"
STOP_DUPLICATE_DONOR = "STOP_T0_SUPPORT_DUPLICATE_DONOR_ROW"
STOP_NOT_INTEGER = "STOP_T0_SUPPORT_COUNT_NOT_EXACT_POSITIVE_INTEGER"
STOP_DONOR_SET = "STOP_T0_SUPPORT_CANDIDATE_DONOR_SET_MISMATCH"
STOP_GEOMETRY = "STOP_T0_SUPPORT_PRODUCTION_GEOMETRY_MISMATCH"
STOP_ROOT_MISMATCH = "STOP_T0_SUPPORT_ROOT_MISMATCH"
STOP_PACKAGE_MEMBER = "STOP_T0_SUPPORT_PACKAGE_MEMBER_INVALID"
STOP_FIELD_SCHEMA = "STOP_T0_SUPPORT_FIELD_SCHEMA_VIOLATION"
STOP_FLOOR_SCOPE = "STOP_T0_SUPPORT_TAIL_FLOOR_USED_OUTSIDE_TAIL_SCOPE"

OP31_OPERATOR_INDEX = 31
MTG_MATRIX_ID = "sea_ad_mtg_rna_final_2026"
PRODUCTION_DONORS = 46
PRODUCTION_IMMUNE_CELLS = 20_804

# Frozen V18 constant. Tail measurability only.
TAIL_MIN_CELLS = 80
TAIL_FLOOR_SCOPE = "TAIL_MEASURABILITY_ONLY__NEVER_ELIGIBILITY_OR_PARENT_ROLE"

MEMBERSHIP_COLUMNS = ("source", "matrix_id", "operator_index", "donor_id", "cell_id")


def _typed(value: Any) -> bytes:
    """Type-tagged, length-prefixed framing; injective over the declared types."""
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


def _is_hex64(value: Any) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value))


def exact_positive_integer(value: Any, *, what: str) -> int:
    """Accept only an exact positive integer. Refuse bool, float and blank."""
    if isinstance(value, bool):
        raise AssertionError("%s: %s is a bool" % (STOP_NOT_INTEGER, what))
    if isinstance(value, int):
        number = int(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text or not text.isdigit():
            raise AssertionError("%s: %s is %r" % (STOP_NOT_INTEGER, what, value))
        number = int(text)
    else:
        raise AssertionError("%s: %s is %r" % (STOP_NOT_INTEGER, what, type(value)))
    if number <= 0:
        raise AssertionError("%s: %s is %d" % (STOP_NOT_INTEGER, what, number))
    return number


def _rows(raw: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    text = bytes(raw).decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return tuple(reader.fieldnames or ()), [dict(row) for row in reader]


def _require_columns(columns: Sequence[str], required: Iterable[str],
                     what: str) -> None:
    for name in required:
        if name not in columns:
            raise AssertionError("%s: %s lacks %r" % (STOP_COLUMNS, what, name))


def support_counts_from_membership(
        *,
        membership_bytes: bytes,
        expected_membership_sha256: str,
        operator_index: int = OP31_OPERATOR_INDEX,
        matrix_id: str = MTG_MATRIX_ID,
) -> dict[str, int]:
    """Per-donor accepted broad-IMMUNE cell counts.

    The membership bytes are authenticated before anything is parsed, and the
    operator and matrix VALUES are compared rather than merely required to be
    present: requiring the columns and ignoring what they say would let a
    membership for another operator or matrix define this support.
    """
    actual = hashlib.sha256(bytes(membership_bytes)).hexdigest()
    if actual != str(expected_membership_sha256):
        raise AssertionError("%s: membership is %s, expected %s"
                            % (STOP_MEMBERSHIP_DIGEST, actual,
                               expected_membership_sha256))
    columns, records = _rows(membership_bytes)
    _require_columns(columns, MEMBERSHIP_COLUMNS, "membership")

    counts: Counter[str] = Counter()
    seen: set[str] = set()
    for position, record in enumerate(records):
        declared_operator = str(record["operator_index"]).strip()
        if int(declared_operator) != int(operator_index):
            raise AssertionError("%s: row %d is operator %s, expected %d"
                                % (STOP_OPERATOR, position, declared_operator,
                                   int(operator_index)))
        if str(record["matrix_id"]).strip() != str(matrix_id):
            raise AssertionError("%s: row %d is matrix %r, expected %r"
                                % (STOP_MATRIX, position, record["matrix_id"],
                                   matrix_id))
        cell = str(record["cell_id"]).strip()
        if cell in seen:
            raise AssertionError("%s: %s appears more than once"
                                % (STOP_DUPLICATE_CELL, cell))
        seen.add(cell)
        counts[str(record["donor_id"]).strip()] += 1
    return dict(counts)


def build_support_rows(
        *,
        counts_by_donor: Mapping[str, int],
        candidate_donors: Sequence[str] | None = None,
) -> tuple[dict[str, Any], ...]:
    """Bind one exact positive integer per donor, in deterministic order.

    When the candidate donor set is supplied it must match exactly. A donor
    present in the candidate universe but absent from the support would
    otherwise silently drop out of the design, and a donor in the support but
    outside the universe would silently enter it.
    """
    donors = sorted(map(str, counts_by_donor), key=lambda d: d.encode("utf-8"))
    if len(donors) != len(set(donors)):
        raise AssertionError("%s: duplicate donor key" % STOP_DUPLICATE_DONOR)

    if candidate_donors is not None:
        expected = {str(d) for d in candidate_donors}
        actual = set(donors)
        if actual != expected:
            raise AssertionError(
                "%s: support-only %s, candidate-only %s"
                % (STOP_DONOR_SET, sorted(actual - expected),
                   sorted(expected - actual)))

    rows = []
    for donor in donors:
        cells = exact_positive_integer(counts_by_donor[donor],
                                       what="cells for %s" % donor)
        rows.append({
            "donor_id": donor,
            "cells": cells,
            # Recorded as an OUTCOME for audit. The frozen role rule computes
            # the split without it, and it may not enter eligibility.
            "tail_measurable": bool(cells >= TAIL_MIN_CELLS),
        })
    return tuple(rows)


def assert_tail_floor_stays_in_scope() -> bool:
    """The 80-cell floor may never widen beyond tail measurability."""
    if TAIL_FLOOR_SCOPE != "TAIL_MEASURABILITY_ONLY__NEVER_ELIGIBILITY_OR_PARENT_ROLE":
        raise AssertionError("%s: scope is %r" % (STOP_FLOOR_SCOPE, TAIL_FLOOR_SCOPE))
    if TAIL_MIN_CELLS != 80:
        raise AssertionError("%s: the frozen floor is 80, not %d"
                            % (STOP_FLOOR_SCOPE, TAIL_MIN_CELLS))
    return True


def assert_production_geometry(
        rows: Sequence[Mapping[str, Any]],
        *,
        expected_donors: int = PRODUCTION_DONORS,
        expected_cells: int = PRODUCTION_IMMUNE_CELLS,
) -> bool:
    """46 donors, one row each, summing to exactly 20,804."""
    donors = [str(r["donor_id"]) for r in rows]
    if len(donors) != len(set(donors)):
        raise AssertionError("%s: %s" % (STOP_DUPLICATE_DONOR,
                                         sorted({d for d in donors
                                                 if donors.count(d) > 1})))
    if len(rows) != int(expected_donors):
        raise AssertionError("%s: %d donors, expected %d"
                            % (STOP_GEOMETRY, len(rows), int(expected_donors)))
    total = sum(int(r["cells"]) for r in rows)
    if total != int(expected_cells):
        raise AssertionError("%s: cells sum to %d, expected %d"
                            % (STOP_GEOMETRY, total, int(expected_cells)))
    return True


def support_root(rows: Sequence[Mapping[str, Any]]) -> str:
    """Digest over the bound counts, with explicit cardinality."""
    parts = [_typed(DOMAIN_TAG), _typed(SCHEMA), _typed(NAMESPACE),
             _typed(TAIL_MIN_CELLS), _typed(len(rows))]
    for row in rows:
        parts.append(_typed([str(row["donor_id"]), int(row["cells"]),
                             bool(row["tail_measurable"])]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def package_root(members: Mapping[str, bytes]) -> str:
    names = sorted(members)
    parts = [_typed(DOMAIN_TAG), _typed("PACKAGE"), _typed(len(names))]
    for name in names:
        parts.append(_typed([name,
                             hashlib.sha256(bytes(members[name])).hexdigest()]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def build_production_authority(
        outdir: Path | str,
        *,
        membership_bytes: bytes,
        expected_membership_sha256: str,
        derivation_code_sha256: str,
        candidate_donors: Sequence[str] | None = None,
        operator_index: int = OP31_OPERATOR_INDEX,
        matrix_id: str = MTG_MATRIX_ID,
        expected_donors: int = PRODUCTION_DONORS,
        expected_cells: int = PRODUCTION_IMMUNE_CELLS,
) -> dict[str, Any]:
    """Derive the support counts from the authenticated membership and package.

    Bytes in, package out. No preassembled rows and no detached digest labels:
    the membership digest recorded here is computed from the bytes this call
    authenticated.
    """
    out = Path(outdir)
    if out.exists() and any(out.iterdir()):
        raise AssertionError("%s: output directory must be absent or empty: %s"
                            % (STOP_PACKAGE_MEMBER, out))
    if not _is_hex64(derivation_code_sha256):
        raise AssertionError("%s: derivation_code_sha256 is not a lowercase hex sha256"
                            % STOP_FIELD_SCHEMA)
    assert_tail_floor_stays_in_scope()

    payload = bytes(membership_bytes)
    counts = support_counts_from_membership(
        membership_bytes=payload,
        expected_membership_sha256=expected_membership_sha256,
        operator_index=operator_index, matrix_id=matrix_id)
    rows = build_support_rows(counts_by_donor=counts,
                              candidate_donors=candidate_donors)
    assert_production_geometry(rows, expected_donors=expected_donors,
                               expected_cells=expected_cells)

    root = support_root(rows)
    registry = io.StringIO()
    writer = csv.writer(registry, lineterminator="\n")
    writer.writerow(["donor_id", "cells", "tail_measurable"])
    for row in rows:
        writer.writerow([row["donor_id"], int(row["cells"]),
                         bool(row["tail_measurable"])])
    registry_bytes = registry.getvalue().encode("utf-8")

    meta = {
        "schema": SCHEMA,
        "namespace": NAMESPACE,
        "finalized": True,
        "donor_count": len(rows),
        "cell_total": sum(int(r["cells"]) for r in rows),
        "population": "ACCEPTED_BROAD_IMMUNE_READER_FIT_SUPPORT",
        "not_the_all_op31_population": True,
        "support_root_sha256": root,
        "membership_sha256": hashlib.sha256(payload).hexdigest(),
        "derivation_code_sha256": str(derivation_code_sha256),
        "derivation_code_byte_semantics": "GIT_BLOB_BYTES__NOT_WORKTREE_BYTES",
        "tail_min_cells": TAIL_MIN_CELLS,
        "tail_floor_scope": TAIL_FLOOR_SCOPE,
        "tail_measurable_donors": sum(1 for r in rows if r["tail_measurable"]),
        "role_consumption": (
            "SOLE_LAWFUL_SOURCE_FOR_THE_DONOR_ROLE_BUILDER_CELLS_INPUT_AND_"
            "TAIL_MEASURABLE_FLAG"),
        "eligibility_role": (
            "NOT_AN_ELIGIBILITY_INPUT__TAIL_FLOOR_MUST_NOT_AFFECT_PARENT_"
            "ELIGIBILITY_OR_SPLIT_ASSIGNMENT"),
        "pathology_values_read": False,
        "real_execution_ready": False,
    }
    meta_bytes = (json.dumps(meta, sort_keys=True, indent=2) + "\n").encode("utf-8")

    manifest = io.StringIO()
    mwriter = csv.writer(manifest, lineterminator="\n")
    mwriter.writerow(["filename", "bytes", "sha256"])
    for name, blob in ((REGISTRY, registry_bytes), (METADATA, meta_bytes)):
        mwriter.writerow([name, len(blob), hashlib.sha256(blob).hexdigest()])
    manifest_bytes = manifest.getvalue().encode("utf-8")

    members = {REGISTRY: registry_bytes, METADATA: meta_bytes,
               MANIFEST: manifest_bytes}
    pkg_root = package_root(members)

    out.mkdir(parents=True, exist_ok=True)
    for name, blob in members.items():
        with io.open(out / name, "wb") as handle:
            handle.write(blob)
    with io.open(out / ROOT_FILE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(pkg_root + "\n")

    return {"support_root_sha256": root, "package_root_sha256": pkg_root,
            "donor_count": len(rows), "cell_total": meta["cell_total"],
            "tail_measurable_donors": meta["tail_measurable_donors"],
            "membership_sha256": meta["membership_sha256"],
            "real_execution_ready": False}


def load_authority(
        outdir: Path | str,
        *,
        expected_package_root_sha256: str,
        expected_support_root_sha256: str,
        expected_membership_sha256: str,
        expected_derivation_code_sha256: str | None = None,
) -> dict[str, Any]:
    """Read the authority back, binding its parent identity externally.

    Every member is read once and verified against those captured bytes, and
    each root must satisfy stored == recomputed == externally expected.
    """
    out = Path(outdir)
    captured: dict[str, bytes] = {}
    for name in MEMBERS:
        path = out / name
        if not path.is_file():
            raise AssertionError("%s: %s absent" % (STOP_PACKAGE_MEMBER, path))
        captured[name] = path.read_bytes()

    pkg_root = package_root(captured)
    if pkg_root != str(expected_package_root_sha256):
        raise AssertionError("%s: package root is %s, expected %s"
                            % (STOP_ROOT_MISMATCH, pkg_root,
                               expected_package_root_sha256))

    columns, records = _rows(captured[REGISTRY])
    _require_columns(columns, ("donor_id", "cells", "tail_measurable"), REGISTRY)
    rows = build_support_rows(
        counts_by_donor={r["donor_id"]: r["cells"] for r in records})
    root = support_root(rows)
    if root != str(expected_support_root_sha256):
        raise AssertionError("%s: support root is %s, expected %s"
                            % (STOP_ROOT_MISMATCH, root,
                               expected_support_root_sha256))

    meta = json.loads(captured[METADATA].decode("utf-8"))
    if meta.get("schema") != SCHEMA or meta.get("finalized") is not True:
        raise AssertionError("%s: metadata schema or finalized flag invalid"
                            % STOP_FIELD_SCHEMA)
    if meta.get("support_root_sha256") != root:
        raise AssertionError("%s: metadata records %r but the registry yields %s"
                            % (STOP_ROOT_MISMATCH,
                               meta.get("support_root_sha256"), root))
    if str(meta.get("membership_sha256")) != str(expected_membership_sha256):
        raise AssertionError("%s: membership is stored as %r, externally expected %r"
                            % (STOP_ROOT_MISMATCH, meta.get("membership_sha256"),
                               expected_membership_sha256))
    if expected_derivation_code_sha256 is not None:
        if str(meta.get("derivation_code_sha256")) != str(expected_derivation_code_sha256):
            raise AssertionError(
                "%s: derivation code is stored as %r, externally expected %r"
                % (STOP_ROOT_MISMATCH, meta.get("derivation_code_sha256"),
                   expected_derivation_code_sha256))
    if meta.get("tail_floor_scope") != TAIL_FLOOR_SCOPE:
        raise AssertionError("%s: stored tail floor scope is %r"
                            % (STOP_FLOOR_SCOPE, meta.get("tail_floor_scope")))
    if meta.get("real_execution_ready") is not False:
        raise AssertionError("%s: real_execution_ready must be False"
                            % STOP_FIELD_SCHEMA)
    return {"rows": rows, "metadata": meta, "support_root_sha256": root,
            "package_root_sha256": pkg_root}
