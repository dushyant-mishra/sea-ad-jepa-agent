from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _registry():
    return json.loads(
        (ROOT / "results/v64/V64_OPEN_REGULATORY_RESOURCE_REGISTRY_V1.json").read_text()
    )


def test_resource_registry_separates_access_from_terms():
    p = _registry()
    for r in p["resources"]:
        assert "access" in r and "license_terms" in r
    assert "PUBLIC_DOWNLOAD_IMPLIES_OPEN_LICENSE" in p["forbidden_assumptions"]


def test_nott_and_screen_are_not_overclaimed_as_open_licensed_data():
    rows = {r["id"]: r for r in _registry()["resources"]}
    assert rows["NOTT_PROCESSED_REGULATORY_FILES"]["license_terms"] == "TERMS_UNKNOWN"
    assert rows["ENCODE_SCREEN_CCRE"]["license_terms"] == "DATA_TERMS_NOT_VERIFIED"


def test_verified_open_terms_are_explicit_only_where_supported():
    rows = {r["id"]: r for r in _registry()["resources"]}
    assert rows["FANTOM5_CAGE"]["license_terms"] == "CC_BY_4_0"
    assert rows["EQTL_CATALOGUE"]["license_terms"] == "CC_BY_4_0_DATA"
    assert rows["SCARLINK_CODE"]["license_terms"] == "MIT"
    assert rows["SCENT_CODE"]["license_terms"] == "MIT"


def test_registry_does_not_authorize_ingestion_or_training():
    p = _registry()
    assert p["governance"]["data_ingested"] is False
    assert p["governance"]["training"] == "OFF"
