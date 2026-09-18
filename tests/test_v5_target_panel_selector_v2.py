import hashlib
import pytest

from sea_ad_jepa.v5.target_panel_selector_v2 import select_target_cols, TargetPanelSelectionReceiptV2


def h(x):
    return hashlib.sha256(x.encode()).hexdigest()


def test_selector_is_deterministic_and_count_is_explicit():
    eligible = list(range(100))
    a = select_target_cols(eligible, target_count=11, eligibility_receipt_sha256=h("elig"))
    b = select_target_cols(eligible, target_count=11, eligibility_receipt_sha256=h("elig"))
    assert a == b
    assert len(a) == 11
    assert len(set(a)) == 11


def test_selector_does_not_privilege_low_indices_or_input_order():
    eligible = list(range(100))
    a = select_target_cols(eligible, target_count=20, eligibility_receipt_sha256=h("elig"))
    b = select_target_cols(reversed(eligible), target_count=20, eligibility_receipt_sha256=h("elig"))
    assert a == b
    assert a != tuple(range(20))


def test_target_count_has_no_hidden_default():
    with pytest.raises(TypeError):
        select_target_cols(range(10), eligibility_receipt_sha256=h("elig"))


def test_receipt_fails_if_frozen_after_outcomes():
    with pytest.raises(ValueError, match="before terminal"):
        TargetPanelSelectionReceiptV2(
            eligibility_receipt_sha256=h("elig"),
            target_count=2,
            selected_target_cols=(1, 2),
            terminal_masking_outcomes_inspected=True,
        ).validate()
