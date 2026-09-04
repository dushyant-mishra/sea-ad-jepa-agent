"""Independent mutation verifier for the frozen real-F1 executor contract.

The literals and expectations below are reconstructed from the frozen contract;
production helpers are only exercised as subjects.  No expression is opened.
"""
from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

# ``resource`` is POSIX-only and the accepted preflight core imports it for a
# telemetry helper not exercised here.  Supply only the import-time name on
# Windows; no resource observation is mocked by these verifier tests.
if "resource" not in sys.modules:
    try:
        import resource  # noqa: F401
    except ModuleNotFoundError:
        sys.modules["resource"] = types.ModuleType("resource")

from scripts.v4 import contextual_target_f1_preflight_core_v1 as core
from scripts.v4 import run_contextual_target_f1_real_production_v1 as subject


LEVELS = (20, 40, 60, 80, 100)
AUTHORITY = {
    "repository_commit": "1" * 40,
    "executor_contract_sha256": "2" * 64,
    "executor_source_sha256": "3" * 64,
    **subject.FROZEN_ROOTS,
}


def cache_key(*, role: str, q: int = 17, evidence: int | None = 60,
              recipient: str = "recipient", input_cell: str = "recipient") -> str:
    return subject.forward_cache_identity(
        AUTHORITY,
        role=role,
        recipient=recipient,
        input_cell=input_cell,
        q=q,
        evidence_level=evidence,
        physical_mask_sha256="4" * 64,
        evidence_mask_sha256="5" * 64,
    )


def one_pair_tasks(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    # The production subject imports this accepted primitive by its historical
    # top-level module name.  Alias the same reviewed module, do not fake it.
    monkeypatch.setitem(sys.modules, "contextual_target_f1_preflight_core_v1", core)
    monkeypatch.setitem(subject.FULL_TOPOLOGY, "total_expensive_forwards", 11)
    state = np.asarray([1, 1, 1, 0, 2, 1, 1, 1], dtype=np.uint8)
    reader = SimpleNamespace(
        states={3: state},
        rows={"recipient": SimpleNamespace(row_locator="source::block#9")},
    )
    population = {
        "dedup": [{"canonical_cell_id": "recipient", "selected_query_address": "1"}],
        "cell_geometry": {"recipient": ("donor", 3, "source")},
        "null_by_recipient": {"recipient": {"source_canonical_cell_id": "null-cell"}},
    }
    return subject.build_forward_tasks(population, reader, AUTHORITY)


def write_effect_store(tmp_path: Path) -> tuple[subject.AtomicEffectStore, Path]:
    store = subject.AtomicEffectStore(tmp_path, "6" * 64)
    values = np.arange(8, dtype=np.float64).reshape(2, 4)
    return store, store.commit("donor__op003", ["effect-a", "effect-b"], values)


def test_p01_teacher_key_includes_evidence_mutation_is_killed():
    # Teacher identity is invariant to the five student evidence levels.
    keys = {cache_key(role="teacher", evidence=level) for level in (None, *LEVELS)}
    assert len(keys) == 1


def test_p02_student_key_drops_evidence_mutation_is_killed():
    assert len({cache_key(role="correct", evidence=level) for level in LEVELS}) == 5


def test_p03_null_key_drops_null_source_mutation_is_killed():
    first = cache_key(role="matched_null", input_cell="null-a")
    second = cache_key(role="matched_null", input_cell="null-b")
    assert first != second


def test_p04_query_removed_from_key_mutation_is_killed():
    assert cache_key(role="correct", q=17) != cache_key(role="correct", q=18)


def test_p05_compute_dedup_cannot_remove_inferential_assignment():
    # Same compute pair can still represent two distinct assignment authorities.
    expected = ["assignment-0@60", "assignment-1@60"]
    with pytest.raises(RuntimeError, match="EFFECT_MEMBERSHIP"):
        subject.validate_effect_ids([expected[0]], expected)


def test_p06_wrong_evidence_level_mutation_is_killed(monkeypatch):
    tasks = one_pair_tasks(monkeypatch)
    students = [row for row in tasks if row["role"] != "teacher"]
    assert [(row["role"], row["evidence_level"]) for row in students] == [
        pair for level in LEVELS for pair in (("correct", level), ("matched_null", level))
    ]


def test_p07_matched_null_cannot_be_qid_wrong_query_comparator(monkeypatch, tmp_path):
    """The bounded dry run must obtain QID from a cyclic wrong query, not null."""
    selected = [
        {"role": "teacher", "selection_sha256": "teacher", "canonical_cell_id": "recipient", "q": 7, "evidence_level": 60},
        {"role": "correct_student", "selection_sha256": "correct-own", "canonical_cell_id": "recipient", "q": 7, "evidence_level": 60},
        {"role": "correct_student", "selection_sha256": "correct-wrong", "canonical_cell_id": "recipient", "q": 11, "evidence_level": 60},
        {"role": "matched_null_student", "selection_sha256": "null", "canonical_cell_id": "recipient", "null_source_cell": "null-cell", "q": 7, "evidence_level": 60},
    ]

    class FakeReader:
        def __init__(self, *_args):
            self.rows = {"recipient": object(), "null-cell": object()}
            self.fixture = {"selected": selected}

    class Marker:
        def __init__(self, records):
            self.keys = [record["selection_sha256"] for record in records]

        def to(self, _device):
            return self

    vectors = {
        "teacher": np.asarray([1.0, 0.0], np.float32),
        "correct-own": np.asarray([1.0, 0.0], np.float32),
        "correct-wrong": np.asarray([-1.0, 0.0], np.float32),
        "null": np.asarray([0.0, 1.0], np.float32),
    }
    captured: dict[str, float] = {}

    def read_fixture(_reader, *_args):
        payload = {"normalized_values": np.zeros((2, 2)), "observation_states": np.ones((2, 2))}
        return payload, [{}, {}], {}, {}

    def prepare_chunk(chunk, _role, *_args):
        return [Marker(chunk), Marker(chunk), Marker(chunk), Marker(chunk)], None, None

    def lean_query_local(_encoder, marker, *_args):
        vector = torch.from_numpy(np.stack([vectors[key] for key in marker.keys]))
        return {"contextual_state": vector, "direct_state": vector}, {}

    def build_effect_row(**kwargs):
        captured["paired_wrong_similarity"] = float(kwargs["paired_wrong_similarity"])
        return {"A": 0.0, "direct_delta": 0.0, "qid_margin": 2.0, "qid_win": 1.0}

    fake_core = SimpleNamespace(MaterializedFixtureReader=FakeReader, lean_query_local=lean_query_local, load_encoder=lambda *_: object())
    fake_effect = SimpleNamespace(build_effect_row=build_effect_row)
    fake_reader = SimpleNamespace(prepare_chunk=prepare_chunk, read_fixture=read_fixture)
    monkeypatch.setitem(sys.modules, "contextual_target_f1_preflight_core_v1", fake_core)
    monkeypatch.setitem(sys.modules, "contextual_target_f1_preflight_executor_v1", fake_effect)
    monkeypatch.setitem(sys.modules, "run_contextual_target_f1_real_forward_preflight_v1", fake_reader)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    subject.run_technical_fixture(tmp_path / "dry", tmp_path, tmp_path)
    assert captured["paired_wrong_similarity"] == -1.0


def test_p08_extra_qid_neural_forward_mutation_is_killed(monkeypatch):
    tasks = one_pair_tasks(monkeypatch)
    assert len(tasks) == 1 + 2 * len(LEVELS)
    assert {row["role"] for row in tasks} == {"teacher", "correct", "matched_null"}


def test_p09_stale_shard_acceptance_mutation_is_killed(tmp_path):
    store, _ = write_effect_store(tmp_path)
    stale = subject.AtomicEffectStore(tmp_path, "7" * 64)
    with pytest.raises(RuntimeError, match="identity"):
        stale.load("donor__op003", ["effect-a", "effect-b"])


def test_p10_dtype_lie_mutation_is_killed(tmp_path):
    store, path = write_effect_store(tmp_path)
    with np.load(path, allow_pickle=False) as packed:
        fields = {name: packed[name].copy() for name in packed.files}
    fields["values"] = fields["values"].astype(np.float32)
    np.savez(path, **fields)
    with pytest.raises(RuntimeError, match="dtype"):
        store.load("donor__op003", ["effect-a", "effect-b"])


def test_p11_corrupted_payload_acceptance_mutation_is_killed(tmp_path):
    store, path = write_effect_store(tmp_path)
    with np.load(path, allow_pickle=False) as packed:
        fields = {name: packed[name].copy() for name in packed.files}
    fields["values"][0, 0] += 1.0
    np.savez(path, **fields)
    with pytest.raises(RuntimeError, match="payload"):
        store.load("donor__op003", ["effect-a", "effect-b"])


def test_p12_required_forward_replaced_by_duplicate_is_killed():
    class Store:
        def load(self, _block, task_ids):
            return np.zeros((len(task_ids), 2, 160), dtype=np.float32)

    attacked_index = [
        {"task_id": "teacher-a", "block_index": 0, "row_index": 0},
        {"task_id": "teacher-a", "block_index": 0, "row_index": 1},
    ]
    with pytest.raises(RuntimeError, match="RECONCILIATION|MEMBERSHIP|DUPLICATE|duplicate"):
        subject.load_forward_results(Store(), attacked_index)


def test_p13_required_effect_replaced_by_duplicate_is_killed():
    with pytest.raises(RuntimeError, match="EFFECT_MEMBERSHIP"):
        subject.validate_effect_ids(["effect-a", "effect-a"], ["effect-a", "effect-b"])


def test_p14_biological_summary_before_completeness_is_killed():
    record = subject.progress_record(completed_shards=9, completed_forwards=27, elapsed_seconds=1.5)
    assert set(record) == {"schema", "completed_shards", "completed_forwards", "elapsed_seconds"}
    forbidden = {"cosine", "A", "direct_delta", "qid_margin", "qid_win", "program", "threshold", "selection"}
    assert forbidden.isdisjoint(record)


def test_p15_launch_authority_bypass_is_killed(tmp_path):
    """A locally fabricated unsigned JSON is not an external authority."""
    output = tmp_path / "private" / "f1"
    fabricated = tmp_path / "self_created_launch.json"
    fabricated.write_text(json.dumps({
        "schema": subject.LAUNCH_SCHEMA,
        "real_f1_execution_authorized": True,
        "output_root": str(output.resolve()),
        **AUTHORITY,
    }), encoding="utf-8")
    with pytest.raises(RuntimeError, match=subject.STOP_UNAUTHORIZED):
        subject.validate_launch_authority(fabricated, output, AUTHORITY)


def test_p15_owner_receipt_binds_exact_non_self_referential_subject(monkeypatch, tmp_path):
    output = tmp_path / "private" / "f1"
    authority_subject = {
        "schema": subject.LAUNCH_SCHEMA,
        "real_f1_execution_authorized": True,
        "output_root": str(output.resolve()),
        **AUTHORITY,
    }
    subject_sha = subject.canonical_sha(authority_subject)
    api_url = "/repos/dushyant-mishra/sea-ad-jepa-agent/issues/comments/123"
    payload = {
        **authority_subject,
        "external_review_comment_api_url": api_url,
        "external_review_subject_sha256": subject_sha,
    }
    path = tmp_path / "externally_reviewed_launch.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    receipt = {
        "user": {"login": "dushyant-mishra"},
        "author_association": "OWNER",
        "body": f"JEPA_F1_REAL_PRODUCTION_AUTHORITY_SHA256={subject_sha}",
    }

    def gh_api(args, text=False):
        assert args == ["gh", "api", api_url]
        assert text is True
        return json.dumps(receipt)

    monkeypatch.setattr(subject.subprocess, "check_output", gh_api)
    assert subject.validate_launch_authority(path, output, AUTHORITY) == payload

    for field, bad_value in (
        ("body", "JEPA_F1_REAL_PRODUCTION_AUTHORITY_SHA256=" + "0" * 64),
        ("author_association", "MEMBER"),
    ):
        attacked = dict(receipt)
        attacked[field] = bad_value
        monkeypatch.setattr(subject.subprocess, "check_output", lambda *_args, **_kwargs: json.dumps(attacked))
        with pytest.raises(RuntimeError, match=subject.STOP_UNAUTHORIZED):
            subject.validate_launch_authority(path, output, AUTHORITY)


@pytest.mark.parametrize("partition", [
    "reader_validation", "reader_oracle", "DEV", "SEALED", "pathology", "quarantined",
])
def test_p16_protected_partition_admission_mutation_is_killed(partition):
    with pytest.raises(RuntimeError, match="FIREWALL"):
        subject.validate_reader_partition(partition)


def test_p17_public_output_path_mutation_is_killed(tmp_path):
    for path in (tmp_path / "public" / "f1", tmp_path / "docs" / "private-f1"):
        with pytest.raises(RuntimeError, match="PRIVATE_OUTPUT"):
            subject.validate_private_output(path)


def test_p18_environment_cannot_override_failed_launch_authority(monkeypatch, tmp_path):
    touched = False

    def production(*_args):
        nonlocal touched
        touched = True

    monkeypatch.setenv("REAL_F1_EXECUTION_AUTHORIZED", "true")
    monkeypatch.setenv("F1_LAUNCH_AUTHORITY", json.dumps(AUTHORITY))
    monkeypatch.setattr(subject, "run_production", production)
    with pytest.raises(RuntimeError, match=subject.STOP_UNAUTHORIZED):
        subject.dispatch("production", tmp_path / "private" / "f1", None, AUTHORITY)
    assert touched is False


def test_p19_41238_namespace_mutation_is_killed():
    assert core.F1_ARCHITECTURE["vocabulary_size"] == 41_238
    assert subject.FROZEN_ROOTS["namespace_sha256"] == "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
    assert subject.FROZEN_ROOTS["namespace_semantic_root"] == "595fd8bc860b13ce9ec2a957b0f3d92f850effcb51ae6e2f06b8c5d25d7bd53f"


def test_p20_no_context_cap_semantics_mutation_is_killed():
    genes = 1_301

    class Encoder:
        def __call__(self, **kwargs):
            batch = kwargs["expression"].shape[0]
            base = torch.arange(genes, dtype=torch.float32)[None, :, None]
            states = torch.cat((base, base.square(), torch.ones_like(base)), dim=2).expand(batch, -1, -1)
            return SimpleNamespace(gene_states=states)

    expression = torch.zeros((1, genes), dtype=torch.float32)
    physical = torch.ones((1, genes), dtype=torch.uint8)
    visible = torch.ones((1, genes), dtype=torch.bool)
    visible[0, 0] = False
    result, _ = core.lean_query_local(Encoder(), expression, physical, visible, torch.tensor([0]), "student")
    expected_mean = torch.tensor([genes / 2.0, genes * (2 * genes - 1) / 6.0, 1.0])
    assert int(result["context_counts"][0]) == genes - 1
    assert torch.allclose(result["mu_context"][0], expected_mean)
