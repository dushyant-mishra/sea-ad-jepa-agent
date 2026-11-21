"""R1/R1D/R2 source and ETL gap census (identity and grouping metadata only; no expression values).

usage: python -I r1_r2_source_gap_probe.py <repo-root> <stage81a3r-root> > out.json

Reads only bound identity tables, the frozen operator-address state matrix, the
FULL104 reader_fit row lineage (source / matrix / donor columns, aggregated to
counts) and, for HVS/SEA-AD, the declared shape attribute of each count matrix.
No count values, no pathology, no reader_validation/oracle rows, no DEV/SEALED data.
"""
import glob
import hashlib
import json
import sys

import h5py
import numpy as np
import pandas as pd

ROOT, AUTH = sys.argv[1].rstrip("/") + "/", sys.argv[2].rstrip("/") + "/"
DECISIONS = "results/v4/stage81a2r_authoritative_source_mapping_decisions_candidate.csv.gz"
PROVENANCE = "results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz"
REGISTRY = "results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv"
STATES = "exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"
PINS = {  # decision table: preservation manifest row on origin/main 2c000ecc (bytes also in git);
    DECISIONS: "e3106248ac77f8840f5ea6035dc765d8e09feeba1f6da21c830b3945d694c773",
    PROVENANCE: "df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51",  # pin listed by #492
    STATES: "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537",  # pin listed by #492
}
ENSEMBL_FIELDS = ["source_exact_ensembl_id", "authority_current_ensembl_id", "hgnc_approved_ensembl",
                  "hgnc_previous_ensembl", "hgnc_alias_ensembl", "hgnc_withdrawn_ensembl",
                  "ensembl_current_symbol_candidates", "canonical_ensembl_gene_id"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensembl_ids(row, fields):
    out = set()
    for field in fields:
        value = row[field]
        if isinstance(value, str):
            out.update(t for t in value.replace(";", "|").split("|") if t.startswith("ENSG"))
    return out


bound = {p: sha256(ROOT + p) for p in PINS}
assert bound == PINS, bound
unpinned = {p: sha256(ROOT + p) for p in (REGISTRY,)}
decisions = pd.read_csv(ROOT + DECISIONS, dtype=str, low_memory=False)
provenance = pd.read_csv(ROOT + PROVENANCE, dtype=str, low_memory=False)
registry = pd.read_csv(ROOT + REGISTRY, dtype=str)
z = np.load(ROOT + STATES, allow_pickle=False)
states, matrix_ids = z["states"], [str(m) for m in z["matrix_id"]]
state_names = [str(s) for s in z["state_names"]]
assert state_names == ["STRUCTURALLY_UNMEASURED", "MEASURED_SCALAR", "MEASURED_COLLISION_UNRESOLVED"]

address_index = {}
for column in ("current_ensembl_gene_id", "legacy_source_exact_id"):
    sub = registry[registry[column].notna()]
    address_index.update(dict(zip(sub[column], sub.molecular_address_index.astype(int))))
current = set(registry.loc[registry.identity_class.eq("current_exact"), "molecular_address_id"])
identity_class = dict(zip(registry.molecular_address_id, registry.identity_class))
ledger_symbols = set(registry.symbol.dropna().str.upper())
mapped_records = set(provenance.source_record_index)
decisions["mapped"] = decisions.source_record_index.isin(mapped_records)
operator_of_source_object = {m.replace("NPH52::matrix::", "NPH52::"): i for i, m in enumerate(matrix_ids)
                             if m.startswith("NPH52::")}

# 1. Feature accounting per deposited feature set, and identity of off-ledger features.
symbol_of_address = {}
for column in ("current_ensembl_gene_id", "legacy_source_exact_id"):
    sub = registry[registry[column].notna()]
    symbol_of_address.update(dict(zip(sub[column], sub.symbol.fillna("").str.upper())))
per_source, nph_reached, nph_symbol_pairs = {}, {}, set()
for source, frame in decisions.groupby("source_dataset_id", sort=True):
    off = frame[~frame.mapped]
    anchors = off.apply(lambda r: ensembl_ids(r, ENSEMBL_FIELDS), axis=1)
    reaches = anchors.apply(lambda s: bool(s & set(address_index)))
    if source.startswith("NPH52::"):
        for symbol, ids in zip(off.raw_source_feature_symbol[reaches].fillna("").str.upper(), anchors[reaches]):
            nph_symbol_pairs.add((symbol, any(symbol_of_address[g] == symbol for g in ids & set(address_index))))
    per_source[source] = {
        "features": int(len(frame)),
        "mapped_to_an_address": int(frame.mapped.sum()),
        "off_ledger": int(len(off)),
        "off_ledger_by_terminal_disposition": {k: int(v) for k, v in off.terminal_disposition.value_counts().items()},
        "off_ledger_without_any_ensembl_anchor": int(anchors.apply(len).eq(0).sum()),
        "off_ledger_whose_identity_reaches_a_ledger_address": int(reaches.sum()),
        "off_ledger_whose_symbol_equals_a_ledger_symbol": int(
            off.raw_source_feature_symbol.fillna("").str.upper().isin(ledger_symbols).sum()),
    }
    if source in operator_of_source_object:
        op = operator_of_source_object[source]
        for ids in anchors[reaches]:
            for gene in ids & set(address_index):
                state = state_names[int(states[op, address_index[gene]])]
                nph_reached.setdefault(state, set()).add((gene, matrix_ids[op]))

# 2. In-ledger alias candidates: a mapped feature whose identity also reaches another current address.
merged = provenance[["source_record_index", "molecular_address_id", "source_dataset_id"]].merge(
    decisions[["source_record_index", "terminal_disposition", "ensembl_history_replacements",
               "authority_current_ensembl_id"]], on="source_record_index", how="left")
pairs, holders = set(), {}
for r in merged.itertuples(index=False):
    others = (ensembl_ids(r._asdict(), ["authority_current_ensembl_id", "ensembl_history_replacements"]) & current) \
        - {r.molecular_address_id}
    for other in others:
        pairs.add((r.molecular_address_id, other))
    if others:  # one entry per mapped source feature, however many other addresses it reaches
        holders[r.source_record_index] = (identity_class[r.molecular_address_id], r.terminal_disposition,
                                          r.source_dataset_id.split("::")[0])
holders = list(holders.values())

# 3. Per-operator geometry: measured-scalar count, collision-blocked features, declared matrix features.
lineage = pd.concat(pd.read_csv(f, usecols=["source", "matrix_id", "donor_id", "reader_partition"], dtype=str)
                    .drop_duplicates() for f in sorted(glob.glob(
                        ROOT + "outputs/full104_v014_20260826/01_full104_metadata_adapter/FULL104_ROW_LINEAGE_SHARDS/*.csv.gz")))
assert set(lineage.reader_partition) == {"reader_fit"}
collisions = pd.read_csv(AUTH + "results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz", low_memory=False)
supplement = pd.read_csv(AUTH + "results/v4/stage81a3r_scalar_mapping_unregistered_collisions.csv")
assets = pd.read_csv(ROOT + "results/v4/stage81a2_canonical_asset_registry.csv", dtype=str).set_index("dataset_id")
semantics = pd.read_csv(ROOT + "results/v4/stage81a2_matrix_semantics_contract.csv", dtype=str).set_index("dataset_id")
per_operator = []
for op, m in enumerate(matrix_ids):
    blocked = set(collisions.loc[collisions.matrix_id.astype(str).eq(m), "source_feature_index"].astype(int))
    for value in supplement.loc[supplement.matrix_id.astype(str).eq(m), "source_feature_indices"].astype(str):
        blocked.update(map(int, value.split("|")))
    declared = None
    if not m.startswith("NPH52::") and m in assets.index:
        with h5py.File(ROOT + str(assets.loc[m, "matrix_path_or_object"]), "r") as handle:
            shape = handle[str(semantics.loc[m, "matrix_slot"])].attrs.get("shape")
            declared = None if shape is None else int(shape[1])
    per_operator.append({"operator_index": op, "matrix_id": m,
                         "measured_scalar_addresses": int((states[op] == 1).sum()),
                         "collision_unresolved_addresses": int((states[op] == 2).sum()),
                         "collision_blocked_source_features": len(blocked),
                         "declared_matrix_features": declared})

# 4. Donor versus matrix structure (counts only; no donor identifiers emitted).
donor_structure = {}
for source, frame in lineage.drop_duplicates(["source", "matrix_id", "donor_id"]).groupby("source"):
    per_donor = frame.groupby("donor_id").matrix_id.nunique()
    donor_structure[source] = {"donors": int(frame.donor_id.nunique()), "matrices": int(frame.matrix_id.nunique()),
                               "donors_in_more_than_one_matrix": int((per_donor > 1).sum()),
                               "matrices_per_donor_median": float(per_donor.median()),
                               "matrices_per_donor_max": int(per_donor.max())}

# 5. QC-entangled addresses (MT-, RPS/RPL, MALAT1, NEAT1) by state per source.
symbols = registry.symbol.fillna("").str.upper()
qc = (symbols.str.startswith("MT-") | symbols.str.match(r"^RP[SL]\d") | symbols.isin(["MALAT1", "NEAT1"])).to_numpy()
qc_states = {}
for prefix, label in (("HVS::", "HVS"), ("sea_ad_", "SEA_AD"), ("NPH52::", "NPH52")):
    rows = [i for i, m in enumerate(matrix_ids) if m.startswith(prefix)]
    qc_states[label] = {"operators": len(rows), "qc_entangled_addresses": int(qc.sum()),
                        "measured_scalar_in_every_operator": int(((states[rows] == 1).all(axis=0) & qc).sum()),
                        "collision_unresolved_in_any_operator": int(((states[rows] == 2).any(axis=0) & qc).sum()),
                        "structurally_unmeasured_in_any_operator": int(((states[rows] == 0).any(axis=0) & qc).sum()),
                        "structurally_unmeasured_symbols": sorted(set(symbols[(states[rows] == 0).any(axis=0) & qc]))}

# 6. Symbol duplication in the address namespace, and presence of abundant transcripts per feature set.
duplicated = registry[registry.symbol.notna()].groupby("symbol").molecular_address_id.nunique()
ABUNDANT = ["RPL13", "RPS18", "RPL10", "RPS12", "RPL23", "ACTB", "MALAT1"]
present = {source: sorted(set(frame.raw_source_feature_symbol.fillna("").str.upper()) & set(ABUNDANT))
           for source, frame in decisions.groupby("source_dataset_id", sort=True)}
nph_distinct_symbols = {s for s, _ in nph_symbol_pairs}
nph_exact_symbols = {s for s, exact in nph_symbol_pairs if exact}

print(json.dumps({
    "schema": "JEPA_MACHA_R1_R2_SOURCE_GAP_PROBE_V1",
    "duplicated_symbols_in_address_namespace": {"symbols": int((duplicated > 1).sum()),
                                                "addresses": int(duplicated[duplicated > 1].sum())},
    "abundant_transcripts_present_by_feature_set": {"checked": ABUNDANT, "present": present},
    "nph52_reaching_off_ledger_symbols": {"distinct": len(nph_distinct_symbols),
                                          "equal_to_reached_address_symbol": len(nph_exact_symbols)},
    "bound_inputs_sha256": bound, "unpinned_inputs_sha256": unpinned,
    "per_source_feature_accounting": per_source,
    "nph52_off_ledger_identity_reaching_ledger_addresses": {
        "distinct_addresses": len({g for v in nph_reached.values() for g, _ in v}),
        "address_operator_pairs_by_state_in_that_operator": {k: len(v) for k, v in sorted(nph_reached.items())},
        "distinct_addresses_by_state": {k: len({g for g, _ in v}) for k, v in sorted(nph_reached.items())},
        "structurally_unmeasured_pairs": sorted([list(p) for p in nph_reached.get("STRUCTURALLY_UNMEASURED", ())]),
    },
    "in_ledger_alias_candidates": {
        "mapped_features": len(holders),
        "holder_identity_class": pd.Series([h[0] for h in holders]).value_counts().to_dict(),
        "terminal_disposition": pd.Series([h[1] for h in holders]).value_counts().to_dict(),
        "by_source": pd.Series([h[2] for h in holders]).value_counts().to_dict(),
        "address_pairs": sorted([list(p) for p in pairs]),
        "distinct_current_addresses_at_risk": len({b for _, b in pairs}),
    },
    "per_operator": per_operator,
    "donor_versus_matrix_reader_fit": donor_structure,
    "qc_entangled_addresses_by_source": qc_states,
}, indent=1, sort_keys=True, default=int))
