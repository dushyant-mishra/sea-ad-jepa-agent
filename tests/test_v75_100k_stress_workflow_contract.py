from pathlib import Path


def test_v75_100k_stress_workflow_is_fail_closed_and_exact_scale():
    workflow = Path('.github/workflows/v75-100k-stress-only.yml')
    text = workflow.read_text()

    assert 'workflow_dispatch:' in text
    assert '--cells 100000' in text
    assert '--shard-size 10000' in text
    assert '--seed 7302' in text
    assert 'validate_v73_stress_promotion_readiness.py' in text
    assert "READY_FOR_100K_STRESS_ONLY" in text
    assert "100K_STRESS_ONLY" in text
    assert 'estimate_v73_synthetic_stress_resources.py --cells 100000 --shard-size 10000' in text
    assert 'actions/upload-artifact@v4' in text

    # The readiness gate must run before the first 100K producer.
    gate_pos = text.index('validate_v73_stress_promotion_readiness.py')
    build_pos = text.index('build_v73_sharded_master_truth.py --root /tmp/v75_100k_stress --cells 100000')
    assert gate_pos < build_pos

    # This workflow must not silently promote beyond the authorized scale.
    assert '--cells 500000' not in text
    assert '--cells 4553407' not in text
    assert 'TRAINING=ON' not in text
