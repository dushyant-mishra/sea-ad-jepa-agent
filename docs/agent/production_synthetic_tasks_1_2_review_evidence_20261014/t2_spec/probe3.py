import sys, os, secrets, pathlib, tempfile, json, copy
WT = "D:/jepa_prodsynth_v311_impl_20261014"
sys.path.insert(0, WT); os.chdir(WT)
import scripts.production_synthetic.canonical_v1 as C
import scripts.production_synthetic.custody_v1 as CU
import tests.production_synthetic.test_custody_v1_hostile as T
from scripts.production_synthetic.custody_v1 import CustodyError
base = pathlib.Path(tempfile.mkdtemp(dir="D:/jepa_ps_t2_review_scratch"))
k=[0]
def tree():
    k[0]+=1; return T.make_tree(base, f"t{k[0]}")
def run(name, fn):
    try: print(f"[{name}] OK -> {fn()}")
    except Exception as e: print(f"[{name}] {type(e).__name__}: {e}")
def rechain(entries):
    prev = "0"*64; out=[]
    for i,e in enumerate(entries):
        e = dict(e, index=i, prev_entry_hash=prev)
        e["entry_hash"] = C.semantic_sha256({"format":T.ENTRY_FORMAT,"index":i,"kind":e["kind"],"payload":e["payload"],"prev_entry_hash":prev})
        prev = e["entry_hash"]; out.append(e)
    return C.canonical_json_bytes({"format":T.LEDGER_FORMAT,"entries":out})

p, w = T.make_world(); led = CU.CustodyLedger(); roots = T.prepare(p, w, led, tree()); T.expose(p, led)
E = led.entries()
print("kinds:", [e["kind"] for e in E])
# tamper payload without rechain
bad = copy.deepcopy(E); bad[-1]["payload"]["method_id"]="other"
run("L1 tamper no rechain", lambda: CU.CustodyLedger.from_bytes(C.canonical_json_bytes({"format":T.LEDGER_FORMAT,"entries":bad})).head)
# delete exposure + rechain => unexposed -> easier successor gets PRE_EXPOSURE_REVISION
forged = CU.CustodyLedger.from_bytes(rechain(E[:-1]))
ch,_ = T.make_world(T.set_snr(0.9))
run("L2 deleted exposure, rechained, no anchor -> successor", lambda: T.successor(p, ch, forged).disposition)
run("L2b same with anchor", lambda: CU.CustodyLedger.from_bytes(rechain(E[:-1]), expected_head=led.head))
# reorder: exposure before attestation
reo = E[:]; reo.insert(3, reo.pop())  # move exposure early
run("L3 reorder rechained", lambda: CU.CustodyLedger.from_bytes(rechain(reo)).head)
# replay entry from another ledger
p2, w2 = T.make_world(); led2 = CU.CustodyLedger(); T.prepare(p2, w2, led2, tree())
mix = E[:-1] + [led2.entries()[-1]]
run("L4 foreign entry rechained", lambda: CU.CustodyLedger.from_bytes(rechain(mix)).head)
# forged emitted_set_sha256 in attestation (rechained)
f5 = copy.deepcopy(E)
for e in f5:
    if e["kind"]=="REALIZATION_SET_ATTESTED": e["payload"]["emitted_set_sha256"]=T._h("anything")
run("L5 forged emitted_set digest rechained", lambda: CU.CustodyLedger.from_bytes(rechain(f5)).head[:8])
# forged secret_absence / code_path attestation (rechained)
f6 = copy.deepcopy(E)
for e in f6:
    if e["kind"]=="WITHHELD_COMMITTED": e["payload"]["secret_absence"]["tree_identity"]=T._h("x"); e["payload"]["code_path_attestation"]["public_paths_digest"]=T._h("y")
run("L6 forged scan attestation rechained", lambda: CU.CustodyLedger.from_bytes(rechain(f6)).head[:8])
# ExposureState from another ledger with same counts
st_other = CU.ExposureState(generator_semantic_hash=p.generator_semantic_hash, exposed=True, exposure_count=1, ledger_head=T._h("bogus"))
ch2,_ = T.make_world(T.set_snr(0.4))
run("L7 ExposureState with bogus ledger_head accepted", lambda: CU.validate_successor_version(p, ch2, parent_exposure_state=st_other, ledger=led).disposition)

# R1: replace a realization's content, same id, before attestation
fr, wn = T.make_world(); l3 = CU.CustodyLedger(); rr = T.prepare(fr, wn, l3, tree(), attest=False)
n, root = rr["SYNTH_QUALIFICATION"]; b = fr.realization_budget("SYNTH_QUALIFICATION")
rows = T.emit(root, "SYNTH_QUALIFICATION", b); rows[0]["content_sha256"] = T._h("cherry-picked replacement world")
run("R1 same-id different content", lambda: CU.attest_realization_set(root, "SYNTH_QUALIFICATION", b, rows, l3, freeze=fr).n_emitted)
# R2: debug exposures before QUAL realization set attested
run("R2 debug attest+expose before QUAL attest", lambda: (CU.attest_realization_set(rr["SYNTH_DEBUG"][1], "SYNTH_DEBUG", fr.realization_budget("SYNTH_DEBUG"), T.emit(rr["SYNTH_DEBUG"][1],"SYNTH_DEBUG",fr.realization_budget("SYNTH_DEBUG")), l3, freeze=fr).n_emitted, T.expose(fr, l3, "SYNTH_DEBUG").exposed))

# E1: error message echo of unknown spec key / exposure key
s = T.base_spec(); s["withheld_family_commitment"]="0"*64; s["WITHHELD_astro_cascade_weight_0p125"]=1
run("M1 unknown top-level key echo", lambda: CU.freeze_generator_version(s))
s = T.base_spec(); s["withheld_family_commitment"]="0"*64; s["mechanism_mixture"]["withheld_mechanism_astro"]=0.1
run("M2 nested plaintext (no echo?)", lambda: CU.freeze_generator_version(s))
ws = {"astro\r\ncascade": 1, "astro\ncascade": 2}
run("M3 withheld spec CRLF key collision at commit time", lambda: CU.withheld_family_commitment(T.dummy_nonce(), ws, T._h("pre"), T.WTAG))
run("M4 withheld class tag descriptive", lambda: CU.withheld_family_commitment(T.dummy_nonce(), {"a":1}, T._h("pre"), "SYNTH_RARE_ASTROCYTE_CASCADE")[:8])
# realism-rerun / withheld check not enforced before exposing a POST_EXPOSURE_VERSION child
def pe():
    pp, ww = T.make_world(); L = CU.CustodyLedger(); T.prepare(pp, ww, L, tree()); T.expose(pp, L)
    c, cw = T.make_world(T.set_snr(0.9))
    d = T.successor(pp, c, L, T.defect(pp, c, ["difficulty_grid/signal_to_noise"]))
    CU.record_generator_freeze(c, L); T.prepare_child = None
    T.commit_withheld(c, cw, L, tree())
    for tag in ("SYNTH_DEBUG","SYNTH_QUALIFICATION"):
        nn = T.dummy_nonce(); CU.record_nonce_commitment(c, L, class_tag=tag, nonce_commitment=CU.nonce_commitment(nn))
        bb = c.realization_budget(tag); ro = CU.sealed_root(nn, c.generator_semantic_hash, tag, bb)
        CU.attest_realization_set(ro, tag, bb, T.emit(ro, tag, bb), L, freeze=c)
    return d.disposition, T.expose(c, L, "SYNTH_QUALIFICATION").exposed
run("S1 POST_EXPOSURE child exposed with no realism-rerun record", pe)
# multiple candidate successors validated for one parent (candidate shopping)
def cand():
    pp, ww = T.make_world(); L = CU.CustodyLedger(); T.prepare(pp, ww, L, tree()); T.expose(pp, L)
    out=[]
    for lvl in (0.4,0.3,0.2):
        c,_ = T.make_world(T.set_snr(lvl)); out.append(T.successor(pp,c,L).disposition)
    return out
run("S2 several candidate successors of same parent", cand)
