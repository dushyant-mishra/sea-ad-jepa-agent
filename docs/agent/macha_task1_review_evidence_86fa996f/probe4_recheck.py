import sys, hashlib
sys.path.insert(0, r"D:/jepa_task1_recheck_799d2e23")
from scripts.v5.td_unified import canonical_v1 as C
code=b"x=1\n"; cs=hashlib.sha1(b"blob %d\0"%len(code)+code).hexdigest(); st={cs:code}
def put(o):
    s=C.canonical_sha256(o); st[s]=o; return s
i=put({"object_role":"INPUT","v":1}); o=put({"object_role":"OUTPUT","v":2}); m=put({"object_role":"MANIFEST","v":3}); r=put({"object_role":"REGISTRY","v":4}); e=put({})
try:
    C.verify_scientific_receipt(C.make_scientific_receipt(payload={"p":1},producer_code_sha=cs,input_shas=[i],parent_receipt_shas=[],output_sha=o,manifest_sha=m,registry_sha=r,access_policy_sha=e),st.get); print("BAD {} alone as access verified")
except Exception as ex: print("OK  {} alone as access refused:", str(ex)[:80])
a2=put({"object_role":"ACCESS_POLICY","x":0}); i2=put({"v":9})
try:
    C.verify_scientific_receipt(C.make_scientific_receipt(payload={"p":2},producer_code_sha=cs,input_shas=[i2],parent_receipt_shas=[],output_sha=o,manifest_sha=m,registry_sha=r,access_policy_sha=a2),st.get); print("BAD untagged input verified")
except Exception as ex: print("OK  untagged input refused:", str(ex)[:80])
