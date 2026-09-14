from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PATH = ROOT / "docs" / "agent" / "V5_PROSPECTIVE_D_SHARED_AUTHORITY_V2.json"
MODULE = "sea_ad_jepa.v5.d_shared_authority_v2"


def _module():
    spec = importlib.util.find_spec(MODULE)
    assert spec is not None, "D_shared V2 authority module must exist"
    return importlib.import_module(MODULE)


def _authority():
    assert AUTHORITY_PATH.exists(), "V2 authority artifact must exist"
    return json.loads(AUTHORITY_PATH.read_text(encoding="utf-8"))


def test_v2_authority_module_and_artifact_exist():
    _module()
    authority = _authority()
    assert authority["schema"] == "JEPA_V5_PROSPECTIVE_D_SHARED_AUTHORITY_V2"


def test_v2_plan_carries_per_quantity_counts_not_scalar_execution_authority():
    m = _module()
    authority = _authority()
    raw = AUTHORITY_PATH.read_bytes()
    sha = __import__("hashlib").sha256(raw).hexdigest()
    plan = m.bind_d_shared_execution_plan_v2(authority, authority_sha256=sha)
    assert plan["schema"] == "JEPA_V5_D_SHARED_PRECISION_EXECUTION_PLAN_V2"
    assert set(plan["quantity_plan"]) == {
        "shared_matched_null_exceedance",
        "shared_subspace_stability",
        "shared_held_donor_cross_view_predictability",
        "shared_independent_view_agreement",
        "shared_measurement_shortcut_increment",
    }
    assert {row["replicates_per_rank"] for row in plan["quantity_plan"].values()} == {9784}
    assert plan["rank_min"] == 1
    assert plan["rank_max"] == 512
    assert "donor_resamples" not in plan
    assert "operator_resamples" not in plan
    assert "null_replicates" not in plan


def test_v2_authority_freezes_rank_multiplicity_generator_and_effect_rule():
    m = _module()
    authority = _authority()
    validated = m.validate_d_shared_authority_v2(authority)
    assert validated["rank_count"] == 512
    assert validated["alpha_per_quantity_rank"] == pytest.approx(0.05 / (10 * 512), rel=0, abs=1e-15)
    assert validated["matched_null_generator"] == "DETERMINISTIC_WITHIN_MATCHING_STRATUM_INDEPENDENT_VIEW_PERMUTATION_FULL_POPULATION_V1"
    assert validated["matching_tuple"] == ["donor", "operator", "Q_DEPTH", "Q_DETECT", "support_measurability"]
    assert validated["effect_criterion"] == "SIMULTANEOUS_LOWER_BOUND_STRICTLY_GT_ZERO_V1"


def test_v2_authority_rejects_wrong_count_and_outcome_access():
    m = _module()
    authority = _authority()
    bad = json.loads(json.dumps(authority))
    bad["quantities"][0]["replicates_per_rank"] -= 1
    with pytest.raises(m.DSharedAuthorityStop, match="REPLICATE_COUNT"):
        m.validate_d_shared_authority_v2(bad)
    bad = json.loads(json.dumps(authority))
    bad["outcomes_inspected_before_freeze"] = True
    with pytest.raises(m.DSharedAuthorityStop, match="PRE_FREEZE_ACCESS"):
        m.validate_d_shared_authority_v2(bad)


def test_v2_authority_rejects_nonfull_rank_envelope_and_generator_substitution():
    m = _module()
    authority = _authority()
    bad = json.loads(json.dumps(authority))
    bad["rank_max"] = 511
    with pytest.raises(m.DSharedAuthorityStop, match="RANK_ENVELOPE"):
        m.validate_d_shared_authority_v2(bad)
    bad = json.loads(json.dumps(authority))
    bad["matched_null_generator"] = "OTHER"
    with pytest.raises(m.DSharedAuthorityStop, match="MATCHED_NULL_GENERATOR"):
        m.validate_d_shared_authority_v2(bad)
