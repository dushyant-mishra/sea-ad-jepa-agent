"""Independent hostile RED for PR428 exact 11ef009c: mutate authentic issued handle."""
import pytest
from scripts.v5.td_unified import challenge_custody_v1 as c

def deps():
 d=dict(task2_manifest_sha="1"*64,task3_registry_sha="2"*64,
 registry_unit_identities=(("G8","3"*64),),producer_actor_identity="4"*64,
 executor_actor_identity="5"*64,controller_actor_identity="6"*64,
 adjudicator_actor_identity="7"*64,realization_schema_sha="a"*64,
 challenge_family_sha="c"*64,adjudication_contract_sha="d"*64,
 multiplicity_policy_sha="e"*64,publication_policy_sha="f"*64,
 genesis_ledger_identity="0"*64,authority_scope="UNIT:G8",
 authority_restrictions=("NO_TRAINING_AUTHORITY",),qualification_budget=2)
 d.update(c.development_fixture_generator_identities())
 return d

class EqAnyStr(str):
 def __eq__(self, other): return True
 def __ne__(self, other): return False
 __hash__ = str.__hash__

def test_mutated_authentic_exposure_cannot_freeze_unexposed_world():
 a=c.create_campaign("external-audit-mutated-issued-exposure",deps(),barrier_status=None,namespace="DEVELOPMENT")
 a,d=c.seal_definition(a,family="fixture",hidden_spec=b"hidden")
 rows=c.generate_development_fixture_rows(a,d,hidden_spec=b"hidden")
 a,s=c.seal_realization_set(a,d,rows,budget=2)
 a,e=c.issue_exposure(a,s,realization_id="r0",method_scientific_identity="1"*64)
 assert a.exposed_realization_ids==("r0",)
 # The legitimate exposed object is retained in the module's registry.
 # Frozen dataclass is not immutable against object.__setattr__.
 object.__setattr__(e,"realization_id",EqAnyStr("r1"))
 with pytest.raises(c.Task4ChallengeCustodyError):
  c.freeze_method_output(a,e,output_sha256="a"*64)
