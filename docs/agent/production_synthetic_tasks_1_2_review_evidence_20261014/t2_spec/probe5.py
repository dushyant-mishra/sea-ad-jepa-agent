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



def scan_with(name, content_fn, n=20):
    hits = 0
    for i in range(n):
        s = secrets.token_bytes(32); d = base / f"{name}{i}"; d.mkdir(); (d / "ok.txt").write_bytes(b"x")
        content_fn(d, s); hits += (not CU.scan_secret_absence(d, s)["secret_absent"])
    print(f"[scan {name}] detected {hits}/{n}")


def pad():
    return secrets.token_bytes(secrets.randbelow(60))


def pem(d, s):
    t = base64.b64encode(pad() + s)
    (d / "f").write_bytes(bytes([10]).join(t[i:i + 64] for i in range(0, len(t), 64)))
scan_with("pem64_fixed", pem)
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
    (d / "f").write_bytes(secrets.token_bytes(200000)); (d / "g").write_text(str(secrets.randbits(12000)))
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
