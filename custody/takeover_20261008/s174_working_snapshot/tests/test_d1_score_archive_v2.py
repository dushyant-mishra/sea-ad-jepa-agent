from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import d1_score_archive_v2 as scores  # noqa: E402


class FakeTeacherSource:
    def __init__(self, _path):
        self.dimension = 3
        self.manifest = {
            "archive_root_sha256": "a" * 64,
            "teacher_checkpoint_sha256": "b" * 64,
            "readout_contract_sha256": "c" * 64,
        }
        self._data = {
            ("D1", 0): np.array([[2.0, 3.0, 4.0], [-1.0, 0.0, 5.0]], dtype=np.float32),
            ("D2", 1): np.array([[1.0, -5.0, 12.0]], dtype=np.float32),
        }

    def strata(self):
        return sorted(self._data)

    def load(self, donor, operator):
        arr = self._data[(str(donor), int(operator))]
        return arr, np.ones(len(arr), dtype=np.float64)


def derivation():
    return {
        "D": 3,
        "mean": [0.0, 0.0, 0.0],
        "eigenvalues": [9.0, 4.0, 4.0],
        "eigenvectors_leading": [
            [-1.0, 0.0, 0.0],
            [ 0.0, 1.0, 0.0],
            [ 0.0, 0.0, 1.0],
        ],
        "degeneracy_blocks": [[0], [1, 2]],
        "real_overlap_lower": [0.9, 0.9, 0.95],
        "null_overlap_upper": [0.1, 0.2, 0.3],
    }


def test_score_archive_materializes_isolated_and_rotation_invariant_scores(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(scores, "ArchivedStrataSource", FakeTeacherSource)
    outdir = tmp_path / "scores"
    manifest = scores.materialize_score_archive(
        teacher_archive_dir=tmp_path / "teacher",
        teacher_archive_root_sha256="a" * 64,
        derivation=derivation(),
        derivation_root_sha256="d" * 64,
        output_dir=outdir,
    )
    assert manifest["program_ids"] == ["D1OBJ-B0-R1-1", "D1OBJ-B1-R2-3"]
    source = scores.ArchivedScoreSource(outdir)
    first = np.asarray(source.load("D1", 0))
    # isolated axis keeps global sign: x=2 -> -2.
    assert first[0, 0] == pytest.approx(-2.0)
    # degenerate block score is sqrt(3^2+4^2)=5.
    assert first[0, 1] == pytest.approx(5.0)
    second = np.asarray(source.load("D2", 1))
    assert second[0, 1] == pytest.approx(13.0)


def test_score_archive_binds_exact_teacher_and_derivation_roots(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(scores, "ArchivedStrataSource", FakeTeacherSource)
    outdir = tmp_path / "scores"
    manifest = scores.materialize_score_archive(
        teacher_archive_dir=tmp_path / "teacher",
        teacher_archive_root_sha256="a" * 64,
        derivation=derivation(),
        derivation_root_sha256="d" * 64,
        output_dir=outdir,
    )
    checked = scores.verify_score_archive(
        outdir,
        expected_teacher_archive_root="a" * 64,
        expected_derivation_root="d" * 64,
    )
    assert checked["terminal"] == "PASS_D1_V2_SCORE_ARCHIVE"
    assert checked["programs"] == 2
    with pytest.raises(ValueError, match=scores.STOP_SCORE_ARCHIVE_DRIFT):
        scores.verify_score_archive(
            outdir, expected_teacher_archive_root="f" * 64)


def test_score_shard_tamper_is_detected(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(scores, "ArchivedStrataSource", FakeTeacherSource)
    outdir = tmp_path / "scores"
    manifest = scores.materialize_score_archive(
        teacher_archive_dir=tmp_path / "teacher",
        teacher_archive_root_sha256="a" * 64,
        derivation=derivation(),
        derivation_root_sha256="d" * 64,
        output_dir=outdir,
    )
    shard = outdir / manifest["entries"][0]["score_file"]
    arr = np.load(shard, allow_pickle=False)
    changed = np.asarray(arr).copy()
    changed[0, 0] += 0.25
    np.save(shard, changed, allow_pickle=False)
    with pytest.raises(ValueError, match=scores.STOP_SCORE_ARCHIVE_DRIFT):
        scores.verify_score_archive(outdir)


def test_existing_score_archive_is_never_overwritten(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(scores, "ArchivedStrataSource", FakeTeacherSource)
    outdir = tmp_path / "scores"
    outdir.mkdir()
    with pytest.raises(FileExistsError):
        scores.materialize_score_archive(
            teacher_archive_dir=tmp_path / "teacher",
            teacher_archive_root_sha256="a" * 64,
            derivation=derivation(),
            derivation_root_sha256="d" * 64,
            output_dir=outdir,
        )
