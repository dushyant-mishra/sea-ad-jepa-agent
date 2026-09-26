"""G3: explicit, training-side attacker-fit objective over existing donor statistics.

Independent review module: does not modify the historical canonical attacker,
run protected masking outcomes, authorize JEPA training, or set a terminal
masking policy. Its fit should be integrated only after an exact frozen run
contract names the selected objective. Screening and held-out scoring are
distinct questions and MUST be declared separately.
"""
from __future__ import annotations

from collections import Counter
from typing import Mapping, Sequence
import numpy as np

OBJECTIVES = (
    "CURRENT_CELL_WEIGHTED",
    "PRODUCTION_OBJECTIVE_MATCHED",
    "SOURCE_DONOR_BALANCED_DIAGNOSTIC",
)
SCHEMA = "V26_G3_EXPLICIT_ATTACKER_FIT_OBJECTIVE_V1"


def donor_total_masses(
    *,
    donor_counts: Mapping[int, int],
    source_by_donor: Mapping[int, str],
    objective: str,
) -> dict[int, float]:
    """Mass summing to 1 over provided TRAIN donors; no heldout inference.

    CURRENT_CELL_WEIGHTED: mass n_d/N (historical fitting).
    PRODUCTION_OBJECTIVE_MATCHED: 1/D (frozen JEPA training estimand).
    SOURCE_DONOR_BALANCED_DIAGNOSTIC: 1/(S*D_source), an explicit
      source-balanced sensitivity diagnostic, NOT production training.
    The implied individual-cell weights equal donor_mass/n_d.
    """
    if objective not in OBJECTIVES:
        raise ValueError("G3 explicit fit objective required; no default/unknown label")
    if not donor_counts or set(donor_counts) != set(source_by_donor):
        raise ValueError("fit donor count/source roster must match exactly")
    keys = sorted(donor_counts)
    for key in keys:
        n = donor_counts[key]
        if (isinstance(key, (bool, np.bool_)) or not isinstance(key, (int, np.integer))
            or isinstance(n, (bool, np.bool_)) or not isinstance(n, (int, np.integer))
            or int(n) <= 0 or not isinstance(source_by_donor[key], str)
            or not source_by_donor[key].strip()):
            raise ValueError("invalid donor code, cell count or source identity")
    if objective == "CURRENT_CELL_WEIGHTED":
        total = sum(int(donor_counts[d]) for d in keys)
        result = {d: float(donor_counts[d]) / total for d in keys}
    elif objective == "PRODUCTION_OBJECTIVE_MATCHED":
        result = {d: 1.0 / len(keys) for d in keys}
    else:
        per_source = Counter(source_by_donor.values())
        result = {
            d: 1.0 / (len(per_source) * per_source[source_by_donor[d]])
            for d in keys
        }
    if not np.isfinite(list(result.values())).all() or abs(sum(result.values()) - 1.0) > 1e-12:
        raise ValueError("invalid scientific fit mass")
    return result


def fit_from_standardized_donor_components(
    *,
    components: Mapping[int, tuple[np.ndarray, np.ndarray, float]],
    donor_counts: Mapping[int, int],
    source_by_donor: Mapping[int, str],
    objective: str,
    alpha: float,
) -> np.ndarray:
    """Weighted ridge, holding per-donor standardization exactly fixed.

    The existing FULL104 attacker supplies each donor's (Xc'Xc, Xc'yc,
    yc'yc) after its original within-donor X standardization and Y centering.
    Applying mass/n_d to each sufficient-statistic triple changes FIT MASS
    only, not the feature standardization, screening or held-out score.
    Ridge regularization uses alpha * sum(w_i)=alpha since total mass=1;
    the target scale uses weighted within-donor Y variance.
    """
    if isinstance(alpha, (bool, np.bool_)) or not isinstance(alpha, (int, float, np.floating)):
        raise ValueError("ridge alpha must be an explicit nonnegative finite scalar")
    if not np.isfinite(alpha) or alpha < 0:
        raise ValueError("ridge alpha must be an explicit nonnegative finite scalar")
    mass = donor_total_masses(
        donor_counts=donor_counts, source_by_donor=source_by_donor, objective=objective,
    )
    if set(components) != set(mass):
        raise ValueError("no missing/extra or held-out donors in G3 sufficient statistics")
    n_feat = None
    gram = rhs = None
    rss = 0.0
    for donor in sorted(mass):
        g, r, yss = components[donor]
        g, r = np.asarray(g, dtype=np.float64), np.asarray(r, dtype=np.float64)
        if n_feat is None:
            n_feat = len(r)
            if n_feat < 1:
                raise ValueError("at least one visible feature is required")
            gram = np.zeros((n_feat, n_feat), dtype=np.float64)
            rhs = np.zeros(n_feat, dtype=np.float64)
        if g.shape != (n_feat, n_feat) or r.shape != (n_feat,):
            raise ValueError("donor standardized moments have inconsistent dimensions")
        if (not np.isfinite(g).all() or not np.isfinite(r).all() or
            not np.isfinite(yss) or yss < -1e-9):
            raise ValueError("invalid donor standardized moments")
        w_cell = mass[donor] / int(donor_counts[donor])
        gram += w_cell * g
        rhs += w_cell * r
        rss += w_cell * max(0.0, float(yss))
    assert gram is not None and rhs is not None
    scale = float(np.sqrt(rss))
    if scale <= 1e-12:
        return np.zeros(len(rhs), dtype=np.float64)
    # Never silently repair an indefinite Gram or substitute a pseudoinverse.
    if not np.allclose(gram, gram.T, atol=1e-8, rtol=1e-8):
        raise ValueError("G3 Gram is not symmetric")
    system = gram + float(alpha) * np.eye(len(rhs), dtype=np.float64)
    return np.linalg.solve(system, rhs / scale)
