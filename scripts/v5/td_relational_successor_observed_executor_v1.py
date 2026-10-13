from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from itertools import combinations
from typing import Sequence

import numpy as np

import td_relational_successor_estimability_v1 as E
import td_relational_successor_gate_v1 as G
import td_relational_successor_geometry_v1 as M


class ObservedExecutorError(ValueError):
    pass


@dataclass(frozen=True)
class _StratumGeometry:
    indices: np.ndarray
    positions: dict[int, int]
    z: np.ndarray
    x: np.ndarray
    y: np.ndarray


def _require_view(name: str, values, measured, feature_ids: Sequence[str], n: int | None = None):
    arr = np.asarray(values, dtype=float)
    support = np.asarray(measured, dtype=bool)
    ids = tuple(feature_ids)
    if arr.ndim != 2 or support.shape != arr.shape:
        raise ObservedExecutorError(f"{name} values/measured must be same-shape 2D arrays")
    if arr.shape[1] != M.VIEW_FEATURE_COUNT or len(ids) != M.VIEW_FEATURE_COUNT:
        raise ObservedExecutorError(f"{name} must contain exactly 512 features")
    if n is not None and arr.shape[0] != n:
        raise ObservedExecutorError(f"{name} cell count mismatch")
    if any(not isinstance(v, str) or not v for v in ids) or len(set(ids)) != len(ids):
        raise ObservedExecutorError(f"{name} feature IDs must be unique nonempty strings")
    if np.any(~np.isfinite(arr[support])):
        raise ObservedExecutorError(f"{name} measured values must be finite")
    return arr, support, ids


def _validate_vectors(*, donor_ids, operator_ids, global_rows, source_library, detected_genes,
                      focal_mask, neighbor_pool_mask, n: int):
    donors = np.asarray(donor_ids, dtype=object)
    operators = np.asarray(operator_ids, dtype=object)
    rows = np.asarray(global_rows)
    library = np.asarray(source_library, dtype=float)
    detected = np.asarray(detected_genes)
    focal = np.asarray(focal_mask, dtype=bool)
    pool = np.asarray(neighbor_pool_mask, dtype=bool)
    if any(len(v) != n for v in (donors, operators, rows, library, detected, focal, pool)):
        raise ObservedExecutorError("cell-vector length mismatch")
    if len(set(rows.tolist())) != n:
        raise ObservedExecutorError("global_rows must be unique")
    if np.any(focal & ~pool):
        raise ObservedExecutorError("focal anchors must belong to neighbor pool")
    if any(not isinstance(v, str) or not v for v in donors.tolist()):
        raise ObservedExecutorError("donor IDs must be nonempty strings")
    if any(not isinstance(v, str) or not v for v in operators.tolist()):
        raise ObservedExecutorError("operator IDs must be nonempty strings")
    if np.any(~np.isfinite(library)) or np.any(library < 0):
        raise ObservedExecutorError("source_library must be finite and nonnegative")
    if not np.issubdtype(detected.dtype, np.integer) or np.any(detected < 0):
        raise ObservedExecutorError("detected_genes must be nonnegative integers")
    return donors, operators, rows.astype(np.int64), library, detected.astype(np.int64), focal, pool


def _stratum_keys(donors: np.ndarray, operators: np.ndarray) -> tuple[tuple[str, str], ...]:
    seen: list[tuple[str, str]] = []
    for donor, operator in zip(donors.tolist(), operators.tolist()):
        key = (str(donor), str(operator))
        if key not in seen:
            seen.append(key)
    return tuple(seen)


def _build_geometry_store(*, z_values, x_values, y_values, z_measured, x_measured, y_measured,
                          z_ids, x_ids, y_ids, z_pairs, x_pairs, y_pairs, donors, operators):
    store: dict[tuple[str, str], _StratumGeometry] = {}
    donor_s = donors.astype(str)
    operator_s = operators.astype(str)
    for key in _stratum_keys(donors, operators):
        donor, operator = key
        idx = np.where((donor_s == donor) & (operator_s == operator))[0]
        z = M.build_concordance_distance_matrix(
            z_values[idx], z_measured[idx], z_ids, z_pairs,
            min_informative=M.MIN_INFORMATIVE_COORDINATES,
        )
        x = M.build_concordance_distance_matrix(
            x_values[idx], x_measured[idx], x_ids, x_pairs,
            min_informative=M.MIN_INFORMATIVE_COORDINATES,
        )
        y = M.build_concordance_distance_matrix(
            y_values[idx], y_measured[idx], y_ids, y_pairs,
            min_informative=M.MIN_INFORMATIVE_COORDINATES,
        )
        store[key] = _StratumGeometry(
            indices=idx.astype(np.int64),
            positions={int(global_index): local for local, global_index in enumerate(idx.tolist())},
            z=z, x=x, y=y,
        )
    return store


def _distance(store, cell_keys, view: str, i: int, j: int) -> float:
    key_i = cell_keys[i]
    if cell_keys[j] != key_i:
        return float("nan")
    record = store[key_i]
    matrix = getattr(record, view)
    return float(matrix[record.positions[i], record.positions[j]])


def _triplet_hash(source: str, panel_id: str, donor: str, operator: str, rows: tuple[int, int, int]) -> bytes:
    a, b, c = rows
    preimage = (
        f"TD316|triplet|source|{source}|panel|{panel_id}|donor|{donor}|operator|{operator}|"
        f"anchor|{a}|j|{b}|k|{c}"
    )
    return hashlib.sha256(preimage.encode("utf-8")).digest()


def _sample_triplets(triplets, *, source: str, panel_id: str, donor: str, operator: str, rows: np.ndarray):
    if len(triplets) <= G.TRIPLET_CAP_PER_STRATUM:
        return list(triplets)
    ranked = []
    for i, j, k in triplets:
        rr = (int(rows[i]), int(rows[j]), int(rows[k]))
        ranked.append((_triplet_hash(source, panel_id, donor, operator, rr), rr, (i, j, k)))
    ranked.sort(key=lambda item: (item[0], item[1]))
    return [triplet for _, _, triplet in ranked[:G.TRIPLET_CAP_PER_STRATUM]]


def _order_sign(a: float, b: float) -> int | None:
    if not np.isfinite(a) or not np.isfinite(b) or a == b:
        return None
    return 1 if a > b else -1


def _median(values) -> float:
    return float(np.median(np.asarray(list(values), dtype=float)))


def _donor_observed(triplets, store, cell_keys):
    resolved = 0
    agree = 0
    for i, j, k in triplets:
        qx = _order_sign(_distance(store, cell_keys, "x", i, j), _distance(store, cell_keys, "x", i, k))
        if qx is None:
            continue
        qy = _order_sign(_distance(store, cell_keys, "y", i, j), _distance(store, cell_keys, "y", i, k))
        if qy is None:
            continue
        resolved += 1
        agree += int(qx == qy)
    return (float(agree / resolved) if resolved >= G.MIN_RESOLVED_RELATIONS_PER_DONOR else None, resolved)


def _donor_null(triplets, store, cell_keys, mapping):
    resolved = 0
    agree = 0
    for i, j, k in triplets:
        qx = _order_sign(_distance(store, cell_keys, "x", i, j), _distance(store, cell_keys, "x", i, k))
        if qx is None:
            continue
        mi, mj, mk = int(mapping[i]), int(mapping[j]), int(mapping[k])
        qy = _order_sign(_distance(store, cell_keys, "y", mi, mj), _distance(store, cell_keys, "y", mi, mk))
        if qy is None:
            continue
        resolved += 1
        agree += int(qx == qy)
    return float(agree / resolved) if resolved >= G.MIN_RESOLVED_RELATIONS_PER_DONOR else None


def evaluate_observed_relational_profile(
    *,
    source: str,
    panel_id: str,
    profile_id: str,
    z_values,
    x_values,
    y_values,
    z_measured,
    x_measured,
    y_measured,
    z_feature_ids: Sequence[str],
    x_feature_ids: Sequence[str],
    y_feature_ids: Sequence[str],
    donor_ids,
    operator_ids,
    global_rows,
    source_library,
    detected_genes,
    focal_mask,
    neighbor_pool_mask,
    min_focal_anchors_per_donor: int,
) -> G.RelationalProfileReceipt:
    if not all(isinstance(v, str) and v for v in (source, panel_id, profile_id)):
        raise ObservedExecutorError("source, panel_id and profile_id must be nonempty strings")
    if not isinstance(min_focal_anchors_per_donor, int) or isinstance(min_focal_anchors_per_donor, bool) or min_focal_anchors_per_donor < 1:
        raise ObservedExecutorError("min_focal_anchors_per_donor must be a positive integer")

    z, zm, z_ids = _require_view("Z", z_values, z_measured, z_feature_ids)
    n = z.shape[0]
    x, xm, x_ids = _require_view("X", x_values, x_measured, x_feature_ids, n)
    y, ym, y_ids = _require_view("Y", y_values, y_measured, y_feature_ids, n)
    if set(z_ids) & set(x_ids) or set(z_ids) & set(y_ids) or set(x_ids) & set(y_ids):
        raise ObservedExecutorError("Z/X/Y feature views must be mutually disjoint")
    donors, operators, rows, library, detected, focal, pool = _validate_vectors(
        donor_ids=donor_ids,
        operator_ids=operator_ids,
        global_rows=global_rows,
        source_library=source_library,
        detected_genes=detected_genes,
        focal_mask=focal_mask,
        neighbor_pool_mask=neighbor_pool_mask,
        n=n,
    )

    z_pairs = M.select_pair_coordinates(z_ids, panel_id=panel_id, view_id="Z")
    x_pairs = M.select_pair_coordinates(x_ids, panel_id=panel_id, view_id="X")
    y_pairs = M.select_pair_coordinates(y_ids, panel_id=panel_id, view_id="Y")
    store = _build_geometry_store(
        z_values=z, x_values=x, y_values=y,
        z_measured=zm, x_measured=xm, y_measured=ym,
        z_ids=z_ids, x_ids=x_ids, y_ids=y_ids,
        z_pairs=z_pairs, x_pairs=x_pairs, y_pairs=y_pairs,
        donors=donors, operators=operators,
    )
    null_maps, _ = M.build_td37a_matched_y_null_maps(
        source=source,
        panel_id=panel_id,
        donor_ids=donors,
        operator_ids=operators,
        global_rows=rows,
        source_library=library,
        detected_genes=detected,
    )
    cell_keys = tuple((str(d), str(o)) for d, o in zip(donors.tolist(), operators.tolist()))

    work = {}
    donor_order = tuple(dict.fromkeys(str(v) for v in donors.tolist()))
    for scale in G.SCALE_GRID:
        label = f"{scale[0]}/{scale[1]}"
        num, den = scale
        neighbor_counts = {donor: [] for donor in donor_order}
        by_donor = {donor: [] for donor in donor_order}
        for (donor, operator), record in store.items():
            anchors = [int(i) for i in record.indices.tolist() if focal[i]]
            all_triplets = []
            for i in anchors:
                candidates = []
                for j in record.indices.tolist():
                    j = int(j)
                    if j == i or not pool[j]:
                        continue
                    dz = _distance(store, cell_keys, "z", i, j)
                    if np.isfinite(dz):
                        candidates.append((dz, int(rows[j]), j))
                candidates.sort(key=lambda item: (item[0], item[1]))
                m = len(candidates)
                k = math.ceil(m * num / den) if m else 0
                neighbor_counts[donor].append(k)
                if k < G.MIN_NEIGHBORS:
                    continue
                selected = [j for _, _, j in candidates[:k]]
                for j, kidx in combinations(selected, 2):
                    if rows[j] <= rows[kidx]:
                        all_triplets.append((i, j, kidx))
                    else:
                        all_triplets.append((i, kidx, j))
            by_donor[donor].extend(_sample_triplets(
                all_triplets,
                source=source,
                panel_id=panel_id,
                donor=donor,
                operator=operator,
                rows=rows,
            ))

        estim = E.assess_relational_stratum_estimability(
            neighbor_counts_by_donor=neighbor_counts,
            min_neighbors=G.MIN_NEIGHBORS,
            min_recurring_donors=G.MIN_SOURCE_DONORS,
            min_estimable_focal_cells_per_donor=min_focal_anchors_per_donor,
        )
        eligible = set(estim.eligible_donors)
        by_donor = {d: triplets for d, triplets in by_donor.items() if d in eligible}
        observed = {}
        resolved = {}
        for donor, triplets in by_donor.items():
            value, n_resolved = _donor_observed(triplets, store, cell_keys)
            resolved[donor] = n_resolved
            if value is not None:
                observed[donor] = value
        observed_statistic = _median(observed.values()) if len(observed) >= G.MIN_SOURCE_DONORS else None
        null_statistics = []
        for q in range(G.N_NULL):
            values = []
            for donor, triplets in by_donor.items():
                value = _donor_null(triplets, store, cell_keys, null_maps[q])
                if value is not None:
                    values.append(value)
            null_statistics.append(_median(values) if len(values) >= G.MIN_SOURCE_DONORS else None)
        work[label] = {
            "scale": scale,
            "estim": estim,
            "triplets": sum(len(v) for v in by_donor.values()),
            "observed": observed,
            "resolved": resolved,
            "observed_statistic": observed_statistic,
            "null_statistics": null_statistics,
        }

    family = [
        label for label, record in work.items()
        if record["observed_statistic"] is not None and all(v is not None for v in record["null_statistics"])
    ]
    family_p95 = None
    if family:
        maxima = []
        for q in range(G.N_NULL):
            maxima.append(max(float(work[label]["null_statistics"][q]) for label in family))
        maxima.sort()
        family_p95 = float(maxima[G.NULL_P95_INDEX])

    results = {}
    for label in G.SCALE_LABELS:
        record = work[label]
        num, den = record["scale"]
        if record["observed_statistic"] is None:
            status = "NOT_ESTIMABLE"
            reason = "INSUFFICIENT_SUPPORT"
        elif not all(v is not None for v in record["null_statistics"]):
            status = "NOT_ESTIMABLE"
            reason = "INCOMPLETE_MATCHED_NULL_SUPPORT"
        else:
            assert family_p95 is not None
            status = "PASS" if (record["observed_statistic"] > 0.5 and record["observed_statistic"] > family_p95) else "FAIL"
            reason = "RELATION_ESTABLISHED" if status == "PASS" else "RELATION_NOT_ESTABLISHED"
        results[label] = G.ScaleResult(
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
            n_sampled_triplets=record["triplets"],
            eligible_donors=tuple(record["estim"].eligible_donors),
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

    return G.RelationalProfileReceipt(
        source=source,
        panel_id=panel_id,
        profile_id=profile_id,
        scale_results=results,
        characterization=tuple(characterization),
        focal_anchor_count=int(focal.sum()),
        failure_scope="SCALE_SPECIFIC_RELATIONAL_CLAIM_ONLY",
        authority={
            "target_selection_authorized": False,
            "td60_authorized": False,
            "stage4_authorized": False,
            "training_authorized": False,
        },
    )
