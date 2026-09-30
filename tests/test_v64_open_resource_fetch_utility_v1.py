from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def _load():
    p=ROOT/"scripts/v64/fetch_open_promoter_resources_v1.py"
    spec=importlib.util.spec_from_file_location("v64_fetch_open_resources",p)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_fetch_plan_is_exact_url_only_and_nonempty():
    m=_load()
    manifest=json.loads((ROOT/"results/v64/V64_OPEN_RESOURCE_FETCH_MANIFEST_V1.json").read_text())
    items=m.plan(manifest)
    assert len(items)>=7
    assert all(x["url"].startswith("https://") for x in items)
    assert all(x["resource_id"] for x in items)


def test_dry_run_does_not_download_or_authorize_training(capsys,tmp_path):
    m=_load()
    rc=m.main([
        "--manifest",str(ROOT/"results/v64/V64_OPEN_RESOURCE_FETCH_MANIFEST_V1.json"),
        "--outdir",str(tmp_path/"cache"),
        "--receipt",str(tmp_path/"receipt.json"),
    ])
    assert rc==0
    assert not (tmp_path/"cache").exists()
    assert not (tmp_path/"receipt.json").exists()
    out=json.loads(capsys.readouterr().out)
    assert out["download"] is False
    assert out["training_authorized"] is False


def test_safe_name_is_deterministic():
    m=_load()
    a=m._safe_name("SCREEN_REGISTRY_V4_GRCH38_PLS","https://downloads.wenglab.org/Registry-V4/GRCh38-cCREs.PLS.bed",1)
    b=m._safe_name("SCREEN_REGISTRY_V4_GRCH38_PLS","https://downloads.wenglab.org/Registry-V4/GRCh38-cCREs.PLS.bed",1)
    assert a==b
    assert a.endswith("GRCh38-cCREs.PLS.bed")
