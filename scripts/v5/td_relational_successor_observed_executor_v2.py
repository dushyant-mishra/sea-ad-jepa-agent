from __future__ import annotations

import math
from itertools import combinations

import numpy as np

import td_relational_successor_estimability_v1 as E
import td_relational_successor_gate_v2 as G
import td_relational_successor_observed_executor_v1 as V1

ObservedExecutorError = V1.ObservedExecutorError
PreparedObservedRelationalContext = V1.PreparedObservedRelationalContext
prepare_observed_relational_context = V1.prepare_observed_relational_context


def _distance(context: PreparedObservedRelationalContext, view: str, i: int, j: int) -> float:
    return V1._distance(context.store, context.cell_keys, view, i, j)


def _donor_observed(triplets, context: PreparedObservedRelationalContext):
    resolved = 0
    agree = 0
    for i, j, k in triplets:
        qx = G._order_sign(_distance(context, "x", i, j), _distance(context, "x", i, k))
        if qx is None:
            raise ObservedExecutorError("internal invariant violated: sampled triplet is not X-resolved")
        qy = G._order_sign(_distance(context, "y", i, j), _distance(context, "y", i, k))
        if qy is None:
            continue
        resolved += 1
        agree += int(qx == qy)
    return (float(agree / resolved) if resolved >= G.MIN_RESOLVED_RELATIONS_PER_DONOR else None, resolved)


def _donor_null(triplets, context: PreparedObservedRelationalContext, mapping):
    resolved = 0
    agree = 0
    for i, j, k in triplets:
        qx = G._order_sign(_distance(context, "x", i, j), _distance(context, "x", i, k))
        if qx is None:
            raise ObservedExecutorError("internal invariant violated: sampled triplet is not X-resolved")
        mi, mj, mk = int(mapping[i]), int(mapping[j]), int(mapping[k])
        qy = G._order_sign(_distance(context, "y", mi, mj), _distance(context, "y", mi, mk))
        if qy is None:
            continue
        resolved += 1
        agree += int(qx == qy)
    return float(agree / resolved) if resolved >= G.MIN_RESOLVED_RELATIONS_PER_DONOR else None


def evaluate_prepared_relational_profile(
    context: PreparedObservedRelationalContext,
    *,
    profile_id: str,
    focal_mask,
    neighbor_pool_mask,
    min_focal_anchors_per_donor: int,
) -> G.RelationalProfileReceipt:
    if not isinstance(context, PreparedObservedRelationalContext):
        raise ObservedExecutorError("context must be a PreparedObservedRelationalContext")
    if not isinstance(profile_id, str) or not profile_id:
        raise ObservedExecutorError("profile_id must be a nonempty string")
    if (not isinstance(min_focal_anchors_per_donor, int) or
            isinstance(min_focal_anchors_per_donor, bool) or min_focal_anchors_per_donor < 1):
        raise ObservedExecutorError("min_focal_anchors_per_donor must be a positive integer")
    focal, pool = V1._validate_profile_masks(
        focal_mask=focal_mask,
        neighbor_pool_mask=neighbor_pool_mask,
        n=context.n_cells,
    )
    donors = context.donors
    rows = context.rows
    donor_order = tuple(dict.fromkeys(str(value) for value in donors.tolist()))
    work = {}

    for scale in G.SCALE_GRID:
        label = f"{scale[0]}/{scale[1]}"
        num, den = scale
        neighbor_counts = {donor: [] for donor in donor_order}
        by_donor = {donor: [] for donor in donor_order}
        for (donor, operator), record in context.store.items():
            anchors = [int(i) for i in record.indices.tolist() if focal[i]]
            all_triplets = []
            for i in anchors:
                candidates = []
                for j_raw in record.indices.tolist():
                    j = int(j_raw)
                    if j == i or not pool[j]:
                        continue
                    dz = _distance(context, "z", i, j)
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
                    # X measurability/non-tie is part of the frozen base population,
                    # therefore it is applied before the deterministic cap.
                    qx = G._order_sign(_distance(context, "x", i, j), _distance(context, "x", i, kidx))
                    if qx is None:
                        continue
                    if rows[j] <= rows[kidx]:
                        all_triplets.append((i, j, kidx))
                    else:
                        all_triplets.append((i, kidx, j))
            by_donor[donor].extend(G._sample_triplets(
                all_triplets,
                source=context.source,
                panel_id=context.panel_id,
                donor=donor,
                operator=operator,
                global_rows=rows,
            ))

        estimability = E.assess_relational_stratum_estimability(
            neighbor_counts_by_donor=neighbor_counts,
            min_neighbors=G.MIN_NEIGHBORS,
            min_recurring_donors=G.MIN_SOURCE_DONORS,
            min_estimable_focal_cells_per_donor=min_focal_anchors_per_donor,
        )
        eligible = set(estimability.eligible_donors)
        by_donor = {donor: triplets for donor, triplets in by_donor.items() if donor in eligible}
        observed = {}
        resolved = {}
        for donor, triplets in by_donor.items():
            value, n_resolved = _donor_observed(triplets, context)
            resolved[donor] = n_resolved
            if value is not None:
                observed[donor] = value
        observed_statistic = V1._median(observed.values()) if len(observed) >= G.MIN_SOURCE_DONORS else None
        null_statistics = []
        for q in range(G.N_NULL):
            values = []
            for donor, triplets in by_donor.items():
                value = _donor_null(triplets, context, context.null_maps[q])
                if value is not None:
                    values.append(value)
            null_statistics.append(V1._median(values) if len(values) >= G.MIN_SOURCE_DONORS else None)
        work[label] = {
            "scale": scale,
            "estimability": estimability,
            "n_triplets": sum(len(value) for value in by_donor.values()),
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
        for q in range(G.N_NULL):
            maxima.append(max(float(work[label]["null_statistics"][q]) for label in family))
        maxima.sort()
        family_p95 = float(maxima[G.NULL_P95_INDEX])

    results = {}
    for label in G.SCALE_LABELS:
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

    return G.RelationalProfileReceipt(
        source=context.source,
        panel_id=context.panel_id,
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
    z_feature_ids,
    x_feature_ids,
    y_feature_ids,
    donor_ids,
    operator_ids,
    global_rows,
    source_library,
    detected_genes,
    focal_mask,
    neighbor_pool_mask,
    min_focal_anchors_per_donor: int,
) -> G.RelationalProfileReceipt:
    context = prepare_observed_relational_context(
        source=source,
        panel_id=panel_id,
        z_values=z_values,
        x_values=x_values,
        y_values=y_values,
        z_measured=z_measured,
        x_measured=x_measured,
        y_measured=y_measured,
        z_feature_ids=z_feature_ids,
        x_feature_ids=x_feature_ids,
        y_feature_ids=y_feature_ids,
        donor_ids=donor_ids,
        operator_ids=operator_ids,
        global_rows=global_rows,
        source_library=source_library,
        detected_genes=detected_genes,
    )
    return evaluate_prepared_relational_profile(
        context,
        profile_id=profile_id,
        focal_mask=focal_mask,
        neighbor_pool_mask=neighbor_pool_mask,
        min_focal_anchors_per_donor=min_focal_anchors_per_donor,
    )
