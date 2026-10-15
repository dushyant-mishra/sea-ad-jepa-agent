import sys, os, secrets, pathlib, tempfile
WT = "D:/jepa_prodsynth_v311_impl_20261014"
sys.path.insert(0, WT); os.chdir(WT)
import scripts.production_synthetic.canonical_v1 as C
import scripts.production_synthetic.custody_v1 as CU
import tests.production_synthetic.test_custody_v1_hostile as T
from scripts.production_synthetic.custody_v1 import CustodyError
base = pathlib.Path(tempfile.mkdtemp(dir="D:/jepa_ps_t2_review_scratch"))
k = [0]
QUAL, DEBUG, WTAG = "SYNTH_QUALIFICATION", "SYNTH_DEBUG", T.WTAG
W_A = T.DUMMY_WITHHELD_SPEC
W_B = {"DUMMY_family": {"composition": "DUMMY_other", "weight": 0.25}, "DUMMY_scoring_rule": "DUMMY", "DUMMY_budget": 2}
EASY = {"DUMMY_family": {"composition": "DUMMY_trivially_separable", "weight": 0.9}, "DUMMY_scoring_rule": "DUMMY", "DUMMY_budget": 2}


def tree():
    k[0] += 1
    return T.make_tree(base, f"t{k[0]}")


def run(name, fn):
    try:
        print(f"[{name}] OK -> {fn()}")
    except Exception as e:
        print(f"[{name}] {type(e).__name__}: {e}")


def conf(level):
    def edit(s):
        s["difficulty_grid"]["confounding_strength"]["level"] = level  # increasing is harder
    return edit


def setup(fr, q, led, change):
    T.commit_and_attest(fr, q, led, tree(), change=change)


def qrun(fr, led, tag="q"):
    T.expose(fr, led, QUAL, tag + fr.generator_semantic_hash[:6])
    CU.record_fit_output_frozen(fr, led, class_tag=QUAL, fit_output_sha256=T._h(tag + fr.generator_semantic_hash))


def wreveal(fr, q, led, spec):
    CU.reveal_withheld_family(fr, led, withheld_spec=spec, nonce=q, withheld_class_tag=WTAG)


def root(withheld=W_A, edit=None):
    v, q = T.make_world(edit, withheld=withheld); led = CU.CustodyLedger(); CU.record_generator_freeze(v, led)
    setup(v, q, led, None)
    return v, q, led


def succ(parent, led, edit=None, withheld=W_A, defect_components=None, defect_dims=()):
    ch, q = T.make_world(edit, withheld=withheld)
    rec = None if defect_components is None else T.defect(parent, ch, defect_dims, defect_components)
    d = T.successor(parent, ch, led, rec)
    CU.record_generator_freeze(ch, led)
    if d.disposition in ("POST_EXPOSURE_VERSION", "NEW_SCIENTIFIC_TESTBED"):
        CU.record_requalification_prerequisites(ch, led, realism_rerun_receipt_sha256=T._h("r"),
                                                withheld_check_plan_sha256=T._h("w"))
    return ch, q, d.disposition



def wreveal(fr, q, led, spec):
    CU.reveal_withheld_family(fr, led, withheld_spec=spec, nonce=q, withheld_class_tag=WTAG)

def q1():
    v1, q1_, led = root(); qrun(v1, led)
    v2, q2, _ = succ(v1, led, conf(3)); setup(v2, q2, led, "UNCHANGED"); qrun(v2, led)
    v3, q3_, _ = succ(v2, led, conf(4)); setup(v3, q3_, led, "UNCHANGED"); T.expose(v3, led, QUAL, "open")
    CU.reveal_class_nonce(v2, led, class_tag=QUAL, nonce=q2)
run("Q1 class-nonce reveal of sharing V2 during V3 open run", q1)

def q1b():
    v1, q1_, led = root(); qrun(v1, led)
    v2, q2, _ = succ(v1, led, conf(3)); setup(v2, q2, led, "UNCHANGED"); T.expose(v2, led, QUAL, "open")
    CU.reveal_class_nonce(v1, led, class_tag=QUAL, nonce=q1_)
run("Q1b class-nonce reveal of V1 during V2 open run", q1b)

def q3():
    v1, q1_, led = root(withheld=W_A); qrun(v1, led); wreveal(v1, q1_, led, W_A)
    v2, q2, _ = succ(v1, led, conf(3), withheld=W_B, defect_components=["withheld_family"])
    setup(v2, q2, led, "CHANGED_BY_DEFECT"); qrun(v2, led); wreveal(v2, q2, led, W_B)
    v3, q3_, _ = succ(v2, led, conf(4), withheld=W_A, defect_components=["withheld_family"])
    setup(v3, q3_, led, "CHANGED_BY_DEFECT"); qrun(v3, led); wreveal(v3, q3_, led, W_A)
    return "eligible(V3) =", CU.withheld_check_eligible(led, v3.generator_semantic_hash), led
r = None
try:
    out = q3(); print("[Q3 revert to public family]", out[:2]); LED_Q3 = out[2]
except Exception as e:
    print("[Q3]", type(e).__name__, e); LED_Q3 = None

def q2a():
    v1, q1_, led = root(); qrun(v1, led); wreveal(v1, q1_, led, W_A)
    cur = v1
    for lvl in (2.000001, 2.000002):
        ch, q, disp = succ(cur, led, conf(lvl)); setup(ch, q, led, "UNCHANGED"); qrun(ch, led); wreveal(ch, q, led, W_A); cur = ch
    return len(CU.qualification_draws_for_method(led, "fixture_method")), led
n, LED_Q2 = q2a(); print("[Q2a epsilon rerolls] draws_for_method =", n)

def cross():
    # V1 W_A -> V2 CHANGED W_B -> V3 UNCHANGED W_B ; leak V2 nonce while V3 open ; and V1 nonce while V3 open
    v1, q1_, led = root(withheld=W_A); qrun(v1, led)
    v2, q2, _ = succ(v1, led, conf(3), withheld=W_B, defect_components=["withheld_family"])
    setup(v2, q2, led, "CHANGED_BY_DEFECT"); qrun(v2, led)
    v3, q3_, _ = succ(v2, led, conf(4), withheld=W_B); setup(v3, q3_, led, "UNCHANGED"); T.expose(v3, led, QUAL, "open")
    res = []
    for nm, v, q in (("V2(same family W_B)", v2, q2), ("V1(other family W_A)", v1, q1_)):
        try:
            CU.reveal_class_nonce(v, led, class_tag=QUAL, nonce=q); res.append(f"{nm} reveal ALLOWED")
        except CustodyError as e:
            res.append(f"{nm} refused")
    return res
run("X1 across CHANGED break then UNCHANGED", cross)

def cross2():
    # V1 W_A -> V2 CHANGED W_B -> V3 CHANGED back to W_A (other group) ; V1 nonce during V3 open run
    v1, q1_, led = root(withheld=W_A); qrun(v1, led)
    v2, q2, _ = succ(v1, led, conf(3), withheld=W_B, defect_components=["withheld_family"])
    setup(v2, q2, led, "CHANGED_BY_DEFECT"); qrun(v2, led)
    v3, q3_, _ = succ(v2, led, conf(4), withheld=W_A, defect_components=["withheld_family"])
    setup(v3, q3_, led, "CHANGED_BY_DEFECT"); T.expose(v3, led, QUAL, "open")
    CU.reveal_class_nonce(v1, led, class_tag=QUAL, nonce=q1_)   # discloses W_A while V3 (carrying W_A) run is open
    CU.record_fit_output_frozen(v3, led, class_tag=QUAL, fit_output_sha256=T._h("v3"))
    wreveal(v1, q1_, led, W_A); wreveal(v2, q2, led, W_B); wreveal(v3, q3_, led, W_A)
    return "V1 nonce reveal allowed during V3 open run; final eligible(V3) =", CU.withheld_check_eligible(led, v3.generator_semantic_hash)
run("X2 revert family leak via other-group nonce", cross2)

def inside_before_commit():
    v1, q1_, led = root(); qrun(v1, led); CU.reveal_class_nonce(v1, led, class_tag=QUAL, nonce=q1_)
    v2, q2, _ = succ(v1, led, conf(3)); setup(v2, q2, led, "UNCHANGED"); qrun(v2, led)
    c = [e for e in led.entries() if e["kind"] == "WITHHELD_COMMITTED"][-1]["payload"]["withheld_check_secret"]
    return f"secret flag at commit = {c}; eligible(V2) = {CU.withheld_check_eligible(led, v2.generator_semantic_hash)}"
run("G1 group member disclosed (class nonce) before commit", inside_before_commit)

def forge():
    import copy
    if LED_Q3 is None: return "skip"
    E = LED_Q3.entries()
    for e in E:
        if e["kind"] == "REVEALED" and e["payload"].get("family_previously_public") is True:
            e["payload"]["family_previously_public"] = False
    prev = "0" * 64; out = []
    for i, e in enumerate(E):
        e = dict(e, index=i, prev_entry_hash=prev)
        e["entry_hash"] = C.semantic_sha256({"format": T.ENTRY_FORMAT, "index": i, "kind": e["kind"], "payload": e["payload"], "prev_entry_hash": prev})
        prev = e["entry_hash"]; out.append(e)
    CU.CustodyLedger.from_bytes(C.canonical_json_bytes({"format": T.LEDGER_FORMAT, "entries": out}))
    return "forged family_previously_public ACCEPTED"
run("F1 forge family_previously_public + rechain", forge)

def draws_superseded_voided():
    v1, q1_, led = root(); qrun(v1, led)                         # V1 draw, later superseded
    v2, q2, _ = succ(v1, led, conf(3), withheld=W_B)             # declared UNCHANGED but different -> voided at reveal
    setup(v2, q2, led, "UNCHANGED"); qrun(v2, led)
    wreveal(v1, q1_, led, W_A)
    try: wreveal(v2, q2, led, W_B)
    except CustodyError as e: pass
    d = CU.qualification_draws_for_method(led, "fixture_method")
    return [x["generator_semantic_hash"][:6] for x in d], v1.generator_semantic_hash[:6], v2.generator_semantic_hash[:6]
run("D superseded + voided included", draws_superseded_voided)

def rename():
    v1, q1_, led = root(); T.expose(v1, led, QUAL, "a"); CU.record_fit_output_frozen(v1, led, class_tag=QUAL, fit_output_sha256=T._h("a"))
    v2, q2, _ = succ(v1, led, conf(2.000001)); setup(v2, q2, led, "UNCHANGED")
    CU.record_exposure(v2, {"exposure_id": "b", "method_id": "fixture_method_v2", "realization_class": QUAL}, led)
    return (len(CU.qualification_draws_for_method(led, "fixture_method")), len(CU.qualification_draws_for_method(led, "fixture_method_v2")))
run("R method_id relabel per reroll -> (draws M, draws M_v2)", rename)
