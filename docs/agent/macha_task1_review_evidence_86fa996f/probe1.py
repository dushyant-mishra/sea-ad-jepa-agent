import sys, time, enum, hashlib
sys.path.insert(0, r"D:/jepa_task1_review_86fa996f")
import numpy as np
from scripts.v5.td_unified import canonical_v1 as C, authority_v1 as A
def tryit(label, f):
    try: print(label, "->", f())
    except Exception as e: print(label, "-> RAISES", type(e).__name__, str(e)[:90])
# 1 numpy float64 repr leak
tryit("np.float64 bytes", lambda: C.canonical_bytes({"x": np.float64(1.5)}))
tryit("float 1.5 bytes", lambda: C.canonical_bytes({"x": 1.5}))
tryit("same digest float vs np.float64", lambda: C.canonical_sha256({"x": 1.5}) == C.canonical_sha256({"x": np.float64(1.5)}))
class F(float):
    def __repr__(self): return "999"
tryit("float subclass repr override", lambda: C.canonical_bytes({"x": F(1.5)}))
class Color(enum.IntEnum):
    RED = 1
tryit("IntEnum bytes", lambda: C.canonical_bytes({"x": Color.RED}))
tryit("np.int64", lambda: C.canonical_bytes({"x": np.int64(3)}))
tryit("np.bool_", lambda: C.canonical_bytes({"x": np.bool_(True)}))
# 2/3 receipt: forged producer code sha + role confusion with {}
store = {}
def put(o):
    s = C.canonical_sha256(o); store[s] = o; return s
empty = put({})
inp = put({"input": "real input"})
r = C.make_scientific_receipt(payload={"result": 1}, producer_code_sha="0"*40, input_shas=[inp], parent_receipt_shas=[], output_sha=empty, manifest_sha=empty, registry_sha=empty, access_policy_sha=empty)
tryit("receipt with producer 0*40 and {} as output/manifest/registry/access verifies", lambda: C.verify_scientific_receipt(r, store.get))
# input also used as output (role reuse)
r2 = C.make_scientific_receipt(payload={"result": 2}, producer_code_sha="f"*40, input_shas=[inp], parent_receipt_shas=[], output_sha=inp, manifest_sha=inp, registry_sha=inp, access_policy_sha=inp)
tryit("input reused as output/manifest/registry/access verifies", lambda: C.verify_scientific_receipt(r2, store.get))
# 5 diamond DAG blowup
prev = []
leaf = C.make_scientific_receipt(payload={"leaf":0}, producer_code_sha="a"*40, input_shas=[], parent_receipt_shas=[], output_sha=empty, manifest_sha=empty, registry_sha=empty, access_policy_sha=empty)
store[leaf["receipt_sha256"]] = leaf
level = [leaf["receipt_sha256"]]
for d in range(1, 21):
    a = C.make_scientific_receipt(payload={"d":d,"k":0}, producer_code_sha="a"*40, input_shas=[], parent_receipt_shas=list(level), output_sha=empty, manifest_sha=empty, registry_sha=empty, access_policy_sha=empty)
    b = C.make_scientific_receipt(payload={"d":d,"k":1}, producer_code_sha="a"*40, input_shas=[], parent_receipt_shas=list(level), output_sha=empty, manifest_sha=empty, registry_sha=empty, access_policy_sha=empty)
    for x in (a,b): store[x["receipt_sha256"]] = x
    level = [a["receipt_sha256"], b["receipt_sha256"]]
    if d in (8, 12, 14, 16):
        t=time.time(); C.verify_scientific_receipt(a, store.get); print(f"diamond depth {d}: verify {time.time()-t:.2f}s")
        if time.time()-t > 20: break
# 4 scope parsing
for scope in ["PIPELINE","PROJECT_WIDE","TD_PIPELINE","ALL","GLOBAL_PROJECT","project-training","TRAINING_PROJECT","Project Training","TRAINING ", "UNIT:G8", "NO_TRAINING"]:
    for st in [A.QualificationStage.FIXTURE_SAME_INTERFACE, A.QualificationStage.TRAINING_AUTHORIZED]:
        tryit(f"scope {scope!r} @ {st.value}", lambda: A.validate_authority_record(A.AuthorityRecord("G8", st, A.ActiveLineageStatus.ACTIVE, scope)).authority_scope)
tryit("unit_id int", lambda: A.validate_authority_record(A.AuthorityRecord(5, A.QualificationStage.SEMANTICS_ONLY, A.ActiveLineageStatus.ACTIVE, "UNIT")))
tryit("REVOKED record at TRAINING_AUTHORIZED unit scope", lambda: A.validate_authority_record(A.AuthorityRecord("G8", A.QualificationStage.TRAINING_AUTHORIZED, A.ActiveLineageStatus.REVOKED_BY_DEFECT, "UNIT")).qualification_stage)
class I(int):
    def __str__(self): return "777"
    def __repr__(self): return "777"
tryit("int subclass str override", lambda: C.canonical_bytes({"x": I(3)}))
class S(str):
    def replace(self, *a): return "FORGED"
tryit("str subclass replace override", lambda: C.canonical_bytes({"x": S("real")}))
