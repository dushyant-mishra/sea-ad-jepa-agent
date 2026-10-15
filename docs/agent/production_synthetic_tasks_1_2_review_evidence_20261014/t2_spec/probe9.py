import sys, os, secrets, pathlib, tempfile
WT = "D:/jepa_prodsynth_v311_impl_20261014"
sys.path.insert(0, WT); os.chdir(WT)
import scripts.production_synthetic.canonical_v1 as C
import scripts.production_synthetic.custody_v1 as CU
import tests.production_synthetic.custody_fixtures_v1 as T
from scripts.production_synthetic.custody_v1 import CustodyError
base = pathlib.Path(tempfile.mkdtemp(dir="D:/jepa_ps_t2_review_scratch"))
k = [0]
QUAL, DEBUG, WTAG = T.QUAL, T.DEBUG, T.WTAG
W_A = T.DUMMY_WITHHELD_SPEC
W_B = {"DUMMY_family": {"composition": "DUMMY_other", "weight": 0.25}, "DUMMY_scoring_rule": "DUMMY", "DUMMY_budget": 2}
EASY = T.EASIER_WITHHELD_SPEC

print("interfaces:", all(hasattr(CU, n) for n in ["freeze_generator_version", "commit_secret", "derive_stream", "record_exposure",
      "validate_successor_version", "attest_realization_set", "scan_secret_absence", "attest_no_unique_withheld_code_path"]))


def tree():
    k[0] += 1
    return T.make_tree(base, f"t{k[0]}")


def run(name, fn):
    try:
        print(f"[{name}] OK -> {fn()}")
    except Exception as e:
        print(f"[{name}] {type(e).__name__}: {str(e)[:150]}")


def conf(level):
    def edit(s):
        s["difficulty_grid"]["confounding_strength"]["level"] = level
    return edit


def setup(fr, q, led, change):
    # withheld spec scan uses DUMMY spec bytes in fixture; fine for absence
    T.commit_and_attest(fr, q, led, tree(), change=change)


def expose(fr, led, tag, eid, method=T.METHOD):
    return CU.record_exposure(fr, led, {"exposure_id": eid, "method_id": method, "realization_class": tag})


def qrun(fr, led, tag="q", method=T.METHOD):
    eid = tag + fr.generator_semantic_hash[:6]
    expose(fr, led, QUAL, eid, method)
    CU.record_fit_output_frozen(fr, led, exposure_id=eid, fit_output_sha256=T._h(eid))


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


# E1 six relaxations
eds = {
    "mixture": lambda s: s.__setitem__("mechanism_mixture", {"weights": {"program_a": 0.5, "program_b": 0.5, "novelty_program": 0.0}}),
    "dropout": lambda s: s["observation_calibration_distributions"].__setitem__("dropout", {"law": "beta", "a": 1.0, "b": 50.0}),
    "control": lambda s: s.__setitem__("applicability_control_matrix", {"matched_null": ["all_targets"]}),
    "qualbudget": lambda s: s["realization_budgets"].__setitem__(QUAL, 1),
    "debugbudget": lambda s: s["realization_budgets"].pop(DEBUG),
    "sigma": lambda s: s["parameter_distributions"]["library_size"].__setitem__("sigma", 0.01),
}
res = []
for nm, ed in eds.items():
    v, q, led = root(); expose(v, led, DEBUG, "d")
    ch, _ = T.make_world(ed)
    try:
        T.successor(v, ch, led); res.append(nm + ":ACCEPTED")
    except CustodyError:
        res.append(nm + ":refused")
print("[E1]", res)


def p2():
    v1, q1 = T.make_world(); led = CU.CustodyLedger(); CU.record_generator_freeze(v1, led)
    v2, _ = T.make_world(T.set_snr(0.9)); T.successor(v1, v2, led); CU.record_generator_freeze(v2, led)
    setup(v1, q1, led, None)
run("P2 superseded commit", p2)


def w1():
    v1, q1, led = root(); qrun(v1, led); wreveal(v1, q1, led, W_A)
    v2, q2, disp = succ(v1, led, conf(3), withheld=EASY); setup(v2, q2, led, "UNCHANGED"); qrun(v2, led)
    wreveal(v2, q2, led, EASY)
run("W1 easier family UNCHANGED", w1)


def w1b():
    v1, q1, led = root(); qrun(v1, led)
    v2, q2, _ = succ(v1, led, conf(3), withheld=EASY); setup(v2, q2, led, "CHANGED_BY_DEFECT")
run("W1b CHANGED w/o defect", w1b)


def w2():
    v1, q1, led = root(); qrun(v1, led); ch, _ = T.make_world(); T.successor(v1, ch, led)
run("W2 reroll", w2)


def q1():
    v1, q1_, led = root(); qrun(v1, led)
    v2, q2, _ = succ(v1, led, conf(3)); setup(v2, q2, led, "UNCHANGED"); qrun(v2, led)
    v3, q3_, _ = succ(v2, led, conf(4)); setup(v3, q3_, led, "UNCHANGED"); expose(v3, led, QUAL, "open")
    CU.reveal_class_nonce(v2, led, class_tag=QUAL, nonce=q2)
run("Q1", q1)


def q1b():
    v1, q1_, led = root(); qrun(v1, led)
    v2, q2, _ = succ(v1, led, conf(3)); setup(v2, q2, led, "UNCHANGED"); expose(v2, led, QUAL, "open")
    CU.reveal_class_nonce(v1, led, class_tag=QUAL, nonce=q1_)
run("Q1b", q1b)


def q3():
    v1, q1_, led = root(withheld=W_A); qrun(v1, led); wreveal(v1, q1_, led, W_A)
    v2, q2, _ = succ(v1, led, conf(3), withheld=W_B, defect_components=["withheld_family"])
    setup(v2, q2, led, "CHANGED_BY_DEFECT"); qrun(v2, led); wreveal(v2, q2, led, W_B)
    v3, q3_, _ = succ(v2, led, conf(4), withheld=W_A, defect_components=["withheld_family"])
    setup(v3, q3_, led, "CHANGED_BY_DEFECT"); qrun(v3, led)
    pre = CU.withheld_check_eligible(led, v3.generator_semantic_hash)
    wreveal(v3, q3_, led, W_A)
    return "eligible before own reveal", pre, "after", CU.withheld_check_eligible(led, v3.generator_semantic_hash)
run("Q3", q3)


def elig_normal():
    v1, q1_, led = root(); qrun(v1, led)
    pre = CU.withheld_check_eligible(led, v1.generator_semantic_hash)
    wreveal(v1, q1_, led, W_A)
    return pre, CU.withheld_check_eligible(led, v1.generator_semantic_hash)
run("eligible normal (pre-reveal, post-reveal)", elig_normal)


def q2a():
    v1, q1_, led = root(); qrun(v1, led, method=T.METHOD_A); wreveal(v1, q1_, led, W_A)
    v2, q2, _ = succ(v1, led, conf(2.000001)); setup(v2, q2, led, "UNCHANGED"); qrun(v2, led, method=T.METHOD_A_RENAMED)
    return (len(CU.qualification_draws_for_method(led, T.METHOD_A)), len(CU.qualification_draws_for_method(led, T.METHOD_A_RENAMED)),
            len(CU.qualification_draws_in_lineage(led, v1.generator_semantic_hash)), len(CU.qualification_draws_in_lineage(led, v2.generator_semantic_hash)))
run("Q2a/rename (perA, perA2, lineage@v1, lineage@v2)", q2a)
run("method_id plain", lambda: expose(*root()[::2], DEBUG, "x", method="fixture_method"))


def fitgate():
    v, q, led = root()
    expose(v, led, QUAL, "a"); expose(v, led, QUAL, "b", method=T.METHOD_B)
    CU.record_fit_output_frozen(v, led, exposure_id="a", fit_output_sha256=T._h("a"))
    out = []
    for nm, fn in (("reveal nonce with b unfrozen", lambda: CU.reveal_class_nonce(v, led, class_tag=QUAL, nonce=q)),
                   ("withheld reveal with b unfrozen", lambda: wreveal(v, q, led, W_A)),
                   ("new exposure after a fit", lambda: expose(v, led, QUAL, "c"))):
        try:
            fn(); out.append(nm + ":ACCEPTED")
        except CustodyError:
            out.append(nm + ":refused")
    CU.record_fit_output_frozen(v, led, exposure_id="b", fit_output_sha256=T._h("b"))
    CU.reveal_class_nonce(v, led, class_tag=QUAL, nonce=q); wreveal(v, q, led, W_A); out.append("after both fits: reveals ok")
    return out
run("fit gate", fitgate)
run("reveal before fit", lambda: (lambda v, q, led: (expose(v, led, QUAL, "a"), CU.reveal_class_nonce(v, led, class_tag=QUAL, nonce=q)))(*root()))


def p3():
    spec = T.base_spec(); dn = T.dummy_nonce(); qn = T.dummy_nonce()
    pre = CU.generator_precommitment_semantic_hash(spec)
    spec["withheld_family_commitment"] = CU.withheld_family_commitment(dn, W_A, pre, WTAG)
    fr = CU.freeze_generator_version(spec); led = CU.CustodyLedger(); CU.record_generator_freeze(fr, led)
    nonces = {DEBUG: dn, QUAL: qn}
    for tag in (DEBUG, QUAL):
        CU.record_nonce_commitment(fr, led, class_tag=tag, nonce_commitment=CU.nonce_commitment(nonces[tag]))
    T.commit_withheld(fr, qn, led, tree())
    for tag in (DEBUG, QUAL):
        b = fr.realization_budget(tag); r = CU.sealed_root(nonces[tag], fr.generator_semantic_hash, tag, b)
        CU.attest_realization_set(fr, led, root=r, class_tag=tag, emitted=T.emit(r, tag, b))
    qrun(fr, led); wreveal(fr, dn, led, W_A)
run("P3 debug-nonce withheld reveal", p3)


def scan_unbound():
    v, q = T.make_world(); led = CU.CustodyLedger(); CU.record_generator_freeze(v, led)
    CU.record_nonce_commitment(v, led, class_tag=QUAL, nonce_commitment=CU.nonce_commitment(q))
    t = tree()
    CU.record_withheld_commitment(v, led, withheld_class_tag=WTAG, nonce_commitment=CU.nonce_commitment(q),
                                  secret_absence_attestations=[CU.require_secret_absence(t, C.canonical_json_bytes(W_A))],
                                  code_path_attestation=T.code_path_attestation())
run("withheld commit with no nonce-bound scan", scan_unbound)
