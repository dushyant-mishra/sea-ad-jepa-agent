"""Macha Task 4 B1/B2 hostile RED, pinned against rejected successor6."""
from __future__ import annotations
from dataclasses import fields
import pytest
from scripts.v5.td_unified import challenge_custody_v1 as c
from scripts.v5.td_unified.task4_authority_barrier_v1 import Task4AuthorityHarness

def deps():
    d=dict(task2_manifest_sha="1"*64,task3_registry_sha="2"*64,
      registry_unit_identities=(("G8","3"*64),),
      producer_actor_identity="4"*64,executor_actor_identity="5"*64,
      controller_actor_identity="6"*64,adjudicator_actor_identity="7"*64,
      realization_schema_sha="a"*64,challenge_family_sha="c"*64,
      adjudication_contract_sha="d"*64,multiplicity_policy_sha="e"*64,
      publication_policy_sha="f"*64,genesis_ledger_identity="0"*64,
      authority_scope="UNIT:G8",authority_restrictions=("NO_TRAINING_AUTHORITY",),
      qualification_budget=2)
    d.update(c.development_fixture_generator_identities())
    return d

def sealed(cid):
    a=c.create_campaign(cid,deps(),barrier_status=None,namespace="DEVELOPMENT")
    a,d=c.seal_definition(a,family="fixture",hidden_spec=b"hidden")
    rows=c.generate_development_fixture_rows(a,d,hidden_spec=b"hidden")
    a,s=c.seal_realization_set(a,d,rows,budget=2)
    return a,d,s

def test_B1_subclass_campaign_cannot_fake_exposure_or_reveal():
    a,d,s=sealed("macha-subclass-campaign")
    original=a.to_payload()
    class Shadow(c.QualificationCampaign):
        def to_payload(self):
            return original
    kw={f.name:getattr(a,f.name) for f in fields(a)}
    kw.update(state=c.CampaignState.ALL_REQUIRED_OUTPUTS_FROZEN,exposures_consumed=2,
      exposed_realization_ids=("r0","r1"),
      frozen_outputs=(("r0","a"*64),("r1","b"*64)),
      terminal_statuses=(("r0","EVALUATED"),("r1","EVALUATED")))
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.reveal_hidden_material(Shadow(**kw),d,s,hidden_spec=b"hidden")

def test_B2_subclass_harness_cannot_open_FINAL():
    class Forged(Task4AuthorityHarness):
        def current_status(self):
            return None
    h=Forged("G8",None,None,"0"*64,{})
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.create_campaign("macha-final-shadow",deps(),barrier_status=None,
                          namespace="FINAL",authority_harness=h)

def test_B1_exposure_subclass_cannot_freeze_unexposed_realization():
    a,d,s=sealed("macha-subclass-exposure")
    a,e=c.issue_exposure(a,s,realization_id="r0",method_scientific_identity="1"*64)
    class Shadow(c.ExposureRecord):
        def identity_tuple(self):
            return e.identity_tuple()
    ghost=Shadow(e.campaign_identity,e.exposure_id,"r1",s.content_sha256s[1],"1"*64,2)
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.freeze_method_output(a,ghost,output_sha256="a"*64)

def test_B1_definition_subclass_cannot_open_uncommitted_hidden_spec():
    import hashlib
    a,d,s=sealed("macha-subclass-definition")
    for rid in s.realization_ids:
        a,e=c.issue_exposure(a,s,realization_id=rid,method_scientific_identity="1"*64)
        a,_=c.freeze_method_output(a,e,output_sha256=("a" if rid=="r0" else "b")*64)
        a=c.record_exposure_terminal(a,e,terminal_status="EVALUATED")
    real=d.to_payload()
    class Shadow(c.SealedChallengeDefinition):
        def to_payload(self):
            return real
    forged=Shadow(d.campaign_identity,d.family,hashlib.sha256(b"other").hexdigest(),d.namespace)
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.reveal_hidden_material(a,forged,s,hidden_spec=b"other")
