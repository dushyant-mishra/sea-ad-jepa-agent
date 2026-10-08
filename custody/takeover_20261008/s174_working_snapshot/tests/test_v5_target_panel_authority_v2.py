import hashlib
import pytest

from sea_ad_jepa.v5.target_panel_authority_v2 import TargetPanelAuthorityV2


def h(x):
    return hashlib.sha256(x.encode()).hexdigest()


def panel(**updates):
    values=dict(
        authority_id="TEST",
        full104_substrate_sha256=h("full104"),
        canonical_registry_authority_sha256=h("registry"),
        support_estimability_authority_sha256=h("support"),
        target_eligibility_receipt_sha256=h("elig"),
        target_panel_sizing_authority_sha256=h("sizing"),
        target_selection_receipt_sha256=h("selection"),
        selector_source_sha256=h("selector-source"),
        support_state_policy_id="STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1",
        selection_policy_id="DETERMINISTIC_HASH_RANKED_ELIGIBLE_TARGET_PANEL_V2",
        outcome_firewall_policy_id="MASKING_QUALIFICATION_OUTCOME_NOT_USED_FOR_SELECTION_V1",
        target_count=128,
    )
    values.update(updates)
    return TargetPanelAuthorityV2(**values)


def test_panel_v2_requires_128_and_strict_current_selection():
    panel().validate()
    with pytest.raises(ValueError, match="128"):
        panel(target_count=64).validate()
    with pytest.raises(ValueError, match="selection_policy_id"):
        panel(selection_policy_id="DISCOVERY_TOP32").validate()


def test_panel_v2_refuses_role_splicing():
    same=h("same")
    with pytest.raises(ValueError, match="role-distinct"):
        panel(target_selection_receipt_sha256=same, selector_source_sha256=same).validate()
