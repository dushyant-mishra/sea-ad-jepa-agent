"""Source census for the production observation contract (metadata only; no expression values).

usage: python -I observation_source_census_probe.py <repo-root> <stage81a3r-root>

1. Every FULL104 (matrix, address) pair in the collision ledger and its unregistered
   supplement: which operator state does the frozen state matrix give it?
2. Address-universe symbols commonly used by depositor QC (mitochondrial, ribosomal,
   MALAT1/NEAT1): which queries would be QC-entangled if depositors filtered on them.
"""
import json
import sys

import numpy as np
import pandas as pd

ROOT, AUTH = sys.argv[1].rstrip("/") + "/", sys.argv[2].rstrip("/") + "/"
lineage = pd.read_csv(ROOT + "outputs/full104_v014_20260826/01_full104_metadata_adapter/FULL104_ROW_LINEAGE.csv")
op_of = dict(zip(lineage.matrix_id.astype(str), lineage.operator_index.astype(int)))
registry = pd.read_csv(ROOT + "results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv", dtype=str)
index_of = dict(zip(registry.molecular_address_id, registry.molecular_address_index.astype(int)))
states = np.load(ROOT + "exports/foundation_calibration_bundle_20260824/support/"
                 "FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz", allow_pickle=False)["states"]
ledger = pd.read_csv(AUTH + "results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz", low_memory=False)
supplement = pd.read_csv(AUTH + "results/v4/stage81a3r_scalar_mapping_unregistered_collisions.csv")
pairs = pd.concat([ledger[["matrix_id", "molecular_address_id"]],
                   supplement[["matrix_id", "molecular_address_id"]]]).drop_duplicates()
pairs = pairs[pairs.matrix_id.astype(str).isin(op_of)]
pair_states = [int(states[op_of[str(m)], index_of[a]]) if a in index_of else -1
               for m, a in zip(pairs.matrix_id, pairs.molecular_address_id)]
symbols = registry.symbol.fillna("")
upper = symbols.str.upper()
out = {
    "collision_pairs_full104": int(len(pairs)),
    "collision_matrices_full104": int(pairs.matrix_id.nunique()),
    "collision_pair_operator_states": {str(k): int(v) for k, v in pd.Series(pair_states).value_counts().items()},
    "state_matrix_totals": {str(int(k)): int(v) for k, v in zip(*np.unique(states, return_counts=True))},
    "address_universe": int(len(registry)),
    "qc_entangled_candidates": {
        "mitochondrial_MT-": sorted(symbols[upper.str.startswith("MT-")].tolist()),
        "ribosomal_RPS_RPL_count": int(upper.str.match(r"^RP[SL]\d").sum()),
        "MALAT1_NEAT1": sorted(set(symbols[symbols.isin(["MALAT1", "NEAT1"])])),
    },
}
print(json.dumps(out, indent=1, sort_keys=True))
