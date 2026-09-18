import hashlib

import numpy as np
import pytest

from sea_ad_jepa.v5.full104_control_calibration_cache_v1 import (
    CACHE_ROLE_ID,
    DISTRACTOR_COUNT,
    Full104ControlCalibrationCacheManifestV1,
    RetainedRowSelectorV1,
    select_calibration_columns,
    vector_digest,
)


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def test_row_selector_is_deterministic_nested_and_keeps_small_donors() -> None:
    selector_a = RetainedRowSelectorV1(full104_manifest_sha256=h("manifest"))
    selector_b = RetainedRowSelectorV1(full104_manifest_sha256=h("manifest"))
    rows = []
    donors = []
    cursor = 0
    for donor in range(104):
        count = 81 if donor == 0 else 1100
        rows.extend(range(cursor, cursor + count))
        donors.extend([donor] * count)
        cursor += count
    rows = np.asarray(rows, dtype=np.int64)
    donors = np.asarray(donors, dtype=np.int64)
    midpoint = rows.size // 2
    selector_a.update(rows[:midpoint], donors[:midpoint])
    selector_a.update(rows[midpoint:], donors[midpoint:])
    selector_b.update(rows, donors)
    out_a = selector_a.finalize()
    out_b = selector_b.finalize()
    for left, right in zip(out_a, out_b):
        assert np.array_equal(left, right)
    selected_rows, donor_code, rank, counts = out_a
    assert counts[0] == 81
    assert np.all(counts[1:] == 1024)
    assert np.array_equal(rank[donor_code == 0], np.arange(81))
    assert np.array_equal(rank[donor_code == 1], np.arange(1024))
    assert np.unique(selected_rows).size == selected_rows.size


def test_column_plan_uses_current_targets_proxies_and_disjoint_distractors() -> None:
    eligible = np.arange(1400, dtype=np.int64)
    targets = np.arange(1024, dtype=np.int64)
    ids = tuple(f"address-{i}" for i in range(1024))
    plan = select_calibration_columns(
        eligible_cols=eligible,
        target_cols=targets,
        target_ids=ids,
        target_eligibility_receipt_sha256=h("eligibility"),
    )
    assert len(plan["target_cols"]) == 1024
    assert len(plan["proxy_cols"]) == 1024
    assert len(plan["distractor_cols"]) == DISTRACTOR_COUNT
    assert set(plan["distractor_cols"]).isdisjoint(plan["target_cols"])
    assert set(plan["distractor_cols"]).isdisjoint(plan["proxy_cols"])
    assert all(t != p for t, p in zip(plan["target_cols"], plan["proxy_cols"]))
    assert set(plan["target_cols"]).issubset(plan["cache_cols"])
    assert set(plan["proxy_cols"]).issubset(plan["cache_cols"])


def manifest(**updates):
    roots = {name: h(name) for name in (
        "manifest","registry","census","support","split","eligibility",
        "target-sem","target-id-sem","proxy-sem","distractor-sem","cache-sem",
        "x","selection","donor","rank","counts","fold","source","full-n","full-sum","full-sumsq",
        "target-file","proxy-file","distractor-file","cache-file","ids-file"
    )}
    values = dict(
        authority_id="TEST",
        cache_role_id=CACHE_ROLE_ID,
        source_substrate_role_id="AUTHENTICATED_FULL104_LEVEL4_RAW_COUNTS_V1",
        normalization_id="EXACT_LOG1P_10000_FROM_RAW_COUNTS_ONCE_V1",
        x_dtype_id="FLOAT32_CALIBRATION_CACHE_NOT_TERMINAL_PRECISION_V1",
        full104_block_manifest_sha256=roots["manifest"],
        canonical_registry_sha256=roots["registry"],
        census_authority_sha256=roots["census"],
        support_estimability_authority_sha256=roots["support"],
        split_receipt_sha256=roots["split"],
        target_eligibility_receipt_sha256=roots["eligibility"],
        row_selection_namespace="JEPA_V5_FULL104_CONTROL_CACHE_ROW_PRIORITY_V1",
        distractor_namespace="JEPA_V5_FULL104_CONTROL_CACHE_DISTRACTOR_V1",
        max_rows_per_donor=1024,
        max_target_count=1024,
        distractor_count=31,
        retained_row_count=100000,
        retained_donor_count=104,
        min_retained_rows_per_donor=81,
        max_retained_rows_observed_per_donor=1024,
        cache_column_count=1800,
        x_shape_rows=100000,
        x_shape_cols=1800,
        target_cols_semantic_sha256=roots["target-sem"],
        target_ids_semantic_sha256=roots["target-id-sem"],
        proxy_cols_semantic_sha256=roots["proxy-sem"],
        distractor_cols_semantic_sha256=roots["distractor-sem"],
        cache_cols_semantic_sha256=roots["cache-sem"],
        x_file_sha256=roots["x"],
        selection_rows_file_sha256=roots["selection"],
        donor_code_file_sha256=roots["donor"],
        row_rank_file_sha256=roots["rank"],
        retained_count_by_donor_file_sha256=roots["counts"],
        fold_by_donor_file_sha256=roots["fold"],
        donor_source_code_file_sha256=roots["source"],
        full_donor_n_file_sha256=roots["full-n"],
        full_donor_sum_file_sha256=roots["full-sum"],
        full_donor_sumsq_file_sha256=roots["full-sumsq"],
        target_cols_file_sha256=roots["target-file"],
        proxy_cols_file_sha256=roots["proxy-file"],
        distractor_cols_file_sha256=roots["distractor-file"],
        cache_cols_file_sha256=roots["cache-file"],
        target_ids_file_sha256=roots["ids-file"],
    )
    values.update(updates)
    return Full104ControlCalibrationCacheManifestV1(**values)


def test_cache_manifest_is_explicitly_nonterminal() -> None:
    m = manifest()
    m.validate()
    m.assert_calibration_only()
    assert "FORBIDDEN_FOR_TERMINAL" in m.cache_role_id
    with pytest.raises(ValueError, match="forbidden for terminal"):
        manifest(terminal_masking_qualification_authorized=True).validate()
    with pytest.raises(ValueError, match="cannot authorize training"):
        manifest(training_authorized=True).validate()


def test_semantic_vector_digest_is_order_sensitive() -> None:
    assert vector_digest([1, 2, 3]) != vector_digest([3, 2, 1])
