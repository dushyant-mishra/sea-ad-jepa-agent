import sys, time, secrets, pathlib, tempfile, os
sys.path.insert(0, "D:/jepa_prodsynth_v311_impl_20261014")
sys.path.insert(0, "D:/jepa_prodsynth_v311_impl_20261014/tests/production_synthetic")
import custody_fixtures_v1 as F
import scripts.production_synthetic.custody_v1 as CU
tmp = pathlib.Path(tempfile.mkdtemp(dir="D:/jepa_ps_t2_quality_scratch")); tree = F.make_tree(tmp)
def tryit(label, fn):
    try: r = fn(); print(label, "ACCEPTED", r if isinstance(r, bool) else "")
    except CU.CustodyError as e: print(label, "CustodyError:", str(e)[:110])
    except Exception as e: print(label, "NON-CUSTODY", type(e).__name__, e)
# P1 late exposure / multi-exposure reveal
fr, qn = F.make_world(); led = CU.CustodyLedger(); F.prepare(fr, qn, led, tree)
F.expose(fr, led, F.QUAL, "A"); F.expose(fr, led, F.QUAL, "B")
CU.record_fit_output_frozen(fr, led, exposure_id="A", fit_output_sha256=F._h("fitA"))
tryit("P1 late exposure C after A frozen:", lambda: F.expose(fr, led, F.QUAL, "C"))
tryit("P1 late DEBUG exposure (other class, no debug fit):", lambda: F.expose(fr, led, F.DEBUG, "D1"))
tryit("P1 reveal with B unfrozen:", lambda: CU.reveal_class_nonce(fr, led, class_tag=F.QUAL, nonce=qn))
tryit("P1 withheld reveal with B unfrozen:", lambda: CU.reveal_withheld_family(fr, led, withheld_spec=F.DUMMY_WITHHELD_SPEC, nonce=qn, withheld_class_tag=F.WTAG))
tryit("P1 freeze B twice? first:", lambda: CU.record_fit_output_frozen(fr, led, exposure_id="B", fit_output_sha256=F._h("fitB")))
tryit("P1 freeze B again:", lambda: CU.record_fit_output_frozen(fr, led, exposure_id="B", fit_output_sha256=F._h("fitB2")))
tryit("P1 freeze unknown exposure:", lambda: CU.record_fit_output_frozen(fr, led, exposure_id="ZZ", fit_output_sha256=F._h("z")))
tryit("P4 eligible before own reveal:", lambda: CU.withheld_check_eligible(led, fr.generator_semantic_hash))
tryit("P4 still_secret before reveal:", lambda: CU.withheld_family_still_secret(led, fr.generator_semantic_hash))
tryit("P1 withheld reveal now:", lambda: CU.reveal_withheld_family(fr, led, withheld_spec=F.DUMMY_WITHHELD_SPEC, nonce=qn, withheld_class_tag=F.WTAG))
tryit("P4 eligible after reveal:", lambda: CU.withheld_check_eligible(led, fr.generator_semantic_hash))
print("replay ok:", CU.CustodyLedger.from_bytes(led.to_bytes(), expected_head=led.head).head == led.head)
# P2 IndexError path
fr3, qn3 = F.make_world(); led3 = CU.CustodyLedger(); CU.record_generator_freeze(fr3, led3)
CU.record_nonce_commitment(fr3, led3, class_tag=F.QUAL, nonce_commitment=CU.nonce_commitment(qn3))
child, qnc = F.make_world(edit=lambda s: s["difficulty_grid"]["confounding_strength"].update(level=3))
CU.validate_successor_version(fr3, child, parent_exposure_state=CU.exposure_state(fr3, led3), ledger=led3)
CU.record_generator_freeze(child, led3)
CU.record_nonce_commitment(child, led3, class_tag=F.QUAL, nonce_commitment=CU.nonce_commitment(qnc))
CU.record_withheld_commitment(child, led3, withheld_class_tag=F.WTAG, nonce_commitment=CU.nonce_commitment(qnc),
    secret_absence_attestations=[CU.require_nonce_absence(tree, qnc)], code_path_attestation=F.code_path_attestation(), withheld_family_change="UNCHANGED")
root = CU.sealed_root(qnc, child.generator_semantic_hash, F.QUAL, 4)
CU.attest_realization_set(child, led3, root=root, class_tag=F.QUAL, emitted=F.emit(root, F.QUAL, 4))
F.expose(child, led3, F.QUAL, "A"); CU.record_fit_output_frozen(child, led3, exposure_id="A", fit_output_sha256=F._h("f"))
tryit("P2 reveal withheld on never-committed superseded root:", lambda: CU.reveal_withheld_family(fr3, led3, withheld_spec=F.DUMMY_WITHHELD_SPEC, nonce=qn3, withheld_class_tag=F.WTAG))
# P2b crafted ledger: inject non-dict payload type into a validator path
import scripts.production_synthetic.canonical_v1 as C
obj = C.load_canonical_json(led3.to_bytes()); 
# scan binding: a hand-built scan dict without nonce_commitment
tryit("P5 withheld commit w/o nonce scan:", lambda: CU.record_withheld_commitment(fr, CU.CustodyLedger(), withheld_class_tag=F.WTAG, nonce_commitment=CU.nonce_commitment(qn), secret_absence_attestations=[CU.require_secret_absence(tree, qn)], code_path_attestation=F.code_path_attestation()))
# P3 4 KB scan + boundary
for n in (64, 65, 1786, 4096, 65536):
    tryit(f"P3 scan {n} B:", lambda n=n: CU.scan_secret_absence(tree, secrets.token_bytes(n))["secret_absent"])
