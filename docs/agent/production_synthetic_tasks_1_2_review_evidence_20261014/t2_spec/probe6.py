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


# W1 / W1b / W2 reruns
def w1():
    v1, q1, led = root(); qrun(v1, led); wreveal(v1, q1, led, W_A)
    v2, q2, disp = succ(v1, led, conf(3), withheld=EASY)
    setup(v2, q2, led, "UNCHANGED"); qrun(v2, led)
    try:
        wreveal(v2, q2, led, EASY); return disp, "easier family under UNCHANGED ACCEPTED"
    except CustodyError as e:
        return disp, f"reveal refused: {e}"
run("W1 easier family declared UNCHANGED", w1)


def w1b():
    v1, q1, led = root(); qrun(v1, led)
    v2, q2, disp = succ(v1, led, conf(3), withheld=EASY)
    try:
        setup(v2, q2, led, "CHANGED_BY_DEFECT"); return "CHANGED_BY_DEFECT without defect record accepted"
    except CustodyError as e:
        return f"refused: {e}"
run("W1b CHANGED_BY_DEFECT w/o defect record", w1b)


def w2():
    v1, q1, led = root(); qrun(v1, led)
    ch, _ = T.make_world()
    T.successor(v1, ch, led)
run("W2 identical reroll", w2)


# Q2: reroll dodges
def q2a():
    v1, q1, led = root(); qrun(v1, led); wreveal(v1, q1, led, W_A)
    out = []; cur = v1
    for lvl in (2.000001, 2.000002, 2.000003):
        ch, q, disp = succ(cur, led, conf(lvl)); setup(ch, q, led, "UNCHANGED"); qrun(ch, led); wreveal(ch, q, led, W_A)
        out.append(disp); cur = ch
    return out, "3 fresh sealed draws via epsilon-harder confounding, no defect record"
run("Q2a epsilon-harder reroll", q2a)


def q2b():
    v1, q1, led = root(); qrun(v1, led)
    def tweak(s):
        s["serialization_contract"]["note"] = "whitespace"
    ch, q, disp = succ(v1, led, tweak, defect_components=["serialization_contract"])
    return disp
run("Q2b trivial public change + boilerplate defect", q2b)


def q2c():
    v1, q1, led = root(); qrun(v1, led); wreveal(v1, q1, led, W_A)
    W_A2 = dict(W_A, DUMMY_padding="x")
    ch, q, disp = succ(v1, led, conf(2.5), withheld=W_A2, defect_components=["withheld_family"])
    setup(ch, q, led, "CHANGED_BY_DEFECT"); qrun(ch, led); wreveal(ch, q, led, W_A2)
    return disp, "withheld trivially padded, CHANGED_BY_DEFECT, reveal accepted"
run("Q2c trivial withheld change", q2c)


# Q3: eligibility True for a family public before fit froze (revert to grand-ancestor family)
def q3():
    v1, q1, led = root(withheld=W_A); qrun(v1, led); wreveal(v1, q1, led, W_A)
    v2, q2, _ = succ(v1, led, conf(3), withheld=W_B, defect_components=["withheld_family"])
    setup(v2, q2, led, "CHANGED_BY_DEFECT"); qrun(v2, led); wreveal(v2, q2, led, W_B)
    v3, q3_, _ = succ(v2, led, conf(4), withheld=W_A, defect_components=["withheld_family"])
    setup(v3, q3_, led, "CHANGED_BY_DEFECT"); qrun(v3, led); wreveal(v3, q3_, led, W_A)
    return "V3 reuses V1's PUBLIC family; withheld_check_eligible(V3) =", CU.withheld_check_eligible(led, v3.generator_semantic_hash)
run("Q3 revert to revealed grand-ancestor family", q3)


# Q1: class-nonce reveal of a sharing version while a sharing run is open
def q1():
    v1, q1_, led = root(); qrun(v1, led)
    v2, q2, _ = succ(v1, led, conf(3)); setup(v2, q2, led, "UNCHANGED"); qrun(v2, led)
    v3, q3_, _ = succ(v2, led, conf(4)); setup(v3, q3_, led, "UNCHANGED")
    T.expose(v3, led, QUAL, "open-run")  # V3 sealed run is OPEN, family W_A shared
    CU.reveal_class_nonce(v2, led, class_tag=QUAL, nonce=q2)  # discloses V2's qualification nonce
    pub = [e for e in led.entries() if e["kind"] == "REVEALED"][-1]["payload"]["nonce_hex"]
    recovered = CU.withheld_family_commitment(bytes.fromhex(pub), W_A, v2.precommitment_semantic_hash, WTAG) == v2.withheld_family_commitment
    CU.record_fit_output_frozen(v3, led, class_tag=QUAL, fit_output_sha256=T._h("v3fit"))
    wreveal(v1, q1_, led, W_A); wreveal(v2, q2, led, W_A); wreveal(v3, q3_, led, W_A)
    return (f"shared family dictionary-recoverable during V3's open run: {recovered}; "
            f"withheld_check_eligible(V3) = {CU.withheld_check_eligible(led, v3.generator_semantic_hash)}")
run("Q1 class-nonce reveal leaks shared family during open run", q1)


def q1b():
    # same leak via V1's own class-nonce reveal (V1 had its own fit frozen) while V2 (UNCHANGED) run is open
    v1, q1_, led = root(); qrun(v1, led)
    v2, q2, _ = succ(v1, led, conf(3)); setup(v2, q2, led, "UNCHANGED"); T.expose(v2, led, QUAL, "open")
    CU.reveal_class_nonce(v1, led, class_tag=QUAL, nonce=q1_)
    return "V1 class-nonce reveal accepted while V2 shares the family and its run is open"
run("Q1b", q1b)


# early superseded-reference reveal while a sharing head is committed but not yet exposed
def q1c():
    v1, q1_, led = root(); T.expose(v1, led, DEBUG, "dbg")
    v2, q2, _ = succ(v1, led, conf(3)); setup(v2, q2, led, "UNCHANGED"); qrun(v2, led)
    v3, q3_, _ = succ(v2, led, conf(4)); setup(v3, q3_, led, "UNCHANGED")
    wreveal(v1, q1_, led, W_A)   # early reveal of superseded reference; V3 shares, not yet exposed
    T.expose(v3, led, QUAL, "after-public")
    CU.record_fit_output_frozen(v3, led, class_tag=QUAL, fit_output_sha256=T._h("x"))
    return f"V3 exposed after its family went public; eligible(V3) = {CU.withheld_check_eligible(led, v3.generator_semantic_hash)}"
run("Q1c early reference reveal before sharing head runs", q1c)


# deadlock probes
def d1():
    v1, q1_, led = root(); T.expose(v1, led, DEBUG, "dbg")  # no own QUAL run
    v2, q2, _ = succ(v1, led, conf(3), withheld=W_B, defect_components=["withheld_family"])
    setup(v2, q2, led, "CHANGED_BY_DEFECT"); qrun(v2, led)
    wreveal(v1, q1_, led, W_A); wreveal(v2, q2, led, W_B)
    return "debug-only reference + CHANGED_BY_DEFECT child: both revealed"
run("D1", d1)


def d2():
    v1, q1_, led = root(); T.expose(v1, led, QUAL, "q-open")  # V1 own QUAL run left open, then superseded
    v2, q2, _ = succ(v1, led, conf(3)); setup(v2, q2, led, "UNCHANGED"); qrun(v2, led)
    try:
        wreveal(v1, q1_, led, W_A)
    except CustodyError as e:
        print("   d2 first attempt:", e)
    CU.record_fit_output_frozen(v1, led, class_tag=QUAL, fit_output_sha256=T._h("late"))
    wreveal(v1, q1_, led, W_A); wreveal(v2, q2, led, W_A)
    return "abandoned superseded run must be fit-frozen first, then lineage reveals"
run("D2", d2)


def d3():
    # superseded V1 never committed withheld (superseded before commitment); V2 is effectively root of family
    v1, q1_ = T.make_world(); led = CU.CustodyLedger(); CU.record_generator_freeze(v1, led)
    v2, q2, _ = succ(v1, led, conf(3))
    try:
        setup(v2, q2, led, "UNCHANGED")
    except CustodyError as e:
        return f"V2 cannot commit UNCHANGED: {e}"
    qrun(v2, led); wreveal(v2, q2, led, W_A)
    return "ok (UNCHANGED with no reference)"
run("D3", d3)
