"""Macha focused hostile re-check 3 of Unified Task 3 at 117dd51d (N2, nested B3-V, B5-F variants, every-revocation).

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


def genesis(prefix, restrictions=None, stage0=Q.SEMANTICS_ONLY):
    d, rf, deps = fx.verified_pair(r, dep_id=f"{prefix}_G8", ref_id=f"{prefix}_REF", dep_stage=stage0, ref_stage=stage0)
    if restrictions is not None:
        d = dataclasses.replace(d, authority_restrictions=restrictions)
    reg0 = r.TDQualificationRegistry((d, rf), (), (), ())
    c0, v0, ao0 = _actors()
    reg0, o0 = fx.bind_actor_registry(r, reg0, {**deps, **ao0}, trusted_actor_objects=tuple(ao0.values()))
    return reg0, c0, v0, o0


def revoke(reg0, uid, c0, o0, cust=None, status=L.REVOKED_BY_DEFECT, **kw):
    return r.revoke_or_supersede(reg0, uid, status, reason_class="DEFECT", controller_identity=c0,
                                 authority_object_resolver=o0.get, dependency_verifier=o0.get, history_custody=cust, **kw)


def up(reg0, uid, dst, c0, v0, o0, cust=None, raw=None):
    return r.promote_unit(reg0, uid, dst, controller_identity=c0, reviewer_identity=v0, authority_object_resolver=o0.get,
                          dependency_verifier=o0.get, history_custody=cust, raw_resolver=raw)


def raises(msg):
    raise AssertionError(msg)


print("== N2 REAL_REFERENCE_READY and later require history custody")
(g8, ref), store = world([("G8", KTQ), ("REF", KTQ)])
reg, c, v, objs = bind((g8, ref), (fx.verified_prereq(r, g8, ref),), store)
t("N2 declared KTQ, Task-2-valid manifest, NO custody -> RRR", lambda: rrr(reg, c, v, objs), True)
t("N2 declared KTQ: custody genesis", lambda: r.RegistryHistoryCustody(reg, attestation_key=b"k"), True)
g0, c0, v0, o0 = genesis("N2A", stage0=Q.SAME_CODE_PATH)
cust = r.RegistryHistoryCustody(g0, attestation_key=b"k")
t("N2 lawful custody at SAME_CODE_PATH -> KNOWN_TRUTH_QUALIFIED (the only route to RRR)",
  lambda: stage(up(g0, "N2A_G8", KTQ, c0, v0, o0, cust), "N2A_G8"), True)
(g8h, refh), storeh = world([("G8", Q.REAL_REFERENCE_READY), ("REF", Q.REAL_REFERENCE_READY)])
regh, ch, vh, objsh = bind((g8h, refh), (), storeh)
t("N2 declared RRR, NO custody -> HUMAN_EXECUTABLE", lambda: stage(up(regh, "G8", Q.HUMAN_EXECUTABLE, ch, vh, objsh, raw=RAW)), True)
t("NOTE legacy.promote_unit still reaches RRR from declared KTQ without custody (public bypass, carried)",
  lambda: stage(legacy.promote_unit(reg, "G8", Q.REAL_REFERENCE_READY, controller_identity=c, reviewer_identity=v,
                                    authority_object_resolver=objs.get, dependency_verifier=objs.get)), False, note=True)

print("== B3-V nested validators")
val = {"object_role": "CONTENT_VALIDATOR", "actor_id": "producer:G8"}


def nested_world(depth):
    ids = ["G8"] + [f"REF{i}" for i in range(1, depth + 1)]
    units, st = world([(u, KTQ) for u in ids])
    pre = []
    for i in range(depth):
        p = fx.verified_prereq(r, units[i], units[i + 1], pid=f"P{i + 1}")
        if i == depth - 1:
            rec = {"object_role": "CONTENT_VALIDATION_RECEIPT", "receipt_schema": "CONTENT_VALIDATION_RECEIPT_V1",
                   "prerequisite_id": p.prerequisite_id, "content_identity_sha": p.prerequisite_unit_sha,
                   "validator_identity_sha": csha(val), "status": "QUALIFIED"}
            st.update({csha(val): val, csha(rec): rec})
            p = dataclasses.replace(p, content_required=True, content_validated=True, content_validation_receipt_sha=csha(rec))
        pre.append(p)
    return bind(units, pre, st)


for depth in (2, 3):
    rg, cc, vv, oo = nested_world(depth)
    t(f"B3-V nested depth {depth}: unregistered producer:G8 validator, actor gate on G8",
      lambda: r._require_registered_prerequisite_actors(rg, "G8", gate="REAL_REFERENCE_READY",
                                                        authority_object_resolver=oo.get, dependency_verifier=oo.get) or "passed", True)
    t(f"B3-V nested depth {depth} through promote_unit -> RRR", lambda: rrr(rg, cc, vv, oo), True)

print("== B5-F revocation anchor")
g0, c0, v0, o0 = genesis("F1")
revoke(g0, "F1_G8", c0, o0, r.RegistryHistoryCustody(g0, attestation_key=b"a"))
t("B5-F exact: fresh custody from the same genesis", lambda: r.RegistryHistoryCustody(g0, attestation_key=b"b"), True)
g0, c0, v0, o0 = genesis("F2")
cust_a = r.RegistryHistoryCustody(g0, attestation_key=b"a")
cust_b = r.RegistryHistoryCustody(g0, attestation_key=b"b")
revoke(g0, "F2_G8", c0, o0, cust_a)
t("B5-F fork: custody B (pre-revocation) promotes the revoked identity",
  lambda: stage(up(g0, "F2_G8", Q.FIXTURE_SAME_INTERFACE, c0, v0, o0, cust_b), "F2_G8"), True)
g0, c0, v0, o0 = genesis("F3")
revoke(g0, "F3_G8", c0, o0, r.RegistryHistoryCustody(g0, attestation_key=b"a"))
t("B5-F no custody: history-free promotion of the revoked identity",
  lambda: stage(up(g0, "F3_G8", Q.FIXTURE_SAME_INTERFACE, c0, v0, o0), "F3_G8"), True)
g0, c0, v0, o0 = genesis("F4")
cust_a = r.RegistryHistoryCustody(g0, attestation_key=b"a")
g1 = up(g0, "F4_G8", Q.FIXTURE_SAME_INTERFACE, c0, v0, o0, cust_a)
revoke(g1, "F4_G8", c0, o0, cust_a)
t("B5-F stage shift: revoked at FIXTURE_SAME_INTERFACE, restart genesis at SEMANTICS_ONLY",
  lambda: r.RegistryHistoryCustody(g0, attestation_key=b"b"), True)
(g8x, refx), storex = world([("X_G8", Q.SEMANTICS_ONLY), ("X_REF", Q.SEMANTICS_ONLY)])
regx, cx, vx, objsx = bind((g8x, refx), (), storex)
revoke(regx, "X_G8", cx, objsx, r.RegistryHistoryCustody(regx, attestation_key=b"a"))
(g8k, refk), storek = world([("X_G8", KTQ), ("X_REF", KTQ)])
regk, ck, vk, objsk = bind((g8k, refk), (fx.verified_prereq(r, g8k, refk),), storek)
t("B5-F + N2 combined: revoked identity declared KTQ -> RRR (no custody)", lambda: rrr(regk, ck, vk, objsk, uid="X_G8"), True)

print("== every revocation is anchored")
g0, c0, v0, o0 = genesis("E1")
revoke(g0, "E1_G8", c0, o0)
t("EVERY low-stage revocation WITHOUT custody, then history-free promotion",
  lambda: stage(up(g0, "E1_G8", Q.FIXTURE_SAME_INTERFACE, c0, v0, o0), "E1_G8"), True)
t("EVERY low-stage revocation WITHOUT custody, then fresh custody genesis",
  lambda: r.RegistryHistoryCustody(g0, attestation_key=b"x"), True)
g0, c0, v0, o0 = genesis("E2")
succ_sha = g0.units_by_id()["E2_REF"].canonical_sha256()


def supersede_then_promote():
    try:
        revoke(g0, "E2_G8", c0, o0, status=L.SUPERSEDED, successor_unit_id="E2_REF",
               successor_unit_sha=succ_sha, requalification_scope="UNIT:E2_REF")
    except Exception as exc:  # noqa: BLE001
        return f"supersession itself refused ({str(exc)[:80]}); not exercised"
    return stage(up(g0, "E2_G8", Q.FIXTURE_SAME_INTERFACE, c0, v0, o0), "E2_G8")


t("EVERY supersession is anchored (supersede E2_G8, then promote E2_G8)", supersede_then_promote, True)

print("== repair-targeted attacks on the anchor key")
g0, c0, v0, o0 = genesis("K1")
revoke(g0, "K1_G8", c0, o0, r.RegistryHistoryCustody(g0, attestation_key=b"a"))
for lbl, restr in (("one extra cosmetic restriction token", ("NO_TRAINING_AUTHORITY", "COSMETIC_V2")),
                   ("the same tokens reordered", ("COSMETIC_V2", "NO_TRAINING_AUTHORITY"))):
    def cosmetic(restr=restr):
        gk, ck2, vk2, ok2 = genesis("K1", restrictions=restr)
        same_exec = all(getattr(gk.units_by_id()["K1_G8"], f) == getattr(g0.units_by_id()["K1_G8"], f)
                        for f in r._IDENTITY_64_FIELDS + r._IDENTITY_40_FIELDS)
        custk = r.RegistryHistoryCustody(gk, attestation_key=b"c")
        out = up(gk, "K1_G8", Q.FIXTURE_SAME_INTERFACE, ck2, vk2, ok2, custk)
        return f"{stage(out, 'K1_G8')}; every code/policy/actor/manifest identity field unchanged: {same_exec}"
    t(f"B5-F KEY: revoked identity re-enters with {lbl} only", cosmetic, True)
t("NOTE lawful reidentify_unit changes a decision-bearing field and leaves REQUIRES_REQUALIFICATION",
  lambda: r.reidentify_unit(g0.units_by_id()["K1_G8"], claim_scope="FIXTURE_ONLY").active_lineage_status.value, False, note=True)

g0, c0, v0, o0 = genesis("T1")
cust_a = r.RegistryHistoryCustody(g0, attestation_key=b"a")
cust_b = r.RegistryHistoryCustody(g0, attestation_key=b"b")
revoke(g0, "T1_REF", c0, o0, cust_a)
t("NOTE revoked PREREQUISITE TARGET stays ACTIVE in forked custody B; its dependent's promotion is not anchor-checked for targets (latent: RRR closed)",
  lambda: stage(up(g0, "T1_G8", Q.FIXTURE_SAME_INTERFACE, c0, v0, o0, cust_b), "T1_G8"), False, note=True)

g0, c0, v0, o0 = genesis("P5")
revoke(g0, "P5_G8", c0, o0, r.RegistryHistoryCustody(g0, attestation_key=b"a"))
t("NOTE in-process anchor clear then fresh custody (R1 class)",
  lambda: (r._PROCESS_REVOCATION_ANCHOR.clear(), r.RegistryHistoryCustody(g0, attestation_key=b"b"))[1] and "created", False, note=True)
child = (
    "import os,sys,types; sys.path.insert(0,os.getcwd()); m=types.ModuleType('tests'); m.__path__=[os.path.join(os.getcwd(),'tests')]; sys.modules['tests']=m\n"
    "from scripts.v5.td_unified import registry_v1 as r\n"
    "from scripts.v5.td_unified.authority_v1 import QualificationStage as Q\n"
    "from tests.v5.td_unified import registry_v1_dependency_fixtures as fx\n"
    "from tests.v5.td_unified.test_registry_v1_macha_rejection import _actors\n"
    "d,rf,deps=fx.verified_pair(r,dep_id='P6_G8',ref_id='P6_REF',dep_stage=Q.SEMANTICS_ONLY,ref_stage=Q.SEMANTICS_ONLY)\n"
    "reg=r.TDQualificationRegistry((d,rf),(),(),()); c,v,ao=_actors()\n"
    "reg,o=fx.bind_actor_registry(r,reg,{**deps,**ao},trusted_actor_objects=tuple(ao.values()))\n"
    "r.RegistryHistoryCustody(reg,attestation_key=b'b'); print('created')\n"
)
g0, c0, v0, o0 = genesis("P6")
revoke(g0, "P6_G8", c0, o0, r.RegistryHistoryCustody(g0, attestation_key=b"a"))
t("NOTE second process: fresh custody for an identity revoked here (R4 open, disclosed)",
  lambda: subprocess.run([sys.executable, "-I", "-c", child], capture_output=True, text=True, cwd=repo, check=True).stdout.strip(),
  False, note=True)

print("== regression N1 / B3-E / B3-R / B1 / B4 / B6")
_, _, dd, _, fixreg, fc, fv, fobjs = _setup()
t("N1 PR fixture manifest (not Task-2-valid) -> RRR", lambda: stage(r.promote_unit(
    fixreg, "G8", Q.REAL_REFERENCE_READY, controller_identity=fc, reviewer_identity=fv,
    authority_object_resolver=fobjs.get, dependency_verifier=dd.get, raw_resolver=RAW)), True)
t("N1 frozen Task 2 binding, valid world, no raw resolver",
  lambda: r._require_frozen_task2_binding(reg, "G8", authority_object_resolver=objs.get, dependency_verifier=objs.get,
                                          raw_resolver=None) or "passed", True)
t("N1 positive control: frozen Task 2 binding passes on the valid world with raw resolver",
  lambda: r._require_frozen_task2_binding(reg, "G8", authority_object_resolver=objs.get, dependency_verifier=objs.get,
                                          raw_resolver=RAW) or "passed", False)
minted_issuer = {"object_role": "PREREQUISITE_EVIDENCE_ISSUER", "actor_id": "minted-issuer"}
mc = {"object_role": "QUALIFICATION_CONTROLLER", "actor_id": "minted-by-producer-1"}
mr = {"object_role": "INDEPENDENT_REVIEWER", "actor_id": "minted-by-producer-2"}
regm, _, _, objsm = bind((g8, ref), (fx.verified_prereq(r, g8, ref),), store, trusted=(mc, mr, minted_issuer))
t("B3-R/B3-E minted controller/reviewer/issuer: frozen privileged-actor policy",
  lambda: roots.require_frozen_privileged_actor_policy(regm.actor_registry_sha, objsm.get) and "passed", True)
for src, dst in ((Q.HUMAN_EXECUTED, Q.DOWNSTREAM_CERTIFIED), (Q.TRAINING_ELIGIBLE, Q.TRAINING_AUTHORIZED)):
    (gx, rx), sx = world([("G8", src), ("REF", src)])
    rg, cc, vv, oo = bind((gx, rx), (), sx)
    for lbl, fn in (("facade", r.promote_unit), ("legacy", legacy.promote_unit)):
        t(f"B1 [{lbl}] {src.value} -> {dst.value}", lambda fn=fn: fn(rg, "G8", dst, controller_identity=cc, reviewer_identity=vv,
                                                                   authority_object_resolver=oo.get, dependency_verifier=oo.get), True)
poison = {("dependency-object-v1", u.canonical_sha256(), f, getattr(u, f)): (True, None)
          for u in (g8, ref) for f in r._IDENTITY_64_FIELDS + r._IDENTITY_40_FIELDS}
t("B4 poisoned cache + empty dependency resolver (readiness)", lambda: r.derive_real_reference_ready(
    "G8", reg, dependency_verifier=lambda s: None, authority_object_resolver=objs.get, verification_cache=poison).ready
  or raises("not ready"), True)
wf_dir = os.path.join(repo, ".github", "workflows")
writers = [n for n in sorted(os.listdir(wf_dir)) if any(k in open(os.path.join(wf_dir, n), encoding="utf-8").read()
                                                       for k in ("contents: write", "write-all", "git push", "git commit"))]
t(f"B6 committed workflows with write/commit/push ({len(os.listdir(wf_dir))} scanned)",
  lambda: raises(str(writers)) if writers else "none", False)

print()
print(f"SUMMARY: {sum(RESULTS)}/{len(RESULTS)} expected; BAD={len(RESULTS) - sum(RESULTS)}")
