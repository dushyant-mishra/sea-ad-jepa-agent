from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "scripts" / "v79"
sys.path.insert(0, str(HERE))

import prepare_v79_v2_core_engineering_benchmark as P  # noqa: E402
import v79_v2_core_fit_contract as FC  # noqa: E402
import v79_v2_core_fit_custody as C  # noqa: E402
import v79_v2_core_fit_runner as R  # noqa: E402


def _canonical(obj):
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _digest(base: Path) -> str:
    h = hashlib.sha256()
    for p in sorted((p for p in base.rglob("*") if p.is_file()), key=lambda x: x.relative_to(base).as_posix()):
        rel = p.relative_to(base).as_posix()
        h.update(rel.encode()); h.update(b"\0"); h.update(hashlib.sha256(p.read_bytes()).digest()); h.update(b"\0")
    return h.hexdigest()


def _make(tmp_path: Path):
    cdir = tmp_path / "custody"; fit_root = cdir / C.FIT_ROOT_NAME; fit_root.mkdir(parents=True)
    contract = json.loads((ROOT / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json").read_text())
    view = P.build_fit_contract_view(contract)
    view_raw = FC.canonical_bytes(view); (cdir / C.FIT_VIEW_NAME).write_bytes(view_raw)
    view_sha = hashlib.sha256(view_raw).hexdigest()
    oid = "0123456789ab"
    manifest_raw = _canonical({"schema":"V79_V2_CORE_BLINDED_WORLD_DATA_MANIFEST_V1","opaque_world_id":oid,
                               "final_contract_sha256":FC.SOURCE_CONTRACT_SHA256,"benchmark_run":False,
                               "qualification_fits_run":0,"training_authorized":False,"generated_outputs":{}})
    wdir = fit_root / oid; wdir.mkdir(); (wdir / "manifest.json").write_bytes(manifest_raw)
    msha = hashlib.sha256(manifest_raw).hexdigest()
    index = {"schema":"V79_V2_CORE_BLINDED_FIT_INDEX_V1","final_contract_sha256":FC.SOURCE_CONTRACT_SHA256,
             "benchmark_run":False,"qualification_fits_run":0,"training_authorized":False,"world_count":1,
             "worlds":[{"opaque_world_id":oid,"manifest_path":f"{oid}/manifest.json","manifest_sha256":msha}]}
    index_raw = _canonical(index); (fit_root / "V79_V2_CORE_BLINDED_FIT_INDEX_V1.json").write_bytes(index_raw)
    isha = hashlib.sha256(index_raw).hexdigest()
    ledger = []
    for g in (0,1):
        for part in ("detection","positive"):
            ledger.append({"fit_id":R.fit_identity(oid,msha,part,g),"primary_seed":100+g+(0 if part=="detection" else 10)})
    receipt = {"schema":C.PREP_SCHEMA,"executor_code_head":"a"*40,"source_contract_sha256":FC.SOURCE_CONTRACT_SHA256,
               "fit_contract_view_path":C.FIT_VIEW_NAME,"fit_contract_view_sha256":view_sha,
               "execution_mode":"ENGINEERING_BENCHMARK","engineering_seed_root":view["seeds"]["engineering_benchmark_root"],
               "root_manifest_sha256":"b"*64,"blinded_index_sha256":isha,"blinded_directory_digest":_digest(fit_root),
               "selected_opaque_world_id":oid,"selected_world_manifest_sha256":msha,"fit_seed_ledger":ledger,
               "benchmark_fit_count":4,"benchmark_run":False,"qualification_fits_run":0,"scoring_run":False,
               "fit_truth_accessed":False,"training_authorized":False}
    raw = _canonical(receipt); (cdir / C.PREP_RECEIPT_NAME).write_bytes(raw)
    return cdir, hashlib.sha256(raw).hexdigest(), receipt


def test_fit_only_custody_roundtrip_has_no_controller_files(tmp_path):
    cdir, rsha, receipt = _make(tmp_path)
    c = C.load_engineering_custody(cdir, expected_prep_receipt_sha256=rsha)
    assert c.selected_opaque_world_id == receipt["selected_opaque_world_id"]
    assert len(c.seed_by_fit_id) == 4
    assert set(p.name for p in cdir.iterdir()) == {C.PREP_RECEIPT_NAME, C.FIT_VIEW_NAME, C.FIT_ROOT_NAME}
    assert not (cdir / "controller_truth").exists()
    assert not (cdir / "V79_V2_CORE_WORLD_SET_MANIFEST_V1.json").exists()


def test_custody_refuses_extra_controller_surface(tmp_path):
    cdir, rsha, _ = _make(tmp_path)
    (cdir / "controller_truth").mkdir()
    with pytest.raises(C.FitCustodyRefused, match="top-level"):
        C.load_engineering_custody(cdir, expected_prep_receipt_sha256=rsha)


def test_custody_refuses_receipt_or_blinded_index_tamper(tmp_path):
    cdir, rsha, _ = _make(tmp_path)
    rp = cdir / C.PREP_RECEIPT_NAME; rp.write_bytes(rp.read_bytes() + b"x")
    with pytest.raises(C.FitCustodyRefused, match="receipt hash"):
        C.load_engineering_custody(cdir, expected_prep_receipt_sha256=rsha)
    cdir2, rsha2, _ = _make(tmp_path / "second")
    ip = cdir2 / C.FIT_ROOT_NAME / "V79_V2_CORE_BLINDED_FIT_INDEX_V1.json"; ip.write_bytes(ip.read_bytes() + b"x")
    with pytest.raises(C.FitCustodyRefused, match="index|digest"):
        C.load_engineering_custody(cdir2, expected_prep_receipt_sha256=rsha2)


def test_custody_refuses_seed_ledger_not_matching_exact_four_fit_ids(tmp_path):
    cdir, _, receipt = _make(tmp_path)
    receipt["fit_seed_ledger"][0]["fit_id"] = "0"*64
    raw = _canonical(receipt); (cdir / C.PREP_RECEIPT_NAME).write_bytes(raw)
    with pytest.raises(C.FitCustodyRefused, match="seed-ledger"):
        C.load_engineering_custody(cdir, expected_prep_receipt_sha256=hashlib.sha256(raw).hexdigest())
