import sys, os, base64, copy, json, secrets, pathlib, tempfile, traceback
WT = "D:/jepa_prodsynth_v311_impl_20261014"
sys.path.insert(0, WT); os.chdir(WT)
import scripts.production_synthetic.canonical_v1 as C
import scripts.production_synthetic.custody_v1 as CU
import tests.production_synthetic.test_custody_v1_hostile as T
from scripts.production_synthetic.custody_v1 import CustodyError

def run(name, fn):
    try:
        r = fn(); print(f"[{name}] OK -> {r}")
    except Exception as e:
        print(f"[{name}] {type(e).__name__}: {e}")

tmp = pathlib.Path(tempfile.mkdtemp(dir="D:/jepa_ps_t2_review_scratch"))
cnt = [0]
def tree():
    cnt[0]+=1; return T.make_tree(tmp, f"t{cnt[0]}")

def exposed_parent():
    p, w = T.make_world(); led = CU.CustodyLedger(); T.prepare(p, w, led, tree()); T.expose(p, led); return p, led

# P1: E1 hole on non-profile components
def edits():
    yield "mechanism_mixture novelty weight->0", lambda s: s.__setitem__("mechanism_mixture", {"weights": {"program_a": 1.0, "program_b": 0.0}})
    yield "dropout relaxed", lambda s: s["observation_calibration_distributions"].__setitem__("dropout", {"law":"beta","a":1.0,"b":50.0})
    yield "control matrix shrunk", lambda s: s.__setitem__("applicability_control_matrix", {"matched_null": ["none"]})
    yield "qual budget 4->1", lambda s: s["realization_budgets"].__setitem__("SYNTH_QUALIFICATION", 1)
    yield "debug budget removed", lambda s: s["realization_budgets"].pop("SYNTH_DEBUG")
    yield "param dist sigma", lambda s: s["parameter_distributions"]["library_size"].__setitem__("sigma", 0.01)
for nm, ed in edits():
    def f(ed=ed):
        p, led = exposed_parent(); ch, _ = T.make_world(ed); d = T.successor(p, ch, led); return d.disposition, d.easier_dimensions
    run("P1 "+nm, f)

# P2: version shopping by exposing non-head ancestor after an easier pre-exposure successor
def p2():
    v1, w1 = T.make_world(); led = CU.CustodyLedger(); CU.record_generator_freeze(v1, led)
    v2, w2 = T.make_world(T.set_snr(0.9))  # easier (decreasing harder)
    d = T.successor(v1, v2, led); CU.record_generator_freeze(v2, led)
    # now commit and expose V1 (non-head) and V2
    T.commit_withheld(v1, w1, led, tree())
    for tag in ("SYNTH_DEBUG","SYNTH_QUALIFICATION"):
        n = T.dummy_nonce(); CU.record_nonce_commitment(v1, led, class_tag=tag, nonce_commitment=CU.nonce_commitment(n))
        b = v1.realization_budget(tag); r = CU.sealed_root(n, v1.generator_semantic_hash, tag, b)
        CU.attest_realization_set(r, tag, b, T.emit(r, tag, b), led, freeze=v1)
    T.expose(v1, led, "SYNTH_QUALIFICATION", "v1-q")
    T.commit_withheld(v2, w2, led, tree())
    for tag in ("SYNTH_DEBUG","SYNTH_QUALIFICATION"):
        n = T.dummy_nonce(); CU.record_nonce_commitment(v2, led, class_tag=tag, nonce_commitment=CU.nonce_commitment(n))
        b = v2.realization_budget(tag); r = CU.sealed_root(n, v2.generator_semantic_hash, tag, b)
        CU.attest_realization_set(r, tag, b, T.emit(r, tag, b), led, freeze=v2)
    T.expose(v2, led, "SYNTH_QUALIFICATION", "v2-q")
    led.verify()
    return d.disposition, "V1 exposed AFTER easier V2 frozen; V2 exposed too; ledger replays clean"
run("P2 non-head exposure / version shopping", p2)

# P3: withheld commitment opened with the DEBUG nonce, debug nonce revealed early
def p3():
    spec = T.base_spec(); dn = T.dummy_nonce()
    pre = CU.generator_precommitment_semantic_hash(spec)
    spec["withheld_family_commitment"] = CU.withheld_family_commitment(dn, T.DUMMY_WITHHELD_SPEC, pre, T.WTAG)
    fr = CU.freeze_generator_version(spec); led = CU.CustodyLedger(); CU.record_generator_freeze(fr, led)
    T.commit_withheld(fr, dn, led, tree())
    qn = T.dummy_nonce()
    CU.record_nonce_commitment(fr, led, class_tag="SYNTH_DEBUG", nonce_commitment=CU.nonce_commitment(dn))
    CU.record_nonce_commitment(fr, led, class_tag="SYNTH_QUALIFICATION", nonce_commitment=CU.nonce_commitment(qn))
    for tag, n in (("SYNTH_DEBUG", dn), ("SYNTH_QUALIFICATION", qn)):
        b = fr.realization_budget(tag); r = CU.sealed_root(n, fr.generator_semantic_hash, tag, b)
        CU.attest_realization_set(r, tag, b, T.emit(r, tag, b), led, freeze=fr)
    T.expose(fr, led, "SYNTH_DEBUG", "d1")
    CU.record_fit_output_frozen(fr, led, class_tag="SYNTH_DEBUG", fit_output_sha256=T._h("fit-debug"))
    CU.reveal_class_nonce(fr, led, class_tag="SYNTH_DEBUG", nonce=dn)   # debug nonce now public in ledger
    pub = [e for e in led.entries() if e["kind"]=="REVEALED"][0]["payload"]["nonce_hex"]
    # attacker brute-forces small withheld space with public nonce:
    ok = CU.withheld_family_commitment(bytes.fromhex(pub), T.DUMMY_WITHHELD_SPEC, fr.precommitment_semantic_hash, T.WTAG) == fr.withheld_family_commitment
    T.expose(fr, led, "SYNTH_QUALIFICATION", "q1")  # qualification still exposable
    CU.record_fit_output_frozen(fr, led, class_tag="SYNTH_QUALIFICATION", fit_output_sha256=T._h("fit-q"))
    CU.reveal_withheld_family(fr, led, withheld_spec=T.DUMMY_WITHHELD_SPEC, nonce=dn, withheld_class_tag=T.WTAG)
    return f"withheld commitment openable from public debug reveal BEFORE qualification exposure: {ok}; withheld reveal accepted"
run("P3 withheld nonce == debug nonce", p3)

# P10: justification wording
def p10():
    p, led = exposed_parent(); ch, _ = T.make_world(T.set_snr(0.9))
    rec = T.defect(p, ch, ["difficulty_grid/signal_to_noise"], defect_description="method M failed at snr 0.5 so we relaxed it")
    return T.successor(p, ch, led, rec).disposition
run("P10 method-failure text in defect_description", p10)

# P4: derive_stream
r = secrets.token_bytes(32)
a = CU.stream_seed_digest(r, ("world_id","a\",\"cell_id\":\"b"), ("purpose_tag","x"))
b = CU.stream_seed_digest(r, ("world_id","a"), ("cell_id","b"), ("purpose_tag","x"))
print("[P4 framing collision]", a == b)
print("[P4 no world_id: same stream across worlds]", CU.stream_seed_digest(r, ("cell_id","c1"),("purpose_tag","x")) == CU.stream_seed_digest(r, ("cell_id","c1"),("purpose_tag","x")))
import unicodedata
print("[P4 NFC vs NFD differ]", CU.stream_seed_digest(r, ("cell_id", unicodedata.normalize("NFC","caf\u00e9")),("purpose_tag","x")) != CU.stream_seed_digest(r, ("cell_id", unicodedata.normalize("NFD","caf\u00e9")),("purpose_tag","x")))
run("P4 int-like str", lambda: CU.stream_seed_digest(r, ("cell_id","3"),("purpose_tag","x")) != CU.stream_seed_digest(r, ("cell_id","03"),("purpose_tag","x")))
import numpy as np
run("P4 np.str_ value", lambda: CU.stream_seed_digest(r, ("cell_id",np.str_("3")),("purpose_tag","x")).hex()[:8])
class S(str): pass
run("P4 str subclass value", lambda: CU.stream_seed_digest(r, ("cell_id",S("3")),("purpose_tag","x")).hex()[:8])
run("P4 draw_index_tag as offset namespace", lambda: [CU.stream_seed_digest(r, ("draw_index_tag",str(i)),("purpose_tag","x")).hex()[:6] for i in range(3)])

# P6: code path canonical error type / leakage
run("P6 CRLF dev path collision", lambda: CU.attest_no_unique_withheld_code_path(["w"], ["x\r\ny","x\ny","w"], ["p"]))
run("P6 CRLF withheld path", lambda: CU.attest_no_unique_withheld_code_path(["SECRETPATH\r\nz","SECRETPATH\nz"], ["d"], ["p"]))
run("P6 unique withheld msg", lambda: CU.attest_no_unique_withheld_code_path(["SECRET_mech.py::astro"], ["d"], ["SECRET_mech.py::astro","d"]))
