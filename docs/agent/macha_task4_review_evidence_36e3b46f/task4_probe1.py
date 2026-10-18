"""Macha independent hostile review of Unified Task 4 candidate 36e3b46f (PR #421).

Synthetic DEVELOPMENT fixtures only; no protected, biological or real bytes. Run from the review worktree root.
All attacks use public types and public functions; none mutates module-private registries
(_LIFECYCLE_DIGESTS, _REGENERATION_EXECUTIONS) or monkeypatches module globals.
"""
import dataclasses
import os
import subprocess
import sys
import types

repo = os.getcwd()
sys.path.insert(0, repo)
_m = types.ModuleType("tests")  # pin repo `tests` ahead of PyMC's site-packages `tests`
_m.__path__ = [os.path.join(repo, "tests")]
sys.modules["tests"] = _m

from scripts.v5.td_unified import challenge_custody_v1 as c  # noqa: E402
from scripts.v5.td_unified import task4_authority_barrier_v1 as b  # noqa: E402
from scripts.v5.td_unified import task4_registry_adapter_v1 as ad  # noqa: E402
from scripts.v5.td_unified import registry_v1 as r  # noqa: E402
from scripts.v5.td_unified.authority_v1 import QualificationStage as Q  # noqa: E402

RESULTS = []
M1, M2 = "1" * 64, "2" * 64


def t(name, fn, expect_refusal, note=False):
    try:
        out = fn()
        refused, detail = False, out
    except Exception as exc:  # noqa: BLE001
        refused, detail = True, f"{type(exc).__name__}: {str(exc)[:170]}"
    ok = refused == expect_refusal
    tag = "NOTE" if note else ("OK  " if ok else "BAD ")
    if not note:
        RESULTS.append(ok)
    print(f"{tag} {name} -> {'REFUSED' if refused else 'ACCEPTED'}: {ascii(str(detail))[:240]}")
    return None if refused else out


def deps(**over):
    d = {
        "task2_manifest_sha": "1" * 64, "task3_registry_sha": "2" * 64,
        "registry_unit_identities": (("G8", "3" * 64),),
        "producer_actor_identity": "4" * 64, "executor_actor_identity": "5" * 64,
        "controller_actor_identity": "6" * 64, "adjudicator_actor_identity": "7" * 64,
        "realization_schema_sha": "a" * 64, "challenge_family_sha": "c" * 64,
        "adjudication_contract_sha": "d" * 64, "multiplicity_policy_sha": "e" * 64,
        "publication_policy_sha": "f" * 64, "genesis_ledger_identity": "0" * 64,
        "authority_scope": "UNIT:G8", "authority_restrictions": ("NO_TRAINING_AUTHORITY",),
        "qualification_budget": 2,
    }
    d.update(c.development_fixture_generator_identities())
    d.update(over)
    return d


HIDDEN = b"hidden-dev-spec"


def sealed_dev(cid, d=None):
    camp = c.create_campaign(cid, d or deps(), barrier_status=None, namespace="DEVELOPMENT")
    camp, definition = c.seal_definition(camp, family="fixture", hidden_spec=HIDDEN)
    rows = c.generate_development_fixture_rows(camp, definition, hidden_spec=HIDDEN)
    camp, sealed = c.seal_realization_set(camp, definition, rows, budget=2)
    return camp, definition, sealed


def complete(camp, definition, sealed, outputs=("a" * 64, "b" * 64), method=M1):
    for rid, out in zip(("r0", "r1"), outputs):
        camp, e = c.issue_exposure(camp, sealed, realization_id=rid, method_scientific_identity=method)
        camp, _ = c.freeze_method_output(camp, e, output_sha256=out)
        camp = c.record_exposure_terminal(camp, e, terminal_status="EVALUATED")
    camp, _ = c.reveal_hidden_material(camp, definition, sealed, hidden_spec=HIDDEN)
    camp, _ = c.verify_regeneration(camp, sealed, definition=definition, hidden_spec=HIDDEN)
    return c.finalize_custody(camp, sealed)


print("== positive control and preserved REDs")
camp0, def0, sealed0 = sealed_dev("pc")
fin0 = t("P0 lawful DEVELOPMENT chain -> CUSTODY_COMPLETE", lambda: complete(camp0, def0, sealed0)[0].state.value, False)
camp, definition, sealed = sealed_dev("echo")
for rid in ("r0", "r1"):
    camp, e = c.issue_exposure(camp, sealed, realization_id=rid, method_scientific_identity=M1)
    camp, _ = c.freeze_method_output(camp, e, output_sha256="c" * 64 if rid == "r0" else "d" * 64)
    camp = c.record_exposure_terminal(camp, e, terminal_status="EVALUATED")
camp, _ = c.reveal_hidden_material(camp, definition, sealed, hidden_spec=HIDDEN)
echo_rows = [{"realization_id": i, "content_sha256": d, "challenge_class": k}
             for i, d, k in zip(sealed.realization_ids, sealed.content_sha256s, sealed.challenge_classes)]
t("PR#417 echo of sealed rows as regeneration", lambda: c.verify_regeneration(camp, sealed, echo_rows, definition=definition, hidden_spec=HIDDEN), True)
t("FINAL with genuine harness-less create", lambda: c.create_campaign("final", deps(), barrier_status=None, namespace="FINAL"), True)
t("plain replace() token copy with forged advanced state (PR test pattern)", lambda: c.reveal_hidden_material(
    dataclasses.replace(sealed_dev("copy")[0], state=c.CampaignState.ALL_REQUIRED_OUTPUTS_FROZEN), def0, sealed0, hidden_spec=HIDDEN), True)

print("== A1 subclassed campaign: fabricated CUSTODY_COMPLETE with zero real exposures")


def subclass_fabrication():
    lawful, definition, sealed = sealed_dev("subclass-fab")  # REALIZATION_SET_SEALED, nothing exposed
    frozen_payload = lawful.to_payload()

    class ShadowCampaign(c.QualificationCampaign):
        def to_payload(self):  # report the last lawful payload so the digest check matches
            return frozen_payload

    fields = {f.name: getattr(lawful, f.name) for f in dataclasses.fields(lawful)}
    fields.update(
        state=c.CampaignState.ALL_REQUIRED_OUTPUTS_FROZEN, exposures_consumed=2,
        exposed_realization_ids=("r0", "r1"),
        issued_exposures=(("exp-1", "r0", sealed.content_sha256s[0], M1, 1), ("exp-2", "r1", sealed.content_sha256s[1], M1, 2)),
        frozen_outputs=(("r0", "e" * 64), ("r1", "f" * 64)),
        terminal_statuses=(("r0", "EVALUATED"), ("r1", "EVALUATED")),
    )
    shadow = ShadowCampaign(**fields)
    shadow, _ = c.reveal_hidden_material(shadow, definition, sealed, hidden_spec=HIDDEN)
    shadow, _ = c.verify_regeneration(shadow, sealed, definition=definition, hidden_spec=HIDDEN)
    done, receipt, evidence = c.finalize_custody(shadow, sealed)
    return (f"{done.state.value}; receipt exposures_consumed={receipt['exposures_consumed']}; "
            f"evidence frozen_outputs={evidence['frozen_outputs']}; real exposures issued by issue_exposure: 0")


t("A1 ShadowCampaign(to_payload override) + copied fields -> reveal/regeneration/finalize", subclass_fabrication, True)

print("== A2 subclassed authority harness: FINAL fail-closed bypass")


def final_via_subclass_harness():
    class ShadowHarness(b.Task4AuthorityHarness):
        def current_status(self):
            return None

    h = ShadowHarness(unit_id="G8", registry=None, custody_store=None, expected_head="0" * 64, actor_context={})
    fc = c.create_campaign("final-shadow", deps(), barrier_status=None, namespace="FINAL", authority_harness=h)
    fc, fdef = c.seal_definition(fc, family="fixture", hidden_spec=HIDDEN, authority_harness=h)
    rows = [{"realization_id": "r0", "content_sha256": "a" * 64, "challenge_class": "A"},
            {"realization_id": "r1", "content_sha256": "b" * 64, "challenge_class": "A"}]
    fc, fsealed = c.seal_realization_set(fc, fdef, rows, budget=2, authority_harness=h)
    for rid in ("r0", "r1"):
        fc, e = c.issue_exposure(fc, fsealed, realization_id=rid, method_scientific_identity=M1, authority_harness=h)
        fc, _ = c.freeze_method_output(fc, e, output_sha256="9" * 64 if rid == "r0" else "8" * 64, authority_harness=h)
        fc = c.record_exposure_terminal(fc, e, terminal_status="EVALUATED", authority_harness=h)
    fc, rev = c.reveal_hidden_material(fc, fdef, fsealed, hidden_spec=HIDDEN, authority_harness=h)
    return f"namespace={fc.namespace} promotion_authority={fc.promotion_authority} state={fc.state.value}"


t("A2 ShadowHarness(current_status override) drives a FINAL campaign to HIDDEN_MATERIAL_REVEALED", final_via_subclass_harness, True)
t("A2 control: genuine Task4AuthorityHarness refuses FINAL",
  lambda: c.create_campaign("final-genuine", deps(), barrier_status=None, namespace="FINAL",
                            authority_harness=b.Task4AuthorityHarness("G8", None, None, "0" * 64, {})), True)

print("== A3 subclassed exposure: output frozen for a realization that was never exposed")


def exposure_shadow():
    camp, definition, sealed = sealed_dev("exposure-shadow")
    camp, e0 = c.issue_exposure(camp, sealed, realization_id="r0", method_scientific_identity=M1)

    class ShadowExposure(c.ExposureRecord):
        def identity_tuple(self):
            return e0.identity_tuple()

    ghost = ShadowExposure(e0.campaign_identity, e0.exposure_id, "r1", sealed.content_sha256s[1], M1, 2)
    camp, _ = c.freeze_method_output(camp, e0, output_sha256="a" * 64)
    camp, _ = c.freeze_method_output(camp, ghost, output_sha256="b" * 64)
    camp = c.record_exposure_terminal(camp, e0, terminal_status="EVALUATED")
    camp = c.record_exposure_terminal(camp, ghost, terminal_status="EVALUATED")
    camp, _ = c.reveal_hidden_material(camp, definition, sealed, hidden_spec=HIDDEN)
    return f"{camp.state.value}; exposed={camp.exposed_realization_ids}; frozen={[k for k, _ in camp.frozen_outputs]}"


t("A3 ShadowExposure(identity_tuple override) freezes r1 unexposed, then hidden material is revealed", exposure_shadow, True)

print("== A4 subclassed definition: reveal accepts hidden material that differs from the commitment")


def definition_shadow():
    camp, definition, sealed = sealed_dev("definition-shadow")
    for rid in ("r0", "r1"):
        camp, e = c.issue_exposure(camp, sealed, realization_id=rid, method_scientific_identity=M1)
        camp, _ = c.freeze_method_output(camp, e, output_sha256="a" * 64 if rid == "r0" else "b" * 64)
        camp = c.record_exposure_terminal(camp, e, terminal_status="EVALUATED")
    committed = definition.to_payload()
    import hashlib

    class ShadowDefinition(c.SealedChallengeDefinition):
        def to_payload(self):
            return committed

    other = b"a-different-hidden-spec"
    ghost = ShadowDefinition(definition.campaign_identity, definition.family, hashlib.sha256(other).hexdigest(), definition.namespace)
    camp, reveal = c.reveal_hidden_material(camp, ghost, sealed, hidden_spec=other)
    return (f"{camp.state.value}; revealed hidden_spec_sha256 == committed? "
            f"{reveal.hidden_spec_sha256 == definition.hidden_spec_commitment}")


t("A4 ShadowDefinition(to_payload override) reveals uncommitted hidden material", definition_shadow, True)


def plain_mismatch():
    camp, definition, sealed = sealed_dev("definition-plain")
    for rid in ("r0", "r1"):
        camp, e = c.issue_exposure(camp, sealed, realization_id=rid, method_scientific_identity=M1)
        camp, _ = c.freeze_method_output(camp, e, output_sha256="a" * 64 if rid == "r0" else "b" * 64)
        camp = c.record_exposure_terminal(camp, e, terminal_status="EVALUATED")
    return c.reveal_hidden_material(camp, definition, sealed, hidden_spec=b"a-different-hidden-spec")


t("A4 control: plain definition with mismatched hidden material at reveal", plain_mismatch, True)

print("== A5 same campaign identity re-created in-process: exposure accounting reset")


def recreate():
    a, adef, asealed = sealed_dev("same-identity")
    a, e = c.issue_exposure(a, asealed, realization_id="r0", method_scientific_identity=M1)
    a, _ = c.freeze_method_output(a, e, output_sha256="0" * 63 + "1")
    a = c.record_exposure_terminal(a, e, terminal_status="TECHNICAL_FAILURE")  # a failed world after exposure
    bcamp, bdef, bsealed = sealed_dev("same-identity")  # same id + dependencies -> same identity
    same = (bcamp.campaign_identity == a.campaign_identity, bsealed.sealed_root == asealed.sealed_root)
    done, receipt, evidence = complete(bcamp, bdef, bsealed, outputs=("5" * 64, "6" * 64), method=M2)
    return (f"same campaign_identity/sealed_root={same}; B {done.state.value} with r0 terminal "
            f"{dict(evidence['terminal_statuses'])['r0']} (A had TECHNICAL_FAILURE); A's exposure history absent from B")


t("A5 re-create the same campaign identity after an exposed failed world, complete custody again", recreate, True)

child = (
    "import os,sys,types; sys.path.insert(0,os.getcwd()); m=types.ModuleType('tests'); m.__path__=[os.path.join(os.getcwd(),'tests')]; sys.modules['tests']=m\n"
    "from scripts.v5.td_unified import challenge_custody_v1 as c\n"
    "exec(open(sys.argv[1], encoding='utf-8').read().split('# ---child---')[1])\n"
)
CHILD_BODY = '''# ---child---
d = {"task2_manifest_sha": "1"*64, "task3_registry_sha": "2"*64, "registry_unit_identities": (("G8","3"*64),),
     "producer_actor_identity": "4"*64, "executor_actor_identity": "5"*64, "controller_actor_identity": "6"*64,
     "adjudicator_actor_identity": "7"*64, "realization_schema_sha": "a"*64, "challenge_family_sha": "c"*64,
     "adjudication_contract_sha": "d"*64, "multiplicity_policy_sha": "e"*64, "publication_policy_sha": "f"*64,
     "genesis_ledger_identity": "0"*64, "authority_scope": "UNIT:G8", "authority_restrictions": ("NO_TRAINING_AUTHORITY",),
     "qualification_budget": 2}
d.update(c.development_fixture_generator_identities())
x = c.create_campaign("same-identity", d, barrier_status=None, namespace="DEVELOPMENT")
print("created", x.campaign_identity[:12])
# ---child---
'''
child_file = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0] if sys.argv[0] else ".")), "task4_probe1_child.txt")
with open(child_file, "w", encoding="utf-8") as fh:
    fh.write(CHILD_BODY)
t("NOTE second process re-creates the same campaign identity (process-local lifecycle, disclosed)",
  lambda: subprocess.run([sys.executable, "-I", "-c", child, child_file], capture_output=True, text=True, cwd=repo, check=True).stdout.strip(),
  False, note=True)

print("== authority boundary")


class ForgedStore:
    def replay(self):
        return types.SimpleNamespace(authoritative=True, head="0" * 64)


t("barrier with a forged authoritative custody store", lambda: b.Task4AuthorityHarness(
    "G8", None, ForgedStore(), "0" * 64, {}).current_status(), True)
t("Task 3 SAME_CODE_PATH -> KNOWN_TRUTH_QUALIFIED still closed",
  lambda: r._legacy._validate_stage_evidence_policy(Q.KNOWN_TRUTH_QUALIFIED, "x"), True)
t("Task 4 modules have no legacy-registry import", lambda: ad.assert_no_legacy_registry_dependency(
    (os.path.join(repo, "scripts", "v5", "td_unified"),)) or "clean", False)
_dc, _dd, _ds = sealed_dev("duck")
t("NOTE duck-typed sealed set (SimpleNamespace copy of the campaign's own set; no type check) accepted by issue_exposure",
  lambda: c.issue_exposure(_dc, types.SimpleNamespace(**dataclasses.asdict(_ds)), realization_id="r0",
                           method_scientific_identity=M1)[1].realization_id, False, note=True)

print()
print(f"SUMMARY: {sum(RESULTS)}/{len(RESULTS)} expected; BAD={len(RESULTS) - sum(RESULTS)}")
