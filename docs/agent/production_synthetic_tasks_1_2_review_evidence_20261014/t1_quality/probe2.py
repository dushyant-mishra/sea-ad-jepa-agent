import sys, time, json
sys.path.insert(0, "D:/jepa_prodsynth_v311_impl_20261014")
import scripts.production_synthetic.canonical_v1 as C
l = []
cur = l
for _ in range(3000):
    n = []; cur.append(n); cur = n
try: C.canonical_json_bytes(l); print("deep accepted")
except C.CanonicalError: print("deep -> CanonicalError")
except Exception as e: print("deep LEAK", type(e).__name__)
def t(label, fn):
    t0 = time.perf_counter(); r = fn(); print(f"{label}: {time.perf_counter()-t0:.2f}s"); return r
reg = [{"address_index": i, "address_id": f"ADDR{i:05d}", "gene_symbol": f"GENE{i}", "ensembl": f"ENSG{i:011d}",
        "chrom": "chr1", "start": i*100, "biotype": "protein_coding", "measured": True} for i in range(41238)]
t("ordered_registry_digest 41,238 x 8 fields", lambda: C.ordered_registry_digest(reg, ["address_index", "address_id"]))
rows = [{"selection_row": i, "donor_id": f"H20.33.{i%500:03d}", "cell_type": "L2/3 IT", "v1": i/7, "v2": i/11,
         "v3": None, "qc": "pass", "n_umi": 1000+i, "flag": False, "note": "x"*30} for i in range(100000)]
t("semantic_row_set_sha256 1e5 x 10 fields", lambda: C.semantic_row_set_sha256(rows, ["selection_row"]))
t("canonical_json_bytes 1e5 rows (one blob)", lambda: C.canonical_json_bytes(rows))
t("json.dumps sort_keys reference 1e5 rows", lambda: json.dumps(rows, sort_keys=True, ensure_ascii=False, separators=(",",":")).encode())
t("load_canonical_json of 1e5-row blob", lambda: C.load_canonical_json(C.canonical_json_bytes(rows)))
