"""Real-Torch smoke test: the production adapter against the actual u0 checkpoint.

Review finding F1-R1 required this. `TorchForwardEngine` previously called a
`build_teacher_encoder` factory the frozen model source does not define, and
invoked the result with a `cell=`/`mask=` interface the frozen `IPBEncoder`
does not accept, so the production seam was not executable as frozen and no
adapter was bound. This test loads the real u0 state dict and drives one
teacher, one correct-student and one matched-null forward through the exact
frozen adapter, then builds the real F1 effect row from the six resulting
vectors.

## The corrected matched-null discriminator

An earlier version of the metamorphic test here fixed one source identity,
supplied two materially different expression vectors, and required BOTH to be
accepted. That demonstrated the value-binding hole while reading as proof of
correctness: it showed that the same authenticated identity could carry
arbitrary values. The discriminator is the other way round.

- same authenticated identity plus altered values must be impossible to
  construct;
- only a DIFFERENT authenticated identity carrying its own authentic values may
  move `S_null`, and even then the recipient's evidence, physical-state and
  hidden-mask identity must stay byte-identical.

## Scope of what a pass here means

u0 is a MECHANICS FIXTURE, not a qualified biological teacher, and nothing here
qualifies it, selects a training target, or authorizes a real F1 sweep.

No claim is made about the effect magnitude. Measured on this fixture across 15
combinations of row seed and source-value seed, |A| ranged from 0.0469 to
0.0681, and A was consistently positive because the correct student shares the
recipient's expression with the teacher while the null carries a different
cell's values. That is a structural consequence of the construction on an
untrained encoder, not a biological signal, so the test asserts only what is
true by construction rather than a magnitude bound.

## Requirements

Torch and the `sea_ad_jepa` package, plus the real u0 checkpoint. When any is
absent the tests report NOT_MEASURABLE and are excluded from any production pass
count; `F1_REQUIRE_TORCH_SMOKE=1` turns that into a failure. A production review
must run:

    conda run -n sea-ad-jepa-v3 python -m pytest tests/test_f1_u0_adapter_smoke_v1.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "v4"
sys.path.insert(0, str(SCRIPTS))

import f1_evidence_mask_authority_v1 as ev  # noqa: E402
import f1_production_runtime_adapter_v1 as adapter  # noqa: E402

AUTHORITY_ROOT_ENV = "F1_PREFREEZE_AUTHORITY_ROOT"
_EXPLICIT = os.environ.get(AUTHORITY_ROOT_ENV)
CANONICAL_ROOTS = ((Path(_EXPLICIT),) if _EXPLICIT
                   else (Path("/mnt/d/Jepa project"), Path("D:/Jepa project"), ROOT))
REQUIRE_SMOKE = os.environ.get("F1_REQUIRE_TORCH_SMOKE") == "1"

CHECKPOINT_REL = "exports/prod41k_teacher_t1_20260823/t1_run/t1_checkpoint_u0000.pt"
NULL_MAP_REL = ("outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/"
                "F1_MATCHED_NULL_PRIMARY_MAP.csv")

# One injected technical recipient, so the smoke row is addressable in the map.
SMOKE_SOURCE_ENTRY = {
    "source_row_locator": "SMOKE::row#2",
    "source_canonical_cell_id": "SMOKE_SOURCE",
    "source_canonical_donor_id": "DONOR_B",
    "recipient_canonical_donor_id": "DONOR_A",
    "operator_index": "0",
}


def _not_measurable(reason: str):
    message = ("NOT_MEASURABLE (not a pass): %s. Set %s and run under the project's "
               "torch environment, or F1_REQUIRE_TORCH_SMOKE=1 to fail instead."
               % (reason, AUTHORITY_ROOT_ENV))
    if REQUIRE_SMOKE:
        pytest.fail(message)
    pytest.skip(message)


def _resolve(relative: str) -> Path:
    for root in CANONICAL_ROOTS:
        candidate = root / relative
        if candidate.is_file():
            return candidate
    _not_measurable("authority %s not reachable" % relative)


def _requirements():
    try:
        import torch  # noqa: F401
    except ImportError:
        _not_measurable("torch is not installed in this interpreter")
    for root in CANONICAL_ROOTS:
        if (root / "src" / "sea_ad_jepa").is_dir():
            sys.path.insert(0, str(root))
            break
    else:
        _not_measurable("the sea_ad_jepa package is not reachable")
    try:
        import sea_ad_jepa.v4.contextual_query_local  # noqa: F401
    except ImportError as error:
        _not_measurable("sea_ad_jepa import failed: %s" % error)
    return _resolve(CHECKPOINT_REL), _resolve(NULL_MAP_REL)


@pytest.fixture(scope="module")
def real_adapter():
    """The frozen adapter over the real u0 encoder. Loaded once."""
    checkpoint, null_map_path = _requirements()
    encoder = adapter.load_u0_encoder(checkpoint)
    loaded = adapter.load_matched_null_map(null_map_path)
    return encoder, loaded


@pytest.fixture()
def technical_row():
    """A technical row shaped like a lawful one. No real biological content."""
    width = adapter.VOCABULARY_SIZE
    rng = np.random.default_rng(20260907)
    state = np.zeros(width, dtype=np.uint8)
    measured = rng.choice(width, size=400, replace=False)
    state[measured] = ev.MEASURED_SCALAR
    remaining = np.setdiff1d(np.arange(width), measured)
    state[rng.choice(remaining, size=50, replace=False)] = ev.MEASURED_COLLISION_UNRESOLVED
    query = int(measured[0])
    expression = np.zeros(width, dtype=np.float32)
    expression[measured] = rng.gamma(2.0, 0.5, size=measured.size).astype(np.float32)
    provenance = adapter.build_row_provenance(
        canonical_cell_id="SMOKE_RECIPIENT", query_address=query,
        physical_state_row=state, donor_id="DONOR_A", source="HVS", operator_index=0)
    return {"normalized_expression": expression, "physical_state": state,
            "query_index": query, "query_address": query,
            "row_locator": "SMOKE::row#1", "provenance": provenance,
            "measured": measured}


def _smoke_adapter(encoder, loaded, entry=None):
    """An adapter over the frozen map plus one injected technical recipient.

    It deliberately leaves `matched_null_map_sha256` unset, because an
    in-memory map is not the authenticated one. Production execution binding
    refuses that, and the binding attack in the parity suite proves it.
    """
    injected = dict(loaded["mapping"])
    injected["SMOKE_RECIPIENT"] = dict(entry or SMOKE_SOURCE_ENTRY)
    return adapter.F1ProductionAdapter(encoder=encoder, matched_null_map=injected)


def _smoke_source_values(measured, seed, *, entry=None):
    """Verified, row-bound values for the injected technical source."""
    info = dict(entry or SMOKE_SOURCE_ENTRY)
    width = adapter.VOCABULARY_SIZE
    rng = np.random.default_rng(seed)
    counts = np.zeros(width, dtype=np.float64)
    counts[measured] = rng.integers(0, 60, size=measured.size).astype(np.float64)
    return adapter.resolve_authenticated_source_values(
        expected=info, raw_counts=counts, source_library=11000.0,
        row_locator=info["source_row_locator"],
        canonical_cell_id=info["source_canonical_cell_id"],
        canonical_donor_id=info["source_canonical_donor_id"])


def test_the_real_u0_encoder_loads_from_the_frozen_checkpoint(real_adapter) -> None:
    encoder, loaded = real_adapter
    assert encoder.training is False, "the accepted mechanics require encoder.eval()"
    assert len(adapter.module_state_sha256(encoder)) == 64
    # The loader returns the digest of the bytes it read, which is what makes a
    # production runtime binding possible at all.
    assert loaded["matched_null_map_sha256"] == adapter.MATCHED_NULL_MAP_SHA256
    mapping = loaded["mapping"]
    # Cell level: 2,781 recipients, matching `recipient_cells` in the geometry.
    assert len(mapping) == 2781
    assert loaded["recipients"] == 2781
    for entry in list(mapping.values())[:20]:
        assert entry["source_canonical_donor_id"] != entry["recipient_canonical_donor_id"]


def test_all_three_routes_execute_and_build_the_real_effect_row(real_adapter,
                                                                technical_row) -> None:
    """One teacher, one correct-student, one matched-null, then the estimand."""
    encoder, loaded = real_adapter
    engine = _smoke_adapter(encoder, loaded)
    row = technical_row

    teacher = engine.teacher_state(row=row)
    assert teacher["role"] == "teacher"
    assert teacher["contextual"].shape == (adapter.MODEL_WIDTH,)
    assert teacher["direct"].shape == (adapter.MODEL_WIDTH,)
    # The teacher-rich target uses all of E, so its context count is |E|.
    eligible = ev.eligible_context(row["physical_state"], row["query_index"])
    assert teacher["context_counts"] == [int(eligible.size)]

    correct = engine.correct_student_state(row=row, evidence_level=60)
    assert correct["arm"] == "correct" and correct["evidence_level"] == 60
    # floor(0.60 * |E|), from the frozen evidence-mask authority.
    assert correct["context_counts"] == [ev.selected_count(60, int(eligible.size))]

    null = engine.matched_null_student_state(
        row=row, evidence_level=60,
        source_values=_smoke_source_values(row["measured"], 11))
    assert null["arm"] == "matched_null"
    assert null["matched_null_source_cell_id"] == "SMOKE_SOURCE"
    assert len(null["matched_null_source_values_sha256"]) == 64
    assert null["matched_null_source_provenance"]["applied_times"] == 1

    from contextual_target_f1_preflight_executor_v1 import build_effect_row, cosine

    own = float(cosine(correct["contextual"], teacher["contextual"]))
    wrong = float(cosine(null["contextual"], teacher["contextual"]))
    effect = build_effect_row(
        s_correct_contextual=correct["contextual"], t_true_contextual=teacher["contextual"],
        s_null_contextual=null["contextual"], s_correct_direct=correct["direct"],
        t_true_direct=teacher["direct"], s_null_direct=null["direct"],
        own_similarity=own, paired_wrong_similarity=wrong)
    for field in ("A", "direct_delta", "qid_margin", "qid_win"):
        assert field in effect and np.isfinite(effect[field]), field
    assert effect["A"] == pytest.approx(own - wrong, abs=1e-12)
    # No magnitude bound is asserted, and that is deliberate.
    #
    # An earlier version of this test asserted |A| < 0.05. Measured across 15
    # combinations of row seed and source-value seed on this fixture, |A| ranged
    # from 0.0469 to 0.0681, so that bound sat inside the observed range and
    # would have passed or failed depending on the seed. It was a number chosen
    # to make the test pass, not a property of the system.
    #
    # The magnitude here is driven by the synthetic value distribution of the
    # fixture, and A came out consistently positive because the correct student
    # shares the recipient's expression with the teacher while the null carries
    # a different cell's values. That is a structural consequence of the
    # construction, not a biological signal: u0 is an untrained mechanics
    # fixture. So the only claims made are the ones that are actually true by
    # construction -- the exact identity above, finiteness, and the
    # mathematical range of a difference of two cosines.
    assert abs(float(effect["A"])) <= 2.0
    assert abs(float(effect["direct_delta"])) <= 4.0


def test_same_source_identity_with_altered_values_is_impossible(real_adapter,
                                                                technical_row) -> None:
    """The corrected discriminator, first half.

    The old test required two different vectors under one identity to BOTH be
    accepted. Altered values must now fail to construct at all.
    """
    encoder, loaded = real_adapter
    _smoke_adapter(encoder, loaded)          # ensures the module fixture is live
    authentic = _smoke_source_values(technical_row["measured"], 5)

    tampered = authentic.normalized()
    tampered[technical_row["measured"][:100]] *= 3.0
    with pytest.raises(AssertionError, match="NORMALIZATION_NOT_ONCE_ONLY"):
        adapter.VerifiedSourceValues(
            row_locator=authentic.row_locator,
            canonical_cell_id=authentic.canonical_cell_id,
            canonical_donor_id=authentic.canonical_donor_id,
            raw_counts=np.zeros(adapter.VOCABULARY_SIZE, dtype=np.float64),
            source_library=authentic.source_library, normalized=tampered)

    # A free array is not an authenticated source at all.
    engine = _smoke_adapter(encoder, loaded)
    with pytest.raises(AssertionError, match="SOURCE_VALUES_UNVERIFIED"):
        engine.matched_null_student_state(
            row=technical_row, evidence_level=60,
            source_values=authentic.normalized())


def test_a_different_authenticated_source_may_move_the_null_state(real_adapter,
                                                                  technical_row) -> None:
    """The corrected discriminator, second half.

    Only a different authenticated identity carrying its own authentic values
    may change S_null, and the recipient's identity must stay byte-identical.
    """
    encoder, loaded = real_adapter
    row = technical_row
    first_engine = _smoke_adapter(encoder, loaded)
    other_entry = dict(SMOKE_SOURCE_ENTRY,
                       source_row_locator="SMOKE::row#3",
                       source_canonical_cell_id="SMOKE_SOURCE_2",
                       source_canonical_donor_id="DONOR_C")
    other_engine = _smoke_adapter(encoder, loaded, entry=other_entry)

    a = first_engine.matched_null_student_state(
        row=row, evidence_level=60,
        source_values=_smoke_source_values(row["measured"], 5))
    b = other_engine.matched_null_student_state(
        row=row, evidence_level=60,
        source_values=_smoke_source_values(row["measured"], 7, entry=other_entry))

    assert not np.allclose(a["contextual"], b["contextual"])
    assert a["matched_null_source_values_sha256"] != b["matched_null_source_values_sha256"]
    assert a["matched_null_source_cell_id"] != b["matched_null_source_cell_id"]
    # Recipient M, U and hidden mask are untouched by the substitution.
    assert a["evidence_sha256"] == b["evidence_sha256"]
    assert a["physical_state_sha256"] == b["physical_state_sha256"]
    assert a["hidden_mask_sha256"] == b["hidden_mask_sha256"]


def test_a_wrong_matched_null_source_is_refused(real_adapter, technical_row) -> None:
    """The source must be the frozen one, never an improvised substitute."""
    encoder, loaded = real_adapter
    engine = _smoke_adapter(encoder, loaded)
    wrong_entry = dict(SMOKE_SOURCE_ENTRY,
                       source_row_locator="SMOKE::rowX",
                       source_canonical_cell_id="NOT_THE_FROZEN_SOURCE")
    values = _smoke_source_values(technical_row["measured"], 3, entry=wrong_entry)
    with pytest.raises(AssertionError, match="MATCHED_NULL_SOURCE"):
        engine.matched_null_student_state(
            row=technical_row, evidence_level=60, source_values=values)


def test_a_same_donor_matched_null_source_is_refused(real_adapter,
                                                     technical_row) -> None:
    """Donor-distinctness is part of the frozen map's meaning."""
    encoder, loaded = real_adapter
    same_donor = dict(SMOKE_SOURCE_ENTRY, source_canonical_donor_id="DONOR_A")
    engine = _smoke_adapter(encoder, loaded, entry=same_donor)
    values = _smoke_source_values(technical_row["measured"], 4, entry=same_donor)
    with pytest.raises(AssertionError, match="NOT_DONOR_DISTINCT"):
        engine.matched_null_student_state(
            row=technical_row, evidence_level=60, source_values=values)


def test_the_teacher_state_is_evidence_invariant(real_adapter, technical_row) -> None:
    """Why 43,108 teacher forwards suffice for 215,540 student comparisons."""
    encoder, loaded = real_adapter
    engine = _smoke_adapter(encoder, loaded)
    first = engine.teacher_state(row=technical_row)
    second = engine.teacher_state(row=technical_row)
    assert np.allclose(first["contextual"], second["contextual"])
    assert first["evidence_sha256"] == second["evidence_sha256"]
    assert first["evidence_level"] is None and first["arm"] is None
    adapter.assert_no_nullized_teacher([{"role": "teacher", "arm": None}])
    with pytest.raises(AssertionError, match="NULLIZED_TEACHER_FORBIDDEN"):
        adapter.assert_no_nullized_teacher([{"role": "teacher", "arm": "matched_null"}])


def test_the_frozen_authority_rejects_a_protected_partition(real_adapter,
                                                            technical_row) -> None:
    """The query-local authority enforces its own firewall before any forward.

    `reader_partition` and `foundation_split` are two separate required fields,
    so neither substitutes for the other.
    """
    encoder, loaded = real_adapter
    engine = _smoke_adapter(encoder, loaded)
    for field, value in (("reader_partition", "reader_oracle"),
                         ("foundation_split", "foundation/dev")):
        row = dict(technical_row)
        row["provenance"] = dict(technical_row["provenance"])
        row["provenance"][field] = value
        with pytest.raises(PermissionError):
            engine.teacher_state(row=row)


def test_a_wrong_model_state_digest_is_refused(real_adapter, technical_row) -> None:
    """The authority binds the digest to the encoder it was handed."""
    encoder, loaded = real_adapter
    engine = _smoke_adapter(encoder, loaded)
    engine._model_state_sha256 = "0" * 64
    with pytest.raises(ValueError, match="model_state_sha256"):
        engine.teacher_state(row=technical_row)
