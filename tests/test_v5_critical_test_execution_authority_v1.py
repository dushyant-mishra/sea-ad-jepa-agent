from pathlib import Path
import pytest
from sea_ad_jepa.v5.critical_test_execution_authority_v1 import CriticalTestExecutionAuthorityV1

def make_authority(status=None):
    return CriticalTestExecutionAuthorityV1('current',('gradient_gate','ema_after_proved_step'),'1'*64,status or {'gradient_gate':'EXECUTED_PASS','ema_after_proved_step':'EXECUTED_PASS'})

def test_exact_pass_set_valid():
    authority=make_authority(); authority.validate()
    assert len(authority.canonical_digest())==64
    assert authority.training_authorized is False

def test_missing_or_extra_test_fails_closed():
    with pytest.raises(ValueError): make_authority({'gradient_gate':'EXECUTED_PASS'}).validate()
    with pytest.raises(ValueError): make_authority({'gradient_gate':'EXECUTED_PASS','ema_after_proved_step':'EXECUTED_PASS','extra':'EXECUTED_PASS'}).validate()

def test_nonexecuted_or_fail_is_never_green():
    for status in ('NOT_RUN','SKIPPED','FAILED','PASS'):
        states={'gradient_gate':'EXECUTED_PASS','ema_after_proved_step':status}
        with pytest.raises(ValueError,match='EXECUTED_PASS'): make_authority(states).validate()

def test_source_has_no_fixed_geometry_vocabulary():
    source=Path('src/sea_ad_jepa/v5/critical_test_execution_authority_v1.py').read_text(encoding='utf-8')
    forbidden=('PROTECTED_48','HISTORICAL_128X8','six block','model_depth')
    assert [token for token in forbidden if token in source] == []
