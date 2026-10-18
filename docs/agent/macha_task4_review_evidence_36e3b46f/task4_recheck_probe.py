"""Macha focused re-check of Unified Task 4 B1-B5 at 64535753 (PR #427).

Synthetic DEVELOPMENT fixtures only. No probe mutates a module-private registry or monkeypatches a module
global; every attack passes ordinary Python values to the public functions. Run from the review worktree root.
"""
import dataclasses
import hashlib
import os
import threading
import types
import sys

repo = os.getcwd()
sys.path.insert(0, repo)
_m = types.ModuleType("tests")
_m.__path__ = [os.path.join(repo, "tests")]
sys.modules["tests"] = _m

from scripts.v5.td_unified import challenge_custody_v1 as c  # noqa: E402
from scripts.v5.td_unified import task4_authority_barrier_v1 as b  # noqa: E402

RESULTS = []
M1, M2 = "1" * 64, "2" * 64
HIDDEN = b"hidden-dev-spec"


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
    print(f"{tag} {name} -> {'REFUSED' if refused else 'ACCEPTED'}: {ascii(str(detail))[:250]}")


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


def sealed_dev(cid):
    camp = c.create_campaign(cid, deps(), barrier_status=None, namespace="DEVELOPMENT")
    camp, definition = c.seal_definition(camp, family="fixture", hidden_spec=HIDDEN)
    rows = c.generate_development_fixture_rows(camp, definition, hidden_spec=HIDDEN)
    camp, sealed = c.seal_realization_set(camp, definition, rows, budget=2)
    return camp, definition, sealed


def expose_all(camp, sealed, rids=("r0", "r1")):
    for rid in rids:
        camp, e = c.issue_exposure(camp, sealed, realization_id=rid, method_scientific_identity=M1)
        camp, _ = c.freeze_method_output(camp, e, output_sha256=hashlib.sha256(rid.encode()).hexdigest())
        camp = c.record_exposure_terminal(camp, e, terminal_status="EVALUATED")
    return camp


class EqAnyStr(str):
    """A str whose canonical/JSON bytes are its own value but which compares equal to anything."""
    __hash__ = str.__hash__

    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False


print("== positive control")
pc, pdef, psealed = sealed_dev("pc")
pc = expose_all(pc, psealed)
pc, _ = c.reveal_hidden_material(pc, pdef, psealed, hidden_spec=HIDDEN)
pc, _ = c.verify_regeneration(pc, psealed, definition=pdef, hidden_spec=HIDDEN)
t("P0 lawful DEVELOPMENT chain -> CUSTODY_COMPLETE", lambda: c.finalize_custody(pc, psealed)[0].state.value, False)

print("== original attacks A1-A5 (exact rerun of the 36e3b46f probe logic)")


def a1():
    lawful, definition, sealed = sealed_dev("a1")
    frozen_payload = lawful.to_payload()

    class ShadowCampaign(c.QualificationCampaign):
        def to_payload(self):
            return frozen_payload
    f = {x.name: getattr(lawful, x.name) for x in dataclasses.fields(lawful)}
    f.update(state=c.CampaignState.ALL_REQUIRED_OUTPUTS_FROZEN, exposures_consumed=2, exposed_realization_ids=("r0", "r1"),
             issued_exposures=(("exp-1", "r0", sealed.content_sha256s[0], M1, 1), ("exp-2", "r1", sealed.content_sha256s[1], M1, 2)),
             frozen_outputs=(("r0", "e" * 64), ("r1", "f" * 64)), terminal_statuses=(("r0", "EVALUATED"), ("r1", "EVALUATED")))
    return c.reveal_hidden_material(ShadowCampaign(**f), definition, sealed, hidden_spec=HIDDEN)[0].state.value


t("A1 ShadowCampaign(to_payload override)", a1, True)


def a2():
    class ShadowHarness(b.Task4AuthorityHarness):
        def current_status(self):
            return None
    h = ShadowHarness(unit_id="G8", registry=None, custody_store=None, expected_head="0" * 64, actor_context={})
    return c.create_campaign("a2-final", deps(), barrier_status=None, namespace="FINAL", authority_harness=h).namespace


t("A2 ShadowHarness(current_status override) creates FINAL", a2, True)


def a3():
    camp, definition, sealed = sealed_dev("a3")
    camp, e0 = c.issue_exposure(camp, sealed, realization_id="r0", method_scientific_identity=M1)

    class ShadowExposure(c.ExposureRecord):
        def identity_tuple(self):
            return e0.identity_tuple()
    ghost = ShadowExposure(e0.campaign_identity, e0.exposure_id, "r1", sealed.content_sha256s[1], M1, 2)
    camp, _ = c.freeze_method_output(camp, e0, output_sha256="a" * 64)
    return c.freeze_method_output(camp, ghost, output_sha256="b" * 64)[0].state.value


t("A3 ShadowExposure(identity_tuple override) freezes unexposed r1", a3, True)


def a4():
    camp, definition, sealed = sealed_dev("a4")
    camp = expose_all(camp, sealed)
    committed = definition.to_payload()

    class ShadowDefinition(c.SealedChallengeDefinition):
        def to_payload(self):
            return committed
    other = b"a-different-hidden-spec"
    ghost = ShadowDefinition(definition.campaign_identity, definition.family, hashlib.sha256(other).hexdigest(), definition.namespace)
    return c.reveal_hidden_material(camp, ghost, sealed, hidden_spec=other)[0].state.value


t("A4 ShadowDefinition(to_payload override) reveals uncommitted spec", a4, True)


def a5():
    a, adef, asealed = sealed_dev("a5")
    a, e = c.issue_exposure(a, asealed, realization_id="r0", method_scientific_identity=M1)
    return sealed_dev("a5")[0].campaign_identity


t("A5 re-create the same campaign identity after an exposure", a5, True)
_dc, _dd, _ds = sealed_dev("duck")
t("A1b duck-typed sealed set (SimpleNamespace)", lambda: c.issue_exposure(
    _dc, types.SimpleNamespace(**dataclasses.asdict(_ds)), realization_id="r0", method_scientific_identity=M1), True)


def forged_plain():
    lawful, definition, sealed = sealed_dev("forged-plain")
    return c.reveal_hidden_material(dataclasses.replace(lawful, state=c.CampaignState.ALL_REQUIRED_OUTPUTS_FROZEN),
                                    definition, sealed, hidden_spec=HIDDEN)


t("control: exact-type campaign with forged fields + copied token", forged_plain, True)
t("control: genuine harness still refuses FINAL", lambda: c.create_campaign(
    "final-genuine", deps(), barrier_status=None, namespace="FINAL",
    authority_harness=b.Task4AuthorityHarness("G8", None, None, "0" * 64, {})), True)

print("== side doors: forged NESTED values inside exact-type objects")


def n3():
    camp, definition, sealed = sealed_dev("n3")
    camp, e0 = c.issue_exposure(camp, sealed, realization_id="r0", method_scientific_identity=M1)
    ghost = c.ExposureRecord(e0.campaign_identity, e0.exposure_id, EqAnyStr("r1"), e0.realization_content_sha256, M1, e0.ordinal)
    camp, _ = c.freeze_method_output(camp, e0, output_sha256="a" * 64)
    camp, _ = c.freeze_method_output(camp, ghost, output_sha256="b" * 64)
    camp = c.record_exposure_terminal(camp, e0, terminal_status="EVALUATED")
    camp = c.record_exposure_terminal(camp, ghost, terminal_status="EVALUATED")
    camp, _ = c.reveal_hidden_material(camp, definition, sealed, hidden_spec=HIDDEN)
    return (f"{camp.state.value}; exposed={list(map(str, camp.exposed_realization_ids))}; "
            f"frozen={[str(k) for k, _ in camp.frozen_outputs]}; type(ghost) is ExposureRecord: {type(ghost) is c.ExposureRecord}")


t("N3 exact ExposureRecord whose realization_id is an eq-anything str('r1'): freeze unexposed r1, reveal", n3, True)


def n4():
    camp, definition, sealed = sealed_dev("n4")
    camp = expose_all(camp, sealed)
    ghost = c.SealedChallengeDefinition(definition.campaign_identity, definition.family,
                                        EqAnyStr(definition.hidden_spec_commitment), definition.namespace)
    other = b"a-different-hidden-spec"
    camp, rev = c.reveal_hidden_material(camp, ghost, sealed, hidden_spec=other)
    return (f"{camp.state.value}; revealed digest equals commitment: "
            f"{str.__eq__(rev.hidden_spec_sha256, definition.hidden_spec_commitment)}; type exact: {type(ghost) is c.SealedChallengeDefinition}")


t("N4 exact SealedChallengeDefinition whose commitment is a ne-nothing str: reveal uncommitted spec", n4, True)


class BudgetShrinkDeps(dict):
    """dict() / JSON see the stored (frozen) values; module subscripting sees budget 1."""
    def __getitem__(self, key):
        return 1 if key == "qualification_budget" else dict.__getitem__(self, key)


def n6():
    lawful = c.create_campaign("n6", deps(), barrier_status=None, namespace="DEVELOPMENT")
    lawful, definition = c.seal_definition(lawful, family="fixture", hidden_spec=HIDDEN)
    f = {x.name: getattr(lawful, x.name) for x in dataclasses.fields(lawful)}
    f["dependencies"] = BudgetShrinkDeps(lawful.dependencies)
    camp = c.QualificationCampaign(**f)  # exact type, lawful token, digest-identical payload
    rows = c.generate_development_fixture_rows(camp, definition, hidden_spec=HIDDEN)
    camp, sealed = c.seal_realization_set(camp, definition, rows, budget=1)
    camp = expose_all(camp, sealed, rids=("r0",))
    camp, _ = c.reveal_hidden_material(camp, definition, sealed, hidden_spec=HIDDEN)
    camp, _ = c.verify_regeneration(camp, sealed, definition=definition, hidden_spec=HIDDEN)
    done, receipt, evidence = c.finalize_custody(camp, sealed)
    return (f"{done.state.value}; identity-frozen budget={dict.__getitem__(lawful.dependencies, 'qualification_budget')}; "
            f"sealed/exposed worlds={len(sealed.realization_ids)}; receipt exposures_consumed={receipt['exposures_consumed']}")


t("N6 exact QualificationCampaign whose dependencies is a dict subclass: finite exam shrunk 2 -> 1, custody complete", n6, True)



def n7():
    camp, definition, sealed = sealed_dev("n7")
    named = EqAnyStr("r1")  # canonical value 'r1', compares equal to 'r0' first
    camp, e = c.issue_exposure(camp, sealed, realization_id=named, method_scientific_identity=M1)
    content_is_r0 = e.realization_content_sha256 == sealed.content_sha256s[0]
    return f"exposure recorded as {str(e.realization_id)!r} but carries r0 content: {content_is_r0}"


t("N7 issue_exposure(realization_id=eq-anything str 'r1') records r1 with r0's content", n7, True)


class ShowDistinctDeps(dict):
    """Validation reads a distinct controller via __getitem__; dict() stores the real (== producer) value."""
    def __getitem__(self, key):
        return "6" * 64 if key == "controller_actor_identity" else dict.__getitem__(self, key)


def n8():
    raw = deps(controller_actor_identity="4" * 64)  # controller == producer: must be refused
    camp = c.create_campaign("n8", ShowDistinctDeps(raw), barrier_status=None, namespace="DEVELOPMENT")
    stored = camp.dependencies
    return (f"created; stored producer == controller: "
            f"{stored['producer_actor_identity'] == stored['controller_actor_identity']}; stored type {type(stored).__name__}")


t("N8 validate_campaign_dependencies checks __getitem__ view but stores dict() view (producer == controller)", n8, True)
t("N8 control: plain dict with producer == controller", lambda: c.create_campaign(
    "n8-plain", deps(controller_actor_identity="4" * 64), barrier_status=None, namespace="DEVELOPMENT"), True)

print("== concurrency and lease")


def race():
    camp, definition, sealed = sealed_dev("race")
    wins, errs = [], []

    def go(rid):
        try:
            wins.append(c.issue_exposure(camp, sealed, realization_id=rid, method_scientific_identity=M1)[1].realization_id)
        except Exception as exc:  # noqa: BLE001
            errs.append(type(exc).__name__)
    ts = [threading.Thread(target=go, args=(rid,)) for rid in ("r0", "r1")]
    for th in ts:
        th.start()
    for th in ts:
        th.join()
    if len(wins) != 1:
        raise AssertionError(f"both exposures consumed one campaign version: {wins}")
    return f"one winner {wins}, refusals {errs}"


t("C two threads issue exposures from the same campaign version (only one may win)", race, False)
t("C lease survives abandonment of the first object", lambda: (sealed_dev("lease"), sealed_dev("lease")), True)

print()
print(f"SUMMARY: {sum(RESULTS)}/{len(RESULTS)} expected; BAD={len(RESULTS) - sum(RESULTS)}")
