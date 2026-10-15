import sys, secrets
sys.path.insert(0, "D:/jepa_prodsynth_v311_impl_20261014")
sys.path.insert(0, "D:/jepa_prodsynth_v311_impl_20261014/tests/production_synthetic")
import pathlib, tempfile
import test_custody_v1 as T
import scripts.production_synthetic.custody_v1 as CU

tmp = pathlib.Path(tempfile.mkdtemp(dir="D:/jepa_ps_t2_quality_scratch"))
tree = T.make_tree(tmp)

# Probe 1: SYNTH_QUALIFICATION exposure after fit freeze, before reveal
fr, qn = T.make_world()
led = CU.CustodyLedger()
keys = T.prepare(fr, qn, led, tree)
T.expose(fr, led, T.QUAL, "A")
CU.record_fit_output_frozen(fr, led, class_tag=T.QUAL, fit_output_sha256=T._h("fitA"))
try:
    T.expose(fr, led, T.QUAL, "C-late")
    print("P1 late qualification exposure after fit freeze ACCEPTED")
except CU.CustodyError as e:
    print("P1 refused:", e)
try:
    CU.reveal_class_nonce(fr, led, class_tag=T.QUAL, nonce=qn)
    print("P1 reveal accepted while late exposure C has no frozen fit output")
except CU.CustodyError as e:
    print("P1 reveal refused:", e)
print("P1 eligible before withheld reveal:", CU.withheld_check_eligible(led, fr.generator_semantic_hash))

# Probe 3: eligibility True before own reveal (no reveal at all)
fr2, qn2 = T.make_world()
led2 = CU.CustodyLedger()
T.prepare(fr2, qn2, led2, tree)
T.expose(fr2, led2, T.QUAL, "A")
print("P3 eligible with no fit freeze and no reveal:", CU.withheld_check_eligible(led2, fr2.generator_semantic_hash))

# Probe 2: superseded root that never committed withheld; descendant fit frozen; reveal on root
fr3, qn3 = T.make_world()
led3 = CU.CustodyLedger()
CU.record_generator_freeze(fr3, led3)
CU.record_nonce_commitment(fr3, led3, class_tag=T.QUAL, nonce_commitment=CU.nonce_commitment(qn3))
child, qnc = T.make_world(edit=lambda s: s["difficulty_grid"]["confounding_strength"].update(level=3))
st = CU.exposure_state(fr3, led3)
d = CU.validate_successor_version(fr3, child, parent_exposure_state=st, ledger=led3)
print("P2 disposition", d.disposition)
CU.record_generator_freeze(child, led3)
T.commit_and_attest(child, qnc, led3, tree)  # withheld_family_change=None? need successor declaration
