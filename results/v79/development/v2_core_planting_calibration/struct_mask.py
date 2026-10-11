"""DEVELOPMENT ONLY. Per-(cell, gene) structural measurement support for the G500 cache genes, from the Stage81A2R
matrix-level measurement-support authority joined through the S174 operator bridge (operator_index -> matrix_id)."""
import hashlib, json, numpy as np, pandas as pd
CACHE = "D:/v79_runs/615b55eb/results/v79/development/s174_structure_replay/V79_ANALYSIS_CACHE_G500.npz"
BRIDGE = "D:/v79_runs/615b55eb/results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json"
SUPPORT = "D:/Jepa project/results/v4/stage81a2r_foundation_molecular_address_measurement_support_candidate.csv.gz"
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
z = np.load(CACHE, allow_pickle=False)
addr, C, src, op = z["gene_address_index"], z["counts_selected"], z["src"], z["op"]
rows = json.load(open(BRIDGE, encoding="utf-8"))["rows"]
mat_of = {}
for r in rows:
    mat_of.setdefault(int(r["operator_index"]), set()).add(r["matrix_id"])
assert all(len(v) == 1 for v in mat_of.values()), "operator maps to several matrices"
mat_of = {k: next(iter(v)) for k, v in mat_of.items()}
sup = pd.read_csv(SUPPORT, usecols=["matrix_id", "molecular_address_index", "measured_address", "measurement_status"])
sup = sup[sup.molecular_address_index.isin(addr)]
missing_mats = sorted(set(mat_of.values()) - set(sup.matrix_id))
assert not missing_mats, missing_mats
key = {(m, int(a)): bool(v) for m, a, v in zip(sup.matrix_id, sup.molecular_address_index, sup.measured_address)}
ops = np.unique(op)
M = np.zeros((len(ops), len(addr)), bool)  # operator x gene measured
for i, o in enumerate(ops):
    for g, a in enumerate(addr):
        M[i, g] = key[(mat_of[int(o)], int(a))]
op_pos = {int(o): i for i, o in enumerate(ops)}
cellmask = M[[op_pos[int(o)] for o in op]]          # cells x genes
viol = int((C[~cellmask] > 0).sum())
print("nonzero counts on structurally unmeasured cells:", viol)
unmeasured_frac_by_gene = 1 - cellmask.mean(0)
part = (unmeasured_frac_by_gene > 0)
print("genes with any structurally unmeasured cells:", int(part.sum()), "of", len(addr))
print("genes fully unmeasured in >=1 source:", int(sum(any(not cellmask[src == s, g].any() for s in range(3)) for g in range(len(addr)))))
print("genes partially unmeasured within a source:", int(sum(any(0 < cellmask[src == s, g].mean() < 1 for s in range(3)) for g in range(len(addr)))))
print("unmeasured cell-gene entries: %.4f of all" % (1 - cellmask.mean()))
by_src = {s: int(sum((not cellmask[src == s, g].all()) for g in range(len(addr)))) for s in range(3)}
print("genes with unmeasured cells, by source:", by_src)
allzero_src = [(g, s) for g in range(len(addr)) for s in range(3) if not (C[src == s, g] > 0).any()]
print("all-zero (gene,source) pairs:", len(allzero_src), "of which fully unmeasured:", sum(not cellmask[src == s, g].any() for g, s in allzero_src))
np.save("V79_G500_STRUCTURAL_SUPPORT_OPxGENE.npy", M)
json.dump(dict(schema="V79_G500_STRUCTURAL_SUPPORT_DEV_V1", cache_sha256=sha(CACHE), bridge_sha256=sha(BRIDGE), support_sha256=sha(SUPPORT),
               operators=[int(o) for o in ops], matrix_of_operator={int(o): mat_of[int(o)] for o in ops},
               nonzero_on_unmeasured=viol, genes_any_unmeasured=int(part.sum()),
               op_x_gene_sha256=hashlib.sha256(np.ascontiguousarray(M).tobytes()).hexdigest()),
          open("V79_G500_STRUCTURAL_SUPPORT_DEV.json", "w"), indent=1)
