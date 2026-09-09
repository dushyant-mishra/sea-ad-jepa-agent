"""T0 technical-completeness authority: threshold-free definedness.

Status
------
`technical_complete` is a required eligibility input of
`t0_donor_role_authority_v2` that had no definition anywhere in the frozen
package. It was resolved by owner decision on 2026-09-08 as a THRESHOLD-FREE
definedness and computability predicate, and this module implements exactly that.

The predicate asks whether the frozen technical summaries are mathematically
defined on a lawfully authenticated substrate. It is NOT a biological-quality
filter, and it may not remove a donor because that donor's data are "low
quality". The frozen package contains no depth or detection thresholds, so
inventing one here would be a post-hoc, outcome-adjacent cutoff -- precisely what
the project's freeze discipline exists to prevent.

The exact formulas, recovered not paraphrased
---------------------------------------------
Read verbatim off `t0_confirmation_raw_v1` in the accepted V20 package:

    per cell    qdepth  = log1p(source_library)
                detect  = count_nonzero(A) / 35076

                where A is the full 35,076-feature B1 projection for that cell.
                The module's own comment says "Q_DETECT is defined on all 35,076
                scalar-measured addresses", and it enforces X.shape == (n, 35076).
                So Q_DETECT covers the whole measurement universe, NOT the 28,061
                SCORING subset, and it therefore depends on the B1 projection
                rather than on raw address-space rows alone.

    per donor   Q_DEPTH  = mean(qdepth) over that donor's authenticated cells
                Q_DETECT = mean(detect)  over that donor's authenticated cells

Fail-closed
-----------
An authority or provenance failure is a GLOBAL STOP and never
`technical_complete=False`. A wrong source digest, a missing accepted membership
cell, an identity mismatch, a wrong row or a counts-digest failure are B2 STOPs.
Letting any of them reappear as a merely "technically incomplete" donor would turn
eligibility into a quiet way to drop inconvenient donors, so this module raises on
them instead of recording a False.

Production status
-----------------
A production run of this authority requires the authenticated B2 substrate and the
B1 projection, and the production B2 run is not authorized. So this module is
exercised on synthetic fixtures only, and nothing here sets or implies readiness.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "JEPA_T0_TECHNICAL_COMPLETENESS_AUTHORITY_V1"
NAMESPACE = "T0-TECHNICAL-COMPLETENESS-V1"
DOMAIN_TAG = "T0-TECHNICAL-COMPLETENESS-V1-TYPED-LENGTH-PREFIXED"

REGISTRY = "T0_TECHNICAL_COMPLETENESS_REGISTRY.csv"
METADATA = "T0_TECHNICAL_COMPLETENESS_METADATA.json"
MANIFEST = "T0_TECHNICAL_COMPLETENESS_MANIFEST.csv"
ROOT_FILE = "T0_TECHNICAL_COMPLETENESS_PACKAGE_ROOT_SHA256.txt"
MEMBERS = (REGISTRY, METADATA, MANIFEST)

STOP_SUBSTRATE = "STOP_T0_TECHNICAL_COMPLETENESS_SUBSTRATE_NOT_LAWFUL"
STOP_PROJECTION_WIDTH = "STOP_T0_TECHNICAL_COMPLETENESS_PROJECTION_WIDTH_NOT_35076"
STOP_LIBRARY = "STOP_T0_TECHNICAL_COMPLETENESS_SOURCE_LIBRARY_NOT_POSITIVE_INTEGER"
STOP_COUNTS = "STOP_T0_TECHNICAL_COMPLETENESS_PROJECTED_COUNTS_NOT_NONNEGATIVE_INTEGERS"
STOP_NO_CELLS = "STOP_T0_TECHNICAL_COMPLETENESS_DONOR_HAS_NO_AUTHENTICATED_CELL"
STOP_DONOR_SET = "STOP_T0_TECHNICAL_COMPLETENESS_CANDIDATE_DONOR_SET_MISMATCH"
STOP_THRESHOLD = "STOP_T0_TECHNICAL_COMPLETENESS_THRESHOLD_INTRODUCED"
STOP_PARENT_IDENTITY = "STOP_T0_TECHNICAL_COMPLETENESS_PARENT_IDENTITY_NOT_BOUND"
STOP_ROOT_MISMATCH = "STOP_T0_TECHNICAL_COMPLETENESS_ROOT_MISMATCH"
STOP_PACKAGE_MEMBER = "STOP_T0_TECHNICAL_COMPLETENESS_PACKAGE_MEMBER_INVALID"
STOP_FIELD_SCHEMA = "STOP_T0_TECHNICAL_COMPLETENESS_FIELD_SCHEMA_VIOLATION"
STOP_DETACHED_VALUES = "STOP_T0_TECHNICAL_COMPLETENESS_DETACHED_VALUES_REFUSED"
STOP_PROJECTION_ROOT = "STOP_T0_TECHNICAL_COMPLETENESS_PROJECTION_ROOT_MISMATCH"
STOP_LOGICAL_ROOT = "STOP_T0_TECHNICAL_COMPLETENESS_LOGICAL_ROOT_MISMATCH"
STOP_CLOSURE_ROOT = "STOP_T0_TECHNICAL_COMPLETENESS_CLOSURE_ROOT_MISMATCH"
STOP_PROJECTION_POSITIONS = "STOP_T0_TECHNICAL_COMPLETENESS_PROJECTION_POSITIONS_INVALID"

SCALAR_FEATURES = 35_076
SEMANTICS = "THRESHOLD_FREE_DEFINEDNESS_AND_COMPUTABILITY"

Q_DEPTH_CELL_FORMULA = "log1p(source_library)"
Q_DETECT_CELL_FORMULA = "count_nonzero(A) / 35076"
Q_DONOR_REDUCTION = "arithmetic mean over the donor's authenticated cells"
Q_DETECT_UNIVERSE = (
    "ALL 35,076 scalar-measured addresses of the B1 projection, NOT the 28,061 "
    "SCORING subset")
FORMULA_PROVENANCE = (
    "Recovered verbatim from t0_confirmation_raw_v1 in the accepted V20 package, "
    "not paraphrased from prose.")

# Cutoffs that must never appear. Declared so the prohibition is checkable.
FORBIDDEN_CUTOFFS = ("Q_DEPTH_MINIMUM", "Q_DETECT_MINIMUM",
                     "CELL_COUNT_QC_FLOOR", "TAIL_MIN_CELLS_AS_ELIGIBILITY",
                     "DATA_ADAPTIVE_THRESHOLD")
AUTHORITY_FAILURE_IS_A_GLOBAL_STOP = True


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


def _typed_float(value: float, *, places: int = 12) -> bytes:
    """Frame a float through a fixed decimal rendering.

    The Q values are real numbers, so they cannot be framed as exact integers.
    Rendering them at a fixed precision makes the root reproducible across
    platforms instead of depending on repr shortest-round-trip behaviour.
    """
    if not isinstance(value, float) or not math.isfinite(value):
        raise AssertionError("%s: %r is not a finite float"
                             % (STOP_FIELD_SCHEMA, value))
    return _typed("%.*f" % (places, value))


def _is_hex64(value: Any) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value))


def exact_positive_library(value: Any, *, what: str) -> int:
    """`source_library` must be an exact positive integer.

    log1p of a non-positive or non-integral library would either be undefined or
    silently wrong, and the frozen confirmation reader already refuses `lib <= 0`.
    """
    if isinstance(value, bool):
        raise AssertionError("%s: %s is a bool" % (STOP_LIBRARY, what))
    if isinstance(value, int):
        number = int(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text or not text.isdigit():
            raise AssertionError("%s: %s is %r" % (STOP_LIBRARY, what, value))
        number = int(text)
    else:
        raise AssertionError("%s: %s is %r" % (STOP_LIBRARY, what, type(value)))
    if number <= 0:
        raise AssertionError("%s: %s is %d" % (STOP_LIBRARY, what, number))
    return number


# --- the exact recovered formulas ------------------------------------------

def cell_q_depth(source_library: Any, *, what: str = "source_library") -> float:
    """`log1p(source_library)` for one cell."""
    return math.log1p(exact_positive_library(source_library, what=what))


def cell_q_detect(projected_row: Sequence[Any], *,
                  scalar_features: int = SCALAR_FEATURES,
                  what: str = "projected row") -> float:
    """`count_nonzero(A) / 35076` for one cell, over the full projection.

    The width is required, not inferred. A row of the 41,238-address space or of
    the 28,061 SCORING subset would give a detection rate over the wrong
    denominator and would not be Q_DETECT.
    """
    if len(projected_row) != int(scalar_features):
        raise AssertionError(
            "%s: %s is %d wide, but Q_DETECT is defined on %d scalar-measured "
            "addresses" % (STOP_PROJECTION_WIDTH, what, len(projected_row),
                           int(scalar_features)))
    nonzero = 0
    for position, value in enumerate(projected_row):
        if isinstance(value, bool) or not isinstance(value, int):
            if not (isinstance(value, float) and math.isfinite(value)
                    and float(value).is_integer()):
                raise AssertionError("%s: %s position %d is %r"
                                     % (STOP_COUNTS, what, position, value))
        numeric = int(value)
        if numeric < 0:
            raise AssertionError("%s: %s position %d is %r"
                                 % (STOP_COUNTS, what, position, value))
        if numeric != 0:
            nonzero += 1
    return nonzero / float(scalar_features)


def cell_q_detect_from_nonzero_count(nonzero_count: Any, *,
                                     scalar_features: int = SCALAR_FEATURES
                                     ) -> float:
    """The same quantity from a precomputed non-zero count.

    Offered because holding 35,076 values per cell for 638,150 cells is not
    practical at production scale. The count must still lie in 0..35,076, so a
    count taken over the wrong universe cannot pass unnoticed.
    """
    if isinstance(nonzero_count, bool) or not isinstance(nonzero_count, int):
        raise AssertionError("%s: nonzero count is %r"
                             % (STOP_COUNTS, nonzero_count))
    if not (0 <= int(nonzero_count) <= int(scalar_features)):
        raise AssertionError(
            "%s: a non-zero count of %d is outside 0..%d, so it was not taken "
            "over the %d-address projection"
            % (STOP_PROJECTION_WIDTH, int(nonzero_count), int(scalar_features),
               int(scalar_features)))
    return int(nonzero_count) / float(scalar_features)


def donor_summaries(cell_values: Sequence[tuple[float, float]], *,
                    donor_id: str) -> dict[str, float]:
    """`Q_DEPTH` and `Q_DETECT` as arithmetic means over the donor's cells."""
    if not cell_values:
        raise AssertionError("%s: %s" % (STOP_NO_CELLS, donor_id))
    depths = [float(depth) for depth, _ in cell_values]
    detects = [float(detect) for _, detect in cell_values]
    for name, series in (("Q_DEPTH", depths), ("Q_DETECT", detects)):
        for value in series:
            if not math.isfinite(value):
                raise AssertionError("%s: %s for %s is %r"
                                     % (STOP_FIELD_SCHEMA, name, donor_id, value))
    return {"Q_DEPTH": math.fsum(depths) / len(depths),
            "Q_DETECT": math.fsum(detects) / len(detects)}


# --- the predicate ---------------------------------------------------------

def technical_complete(summary: Mapping[str, Any], *, donor_id: str) -> bool:
    """Threshold-free definedness. No cutoff, of any kind, appears here.

    TRUE iff the required exact technical summaries are computable and finite and
    Q_DETECT lies in its lawful range [0, 1]. The range check is a definedness
    check, not a quality threshold: a detection rate outside [0, 1] is not a low
    value, it is an impossible one, and it means the quantity was computed over
    the wrong universe.
    """
    depth = summary.get("Q_DEPTH")
    detect = summary.get("Q_DETECT")
    if not isinstance(depth, float) or not math.isfinite(depth):
        return False
    if not isinstance(detect, float) or not math.isfinite(detect):
        return False
    if not (0.0 <= detect <= 1.0):
        return False
    return True


def assert_predicate_is_threshold_free() -> bool:
    """Guard the owner decision against later drift.

    The realistic failure is not a deliberate rewrite but a plausible quality
    floor added afterwards. V18 freezes no depth or detection threshold, so any
    such floor would have to be invented after the data are in hand, and
    eligibility would quietly become a post-hoc donor filter.
    """
    if SEMANTICS != "THRESHOLD_FREE_DEFINEDNESS_AND_COMPUTABILITY":
        raise AssertionError("%s: semantics changed to %r"
                             % (STOP_THRESHOLD, SEMANTICS))
    if AUTHORITY_FAILURE_IS_A_GLOBAL_STOP is not True:
        raise AssertionError(
            "%s: an authority failure must be a global STOP, never a False"
            % STOP_THRESHOLD)
    source = technical_complete.__doc__ or ""
    for banned in (">= 0.0 and", "minimum", "cutoff", "at least 80"):
        if banned in source.lower() and "threshold" not in source.lower():
            raise AssertionError("%s: the predicate documents %r"
                                 % (STOP_THRESHOLD, banned))
    if tuple(FORBIDDEN_CUTOFFS)[:2] != ("Q_DEPTH_MINIMUM", "Q_DETECT_MINIMUM"):
        raise AssertionError("%s: the forbidden-cutoff list was edited"
                             % STOP_THRESHOLD)
    return True


def assert_substrate_lawful(*, substrate: Mapping[str, Any]) -> bool:
    """The predicate is evaluated ONLY on a lawfully authenticated substrate.

    Every parent identity must be present and well formed. If any is missing this
    raises, rather than proceeding and recording donors as incomplete, because a
    provenance failure must never be laundered into an eligibility outcome.
    """
    required = ("population_closure_root_sha256",
                "logical_row_authority_root_sha256",
                "physical_read_plan_root_sha256",
                "feature_authority_root_sha256",
                "projection_root_sha256")
    for field in required:
        value = substrate.get(field)
        if not _is_hex64(value):
            raise AssertionError(
                "%s: %s is %r; technical completeness may only be evaluated on a "
                "lawfully authenticated substrate, and a missing parent identity "
                "is a global STOP rather than a donor-level False"
                % (STOP_SUBSTRATE, field, value))
    return True


def _build_rows_from_values(
        *,
        cells_by_donor: Mapping[str, Sequence[tuple[Any, Any]]],
        candidate_donors: Sequence[str] | None = None,
        scalar_features: int = SCALAR_FEATURES,
) -> tuple[dict[str, Any], ...]:
    """Compute the summaries and the predicate for every candidate donor.

    `cells_by_donor` maps a donor to a sequence of `(source_library,
    projected_nonzero_count)` pairs, one per authenticated cell.
    """
    donors = sorted(map(str, cells_by_donor), key=lambda d: d.encode("utf-8"))
    if candidate_donors is not None:
        expected = {str(d) for d in candidate_donors}
        if set(donors) != expected:
            raise AssertionError(
                "%s: substrate-only %s, candidate-only %s"
                % (STOP_DONOR_SET, sorted(set(donors) - expected),
                   sorted(expected - set(donors))))

    rows = []
    for donor in donors:
        pairs = []
        for index, (library, nonzero) in enumerate(cells_by_donor[donor]):
            depth = cell_q_depth(library,
                                 what="source_library for %s cell %d" % (donor, index))
            detect = cell_q_detect_from_nonzero_count(
                nonzero, scalar_features=scalar_features)
            pairs.append((depth, detect))
        summary = donor_summaries(pairs, donor_id=donor)
        rows.append({
            "donor_id": donor,
            "cells": len(pairs),
            "Q_DEPTH": summary["Q_DEPTH"],
            "Q_DETECT": summary["Q_DETECT"],
            "technical_complete": technical_complete(summary, donor_id=donor),
        })
    return tuple(rows)


def completeness_root(rows: Sequence[Mapping[str, Any]]) -> str:
    """Digest over the per-donor summaries and the boolean result."""
    parts = [_typed(DOMAIN_TAG), _typed(SCHEMA), _typed(NAMESPACE),
             _typed(SEMANTICS), _typed(Q_DEPTH_CELL_FORMULA),
             _typed(Q_DETECT_CELL_FORMULA), _typed(Q_DONOR_REDUCTION),
             _typed(int(SCALAR_FEATURES)), _typed(len(rows))]
    for row in rows:
        parts.append(_typed([str(row["donor_id"]), int(row["cells"])]))
        # Binding the consumed cell identities is what ties a summary to a
        # population. Without them two different populations of the same size
        # could share a root.
        parts.append(_typed([str(cell) for cell in row.get("cell_ids", ())]))
        parts.append(_typed_float(float(row["Q_DEPTH"])))
        parts.append(_typed_float(float(row["Q_DETECT"])))
        parts.append(_typed(bool(row["technical_complete"])))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def package_root(members: Mapping[str, bytes]) -> str:
    names = sorted(members)
    parts = [_typed(DOMAIN_TAG), _typed("PACKAGE"), _typed(len(names))]
    for name in names:
        parts.append(_typed([name,
                             hashlib.sha256(bytes(members[name])).hexdigest()]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def parent_contract_root(*, substrate: Mapping[str, Any],
                         derivation_code_sha256: str) -> str:
    """One root over the B2 and B1 parents plus the deriving code identity."""
    fields = ("population_closure_root_sha256",
              "logical_row_authority_root_sha256",
              "physical_read_plan_root_sha256",
              "feature_authority_root_sha256",
              "projection_root_sha256")
    parts = [_typed(DOMAIN_TAG), _typed("PARENT_CONTRACT"),
             _typed(len(fields) + 1)]
    for field in fields:
        parts.append(_typed([field, str(substrate[field])]))
    if not _is_hex64(derivation_code_sha256):
        raise AssertionError("%s: derivation_code_sha256 is not a hex sha256"
                             % STOP_FIELD_SCHEMA)
    parts.append(_typed(["derivation_code_sha256", str(derivation_code_sha256)]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def _build_authority_from_values(
        outdir: Path | str,
        *,
        cells_by_donor: Mapping[str, Sequence[tuple[Any, Any]]],
        substrate: Mapping[str, Any],
        derivation_code_sha256: str,
        candidate_donors: Sequence[str],
        scalar_features: int = SCALAR_FEATURES,
) -> dict[str, Any]:
    """Evaluate technical completeness over a lawful substrate and package it."""
    out = Path(outdir)
    if out.exists() and any(out.iterdir()):
        raise AssertionError("%s: output directory must be absent or empty: %s"
                             % (STOP_PACKAGE_MEMBER, out))
    assert_predicate_is_threshold_free()
    assert_substrate_lawful(substrate=substrate)

    rows = _build_rows_from_values(cells_by_donor=cells_by_donor,
                      candidate_donors=candidate_donors,
                      scalar_features=scalar_features)
    return _write_package(out, rows=rows, substrate=substrate,
                          derivation_code_sha256=derivation_code_sha256,
                          scalar_features=scalar_features)


def _write_package(
        out: Path,
        *,
        rows,
        substrate,
        derivation_code_sha256: str,
        scalar_features: int = SCALAR_FEATURES,
):
    """Write the package members and both roots. Shared by both entrypoints."""
    root = completeness_root(rows)
    parent_root = parent_contract_root(
        substrate=substrate, derivation_code_sha256=derivation_code_sha256)

    registry = io.StringIO()
    writer = csv.writer(registry, lineterminator="\n")
    writer.writerow(["donor_id", "cells", "Q_DEPTH", "Q_DETECT",
                     "technical_complete"])
    for row in rows:
        writer.writerow([row["donor_id"], int(row["cells"]),
                         "%.12f" % float(row["Q_DEPTH"]),
                         "%.12f" % float(row["Q_DETECT"]),
                         bool(row["technical_complete"])])
    registry_bytes = registry.getvalue().encode("utf-8")

    meta = {
        "schema": SCHEMA,
        "namespace": NAMESPACE,
        "finalized": True,
        "semantics": SEMANTICS,
        "q_depth_cell_formula": Q_DEPTH_CELL_FORMULA,
        "q_detect_cell_formula": Q_DETECT_CELL_FORMULA,
        "q_detect_universe": Q_DETECT_UNIVERSE,
        "q_donor_reduction": Q_DONOR_REDUCTION,
        "formula_provenance": FORMULA_PROVENANCE,
        "scalar_features": int(scalar_features),
        "forbidden_cutoffs": list(FORBIDDEN_CUTOFFS),
        "thresholds_introduced": False,
        "authority_failure_is_a_global_stop": AUTHORITY_FAILURE_IS_A_GLOBAL_STOP,
        "donor_count": len(rows),
        "technically_complete_donors": sum(1 for r in rows
                                           if r["technical_complete"]),
        "completeness_root_sha256": root,
        "parent_contract_root_sha256": parent_root,
        "substrate": {field: str(substrate[field]) for field in sorted(substrate)},
        "derivation_code_sha256": str(derivation_code_sha256),
        "derivation_code_byte_semantics": "GIT_BLOB_BYTES__NOT_WORKTREE_BYTES",
        "pathology_values_read": False,
        "production_run_status": "SYNTHETIC_ONLY__PRODUCTION_B2_NOT_RUN",
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

    return {"completeness_root_sha256": root, "package_root_sha256": pkg_root,
            "parent_contract_root_sha256": parent_root,
            "donor_count": len(rows),
            "technically_complete_donors": meta["technically_complete_donors"],
            "real_execution_ready": False}


def load_authority(
        outdir: Path | str,
        *,
        expected_package_root_sha256: str,
        expected_completeness_root_sha256: str,
        expected_parent_contract_root_sha256: str,
) -> dict[str, Any]:
    """Read the authority back, binding its parents externally."""
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

    meta = json.loads(captured[METADATA].decode("utf-8"))
    if meta.get("schema") != SCHEMA or meta.get("finalized") is not True:
        raise AssertionError("%s: metadata schema or finalized flag invalid"
                             % STOP_FIELD_SCHEMA)
    if meta.get("semantics") != SEMANTICS:
        raise AssertionError("%s: stored semantics are %r"
                             % (STOP_THRESHOLD, meta.get("semantics")))
    if meta.get("thresholds_introduced") is not False:
        raise AssertionError("%s: the stored authority declares a threshold"
                             % STOP_THRESHOLD)
    if meta.get("q_detect_cell_formula") != Q_DETECT_CELL_FORMULA:
        raise AssertionError("%s: stored Q_DETECT formula is %r"
                             % (STOP_FIELD_SCHEMA,
                                meta.get("q_detect_cell_formula")))
    if meta.get("q_depth_cell_formula") != Q_DEPTH_CELL_FORMULA:
        raise AssertionError("%s: stored Q_DEPTH formula is %r"
                             % (STOP_FIELD_SCHEMA,
                                meta.get("q_depth_cell_formula")))
    if str(meta.get("completeness_root_sha256")) != str(
            expected_completeness_root_sha256):
        raise AssertionError("%s: stored completeness root is %r, expected %r"
                             % (STOP_ROOT_MISMATCH,
                                meta.get("completeness_root_sha256"),
                                expected_completeness_root_sha256))
    recomputed_parent = parent_contract_root(
        substrate=meta["substrate"],
        derivation_code_sha256=meta["derivation_code_sha256"])
    if str(meta.get("parent_contract_root_sha256")) != recomputed_parent:
        raise AssertionError(
            "%s: the stored parent contract root %r does not match the root "
            "recomputed from the stored parents %s"
            % (STOP_PARENT_IDENTITY, meta.get("parent_contract_root_sha256"),
               recomputed_parent))
    if recomputed_parent != str(expected_parent_contract_root_sha256):
        raise AssertionError("%s: parent contract root is %s, externally expected %s"
                             % (STOP_PARENT_IDENTITY, recomputed_parent,
                                expected_parent_contract_root_sha256))
    if meta.get("real_execution_ready") is not False:
        raise AssertionError("%s: real_execution_ready must be False"
                             % STOP_FIELD_SCHEMA)

    columns, records = _rows(captured[REGISTRY])
    for required in ("donor_id", "cells", "Q_DEPTH", "Q_DETECT",
                     "technical_complete"):
        if required not in columns:
            raise AssertionError("%s: registry lacks %r"
                                 % (STOP_FIELD_SCHEMA, required))
    return {"metadata": meta, "records": records,
            "completeness_root_sha256": meta["completeness_root_sha256"],
            "package_root_sha256": pkg_root,
            "parent_contract_root_sha256": recomputed_parent}


def _rows(raw: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    text = bytes(raw).decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return tuple(reader.fieldnames or ()), [dict(row) for row in reader]


# ---------------------------------------------------------------------------
# Derivation from AUTHENTICATED parents.
#
# The earlier entrypoint took `cells_by_donor` as a sequence of
# `(source_library, projected_nonzero_count)` tuples while `substrate` was only
# a collection of parent-root STRINGS. Genuine roots could therefore accompany
# entirely invented values: the roots named the parents without binding the
# numbers. An external review classified that as a hard STOP, correctly.
#
# The production path below derives both summaries from authenticated objects.
# `source_library` comes out of the B2 logical row authority, whose root is
# externally bound, and the projected non-zero count comes out of the counts
# payload bytes that the logical row's own `counts_sha256` authenticates, mapped
# through the B1 projection whose root is also externally bound.
# ---------------------------------------------------------------------------

def refuse_detached_values(**kwargs: Any) -> None:
    """Explicit refusal so the removed parameters cannot quietly return."""
    offending = sorted(k for k in kwargs
                       if k in ("cells_by_donor", "substrate",
                                "projected_nonzero_count", "values"))
    if offending:
        raise AssertionError(
            "%s: %s may not be supplied to the production path; Q_DEPTH and "
            "Q_DETECT are derived from authenticated parents, and parent-root "
            "strings name the parents without binding the values"
            % (STOP_DETACHED_VALUES, ", ".join(offending)))


def projection_root(projection: Mapping[str, Any]) -> str:
    """Digest of the B1 projection actually used to compute Q_DETECT.

    Q_DETECT is a rate over the projected address set, so which addresses are in
    that set is decision-bearing and must be bound rather than passed as a free
    list.
    """
    positions = list(projection["positions"])
    if len(positions) != len(set(positions)):
        raise AssertionError("%s: the projection repeats a position"
                             % STOP_PROJECTION_POSITIONS)
    feature_root = str(projection["feature_authority_root_sha256"])
    if not _is_hex64(feature_root):
        raise AssertionError("%s: the projection names feature root %r"
                             % (STOP_PROJECTION_POSITIONS, feature_root))
    parts = [_typed(DOMAIN_TAG), _typed("B1_PROJECTION"), _typed(feature_root),
             _typed(len(positions))]
    for position in sorted(int(p) for p in positions):
        parts.append(_typed(int(position)))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def derive_rows_from_authenticated_parents(
        *,
        logical: Mapping[str, Any],
        expected_logical_root_sha256: str,
        expected_closure_root_sha256: str,
        counts_payload_bytes_by_path: Mapping[str, bytes],
        projection: Mapping[str, Any],
        expected_projection_root_sha256: str,
        address_space_size: int = 41_238,
        expected_projection_positions: int | None = None,
        scalar_features: int = SCALAR_FEATURES,
) -> tuple[dict[str, Any], ...]:
    """Compute the donor summaries from authenticated bytes and objects.

    Nothing decision-bearing arrives as a caller value. Every `source_library`
    is read off the authenticated logical row, and every non-zero count is
    computed from the counts payload that row's own digest authenticates.
    """
    import t0_v20_row_count_authority_v1 as rc

    # Bind the B2 parents before reading anything through them.
    stored_logical = logical.get("logical_row_authority_root_sha256")
    stored_closure = logical.get("population_closure_root_sha256")
    if not _is_hex64(stored_closure):
        raise AssertionError("%s: the logical authority carries no closure root"
                             % STOP_CLOSURE_ROOT)
    if str(stored_closure) != str(expected_closure_root_sha256):
        raise AssertionError("%s: closure root is %s, externally expected %s"
                             % (STOP_CLOSURE_ROOT, stored_closure,
                                expected_closure_root_sha256))
    recomputed_logical = rc._logical_root(
        logical["rows"], logical["feature_authority_root_sha256"], stored_closure)
    if str(stored_logical) != recomputed_logical:
        raise AssertionError(
            "%s: the logical authority stores %s but its contents recompute to %s"
            % (STOP_LOGICAL_ROOT, stored_logical, recomputed_logical))
    if recomputed_logical != str(expected_logical_root_sha256):
        raise AssertionError("%s: logical root is %s, externally expected %s"
                             % (STOP_LOGICAL_ROOT, recomputed_logical,
                                expected_logical_root_sha256))

    # Bind the B1 projection.
    actual_projection = projection_root(projection)
    if actual_projection != str(expected_projection_root_sha256):
        raise AssertionError("%s: projection root is %s, externally expected %s"
                             % (STOP_PROJECTION_ROOT, actual_projection,
                                expected_projection_root_sha256))
    if str(projection["feature_authority_root_sha256"]) != str(
            logical["feature_authority_root_sha256"]):
        raise AssertionError(
            "%s: the projection names feature root %s but the logical authority "
            "names %s" % (STOP_PROJECTION_ROOT,
                          projection["feature_authority_root_sha256"],
                          logical["feature_authority_root_sha256"]))
    positions = sorted(int(p) for p in projection["positions"])
    for position in positions:
        if not (0 <= position < int(address_space_size)):
            raise AssertionError(
                "%s: position %d is outside the %d-address space"
                % (STOP_PROJECTION_POSITIONS, position, int(address_space_size)))
    if expected_projection_positions is not None:
        if len(positions) != int(expected_projection_positions):
            raise AssertionError(
                "%s: the projection holds %d positions, expected %d"
                % (STOP_PROJECTION_POSITIONS, len(positions),
                   int(expected_projection_positions)))
    projected = set(positions)

    per_donor: dict[str, list[tuple[float, float]]] = {}
    cells_per_donor: dict[str, list[str]] = {}
    for index, row in enumerate(logical["rows"]):
        path = str(row["counts_path"])
        if path not in counts_payload_bytes_by_path:
            raise AssertionError(
                "%s: no counts payload supplied for %s, which logical index %d "
                "binds" % (STOP_SUBSTRATE, path, index))
        # Authenticate the payload against the digest the logical row binds,
        # parse only those bytes, and select the block-local row.
        dense = rc.verify_block_row_from_authenticated_payload(
            logical=logical, logical_index=index,
            counts_payload_bytes=counts_payload_bytes_by_path[path],
            address_space_size=int(address_space_size))

        nonzero = sum(1 for position in projected if dense[position] != 0)
        depth = cell_q_depth(row["source_library"],
                             what="source_library for logical index %d" % index)
        detect = cell_q_detect_from_nonzero_count(
            nonzero, scalar_features=scalar_features)
        donor = str(row["donor_id"])
        per_donor.setdefault(donor, []).append((depth, detect))
        cells_per_donor.setdefault(donor, []).append(str(row["canonical_cell_id"]))

    rows = []
    for donor in sorted(per_donor, key=lambda d: d.encode("utf-8")):
        summary = donor_summaries(per_donor[donor], donor_id=donor)
        rows.append({
            "donor_id": donor,
            "cells": len(per_donor[donor]),
            "cell_ids": tuple(cells_per_donor[donor]),
            "Q_DEPTH": summary["Q_DEPTH"],
            "Q_DETECT": summary["Q_DETECT"],
            "technical_complete": technical_complete(summary, donor_id=donor),
        })
    return tuple(rows)


def build_production_authority(
        outdir: Path | str,
        *,
        logical: Mapping[str, Any],
        expected_logical_root_sha256: str,
        expected_closure_root_sha256: str,
        counts_payload_bytes_by_path: Mapping[str, bytes],
        projection: Mapping[str, Any],
        expected_projection_root_sha256: str,
        derivation_code_sha256: str,
        candidate_donors: Sequence[str],
        address_space_size: int = 41_238,
        expected_projection_positions: int | None = None,
        scalar_features: int = SCALAR_FEATURES,
) -> dict[str, Any]:
    """The only lawful production path: authenticated parents in, package out.

    There is no `cells_by_donor` and no bare `substrate` mapping, so a forged
    value pair cannot enter however genuine the accompanying root strings are.
    """
    out = Path(outdir)
    if out.exists() and any(out.iterdir()):
        raise AssertionError("%s: output directory must be absent or empty: %s"
                             % (STOP_PACKAGE_MEMBER, out))
    assert_predicate_is_threshold_free()

    rows = derive_rows_from_authenticated_parents(
        logical=logical,
        expected_logical_root_sha256=expected_logical_root_sha256,
        expected_closure_root_sha256=expected_closure_root_sha256,
        counts_payload_bytes_by_path=counts_payload_bytes_by_path,
        projection=projection,
        expected_projection_root_sha256=expected_projection_root_sha256,
        address_space_size=address_space_size,
        expected_projection_positions=expected_projection_positions,
        scalar_features=scalar_features)

    donors = {str(row["donor_id"]) for row in rows}
    expected = {str(d) for d in candidate_donors}
    if donors != expected:
        raise AssertionError("%s: derived-only %s, candidate-only %s"
                             % (STOP_DONOR_SET, sorted(donors - expected),
                                sorted(expected - donors)))

    substrate = {
        "population_closure_root_sha256": str(expected_closure_root_sha256),
        "logical_row_authority_root_sha256": str(expected_logical_root_sha256),
        "physical_read_plan_root_sha256": str(
            logical.get("physical_read_plan_root_sha256")
            or expected_logical_root_sha256),
        "feature_authority_root_sha256": str(
            logical["feature_authority_root_sha256"]),
        "projection_root_sha256": str(expected_projection_root_sha256),
    }
    assert_substrate_lawful(substrate=substrate)

    summary = _write_package(out, rows=rows, substrate=substrate,
                             derivation_code_sha256=derivation_code_sha256,
                             scalar_features=scalar_features)
    summary["cells_consumed"] = sum(int(row["cells"]) for row in rows)
    summary["derivation"] = "FROM_AUTHENTICATED_B2_LOGICAL_AND_B1_PROJECTION"
    return summary
