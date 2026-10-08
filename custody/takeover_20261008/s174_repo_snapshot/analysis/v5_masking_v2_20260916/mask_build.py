"""Read-only FULL104 materialization for masking qualification.

Builds a frozen, seeded address+cell sample and the per-donor measurability matrix.
No training. No D_shared. No protected outcome. Read-only with respect to FULL104.
"""
import csv, hashlib, json, pathlib, time
import numpy as np

P = pathlib.Path(r'D:/Jepa project')
L4 = P / 'outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4'
OBS = P / 'exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz'
OUT = pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')

NS = 'JEPA_V5_MASKING_QUALIFICATION_SAMPLE_V1'
N_COMMON = 400          # sampled from common core (measurable in all 42 operators)
N_NATIVE = 200          # sampled from native-support addresses
BLOCKS_PER_OP = 4
t0 = time.time()

z = np.load(OBS, allow_pickle=False)
states = z['states']                       # (42, 41238) uint8; 1 == MEASURED_SCALAR
measurable_by_op = (states == 1)
n_ops, n_addr = measurable_by_op.shape
common = np.flatnonzero(measurable_by_op.all(axis=0))
n_op_measuring = measurable_by_op.sum(axis=0)
native = np.flatnonzero((n_op_measuring >= 8) & (n_op_measuring < n_ops))
print('addresses %d | common-core %d | native (8..41 ops) %d' % (n_addr, common.size, native.size))

def seeded(name):
    return np.random.default_rng(int.from_bytes(
        hashlib.sha256(f'{NS}|{name}'.encode()).digest()[:8], 'big'))

sel_common = np.sort(seeded('common').choice(common, size=min(N_COMMON, common.size), replace=False))
sel_native = np.sort(seeded('native').choice(native, size=min(N_NATIVE, native.size), replace=False))
addr_sel = np.sort(np.concatenate([sel_common, sel_native]))
is_common = np.isin(addr_sel, sel_common)
pos_of_addr = {int(a): i for i, a in enumerate(addr_sel)}
print('sampled addresses %d (common %d, native %d)' % (addr_sel.size, sel_common.size, sel_native.size))

rows = list(csv.DictReader((L4 / 'PHASE2_EXPRESSION_BLOCK_MANIFEST.csv').open(newline='')))
by_op = {}
for i, r in enumerate(rows):
    by_op.setdefault(int(r['operator_index']), []).append(i)
blocks = []
for op in sorted(by_op):
    idxs = by_op[op]
    g = seeded(f'blocks|{op}')
    pick = g.choice(len(idxs), size=min(BLOCKS_PER_OP, len(idxs)), replace=False)
    blocks += [idxs[int(k)] for k in pick]
blocks = sorted(set(blocks))
print('blocks selected %d of %d' % (len(blocks), len(rows)))

vals, donors, srcs, ops = [], [], [], []
for n, bi in enumerate(blocks):
    r = rows[bi]
    zz = np.load(L4 / r['counts_path'], allow_pickle=False)
    indptr, indices, data = zz['indptr'], zz['indices'], zz['data'].astype(np.float64)
    nr = len(indptr) - 1
    md = list(csv.DictReader((L4 / r['meta_path']).open(newline='')))
    lib = np.array([float(x['source_library']) for x in md])
    dense = np.zeros((nr, addr_sel.size), dtype=np.float32)
    for i in range(nr):
        a, b = indptr[i], indptr[i + 1]
        if b <= a or lib[i] <= 0:
            continue
        ix, ct = indices[a:b], data[a:b]
        keep = np.isin(ix, addr_sel)
        if not keep.any():
            continue
        # frozen FULL104 normalization, applied exactly once
        nm = np.log1p(ct[keep] * 10000.0 / lib[i])
        cols = np.array([pos_of_addr[int(v)] for v in ix[keep]], dtype=np.int64)
        dense[i, cols] = nm
    vals.append(dense)
    donors += [x['donor_id'] for x in md]
    srcs += [r['source']] * nr
    ops += [int(r['operator_index'])] * nr
    if (n + 1) % 40 == 0:
        print('  %d/%d blocks  %.1f min' % (n + 1, len(blocks), (time.time() - t0) / 60), flush=True)

V = np.vstack(vals)
donors = np.array(donors); srcs = np.array(srcs); ops = np.array(ops, dtype=np.int32)
dcode, duniq = None, None
duniq, dcode = np.unique(donors, return_inverse=True)
print('cells %d | donors %d | sources %s' % (V.shape[0], duniq.size, dict(zip(*np.unique(srcs, return_counts=True)))))

# per-donor measurability, derived from the operator observation state (never from values)
op_of_donor = np.zeros(duniq.size, dtype=np.int32)
src_of_donor = np.empty(duniq.size, dtype=object)
for d in range(duniq.size):
    sel = dcode == d
    op_of_donor[d] = np.bincount(ops[sel]).argmax()
    src_of_donor[d] = srcs[sel][0]
meas_by_donor = measurable_by_op[op_of_donor][:, addr_sel]
print('per-donor measurable fraction: min %.3f median %.3f max %.3f'
      % (meas_by_donor.mean(1).min(), np.median(meas_by_donor.mean(1)), meas_by_donor.mean(1).max()))

np.savez_compressed(OUT / 'mask_sample.npz', values=V, donor_code=dcode, operator=ops,
                    addr_sel=addr_sel, is_common=is_common, meas_by_donor=meas_by_donor,
                    op_of_donor=op_of_donor,
                    source=np.array([str(s) for s in srcs]),
                    src_of_donor=np.array([str(s) for s in src_of_donor]))
json.dump({'namespace': NS, 'n_cells': int(V.shape[0]), 'n_donors': int(duniq.size),
           'n_addresses': int(addr_sel.size), 'n_common': int(is_common.sum()),
           'n_native': int((~is_common).sum()), 'blocks': len(blocks),
           'blocks_per_operator': BLOCKS_PER_OP,
           'normalization': 'log1p(raw*10000/source_library) applied exactly once',
           'measurability_source': 'FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz state==MEASURED_SCALAR',
           'read_only_full104': True, 'no_protected_data': True},
          open(OUT / 'mask_sample_plan.json', 'w'), indent=2, sort_keys=True)
print('wall %.1f min  SAMPLE_DONE' % ((time.time() - t0) / 60))
