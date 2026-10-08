import pytest
from pathlib import Path
from sea_ad_jepa.v5.production_protected_registry_authority_v1 import ProductionProtectedRegistryAuthorityV1, PROTECTED_ROLES, PROTECTED_PARAMETERS

def records(depth):
    return [
        {'block_index':b,'role':r,'parameter':p,'tensor_name':f'blocks.{b}.{r}.{p}'}
        for b in range(depth) for r in PROTECTED_ROLES for p in PROTECTED_PARAMETERS
    ]

def test_two_block_registry_is_dynamic():
    authority=ProductionProtectedRegistryAuthorityV1('current',2,records(2)); authority.validate()
    assert authority.expected_tensors == 16
    assert len(authority.normalized_records()) == 16
    assert len(authority.registry_sha256()) == 64

def test_depth_change_changes_expected_count_and_digest():
    a=ProductionProtectedRegistryAuthorityV1('current',2,records(2))
    b=ProductionProtectedRegistryAuthorityV1('current',3,records(3))
    assert a.expected_tensors==16 and b.expected_tensors==24
    assert a.registry_sha256()!=b.registry_sha256()

def test_missing_or_duplicate_fails_closed():
    rows=records(2)
    with pytest.raises(ValueError): ProductionProtectedRegistryAuthorityV1('x',2,rows[:-1]).validate()
    bad=rows.copy(); bad[-1]=bad[0]
    with pytest.raises(ValueError): ProductionProtectedRegistryAuthorityV1('x',2,bad).validate()

def test_source_has_no_fixed_historical_geometry_tokens():
    source=Path('src/sea_ad_jepa/v5/production_protected_registry_authority_v1.py').read_text(encoding='utf-8')
    forbidden=('PROTECTED_48','HISTORICAL_128X8','six-block','exactly 48','model_depth = 6')
    assert [token for token in forbidden if token in source] == []
