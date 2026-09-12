#!/usr/bin/env python3
"""The nuisance-only (lambda -> infinity) LOO comparator for V20's discovery fit.

V20 published a 17-point ridge CV curve whose minimum sits at the grid boundary,
`CV MSE = 1.882992` at exponent +2.0. What was never computed is the value that
curve is descending toward: the loss when the expression contribution is
identically zero. Without it there is no way to say whether the fitted model beats
predicting nothing.

This computes exactly that, changing one thing and nothing else.

Why no expression data is required. In `fit_t0_target`'s CV loop the held-out
quantity is

    yte = (y[~tr] - Zte @ by) / ysd

and both `by` and `ysd` come from `_fit_nuisance` via `lstsq(train_z, train_y)` --
outcome and nuisance only. Verified empirically: `by` and `ysd` are bit-identical
across three unrelated expression matrices. Setting the expression contribution to
zero gives `pred = 0`, so

    L_inf = (1/n) * sum_i yte_i^2

which is a function of (AT8, age, sex) alone. The folds, the per-fold nuisance
refit, the training-fold response standardization and the squared-error loss are
all V20's, unchanged.

Access discipline. AT8 is read only through the frozen discovery-only loader
`t0_stage2b_discovery_at8_v1.load_role_numeric_at8`, which skips confirmation
rows before their values are touched, refuses any donor outside the frozen set,
and refuses unless the loaded set reproduces the frozen donor-set digest. The
endpoint vector is additionally required to reproduce V20's frozen
`endpoint_values_sha256`, which proves this read is the same one V20 performed.
Pathology magnitudes are never printed or written: the outputs are fold losses on
the standardized residual scale, which is the same class of quantity V20 already
published.

Interpretation is deliberately left to the reader. This module computes and
reports; it draws no conclusion and changes no authority.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
FROZEN = HERE / "t0_v20_frozen"
if str(FROZEN) not in sys.path:
    sys.path.insert(0, str(FROZEN))

import t0_stage2b_discovery_at8_v1 as stage2b  # noqa: E402
import t0_target_learner_v1 as learner  # noqa: E402

REPO = HERE.parent.parent
ROLE_REGISTRY = REPO / "outputs/t0_donor_role_20260909/T0_DONOR_ROLE_REGISTRY.csv"
AGE_SEX_REGISTRY = REPO / "outputs/t0_age_sex_20260908/T0_AGE_SEX_REGISTRY.csv"

FROZEN_PATHOLOGY_SHA = (
    "ebbe9bc0c623c663331425794bd8fb1b4c4f3657455cf55d806cc383ea6d8e3a")
FROZEN_DONOR_SET_SHA = (
    "4395fec74bcf7abf192d731db3c827fa25cfde1b5297db4203b041984a780d33")
FROZEN_ENDPOINT_VALUES_SHA = (
    "4cfb572798ab3f48c08aaa74a841e4cb92c01cfc69303f0f3a45c006a81c671a")
ENDPOINT_IDENTITY = "percent AT8 positive area_Grey matter"
V20_BEST_GRID_LOSS = 1.882992

STOP = "STOP_T0_V21_NULL_COMPARATOR_REFUSED"


def _fail(message: str) -> None:
    raise RuntimeError("%s: %s" % (STOP, message))


def donor_roles() -> tuple[set[str], set[str]]:
    rows = list(csv.DictReader(ROLE_REGISTRY.open(encoding="utf-8")))
    discovery = {r["donor_id"].strip() for r in rows
                 if r["role"].strip().upper() == "DISCOVERY"}
    confirmation = {r["donor_id"].strip() for r in rows
                    if r["role"].strip().upper() == "CONFIRMATION"}
    if len(discovery) != 28 or len(confirmation) != 18:
        _fail("expected 28 discovery and 18 confirmation donors; got %d and %d"
              % (len(discovery), len(confirmation)))
    return discovery, confirmation


def age_sex_for(donors: list[str]) -> tuple[np.ndarray, np.ndarray]:
    rows = {r["donor_id"].strip(): r
            for r in csv.DictReader(AGE_SEX_REGISTRY.open(encoding="utf-8"))}
    missing = [d for d in donors if d not in rows]
    if missing:
        _fail("age/sex authority lacks %s" % missing)
    age = np.array([float(rows[d]["age"]) for d in donors], dtype=np.float64)
    sex = np.array([1.0 if rows[d]["sex"].strip().lower() == "female" else 0.0
                    for d in donors], dtype=np.float64)
    return age, sex


def donor_id_field(source: Path, donors: set[str]) -> str:
    """The header column whose values are the donor identities we hold."""
    header = stage2b._split_csv_line(
        source.read_text(encoding="utf-8-sig").splitlines()[0])
    lines = source.read_text(encoding="utf-8-sig").splitlines()[1:]
    for index, name in enumerate(header):
        sample = {stage2b._split_csv_line(l)[index].strip()
                  for l in lines[:200] if l.strip()}
        if len(sample & donors) >= 5:
            return name
    _fail("no column of the source carries the frozen donor identities")


def nuisance_only_fold_losses(y: np.ndarray, age: np.ndarray,
                              sex: np.ndarray) -> np.ndarray:
    """V20's CV loop with the expression contribution set to zero.

    Folds, per-fold nuisance refit, held-out design construction and response
    standardization are copied from `fit_t0_target` without alteration. The only
    change is `pred = 0`, so each fold contributes `yte**2`.
    """
    n = len(y)
    losses = np.empty(n, dtype=np.float64)
    for i in range(n):
        tr = np.arange(n) != i
        ztr, center = learner.nuisance_design(age[tr], sex[tr])
        ac_te = age[~tr] - center
        zte = np.c_[np.ones(1), ac_te, ac_te * ac_te, sex[~tr]]
        by = np.linalg.lstsq(ztr, y[tr], rcond=None)[0]
        yr = y[tr] - ztr @ by
        ysd = float(np.std(yr, ddof=1))
        if not np.isfinite(ysd) or ysd <= 0:
            _fail("fold %d has a nonpositive residual response SD" % i)
        yte = (y[~tr] - zte @ by) / ysd
        losses[i] = float(yte[0]) ** 2
    return losses


def nuisance_only_via_frozen_helper(y, age, sex) -> np.ndarray:
    """Independent reproduction routed through the frozen `_fit_nuisance`.

    Uses a constant dummy expression matrix, which cannot affect `by` or `ysd`;
    that invariance is asserted here rather than assumed.
    """
    n = len(y)
    losses = np.empty(n, dtype=np.float64)
    dummy = np.ones((n, 3), dtype=np.float64)
    dummy[:, 1] = np.arange(n, dtype=np.float64)
    dummy[:, 2] = np.linspace(-1.0, 1.0, n)
    for i in range(n):
        tr = np.arange(n) != i
        ztr, center = learner.nuisance_design(age[tr], sex[tr])
        ac_te = age[~tr] - center
        zte = np.c_[np.ones(1), ac_te, ac_te * ac_te, sex[~tr]]
        by, _bx, ysd, _xsd, _good, _xs, _ys = learner._fit_nuisance(
            ztr, y[tr], dummy[tr])
        losses[i] = float(((y[~tr] - zte @ by) / ysd)[0]) ** 2
    return losses


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pathology-source", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    discovery, confirmation = donor_roles()
    print("donor roles: %d DISCOVERY, %d CONFIRMATION"
          % (len(discovery), len(confirmation)))

    field = donor_id_field(args.pathology_source, discovery)
    print("donor identity column: %r" % field)

    loaded = stage2b.load_role_numeric_at8(
        args.pathology_source,
        role="DISCOVERY",
        endpoint_identity=ENDPOINT_IDENTITY,
        donor_id_field=field,
        included_donors=discovery,
        excluded_donors=confirmation,
        expected_source_sha256=FROZEN_PATHOLOGY_SHA,
        expected_donor_set_sha256=FROZEN_DONOR_SET_SHA)

    if loaded["endpoint_values_sha256"] != FROZEN_ENDPOINT_VALUES_SHA:
        _fail("endpoint values digest %s does not reproduce the frozen %s"
              % (loaded["endpoint_values_sha256"], FROZEN_ENDPOINT_VALUES_SHA))
    print("endpoint values digest reproduces V20 exactly: %s"
          % loaded["endpoint_values_sha256"])
    print("confirmation rows present and skipped unread: %d"
          % loaded["confirmation_rows_present_and_skipped"])
    if loaded["confirmation_numeric_at8_accessed"]:
        _fail("confirmation AT8 was accessed")

    donors = sorted(loaded["values"], key=lambda d: d.encode("utf-8"))
    y = np.array([loaded["values"][d] for d in donors], dtype=np.float64)
    age, sex = age_sex_for(donors)

    primary = nuisance_only_fold_losses(y, age, sex)
    secondary = nuisance_only_via_frozen_helper(y, age, sex)
    agree = bool(np.array_equal(primary, secondary))

    mean_a = float(primary.mean())
    mean_b = float(np.sum(secondary) / len(secondary))
    mean_c = float(math_fsum(primary) / len(primary))

    print()
    print("PER-FOLD NUISANCE-ONLY LOSSES (standardized residual scale)")
    for i, (d, v) in enumerate(zip(donors, primary)):
        print("  fold %2d  donor %-12s  yte^2 = %.12f" % (i, d, v))

    print()
    print("L_inf  (mean, np.mean)        = %.12f" % mean_a)
    print("L_inf  (independent helper)   = %.12f" % mean_b)
    print("L_inf  (exact fsum)           = %.12f" % mean_c)
    print("two implementations bitwise identical: %s" % agree)
    print()
    print("V20 best grid point (exp +2.0) = %.12f" % V20_BEST_GRID_LOSS)
    print("L_inf - V20_best               = %+.12f" % (mean_a - V20_BEST_GRID_LOSS))
    print()
    print("fold-loss spread: min %.6f  median %.6f  max %.6f"
          % (primary.min(), float(np.median(primary)), primary.max()))
    order = np.argsort(primary)[::-1][:3]
    print("largest three fold contributions: %s"
          % ", ".join("fold %d (%.4f)" % (int(i), primary[int(i)])
                      for i in order))
    print("share of the total from the largest fold: %.1f%%"
          % (100.0 * primary.max() / primary.sum()))

    report = {
        "endpoint_values_sha256": loaded["endpoint_values_sha256"],
        "donor_set_sha256": loaded["donor_set_sha256"],
        "pathology_source_sha256": loaded["pathology_source_sha256"],
        "confirmation_rows_present_and_skipped":
            loaded["confirmation_rows_present_and_skipped"],
        "confirmation_numeric_at8_accessed": False,
        "n_folds": int(len(primary)),
        "fold_losses": [float(v) for v in primary],
        "fold_donor_order": donors,
        "L_infinity_mean": mean_a,
        "L_infinity_mean_independent": mean_b,
        "L_infinity_mean_fsum": mean_c,
        "implementations_bitwise_identical": agree,
        "v20_best_grid_loss": V20_BEST_GRID_LOSS,
        "difference": mean_a - V20_BEST_GRID_LOSS,
        "note": "Reported without interpretation. Pathology magnitudes are not "
                "emitted; fold losses are on the standardized residual scale.",
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("written: %s" % args.out)
    return 0


def math_fsum(values) -> float:
    import math
    return math.fsum(float(v) for v in values)


if __name__ == "__main__":
    raise SystemExit(main())
