"""Macha focused hostile re-check 2 of Unified Task 3 at d9e58a18 (N1, N2, B3-V, B3-E, B3-R, B5-F).

Synthetic only. The reader split is the synthetic 104/22/23 file used by Task 2's own tests, with
FROZEN_READER_SPLIT_SHA256 monkeypatched exactly as those tests do (simulates the controller holding the
frozen split). No real, protected or biological bytes are read. Run from the review worktree root.
"""
import dataclasses
import hashlib
import os
import subprocess
import sys
import types

repo = os.getcwd()
sys.path.insert(0, repo)
_m = types.ModuleType("tests")  # pin repo `tests` ahead of PyMC's site-packages `tests`
_m.__path__ = [os.path.join(repo, "tests")]
sys.modules["tests"] = _m

from scripts.v5.td_unified import registry_v1 as r  # noqa: E402
from scripts.v5.td_unified import registry_v1_legacy as legacy  # noqa: E402
from scripts.v5.td_unified import manifest_v1 as M  # noqa: E402
from scripts.v5.td_unified import task3_trust_roots_v1 as roots  # noqa: E402
from scripts.v5.td_unified.authority_v1 import ActiveLineageStatus as L  # noqa: E402
from scripts.v5.td_unified.authority_v1 import QualificationStage as Q  # noqa: E402
from scripts.v5.td_unified.canonical_v1 import canonical_sha256 as csha  # noqa: E402
from tests.v5.td_unified import registry_v1_dependency_fixtures as fx  # noqa: E402
from tests.v5.td_unified.test_registry_v1_macha_rejection import _actors, _setup  # noqa: E402

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
    print(f"{tag} {name} -> {'REFUSED' if refused else 'ACCEPTED'}: {ascii(str(detail))[:230]}")
    return None if refused else out


def stage(reg, uid="G8"):
    return reg.units_by_id()[uid].qualification_stage.value


# ---------------------------------------------------------------- Task-2-valid synthetic world
rows = ["donor_id,reader_partition"] + [f"F{i:03d},reader_fit" for i in range(104)]
rows += [f"V{i:03d},reader_validation" for i in range(22)] + [f"O{i:03d},reader_oracle" for i in range(23)]
RAW_BYTES = ("\n".join(rows) + "\n").encode()
RAW_SHA = hashlib.sha256(RAW_BYTES).hexdigest()
M.FROZEN_READER_SPLIT_SHA256 = RAW_SHA
RAW = {RAW_SHA: RAW_BYTES}.get
POLICY = M.build_current_td_access_policy_from_reader_split(reader_split_raw=RAW_BYTES)


def world(specs):
    store = {}

    def put(o):
        h = csha(o)
        store[h] = o
        return h

    def code(b):
        h = hashlib.sha1(f"blob {len(b)}\0".encode() + b).hexdigest()
        store[h] = b
        return h

    ids_by, table_rows = {}, []
    for uid, _ in specs:
        ids, objs = fx._core(uid)
        store.update(objs)
        ids_by[uid] = ids
        table_rows.append(fx._row(uid, ids))
    f = {"access_policy_sha": put(POLICY.to_payload()),
         "population_split_registry_sha": put({"object_role": "POPULATION_SPLIT_REGISTRY", "reader_split_raw_sha256": RAW_SHA,
                                               "population_registry_sha256": M.FROZEN_POPULATION_REGISTRY_SHA256}),
         "crossfit_policy_sha": put(M.derive_crossfit_policy_payload(POLICY)),
         "protected_partition_policy_sha": put(M.derive_protected_partition_policy_payload(POLICY))}
    for part in ("reader_fit", "reader_validation", "reader_oracle"):
        f[f"{part}_policy_sha"] = put(M.derive_reader_partition_policy_payload(POLICY, part))
    norm = put({"object_role": "NORMALIZATION_CONTRACT", "rule": "n"})
    lib = put({"object_role": "LIBRARY_CONTRACT", "rule": "l"})
    f["normalization_library_contract_sha"] = put({"object_role": "NORMALIZATION_LIBRARY_CONTRACT",
                                                   "contract_schema": "NORMALIZATION_LIBRARY_CONTRACT_IDENTITY_V1",
                                                   "normalization_contract_sha": norm, "library_contract_sha": lib})
    f["target_portfolio_code_identity_sha"] = put({"object_role": "TARGET_PORTFOLIO_CODE_IDENTITY", "identity_schema": "GIT_BLOB_IDENTITY_V1",
                                                   "git_blob_sha1": code(b"def portfolio(): pass\n")})
    f["target_portfolio_policy_sha"] = put({"object_role": "TARGET_PORTFOLIO_POLICY", "policy_schema": "TARGET_PORTFOLIO_POLICY_IDENTITY_V1",
                                            "policy_contract_sha": put({"object_role": "TARGET_PORTFOLIO_POLICY_CONTRACT", "c": 1})})
    f["unit_execution_identity_table_sha"] = put({"object_role": "UNIT_EXECUTION_IDENTITY_TABLE",
                                                  "table_schema": "UNIT_EXECUTION_IDENTITY_TABLE_V1", "units": table_rows})
    for field, role in M._MANIFEST_ROLE_BY_FIELD.items():
        if field not in f:
            f[field] = put({"object_role": role, "x": field})
    manifest = {"schema": "TD_EXECUTION_MANIFEST_V1", "controller_code_sha": code(b"controller = 1\n"), **f}
    msha = put(manifest)
    M.validate_manifest(dict(manifest), store.get, raw_resolver=RAW)  # positive control: frozen Task 2 accepts
    units = [fx._build_unit(r, uid, ids_by[uid], manifest_sha=msha, access_sha=f["access_policy_sha"], stage=st,
                            status=L.ACTIVE, population_authority="AUTHENTICATED_READER_SPLIT",
                            claim_scope="POOLED_DONOR_LEVEL") for uid, st in specs]
    return units, store


def bind(units, prereqs, store, trusted=None):
    c, v, ao = _actors()
    trusted_objs = tuple(ao.values()) if trusted is None else tuple(trusted)
    reg = r.TDQualificationRegistry(tuple(units), tuple(prereqs), (), ())
    extra = {csha(o): o for o in trusted_objs}
    reg, objs = fx.bind_actor_registry(r, reg, {**store, **ao, **extra}, trusted_actor_objects=trusted_objs)
    return reg, c, v, objs


def rrr(reg, c, v, objs, raw=RAW, uid="G8"):
    return stage(r.promote_unit(reg, uid, Q.REAL_REFERENCE_READY, controller_identity=c, reviewer_identity=v,
                                authority_object_resolver=objs.get, dependency_verifier=objs.get, raw_resolver=raw), uid)


KTQ = Q.KNOWN_TRUTH_QUALIFIED

print("== N1 frozen Task 2 binding at the RRR boundary")
(g8, ref), store = world([("G8", KTQ), ("REF", KTQ)])
print("    positive control: frozen Task 2 validate_manifest accepts the synthetic world manifest")
reg, c, v, objs = bind((g8, ref), (fx.verified_prereq(r, g8, ref),), store)
_, _, dd, _, fixreg, fc, fv, fobjs = _setup()
t("N1 PR fixture manifest (not Task-2-valid) -> RRR", lambda: stage(r.promote_unit(
    fixreg, "G8", Q.REAL_REFERENCE_READY, controller_identity=fc, reviewer_identity=fv,
    authority_object_resolver=fobjs.get, dependency_verifier=dd.get, raw_resolver=RAW)), True)
t("N1 Task-2-valid manifest but no raw resolver -> RRR", lambda: rrr(reg, c, v, objs, raw=None), True)
t("N1 Task-2-valid manifest, altered split bytes -> RRR",
  lambda: rrr(reg, c, v, objs, raw={RAW_SHA: RAW_BYTES.replace(b"reader_fit", b"reader_fiT", 1)}.get), True)
t("NOTE derive_real_reference_ready (diagnostic) on the PR fixture (no Task 2 validation)",
  lambda: r.derive_real_reference_ready("G8", fixreg, dependency_verifier=dd.get, authority_object_resolver=fobjs.get).ready,
  False, note=True)

print("== N2 KNOWN_TRUTH_QUALIFIED by declaration")
t("N2 custody genesis declaring KTQ", lambda: r.RegistryHistoryCustody(reg, attestation_key=b"k"), True)
t("N2 history-free registry DECLARING G8+REF at KTQ (no SEALED_CHALLENGE_REVIEW), no custody, Task-2-valid -> RRR",
  lambda: rrr(reg, c, v, objs), True)

print("== B3-V content validators")
(g8b, refb), storeb = world([("G8", KTQ), ("REF", KTQ)])
p1 = fx.verified_prereq(r, g8b, refb)
val = {"object_role": "CONTENT_VALIDATOR", "actor_id": "producer:G8"}
rec = {"object_role": "CONTENT_VALIDATION_RECEIPT", "receipt_schema": "CONTENT_VALIDATION_RECEIPT_V1", "prerequisite_id": "P1",
       "content_identity_sha": p1.prerequisite_unit_sha, "validator_identity_sha": csha(val), "status": "QUALIFIED"}
storeb.update({csha(val): val, csha(rec): rec})
regb, cb, vb, objsb = bind((g8b, refb), (dataclasses.replace(p1, content_required=True, content_validated=True,
                                                              content_validation_receipt_sha=csha(rec)),), storeb)
t("B3-V direct prerequisite, validator = unregistered producer:G8 -> RRR", lambda: rrr(regb, cb, vb, objsb), True)

(g8n, refn, ref2n), storen = world([("G8", KTQ), ("REF", KTQ), ("REF2", KTQ)])
pa = fx.verified_prereq(r, g8n, refn, pid="P1")
pb = fx.verified_prereq(r, refn, ref2n, pid="P2")
recn = dict(rec, prerequisite_id="P2", content_identity_sha=pb.prerequisite_unit_sha)
storen.update({csha(val): val, csha(recn): recn})
pbc = dataclasses.replace(pb, content_required=True, content_validated=True, content_validation_receipt_sha=csha(recn))
regn, cn, vn, objsn = bind((g8n, refn, ref2n), (pa, pbc), storen)
t("B3-V NESTED: REF's own RRR prerequisite validated by unregistered producer:G8; actor gate on G8",
  lambda: r._require_registered_prerequisite_actors(regn, "G8", gate="REAL_REFERENCE_READY",
                                                    authority_object_resolver=objsn.get, dependency_verifier=objsn.get) or "passed", True)
t("B3-V NESTED through promote_unit G8 -> RRR", lambda: rrr(regn, cn, vn, objsn), True)

print("== B3-E evidence issuers")
harness = {"object_role": "PREREQUISITE_EVIDENCE_ISSUER", "actor_id": "HARNESS"}
prod_issuer = {"object_role": "PREREQUISITE_EVIDENCE_ISSUER", "actor_id": "producer:G8"}
minted_issuer = {"object_role": "PREREQUISITE_EVIDENCE_ISSUER", "actor_id": "minted-issuer"}


def iso_reg(issuer_obj, trust_issuer):
    (gx, rx), sx = world([("G8", KTQ), ("REF", KTQ)])
    ev = {"object_role": "PREREQUISITE_EVIDENCE", "requirement_class": "PROCESS_ISOLATION", "producer_process_isolated": True,
          "harness_drives_finalization": True, "reader_fit_values_out_of_process": True,
          "protected_partitions_physically_absent": True}
    if issuer_obj is not None:
        ev["issuer_identity_sha"] = csha(issuer_obj)
        sx[csha(issuer_obj)] = issuer_obj
    sx[csha(ev)] = ev
    iso = dataclasses.replace(fx.verified_prereq(r, gx, rx, pid="ISO", gate="HUMAN_EXECUTABLE", requirement_class="PROCESS_ISOLATION"),
                              evidence_receipt_sha=csha(ev))
    c0, v0, ao0 = _actors()
    trusted = tuple(ao0.values()) + ((issuer_obj,) if trust_issuer else ())
    return bind((gx, rx), (fx.verified_prereq(r, gx, rx), iso), sx, trusted=trusted)


for lbl, iobj, trust in (("no issuer", None, False), ("issuer = producer:G8 (registered)", prod_issuer, True),
                         ("issuer unregistered", minted_issuer, False)):
    rg, cc, vv, oo = iso_reg(iobj, trust)
    t(f"B3-E HUMAN_EXECUTABLE evidence, {lbl}", lambda: r._require_registered_prerequisite_actors(
        rg, "G8", gate="HUMAN_EXECUTABLE", authority_object_resolver=oo.get, dependency_verifier=oo.get) or "passed", True)
rg, cc, vv, oo = iso_reg(minted_issuer, True)
t("B3-E minted issuer registered by producer: frozen privileged-actor policy",
  lambda: roots.require_frozen_privileged_actor_policy(rg.actor_registry_sha, oo.get) and "passed", True)
rg, cc, vv, oo = iso_reg(harness, True)
t("B3-E positive control: issuer HARNESS (registered) passes the issuer gate", lambda: r._require_registered_prerequisite_actors(
    rg, "G8", gate="HUMAN_EXECUTABLE", authority_object_resolver=oo.get, dependency_verifier=oo.get) or "passed", False)

print("== B3-R actor registry anchor")
mc = {"object_role": "QUALIFICATION_CONTROLLER", "actor_id": "minted-by-producer-1"}
mr = {"object_role": "INDEPENDENT_REVIEWER", "actor_id": "minted-by-producer-2"}
(g8r, refr), storer = world([("G8", KTQ), ("REF", KTQ)])
regr, _, _, objsr = bind((g8r, refr), (fx.verified_prereq(r, g8r, refr),), storer, trusted=(mc, mr))
t("B3-R producer-authored registry, minted controller+reviewer -> RRR",
  lambda: rrr(regr, csha(mc), csha(mr), objsr), True)
fake_c1 = {"object_role": "QUALIFICATION_CONTROLLER", "actor_id": "C1", "minted_by": "producer:G8"}
r1 = {"object_role": "INDEPENDENT_REVIEWER", "actor_id": "R1"}
regf, _, _, objsf = bind((g8r, refr), (fx.verified_prereq(r, g8r, refr),), storer, trusted=(fake_c1, r1))
t("NOTE producer-authored registry whose 'C1' controller object is producer-made (names pinned, not digests) -> RRR",
  lambda: rrr(regf, csha(fake_c1), csha(r1), objsf), False, note=True)

print("== B5-F revocation anchoring")


def genesis(prefix):
    d, rf, deps = fx.verified_pair(r, dep_id=f"{prefix}_G8", ref_id=f"{prefix}_REF", dep_stage=Q.SEMANTICS_ONLY, ref_stage=Q.SEMANTICS_ONLY)
    reg0 = r.TDQualificationRegistry((d, rf), (), (), ())
    c0, v0, ao0 = _actors()
    reg0, o0 = fx.bind_actor_registry(r, reg0, {**deps, **ao0}, trusted_actor_objects=tuple(ao0.values()))
    return reg0, c0, v0, o0


def revoke(reg0, uid, c0, o0, cust):
    return r.revoke_or_supersede(reg0, uid, L.REVOKED_BY_DEFECT, reason_class="DEFECT", controller_identity=c0,
                                 authority_object_resolver=o0.get, dependency_verifier=o0.get, history_custody=cust)


def up(reg0, uid, dst, c0, v0, o0, cust=None):
    return r.promote_unit(reg0, uid, dst, controller_identity=c0, reviewer_identity=v0, authority_object_resolver=o0.get,
                          dependency_verifier=o0.get, history_custody=cust)


g0, c0, v0, o0 = genesis("F1")
revoke(g0, "F1_G8", c0, o0, r.RegistryHistoryCustody(g0, attestation_key=b"a"))
t("B5-F the PR's exact attack: fresh custody from the same genesis after revocation",
  lambda: r.RegistryHistoryCustody(g0, attestation_key=b"b"), True)

g0, c0, v0, o0 = genesis("F2")
cust_a = r.RegistryHistoryCustody(g0, attestation_key=b"a")
cust_b = r.RegistryHistoryCustody(g0, attestation_key=b"b")  # forked before the revocation
revoke(g0, "F2_G8", c0, o0, cust_a)
t("B5-F FORK: custody B created before the revocation keeps promoting the revoked identity",
  lambda: stage(up(g0, "F2_G8", Q.FIXTURE_SAME_INTERFACE, c0, v0, o0, cust_b), "F2_G8"), True)

g0, c0, v0, o0 = genesis("F3")
revoke(g0, "F3_G8", c0, o0, r.RegistryHistoryCustody(g0, attestation_key=b"a"))
t("B5-F NO CUSTODY: history-free registry promotes the anchored revoked identity",
  lambda: stage(up(g0, "F3_G8", Q.FIXTURE_SAME_INTERFACE, c0, v0, o0), "F3_G8"), True)

g0, c0, v0, o0 = genesis("F4")
cust_a = r.RegistryHistoryCustody(g0, attestation_key=b"a")
g1 = up(g0, "F4_G8", Q.FIXTURE_SAME_INTERFACE, c0, v0, o0, cust_a)
revoked_sha = g1.units_by_id()["F4_G8"].canonical_sha256()
revoke(g1, "F4_G8", c0, o0, cust_a)


def stage_shift():
    cust_b = r.RegistryHistoryCustody(g0, attestation_key=b"b")  # earlier-stage identity is not in the anchor
    g2 = up(g0, "F4_G8", Q.FIXTURE_SAME_INTERFACE, c0, v0, o0, cust_b)
    same = g2.units_by_id()["F4_G8"].canonical_sha256() == revoked_sha
    return f"{stage(g2, 'F4_G8')}; identity equal to the anchored revoked identity: {same}"


t("B5-F STAGE SHIFT: revoke at FIXTURE_SAME_INTERFACE, restart genesis at SEMANTICS_ONLY, re-promote", stage_shift, True)

(g8x, refx), storex = world([("X_G8", Q.SEMANTICS_ONLY), ("X_REF", Q.SEMANTICS_ONLY)])
regx, cx, vx, objsx = bind((g8x, refx), (), storex)
revoke(regx, "X_G8", cx, objsx, r.RegistryHistoryCustody(regx, attestation_key=b"a"))
(g8k, refk), storek = world([("X_G8", KTQ), ("X_REF", KTQ)])  # same execution identities, stage declared
regk, ck, vk, objsk = bind((g8k, refk), (fx.verified_prereq(r, g8k, refk),), storek)
t("B5-F + N2 COMBINED: unit REVOKED_BY_DEFECT under custody, then declared KTQ in a history-free registry -> RRR",
  lambda: rrr(regk, ck, vk, objsk, uid="X_G8"), True)

g0, c0, v0, o0 = genesis("F5")
revoke(g0, "F5_G8", c0, o0, r.RegistryHistoryCustody(g0, attestation_key=b"a"))
t("NOTE in-process anchor clear (r._PROCESS_REVOCATION_ANCHOR.clear()) then fresh custody",
  lambda: (r._PROCESS_REVOCATION_ANCHOR.clear(), r.RegistryHistoryCustody(g0, attestation_key=b"b"))[1] and "created",
  False, note=True)

child = (
    "import os,sys,types; sys.path.insert(0,os.getcwd()); m=types.ModuleType('tests'); m.__path__=[os.path.join(os.getcwd(),'tests')]; sys.modules['tests']=m\n"
    "from scripts.v5.td_unified import registry_v1 as r\n"
    "from scripts.v5.td_unified.authority_v1 import QualificationStage as Q\n"
    "from tests.v5.td_unified import registry_v1_dependency_fixtures as fx\n"
    "from tests.v5.td_unified.test_registry_v1_macha_rejection import _actors\n"
    "d,rf,deps=fx.verified_pair(r,dep_id='F6_G8',ref_id='F6_REF',dep_stage=Q.SEMANTICS_ONLY,ref_stage=Q.SEMANTICS_ONLY)\n"
    "reg=r.TDQualificationRegistry((d,rf),(),(),()); c,v,ao=_actors()\n"
    "reg,o=fx.bind_actor_registry(r,reg,{**deps,**ao},trusted_actor_objects=tuple(ao.values()))\n"
    "r.RegistryHistoryCustody(reg,attestation_key=b'b'); print('created')\n"
)
g0, c0, v0, o0 = genesis("F6")
revoke(g0, "F6_G8", c0, o0, r.RegistryHistoryCustody(g0, attestation_key=b"a"))
t("NOTE second process: fresh custody for the identity revoked in this process (disclosed R4)",
  lambda: subprocess.run([sys.executable, "-I", "-c", child], capture_output=True, text=True, cwd=repo, check=True).stdout.strip(),
  False, note=True)

(g8m, refm), storem = world([("G8", Q.SAME_CODE_PATH), ("REF", Q.SAME_CODE_PATH)])
regm, _, _, objsm = bind((g8m, refm), (), storem, trusted=(mc, mr))
t("NOTE revocation by a minted controller in a producer-authored registry (frozen policy not applied to revoke)",
  lambda: r.revoke_or_supersede(regm, "G8", L.REVOKED_BY_DEFECT, reason_class="DEFECT", controller_identity=csha(mc),
                                authority_object_resolver=objsm.get, dependency_verifier=objsm.get).revocations[-1].reason_class,
  False, note=True)

print("== regression B1 / B4 / B6 and legacy surface")
for src, dst in ((Q.HUMAN_EXECUTED, Q.DOWNSTREAM_CERTIFIED), (Q.TRAINING_ELIGIBLE, Q.TRAINING_AUTHORIZED)):
    (gx, rx), sx = world([("G8", src), ("REF", src)])
    rg, cc, vv, oo = bind((gx, rx), (), sx)
    for lbl, fn in (("facade", r.promote_unit), ("legacy", legacy.promote_unit)):
        t(f"B1 [{lbl}] {src.value} -> {dst.value}", lambda fn=fn: fn(rg, "G8", dst, controller_identity=cc, reviewer_identity=vv,
                                                                   authority_object_resolver=oo.get, dependency_verifier=oo.get), True)
poison = {("dependency-object-v1", u.canonical_sha256(), f, getattr(u, f)): (True, None)
          for u in (g8, ref) for f in r._IDENTITY_64_FIELDS + r._IDENTITY_40_FIELDS}
t("B4 poisoned cache + empty dependency resolver -> RRR", lambda: stage(r.promote_unit(
    reg, "G8", Q.REAL_REFERENCE_READY, controller_identity=c, reviewer_identity=v, authority_object_resolver=objs.get,
    dependency_verifier=lambda s: None, raw_resolver=RAW, verification_cache=poison)), True)
wf_dir = os.path.join(repo, ".github", "workflows")
writers = [n for n in sorted(os.listdir(wf_dir)) if any(k in open(os.path.join(wf_dir, n), encoding="utf-8").read()
                                                       for k in ("contents: write", "write-all", "git push", "git commit"))]
t(f"B6 committed workflows with write/commit/push ({len(os.listdir(wf_dir))} scanned)",
  lambda: (_ for _ in ()).throw(AssertionError(writers)) if writers else "none", False)
t("NOTE legacy.promote_unit -> RRR on the PR fixture (no Task 2, no frozen actors, no issuer gate)",
  lambda: stage(legacy.promote_unit(fixreg, "G8", Q.REAL_REFERENCE_READY, controller_identity=fc, reviewer_identity=fv,
                                    authority_object_resolver=fobjs.get, dependency_verifier=dd.get)), False, note=True)

print()
print(f"SUMMARY: {sum(RESULTS)}/{len(RESULTS)} expected; BAD={len(RESULTS) - sum(RESULTS)}")
