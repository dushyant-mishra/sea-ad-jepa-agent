import sys, hashlib, subprocess, enum, random
sys.path.insert(0, r"D:/jepa_task1_recheck_799d2e23")
import numpy as np
from scripts.v5.td_unified import canonical_v1 as C, authority_v1 as A
def t(label, f, expect_raise):
    try: r = f(); ok = not expect_raise; print(("OK  " if ok else "BAD ")+label, "->", str(r)[:100])
    except Exception as e: ok = expect_raise; print(("OK  " if ok else "BAD ")+label, "-> RAISES", type(e).__name__, str(e)[:80])
print("== T1-B1")
t("np.float64(1.5) bytes == float 1.5 bytes", lambda: C.canonical_bytes({"x": np.float64(1.5)}) == b'{"x":1.5}' or (_ for _ in ()).throw(AssertionError(C.canonical_bytes({"x": np.float64(1.5)}))), False)
class F(float):
    def __repr__(self): return "999"
class I(int):
    def __str__(self): return "777"
class S(str):
    def replace(self, *a): return "FORGED"
class D(dict): pass
class L(list): pass
class G(np.float64): pass
for lab, v in [("float subclass", F(1.5)), ("int subclass", I(3)), ("str subclass", S("x")), ("dict subclass", D(a=1)), ("list subclass", L([1])), ("np.float64 subclass", G(1.5)), ("np.str_", np.str_("a")), ("np.complex128", np.complex128(1)), ("np.datetime64", np.datetime64("2026-01-01")), ("np.ndarray", np.array([1.0]))]:
    t("rejects "+lab, lambda v=v: C.canonical_bytes({"x": v}), True)
class E(enum.IntEnum):
    A = 1
t("rejects IntEnum (int subclass)", lambda: C.canonical_bytes({"x": E.A}), True)
t("np.float32(0.1) widened like old Task1", lambda: C.canonical_bytes(np.float32(0.1)), False)
t("np.int64 / np.uint64 max", lambda: C.canonical_bytes([np.int64(-5), np.uint64(2**64-1), np.bool_(True)]), False)
old = subprocess.check_output(["git","-C",r"D:/Jepa project","show","ff597faf:scripts/production_synthetic/canonical_v1.py"]); ns={}; exec(compile(old,"old","exec"), ns)
random.seed(7); mism=0; n=0
pool=[None,True,False,0,-0.0,1.0,0.1,5e-324,1e308,2**63,"a\r\nb","\u00e9",np.float64(0.1),np.float32(0.1),np.float16(0.5),np.int8(-3),np.uint64(2**64-1),np.bool_(False),np.int64(7)]
def rnd(d=0):
    r=random.random()
    if d>3 or r<0.35: return random.choice(pool)
    if r<0.65: return [rnd(d+1) for _ in range(random.randint(0,4))]
    return {random.choice("abcé")+str(random.randint(0,4)): rnd(d+1) for _ in range(random.randint(0,4))}
for _ in range(4000):
    x=rnd(); n+=1
    try: a=ns["canonical_json_bytes"](x)
    except Exception as e: a=("E",)
    try: b=C.canonical_bytes(x)
    except Exception as e: b=("E",)
    if a!=b: mism+=1; ex=(x,a,b)
print(f"old-vs-unified incl numpy scalars: {mism} mismatches / {n}")
if mism: print("  example", ex)
print("== T1-B5 independent KAT")
kat = hashlib.sha256(b"JEPA-TD-UNIFIED-CANONICAL-V1\x00" + b'{"a":1,"b":[true,null,1.0]}').hexdigest()
print("independent hashlib:", kat, "module:", C.canonical_sha256({"b":[True,None,1.0],"a":1}), "equal:", kat == C.canonical_sha256({"b":[True,None,1.0],"a":1}))
print("== T1-B2 / T1-B3")
code = b"def produce():\n    return 1\n"
code_sha = hashlib.sha1(b"blob %d\0" % len(code) + code).hexdigest()
store = {code_sha: code}
def put(o):
    s=C.canonical_sha256(o); store[s]=o; return s
inp=put({"object_role":"INPUT","x":1}); out=put({"object_role":"OUTPUT","y":2}); man=put({"object_role":"MANIFEST","m":1}); reg=put({"object_role":"REGISTRY","r":1}); acc=put({"object_role":"ACCESS_POLICY","a":1})
good=C.make_scientific_receipt(payload={"p":1}, producer_code_sha=code_sha, input_shas=[inp], parent_receipt_shas=[], output_sha=out, manifest_sha=man, registry_sha=reg, access_policy_sha=acc)
t("valid receipt verifies", lambda: C.verify_scientific_receipt(good, store.get).receipt_sha256[:12], False)
t("producer 0*40 refused", lambda: C.verify_scientific_receipt(C.make_scientific_receipt(payload={"p":1}, producer_code_sha="0"*40, input_shas=[inp], parent_receipt_shas=[], output_sha=out, manifest_sha=man, registry_sha=reg, access_policy_sha=acc), store.get), True)
other=b"tampered\n"; store["f"*40]=other
t("producer resolving to wrong bytes refused", lambda: C.verify_scientific_receipt(C.make_scientific_receipt(payload={"p":1}, producer_code_sha="f"*40, input_shas=[inp], parent_receipt_shas=[], output_sha=out, manifest_sha=man, registry_sha=reg, access_policy_sha=acc), store.get), True)
store[code_sha+"x"]=None
s2=dict(store); s2[code_sha]=code.decode()
t("producer resolving to str (not bytes) refused", lambda: C.verify_scientific_receipt(good, s2.get), True)
empty=put({})
t("{} as all four roles refused", lambda: C.verify_scientific_receipt(C.make_scientific_receipt(payload={"p":2}, producer_code_sha=code_sha, input_shas=[inp], parent_receipt_shas=[], output_sha=empty, manifest_sha=empty, registry_sha=empty, access_policy_sha=empty), store.get), True)
t("input reused as output refused", lambda: C.verify_scientific_receipt(C.make_scientific_receipt(payload={"p":3}, producer_code_sha=code_sha, input_shas=[inp], parent_receipt_shas=[], output_sha=inp, manifest_sha=man, registry_sha=reg, access_policy_sha=acc), store.get), True)
t("manifest object in registry slot refused", lambda: C.verify_scientific_receipt(C.make_scientific_receipt(payload={"p":4}, producer_code_sha=code_sha, input_shas=[inp], parent_receipt_shas=[], output_sha=out, manifest_sha=man, registry_sha=man, access_policy_sha=acc), store.get), True)
store[good["receipt_sha256"]]=good
t("receipt in access-policy slot refused", lambda: C.verify_scientific_receipt(C.make_scientific_receipt(payload={"p":5}, producer_code_sha=code_sha, input_shas=[inp], parent_receipt_shas=[], output_sha=out, manifest_sha=man, registry_sha=reg, access_policy_sha=good["receipt_sha256"]), store.get), True)
print("== T1-B4")
Q=A.QualificationStage; St=A.ActiveLineageStatus
for scope in ["PIPELINE","PROJECT_WIDE","TD_PIPELINE","ALL","GLOBAL_PROJECT","project-training","TRAINING_PROJECT","Project Training","PROJECT\n","UNIT:G9","PIPELINE:G8 ","unit:G8","UNIT:G8__NO_TRAINING_AUTHORITY"]:
    t(f"refuses scope {scope!r} for unit G8", lambda scope=scope: A.validate_authority_record(A.AuthorityRecord("G8", Q.FIXTURE_SAME_INTERFACE, St.ACTIVE, scope)), True)
t("UNIT:G8 @ FIXTURE accepted", lambda: A.validate_authority_record(A.AuthorityRecord("G8", Q.FIXTURE_SAME_INTERFACE, St.ACTIVE, "UNIT:G8")).authority_scope, False)
t("UNIT:G8 @ DOWNSTREAM_CERTIFIED refused", lambda: A.validate_authority_record(A.AuthorityRecord("G8", Q.DOWNSTREAM_CERTIFIED, St.ACTIVE, "UNIT:G8")), True)
t("UNIT:G8 @ TRAINING_AUTHORIZED refused", lambda: A.validate_authority_record(A.AuthorityRecord("G8", Q.TRAINING_AUTHORIZED, St.ACTIVE, "UNIT:G8")), True)
t("PIPELINE:TD @ FIXTURE refused", lambda: A.validate_authority_record(A.AuthorityRecord("TD", Q.FIXTURE_SAME_INTERFACE, St.ACTIVE, "PIPELINE:TD")), True)
t("PROJECT with unit_id G8 refused", lambda: A.validate_authority_record(A.AuthorityRecord("G8", Q.TRAINING_AUTHORIZED, St.ACTIVE, "PROJECT")), True)
t("PROJECT @ TRAINING_ELIGIBLE refused", lambda: A.validate_authority_record(A.AuthorityRecord("PROJECT", Q.TRAINING_ELIGIBLE, St.ACTIVE, "PROJECT")), True)
t("lowercase restriction refused", lambda: A.validate_authority_record(A.AuthorityRecord("G8", Q.SEMANTICS_ONLY, St.ACTIVE, "UNIT:G8", ("no_training",))), True)
t("restriction list (not tuple) refused", lambda: A.validate_authority_record(A.AuthorityRecord("G8", Q.SEMANTICS_ONLY, St.ACTIVE, "UNIT:G8", ["NO_TRAINING"])), True)
t("unit_id int refused as AuthorityError", lambda: A.validate_authority_record(A.AuthorityRecord(5, Q.SEMANTICS_ONLY, St.ACTIVE, "UNIT:5")), True)
