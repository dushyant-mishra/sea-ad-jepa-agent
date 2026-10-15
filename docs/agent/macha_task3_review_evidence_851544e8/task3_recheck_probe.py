"""Macha focused hostile re-check of Unified Task 3 B1-B6 at 68df3158.

Synthetic fixtures only (the PR's own); no protected or biological values.
Run from the review worktree root:  python <this file>
"""
import dataclasses
import os
import sys
import types

repo = os.getcwd()
sys.path.insert(0, repo)
_m = types.ModuleType("tests")  # pin repo `tests` ahead of PyMC's site-packages `tests`
_m.__path__ = [os.path.join(repo, "tests")]
sys.modules["tests"] = _m

from scripts.v5.td_unified import registry_v1 as r  # noqa: E402
from scripts.v5.td_unified import registry_v1_legacy as legacy  # noqa: E402
from scripts.v5.td_unified import manifest_v1 as task2  # noqa: E402
from scripts.v5.td_unified.authority_v1 import ActiveLineageStatus as L  # noqa: E402
from scripts.v5.td_unified.authority_v1 import QualificationStage as Q  # noqa: E402
from tests.v5.td_unified import registry_v1_dependency_fixtures as fx  # noqa: E402
from tests.v5.td_unified.test_registry_v1_macha_rejection import (  # noqa: E402
    _actors, _human_execution_registry, _setup,
)

RESULTS = []


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
    print(f"{tag} {name} -> {'REFUSED' if refused else 'ACCEPTED'}: {ascii(str(detail))[:220]}")
    return None if refused else out


def ready(res):
    if not res.ready:
        raise AssertionError("not ready: " + "; ".join(res.blockers)[:160])
    return "ready"


def stage(reg, uid="G8"):
    return reg.units_by_id()[uid].qualification_stage.value


def human_executable_flow():
    ref, deps, reg_h, c, v, res, pe, ce, cust = _human_execution_registry()
    reg_he = r.promote_unit(reg_h, "G8", Q.HUMAN_EXECUTABLE, controller_identity=c, reviewer_identity=v,
                            authority_object_resolver=res.get, dependency_verifier=deps.get,
                            history_custody=cust)
    return ref, deps, reg_h, reg_he, c, v, res, cust


print("== P0 positive control: the PR's own lawful flow")
P0 = t("P0 genesis(KTQ) -> RRR -> HUMAN_EXECUTABLE with custody", lambda: stage(human_executable_flow()[3]), False)

print("== B1 Task 1 authority law")
ref, deps, reg_h, reg_he, c, v, res, cust = human_executable_flow()
t("B1 HUMAN_EXECUTABLE -> HUMAN_EXECUTED (and thus any later stage)",
  lambda: r.promote_unit(reg_he, "G8", Q.HUMAN_EXECUTED, controller_identity=c, reviewer_identity=v,
                         authority_object_resolver=res.get, dependency_verifier=deps.get, history_custody=cust), True)


def bound_pair(dep_stage):
    dep, ref2, d = fx.verified_pair(r, dep_stage=dep_stage)
    reg = r.TDQualificationRegistry((dep, ref2), (), (), ())
    c2, v2, ao = _actors()
    reg, objs = fx.bind_actor_registry(r, reg, {**d, **ao}, trusted_actor_objects=tuple(ao.values()))
    return reg, c2, v2, objs, d


for src, dst in ((Q.HUMAN_EXECUTED, Q.DOWNSTREAM_CERTIFIED), (Q.DOWNSTREAM_CERTIFIED, Q.TRAINING_ELIGIBLE),
                 (Q.TRAINING_ELIGIBLE, Q.TRAINING_AUTHORIZED)):
    reg, c2, v2, objs, d = bound_pair(src)
    for label, fn in (("facade", r.promote_unit), ("legacy", legacy.promote_unit)):
        t(f"B1 [{label}] declared {src.value} -> {dst.value} (UNIT scope, bound actors)",
          lambda fn=fn: fn(reg, "G8", dst, controller_identity=c2, reviewer_identity=v2,
                           authority_object_resolver=objs.get, dependency_verifier=d.get), True)
t("NOTE RegistryUnit construction validates Task 1 law (UNIT scope at TRAINING_AUTHORIZED)",
  lambda: fx.verified_pair(r, dep_stage=Q.TRAINING_AUTHORIZED)[0].qualification_stage.value, True, note=True)
t("B1 custody genesis refuses a declared UNIT record at TRAINING_AUTHORIZED",
  lambda: r.RegistryHistoryCustody(bound_pair(Q.TRAINING_AUTHORIZED)[0], attestation_key=b"k"), True)

print("== B2 stage evidence")
reg, c2, v2, objs, d = bound_pair(Q.SAME_CODE_PATH)
for rev in (None, v2):
    t(f"B2 SAME_CODE_PATH -> KNOWN_TRUTH_QUALIFIED reviewer={'yes' if rev else 'no'}",
      lambda rev=rev: r.promote_unit(reg, "G8", Q.KNOWN_TRUTH_QUALIFIED, controller_identity=c2, reviewer_identity=rev,
                                     authority_object_resolver=objs.get, dependency_verifier=d.get), True)
t("B2 [legacy] SAME_CODE_PATH -> KNOWN_TRUTH_QUALIFIED with reviewer",
  lambda: legacy.promote_unit(reg, "G8", Q.KNOWN_TRUTH_QUALIFIED, controller_identity=c2, reviewer_identity=v2,
                              authority_object_resolver=objs.get, dependency_verifier=d.get), True)
t("N2 KNOWN_TRUTH_QUALIFIED obtained by DECLARATION at genesis (no SEALED_CHALLENGE_REVIEW) then RRR -> HUMAN_EXECUTABLE",
  lambda: stage(human_executable_flow()[3]), True)

print("== B3 actor registry")
for alias in ("producer:G8 ", " producer:G8", "PRODUCER:G8", "producer：G8", "minted-by-producer-1"):
    _, _, dd, _, regb, _, rv, legit = _setup()
    hc, _, hostile = _actors(cid=alias)
    t(f"B3 controller alias {ascii(alias)} (not in curated registry)",
      lambda: r.promote_unit(regb, "G8", Q.REAL_REFERENCE_READY, controller_identity=hc, reviewer_identity=rv,
                             authority_object_resolver={**legit, **hostile}.get, dependency_verifier=dd.get), True)
for cid, rid, lbl in (("C1", "C1", "reviewer==controller"), ("C1", "producer:G8", "reviewer==producer")):
    _, _, dd, _, regb, cc, _, legit = _setup()
    _, hr, hostile = _actors(cid=cid, rid=rid)
    t(f"B3 {lbl}", lambda: r.promote_unit(regb, "G8", Q.REAL_REFERENCE_READY, controller_identity=cc, reviewer_identity=hr,
                                           authority_object_resolver={**legit, **hostile}.get, dependency_verifier=dd.get), True)

# B3-V: content validator that is NOT in the closed registry, and is the producer itself
dep, ref3, dd, p1, regb, cc, rv, legit = _setup()
validator_obj = {"object_role": "CONTENT_VALIDATOR", "actor_id": "producer:G8"}
receipt = {"object_role": "CONTENT_VALIDATION_RECEIPT", "receipt_schema": "CONTENT_VALIDATION_RECEIPT_V1",
           "prerequisite_id": p1.prerequisite_id, "content_identity_sha": p1.prerequisite_unit_sha,
           "validator_identity_sha": r.canonical_sha256(validator_obj), "status": "QUALIFIED"}
p1c = dataclasses.replace(p1, content_required=True, content_validated=True,
                          content_validation_receipt_sha=r.canonical_sha256(receipt))
regv = dataclasses.replace(regb, prerequisites=(p1c,))
objs_v = {**legit, r.canonical_sha256(validator_obj): validator_obj, r.canonical_sha256(receipt): receipt}
t("B3-V unregistered CONTENT_VALIDATOR (actor_id = producer:G8) satisfies content-required prerequisite",
  lambda: ready(r.derive_real_reference_ready("G8", regv, dependency_verifier=dd.get, authority_object_resolver=objs_v.get)), True)
t("B3-V same, through promote_unit -> RRR",
  lambda: stage(r.promote_unit(regv, "G8", Q.REAL_REFERENCE_READY, controller_identity=cc, reviewer_identity=rv,
                               authority_object_resolver=objs_v.get, dependency_verifier=dd.get)), True)

# B3-E: PROCESS_ISOLATION / LEDGER_CUSTODY evidence names no issuer at all (plan: registered PREREQUISITE_EVIDENCE_ISSUER)
t("B3-E HUMAN_EXECUTABLE evidence with no issuer binding (P0 evidence objects have no issuer field)",
  lambda: stage(human_executable_flow()[3]), True)

# B3-R: producer authors the actor registry and curates its own minted controller/reviewer
dep, ref4, d4 = fx.verified_pair(r)
p4 = fx.verified_prereq(r, dep, ref4)
mc = {"object_role": "QUALIFICATION_CONTROLLER", "actor_id": "minted-by-producer-1"}
mr = {"object_role": "INDEPENDENT_REVIEWER", "actor_id": "minted-by-producer-2"}
reg4 = r.TDQualificationRegistry((dep, ref4), (p4,), (), ())
reg4, objs4 = fx.bind_actor_registry(r, reg4, {**d4, r.canonical_sha256(mc): mc, r.canonical_sha256(mr): mr},
                                     trusted_actor_objects=(mc, mr))
cust4 = r.RegistryHistoryCustody(reg4, attestation_key=b"producer-chosen-key")
t("B3-R producer-authored actor registry with self-minted controller+reviewer -> RRR under producer-made custody",
  lambda: stage(r.promote_unit(reg4, "G8", Q.REAL_REFERENCE_READY, controller_identity=r.canonical_sha256(mc),
                               reviewer_identity=r.canonical_sha256(mr), authority_object_resolver=objs4.get,
                               dependency_verifier=d4.get, history_custody=cust4)), True)
t("NOTE actor identities are public content digests, not credentials (producer presents registered C1 digest)",
  lambda: stage(r.promote_unit(*_setup()[4:5], "G8", Q.REAL_REFERENCE_READY, controller_identity=_setup()[5],
                               reviewer_identity=_setup()[6], authority_object_resolver=_setup()[7].get,
                               dependency_verifier=_setup()[2].get)), False, note=True)



# B3-I: independence on LOGICAL actor id when one curated actor holds two role objects (RED6 class)
def curated_dual_role(extra_objs):
    dep6, ref6, d6 = fx.verified_pair(r)
    p6 = fx.verified_prereq(r, dep6, ref6)
    reg6 = r.TDQualificationRegistry((dep6, ref6), (p6,), (), ())
    c6, v6, ao6 = _actors()
    trusted = tuple(ao6.values()) + tuple(extra_objs)
    allobjs = {**d6, **ao6, **{r.canonical_sha256(o): o for o in extra_objs}}
    reg6, o6 = fx.bind_actor_registry(r, reg6, allobjs, trusted_actor_objects=trusted)
    return reg6, c6, v6, o6, d6


c1_as_reviewer = {"object_role": "INDEPENDENT_REVIEWER", "actor_id": "C1"}
reg6, c6, v6, o6, d6 = curated_dual_role([c1_as_reviewer])
t("B3-I curated C1 holds controller+reviewer roles; reviewer=C1",
  lambda: r.promote_unit(reg6, "G8", Q.REAL_REFERENCE_READY, controller_identity=c6,
                         reviewer_identity=r.canonical_sha256(c1_as_reviewer), authority_object_resolver=o6.get,
                         dependency_verifier=d6.get), True)
prod_as_reviewer = {"object_role": "INDEPENDENT_REVIEWER", "actor_id": "producer:G8"}
reg6, c6, v6, o6, d6 = curated_dual_role([prod_as_reviewer])
t("B3-I curated producer:G8 also registered as reviewer; reviewer=producer",
  lambda: r.promote_unit(reg6, "G8", Q.REAL_REFERENCE_READY, controller_identity=c6,
                         reviewer_identity=r.canonical_sha256(prod_as_reviewer), authority_object_resolver=o6.get,
                         dependency_verifier=d6.get), True)
prod_as_ctl = {"object_role": "QUALIFICATION_CONTROLLER", "actor_id": "executor:G8"}
reg6, c6, v6, o6, d6 = curated_dual_role([prod_as_ctl])
t("B3-I curated executor:G8 also registered as controller; controller=executor",
  lambda: r.promote_unit(reg6, "G8", Q.REAL_REFERENCE_READY, controller_identity=r.canonical_sha256(prod_as_ctl),
                         reviewer_identity=v6, authority_object_resolver=o6.get, dependency_verifier=d6.get), True)
prod_as_ctl2 = {"object_role": "QUALIFICATION_CONTROLLER", "actor_id": "producer:G8"}
reg6, c6, v6, o6, d6 = curated_dual_role([prod_as_ctl2])
t("B3-I curated producer:G8 also registered as controller; revocation by producer",
  lambda: r.revoke_or_supersede(reg6, "G8", L.REVOKED_BY_DEFECT, reason_class="DEFECT",
                                controller_identity=r.canonical_sha256(prod_as_ctl2), authority_object_resolver=o6.get,
                                dependency_verifier=d6.get), True)

print("== B4 verification cache")
dep, ref5, dd, _, regc, _, _, ao = _setup()
cache = {}
r.derive_real_reference_ready("G8", regc, dependency_verifier=dd.get, authority_object_resolver=ao.get, verification_cache=cache)
t("B4/H4 warmed cache + empty resolver", lambda: ready(r.derive_real_reference_ready(
    "G8", regc, dependency_verifier=lambda s: None, authority_object_resolver=ao.get, verification_cache=cache)), True)
poison = {("dependency-object-v1", u.canonical_sha256(), f, getattr(u, f)): (True, None)
          for u in (dep, ref5) for f in r._IDENTITY_64_FIELDS + r._IDENTITY_40_FIELDS}
t("B4/H3 poisoned cache + empty resolver", lambda: ready(r.derive_real_reference_ready(
    "G8", regc, dependency_verifier=lambda s: None, authority_object_resolver=ao.get, verification_cache=poison)), True)
t("B4/H3 [legacy] poisoned cache + empty resolver via promote_unit RRR", lambda: legacy.promote_unit(
    regc, "G8", Q.REAL_REFERENCE_READY, controller_identity=_setup()[5], reviewer_identity=_setup()[6],
    authority_object_resolver=ao.get, dependency_verifier=lambda s: None, verification_cache=poison), True)

print("== B5 history custody")
ref, deps, reg_h, c, v, res, pe, ce, cust = _human_execution_registry()
rrr = r.TDQualificationRegistry(reg_h.units, tuple(p for p in reg_h.prerequisites if p.gate == "REAL_REFERENCE_READY"),
                                reg_h.promotions, reg_h.revocations, actor_registry_sha=reg_h.actor_registry_sha)
revoked = r.revoke_or_supersede(rrr, "G8", L.REVOKED_BY_DEFECT, reason_class="DEFECT", controller_identity=c,
                                authority_object_resolver=res.get, dependency_verifier=deps.get, history_custody=cust)
revoked_g8_sha = reg_h.units_by_id()["G8"].canonical_sha256()
forged = dataclasses.replace(revoked.units_by_id()["G8"], active_lineage_status=L.ACTIVE)
forged_back = r.TDQualificationRegistry(tuple(forged if u.unit_id == "G8" else u for u in revoked.units),
                                        reg_h.prerequisites, revoked.promotions, (), actor_registry_sha=reg_h.actor_registry_sha)
t("B5/H6 deleted revocation, same custody", lambda: r.promote_unit(
    forged_back, "G8", Q.HUMAN_EXECUTABLE, controller_identity=c, reviewer_identity=v,
    authority_object_resolver=res.get, dependency_verifier=deps.get, history_custody=cust), True)
t("B5/H6 deleted revocation, no custody", lambda: r.promote_unit(
    forged_back, "G8", Q.HUMAN_EXECUTABLE, controller_identity=c, reviewer_identity=v,
    authority_object_resolver=res.get, dependency_verifier=deps.get), True)


def fresh_custody_requalify():
    ref_b, deps_b, reg_hb, c_b, v_b, res_b, _, _, cust_b = _human_execution_registry()  # brand-new custody, new genesis
    assert reg_hb.units_by_id()["G8"].canonical_sha256() == revoked_g8_sha, "different unit identity"
    out = r.promote_unit(reg_hb, "G8", Q.HUMAN_EXECUTABLE, controller_identity=c_b, reviewer_identity=v_b,
                         authority_object_resolver=res_b.get, dependency_verifier=deps_b.get, history_custody=cust_b)
    return f"{stage(out)} for the SAME G8 identity revoked in custody A"


t("B5-F revoked unit re-qualified to HUMAN_EXECUTABLE by discarding custody and starting a fresh genesis", fresh_custody_requalify, True)
t("B5 fresh custody from advanced (RRR) genesis", lambda: r.RegistryHistoryCustody(
    dataclasses.replace(rrr, promotions=()), attestation_key=b"x"), True)
t("NOTE custody private state is writable in-process (cust._revocations = ()) then H6 with same custody",
  lambda: (setattr(cust, "_revocations", ()), setattr(cust, "_unit_state", {u.unit_id: u.to_payload() for u in forged_back.units}),
           stage(r.promote_unit(forged_back, "G8", Q.HUMAN_EXECUTABLE, controller_identity=c, reviewer_identity=v,
                                authority_object_resolver=res.get, dependency_verifier=deps.get, history_custody=cust)))[-1],
  False, note=True)
ref, deps, reg_h, c, v, res, pe, ce, cust = _human_execution_registry()
t("NOTE legacy.promote_unit is a public HUMAN_EXECUTABLE path that ignores custody",
  lambda: stage(legacy.promote_unit(reg_h, "G8", Q.HUMAN_EXECUTABLE, controller_identity=c, reviewer_identity=v,
                                    authority_object_resolver=res.get, dependency_verifier=deps.get)), False, note=True)

print("== N1 frozen Task 2 population/manifest authority at the RRR consumption point")
ids, objs = fx._core("G8")
rids, robjs = fx._core("REF")
fake_access = {"object_role": "ACCESS_POLICY", "population_authority": "AUTHENTICATED_READER_SPLIT",
               "fit_donors": [f"FAKE_{i:03d}" for i in range(104)], "crossfit_folds": "CHOSEN_LATER"}
t("N1 control: frozen Task 2 validator refuses the forged access policy",
  lambda: task2.validate_population_access_policy_payload(dict(fake_access)), True)
asha = r.canonical_sha256(fake_access)
table = {"object_role": "UNIT_EXECUTION_IDENTITY_TABLE", "table_schema": "UNIT_EXECUTION_IDENTITY_TABLE_V1",
         "units": [fx._row("G8", ids), fx._row("REF", rids)]}
tsha = r.canonical_sha256(table)
manifest = {"schema": "TD_EXECUTION_MANIFEST_V1", "access_policy_sha": asha, "unit_execution_identity_table_sha": tsha}
msha = r.canonical_sha256(manifest)
t("N1 control: frozen Task 2 validate_manifest refuses the Task-3-accepted manifest",
  lambda: task2.validate_manifest(dict(manifest), {**objs, asha: fake_access, tsha: table}.get), True)
g8 = fx._build_unit(r, "G8", ids, manifest_sha=msha, access_sha=asha, stage=Q.KNOWN_TRUTH_QUALIFIED, status=L.ACTIVE,
                    population_authority="AUTHENTICATED_READER_SPLIT", claim_scope="POOLED_DONOR_LEVEL")
rf = fx._build_unit(r, "REF", rids, manifest_sha=msha, access_sha=asha, stage=Q.KNOWN_TRUTH_QUALIFIED, status=L.ACTIVE,
                    population_authority="AUTHENTICATED_READER_SPLIT", claim_scope="POOLED_DONOR_LEVEL")
pn = fx.verified_prereq(r, g8, rf)
regn = r.TDQualificationRegistry((g8, rf), (pn,), (), ())
cn, vn, aon = _actors()
allo = {**objs, **robjs, asha: fake_access, tsha: table, msha: manifest, **aon}
regn, allo = fx.bind_actor_registry(r, regn, allo, trusted_actor_objects=tuple(aon.values()))
t("N1 forged 104 FAKE donors + folds CHOSEN_LATER accepted as AUTHENTICATED_READER_SPLIT -> RRR",
  lambda: stage(r.promote_unit(regn, "G8", Q.REAL_REFERENCE_READY, controller_identity=cn, reviewer_identity=vn,
                               authority_object_resolver=allo.get, dependency_verifier=allo.get)), True)

print()
print(f"SUMMARY: {sum(RESULTS)}/{len(RESULTS)} expected; BAD={len(RESULTS) - sum(RESULTS)}")
