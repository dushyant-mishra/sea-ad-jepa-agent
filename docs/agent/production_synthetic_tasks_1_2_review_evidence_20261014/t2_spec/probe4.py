import sys, os, secrets, pathlib, tempfile, base64, json
WT = "D:/jepa_prodsynth_v311_impl_20261014"
sys.path.insert(0, WT); os.chdir(WT)
import scripts.production_synthetic.canonical_v1 as C
import scripts.production_synthetic.custody_v1 as CU
import tests.production_synthetic.test_custody_v1_hostile as T
from scripts.production_synthetic.custody_v1 import CustodyError
base = pathlib.Path(tempfile.mkdtemp(dir="D:/jepa_ps_t2_review_scratch"))
k = [0]


def tree():
    k[0] += 1
    return T.make_tree(base, f"t{k[0]}")


def run(name, fn):
    try:
        print(f"[{name}] OK -> {fn()}")
    except Exception as e:
        print(f"[{name}] {type(e).__name__}: {e}")


def chain(e):
    return T._chain_text(e)


def exposed_parent():
    p, q = T.make_world(); led = CU.CustodyLedger(); T.prepare(p, q, led, tree()); T.expose(p, led)
    return p, q, led


eds = {
    "mixture novelty->0": lambda s: s.__setitem__("mechanism_mixture", {"weights": {"program_a": 0.5, "program_b": 0.5, "novelty_program": 0.0}}),
    "dropout relaxed": lambda s: s["observation_calibration_distributions"].__setitem__("dropout", {"law": "beta", "a": 1.0, "b": 50.0}),
    "control matrix shrunk": lambda s: s.__setitem__("applicability_control_matrix", {"matched_null": ["all_targets"]}),
    "qual budget 4->1": lambda s: s["realization_budgets"].__setitem__("SYNTH_QUALIFICATION", 1),
    "debug budget removed": lambda s: s["realization_budgets"].pop("SYNTH_DEBUG"),
    "param sigma": lambda s: s["parameter_distributions"]["library_size"].__setitem__("sigma", 0.01),
}
for nm, ed in eds.items():
    def f(ed=ed):
        p, q, led = exposed_parent(); ch, _ = T.make_world(ed); return T.successor(p, ch, led).disposition
    run("P1 " + nm, f)


def p2():
    v1, q1 = T.make_world(); led = CU.CustodyLedger(); CU.record_generator_freeze(v1, led)
    v2, q2 = T.make_world(T.set_snr(0.9)); T.successor(v1, v2, led); CU.record_generator_freeze(v2, led)
    T.commit_and_attest(v1, q1, led, tree())
run("P2 superseded V1 commit/attest", p2)


def p2b():
    v1, q1 = T.make_world(); led = CU.CustodyLedger(); T.prepare(v1, q1, led, tree())
    v2, _ = T.make_world(T.set_snr(0.9)); T.successor(v1, v2, led)
    T.expose(v1, led, "SYNTH_QUALIFICATION", "late")
run("P2b expose parent after successor recorded", p2b)


def p2c():
    v1, q1 = T.make_world(); led = CU.CustodyLedger(); CU.record_generator_freeze(v1, led)
    a, _ = T.make_world(T.set_snr(0.4)); b, _ = T.make_world(T.set_snr(0.3))
    T.successor(v1, a, led); T.successor(v1, b, led)
run("P2c second successor of same parent", p2c)


def p3():
    spec = T.base_spec(); dn = T.dummy_nonce(); qn = T.dummy_nonce()
    pre = CU.generator_precommitment_semantic_hash(spec)
    spec["withheld_family_commitment"] = CU.withheld_family_commitment(dn, T.DUMMY_WITHHELD_SPEC, pre, T.WTAG)
    fr = CU.freeze_generator_version(spec); led = CU.CustodyLedger(); CU.record_generator_freeze(fr, led)
    CU.record_nonce_commitment(fr, led, class_tag="SYNTH_DEBUG", nonce_commitment=CU.nonce_commitment(dn))
    CU.record_nonce_commitment(fr, led, class_tag="SYNTH_QUALIFICATION", nonce_commitment=CU.nonce_commitment(qn))
    CU.record_withheld_commitment(fr, led, withheld_class_tag=T.WTAG, nonce_commitment=CU.nonce_commitment(qn),
                                  secret_absence_attestations=[CU.require_secret_absence(tree(), qn)],
                                  code_path_attestation=T.code_path_attestation())
    for tag, n in (("SYNTH_DEBUG", dn), ("SYNTH_QUALIFICATION", qn)):
        b = fr.realization_budget(tag); r = CU.sealed_root(n, fr.generator_semantic_hash, tag, b)
        CU.attest_realization_set(r, tag, b, T.emit(r, tag, b), led, freeze=fr)
    T.expose(fr, led, "SYNTH_DEBUG", "d1")
    CU.record_fit_output_frozen(fr, led, class_tag="SYNTH_DEBUG", fit_output_sha256=T._h("f"))
    CU.reveal_class_nonce(fr, led, class_tag="SYNTH_DEBUG", nonce=dn)
    T.expose(fr, led, "SYNTH_QUALIFICATION", "q1")
    CU.record_fit_output_frozen(fr, led, class_tag="SYNTH_QUALIFICATION", fit_output_sha256=T._h("g"))
    try:
        CU.reveal_withheld_family(fr, led, withheld_spec=T.DUMMY_WITHHELD_SPEC, nonce=dn, withheld_class_tag=T.WTAG)
        return "withheld reveal with debug nonce ACCEPTED"
    except CustodyError as e:
        return f"steps accepted up to reveal; reveal refused: {e}"
run("P3 debug-nonce withheld commitment", p3)


def p3b():
    p, q, led = exposed_parent()
    T.expose(p, led, "SYNTH_QUALIFICATION", "q")
    CU.reveal_class_nonce(p, led, class_tag="SYNTH_QUALIFICATION", nonce=q)
run("P3b qual nonce reveal before qual fit freeze", p3b)

EASY = {"DUMMY_family": {"composition": "DUMMY_trivially_separable", "weight": 0.9}, "DUMMY_scoring_rule": "DUMMY",
        "DUMMY_budget": 2}


def full_cycle(fr, q, led, withheld):
    T.commit_and_attest(fr, q, led, tree())
    T.expose(fr, led, "SYNTH_QUALIFICATION", "q-" + fr.generator_semantic_hash[:6])
    CU.record_fit_output_frozen(fr, led, class_tag="SYNTH_QUALIFICATION", fit_output_sha256=T._h(fr.generator_semantic_hash))
    CU.reveal_class_nonce(fr, led, class_tag="SYNTH_QUALIFICATION", nonce=q)
    CU.reveal_withheld_family(fr, led, withheld_spec=withheld, nonce=q, withheld_class_tag=T.WTAG)


def w1():
    p, q = T.make_world(); led = CU.CustodyLedger(); CU.record_generator_freeze(p, led)
    full_cycle(p, q, led, T.DUMMY_WITHHELD_SPEC)
    ch, q2 = T.make_world(withheld=EASY)
    d = T.successor(p, ch, led); CU.record_generator_freeze(ch, led); full_cycle(ch, q2, led, EASY)
    return d.disposition, d.changed_components, "easier withheld family committed/exposed/revealed: accepted"
run("W1 withheld family swapped post-exposure", w1)


def w1b():
    # parent exposed but withheld NOT yet revealed; child swaps withheld family
    p, q, led = exposed_parent()
    ch, q2 = T.make_world(withheld=EASY)
    return T.successor(p, ch, led).disposition
run("W1b swap withheld before parent reveal", w1b)


def w2():
    p, q = T.make_world(); led = CU.CustodyLedger(); CU.record_generator_freeze(p, led)
    full_cycle(p, q, led, T.DUMMY_WITHHELD_SPEC)
    out = []; cur = p
    for i in range(3):
        ch, qn = T.make_world()
        assert ch.precommitment_semantic_hash == p.precommitment_semantic_hash
        out.append(T.successor(cur, ch, led).disposition); CU.record_generator_freeze(ch, led)
        full_cycle(ch, qn, led, T.DUMMY_WITHHELD_SPEC); cur = ch
    return out, "3 rerolls of sealed qualification draw, identical public spec"
run("W2 identical reroll successors", w2)


def w3():
    p, q, led = exposed_parent()
    ch, q2 = T.make_world()
    s = ch.spec(); s["withheld_family_commitment"] = p.withheld_family_commitment
    try:
        CU.freeze_generator_version(s); return "child with copied parent commitment == parent version (same gsh)"
    except CustodyError as e:
        return str(e)
run("W3 copy parent commitment", w3)


def scan_with(name, content_fn, n=20):
    hits = 0
    for i in range(n):
        s = secrets.token_bytes(32); d = base / f"{name}{i}"; d.mkdir(); (d / "ok.txt").write_bytes(b"x")
        content_fn(d, s); hits += (not CU.scan_secret_absence(d, s)["secret_absent"])
    print(f"[scan {name}] detected {hits}/{n}")


def pad():
    return secrets.token_bytes(secrets.randbelow(60))


scan_with("mime76", lambda d, s: (d / "f").write_bytes(base64.encodebytes(pad() + s)))
scan_with("pem64", lambda d, s: (d / "f").write_bytes(b"\n".join([base64.b64encode(pad() + s)[i:i + 64] for i in range(0, 200, 64)])))
scan_with("crlf_wrapped_b64", lambda d, s: (d / "f").write_bytes(base64.encodebytes(pad() + s).replace(b"\n", b"\r\n")))
scan_with("py_repr", lambda d, s: (d / "f.py").write_text(f"N = {s!r}\n"))
scan_with("py_repr_bytearray", lambda d, s: (d / "f.py").write_text(f"N = {bytearray(s)!r}\n"))
scan_with("json_int_list", lambda d, s: (d / "f.json").write_text(json.dumps(list(s))))
scan_with("json_int_list_indented", lambda d, s: (d / "f.json").write_text(json.dumps(list(s), indent=2)))
scan_with("hex_colon", lambda d, s: (d / "f").write_text(":".join(f"{b:02x}" for b in s)))
scan_with("hex_space_upper", lambda d, s: (d / "f").write_text(" ".join(f"{b:02X}" for b in s)))
scan_with("hex_c_array", lambda d, s: (d / "f").write_text("{" + ", ".join(f"0x{b:02x}" for b in s) + "}"))
scan_with("hex_backslash_x", lambda d, s: (d / "f").write_text("".join(f"\\x{b:02x}" for b in s)))
scan_with("decimal", lambda d, s: (d / "f").write_text(str(int.from_bytes(s, "big"))))
scan_with("decimal_little", lambda d, s: (d / "f").write_text(str(int.from_bytes(s, "little"))))
scan_with("hex_wrapped_lines", lambda d, s: (d / "f").write_text(s.hex()[:30] + "\n" + s.hex()[30:]))
scan_with("b64_json_string", lambda d, s: (d / "f").write_text(json.dumps(base64.b64encode(s).decode())))
scan_with("split_files", lambda d, s: ((d / "a").write_bytes(s[:16]), (d / "b").write_bytes(s[16:])))

for label, writer in (
    ("withheld spec pretty JSON sorted", lambda ws: json.dumps(ws, indent=2, sort_keys=True)),
    ("withheld spec JSON unsorted", lambda ws: json.dumps({"rule": ws["rule"], "fam": {"w": ws["fam"]["w"], "comp": ws["fam"]["comp"]}})),
    ("withheld spec as python dict repr", lambda ws: repr(ws)),
):
    hits = 0
    for i in range(5):
        ws = {"fam": {"comp": f"x{secrets.token_hex(4)}", "w": 0.125}, "rule": "r"}
        d = base / f"ws{label[:6]}{i}{secrets.token_hex(2)}"; d.mkdir(); (d / "f.txt").write_text(writer(ws))
        hits += not CU.scan_secret_absence(d, C.canonical_json_bytes(ws))["secret_absent"]
    print(f"[scan {label}] detected {hits}/5")

fp = 0
for i in range(20):
    s = secrets.token_bytes(32); d = base / f"fp{i}"; d.mkdir()
    (d / "f").write_bytes(secrets.token_bytes(200000)); (d / "g").write_text(str(secrets.randbits(40000)))
    fp += not CU.scan_secret_absence(d, s)["secret_absent"]
print("[scan false positives, random data]", fp, "/20")

s = T.base_spec(); s["withheld_family_commitment"] = "0" * 64; s["astro_cascade_weight_0p125"] = 1
try:
    CU.freeze_generator_version(s)
except Exception as e:
    print("[M1 unknown key echo]", "astro" in chain(e), "|", chain(e)[:150])
try:
    CU.withheld_family_commitment(T.dummy_nonce(), {"astro\r\ncascade": 1, "astro\ncascade": 2}, T._h("p"), T.WTAG)
except Exception as e:
    print("[M3 withheld key echo]", "astro" in chain(e), "|", chain(e)[:150])
try:
    CU.attest_no_unique_withheld_code_path(["w"], ["x\r\nSECRETP", "x\nSECRETP", "w"], ["p"])
except Exception as e:
    print("[P6 CRLF path]", type(e).__name__, "SECRETP" in chain(e), "|", chain(e)[:150])
print("[P6 return keys]", sorted(T.code_path_attestation()))
r = secrets.token_bytes(32)
run("P4 no world_id", lambda: CU.stream_seed_digest(r, ("cell_id", "c1"), ("purpose_tag", "x")))
