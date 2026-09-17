from __future__ import annotations

import hashlib

import pytest

from sea_ad_jepa.v5.address_universe_ladder_authority_v1 import AddressUniverseLadderAuthorityV1
from sea_ad_jepa.v5.outer_split_authority_v1 import OuterDonorSplitAuthorityV1
from sea_ad_jepa.v5.target_panel_authority_v1 import TargetPanelAuthorityV1


STRICT_SCALAR = "STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1"


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def split(**updates):
    values = dict(
        authority_id="JEPA_V5_OUTER_DONOR_SPLIT_AUTHORITY_V1",
        full104_substrate_sha256=h("full104"),
        donor_registry_sha256=h("donor-registry"),
        fold_assignment_artifact_sha256=h("folds"),
        split_semantics_id="OUTER_HELD_DONOR_EVALUATION_V1",
        screening_scope_policy_id="SCREEN_AND_FIT_ON_OUTER_TRAIN_DONORS_ONLY_V1",
        heldout_scope_policy_id="HELDOUT_DONORS_EVALUATION_ONLY_V1",
        n_folds=4,
        n_donors=104,
    )
    values.update(updates)
    return OuterDonorSplitAuthorityV1(**values)


def panel(**updates):
    values = dict(
        authority_id="JEPA_V5_TARGET_PANEL_AUTHORITY_V1",
        full104_substrate_sha256=h("full104"),
        canonical_registry_authority_sha256=h("registry-authority"),
        support_estimability_authority_sha256=h("support"),
        eligible_universe_authority_sha256=h("universe"),
        selector_artifact_sha256=h("selector"),
        target_list_artifact_sha256=h("target-list"),
        support_state_policy_id=STRICT_SCALAR,
        selection_policy_id="DETERMINISTIC_OUTCOME_BLIND_TARGET_PANEL_V1",
        outcome_firewall_policy_id="MASKING_QUALIFICATION_OUTCOME_NOT_USED_FOR_SELECTION_V1",
        target_count=64,
    )
    values.update(updates)
    return TargetPanelAuthorityV1(**values)


def ladder(**updates):
    values = dict(
        authority_id="JEPA_V5_ADDRESS_UNIVERSE_LADDER_AUTHORITY_V1",
        canonical_registry_authority_sha256=h("registry-authority"),
        support_estimability_authority_sha256=h("support"),
        ladder_artifact_sha256=h("ladder"),
        ordered_universe_ids=("QUALIFICATION_800_V1", "QUALIFICATION_6000_V1", "FULL_COMMON_CORE_17186_V1"),
        ordered_universe_sha256=(h("u800"), h("u6000"), h("u17186")),
        ordered_universe_sizes=(800, 6000, 17186),
        support_state_policy_id=STRICT_SCALAR,
        terminal_policy_id="FULL_COMMON_CORE_MUST_BE_TERMINAL_V1",
    )
    values.update(updates)
    return AddressUniverseLadderAuthorityV1(**values)


def test_outer_split_is_donor_heldout_and_full104_bound() -> None:
    split().validate()
    with pytest.raises(ValueError, match="split_semantics_id"):
        split(split_semantics_id="RANDOM_CELL_SPLIT").validate()
    with pytest.raises(ValueError, match="screening_scope_policy_id"):
        split(screening_scope_policy_id="SCREEN_ON_ALL_DONORS").validate()
    with pytest.raises(ValueError, match="heldout_scope_policy_id"):
        split(heldout_scope_policy_id="HELDOUT_CAN_TUNE").validate()
    with pytest.raises(ValueError, match="n_donors"):
        split(n_donors=103).validate()


def test_role_splicing_is_rejected_for_split_artifacts() -> None:
    digest = h("same")
    with pytest.raises(ValueError, match="distinct"):
        split(donor_registry_sha256=digest, fold_assignment_artifact_sha256=digest).validate()


def test_target_panel_is_deterministic_outcome_blind_and_strict_scalar_only() -> None:
    panel().validate()
    with pytest.raises(ValueError, match="selection_policy_id"):
        panel(selection_policy_id="PICK_TOP_RIDGE8_WINNERS").validate()
    with pytest.raises(ValueError, match="outcome_firewall_policy_id"):
        panel(outcome_firewall_policy_id="OUTCOME_ALLOWED").validate()
    with pytest.raises(ValueError, match="support_state_policy_id"):
        panel(support_state_policy_id="BINARY_MEASURED_INCLUDING_COLLISION_UNRESOLVED").validate()
    with pytest.raises(ValueError, match="target_count"):
        panel(target_count=0).validate()


def test_target_panel_roles_are_distinct() -> None:
    digest = h("same")
    with pytest.raises(ValueError, match="distinct"):
        panel(selector_artifact_sha256=digest, target_list_artifact_sha256=digest).validate()
    with pytest.raises(ValueError, match="distinct"):
        panel(support_estimability_authority_sha256=digest, eligible_universe_authority_sha256=digest).validate()


def test_universe_ladder_requires_terminal_full_common_core_and_strict_scalar_state() -> None:
    ladder().validate()
    with pytest.raises(ValueError, match="terminal"):
        ladder(ordered_universe_ids=("QUALIFICATION_800_V1",), ordered_universe_sha256=(h("u800"),), ordered_universe_sizes=(800,)).validate()
    with pytest.raises(ValueError, match="17186"):
        ladder(ordered_universe_sizes=(800, 6000, 17000)).validate()
    with pytest.raises(ValueError, match="support_state_policy_id"):
        ladder(support_state_policy_id="MEASURED_OR_COLLISION_UNRESOLVED").validate()


def test_universe_ladder_lengths_and_uniqueness_are_exact() -> None:
    with pytest.raises(ValueError, match="same nonzero length"):
        ladder(ordered_universe_sha256=(h("u800"),)).validate()
    with pytest.raises(ValueError, match="unique"):
        ladder(ordered_universe_ids=("QUALIFICATION_800_V1", "QUALIFICATION_800_V1", "FULL_COMMON_CORE_17186_V1")).validate()
    with pytest.raises(ValueError, match="strictly increasing"):
        ladder(ordered_universe_sizes=(800, 700, 17186)).validate()


def test_all_three_authorities_cannot_authorize_training() -> None:
    for obj in (split(training_authorized=True), panel(training_authorized=True), ladder(training_authorized=True)):
        with pytest.raises(ValueError, match="cannot authorize training"):
            obj.validate()
