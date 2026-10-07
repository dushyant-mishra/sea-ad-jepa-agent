import json
from pathlib import Path

import numpy as np

from scripts.v77.v77_synthetic_batch_adapter import build_from_world, sample_hidden_targets
from sea_ad_jepa.qualification import v77_join, v77_zero_update
from sea_ad_jepa.qualification.qsafe import REQUIRED_Q_SAFETY_CHANNELS
from sea_ad_jepa.qualification.receipts import BoundAdapterQSafetyProofV1


def _write_world(root: Path, counts: np.ndarray) -> None:
    truth = root / "hidden_truth"
    obs = root / "observable_raw" / "obs"
    truth.mkdir(parents=True)
    obs.mkdir(parents=True)
    np.savez(truth / "TRUTH_000.npz", global_cell_index=np.array([101], dtype=np.int64))

    counts = np.asarray(counts, dtype=np.float64)
    nz = np.flatnonzero(counts)
    support = np.ones((1, len(counts)), dtype=bool)
    np.savez(
        obs / "shard_000.npz",
        data=counts[nz],
        indices=nz.astype(np.int32),
        indptr=np.array([0, len(nz)], dtype=np.int64),
        global_cell_index=np.array([101], dtype=np.int64),
        support_mask_packed=np.packbits(support, axis=1),
        support_count=np.array([len(counts)], dtype=np.int32),
        source_index=np.array([0], dtype=np.int16),
        operator_index=np.array([0], dtype=np.int16),
        donor_index=np.array([0], dtype=np.int32),
    )
    manifest = {
        "schema": "V77_TEST_OBSERVER_V1",
        "n_addresses": len(counts),
        "shards": [{"file": "shard_000.npz"}],
        "structural_support_rule": "test-support-v1",
        "feature_identity": {"registry": [f"g{i}" for i in range(len(counts))]},
        "observation_identity": {
            "source_roster": ["SRC"],
            "operator_ids": ["OP"],
            "operator_source_map": [["OP", "SRC"]],
            "donor_ids": ["D0"],
        },
    }
    (obs / "OBSERVER_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_hidden_query_value_perturbation_cannot_change_model_side_and_mints_bound_proof(tmp_path):
    support = np.ones((1, 4), dtype=bool)
    gci = np.array([101], dtype=np.int64)
    seed = 20261007
    hidden = sample_hidden_targets(support, gci, hidden_fraction=0.25, seed=seed)
    hidden_index = int(np.flatnonzero(hidden[0])[0])

    counts_a = np.array([2.0, 3.0, 5.0, 7.0])
    counts_b = counts_a.copy()
    counts_b[hidden_index] += 100.0
    root_a = tmp_path / "world-a"
    root_b = tmp_path / "world-b"
    _write_world(root_a, counts_a)
    _write_world(root_b, counts_b)

    universe = np.arange(4, dtype=np.int64)
    baseline = build_from_world(root_a, "obs", universe, hidden_fraction=0.25, seed=seed)
    challenge = build_from_world(root_b, "obs", universe, hidden_fraction=0.25, seed=seed)

    assert baseline.readout.digest() != challenge.readout.digest(), "attack did not change hidden query value"
    assert baseline.model.digest() == challenge.model.digest(), "hidden query value leaked into model-visible state"
    assert baseline.operator_context.digest() == challenge.operator_context.digest(), "hidden query value leaked into operator summaries"

    batch = v77_join.build_qualification_batch_from_v77_conversion(
        baseline,
        feature_ids=("g0", "g1", "g2", "g3"),
        experiment_run_id="v77-qsafe-executed-001",
        adapter_id="v77-synthetic-batch-adapter",
        adapter_digest="a" * 64,
        code_commit="1234567890abcdef1234567890abcdef12345678",
        environment_digest="e" * 64,
        synthetic_realization_id="v77-dev-qsafe-001",
        challenge_partition="DEVELOPMENT_CALIBRATION",
    )

    prove = getattr(v77_join, "prove_v77_executed_q_safety_from_query_perturbation", None)
    assert callable(prove), "V77 join has no executed query-perturbation q-safety proof"
    proof = prove(
        baseline,
        challenge,
        batch=batch,
        adapter_id="v77-synthetic-batch-adapter",
        adapter_digest="a" * 64,
        runtime_source_sha256="c" * 64,
    )
    assert isinstance(proof, BoundAdapterQSafetyProofV1)
    assert {item.channel for item in proof.channel_evidence} == set(REQUIRED_Q_SAFETY_CHANNELS)
    assert proof.batch_scientific_identity_digest == batch.scientific_identity.digest()

    receipt = v77_zero_update.run_canonical_v5_zero_update(
        batch,
        q_safety_proof=proof,
        runtime_source_sha256="c" * 64,
        init_seed=8113002,
    )
    assert receipt["schema"] == "V77_CANONICAL_V5_ZERO_UPDATE_V1"
    assert receipt["q_safety_proof_digest"] == proof.digest()
    assert receipt["batch_scientific_identity_digest"] == batch.scientific_identity.digest()
    assert receipt["checkpoint_digest_before"] == receipt["checkpoint_digest_after"]
    assert receipt["online_parameters_unchanged"] is True
    assert receipt["teacher_parameters_unchanged"] is True
    assert receipt["predictor_parameters_unchanged"] is True
    assert receipt["optimizer_state_unchanged"] is True
    assert receipt["optimizer_step_performed"] is False
    assert receipt["ema_performed"] is False
    assert receipt["training_authorized"] is False
