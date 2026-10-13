from __future__ import annotations

import hashlib
import math
from itertools import combinations
from typing import Mapping

import numpy as np

import td_relational_successor_estimability_v1 as E
import td_relational_successor_gate_v1 as V1

RelationalGateError = V1.RelationalGateError
ScaleResult = V1.ScaleResult
RelationalProfileReceipt = V1.RelationalProfileReceipt
RareIncrementScaleResult = V1.RareIncrementScaleResult
RareIncrementReceipt = V1.RareIncrementReceipt

SCALE_GRID = V1.SCALE_GRID
SCALE_LABELS = V1.SCALE_LABELS
MIN_NEIGHBORS = V1.MIN_NEIGHBORS
MIN_SOURCE_DONORS = V1.MIN_SOURCE_DONORS
MIN_RESOLVED_RELATIONS_PER_DONOR = V1.MIN_RESOLVED_RELATIONS_PER_DONOR
TRIPLET_CAP_PER_STRATUM = V1.TRIPLET_CAP_PER_STRATUM
N_NULL = V1.N_NULL
NULL_P95_INDEX = V1.NULL_P95_INDEX

_AUTHORITY = {
    "target_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _as_square(name: str, value, n: int | None = None) -> np.ndarray:
    arr = np.asarray(value, dtype=float)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        raise RelationalGateError(f"{name} must be square")
    if n is not None and arr.shape != (n, n):
        raise RelationalGateError(f"{name} shape mismatch")
    return arr


def _validate_inputs(*, z_distances, x_distances, y_distances, donor_ids, operator_ids, global_rows,
                     focal_mask, neighbor_pool_mask, null_y_identity_maps):
    donors = np.asarray(donor_ids, dtype=object)
    operators = np.asarray(operator_ids, dtype=object)
    rows = np.asarray(global_rows)
    focal = np.asarray(focal_mask, dtype=bool)
    pool = np.asarray(neighbor_pool_mask, dtype=bool)
    n = len(donors)
    if n == 0:
        raise RelationalGateError("empty profile")
    if any(len(v) != n for v in (operators, rows, focal, pool)):
        raise RelationalGateError("cell-vector length mismatch")
    if len(set(rows.tolist())) != n:
        raise RelationalGateError("global_rows must be unique")
    if np.any(focal & ~pool):
        raise RelationalGateError("focal anchors must belong to the lawful neighbor pool")
    z = _as_square("z_distances", z_distances, n)
    x = _as_square("x_distances", x_distances, n)
    y = _as_square("y_distances", y_distances, n)
    maps = np.asarray(null_y_identity_maps)
    if maps.shape != (N_NULL, n):
        raise RelationalGateError(f"exactly {N_NULL} null Y identity maps are required")
    target = np.arange(n)
    for q, mapping in enumerate(maps):
        if not np.issubdtype(mapping.dtype, np.integer):
            raise RelationalGateError(f"null map {q} must contain integer indices")
        if not np.array_equal(np.sort(mapping), target):
            raise RelationalGateError(f"null map {q} must be a full identity permutation")
        if np.any(donors[mapping] != donors) or np.any(operators[mapping] != operators):
            raise RelationalGateError(f"null map {q} violates donor/operator matched reassignment")
    return z, x, y, donors, operators, rows.astype(np.int64), focal, pool, maps.astype(np.int64)


def _triplet_digest(source: str, panel_id: str, donor: str, operator: str,
                    rows: tuple[int, int, int]) -> bytes:
    a, b, c = rows
    preimage = (
        f"TD316V2|triplet|source|{source}|panel|{panel_id}|donor|{donor}|operator|{operator}|"
        f"anchor|{a}|j|{b}|k|{c}"
    )
    return hashlib.sha256(preimage.encode("utf-8")).digest()


def _sample_triplets(triplets, *, source: str, panel_id: str, donor: str,
                     operator: str, global_rows: np.ndarray):
    triplets = list(triplets)
    if len(triplets) <= TRIPLET_CAP_PER_STRATUM:
        return triplets
    ranked = []
    for triplet in triplets:
        i, j, k = triplet
        row_triplet = (int(global_rows[i]), int(global_rows[j]), int(global_rows[k]))
        ranked.append((_triplet_digest(source, panel_id, str(donor), str(operator), row_triplet),
                       row_triplet, triplet))
    ranked.sort(key=lambda item: (item[0], item[1]))
    return [triplet for _, _, triplet in ranked[:TRIPLET_CAP_PER_STRATUM]]


def _order_sign(a: float, b: float) -> int | None:
    if not np.isfinite(a) or not np.isfinite(b) or a == b:
        return None
    return 1 if a > b else -1


def _median(values) -> float:
    return float(np.median(np.asarray(list(values), dtype=float)))


def _build_scale_population(*, source, panel_id, scale, z, x, donors, operators, rows,
                            focal, pool, min_focal_anchors_per_donor):
    """Build the frozen Z-selected, X-resolved triplet population before hash capping."""
    num, den = scale
    donor_order = tuple(dict.fromkeys(str(d) for d in donors.tolist()))
    neighbor_counts_by_donor = {donor: [] for donor in donor_order}
    by_donor: dict[str, list[tuple[int, int, int]]] = {donor: [] for donor in donor_order}
    seen: list[tuple[str, str]] = []
    for donor, operator in zip(donors.tolist(), operators.tolist()):
        key = (str(donor), str(operator))
        if key not in seen:
            seen.append(key)
    donor_s = donors.astype(str)
    operator_s = operators.astype(str)
    for donor, operator in seen:
        stratum = np.where((donor_s == donor) & (operator_s == operator) & pool)[0]
        anchors = [int(i) for i in stratum if focal[i]]
        all_triplets: list[tuple[int, int, int]] = []
        for i in anchors:
            candidates = []
            for j in stratum:
                if j == i:
                    continue
                dz = z[i, j]
                if np.isfinite(dz):
                    candidates.append((float(dz), int(rows[j]), int(j)))
            candidates.sort(key=lambda value: (value[0], value[1]))
            m = len(candidates)
            k = math.ceil(m * num / den) if m else 0
            neighbor_counts_by_donor[donor].append(k)
            if k < MIN_NEIGHBORS:
                continue
            selected = [j for _, _, j in candidates[:k]]
            for j, kidx in combinations(selected, 2):
                # Frozen mechanics: X measurability/non-tie defines the base triplet
                # population before deterministic bounded sampling. Y remains outcome-side.
                if _order_sign(x[i, j], x[i, kidx]) is None:
                    continue
                if rows[j] <= rows[kidx]:
                    all_triplets.append((i, j, kidx))
                else:
                    all_triplets.append((i, kidx, j))
        sampled = _sample_triplets(
            all_triplets,
            source=source,
            panel_id=panel_id,
            donor=donor,
            operator=operator,
            global_rows=rows,
        )
        by_donor[donor].extend(sampled)
    estimability = E.assess_relational_stratum_estimability(
        neighbor_counts_by_donor=neighbor_counts_by_donor,
        min_neighbors=MIN_NEIGHBORS,
        min_recurring_donors=MIN_SOURCE_DONORS,
        min_estimable_focal_cells_per_donor=min_focal_anchors_per_donor,
    )
    eligible = set(estimability.eligible_donors)
    by_donor = {donor: triplets for donor, triplets in by_donor.items() if donor in eligible}
    return estimability, by_donor, sum(len(value) for value in by_donor.values())


def _donor_observed(triplets, x, y):
    resolved = 0
    agree = 0
    for i, j, k in triplets:
        qx = _order_sign(x[i, j], x[i, k])
        if qx is None:
            raise RelationalGateError("internal invariant violated: sampled triplet is not X-resolved")
        qy = _order_sign(y[i, j], y[i, k])
        if qy is None:
            continue
        resolved += 1
        agree += int(qx == qy)
    return (float(agree / resolved) if resolved >= MIN_RESOLVED_RELATIONS_PER_DONOR else None, resolved)


def _donor_null(triplets, x, y, mapping):
    resolved = 0
    agree = 0
    for i, j, k in triplets:
        qx = _order_sign(x[i, j], x[i, k])
        if qx is None:
            raise RelationalGateError("internal invariant violated: sampled triplet is not X-resolved")
        mi, mj, mk = int(mapping[i]), int(mapping[j]), int(mapping[k])
        qy = _order_sign(y[mi, mj], y[mi, mk])
        if qy is None:
            continue
        resolved += 1
        agree += int(qx == qy)
    return float(agree / resolved) if resolved >= MIN_RESOLVED_RELATIONS_PER_DONOR else None


def evaluate_relational_profile(*, source: str, panel_id: str, profile_id: str,
                                z_distances, x_distances, y_distances, donor_ids,
                                operator_ids, global_rows, focal_mask, neighbor_pool_mask,
                                null_y_identity_maps, min_focal_anchors_per_donor: int) -> RelationalProfileReceipt:
    if not all(isinstance(value, str) and value for value in (source, panel_id, profile_id)):
        raise RelationalGateError("source, panel_id and profile_id must be nonempty strings")
    if (not isinstance(min_focal_anchors_per_donor, int) or
            isinstance(min_focal_anchors_per_donor, bool) or min_focal_anchors_per_donor < 1):
        raise RelationalGateError("min_focal_anchors_per_donor must be a positive integer")
    z, x, y, donors, operators, rows, focal, pool, maps = _validate_inputs(
        z_distances=z_distances,
        x_distances=x_distances,
        y_distances=y_distances,
        donor_ids=donor_ids,
        operator_ids=operator_ids,
        global_rows=global_rows,
        focal_mask=focal_mask,
        neighbor_pool_mask=neighbor_pool_mask,
        null_y_identity_maps=null_y_identity_maps,
    )
    work = {}
    for scale in SCALE_GRID:
        label = f"{scale[0]}/{scale[1]}"
        estimability, by_donor, n_triplets = _build_scale_population(
            source=source,
            panel_id=panel_id,
            scale=scale,
            z=z,
            x=x,
            donors=donors,
            operators=operators,
            rows=rows,
            focal=focal,
            pool=pool,
            min_focal_anchors_per_donor=min_focal_anchors_per_donor,
        )
        observed = {}
        resolved = {}
        for donor, triplets in by_donor.items():
            value, n_resolved = _donor_observed(triplets, x, y)
            resolved[donor] = n_resolved
            if value is not None:
                observed[donor] = value
        observed_statistic = _median(observed.values()) if len(observed) >= MIN_SOURCE_DONORS else None
        null_statistics = []
        for q in range(N_NULL):
            values = []
            for donor, triplets in by_donor.items():
                value = _donor_null(triplets, x, y, maps[q])
                if value is not None:
                    values.append(value)
            null_statistics.append(_median(values) if len(values) >= MIN_SOURCE_DONORS else None)
        work[label] = {
            "scale": scale,
            "estimability": estimability,
            "n_triplets": n_triplets,
            "observed": observed,
            "resolved": resolved,
            "observed_statistic": observed_statistic,
            "null_statistics": null_statistics,
        }

    family = [
        label for label, record in work.items()
        if record["observed_statistic"] is not None and all(value is not None for value in record["null_statistics"])
    ]
    family_p95 = None
    if family:
        maxima = []
        for q in range(N_NULL):
            maxima.append(max(float(work[label]["null_statistics"][q]) for label in family))
        maxima.sort()
        family_p95 = float(maxima[NULL_P95_INDEX])

    results = {}
    for label in SCALE_LABELS:
        record = work[label]
        num, den = record["scale"]
        if record["observed_statistic"] is None:
            status, reason = "NOT_ESTIMABLE", "INSUFFICIENT_SUPPORT"
        elif not all(value is not None for value in record["null_statistics"]):
            status, reason = "NOT_ESTIMABLE", "INCOMPLETE_MATCHED_NULL_SUPPORT"
        else:
            assert family_p95 is not None
            status = "PASS" if (record["observed_statistic"] > 0.5 and record["observed_statistic"] > family_p95) else "FAIL"
            reason = "RELATION_ESTABLISHED" if status == "PASS" else "RELATION_NOT_ESTABLISHED"
        results[label] = ScaleResult(
            scale_label=label,
            numerator=num,
            denominator=den,
            status=status,
            reason=reason,
            observed_statistic=record["observed_statistic"],
            family_null_p95=family_p95 if label in family else None,
            n_observed_donors=len(record["observed"]),
            observed_donor_agreements=dict(record["observed"]),
            observed_resolved_relations=dict(record["resolved"]),
            null_source_statistics=tuple(record["null_statistics"]),
            n_sampled_triplets=record["n_triplets"],
            eligible_donors=tuple(record["estimability"].eligible_donors),
        )

    estimable = [result for result in results.values() if result.status in {"PASS", "FAIL"}]
    characterization = []
    if any(result.status == "PASS" and (result.numerator / result.denominator) <= 1 / 3 for result in results.values()):
        characterization.append("FINE_SCALE_RELATION_ESTABLISHED")
    if results["1/2"].status == "PASS":
        characterization.append("MESOSCALE_RELATION_ESTABLISHED")
    if any(result.status == "PASS" for result in estimable) and any(result.status == "FAIL" for result in estimable):
        characterization.append("SCALE_DEPENDENT_RELATION_ESTABLISHED")
    if estimable and all(result.status == "FAIL" for result in estimable):
        characterization.append("NO_RELATION_ESTABLISHED")
    if not estimable:
        characterization.append("NOT_ESTIMABLE")

    return RelationalProfileReceipt(
        source=source,
        panel_id=panel_id,
        profile_id=profile_id,
        scale_results=results,
        characterization=tuple(characterization),
        focal_anchor_count=int(focal.sum()),
        failure_scope="SCALE_SPECIFIC_RELATIONAL_CLAIM_ONLY",
        authority=dict(_AUTHORITY),
    )


def adjudicate_rare_increment(program: RelationalProfileReceipt,
                              controls: Mapping[str, RelationalProfileReceipt]) -> RareIncrementReceipt:
    return V1.adjudicate_rare_increment(program, controls)
