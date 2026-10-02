from pathlib import Path
import importlib.util
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/v64/build_stage4_synthetic_worlds_v1.py"
EXECUTOR = ROOT / "scripts/v64/stage4_executor_v1.py"
RUNNER = ROOT / "scripts/v64/run_stage4_g2_sensitivity_curve_v1.py"
VERIFIER = ROOT / "scripts/v64/verify_confound_block_geometry_v1.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_repaired_partition_exactly_occupies_k_blocks():
    b = load(BUILDER, "v73_builder")
    for k in (1, 5, 20, 50, 200):
        labels, sizes = b._balanced_confound_partition(
            k, b.N_EDGES, np.random.default_rng(730000 + k))
        assert len(labels) == b.N_EDGES
        assert len(sizes) == k
        assert np.count_nonzero(sizes) == k
        assert sizes.sum() == b.N_EDGES
        assert int(sizes.max()) - int(sizes.min()) <= 1
    labels, sizes = b._balanced_confound_partition(
        b.N_EDGES, b.N_EDGES, np.random.default_rng(731000))
    assert sorted(labels.tolist()) == list(range(b.N_EDGES))
    assert np.all(sizes == 1)


def test_synthetic_executor_rejects_root_outside_fixed_parent():
    e = load(EXECUTOR, "v73_executor")
    with pytest.raises(e.Stop, match="synthetic root must stay under"):
        e.load_synthetic_world("HIDDEN_CONFOUND_K", "/tmp/not-the-jepa-synthetic-root")


def test_real_executor_cli_still_has_no_input_root_flag():
    text = EXECUTOR.read_text()
    assert 'ap.add_argument("--input-root"' not in text
    assert 'ap.add_argument("--output-root"' not in text
    assert 'V64_STAGE4_SYNTHETIC_ROOT' in text
    assert 'if a.synthetic_world:' in text


def test_runner_uses_draw_identity_not_worker_identity_for_writable_root():
    text = RUNNER.read_text()
    assert '"K%04d" % K' in text
    assert '"draw%03d_seed%09d" % (draw_index, seed_base)' in text
    assert 'V64_STAGE4_SYNTHETIC_ROOT' in text
    assert 'duplicate_roots' in text
    assert 'worker number and completion order are deliberately absent' in text


def test_experimental_builder_receipt_cannot_default_to_canonical_receipt():
    text = BUILDER.read_text()
    assert 'CANONICAL_BUILD_RECEIPT' in text
    assert 'V64_STAGE4_SYNTHETIC_EXPERIMENT_BUILD_' in text
    assert 'elif canonical:' in text
    assert 'if explicit_receipt:' in text


def test_verifier_requires_exact_partition_membership_not_only_component_count():
    text = VERIFIER.read_text()
    assert 'partition_membership_agreement' in text
    assert 'd_same == r_same' in text
    assert 'fraction_agree' in text
    assert '.get("exact")' in text
