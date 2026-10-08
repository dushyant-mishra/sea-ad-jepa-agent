from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_address_identity_contract_forbids_address_gene_collapse():
    t=(ROOT/"docs/agent/V64_ADDRESS_GENE_PROMOTER_IDENTITY_CONTRACT_20260930.md").read_text()
    assert "17,186 common measured addresses" in t
    assert "17,186 genes" in t
    assert "may not be used as" in t
    assert "address→gene bridge" in t


def test_resource_fetch_manifest_separates_automated_fetch_from_manual_custody():
    p=json.loads((ROOT/"results/v64/V64_OPEN_RESOURCE_FETCH_MANIFEST_V1.json").read_text())
    assert p["status"]=="AUTOMATED_FETCH_SCOPE_SEPARATED_FROM_MANUAL_CHAT_CUSTODY"
    assert p["governance"]["training"]=="OFF"
    assert p["governance"]["phaseB"]=="STOPPED"

    assert p["resources"]
    for r in p["resources"]:
        assert r["automated_fetch"] is True
        urls = ([r["download_url"]] if "download_url" in r else r.get("download_urls", []))
        assert urls
        assert all(u.startswith("https://") for u in urls)

    manual={r["id"]:r for r in p["manual_custody_resources"]}
    assert manual["DONG_ROUSSOS_2024_SUPPLEMENTARY_DATA_8"]["automated_fetch"] is False
    assert manual["DONG_ROUSSOS_2024_SUPPLEMENTARY_DATA_10"]["automated_fetch"] is False
    assert manual["DONG_ROUSSOS_2024_SUPPLEMENTARY_DATA_8"]["sha256"]=="eb3c2e0eaf055bac3954802497cbdd07ccc65638ae361e1cf9af10668f224a74"
    assert manual["DONG_ROUSSOS_2024_SUPPLEMENTARY_DATA_10"]["sha256"]=="c2005fb8947b4352450a9a86f297673cce5350aab1b2ac69fe3949317c4f1f59"


def test_gencode_is_annotation_base_and_screen_terms_remain_conservative():
    p=json.loads((ROOT/"results/v64/V64_OPEN_RESOURCE_FETCH_MANIFEST_V1.json").read_text())
    rows={r["id"]:r for r in p["resources"]}
    assert rows["GENCODE_V50_COMPREHENSIVE_CHR_GTF"]["genome_build"]=="GRCh38.p14"
    assert rows["SCREEN_REGISTRY_V4_GRCH38_PLS"]["data_license_status"]=="NOT_VERIFIED"
