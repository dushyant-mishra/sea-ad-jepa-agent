import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts' / 'v5'
sys.path.insert(0, str(SCRIPTS))

import td_target_tournament_precision as p


def donor_rows(values):
    return [
        {'donor_id': f'd{i}', 'delta': value}
        for i, value in enumerate(values)
    ]


def test_unique_donor_records_can_establish_sign_resolution():
    out = p.sign_recurrence_gate(donor_rows([1,1,1,1,1,1]), 0.05)
    assert out['n_total_donors'] == 6
    assert out['n_nonzero_donors'] == 6
    assert out['donor_ids_bound'] is True
    assert out['pass'] is True


def test_duplicate_donor_identity_is_rejected_instead_of_inflating_n():
    rows = donor_rows([1,1,1,1,1,1])
    rows[-1]['donor_id'] = rows[0]['donor_id']
    with pytest.raises(p.PrecisionContractError):
        p.sign_recurrence_gate(rows, 0.05)


def test_bare_numeric_delta_list_is_rejected_as_unit_ambiguous():
    with pytest.raises(p.PrecisionContractError):
        p.sign_recurrence_gate([1,1,1,1,1,1], 0.05)


def test_donor_id_must_be_exact_nonempty_nul_free_string():
    for bad in (1, True, '', 'a\0b'):
        rows = donor_rows([1])
        rows[0]['donor_id'] = bad
        with pytest.raises(p.PrecisionContractError):
            p.sign_recurrence_gate(rows, 0.05)
