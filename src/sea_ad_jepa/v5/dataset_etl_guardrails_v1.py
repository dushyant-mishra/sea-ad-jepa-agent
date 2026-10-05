"""Strict FULL104 dataset-ETL guardrails.

These guards qualify the already-reproduced V3 ETL evidence without mutating its
historical bytes. They close two audit gaps:

1. source inference may not fall through to SEA_AD for an unknown matrix id;
2. support-pattern source identification must be demonstrated by hash uniqueness
   across sources, not inferred from counts like 1 + 7 + 1.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterable, Mapping

CURRENT_SEA_AD_MATRIX_IDS = frozenset(
    {
        "sea_ad_ang_rna_final_2026",
        "sea_ad_caudate_rna_all_2025",
        "sea_ad_fi_rna_final_2026",
        "sea_ad_hip_rna_final_2026",
        "sea_ad_itg_rna_final_2026",
        "sea_ad_lec_rna_final_2026",
        "sea_ad_mec_rna_final_2026",
        "sea_ad_mtg_rna_final_2026",
        "sea_ad_pfc_a9_rna_final_2026",
        "sea_ad_stg_rna_final_2026",
        "sea_ad_v1c_rna_final_2026",
    }
)

EXPECTED_OPERATOR_COUNTS = {"HVS": 24, "NPH52": 7, "SEA_AD": 11}
EXPECTED_PATTERN_COUNTS = {"HVS": 1, "NPH52": 7, "SEA_AD": 1}


def strict_source_from_matrix_id(matrix_id: str) -> str:
    value = str(matrix_id)
    if value.startswith("HVS::") and len(value) > len("HVS::"):
        return "HVS"
    if value.startswith("NPH52::matrix::") and len(value) > len("NPH52::matrix::"):
        return "NPH52"
    if value in CURRENT_SEA_AD_MATRIX_IDS:
        return "SEA_AD"
    raise ValueError(f"unrecognized current FULL104 matrix_id: {value!r}")


def validate_operator_source_rows(rows: Iterable[Mapping[str, object]]) -> dict[str, int]:
    seen_matrix: set[str] = set()
    seen_operator: set[int] = set()
    counts: Counter[str] = Counter()

    for row in rows:
        matrix_id = str(row["matrix_id"])
        source = str(row["source"])
        operator_index = int(row["operator_index"])
        inferred = strict_source_from_matrix_id(matrix_id)
        if source != inferred:
            raise ValueError(
                f"matrix/source mismatch for {matrix_id!r}: declared {source!r}, inferred {inferred!r}"
            )
        if matrix_id in seen_matrix:
            raise ValueError(f"duplicate matrix_id: {matrix_id!r}")
        if operator_index in seen_operator:
            raise ValueError(f"duplicate operator_index: {operator_index}")
        seen_matrix.add(matrix_id)
        seen_operator.add(operator_index)
        counts[source] += 1

    observed = dict(counts)
    if observed != EXPECTED_OPERATOR_COUNTS:
        raise ValueError(
            f"current FULL104 operator counts drifted: expected {EXPECTED_OPERATOR_COUNTS}, "
            f"observed {observed}"
        )
    if seen_operator != set(range(42)):
        raise ValueError("current FULL104 operator indexes must be exactly 0..41")
    return observed


def validate_support_pattern_source_identity(
    rows: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    source_by_hash: dict[str, set[str]] = defaultdict(set)
    operators_by_source: Counter[str] = Counter()
    patterns_by_source: Counter[str] = Counter()

    for row in rows:
        source = str(row["source"])
        digest = str(row["support_pattern_sha256"])
        operators = int(row["operators"])
        if source not in EXPECTED_PATTERN_COUNTS:
            raise ValueError(f"unexpected support-pattern source {source!r}")
        if len(digest) != 64:
            raise ValueError("support_pattern_sha256 must be a SHA-256 digest")
        try:
            int(digest, 16)
        except ValueError as exc:
            raise ValueError("support_pattern_sha256 must be hexadecimal") from exc
        if operators <= 0:
            raise ValueError("support-pattern operator count must be positive")
        source_by_hash[digest].add(source)
        operators_by_source[source] += operators
        patterns_by_source[source] += 1

    collisions = {
        digest: sorted(sources)
        for digest, sources in source_by_hash.items()
        if len(sources) != 1
    }
    if collisions:
        raise ValueError(
            f"support pattern hash is shared across sources: {collisions}"
        )

    observed_patterns = dict(patterns_by_source)
    if observed_patterns != EXPECTED_PATTERN_COUNTS:
        raise ValueError(
            f"current FULL104 pattern counts drifted: expected {EXPECTED_PATTERN_COUNTS}, "
            f"observed {observed_patterns}"
        )
    observed_operators = dict(operators_by_source)
    if observed_operators != EXPECTED_OPERATOR_COUNTS:
        raise ValueError(
            f"support-pattern operator totals drifted: expected {EXPECTED_OPERATOR_COUNTS}, "
            f"observed {observed_operators}"
        )
    return {
        "support_pattern_is_source_identifying": True,
        "patterns_by_source": observed_patterns,
        "operators_by_source": observed_operators,
        "distinct_pattern_hashes": len(source_by_hash),
        "cross_source_hash_collisions": 0,
    }
