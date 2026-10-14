from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_relational_successor_disk_runner_v4 as D4


def _materialize_engine_tree(root: Path) -> None:
    for index, relative in enumerate(D4.FIT_ENGINE_FILES):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"engine-file-{index}\n", encoding="utf-8")


def test_phase1_api_still_has_no_controller_parameter():
    params = set(inspect.signature(D4.run_blinded_fit_phase).parameters)
    assert "controller_manifest_path" not in params
    assert "controller_manifest" not in params
    assert "controller" not in params


def test_fit_engine_identity_covers_the_science_critical_stack(tmp_path):
    _materialize_engine_tree(tmp_path)
    identity = D4.fit_engine_identity(tmp_path)
    assert tuple(identity) == D4.FIT_ENGINE_FILES
    assert all(len(value) == 64 for value in identity.values())


def test_fit_engine_identity_changes_if_any_bound_source_changes(tmp_path):
    _materialize_engine_tree(tmp_path)
    before = D4.fit_engine_identity(tmp_path)
    changed = tmp_path / D4.FIT_ENGINE_FILES[4]
    changed.write_text("mutated\n", encoding="utf-8")
    after = D4.fit_engine_identity(tmp_path)
    assert before != after
    assert before[D4.FIT_ENGINE_FILES[4]] != after[D4.FIT_ENGINE_FILES[4]]


def test_v4_document_rejects_engine_identity_mismatch_before_v3_receipt_parse(tmp_path, monkeypatch):
    _materialize_engine_tree(tmp_path)
    expected = D4.fit_engine_identity(tmp_path)
    bad = dict(expected)
    bad[D4.FIT_ENGINE_FILES[0]] = "0" * 64
    document = {
        "schema": D4.BLINDED_SCHEMA,
        "package_id": "pkg",
        "package_sha256": "a" * 64,
        "fit_engine_identity": bad,
        "fit_receipt": {},
        "authority": {},
    }
    called = {"v3": False}

    def forbidden(*args, **kwargs):
        called["v3"] = True
        raise AssertionError("V3 receipt parsing must not run after engine mismatch")

    monkeypatch.setattr(D4.V3, "_fit_receipt_from_document", forbidden)
    with pytest.raises(D4.DiskRunnerV4Error, match="fit-engine identity mismatch"):
        D4._fit_receipt_from_v4_document(document, object(), repo_root=tmp_path)
    assert called["v3"] is False


def test_adjudication_authenticates_engine_before_controller_read(monkeypatch, tmp_path):
    called = {"controller": False}

    def mismatch(**kwargs):
        raise D4.DiskRunnerV4Error("blinded receipt fit-engine identity mismatch: x")

    def forbidden_controller(_):
        called["controller"] = True
        raise AssertionError("controller truth must remain closed")

    monkeypatch.setattr(D4, "authenticate_blinded_phase_inputs", mismatch)
    monkeypatch.setattr(D4.V3, "_read_controller_json", forbidden_controller)
    fit_dir = tmp_path / "fit"
    fit_dir.mkdir()
    with pytest.raises(D4.DiskRunnerV4Error, match="fit-engine identity mismatch"):
        D4.adjudicate_frozen_blinded_phase(
            repo_root=tmp_path,
            binding_path=tmp_path / "binding.json",
            fit_dir=fit_dir,
            authenticated_package_sha256="a" * 64,
            blinded_receipt_path=tmp_path / "blind.json",
            expected_blinded_receipt_sha256="b" * 64,
            controller_manifest_path=tmp_path / "controller.json",
            output_path=tmp_path / "out.json",
        )
    assert called["controller"] is False


def test_v4_cli_requires_repo_root_for_blinded_fit():
    parser = D4._parser()
    args = parser.parse_args([
        "blinded-fit",
        "--repo-root", ".",
        "--binding", "binding.json",
        "--fit-dir", "fit",
        "--authenticated-package-sha256", "a" * 64,
        "--output", "blind.json",
    ])
    assert args.phase == "blinded-fit"
    assert args.repo_root == "."
