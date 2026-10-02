import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_routeb_successor_contract_binds_fragment_receipts_cryptographically():
    p = ROOT / "results/v64/V72_ROUTEB_PROVENANCE_BINDING_SUCCESSOR_CONTRACT_V1.json"
    obj = json.loads(p.read_text())
    req = " ".join(obj["fragment_custody"]["required"])
    assert "SHA-256 equals completed QC receipt fragment SHA-256" in req
    assert "full/non-partial" in req
    assert obj["governance"]["routeB_pseudobulk"].startswith("NOT_AUTHORIZED")


def test_routeb_consensus_contract_binds_auxiliary_bytes_not_just_paths():
    p = ROOT / "results/v64/V72_ROUTEB_PROVENANCE_BINDING_SUCCESSOR_CONTRACT_V1.json"
    obj = json.loads(p.read_text())
    req = " ".join(obj["consensus_auxiliary_inputs"]["required"])
    assert "chromsizes path, bytes and SHA-256" in req
    assert "blacklist path, bytes and SHA-256" in req
    assert "Paths are locators, not identities" in obj["consensus_auxiliary_inputs"]["rule"]


def test_routeb_blacklist_authority_is_versioned():
    p = ROOT / "results/v64/V72_ROUTEB_PROVENANCE_BINDING_SUCCESSOR_CONTRACT_V1.json"
    obj = json.loads(p.read_text())
    assert obj["blacklist_authority"].endswith(
        "V72_ROUTEB_HG38_BLACKLIST_PROSPECTIVE_AMENDMENT_V1.json"
    )
