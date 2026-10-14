"""Hostile synthetic mechanics probes for G8 (#343 head 82d17bfb).

Usage: python -B g8_probe.py <g8_worktree_root>
Synthetic data only. No real human data is read.
"""
from __future__ import annotations

import json
import math
import sys
from fractions import Fraction

import numpy as np

sys.path.insert(0, sys.argv[1])
import scripts.v5.td_real_measurement_reference_v1 as M  # noqa: E402

OUT: dict = {"module": M.__file__, "numpy": np.__version__}


def exact_nmin(a: Fraction) -> int:
    v = 1 / a - 1
    return max(1, -((-v.numerator) // v.denominator))  # ceil


def exact_upper_rank(n: int, a: Fraction) -> int:
    v = (n + 1) * (1 - a)
    return -((-v.numerator) // v.denominator)


def exact_lower_rank(n: int, a: Fraction) -> int:
    v = (n + 1) * a
    return v.numerator // v.denominator


# ---- 1. n_min and ranks at the frozen alphas, and exact-rational sweep
OUT["1_nmin_0.01/3"] = M.minimum_calibration_size(0.01 / 3)
OUT["1_nmin_0.01/6"] = M.minimum_calibration_size(0.01 / 6)
ref = M.build_depth_reference({d: {"displacements": [0.0] * 299, "support_fractions": [1.0] * 299} for d in M.DEPTHS})
OUT["1_K299_status_under_code"] = ref["status"]
OUT["1_code_alpha_eff"] = ref["alpha_eff"]
OUT["1_code_required_n"] = ref["required_n_per_depth"]
for n in (599, 600, 1000):
    u = M.upper_prediction_bound(list(range(n)), alpha=0.01 / 6)
    lo = M.lower_prediction_bound([i / n for i in range(n)], alpha=0.01 / 6)
    OUT[f"1_ranks_n{n}"] = {"upper": u.get("rank_1_based"), "upper_exact": exact_upper_rank(n, Fraction(1, 600)),
                            "lower": lo.get("rank_1_based"), "lower_exact": exact_lower_rank(n, Fraction(1, 600))}

mism = []
for k in range(1, 61):
    for base in (Fraction(1, 100), Fraction(1, 20), Fraction(1, 10)):
        a = base / k
        af = float(base) / k
        if not (0 < af < 1):
            continue
        if M.minimum_calibration_size(af) != exact_nmin(a):
            mism.append(("nmin", str(a), M.minimum_calibration_size(af), exact_nmin(a)))
        nmin = exact_nmin(a)
        for n in (nmin, nmin + 1, nmin + 7, 2 * nmin + 1, 10 * nmin + 3):
            u = M.upper_prediction_bound([0.0] * n, alpha=af)
            lo = M.lower_prediction_bound([0.5] * n, alpha=af)
            if u.get("rank_1_based") != exact_upper_rank(n, a):
                mism.append(("upper", str(a), n, u.get("rank_1_based"), exact_upper_rank(n, a)))
            if lo.get("rank_1_based") != exact_lower_rank(n, a):
                mism.append(("lower", str(a), n, lo.get("rank_1_based"), exact_lower_rank(n, a)))
OUT["1_rational_sweep_mismatches_vs_intended_rational"] = mism[:10]
OUT["1_rational_sweep_mismatch_count"] = len(mism)

# adversarial float alpha: true n_min exceeds code n_min (fudge rounds the wrong way)
adv = 1.0 / (100.0 + 5e-13)
fa = Fraction(adv)
n_code = M.minimum_calibration_size(adv)
u = M.upper_prediction_bound([float(i) for i in range(n_code)], alpha=adv)
OUT["1_adversarial_alpha"] = {"alpha": adv, "code_nmin": n_code, "exact_nmin_of_float": exact_nmin(fa),
                              "code_status_at_code_nmin": u["status"], "code_rank": u.get("rank_1_based"),
                              "exact_rank": exact_upper_rank(n_code, fa)}

# ---- 2. storage-layout binding of thinning randomness
cellA = [40, 0, 7, 120]
cellB = [3, 55, 0, 9]
m1 = M.thin_integer_counts([cellA, cellB], fraction=0.5, seed_namespace="CAL_A", seed=7)
m2 = M.thin_integer_counts([cellB, cellA], fraction=0.5, seed_namespace="CAL_A", seed=7)
OUT["2_same_cellA_two_row_orders"] = {"order1": m1[0], "order2": m2[1], "identical": m1[0] == m2[1]}
solo = M.thin_integer_counts([cellA], fraction=0.5, seed_namespace="CAL_A", seed=7)
pre = M.thin_integer_counts([[1, 1, 1, 1], cellA], fraction=0.5, seed_namespace="CAL_A", seed=7)
OUT["2_cellA_alone_vs_after_prepended_row"] = {"alone": solo[0], "after": pre[1], "identical": solo[0] == pre[1]}
blk1 = M.thin_integer_counts([[50] * 6], fraction=0.5, seed_namespace="CAL_A", seed=7)
blk2 = M.thin_integer_counts([[50] * 6], fraction=0.5, seed_namespace="CAL_A", seed=7)
OUT["2_two_different_cells_in_two_blocks_same_seed_identical_draws"] = blk1 == blk2
# address subsetting: dropping an address column changes the other addresses' draws
full = M.thin_integer_counts([cellA], fraction=0.5, seed_namespace="CAL_A", seed=7)[0]
sub = M.thin_integer_counts([cellA[1:]], fraction=0.5, seed_namespace="CAL_A", seed=7)[0]
OUT["2_address_subset_changes_other_addresses"] = {"full_tail": full[1:], "subset": sub, "identical": full[1:] == sub}
OUT["2_thin_signature"] = list(M.thin_integer_counts.__code__.co_varnames[:M.thin_integer_counts.__code__.co_argcount + M.thin_integer_counts.__code__.co_kwonlyargcount])

# ---- 3. integer / nonnegativity validation
cases = {
    "float_2.0": [[2.0]], "np_float64_2.0": [[np.float64(2.0)]], "bool_True": [[True]],
    "np_bool_True": [[np.bool_(True)]], "negative": [[-1]], "nan": [[float("nan")]],
    "None": [[None]], "np_int64_ok": [[np.int64(5)]], "np_uint64_2**63": [[np.uint64(2 ** 63)]],
    "py_int_2**63": [[2 ** 63]], "string_'3'": [["3"]], "ragged": [[1, 2], [3]], "1d": [1, 2, 3],
    "empty_cols": [[]], "int_ndarray": np.array([[4, 0]], dtype=np.int32),
    "float_ndarray_integral": np.array([[4.0, 0.0]]),
}
val = {}
for name, c in cases.items():
    try:
        r = M.thin_integer_counts(c, fraction=0.5, seed_namespace="A", seed=1)
        val[name] = f"ACCEPTED -> {r}"
    except M.MeasurementReferenceError as exc:
        val[name] = f"REJECTED(MRE): {str(exc)[:60]}"
    except Exception as exc:
        val[name] = f"RAISED {type(exc).__name__}: {str(exc)[:60]}"
OUT["3_count_validation"] = val
fr = {}
for name, f in {"np_float64_0.5": np.float64(0.5), "np_float32_0.5": np.float32(0.5), "int_0": 0, "Fraction_1/2": Fraction(1, 2)}.items():
    try:
        M.thin_integer_counts([[3]], fraction=f, seed_namespace="A", seed=1)
        fr[name] = "ACCEPTED"
    except Exception as exc:
        fr[name] = f"{type(exc).__name__}"
OUT["3_fraction_validation"] = fr
for name, s in {"np_int64_seed": np.int64(3)}.items():
    try:
        M.thin_integer_counts([[3]], fraction=0.5, seed_namespace="A", seed=s)
        OUT["3_" + name] = "ACCEPTED"
    except Exception as exc:
        OUT["3_" + name] = type(exc).__name__

# ---- 4. structural-unmeasured vs measured-zero
masked = np.ma.array([[50, 30]], mask=[[False, True]])
try:
    r = M.thin_integer_counts(masked, fraction=0.5, seed_namespace="A", seed=1)
    OUT["4_masked_unmeasured_entry"] = f"ACCEPTED; masked entry thinned as measured -> {r}"
except Exception as exc:
    OUT["4_masked_unmeasured_entry"] = f"{type(exc).__name__}: {str(exc)[:80]}"
OUT["4_mask_or_support_parameter_present"] = any(
    k in M.thin_integer_counts.__code__.co_varnames for k in ("mask", "support", "measured", "unmeasured"))
z = M.thin_integer_counts([[0, 1]], fraction=0.5, seed_namespace="A", seed=1)
OUT["4_unmeasured_encoded_as_0_and_measured_0_indistinguishable_output"] = z

# ---- 5. library-size consistency
rng = np.random.default_rng(0)
on = np.array([[30, 0, 12, 5]] * 1, dtype=np.int64)
off_total = 900  # molecules at source columns outside the passed address set
lib_full = int(on.sum()) + off_total
p = 0.25
thin_on = np.array(M.thin_integer_counts(on.tolist(), fraction=p, seed_namespace="CAL", seed=0))
norm_full_lib = np.log1p(thin_on * 1e4 / lib_full)                 # caller reuses full-source library
lib_thin = int(thin_on.sum()) + int(rng.binomial(off_total, p))    # consistent thinned library
norm_thin_lib = np.log1p(thin_on * 1e4 / lib_thin)
norm_orig = np.log1p(on * 1e4 / lib_full)
OUT["5_library"] = {
    "thin_api_returns_library": False,
    "orig_norm": np.round(norm_orig, 3).tolist(),
    "thinned_with_unthinned_full_library": np.round(norm_full_lib, 3).tolist(),
    "thinned_with_thinned_library": np.round(norm_thin_lib, 3).tolist(),
}

# ---- 6. namespace disjointness enforcement
same = M.thin_integer_counts([[9, 9]], fraction=0.5, seed_namespace="CAL_A", seed=0)
OUT["6_thin_accepts_deciding_equal_calibration_namespace"] = same is not None
OUT["6_build_depth_reference_takes_namespaces"] = any(
    "namespace" in v for v in M.build_depth_reference.__code__.co_varnames)
OUT["6_validator_has_refit_slot"] = "refit" in " ".join(M.validate_seed_namespaces.__code__.co_varnames)
try:
    M.validate_seed_namespaces(calibration_namespaces=["CAL"], deciding_namespace="CAL ", null_namespace="cal")
    OUT["6_near_duplicate_names_accepted"] = True
except M.MeasurementReferenceError:
    OUT["6_near_duplicate_names_accepted"] = False
ref_keys = sorted(ref)
OUT["6_reference_output_keys"] = ref_keys
OUT["6_reference_records_rng_or_namespace_or_input_binding"] = any(
    k for k in ref_keys if any(t in k for t in ("rng", "seed", "namespace", "binding", "numpy")))

# ---- 7. calibration lists are caller-asserted: duplicated single realization passes
one = 0.12
dup = M.build_depth_reference({d: {"displacements": [one] * 599, "support_fractions": [0.9] * 599} for d in M.DEPTHS})
OUT["7_599_copies_of_one_realization_status"] = dup["status"]

print(json.dumps(OUT, indent=1, default=str))
