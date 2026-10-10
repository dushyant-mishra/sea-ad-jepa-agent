import json
from pathlib import Path
import pytest

from scripts.v79.build_v79_factorial_worlds import validate_arm_manifest, manifest_hash
from scripts.v79.run_v79_factorial_tournament import (
    FROZEN_V78_BASE_SHA,
    preexecution_gate,
    falsification_blockers,
    terminal_ruling,
    make_receipt,
    run_preexecution_only,
)


def manifest_dict():
    return {
        "arm_names": ["H0","H1","H2","H3","C_OBS","C_BIO"],
        "biology_seed": 101, "observation_seed": 202, "counterfactual_biology_seed": 303,
        "crossing_seed": 404, "cell_count": 2400, "donor_count": 12,
        "balancing_rule": "BALANCED_WITHIN_BROAD_CLASS",
        "h2_realization_family": "independent_thinning", "h3_realization_family": "independent_thinning",
        "endpoint_version": "V79_FACTORIAL_ENDPOINTS_V1", "training_authorized": False,
    }


def good_contract():
    m = validate_arm_manifest(manifest_dict())
    return {
        "v78_base_sha": FROZEN_V78_BASE_SHA,
        "authority_hashes": {
            "biology": {"expected": "bio123", "actual": "bio123"},
            "observation": {"expected": "obs123", "actual": "obs123"},
            "evaluation_universe": {"expected": "uni123", "actual": "uni123"},
        },
        "preregistered_manifest_hash": manifest_hash(m),
        "test_or_morabito_accessed": False,
        "pathology_accessed": False,
        "target_discovery_modified": False,
        "post_outcome_arm_mutation": False,
        "training_authorized": False,
    }


def test_gate_ready_only_with_zero_blockers():
    rec = preexecution_gate(good_contract(), manifest_dict())
    assert rec["status"] == "READY"
    assert rec["blockers"] == []
    assert rec["training_authorized"] is False


@pytest.mark.parametrize("mutator,expected", [
    (lambda c: c.update(v78_base_sha="moved"), "frozen_v78_base_moved"),
    (lambda c: c["authority_hashes"]["biology"].update(actual="wrong"), "authority_hash_mismatch:biology"),
    (lambda c: c.update(preregistered_manifest_hash="wrong"), "arm_manifest_hash_mismatch"),
    (lambda c: c.update(test_or_morabito_accessed=True), "protected_data_access"),
    (lambda c: c.update(pathology_accessed=True), "pathology_access"),
    (lambda c: c.update(target_discovery_modified=True), "target_discovery_modified"),
    (lambda c: c.update(post_outcome_arm_mutation=True), "post_outcome_arm_mutation"),
    (lambda c: c.update(training_authorized=True), "training_authorization_contamination"),
])
def test_gate_custody_and_unauthorized_mutations_block(mutator, expected):
    c = good_contract(); mutator(c)
    rec = preexecution_gate(c, manifest_dict())
    assert rec["status"] == "BLOCKED"
    assert expected in rec["blockers"]


def good_checks():
    return {
        "within_class_geometry_plausible": True,
        "degree_transitivity_preserved": True,
        "biology_independent_of_source": True,
        "detected_counts_emergent": True,
        "c_obs_truth_identical": True,
        "c_bio_truth_distinct": True,
        "identity_firewall_clean": True,
        "manifest_unchanged": True,
        "protected_data_clean": True,
        "training_authorized_false": True,
    }


@pytest.mark.parametrize("key", list(good_checks().keys()))
def test_each_falsification_rule_is_verdict_bearing(key):
    checks = good_checks(); checks[key] = False
    blockers = falsification_blockers(checks)
    assert key in blockers


def evidence():
    return {
        "H1": {"biology_endpoint_pass": True, "observer_endpoint_pass": False, "joint_adequate": False},
        "H2": {"biology_endpoint_pass": False, "observer_endpoint_pass": True, "joint_adequate": False},
        "H3": {"joint_adequate": True},
    }


def test_terminal_ruling_can_recommend_family_but_never_training():
    ruling = terminal_ruling(evidence(), good_checks(), adequacy_pass=True)
    assert ruling["mechanism_family_ruling"] == "BOTH_AND_INTERACTION"
    assert ruling["training_authorized"] is False
    assert ruling["v78_retuning_authorized"] is False
    assert ruling["synthetic_arm_promoted"]["authority"] == "NOT_TRAINING_AUTHORITY"


def test_terminal_ruling_unresolved_on_any_falsification():
    checks = good_checks(); checks["c_obs_truth_identical"] = False
    ruling = terminal_ruling(evidence(), checks, adequacy_pass=True)
    assert ruling["mechanism_family_ruling"] == "FAMILY_UNRESOLVED"
    assert ruling["synthetic_arm_promoted"] is None


def test_receipt_schema_has_lineage_manifest_seeds_endpoint_and_false_flags():
    m = validate_arm_manifest(manifest_dict())
    ctx = good_contract()
    rec = make_receipt("SCORE", ctx, m, {"x": 1})
    assert rec["v78_base_sha"] == FROZEN_V78_BASE_SHA
    assert rec["manifest_hash"] == manifest_hash(m)
    assert rec["seed_set"] == {"biology":101,"observation":202,"counterfactual_biology":303,"crossing":404}
    assert rec["endpoint_version"] == "V79_FACTORIAL_ENDPOINTS_V1"
    for key in ["training_authorized","v78_retuning_authorized","test_or_morabito_accessed","pathology_accessed","target_discovery_modified"]:
        assert rec[key] is False


def test_preexecution_only_writes_gate_and_manifest_but_no_scientific_outputs(tmp_path):
    m = manifest_dict(); c = good_contract()
    result = run_preexecution_only(c, m, tmp_path)
    assert result["status"] == "READY"
    names = {p.name for p in tmp_path.iterdir()}
    assert names == {"V79_FACTORIAL_PREEXECUTION_GATE_V1.json", "V79_FACTORIAL_ARM_MANIFEST_V1.json"}
    assert not any("SCORE" in n or "RULING" in n for n in names)
    gate = json.loads((tmp_path / "V79_FACTORIAL_PREEXECUTION_GATE_V1.json").read_text())
    assert gate["training_authorized"] is False


def test_authority_file_bytes_override_self_declared_actual_hashes(tmp_path):
    from hashlib import sha256
    from scripts.v79.run_v79_factorial_tournament import bind_authority_file_hashes
    bio = tmp_path / "bio.json"; obs = tmp_path / "obs.json"
    bio.write_text('{"schema":"BIO"}\n'); obs.write_text('{"schema":"OBS"}\n')
    c = good_contract()
    c["authority_hashes"]["biology"] = {"expected": sha256(bio.read_bytes()).hexdigest(), "actual": "forged"}
    c["authority_hashes"]["observation"] = {"expected": sha256(obs.read_bytes()).hexdigest(), "actual": "forged"}
    bound = bind_authority_file_hashes(c, {"biology": bio, "observation": obs})
    assert bound["authority_hashes"]["biology"]["actual"] == sha256(bio.read_bytes()).hexdigest()
    assert bound["authority_hashes"]["observation"]["actual"] == sha256(obs.read_bytes()).hexdigest()
    assert preexecution_gate(bound, manifest_dict())["status"] == "READY"


def test_bind_authority_file_hashes_supports_additional_custody_inputs(tmp_path):
    from hashlib import sha256
    from scripts.v79.run_v79_factorial_tournament import bind_authority_file_hashes
    p = tmp_path / "registry.csv"; p.write_bytes(b"registry-bytes\n")
    c = good_contract()
    c["authority_hashes"]["registry"] = {"expected": sha256(p.read_bytes()).hexdigest(), "actual": "quoted"}
    bound = bind_authority_file_hashes(c, {"registry": p})
    assert bound["authority_hashes"]["registry"]["actual"] == sha256(p.read_bytes()).hexdigest()


def test_cli_accepts_additional_named_authority_files_and_authenticates_bytes(tmp_path):
    from hashlib import sha256
    from scripts.v79.run_v79_factorial_tournament import main
    manifest = tmp_path / "manifest.json"; manifest.write_text(json.dumps(manifest_dict()))
    bio = tmp_path / "bio.json"; bio.write_text('{}')
    obs = tmp_path / "obs.json"; obs.write_text('{}')
    registry = tmp_path / "registry.csv"; registry.write_bytes(b'registry-bytes\n')
    c = good_contract()
    c["authority_hashes"]["biology"] = {"expected": sha256(bio.read_bytes()).hexdigest(), "actual": "quoted"}
    c["authority_hashes"]["observation"] = {"expected": sha256(obs.read_bytes()).hexdigest(), "actual": "quoted"}
    c["authority_hashes"]["registry"] = {"expected": sha256(registry.read_bytes()).hexdigest(), "actual": "quoted"}
    custody = tmp_path / "custody.json"; custody.write_text(json.dumps(c))
    out = tmp_path / "out"
    rc = main(["--manifest",str(manifest),"--custody",str(custody),
               "--biology-authority",str(bio),"--observation-authority",str(obs),
               "--authority-file",f"registry={registry}","--out",str(out),"--preexecution-only"])
    assert rc == 0
    gate = json.loads((out / "V79_FACTORIAL_PREEXECUTION_GATE_V1.json").read_text())
    assert gate["status"] == "READY"


def test_preexecution_gate_receipt_carries_authenticated_authority_hashes():
    c = good_contract()
    rec = preexecution_gate(c, manifest_dict())
    assert rec["authority_hashes"] == c["authority_hashes"]
