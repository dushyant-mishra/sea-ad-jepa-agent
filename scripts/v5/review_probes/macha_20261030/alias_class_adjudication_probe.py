"""Adjudicate the #509 in-ledger alias candidates into query-rights classes (identity only).

usage: python -I alias_class_adjudication_probe.py <repo-root> > out.json

Rule, fixed before the first run. For each legacy holder address H whose source
features have multiple current Ensembl replacements, take H's locus from the
source-feature coordinates (any source; the legacy ID names one gene model) and
each replacement's locus from the pinned Ensembl 116 GTF. Same chromosome, same
strand and >= 1 bp overlap count as locus support. Let OV be the replacements
(address or not) with locus support. For each pair (H, R), R a current address:
  - H has no coordinates          -> UNRESOLVED_NO_LEGACY_LOCUS     -> BLOCK_QUERY_OR_OPERATOR
  - R in OV and |OV| == 1         -> SHARED_FEATURE_IDENTITY        -> SHARE_RIGHTS_CLASS
  - R in OV and |OV| >  1         -> AMBIGUOUS_HISTORICAL_REPLACEMENT -> BLOCK_QUERY_OR_OPERATOR
  - R not in OV                   -> UNSUPPORTED_EQUIVALENCE        -> NO_SHARED_LOCUS_RECORDED
The constraint matters only in operators where both H and R are MEASURED_SCALAR.
HGNC previous/alias symbol agreement is reported but is not part of the rule.
"""
import gzip
import hashlib
import json
import sys

import numpy as np
import pandas as pd

ROOT = sys.argv[1].rstrip("/") + "/"
PINS = {
    "results/v4/stage81a2r_authoritative_source_mapping_decisions_candidate.csv.gz":
        "e3106248ac77f8840f5ea6035dc765d8e09feeba1f6da21c830b3945d694c773",
    "results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz":
        "df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51",
    "results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv":
        "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd",
    "exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz":
        "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537",
    "data/external/v4/gene_identity_authority/ensembl_116/Homo_sapiens.GRCh38.116.gtf.gz":
        "ed992f0eac7197d9627bda618f8f831ba355c95bd5d0796af785387d462828b6",  # pin quoted by #492
    "data/external/v4/gene_identity_authority/hgnc_2026-08/hgnc_complete_set_2026-08-07.txt":
        "faaeb6ae1e2a596be658b5f23ee44937c9c5379fa37d1f5ace54b94b16962b1c",  # pin quoted by #492
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


observed = {p: sha256(ROOT + p) for p in PINS}
mismatch = {p: v for p, v in observed.items() if v != PINS[p]}
assert not mismatch, mismatch
paths = list(PINS)
decisions = pd.read_csv(ROOT + paths[0], dtype=str, low_memory=False)
provenance = pd.read_csv(ROOT + paths[1], dtype=str, low_memory=False, usecols=["source_record_index", "molecular_address_id"])
registry = pd.read_csv(ROOT + paths[2], dtype=str)
z = np.load(ROOT + paths[3], allow_pickle=False)
states, matrix_ids = z["states"], [str(m) for m in z["matrix_id"]]
assert [str(s) for s in z["state_names"]] == ["STRUCTURALLY_UNMEASURED", "MEASURED_SCALAR", "MEASURED_COLLISION_UNRESOLVED"]
index_of = dict(zip(registry.molecular_address_id, registry.molecular_address_index.astype(int)))
symbol_of = dict(zip(registry.molecular_address_id, registry.symbol))
current = set(registry.loc[registry.identity_class.eq("current_exact"), "molecular_address_id"])

genes = {}
with gzip.open(ROOT + paths[4], "rt") as fh:
    for line in fh:
        if line.startswith("#"):
            continue
        f = line.split("\t", 9)
        if f[2] != "gene":
            continue
        attrs = dict(part.strip().split(" ", 1) for part in f[8].strip().rstrip(";").split(";") if part.strip())
        gid = attrs["gene_id"].strip('"')
        genes[gid] = {"chrom": f[0], "start": int(f[3]), "end": int(f[4]), "strand": f[6],
                      "name": attrs.get("gene_name", '""').strip('"'), "biotype": attrs.get("gene_biotype", '""').strip('"')}
hgnc = pd.read_csv(ROOT + paths[5], sep="\t", dtype=str, usecols=["symbol", "prev_symbol", "alias_symbol", "ensembl_gene_id"])
hgnc_symbols = {}
for r in hgnc.itertuples(index=False):
    if isinstance(r.ensembl_gene_id, str):
        names = {r.symbol} | set(str(r.prev_symbol).split("|")) | set(str(r.alias_symbol).split("|"))
        hgnc_symbols[r.ensembl_gene_id] = {n.upper() for n in names if n and n != "nan"}

merged = provenance.merge(decisions, on="source_record_index")
merged = merged[merged.terminal_disposition.eq("LEGACY_EXACT_ENSEMBL_MULTIPLE_CURRENT_REPLACEMENTS")]
holders = {}
for r in merged.itertuples(index=False):
    reps = [t for t in str(r.ensembl_history_replacements).replace(";", "|").split("|") if t.startswith("ENSG")]
    if not (set(reps) & current) - {r.molecular_address_id}:
        continue
    h = holders.setdefault(r.molecular_address_id, {"replacements": set(), "loci": set(), "source_symbols": set(), "sources": set()})
    h["replacements"].update(reps)
    h["source_symbols"].add(str(r.raw_source_feature_symbol).upper())
    h["sources"].add(r.source_dataset_id.split("::")[0])
    if isinstance(r.source_chromosome, str) and isinstance(r.source_start, str) and isinstance(r.source_strand, str):
        h["loci"].add((r.source_chromosome.removeprefix("chr"), int(float(r.source_start)), int(float(r.source_end)), r.source_strand))


def overlaps(locus, gene):
    chrom, start, end, strand = locus
    return chrom == gene["chrom"] and strand == gene["strand"] and start <= gene["end"] and gene["start"] <= end


pairs = []
for holder, h in sorted(holders.items()):
    supported = {rep for rep in h["replacements"] if rep in genes and any(overlaps(l, genes[rep]) for l in h["loci"])}
    for rep in sorted((h["replacements"] & current) - {holder}):
        if not h["loci"]:
            cls, action = "UNRESOLVED_NO_LEGACY_LOCUS", "BLOCK_QUERY_OR_OPERATOR"
        elif rep in supported and len(supported) == 1:
            cls, action = "SHARED_FEATURE_IDENTITY", "SHARE_RIGHTS_CLASS"
        elif rep in supported:
            cls, action = "AMBIGUOUS_HISTORICAL_REPLACEMENT", "BLOCK_QUERY_OR_OPERATOR"
        else:
            cls, action = "UNSUPPORTED_EQUIVALENCE", "NO_SHARED_LOCUS_RECORDED"
        both_measured = [matrix_ids[op] for op in range(len(matrix_ids))
                         if states[op, index_of[holder]] == 1 and states[op, index_of[rep]] == 1]
        pairs.append({
            "legacy_holder": holder, "holder_source_symbols": sorted(h["source_symbols"]), "holder_sources": sorted(h["sources"]),
            "holder_loci": sorted(h["loci"]), "all_replacements": sorted(h["replacements"]),
            "replacements_with_locus_support": sorted(supported),
            "current_address": rep, "current_symbol": symbol_of.get(rep), "current_locus": genes.get(rep),
            "hgnc_symbol_set_contains_holder_source_symbol": bool(hgnc_symbols.get(rep, set()) & h["source_symbols"]),
            "classification": cls, "proposed_action": action,
            "operators_where_both_measured_scalar": both_measured,
        })

table = {}
for p in pairs:
    t = table.setdefault(p["current_address"], {"current_symbol": p["current_symbol"], "holders": [], "actions": set(),
                                                 "operators_constrained": set()})
    t["holders"].append(p["legacy_holder"])
    t["actions"].add(p["proposed_action"])
    if p["proposed_action"] != "NO_SHARED_LOCUS_RECORDED":
        t["operators_constrained"].update(p["operators_where_both_measured_scalar"])
rights_table = []
for address, t in sorted(table.items()):
    action = ("BLOCK_QUERY_OR_OPERATOR" if "BLOCK_QUERY_OR_OPERATOR" in t["actions"]
              else "SHARE_RIGHTS_CLASS" if "SHARE_RIGHTS_CLASS" in t["actions"] else "NO_CONSTRAINT_FROM_THIS_AUDIT")
    rights_table.append({"query_address": address, "symbol": t["current_symbol"], "holders": sorted(set(t["holders"])),
                         "proposed_action": action, "operators_constrained": sorted(t["operators_constrained"]),
                         "operators_constrained_count": len(t["operators_constrained"])})

print(json.dumps({"schema": "JEPA_MACHA_ALIAS_CLASS_ADJUDICATION_V1", "bound_inputs_sha256": observed,
                  "rule": __doc__.split("Rule, fixed before the first run.")[1].strip(),
                  "pairs": pairs, "proposed_query_rights_table": rights_table,
                  "counts": {"holders": len(holders), "pairs": len(pairs),
                             "by_classification": pd.Series([p["classification"] for p in pairs]).value_counts().to_dict(),
                             "by_query_action": pd.Series([r["proposed_action"] for r in rights_table]).value_counts().to_dict()}},
                 indent=1, sort_keys=True, default=lambda o: sorted(o) if isinstance(o, set) else str(o)))
