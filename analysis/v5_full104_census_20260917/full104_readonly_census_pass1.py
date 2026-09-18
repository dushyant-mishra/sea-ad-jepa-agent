"""FULL104 read-only support/precision/evidence-budget census -- PASS 1.

Reads ONLY sparsity structure (indices/indptr) and block metadata.
Inspects NO RIDGE8/TOP8/PREFIX3 qualification outcome.
No expression values are used for any decision; `data` is never loaded.
"""
import numpy as np, pathlib, csv, time, json, collections, sys

P = pathlib.Path(r'D:/Jepa project')
L4 = P/'outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4'
OUT = pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad/census')
NA = 41238

st = np.load(P/'exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz',
             allow_pickle=False)['states']
panel_scalar = (st == 1)                       # 42 x 41238 strictly MEASURED_SCALAR
panel_any    = (st == 1) | (st == 2)           # includes MEASURED_COLLISION_UNRESOLVED
core = np.flatnonzero(panel_scalar.all(0))     # 17,186 terminal common core
in_core = np.zeros(NA, bool); in_core[core] = True

rows = list(csv.DictReader((L4/'PHASE2_EXPRESSION_BLOCK_MANIFEST.csv').open(newline='')))
NB = len(rows)

# ---- donor registry (from block metadata) ----
donor_of_block = []
donors = {}
t0 = time.time()
for bi, r in enumerate(rows):
    md = list(csv.DictReader((L4/r['meta_path']).open(newline='')))
    dl = [x['donor_id'] for x in md]
    lib = np.array([float(x['source_library']) for x in md], dtype=np.float64)
    donor_of_block.append((dl, lib))
    for d in dl: donors[d] = None
duniq = np.array(sorted(donors)); dindex = {d: i for i, d in enumerate(duniq)}
ND = duniq.size
print('metadata pass: %d blocks, %d donors, %.1f s' % (NB, ND, time.time()-t0), flush=True)

# ---- accumulators ----
NC = sum(int(r['rows']) for r in rows)
cell_donor   = np.zeros(NC, np.int16)
cell_op      = np.zeros(NC, np.int8)
cell_nnz_tot = np.zeros(NC, np.int32)   # measured-nonzero, all addresses
cell_nnz_core= np.zeros(NC, np.int32)   # measured-nonzero within terminal common core
cell_lib     = np.zeros(NC, np.float64)
donor_addr_nnz = np.zeros((ND, NA), np.int32)   # cells with nonzero, per donor x address
donor_src = np.zeros(ND, np.int8)
donor_ops = collections.defaultdict(set)
SRC = {'HVS': 0, 'NPH52': 1, 'SEA_AD': 2}
nnz_outside_panel = 0
nnz_in_collision  = 0

pos = 0
t0 = time.time()
for bi, r in enumerate(rows):
    op = int(r['operator_index']); src = SRC[r['source']]
    z = np.load(L4/r['counts_path'], allow_pickle=False)
    ip = z['indptr']; ix = z['indices']
    n = len(ip)-1
    dl, lib = donor_of_block[bi]
    dcodes = np.array([dindex[d] for d in dl], np.int16)
    cell_donor[pos:pos+n] = dcodes
    cell_op[pos:pos+n] = op
    cell_lib[pos:pos+n] = lib
    for d in np.unique(dcodes):
        donor_src[d] = src; donor_ops[int(d)].add(op)
    cnt = np.diff(ip)
    cell_nnz_tot[pos:pos+n] = cnt
    corehit = in_core[ix]
    cell_nnz_core[pos:pos+n] = np.add.reduceat(corehit.astype(np.int32),
                                               ip[:-1]) * (cnt > 0) if n else 0
    # exact per-row core counts (reduceat mishandles empty rows; correct them)
    empty = np.flatnonzero(cnt == 0)
    if empty.size: cell_nnz_core[pos+empty] = 0
    # panel conformance
    ps = panel_scalar[op]; pa = panel_any[op]
    nnz_outside_panel += int((~pa[ix]).sum())
    nnz_in_collision  += int((pa[ix] & ~ps[ix]).sum())
    # donor x address nonzero counts
    for d in np.unique(dcodes):
        sel = np.flatnonzero(dcodes == d)
        for i in sel:
            a, b = ip[i], ip[i+1]
            if b > a: donor_addr_nnz[d, ix[a:b]] += 1
    pos += n
    if (bi+1) % 500 == 0:
        el = time.time()-t0
        print('  block %5d/%d  cells %9d  %.1f min elapsed, %.1f min est total'
              % (bi+1, NB, pos, el/60, el/60*NB/(bi+1)), flush=True)

assert pos == NC, (pos, NC)
np.savez_compressed(OUT/'pass1.npz', cell_donor=cell_donor, cell_op=cell_op,
                    cell_nnz_tot=cell_nnz_tot, cell_nnz_core=cell_nnz_core,
                    cell_lib=cell_lib, donor_addr_nnz=donor_addr_nnz,
                    donor_src=donor_src, duniq=duniq, core=core)
json.dump({'n_cells': int(NC), 'n_donors': int(ND), 'n_blocks': NB,
           'nnz_outside_declared_panel': nnz_outside_panel,
           'nnz_in_collision_unresolved': nnz_in_collision,
           'donor_operators': {str(k): sorted(v) for k, v in donor_ops.items()},
           'wall_min': (time.time()-t0)/60}, open(OUT/'pass1_meta.json', 'w'), indent=2)
print('PASS1_DONE cells=%d donors=%d outside_panel=%d collision=%d %.1f min'
      % (NC, ND, nnz_outside_panel, nnz_in_collision, (time.time()-t0)/60), flush=True)
