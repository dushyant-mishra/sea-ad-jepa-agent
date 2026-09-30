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


def test_resource_fetch_manifest_never_claims_missing_bytes():
    p=json.loads((ROOT/"results/v64/V64_OPEN_RESOURCE_FETCH_MANIFEST_V1.json").read_text())
    assert p["status"]=="SOURCE_URLS_VERIFIED__BYTES_NOT_YET_IN_CHAT_CUSTODY"
    assert p["governance"]["data_ingestion_completed"] is False
    for r in p["resources"]:
        assert r["bytes_in_chat_custody"] is False
        assert r["sha256"] is None
        urls = ([r["download_url"]] if "download_url" in r else r.get("download_urls", []))
        assert urls
        assert all(u.startswith("https://") for u in urls)


def test_gencode_is_annotation_base_and_screen_terms_remain_conservative():
    p=json.loads((ROOT/"results/v64/V64_OPEN_RESOURCE_FETCH_MANIFEST_V1.json").read_text())
    rows={r["id"]:r for r in p["resources"]}
    assert rows["GENCODE_V50_COMPREHENSIVE_CHR_GTF"]["genome_build"]=="GRCh38.p14"
    assert rows["SCREEN_REGISTRY_V4_GRCH38_PLS"]["data_license_status"]=="NOT_VERIFIED"
