import sys, os, base64, secrets, pathlib, tempfile, json, subprocess
WT = "D:/jepa_prodsynth_v311_impl_20261014"
sys.path.insert(0, WT); os.chdir(WT)
import scripts.production_synthetic.canonical_v1 as C
import scripts.production_synthetic.custody_v1 as CU
import tests.production_synthetic.test_custody_v1_hostile as T
base = pathlib.Path(tempfile.mkdtemp(dir="D:/jepa_ps_t2_review_scratch"))
def scan_with(name, content_fn, secret=None, n=20):
    hits = 0
    for i in range(n):
        s = secret or secrets.token_bytes(32)
        d = base / f"{name}{i}"; d.mkdir(); (d/"ok.txt").write_bytes(b"x")
        content_fn(d, s)
        att = CU.scan_secret_absence(d, s)
        hits += (not att["secret_absent"])
    print(f"[scan {name}] detected {hits}/{n}")
scan_with("raw", lambda d,s: (d/"f").write_bytes(b"pre"+s))
scan_with("mime_b64_wrapped76", lambda d,s: (d/"f").write_bytes(base64.encodebytes(secrets.token_bytes(secrets.randbelow(60)) + s)))
scan_with("pem_b64_wrapped64", lambda d,s: (d/"f").write_bytes(b"\n".join([base64.b64encode(secrets.token_bytes(secrets.randbelow(60))+s)[i:i+64] for i in range(0,200,64)])))
scan_with("py_repr", lambda d,s: (d/"f.py").write_text(f"NONCE = {s!r}\n"))
scan_with("json_int_list", lambda d,s: (d/"f.json").write_text(json.dumps(list(s))))
scan_with("hex_colon", lambda d,s: (d/"f").write_text(":".join(f"{b:02x}" for b in s)))
scan_with("hex_0x_list", lambda d,s: (d/"f").write_text(", ".join(f"0x{b:02x}" for b in s)))
scan_with("hex_upper", lambda d,s: (d/"f").write_text(s.hex().upper()))
scan_with("b64_urlsafe_nopad", lambda d,s: (d/"f").write_bytes(base64.urlsafe_b64encode(b"ab"+s).rstrip(b"=")))
scan_with("decimal_int", lambda d,s: (d/"f").write_text(str(int.from_bytes(s,"big"))))
scan_with("utf16_hex", lambda d,s: (d/"f").write_bytes(s.hex().encode("utf-16-le")))
scan_with("split_across_files", lambda d,s: ((d/"a").write_bytes(s[:16]), (d/"b").write_bytes(s[16:])))
scan_with("in_dot_git", lambda d,s: ((d/".git").mkdir(), (d/".git"/"x").write_bytes(s)))
scan_with("in_nested_dot_git_dir", lambda d,s: ((d/"sub"/".git").mkdir(parents=True), (d/"sub"/".git"/"x").write_bytes(s)))
scan_with("in_dot_GIT_upper", lambda d,s: ((d/".GIT_x").mkdir(), (d/".GIT_x"/"x").write_bytes(s)), n=2)
scan_with("filename_hex", lambda d,s: (d/(s.hex()+".txt")).write_bytes(b"x"), n=3)
# symlink
try:
    d = base/"sym"; d.mkdir(); (d/"ok").write_bytes(b"x"); s = secrets.token_bytes(32)
    outside = base/"outside_secret"; outside.write_bytes(s)
    os.symlink(str(outside), str(d/"link"))
    print("[scan symlink-to-outside-secret] absent=", CU.scan_secret_absence(d, s)["secret_absent"], "(link text not followed; target outside tree)")
    d2 = base/"sym2"; d2.mkdir(); (d2/"ok").write_bytes(b"x")
    os.symlink(s.hex(), str(d2/"lnk"))
    print("[scan symlink-text-hex] absent=", CU.scan_secret_absence(d2, s)["secret_absent"])
except OSError as e:
    print("[scan symlink] cannot create symlink on this host:", e)
# junction (Windows)
d = base/"junc"; d.mkdir(); (d/"ok").write_bytes(b"x"); s = secrets.token_bytes(32)
tgt = base/"junc_target"; tgt.mkdir(); (tgt/"sec").write_bytes(s)
r = subprocess.run(["cmd","/c","mklink","/J", str(d/"j").replace("/","\\"), str(tgt).replace("/","\\")], capture_output=True, text=True)
print("[junction create]", r.returncode, r.stdout.strip())
if r.returncode == 0:
    att = CU.scan_secret_absence(d, s); print("[scan junction followed?] absent=", att["secret_absent"], "files_scanned=", att["files_scanned"])
# output shape
d = base/"shape"; d.mkdir(); s = secrets.token_bytes(32); (d/("x")).write_bytes(s)
print("[scan return keys]", CU.scan_secret_absence(d, s))
try: CU.require_secret_absence(d, s)
except Exception as e: print("[require msg]", e, "| cause:", repr(e.__cause__))
