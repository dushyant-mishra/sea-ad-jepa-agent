"""Stage-A structural qualification attacks for V5_SHARED_ADDRESS_QUERY_PROVIDER_V1.

Fixture-only geometry. None of the numbers below is a production default: n_buckets,
n_hashes, query_width and init_seed are supplied by later authorities, and are chosen here
purely to be small and fast.
"""
from __future__ import annotations

import json

import pytest

from sea_ad_jepa.v5.address_identity_encoding_v1 import (
    AddressIdentityEncodingV1,
    ForbiddenProviderInputError,
    is_per_address_memorization,
    reject_forbidden_inputs,
    trainable_parameter_count,
)

torch = pytest.importorskip("torch", reason="structural gradient/EMA checks require torch")

from sea_ad_jepa.v5.shared_address_query_provider_v1 import (  # noqa: E402
    PROVIDER_ID,
    SharedAddressQueryProviderV1,
)

REGISTRY_AUTHORITY = "28b20a457c44ac864c375492c8875e865ed6fe6d2000338d5fd46d9557a25676"

# fixture-only geometry -- NOT production values
FX_BUCKETS, FX_HASHES, FX_WIDTH, FX_SEED = 64, 4, 8, 1234
ADDRESSES = [f"ENSG{i:011d}" for i in range(32)]


def make_provider(**over) -> "SharedAddressQueryProviderV1":
    kw = dict(registry_authority_sha256=REGISTRY_AUTHORITY, n_buckets=FX_BUCKETS,
              n_hashes=FX_HASHES, query_width=FX_WIDTH, init_seed=FX_SEED)
    kw.update(over)
    return SharedAddressQueryProviderV1(**kw)


# ============================================================ CHECK 1: sharing
def test_trainable_parameters_do_not_scale_with_address_count() -> None:
    p = make_provider()
    assert p.trainable_parameter_count() == p.expected_trainable_parameter_count()
    assert p.trainable_parameter_count() == FX_BUCKETS * FX_WIDTH + FX_WIDTH
    # The registry has 41,238 addresses; the parameter budget does not know that.
    assert p.trainable_parameter_count() < 41238 * FX_WIDTH


def test_parameter_count_is_invariant_to_registry_row_count() -> None:
    for n_addresses in (10, 1000, 41238, 10 ** 6):
        assert trainable_parameter_count(n_buckets=FX_BUCKETS, query_width=FX_WIDTH) \
            == FX_BUCKETS * FX_WIDTH + FX_WIDTH


def test_unrestricted_per_address_embedding_is_rejected_by_qualification() -> None:
    attack = torch.nn.Embedding(41238, FX_WIDTH)
    n = sum(q.numel() for q in attack.parameters() if q.requires_grad)
    assert is_per_address_memorization(
        trainable_parameters=n, n_addresses=41238, query_width=FX_WIDTH) is True


def test_shared_provider_passes_the_same_qualification() -> None:
    p = make_provider()
    assert is_per_address_memorization(
        trainable_parameters=p.trainable_parameter_count(),
        n_addresses=41238, query_width=FX_WIDTH) is False


def test_distinct_addresses_provably_share_projection_rows() -> None:
    enc = AddressIdentityEncodingV1(n_buckets=FX_BUCKETS, n_hashes=FX_HASHES)
    used = [b for a in ADDRESSES for b in enc.buckets_for(a)]
    assert len(set(used)) < len(used), "addresses must share buckets, not own private rows"


# ============================================================ CHECK 2: gradient
def _context_prediction_loss(provider, *, detach_query=False, drop_query=False):
    """Smallest real context/evidence -> provider -> prediction path."""
    torch.manual_seed(0)
    context = torch.randn(len(ADDRESSES), FX_WIDTH)          # stands in for evidence
    readout = torch.nn.Linear(FX_WIDTH, 1)
    query = provider(ADDRESSES)
    if detach_query:
        query = query.detach()
    combined = context if drop_query else context * query
    prediction = readout(combined).squeeze(-1)
    target = torch.zeros(len(ADDRESSES))
    return torch.nn.functional.mse_loss(prediction, target)


def test_provider_parameters_receive_nonzero_gradient_from_the_prediction_path() -> None:
    p = make_provider()
    _context_prediction_loss(p).backward()
    for name, param in p.named_trainable_parameters():
        assert param.grad is not None, f"{name} received no gradient"
        assert torch.isfinite(param.grad).all(), f"{name} gradient not finite"
    assert p.projection.grad.abs().sum() > 0, "shared projection got zero gradient"


@pytest.mark.parametrize("kw", [{"detach_query": True}, {"drop_query": True}])
def test_broken_gradient_pathways_fail_qualification(kw: dict) -> None:
    p = make_provider()
    _context_prediction_loss(p, **kw).backward()
    total = sum(0.0 if q.grad is None else float(q.grad.abs().sum())
                for _, q in p.named_trainable_parameters())
    assert total == 0.0, "a detached/unused query must not produce provider gradient"


def test_stop_gradient_provider_fails_qualification() -> None:
    p = make_provider()
    for _, param in p.named_trainable_parameters():
        param.requires_grad_(False)
    assert p.trainable_parameter_count() == 0


# ============================================================ CHECK 3: teacher/EMA
def _ema_update(teacher: dict, student, decay: float) -> dict:
    return {k: decay * teacher[k] + (1.0 - decay) * dict(student.named_parameters())[k].detach()
            for k in teacher}


def test_every_trainable_parameter_is_enrolled_in_ema_state() -> None:
    p = make_provider()
    enrolled = {k for k, _ in p.named_trainable_parameters()}
    assert enrolled == {k for k, q in p.named_parameters() if q.requires_grad}
    assert enrolled, "provider exposes no trainable parameters to EMA"


def test_no_trainable_parameter_is_silently_omitted_from_ema() -> None:
    p = make_provider()
    teacher = {k: v.detach().clone() for k, v in p.named_trainable_parameters()}
    assert set(teacher) == {"projection", "bias"}


def test_skipped_optimizer_step_cannot_advance_ema_state() -> None:
    p = make_provider()
    teacher = {k: v.detach().clone() for k, v in p.named_trainable_parameters()}
    # no optimizer step taken -> student unchanged -> EMA must be a fixed point
    updated = _ema_update(teacher, p, decay=0.9)
    for k in teacher:
        assert torch.equal(teacher[k], updated[k]), f"EMA advanced for {k} without a step"


def test_teacher_and_student_provider_state_are_distinguishable() -> None:
    student = make_provider()
    teacher = {k: v.detach().clone() for k, v in student.named_trainable_parameters()}
    with torch.no_grad():
        student.projection.add_(1.0)
    assert not torch.equal(teacher["projection"], student.projection.detach())


# ============================================================ CHECK 4: replay
def test_checkpoint_roundtrip_reproduces_identical_address_to_query_behaviour() -> None:
    p = make_provider()
    with torch.no_grad():
        p.projection.add_(0.25)
    before = p(ADDRESSES)
    state, weights = p.replay_state(), p.state_dict()
    revived = SharedAddressQueryProviderV1.from_replay_state(state)
    revived.load_state_dict(weights)
    assert torch.equal(before, revived(ADDRESSES))


def test_replay_state_is_complete_enough_to_rebuild() -> None:
    for key in ("provider_id", "registry_authority_sha256", "encoding_fingerprint",
                "n_buckets", "n_hashes", "query_width", "init_seed"):
        assert key in make_provider().replay_state()


@pytest.mark.parametrize("missing", ["n_buckets", "n_hashes", "query_width", "init_seed",
                                     "registry_authority_sha256", "encoding_fingerprint"])
def test_partial_replay_state_fails_closed(missing: str) -> None:
    state = make_provider().replay_state()
    state.pop(missing)
    with pytest.raises(ValueError, match=missing):
        SharedAddressQueryProviderV1.from_replay_state(state)


def test_wrong_provider_id_in_replay_state_fails_closed() -> None:
    state = make_provider().replay_state()
    state["provider_id"] = "TD60_PROVIDER"
    with pytest.raises(ValueError, match="provider"):
        SharedAddressQueryProviderV1.from_replay_state(state)


def test_tampered_encoding_fingerprint_fails_closed() -> None:
    state = make_provider().replay_state()
    state["encoding_fingerprint"] = "0" * 64
    with pytest.raises(ValueError, match="fingerprint"):
        SharedAddressQueryProviderV1.from_replay_state(state)


def test_missing_parameter_in_checkpoint_fails_closed() -> None:
    p = make_provider()
    weights = p.state_dict()
    weights.pop("projection")
    with pytest.raises(RuntimeError):
        make_provider().load_state_dict(weights, strict=True)


def test_replay_is_deterministic_across_fresh_construction() -> None:
    a, b = make_provider(), make_provider()
    assert torch.equal(a(ADDRESSES), b(ADDRESSES))


def test_different_registry_authority_changes_the_query_artifact_binding() -> None:
    a = make_provider().query_artifact_sha256()
    b = make_provider(registry_authority_sha256="c" * 64).query_artifact_sha256()
    assert a != b


# ============================================================ CHECK 5: target independence
def test_query_is_unchanged_by_hidden_target_values() -> None:
    p = make_provider()
    baseline = p(ADDRESSES)
    for permutation in ([3.0, -1.0, 7.5], [0.0, 0.0, 0.0], [1e6, -1e6, 42.0]):
        # hidden targets exist in the caller's world; they must be structurally unable to
        # reach the provider at all.
        with pytest.raises(ForbiddenProviderInputError):
            p(ADDRESSES, target_value=permutation)
    assert torch.equal(baseline, p(ADDRESSES))


# ============================================================ CHECK 6: QC independence
@pytest.mark.parametrize("field", ["depth", "q_depth", "q_detect", "detection",
                                   "visibility", "expression_mean", "support_frequency"])
def test_qc_and_visibility_cannot_enter_the_provider(field: str) -> None:
    p = make_provider()
    baseline = p(ADDRESSES)
    with pytest.raises(ForbiddenProviderInputError, match=field):
        p(ADDRESSES, **{field: [1.0] * len(ADDRESSES)})
    assert torch.equal(baseline, p(ADDRESSES)), "query changed after a rejected QC attempt"


# ============================================================ CHECK 7: privileged lookup
@pytest.mark.parametrize("field", ["symbol", "biotype", "ontology", "graph_neighborhood",
                                   "chromosomal_coordinate", "source", "operator_index",
                                   "donor_id", "dataset_id", "expression_variance",
                                   "target_rank", "canonical_cell_id"])
def test_privileged_metadata_cannot_be_fed_to_the_provider(field: str) -> None:
    with pytest.raises(ForbiddenProviderInputError, match=field):
        make_provider()(ADDRESSES, **{field: ["x"] * len(ADDRESSES)})


def test_encoding_depends_only_on_canonical_identity() -> None:
    enc = AddressIdentityEncodingV1(n_buckets=FX_BUCKETS, n_hashes=FX_HASHES)
    assert enc.buckets_for("ENSG00000000003") == enc.buckets_for("ENSG00000000003")
    assert enc.buckets_for("ENSG00000000003") != enc.buckets_for("ENSG00000000005")


# ============================================================ CHECK 10: no QC re-entry
def test_provider_signature_offers_no_visibility_or_qc_channel() -> None:
    import inspect
    params = inspect.signature(SharedAddressQueryProviderV1.forward).parameters
    assert set(params) - {"self"} == {"molecular_address_ids", "forbidden"}, (
        "the only positional channel is canonical identity; everything else is rejected"
    )


def test_provider_output_shape_is_geometry_supplied_not_registry_derived() -> None:
    p = make_provider(query_width=5)
    assert p(ADDRESSES).shape == (len(ADDRESSES), 5)


# ============================================================ historical carryover
def test_no_historical_constant_is_a_provider_default() -> None:
    import inspect
    sig = inspect.signature(SharedAddressQueryProviderV1.__init__)
    for name, param in sig.parameters.items():
        assert param.default is inspect.Parameter.empty or name == "self", (
            f"{name} has a default; Stage-A must not ship a production default"
        )


def test_provider_id_carries_no_historical_experiment_name() -> None:
    assert not any(tag in PROVIDER_ID.upper() for tag in ("TD57", "TD59", "TD60"))
