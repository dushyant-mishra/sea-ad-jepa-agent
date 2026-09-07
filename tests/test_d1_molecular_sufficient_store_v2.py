from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import d1_molecular_sufficient_store_v2 as store  # noqa: E402
from d1_real_data_derivation_core_v1 import MEASURED_SCALAR  # noqa: E402


class FakeTeacher:
    def __init__(self, _path):
        self.manifest = {
            "archive_root_sha256": "a" * 64,
            "teacher_checkpoint_sha256": "b" * 64,
            "readout_contract_sha256": "c" * 64,
            "entries": [
                {"donor_id": "D1", "operator_index": 0, "rows": 2},
                {"donor_id": "D1", "operator_index": 1, "rows": 1},
                {"donor_id": "D2", "operator_index": 1, "rows": 2},
            ],
        }
        self._ids = {
            ("D1", 0): ["a", "b"],
            ("D1", 1): ["c"],
            ("D2", 1): ["d", "e"],
        }

    def strata(self):
        return sorted(self._ids)

    def cell_ids(self, donor, operator):
        return list(self._ids[(str(donor), int(operator))])


class FakeScores:
    def __init__(self, _path):
        self.manifest = {
            "score_archive_root_sha256": "d" * 64,
            "teacher_archive_root_sha256": "a" * 64,
            "derivation_root_sha256": "e" * 64,
        }
        self.program_ids = ["P1", "P2"]
        self._scores = {
            ("D1", 0): np.array([[1.0, 2.0], [3.0, 4.0]]),
            ("D1", 1): np.array([[5.0, 6.0]]),
            ("D2", 1): np.array([[7.0, 8.0], [9.0, 10.0]]),
        }

    def strata(self):
        return sorted(self._scores)

    def load(self, donor, operator):
        return self._scores[(str(donor), int(operator))]


class FakeExpression:
    def __init__(self, *, cross_source=False):
        # 42 operators are required by the reconstruction store, but only 0/1
        # occur in the fixture strata.
        self.observation = {
            "states": np.ones((42, 4), dtype=np.uint8),
            "sha256": "f" * 64,
        }
        # address 3 is structurally unmeasured in operator 0, measured in op1.
        self.observation["states"][0, 3] = 0
        self.cross_source = cross_source

    def load_sparse_stratum(self, *, donor_id, operator_index, expected_cell_ids):
        key = (str(donor_id), int(operator_index))
        if key == ("D1", 0):
            x = np.array([[0.0, 2.0, 0.0, 0.0],
                          [0.0, 0.0, 3.0, 0.0]])
            source = "S1"
        elif key == ("D1", 1):
            x = np.array([[4.0, 0.0, 0.0, 5.0]])
            source = "S2" if self.cross_source else "S1"
        elif key == ("D2", 1):
            x = np.array([[1.0, 1.0, 0.0, 0.0],
                          [2.0, 0.0, 1.0, 0.0]])
            source = "S2"
        else:
            raise KeyError(key)
        ids = {
            ("D1", 0): ["a", "b"],
            ("D1", 1): ["c"],
            ("D2", 1): ["d", "e"],
        }[key]
        assert list(expected_cell_ids) == ids
        return {
            "canonical_cell_id": ids,
            "expression_csr": sp.csr_matrix(x, dtype=np.float32),
            "source": source,
        }

    def release_operator(self, _operator):
        pass


def test_sparse_crossproducts_equal_dense_weighted_algebra() -> None:
    x = sp.csr_matrix(np.array([[0.0, 2.0, 0.0],
                                [3.0, 0.0, 1.0]]))
    scores = np.array([[1.0, 2.0], [4.0, 5.0]])
    weights = np.array([0.25, 0.75])
    sum_x, sum_sx = store._sparse_crossproducts(x, scores, weights)
    expected_x = weights @ x.toarray()
    expected_sx = (scores * weights[:, None]).T @ x.toarray()
    assert np.allclose(sum_x.toarray().reshape(-1), expected_x)
    assert np.allclose(sum_sx.toarray(), expected_sx)


def test_materialized_store_reconstructs_masked_score_moments_exactly(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(store, "ArchivedStrataSource", FakeTeacher)
    monkeypatch.setattr(store, "ArchivedScoreSource", FakeScores)
    outdir = tmp_path / "store"
    payload = store.materialize_molecular_store(
        teacher_archive_dir=tmp_path / "teacher",
        score_archive_dir=tmp_path / "scores",
        score_archive_root_sha256="d" * 64,
        expression_reader=FakeExpression(),
        expression_location_manifest_sha256="1" * 64,
        population_audit_root_sha256="2" * 64,
        output_dir=outdir,
    )
    assert payload["rows"] == 5
    assert payload["strata"] == 3
    assert payload["donors"] == 2
    assert payload["operators"] == 2

    obs = FakeExpression().observation["states"]
    opened = store.MolecularStore(outdir, obs)
    idx = opened.stratum_indices(donor="D1")
    moments = opened.reconstruct_masked_score_moments(idx)

    # D1 has two operators. With donor-primary weighting each operator carries
    # mass 1/2. Address 3 is unmeasured in op0 and measured in op1, so its mass
    # is exactly 1/2 instead of 1.
    assert moments["mass"][0] == pytest.approx(1.0)
    assert moments["mass"][3] == pytest.approx(0.5)

    # P1 score sum in D1/op0: cell weight 1/(2*2)=1/4 => (1+3)/4 = 1.
    # D1/op1: one cell weight 1/(2*1)=1/2 => 5/2 = 2.5.
    # Address 0 measured in both operators => 3.5.
    assert moments["sum_s"][0, 0] == pytest.approx(3.5)
    # Address 3 only op1 => 2.5.
    assert moments["sum_s"][0, 3] == pytest.approx(2.5)


def test_measured_all_zero_address_remains_reconstructibly_estimable(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(store, "ArchivedStrataSource", FakeTeacher)
    monkeypatch.setattr(store, "ArchivedScoreSource", FakeScores)
    outdir = tmp_path / "store"
    store.materialize_molecular_store(
        teacher_archive_dir=tmp_path / "teacher",
        score_archive_dir=tmp_path / "scores",
        score_archive_root_sha256="d" * 64,
        expression_reader=FakeExpression(),
        expression_location_manifest_sha256="1" * 64,
        population_audit_root_sha256="2" * 64,
        output_dir=outdir,
    )
    opened = store.MolecularStore(outdir, FakeExpression().observation["states"])
    donor_x, donor_sx = opened.donor_sparse("D1")
    # Address 0 is measured for D1 but has a numeric zero in one of its strata.
    # Sparse storage can omit numeric zeros without losing measuredness, because
    # mass is reconstructed from the observation mask.
    moments = opened.reconstruct_masked_score_moments(
        opened.stratum_indices(donor="D1"))
    assert moments["mass"][0] > 0
    assert donor_x.shape == (1, 4)
    assert donor_sx.shape == (2, 4)


def test_donor_crossing_source_families_is_a_stop(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(store, "ArchivedStrataSource", FakeTeacher)
    monkeypatch.setattr(store, "ArchivedScoreSource", FakeScores)
    with pytest.raises(ValueError, match="crosses sources"):
        store.materialize_molecular_store(
            teacher_archive_dir=tmp_path / "teacher",
            score_archive_dir=tmp_path / "scores",
            score_archive_root_sha256="d" * 64,
            expression_reader=FakeExpression(cross_source=True),
            expression_location_manifest_sha256="1" * 64,
            population_audit_root_sha256="2" * 64,
            output_dir=tmp_path / "bad",
        )


def test_store_hash_tamper_is_detected(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(store, "ArchivedStrataSource", FakeTeacher)
    monkeypatch.setattr(store, "ArchivedScoreSource", FakeScores)
    outdir = tmp_path / "store"
    payload = store.materialize_molecular_store(
        teacher_archive_dir=tmp_path / "teacher",
        score_archive_dir=tmp_path / "scores",
        score_archive_root_sha256="d" * 64,
        expression_reader=FakeExpression(),
        expression_location_manifest_sha256="1" * 64,
        population_audit_root_sha256="2" * 64,
        output_dir=outdir,
    )
    donor = payload["donor_entries"][0]
    path = outdir / donor["sum_sx_file"]
    with path.open("ab") as handle:
        handle.write(b"tamper")
    with pytest.raises(ValueError, match=store.STOP_STORE_DRIFT):
        store.verify_molecular_store(outdir)


def test_existing_store_is_never_overwritten(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(store, "ArchivedStrataSource", FakeTeacher)
    monkeypatch.setattr(store, "ArchivedScoreSource", FakeScores)
    outdir = tmp_path / "store"
    outdir.mkdir()
    with pytest.raises(FileExistsError):
        store.materialize_molecular_store(
            teacher_archive_dir=tmp_path / "teacher",
            score_archive_dir=tmp_path / "scores",
            score_archive_root_sha256="d" * 64,
            expression_reader=FakeExpression(),
            expression_location_manifest_sha256="1" * 64,
            population_audit_root_sha256="2" * 64,
            output_dir=outdir,
        )
