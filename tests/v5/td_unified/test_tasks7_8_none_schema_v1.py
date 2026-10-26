"""Static JSON Schema round-trip and hostile status-promotion checks."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip(
    'jsonschema', reason='standalone Task7/8 schema CI installs jsonschema; inherited Task2/3 do not'
)
Draft202012Validator = jsonschema.Draft202012Validator

from scripts.v5.td_unified.canonical_v1 import canonical_sha256
from scripts.v5.td_unified.target_bundle_v1 import issue_target_none_fixture
from scripts.v5.td_unified.downstream_contract_v1 import certify_downstream_abstention

ROOT=Path(__file__).resolve().parents[3] / "schemas" / "target_discovery" / "unified_v1"


def payloads():
    parents={
        "manifest":{"object_role":"FIXTURE_MANIFEST","reader_partition":"reader_fit"},
        "registry":{"object_role":"FIXTURE_REGISTRY","status":"NO_QUALIFIED_TARGETS"},
        "controller":{"object_role":"FIXTURE_CONTROLLER","status":"NO_DECISION_PROMOTION"},
        "falsifier":{"object_role":"FIXTURE_FALSIFIER","failed_or_unresolved":["G6","G7"]},
    }
    sha={k:canonical_sha256(x) for k,x in parents.items()}
    resolver={canonical_sha256(x):x for x in parents.values()}
    bundle=issue_target_none_fixture(
        manifest_sha256=sha["manifest"],registry_sha256=sha["registry"],
        controller_sha256=sha["controller"],falsifier_sha256=sha["falsifier"],
        resolver=resolver.get)
    receipt=certify_downstream_abstention(bundle,resolver=resolver.get)
    return bundle,receipt


@pytest.mark.parametrize("name,index",[
    ("target_none_fixture_bundle_v1.json",0),
    ("downstream_none_abstention_fixture_v1.json",1),
])
def test_exact_emitted_fixture_receipts_match_independently_validated_schemas(name,index):
    body=json.loads((ROOT/name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(body)
    validator=Draft202012Validator(body)
    assert not list(validator.iter_errors(payloads()[index]))


@pytest.mark.parametrize("name,index,key,evil",[
    ("target_none_fixture_bundle_v1.json",0,"target_selection","C1"),
    ("target_none_fixture_bundle_v1.json",0,"externally_authenticated",True),
    ("target_none_fixture_bundle_v1.json",0,"qualification_stage","KNOWN_TRUTH_QUALIFIED"),
    ("target_none_fixture_bundle_v1.json",0,"training_authorized",True),
    ("downstream_none_abstention_fixture_v1.json",1,"status","DOWNSTREAM_CERTIFIED"),
    ("downstream_none_abstention_fixture_v1.json",1,"teacher_executed",True),
    ("downstream_none_abstention_fixture_v1.json",1,"ema_updates",5),
    ("downstream_none_abstention_fixture_v1.json",1,"downstream_certified",True),
])
def test_machine_schema_refuses_fixture_authority_promotion(name,index,key,evil):
    body=json.loads((ROOT/name).read_text(encoding="utf-8"))
    data=deepcopy(payloads()[index])
    data[key]=evil
    assert list(Draft202012Validator(body).iter_errors(data)), (name,key)


def test_receipt_schema_rejects_unknown_parent_or_authority_fields():
    body=json.loads((ROOT/"target_none_fixture_bundle_v1.json").read_text())
    bundle,_=payloads()
    for extra in ("trusted_actor","secret_truth","authentication_signature","stage4_authorized"):
        corrupted={**bundle,extra:"PASS"}
        assert not Draft202012Validator(body).is_valid(corrupted)
