"""Rights-ladder RNA observation producer with a query-excluded depth (fixture scope).

Closes the *semantic* half of G7 R2 at the shared source -> CaseBundle / G7 edge.
A cell's physical library total contains every molecule, including those of genes
withheld by evidence rights, so exposing it (or any offset, scale or per-cell copy
of it) lets withheld evidence reach visible bytes. Here the only depth a consumer
sees is

    depth = whole-row raw total - every MEASURED_SCALAR count whose right lies
            outside the BASE (most restrictive) level of the frozen ladder.

That depth is a function of base-visible molecules, collision mass inside base
rights and off-ledger mass only. So changing withheld counts (with the physical
total moving by the same amount, as it does) cannot change a visible byte at any
level, and the depth is identical at every level of the ladder: evidence rights
change evidence, never depth (V3.1.1 E3).

Consequences consumers must respect:
- above the base level a visible non-base count is NOT part of the depth, so
  physical-total checks such as ``count <= library_size`` or ``sum(counts) <=
  library_size`` hold at the base level (the student view) but not in general;
- withheld mass that cannot be removed exactly (a collision-unresolved address
  outside the base rights) or a depth of zero is NOT_ESTIMABLE, never guessed;
- refusals are outcomes too: whether a call is refused, and with which class and
  message, depends only on structure, base-visible counts and total minus stored
  counts, never on withheld counts. This holds inside the declared integer domain
  (every integer, the physical total included, below 2**53); a total pushed out of
  that domain by withheld molecules alone is refused before any semantics.

Preconditions this module cannot check from its own inputs (a source producer must
attest them): every source feature carrying molecules of an outside-base address's
gene is mapped to that address (an off-ledger alias would leave withheld molecules
in the depth), and the cell roster was not selected with statistics that include
withheld genes (depositor QC on whole-transcriptome totals makes inclusion weakly
dependent on them).

This module does NOT authenticate where counts came from, that one record is one
physical nucleus, or that donor IDs denote distinct donors (G7 R1/R1D and the
issuer half of R2). ``atom_id`` is a coordinate identity a consumer can recompute,
not a physical measurement identity. Every input is rebuilt from exact built-ins
before any comparison, and only that private snapshot is validated and emitted.
"""
from __future__ import annotations

from scripts.v5.td_unified.canonical_v1 import canonical_sha256 as _canonical_sha256

MEASURED_SCALAR = "MEASURED_SCALAR"
STRUCTURALLY_UNMEASURED = "STRUCTURALLY_UNMEASURED"
MEASURED_COLLISION_UNRESOLVED = "MEASURED_COLLISION_UNRESOLVED"
WITHHELD_BY_EVIDENCE_RIGHTS = "WITHHELD_BY_EVIDENCE_RIGHTS"
_OPERATOR_STATES = frozenset({MEASURED_SCALAR, STRUCTURALLY_UNMEASURED, MEASURED_COLLISION_UNRESOLVED})
_CELL_KEYS = frozenset({"cell_id", "donor_id", "source_id", "operator_id", "library_total", "counts"})
_LEVEL_KEYS = frozenset({"level_id", "evidence_rights"})
_MAX_DEPTH = 16
# Physical counts and totals are far below this; it also keeps every integer exact
# in float64 and inside every canonical encoder's integer domain.
_MAX_INT = 2 ** 53
DEPTH_RULE = "WHOLE_ROW_RAW_TOTAL_MINUS_MEASURED_COUNTS_OUTSIDE_BASE_RIGHTS"


class QExcludedObservationError(ValueError):
    """Malformed, ambiguous or non-exact producer input."""


class QExcludedDepthNotEstimable(QExcludedObservationError):
    """Withheld mass cannot be removed exactly from the depth."""


def _snapshot(value, depth=0):
    """Fresh copy built only from exact JSON built-ins; nothing caller-defined runs."""
    if depth > _MAX_DEPTH:
        raise QExcludedObservationError("input nesting exceeds the producer bound")
    kind = type(value)
    if value is None:
        return value
    if kind is str:
        if any(0xD800 <= ord(ch) <= 0xDFFF for ch in value):
            raise QExcludedObservationError("lone surrogate is not canonical text")
        return value
    if kind is int:
        if not -_MAX_INT < value < _MAX_INT:
            raise QExcludedObservationError("integer outside the physical count domain")
        return value
    if kind is list:
        return [_snapshot(item, depth + 1) for item in value]
    if kind is dict:
        out = {}
        for key, item in dict.items(value):
            if type(key) is not str:
                raise QExcludedObservationError("mapping keys must be exact built-in strings")
            out[key] = _snapshot(item, depth + 1)
        return out
    raise QExcludedObservationError("input must contain only exact dict/list/str/int/None values")


def _token(value, label):
    if (type(value) is not str or not value or value != value.strip()
            or any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value)):
        raise QExcludedObservationError(f"{label} must be a nonempty trimmed string without control characters")
    return value


def canonical_sha256(value):
    try:
        return _canonical_sha256(value)
    except Exception as exc:  # noqa: BLE001 - the snapshot domain should make this unreachable
        raise QExcludedObservationError("producer output is not canonically serializable") from exc


def _ladder(raw):
    if type(raw) is not list or not raw:
        raise QExcludedObservationError("the frozen rights ladder must be a nonempty list")
    levels, seen_ids, previous = [], set(), None
    for level in raw:
        if type(level) is not dict or set(level) != _LEVEL_KEYS:
            raise QExcludedObservationError("ladder level fields are not exact")
        level_id = _token(level["level_id"], "level_id")
        if level_id in seen_ids:
            raise QExcludedObservationError("duplicate ladder level_id")
        seen_ids.add(level_id)
        rights = level["evidence_rights"]
        if type(rights) is not list or not rights:
            raise QExcludedObservationError("each level needs a nonempty evidence_rights list")
        names = [_token(r, "evidence right") for r in rights]
        if len(set(names)) != len(names):
            raise QExcludedObservationError("duplicate evidence right within a level")
        current = frozenset(names)
        if previous is not None and not previous < current:
            raise QExcludedObservationError("ladder levels must be strictly nested and increasing")
        previous = current
        levels.append((level_id, names, current))  # frozen order: consumers pin these bytes
    return levels


def produce_rights_ladder_observations(*, cells, address_rights, operator_states, ladder):
    """Return per-level observation rows whose only depth is query-excluded.

    ``cells``: list of {cell_id, donor_id, source_id, operator_id, library_total,
    counts}; ``counts`` maps address -> raw integer count and may omit measured
    zeros. ``address_rights``: address -> evidence right (the full universe).
    ``operator_states``: operator -> address -> one of the three physical states.
    ``ladder``: ordered levels {level_id, evidence_rights}, strictly nested.
    """
    snap = _snapshot({"cells": cells, "address_rights": address_rights,
                      "operator_states": operator_states, "ladder": ladder})
    levels = _ladder(snap["ladder"])
    base_rights, all_rights = levels[0][2], levels[-1][2]

    rights = snap["address_rights"]
    if type(rights) is not dict or not rights:
        raise QExcludedObservationError("address_rights must be a nonempty mapping")
    for address, right in rights.items():
        _token(address, "address_id")
        if _token(right, "evidence right") not in all_rights:
            raise QExcludedObservationError("address right is not part of the frozen ladder")
    universe = sorted(rights)
    outside_base = frozenset(a for a in universe if rights[a] not in base_rights)

    states = snap["operator_states"]
    if type(states) is not dict or not states:
        raise QExcludedObservationError("operator_states must be a nonempty mapping")
    for operator, by_address in states.items():
        _token(operator, "operator_id")
        if type(by_address) is not dict or set(by_address) != set(universe):
            raise QExcludedObservationError("each operator state map must cover the address universe exactly")
        for state in by_address.values():
            if type(state) is not str or state not in _OPERATOR_STATES:
                raise QExcludedObservationError("unknown physical measurement state")

    raw_cells = snap["cells"]
    if type(raw_cells) is not list or not raw_cells:
        raise QExcludedObservationError("cells must be a nonempty list")
    prepared, seen_cells = [], set()
    for cell in raw_cells:
        if type(cell) is not dict or set(cell) != _CELL_KEYS:
            raise QExcludedObservationError("cell fields are not exact")
        ident = {k: _token(cell[k], k) for k in ("cell_id", "donor_id", "source_id", "operator_id")}
        if ident["cell_id"] in seen_cells:
            raise QExcludedObservationError("duplicate cell_id")
        seen_cells.add(ident["cell_id"])
        if ident["operator_id"] not in states:
            raise QExcludedObservationError("cell names an operator without a frozen state map")
        op_states = states[ident["operator_id"]]
        counts = cell["counts"]
        if type(counts) is not dict:
            raise QExcludedObservationError("counts must be a mapping")
        for address, count in counts.items():
            if address not in rights:
                raise QExcludedObservationError("count for an address outside the universe")
            if op_states[address] != MEASURED_SCALAR:
                raise QExcludedObservationError("count supplied for an address the operator did not measure as a scalar")
            if type(count) is not int or count < 0:
                raise QExcludedObservationError("counts must be nonnegative exact integers")
        total = cell["library_total"]
        # Refusals obey noninterference too: compare only quantities that withheld
        # counts cannot move (total - stored counts, and the depth below). A bare
        # ``total < 1`` refused an empty droplet as malformed but a cell holding only
        # withheld molecules as NOT_ESTIMABLE, revealing that they exist (#481 A4).
        if type(total) is not int or total < sum(counts.values()):
            raise QExcludedObservationError("library_total must be an exact integer covering every stored count")
        for address in outside_base:
            if op_states[address] == MEASURED_COLLISION_UNRESOLVED:
                raise QExcludedDepthNotEstimable(
                    "collision-unresolved mass outside the base rights cannot be removed from the depth")
        depth = total - sum(counts.get(a, 0) for a in outside_base if op_states[a] == MEASURED_SCALAR)
        if depth < 1:
            raise QExcludedDepthNotEstimable("no query-excluded depth remains for this cell")
        prepared.append((ident, op_states, counts, depth))
    prepared.sort(key=lambda item: item[0]["cell_id"])

    out_levels = []
    for level_id, level_rights, visible in levels:
        rows = []
        for ident, op_states, counts, depth in prepared:
            for address in universe:
                physical = op_states[address]
                if physical == MEASURED_SCALAR and rights[address] in visible:
                    state, count, library = MEASURED_SCALAR, counts.get(address, 0), depth
                elif physical == MEASURED_SCALAR:
                    state, count, library = WITHHELD_BY_EVIDENCE_RIGHTS, None, None
                else:
                    state, count, library = physical, None, None
                rows.append({
                    "atom_id": canonical_sha256(["JEPA_Q_EXCLUDED_ATOM_V1", ident["source_id"],
                                                 ident["operator_id"], ident["cell_id"], address]),
                    "cell_id": ident["cell_id"], "donor_id": ident["donor_id"],
                    "source_id": ident["source_id"], "operator_id": ident["operator_id"],
                    "address_id": address, "right": rights[address],
                    "state": state, "count": count, "library_size": library,
                })
        out_levels.append({
            "level_id": level_id,
            "evidence_rights": level_rights,
            "rows": rows,
            "rows_sha256": canonical_sha256(rows),
            "casebundle_observations": [
                {"cell_id": r["cell_id"], "donor_id": r["donor_id"], "source_id": r["source_id"],
                 "operator_id": r["operator_id"], "address_id": r["address_id"], "state": r["state"],
                 "count": r["count"], "library_size": r["library_size"], "evidence_right": r["right"]}
                for r in rows],
            "g7_atoms": [
                {"atom_id": r["atom_id"], "source": r["source_id"], "donor_id": r["donor_id"],
                 "right": r["right"], "state": r["state"], "count": r["count"],
                 "library_size": r["library_size"]}
                for r in rows],
        })
    return {
        "schema": "JEPA_TD_Q_EXCLUDED_OBSERVATION_LADDER_V1",
        "authority_scope": "FIXTURE_ONLY",
        "depth_rule": DEPTH_RULE,
        "levels": out_levels,
        "source_authenticated": False,
        "physical_measurement_identity_authenticated": False,
        "donor_identity_authenticated": False,
        "authority_effect": "NONE",
    }
