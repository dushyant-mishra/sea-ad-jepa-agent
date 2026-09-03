"""Independent F1 gate reconstruction from raw frozen synthetic endpoints."""
from __future__ import annotations

import math

import numpy as np
from scipy.stats import t as student_t


ALPHA = 0.05
PROGRAMS = (
    "broad_common", "weak_distributed", "local", "local_core",
    "local_halo", "core_halo", "sparse_marker_like", "innovation_tail",
)
GATE_ORDER = (
    "legal_provenance",
    "overall_A_60_one_sided_positive",
    "protected_program_family_estimable",
    "no_contextual_minus_direct_degradation",
    "evidence_trend_one_sided_positive",
    "qid_v2_margin_one_sided_positive",
    "qid_v2_win_one_sided_positive",
    "no_qid_v2_program_negative_margin",
    "two_draw_sign_stable",
    "hc3_nuisance_positive",
    "cross_source_replication",
)
RECORD_FIELDS = {
    "overall_A", "program_A", "program_delta", "evidence_A", "qid_margin",
    "qid_win_minus_half", "program_qid_margin", "draw0", "draw1",
}


def independent_slope(evidence_row) -> float:
    row = np.asarray(evidence_row, dtype=np.float64)
    if row.shape != (5,) or not np.isfinite(row).all():
        raise ValueError("invalid independent evidence row")
    return float(math.fsum((-float(row[0]), -0.5 * float(row[1]), 0.5 * float(row[3]), float(row[4]))))


def independent_slopes(evidence_rows) -> np.ndarray:
    rows = np.asarray(evidence_rows, dtype=np.float64)
    if rows.ndim != 2 or rows.shape[1:] != (5,) or not np.isfinite(rows).all():
        raise ValueError("invalid independent evidence matrix")
    return np.asarray([independent_slope(row) for row in rows], dtype=np.float64)


def independent_interval(values, alpha: float = ALPHA) -> dict:
    x = np.asarray(values, dtype=np.float64)
    if x.ndim != 1:
        raise ValueError("independent interval requires one-dimensional values")
    n = int(x.size)
    mean = math.fsum(map(float, x)) / n if n else None
    if n < 2 or not np.isfinite(x).all():
        return {"estimable": False, "n": n, "mean": mean, "lower": None, "upper": None, "lower_one_sided": None, "p_positive": None, "p_negative": None}
    sum_squares = math.fsum((float(value) - mean) ** 2 for value in x)
    if sum_squares == 0.0:
        return {"estimable": False, "n": n, "mean": mean, "lower": None, "upper": None, "lower_one_sided": None, "p_positive": None, "p_negative": None}
    se = math.sqrt(sum_squares / (n - 1)) / math.sqrt(n)
    statistic = mean / se
    critical = float(student_t.ppf(1.0 - alpha / 2.0, n - 1))
    lower_one_sided = mean - float(student_t.ppf(1.0 - alpha, n - 1)) * se
    return {
        "estimable": True, "n": n, "mean": mean,
        "lower": mean - critical * se, "upper": mean + critical * se,
        "lower_one_sided": lower_one_sided,
        "p_positive": float(student_t.sf(statistic, n - 1)),
        "p_negative": float(student_t.cdf(statistic, n - 1)),
    }


def independent_report(evidence_rows, alpha: float = ALPHA) -> dict:
    rows = np.asarray(evidence_rows, dtype=np.float64)
    if rows.shape != (104, 5) or not np.isfinite(rows).all():
        raise ValueError("independent adjudication requires 104 donors by five levels")
    report = independent_interval(independent_slopes(rows), alpha)
    report["gate"] = bool(report["estimable"] and report["lower_one_sided"] > 0.0)
    return report


def independent_holm(probabilities) -> np.ndarray:
    p = np.asarray(probabilities, dtype=np.float64)
    if p.ndim != 1 or not np.isfinite(p).all() or np.any((p < 0.0) | (p > 1.0)):
        raise ValueError("invalid Holm probabilities")
    adjusted = np.empty(p.size, dtype=np.float64)
    running = 0.0
    for rank, index in enumerate(sorted(range(p.size), key=lambda i: (float(p[i]), i))):
        running = max(running, (p.size - rank) * float(p[index]))
        adjusted[index] = min(1.0, running)
    return adjusted


def _raw_endpoints(synthetic: dict, donor_order) -> dict:
    if set(synthetic) != {"donor_records", "legal"} or type(synthetic["legal"]) is not bool:
        raise ValueError("invalid raw synthetic authority")
    donors = list(donor_order)
    records = synthetic["donor_records"]
    if len(donors) != 104 or len(set(donors)) != 104 or not isinstance(records, dict) or set(records) != set(donors):
        raise ValueError("donor population mismatch")
    ordered = [records[donor] for donor in donors]
    if any(set(record) != RECORD_FIELDS for record in ordered):
        raise ValueError("raw donor endpoint schema mismatch")
    sources = [donor.split("::", 1)[0] if "::" in donor else "" for donor in donors]
    if set(sources) != {"HVS", "NPH52", "SEA_AD"}:
        raise ValueError("donor-derived source authority mismatch")
    vectors = {name: np.asarray([record[name] for record in ordered], dtype=np.float64) for name in ("overall_A", "qid_margin", "qid_win_minus_half", "draw0", "draw1")}
    evidence = np.asarray([record["evidence_A"] for record in ordered], dtype=np.float64)
    if evidence.shape != (104, 5) or any(value.shape != (104,) for value in vectors.values()):
        raise ValueError("raw endpoint shape mismatch")
    if not np.isfinite(evidence).all() or any(not np.isfinite(value).all() for value in vectors.values()):
        raise ValueError("nonfinite raw endpoint")
    families = {}
    for family in ("program_A", "program_delta", "program_qid_margin"):
        if any(set(record[family]) != set(PROGRAMS) for record in ordered):
            raise ValueError("protected-program family mismatch")
        families[family] = {program: np.asarray([record[family][program] for record in ordered], dtype=np.float64) for program in PROGRAMS}
        if any(value.shape != (104,) or not np.isfinite(value).all() for value in families[family].values()):
            raise ValueError("invalid protected-program endpoint")
    return {**vectors, **families, "evidence_A": evidence, "sources": sources, "legal": synthetic["legal"]}


def independent_complete_adjudication(
    synthetic: dict,
    donor_order,
    *,
    accepted_hc3_report: dict,
    accepted_hc3_method: str,
) -> dict:
    """Construct every current gate without consuming a production gate vector."""
    if accepted_hc3_method != "REDUCED_QR_TRIANGULAR_SOLVE_HC3":
        raise ValueError("accepted QR-HC3 authority required")
    if not isinstance(accepted_hc3_report, dict):
        raise ValueError("accepted QR-HC3 report required")
    raw = _raw_endpoints(synthetic, donor_order)
    overall = independent_interval(raw["overall_A"])
    program = {key: independent_interval(raw["program_A"][key]) for key in PROGRAMS}
    direct = {key: independent_interval(raw["program_delta"][key]) for key in PROGRAMS}
    qprogram = {key: independent_interval(raw["program_qid_margin"][key]) for key in PROGRAMS}
    positive_holm = independent_holm([program[key]["p_positive"] if program[key]["estimable"] else 1.0 for key in PROGRAMS])
    direct_negative_holm = independent_holm([direct[key]["p_negative"] if direct[key]["estimable"] else 0.0 for key in PROGRAMS])
    qprogram_negative_holm = independent_holm([qprogram[key]["p_negative"] if qprogram[key]["estimable"] else 0.0 for key in PROGRAMS])
    evidence = independent_report(raw["evidence_A"])
    qid_margin = independent_interval(raw["qid_margin"])
    qid_win = independent_interval(raw["qid_win_minus_half"])
    source_reports = {
        source: independent_interval(raw["overall_A"][np.asarray(raw["sources"]) == source])
        for source in sorted(set(raw["sources"]))
    }
    draw_means = [math.fsum(map(float, raw[name])) / 104 for name in ("draw0", "draw1")]
    hc3_gate = bool(
        accepted_hc3_report.get("estimable") is True
        and accepted_hc3_report.get("lower") is not None
        and accepted_hc3_report["lower"] > 0.0
    )
    gates = {
        "legal_provenance": raw["legal"] is True,
        "overall_A_60_one_sided_positive": bool(overall["estimable"] and overall["lower_one_sided"] > 0.0),
        "protected_program_family_estimable": bool(all(program[key]["estimable"] for key in PROGRAMS)),
        "no_contextual_minus_direct_degradation": bool(all(direct[key]["estimable"] for key in PROGRAMS) and np.all(direct_negative_holm >= ALPHA)),
        "evidence_trend_one_sided_positive": bool(evidence["gate"]),
        "qid_v2_margin_one_sided_positive": bool(qid_margin["estimable"] and qid_margin["lower_one_sided"] > 0.0),
        "qid_v2_win_one_sided_positive": bool(qid_win["estimable"] and qid_win["lower_one_sided"] > 0.0),
        "no_qid_v2_program_negative_margin": bool(all(qprogram[key]["estimable"] for key in PROGRAMS) and np.all(qprogram_negative_holm >= ALPHA)),
        "two_draw_sign_stable": bool(not ((draw_means[0] < 0.0 < draw_means[1]) or (draw_means[1] < 0.0 < draw_means[0]))),
        "hc3_nuisance_positive": hc3_gate,
        "cross_source_replication": bool(all(report["estimable"] and report["lower"] > 0.0 for report in source_reports.values())),
    }
    if tuple(gates) != GATE_ORDER:
        raise RuntimeError("independent gate order mismatch")
    return {
        "qualified": bool(all(gates.values())),
        "gates": gates,
        "reports": {
            "overall": overall,
            "protected_program_positive_holm_report_only": dict(zip(PROGRAMS, positive_holm.tolist())),
            "protected_program": program,
            "direct_negative_holm": dict(zip(PROGRAMS, direct_negative_holm.tolist())),
            "evidence_slope": {key: value for key, value in evidence.items() if key != "gate"},
            "qid_margin": qid_margin,
            "qid_win_minus_half": qid_win,
            "qid_program_negative_margin_holm": dict(zip(PROGRAMS, qprogram_negative_holm.tolist())),
            "draw_means": draw_means,
            "nuisance": accepted_hc3_report,
            "source_replication": source_reports,
        },
        "independent_gate_construction": "FROM_RAW_FROZEN_ENDPOINTS",
        "copied_production_gate_count": 0,
        "accepted_hc3_authority_reused": True,
    }


def compare_complete_adjudications(independent: dict, production: dict) -> dict:
    """Compare only after the independent gate vector already exists."""
    gate_comparisons = {
        gate: independent["gates"].get(gate) is production.get("gates", {}).get(gate)
        for gate in GATE_ORDER
    }
    return {
        "gate_comparisons": gate_comparisons,
        "all_11_gate_comparisons": bool(all(gate_comparisons.values())),
        "qualified_comparison": independent["qualified"] is production.get("qualified"),
    }
