import importlib.util
from pathlib import Path

P = Path(__file__).resolve().parents[1] / 'scripts' / 'v5_anticheat' / 'full_reader_relational_target_preflight_v1.py'
spec = importlib.util.spec_from_file_location('full_reader_preflight', P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_train_loader_physical_binding_never_closes_full104():
    out = m.classify_expression_authority(
        loader_schema='foundation-train-loader-v1',
        location_status='PASS_42_OF_42_PHYSICAL_SHARDS_BOUND',
    )
    assert out['terminal'] == 'STOP_TRAIN_CACHE_IS_NOT_FULL104_EXPRESSION_AUTHORITY'
    assert out['full104_expression_binding_closed'] is False
    assert out['required_production_binder'] == 'scripts/v5_anticheat/bind_full104_expression_blocks_v4.py'
    assert out['required_production_terminal'] == 'PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE'


def test_missing_location_stays_fail_closed():
    out = m.classify_expression_authority(
        loader_schema='foundation-train-loader-v1',
        location_status='MISSING',
    )
    assert out['terminal'] == 'STOP_FULL_READER_EXPRESSION_LOCATION_BINDING_MISSING'
    assert out['full104_expression_binding_closed'] is False
