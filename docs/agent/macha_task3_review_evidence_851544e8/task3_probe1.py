import sys, dataclasses
sys.path.insert(0, r"D:/jepa_task3_review_851544e8")
import scripts.v5.td_unified.registry_v1 as r
from scripts.v5.td_unified.authority_v1 import QualificationStage as Q, ActiveLineageStatus as L
from tests.v5.td_unified.registry_v1_dependency_fixtures import verified_pair, verified_prereq, direct_fixture_actor_objects

out = []
def t(label, f, expect_raise):
    try:
        v = f(); ok = not expect_raise; msg = str(v)[:110]
    except Exception as e:
        ok = expect_raise; msg = f"RAISES {type(e).__name__}: {str(e)[:110]}"
    out.append(ok); print(ascii(("OK  " if ok else "BAD ") + label + " -> " + msg)[1:-1])

def actors(units, *, cid="C1", rid="R1"):
    c = {"object_role": "QUALIFICATION_CONTROLLER", "actor_id": cid}
    v = {"object_role": "INDEPENDENT_REVIEWER", "actor_id": rid}
    res = {r.canonical_sha256(c): c, r.canonical_sha256(v): v}
    return r.canonical_sha256(c), r.canonical_sha256(v), res

def setup():
    dep, ref, deps = verified_pair(r)
    p = verified_prereq(r, dep, ref)
    reg = r.TDQualificationRegistry((dep, ref), (p,), (), ())
    c, v, res = actors([dep, ref])
    return dep, ref, deps, p, reg, c, v, res

dep, ref, deps, p, reg, c, v, res = setup()
t("baseline: KNOWN_TRUTH -> REAL_REFERENCE_READY promotes", lambda: r.promote_unit(reg, "G8", Q.REAL_REFERENCE_READY, controller_identity=c, reviewer_identity=v, authority_object_resolver=res.get, dependency_verifier=deps.get).units_by_id()["G8"].qualification_stage.value, False)

print("== H1: climb beyond HUMAN_EXECUTED with a UNIT-scoped record (frozen Task 1: UNIT max HUMAN_EXECUTED)")
reg1 = r.promote_unit(reg, "G8", Q.REAL_REFERENCE_READY, controller_identity=c, reviewer_identity=v, authority_object_resolver=res.get, dependency_verifier=deps.get)
g8 = reg1.units_by_id()["G8"]
ev_iso = {"object_role": "PREREQUISITE_EVIDENCE", "requirement_class": "PROCESS_ISOLATION", "producer_process_isolated": True, "harness_drives_finalization": True, "reader_fit_values_out_of_process": True, "protected_partitions_physically_absent": True}
ev_cus = {"object_role": "PREREQUISITE_EVIDENCE", "requirement_class": "CROSS_PROCESS_LEDGER_CUSTODY", "persistent_ledger": True, "signing_key_out_of_process": True, "key_custodian": "HARNESS"}
res2 = dict(res); res2[r.canonical_sha256(ev_iso)] = ev_iso; res2[r.canonical_sha256(ev_cus)] = ev_cus
snap = reg.to_payload(); res2[r.canonical_sha256(snap)] = snap
def ext(pid, cls, ev):
    return dataclasses.replace(verified_prereq(r, g8, ref, pid=pid, gate="HUMAN_EXECUTABLE", requirement_class=cls), evidence_receipt_sha=r.canonical_sha256(ev))
reg1b = r.TDQualificationRegistry(reg1.units, reg1.prerequisites + (ext("ISO", "PROCESS_ISOLATION", ev_iso), ext("CUS", "CROSS_PROCESS_LEDGER_CUSTODY", ev_cus)), reg1.promotions, reg1.revocations)
cur = reg1b
for st in [Q.HUMAN_EXECUTABLE, Q.HUMAN_EXECUTED, Q.DOWNSTREAM_CERTIFIED, Q.TRAINING_ELIGIBLE, Q.TRAINING_AUTHORIZED]:
    try:
        cur = r.promote_unit(cur, "G8", st, controller_identity=c, reviewer_identity=v, authority_object_resolver=res2.get, dependency_verifier=deps.get)
        reached = st
    except Exception as e:
        print(f"    stopped before {st.value}: {type(e).__name__}: {str(e)[:120]}"); break
fin = cur.units_by_id()["G8"]
print(f"    reached stage: {fin.qualification_stage.value}; scope={fin.authority_scope}; restrictions={fin.authority_restrictions}")
t("H1 UNIT-scoped unit must not reach beyond HUMAN_EXECUTED", lambda: (_ for _ in ()).throw(AssertionError("reached " + fin.qualification_stage.value)) if fin.qualification_stage in (Q.DOWNSTREAM_CERTIFIED, Q.TRAINING_ELIGIBLE, Q.TRAINING_AUTHORIZED) else fin.qualification_stage.value, False)

print("== H2: KNOWN_TRUTH_QUALIFIED with no sealed-challenge evidence and no reviewer")
dep0, ref0, deps0 = verified_pair(r, dep_stage=Q.SAME_CODE_PATH)
reg0 = r.TDQualificationRegistry((dep0, ref0), (), (), ())
c0, v0, res0 = actors([dep0, ref0])
t("H2 SAME_CODE_PATH -> KNOWN_TRUTH_QUALIFIED with controller only must be refused", lambda: r.promote_unit(reg0, "G8", Q.KNOWN_TRUTH_QUALIFIED, controller_identity=c0, reviewer_identity=None, authority_object_resolver=res0.get, dependency_verifier=deps0.get).units_by_id()["G8"].qualification_stage.value, True)

print("== T3-B actor aliasing")
pa = "producer:G8"
for variant in [pa, pa + " ", " " + pa, pa.upper(), pa.replace(":", "\uff1a")]:
    cc, vv, rr = actors([dep, ref], cid=variant)
    t(f"T3-B controller actor_id {variant!r} vs producer {pa!r} must be refused", lambda cc=cc, vv=vv, rr=rr: r.promote_unit(reg, "G8", Q.REAL_REFERENCE_READY, controller_identity=cc, reviewer_identity=vv, authority_object_resolver=rr.get, dependency_verifier=deps.get) and "PROMOTED", True)
cc, vv, rr = actors([dep, ref], cid="C1", rid="C1")
t("T3-B reviewer actor == controller actor (different role objects) refused", lambda: r.promote_unit(reg, "G8", Q.REAL_REFERENCE_READY, controller_identity=cc, reviewer_identity=vv, authority_object_resolver=rr.get, dependency_verifier=deps.get) and "PROMOTED", True)
cc, vv, rr = actors([dep, ref], cid="C1", rid=pa)
t("T3-B reviewer actor == producer actor refused", lambda: r.promote_unit(reg, "G8", Q.REAL_REFERENCE_READY, controller_identity=cc, reviewer_identity=vv, authority_object_resolver=rr.get, dependency_verifier=deps.get) and "PROMOTED", True)
cc, vv, rr = actors([dep, ref], cid="minted-by-producer-1")
t("NOTE self-minted controller actor (any new string) is accepted -> no actor registry", lambda: r.promote_unit(reg, "G8", Q.REAL_REFERENCE_READY, controller_identity=cc, reviewer_identity=vv, authority_object_resolver=rr.get, dependency_verifier=deps.get) and "PROMOTED", False)

print("== H3/H4: verification cache poisoning and resolver change")
cache = {}
r.derive_real_reference_ready("G8", reg, dependency_verifier=deps.get, authority_object_resolver=res.get, verification_cache=cache)
t("H4 cached positive must not survive a resolver that lacks the objects", lambda: (lambda rr: (_ for _ in ()).throw(AssertionError("ready with empty resolver")) if rr.ready else rr.blockers[0])(r.derive_real_reference_ready("G8", reg, dependency_verifier=(lambda s: None), authority_object_resolver=res.get, verification_cache=cache)), False)
poison = {}
for u in (dep, ref):
    for fld in r._IDENTITY_64_FIELDS + r._IDENTITY_40_FIELDS:
        poison[("dependency-object-v1", u.canonical_sha256(), fld, getattr(u, fld))] = (True, None)
t("H3 caller-poisoned cache must not authenticate unresolvable dependencies", lambda: (lambda rr: (_ for _ in ()).throw(AssertionError("ready via poisoned cache")) if rr.ready else rr.blockers[0])(r.derive_real_reference_ready("G8", reg, dependency_verifier=(lambda s: None), authority_object_resolver=res.get, verification_cache=poison)), False)

print("== H5/H6: provenance and history")
regR = r.revoke_or_supersede(reg1, "G8", L.REVOKED_BY_DEFECT, reason_class="DEFECT", controller_identity=c, authority_object_resolver=res.get, dependency_verifier=deps.get)
un = dataclasses.replace(regR.units_by_id()["G8"], active_lineage_status=L.ACTIVE)
forged_back = r.TDQualificationRegistry(tuple(un if u.unit_id == "G8" else u for u in regR.units), regR.prerequisites, regR.promotions, ())
t("H6 revocation receipt deleted + unit set ACTIVE must be detected (revoked unit re-promoted)", lambda: r.promote_unit(r.TDQualificationRegistry(forged_back.units, reg1b.prerequisites, forged_back.promotions, ()), "G8", Q.HUMAN_EXECUTABLE, controller_identity=c, reviewer_identity=v, authority_object_resolver=res2.get, dependency_verifier=deps.get) and "RE-PROMOTED AFTER REVOCATION", True)

# H5: hand-construct G8 directly at REAL_REFERENCE_READY with fabricated snapshot + receipt
# (the authoritative source copy at review head 869ca777 contains the complete setup).

print("== packet T3-C spot checks")
t("T3-C missing dependency resolver blocks readiness", lambda: (lambda rr: rr.ready and (_ for _ in ()).throw(AssertionError("ready")) or rr.blockers[0])(r.derive_real_reference_ready("G8", reg, authority_object_resolver=res.get)), False)
t("T3-C boolean True resolver blocks readiness", lambda: (lambda rr: rr.ready and (_ for _ in ()).throw(AssertionError("ready")) or rr.blockers[0])(r.derive_real_reference_ready("G8", reg, dependency_verifier=(lambda s: True), authority_object_resolver=res.get)), False)
t("T3-C asserted_ready=True ignored when prerequisite missing", lambda: (lambda rr: rr.ready and (_ for _ in ()).throw(AssertionError("ready")) or rr.unsatisfied_prerequisite_ids)(r.derive_real_reference_ready("G8", r.TDQualificationRegistry((dep, dataclasses.replace(ref, active_lineage_status=L.REVOKED_BY_DEFECT)), (p,), (), ()), asserted_ready=True, dependency_verifier=deps.get, authority_object_resolver=res.get)), False)
print(f"\nSUMMARY: {sum(out)}/{len(out)} expected; BAD={len(out)-sum(out)}")

# Custody note: this mirrored probe is retained for takeover convenience. The exact authoritative source bytes are at
# review head 869ca777a498181c519ccfc04b8bf5db0f2888c7, blob f7811887c3c4e475b666e9558449ac5f7cfe71f5.
