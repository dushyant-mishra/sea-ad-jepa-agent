import sys
sys.path.insert(0, "D:/jepa_prodsynth_v311_impl_20261014")
sys.path.insert(0, "D:/jepa_prodsynth_v311_impl_20261014/tests/production_synthetic")
import pathlib, tempfile
import test_custody_v1 as T
import scripts.production_synthetic.custody_v1 as CU
import scripts.production_synthetic.canonical_v1 as C
tmp = pathlib.Path(tempfile.mkdtemp(dir="D:/jepa_ps_t2_quality_scratch"))
tree = T.make_tree(tmp)
fr3, qn3 = T.make_world()
led3 = CU.CustodyLedger()
CU.record_generator_freeze(fr3, led3)
CU.record_nonce_commitment(fr3, led3, class_tag=T.QUAL, nonce_commitment=CU.nonce_commitment(qn3))
child, qnc = T.make_world(edit=lambda s: s["difficulty_grid"]["confounding_strength"].update(level=3))
st = CU.exposure_state(fr3, led3)
CU.validate_successor_version(fr3, child, parent_exposure_state=st, ledger=led3)
CU.record_generator_freeze(child, led3)
for tag, n in ((T.QUAL, qnc),):
    CU.record_nonce_commitment(child, led3, class_tag=tag, nonce_commitment=CU.nonce_commitment(n))
scans = [CU.require_secret_absence(tree, qnc)]
CU.record_withheld_commitment(child, led3, withheld_class_tag=T.WTAG, nonce_commitment=CU.nonce_commitment(qnc),
    secret_absence_attestations=scans, code_path_attestation=T.code_path_attestation(), withheld_family_change="UNCHANGED")
root = CU.sealed_root(qnc, child.generator_semantic_hash, T.QUAL, 4)
CU.attest_realization_set(root, T.QUAL, 4, T.emit(root, T.QUAL, 4), led3, freeze=child)
T.expose(child, led3, T.QUAL, "A")
CU.record_fit_output_frozen(child, led3, class_tag=T.QUAL, fit_output_sha256=T._h("fit"))
try:
    CU.reveal_withheld_family(fr3, led3, withheld_spec=T.DUMMY_WITHHELD_SPEC, nonce=qn3, withheld_class_tag=T.WTAG)
    print("P2 accepted")
except CU.CustodyError as e:
    print("P2 CustodyError:", e)
except Exception as e:
    print("P2 NON-CUSTODY EXCEPTION:", type(e).__name__, e)
# replay a ledger with raw bad entry injected
raw = led3.to_bytes()
print("replay ok, head", CU.CustodyLedger.from_bytes(raw).head == led3.head)
