import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_routeb_blacklist_amendment_is_pinned_and_prospective():
    p = ROOT / "results/v64/V72_ROUTEB_HG38_BLACKLIST_PROSPECTIVE_AMENDMENT_V1.json"
    obj = json.loads(p.read_text())
    assert obj["status"].startswith("PROSPECTIVE")
    assert obj["decision"] == "APPLY_ENCODE_BLACKLIST_V2_TO_ROUTE_B_CONSENSUS_PEAK_CONSTRUCTION"
    r = obj["resource"]
    assert r["release_tag"] == "v2.0"
    assert r["release_commit"] == "f4a45ab5b52d427a8689a1a143e8504e1cba5962"
    assert r["git_blob_sha1"] == "a4ec858104cbe907e9056e873cec278cee11066a"
    assert r["expected_decompressed_region_count"] == 636
    assert r["sha256_status"].startswith("MUST_BE_COMPUTED")


def test_successor_dockerfile_pins_cistarget_commit_and_refuses_unbound_binaries():
    p = ROOT / "docker/scenicplus/Dockerfile.successor_pinned"
    s = p.read_text()
    assert "304d5dc1b15e5c923908a50a1ec291c3faaccf9c" in s
    assert "CREATE_CISTARGET_DATABASES_REF=master" not in s
    assert "REQUIRED_FROM_VALIDATED_IMAGE" in s
    assert 'test "${CBUST_SHA256}" != "REQUIRED_FROM_VALIDATED_IMAGE"' in s
    assert 'test "${LIFTOVER_SHA256}" != "REQUIRED_FROM_VALIDATED_IMAGE"' in s
    assert 'test "${BIGWIGAVERAGEOVERBED_SHA256}" != "REQUIRED_FROM_VALIDATED_IMAGE"' in s
    for digest in [
        "e06e80ba6a128ba5c2f07afbc324660b621cfb7ba9f488fcb3a8b2a24516cb81",
        "e16a899829d7959b219173762ca069a0873ff1244b80cb089c7307404909672a",
        "5873fbaadcec2006bebf9f6473b1de1068cbdd83ef3fb0e1630ab6b7ca534b13",
        "0bd6c561d3fb49330885349198cf451322b9635e01429c2d8cdee9b387619c84",
        "1739638242593e5e8305465633c013c89c0ae4daa87ad3ebc1d31654de008921",
    ]:
        assert digest in s


def test_historical_validated_recipe_is_not_rewritten():
    old = (ROOT / "docker/scenicplus/Dockerfile").read_text()
    new = (ROOT / "docker/scenicplus/Dockerfile.successor_pinned").read_text()
    assert "CREATE_CISTARGET_DATABASES_REF=master" in old
    assert "CREATE_CISTARGET_DATABASES_REF=master" not in new


def test_g2_gap_contract_forbids_posthoc_v2_thresholding():
    p = ROOT / "results/v64/V72_STAGE4_G2_SPECIFICATION_GAP_CONTRACT_V1.json"
    obj = json.loads(p.read_text())
    assert obj["status"].startswith("OPEN")
    forbidden = " ".join(obj["forbidden_inputs_to_semantic_choice"])
    assert "V2 biology G2 pass rate" in forbidden
    assert "pending HIDDEN_CONFOUND_K curve" in forbidden
    assert obj["current_action"] == "NO_STAGE4_AUTHORIZATION_CHANGE"
