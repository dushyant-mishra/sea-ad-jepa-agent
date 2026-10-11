import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / 'scripts/v5/td_target_tournament_precision.py'
spec = importlib.util.spec_from_file_location('td_target_tournament_precision', MOD)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_minimum_donors_for_two_sided_sign_resolution_at_point05_is_six():
    assert m.minimum_donors_for_sign_resolution(0.05) == 6


def test_two_nph_donors_cannot_qualify_even_if_all_positive_at_point05():
    out = m.sign_recurrence_gate([1.0, 2.0], alpha_eff=0.05)
    assert out['resolution_estimable'] is False
    assert out['pass'] is False


def test_six_all_positive_can_pass_two_sided_sign_gate_at_point05():
    out = m.sign_recurrence_gate([1,1,1,1,1,1], alpha_eff=0.05)
    assert out['resolution_estimable'] is True
    assert out['two_sided_p'] == pytest.approx(0.03125)
    assert out['pass'] is True


def test_mixed_donors_do_not_pass():
    out = m.sign_recurrence_gate([1,1,1,-1,-1,-1], alpha_eff=0.05)
    assert out['pass'] is False


def test_zero_deltas_are_reported_as_ties_and_excluded():
    out = m.sign_recurrence_gate([1,1,1,1,1,1,0,0], alpha_eff=0.05)
    assert out['n_ties'] == 2 and out['n_nonzero'] == 6


def test_minimum_permutation_draws_are_derived_from_alpha_resolution():
    assert m.minimum_permutation_draws_for_resolution(0.05) == 19
    assert m.minimum_permutation_draws_for_resolution(0.01) == 99


def test_invalid_alpha_rejected():
    for a in [0,1,-0.1,1.1]:
        with pytest.raises(ValueError):
            m.minimum_donors_for_sign_resolution(a)
