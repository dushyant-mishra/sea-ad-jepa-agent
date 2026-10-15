import sys, time, os, secrets, base64
sys.path.insert(0, "D:/jepa_prodsynth_v311_impl_20261014")
import scripts.production_synthetic.custody_v1 as CU
root = "D:/jepa_ps_t2_quality_scratch/scan_tree"
if not os.path.isdir(root):
    rnd = secrets.token_bytes
    for i in range(2000):
        d = os.path.join(root, f"d{i%40:02d}")
        os.makedirs(d, exist_ok=True)
        # mix of text-like and binary content, ~25 KB each => ~50 MB
        if i % 2:
            data = base64.b64encode(rnd(18750))
        else:
            data = rnd(25000)
        with open(os.path.join(d, f"f{i:04d}.bin"), "wb") as fh:
            fh.write(data)
    with open(os.path.join(root, "big.bin"), "wb") as fh:
        fh.write(secrets.token_bytes(8 << 20))
tot = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(root) for f in fs)
s = secrets.token_bytes(32)
for _ in range(2):
    t = time.perf_counter(); r = CU.scan_secret_absence(root, s); dt = time.perf_counter() - t
    print(f"files={r['files_scanned']} MB={tot/1e6:.1f} absent={r['secret_absent']} time={dt:.2f}s")
# withheld spec-sized secret (long canonical json)
s2 = b"{\"DUMMY\":" + b"\"x\"," * 400 + b"\"y\":1}"
t = time.perf_counter(); r = CU.scan_secret_absence(root, s2); print(f"long secret ({len(s2)} B): {time.perf_counter()-t:.2f}s")
# plant base64-wrapped secret in one file and check found
p = os.path.join(root, "d00", "planted.txt")
open(p, "wb").write(b"x = '''\n" + b"\n".join(base64.encodebytes(b"pad" + s).split(b"\n")) + b"'''\n")
print("planted b64 found:", not CU.scan_secret_absence(root, s)["secret_absent"])
os.remove(p)
for n in (1785, 1786, 1787, 1800):
    try:
        CU.scan_secret_absence(root, secrets.token_bytes(n)); print(n, "ok")
    except Exception as e:
        print(n, type(e).__name__, isinstance(e, CU.CustodyError))
