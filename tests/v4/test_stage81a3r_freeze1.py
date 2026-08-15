import importlib.util
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/v4/stage81a3r_freeze1.py"
SPEC = importlib.util.spec_from_file_location("stage81a3r_freeze1", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CONFIG = yaml.safe_load((ROOT / "configs/v4/stage81a3r_freeze1.yaml").read_text())


def assembled():
    return MODULE.assemble(ROOT, CONFIG)


def test_freeze1_contract_matches_accepted_counts_and_dimensions():
    contract, evidence, current_state, _ = assembled()
    assert contract["status"] == "STAGE81A3_FREEZE1_DECLARED"
    assert contract["foundation_molecular_space"]["universal_addresses"] == 41_238
    assert contract["scalar_observation_contract"]["scalar_observable_somewhere_in_train"] == 40_949
    assert contract["scalar_observation_contract"]["collision_only_scalar_unobservable"] == 289
    assert contract["molecular_ledger"]["d_gene"] == 160
    assert contract["global_state"]["d_global"] == 224
    assert evidence["frozen_a2r_semantic_hash"] == MODULE.EXPECTED_A2R_HASH
    assert evidence["validation"]["full_v4"]["new_a3r_failures"] == 0
    assert evidence["validation"]["repository"]["known_historical_portability_failures"] == 28
    assert current_state["stage81a3_freeze1"] == "declared"
    assert current_state["stage81b"] == "not_started"


def test_historical_208_is_explicitly_superseded():
    contract, _, _, readout = assembled()
    historical = contract["qualification_evidence"]["historical_pre_range_closure"]
    assert historical == {
        "k_bulk": 208,
        "first_unsupported_block": [209, 224],
        "authority": "SUPERSEDED_BY_RANGE_CLOSURE",
    }
    assert "historical pre-range-closure candidate `208`" in readout
    assert "**`d_global=224`**" in readout


def test_observation_and_production_refit_firewalls_are_explicit():
    contract, _, _, _ = assembled()
    scalar = contract["scalar_observation_contract"]
    assert scalar["allowed_states"] == [
        "MEASURED_SCALAR",
        "STRUCTURALLY_UNMEASURED",
        "MEASURED_COLLISION_UNRESOLVED",
    ]
    assert set(scalar["forbidden_collision_materialization"]) == {"sum", "mean", "max", "first_row", "zero"}
    policy = contract["production_basis_policy"]
    assert policy["stage81b_action"] == "ONE_TIME_COMPLETE_AUTHORIZED_TRAIN_REFIT"
    assert policy["refit_dimension"] == 224
    assert policy["dimension_reselection_forbidden"] is True
    assert contract["governance"]["stage81b"] == "NOT_STARTED"


def test_contract_generation_is_deterministic_and_matches_frozen_files():
    first = assembled()
    second = assembled()
    assert json.dumps(first[0], sort_keys=True) == json.dumps(second[0], sort_keys=True)
    assert json.dumps(first[1], sort_keys=True) == json.dumps(second[1], sort_keys=True)
    assert json.dumps(first[2], sort_keys=True) == json.dumps(second[2], sort_keys=True)
    assert first[3] == second[3]
    assert json.loads((ROOT / CONFIG["outputs"]["contract"]).read_text()) == first[0]
    assert json.loads((ROOT / CONFIG["outputs"]["evidence_manifest"]).read_text()) == first[1]
    assert json.loads((ROOT / CONFIG["outputs"]["current_state"]).read_text()) == first[2]
    assert (ROOT / CONFIG["outputs"]["readout"]).read_text() == first[3]
