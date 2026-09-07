"""Real-Torch smoke test: the production adapter against the actual u0 checkpoint.

Review finding F1-R1 required this. `TorchForwardEngine` previously called a
`build_teacher_encoder` factory the frozen model source does not define, and
invoked the result with a `cell=`/`mask=` interface the frozen `IPBEncoder`
does not accept, so the production seam was not executable as frozen and no
adapter was bound. This test loads the real u0 state dict and drives one
teacher, one correct-student and one matched-null forward through the exact
frozen adapter, then builds the real F1 effect row from the six resulting
vectors.

## Scope of what a pass here means

u0 is a MECHANICS FIXTURE, not a qualified biological teacher. The effect values
this produces are near zero, which is the expected mechanical result for an
untrained encoder and is not evidence about biology. Nothing here qualifies u0,
selects a training target, or authorizes a real F1 sweep.

## Requirements

Torch and the `sea_ad_jepa` package, plus the real u0 checkpoint. When any is
absent the tests report NOT_MEASURABLE and are excluded from any production pass
count; `F1_REQUIRE_TORCH_SMOKE=1` turns that into a failure. The project's
validated environment has torch, so a production review must run:

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
    mapping = adapter.load_matched_null_map(null_map_path)
    return encoder, mapping


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


def _smoke_adapter(encoder, mapping):
    injected = dict(mapping)
    injected["SMOKE_RECIPIENT"] = {
        "source_row_locator": "SMOKE::row#2",
        "source_canonical_cell_id": "SMOKE_SOURCE",
        "source_canonical_donor_id": "DONOR_B",
        "recipient_canonical_donor_id": "DONOR_A",
        "operator_index": "0"}
    return adapter.F1ProductionAdapter(encoder=encoder, matched_null_map=injected)


def test_the_real_u0_encoder_loads_from_the_frozen_checkpoint(real_adapter) -> None:
    encoder, mapping = real_adapter
    assert encoder.training is False, "the accepted mechanics require encoder.eval()"
    assert len(adapter.module_state_sha256(encoder)) == 64
    # The frozen matched-null map is cell level: 2,781 recipients, matching
    # `recipient_cells` in the frozen geometry.
    assert len(mapping) == 2781
    for entry in list(mapping.values())[:20]:
        assert entry["source_canonical_donor_id"] != entry["recipient_canonical_donor_id"]


def test_all_three_routes_execute_and_build_the_real_effect_row(real_adapter,
                                                                technical_row) -> None:
    """One teacher, one correct-student, one matched-null, then the estimand."""
    encoder, mapping = real_adapter
    engine = _smoke_adapter(encoder, mapping)
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

    source_expression = np.zeros(adapter.VOCABULARY_SIZE, dtype=np.float32)
    rng = np.random.default_rng(11)
    source_expression[row["measured"]] = rng.gamma(
        2.0, 0.5, size=row["measured"].size).astype(np.float32)
    null = engine.matched_null_student_state(
        row=row, evidence_level=60, source_normalized_expression=source_expression,
        source_row={"canonical_cell_id": "SMOKE_SOURCE",
                    "canonical_donor_id": "DONOR_B"})
    assert null["arm"] == "matched_null"
    assert null["matched_null_source_cell_id"] == "SMOKE_SOURCE"

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
    # u0 is untrained, so the effect is expected to be near zero. That is a
    # mechanical fact about a fixture, not a biological result.
    assert abs(float(effect["A"])) < 0.05


def test_the_matched_null_substitution_is_metamorphic(real_adapter,
                                                      technical_row) -> None:
    """F1-R6: changing the source changes the null state, nothing else.

    The causal contract permutes normalized values only, before the encoder, and
    keeps the recipient's M, U, q, operator and source. So a different source
    must move S_null while the recipient's evidence and physical-state identity
    stay byte-identical.
    """
    encoder, mapping = real_adapter
    engine = _smoke_adapter(encoder, mapping)
    row = technical_row
    rng = np.random.default_rng(5)
    first = np.zeros(adapter.VOCABULARY_SIZE, dtype=np.float32)
    first[row["measured"]] = rng.gamma(2.0, 0.5, size=row["measured"].size).astype(np.float32)
    second = first.copy()
    second[row["measured"][:100]] = second[row["measured"][:100]] * 3.0 + 1.0

    source_row = {"canonical_cell_id": "SMOKE_SOURCE", "canonical_donor_id": "DONOR_B"}
    a = engine.matched_null_student_state(row=row, evidence_level=60,
                                          source_normalized_expression=first,
                                          source_row=source_row)
    b = engine.matched_null_student_state(row=row, evidence_level=60,
                                          source_normalized_expression=second,
                                          source_row=source_row)
    assert not np.allclose(a["contextual"], b["contextual"]), (
        "a different matched-null source must change the null state")
    assert a["evidence_sha256"] == b["evidence_sha256"]
    assert a["physical_state_sha256"] == b["physical_state_sha256"]
    assert a["hidden_mask_sha256"] == b["hidden_mask_sha256"]


def test_a_wrong_matched_null_source_is_refused(real_adapter, technical_row) -> None:
    """The source must be the frozen one, never an improvised substitute."""
    encoder, mapping = real_adapter
    engine = _smoke_adapter(encoder, mapping)
    expression = np.zeros(adapter.VOCABULARY_SIZE, dtype=np.float32)
    expression[technical_row["measured"]] = 1.0
    with pytest.raises(AssertionError, match="MATCHED_NULL_SOURCE_UNRESOLVED"):
        engine.matched_null_student_state(
            row=technical_row, evidence_level=60,
            source_normalized_expression=expression,
            source_row={"canonical_cell_id": "NOT_THE_FROZEN_SOURCE",
                        "canonical_donor_id": "DONOR_B"})


def test_a_same_donor_matched_null_source_is_refused(real_adapter,
                                                     technical_row) -> None:
    """Donor-distinctness is part of the frozen map's meaning."""
    encoder, mapping = real_adapter
    injected = dict(mapping)
    injected["SMOKE_RECIPIENT"] = {
        "source_row_locator": "SMOKE::row#2",
        "source_canonical_cell_id": "SMOKE_SOURCE",
        "source_canonical_donor_id": "DONOR_A",       # same donor
        "recipient_canonical_donor_id": "DONOR_A",
        "operator_index": "0"}
    engine = adapter.F1ProductionAdapter(encoder=encoder, matched_null_map=injected)
    expression = np.zeros(adapter.VOCABULARY_SIZE, dtype=np.float32)
    expression[technical_row["measured"]] = 1.0
    with pytest.raises(AssertionError, match="NOT_DONOR_DISTINCT"):
        engine.matched_null_student_state(
            row=technical_row, evidence_level=60,
            source_normalized_expression=expression,
            source_row={"canonical_cell_id": "SMOKE_SOURCE",
                        "canonical_donor_id": "DONOR_A"})


def test_the_teacher_state_is_evidence_invariant(real_adapter, technical_row) -> None:
    """Why 43,108 teacher forwards suffice for 215,540 student comparisons."""
    encoder, mapping = real_adapter
    engine = _smoke_adapter(encoder, mapping)
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
    encoder, mapping = real_adapter
    engine = _smoke_adapter(encoder, mapping)
    for field, value in (("reader_partition", "reader_oracle"),
                         ("foundation_split", "foundation/dev")):
        row = dict(technical_row)
        row["provenance"] = dict(technical_row["provenance"])
        row["provenance"][field] = value
        with pytest.raises(PermissionError):
            engine.teacher_state(row=row)


def test_a_wrong_model_state_digest_is_refused(real_adapter, technical_row) -> None:
    """The authority binds the digest to the encoder it was handed."""
    encoder, mapping = real_adapter
    engine = _smoke_adapter(encoder, mapping)
    engine._model_state_sha256 = "0" * 64
    with pytest.raises(ValueError, match="model_state_sha256"):
        engine.teacher_state(row=technical_row)
