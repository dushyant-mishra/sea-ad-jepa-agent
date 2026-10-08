#!/usr/bin/env python3
"""Are R8's exact gene panels even MEASURABLE in FULL104 microglia?

R8 measured three microglial programs on 361 nuclei drawn from TWO operators,
and the reliability gate returned INSUFFICIENTLY_MEASURED for all three. The
obvious next question is whether the same panels behave differently on the much
larger FULL104 myeloid cohort (~188k candidate nuclei across 104 donors).

Before any count is opened, one prerequisite is decidable from the authenticated
contracts alone: is each panel gene DECLARED MEASURED in the matrices that
actually contain microglia? A gene that is not in a matrix's measured address
set is not a zero - it is an absence of measurement, and averaging it with a
real zero is the mistake the whole support ledger exists to prevent.

This script answers exactly that and nothing more. No expression is opened, no
model is fitted, and no pathology column is read.

WHY IT MATTERS FOR THE LADDER

  The resolution ladder aggregates nuclei within a donor. Aggregation cannot
  repair an UNMEASURED address: summing 50 nuclei that never measured TMEM119
  yields 50 times nothing. So panel support per source is a hard gate on which
  programs can be carried up the ladder in which source - and, because the
  sources do not share a support set, possibly a different program per source.

R8 PANELS, transcribed verbatim from
  JEPA_R8_STRUCTURED_TARGET_PROBE_20260926.py lines 16-20
  sha256 d9c3cd078eab2899... (full digest recorded in the receipt)
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import sqlite3
import sys
from collections import defaultdict

# Verbatim from the R8 probe. query / four partners / two reserved readouts.
R8_PROGRAMS = {
    "APOE_LIPID": {
        "query": "APOE",
        "panel": ["APOC1", "ABCA1", "GPNMB", "TREM2"],
        "readout": ["CTSD", "LPL"],
    },
    "P2RY12_HOMEOSTATIC": {
        "query": "P2RY12",
        "panel": ["TMEM119", "CX3CR1", "GPR34", "C1QA"],
        "readout": ["SALL1", "CSF1R"],
    },
    "HLA_DRA_ANTIGEN": {
        "query": "HLA-DRA",
        "panel": ["CD74", "HLA-DPA1", "HLA-DMA", "IFI30"],
        "readout": ["HLA-DMB", "CTSS"],
    },
}

# R8's OWN frozen address choices, read from
#   JEPA_R8_STRUCTURED_TARGET_RESULTS_20260926.json -> results[program]
# Two panel symbols are AMBIGUOUS in the address namespace (HLA-DPA1 and the
# reserved readout HLA-DMB each resolve to two molecular addresses, one
# current_exact and one legacy_exact). This script will not choose between them
# on its own - choosing would silently change which molecule the target
# measures. It reports the ambiguity, and separately reports the state under
# R8's recorded resolution, which is a fact about the prior run rather than a
# judgement of mine.
R8_RECORDED_ADDRESSES = {
    "APOE_LIPID": {"query": 6186, "panel": [6188, 11425, 7194, 2044],
                   "readout": [4748, 13734]},
    "P2RY12_HOMEOSTATIC": {"query": 12469, "panel": [15109, 12239, 12995, 13365],
                           "readout": [2810, 14980]},
    "HLA_DRA_ANTIGEN": {"query": 18511, "panel": [392, 23673, 18500, 20496],
                        "readout": [26659, 10846]},
}

# The (source, native_class) pairs that carry candidate myeloid nuclei. Kept as
# pairs, never as a bare label: the same word means different things per source.
CANDIDATE_LABELS = (
    ("HVS", "Microglia-PVM"),
    ("NPH52", "MG"),
    ("SEA_AD", "Immune"),
    ("SEA_AD", "Microglia-PVMSubclass"),
)

FIT_PARTITION = "reader_fit"


def sha_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def load_symbol_addresses(namespace_csv: str) -> dict:
    """symbol -> list of molecular_address_index.

    A symbol may map to more than one address (paralogous identifiers, legacy
    identifiers resolving to the same symbol). That ambiguity is REPORTED, not
    silently resolved by taking the first hit: picking one of several addresses
    for APOE would quietly change which molecule the target measures.
    """
    wanted = set()
    for g in R8_PROGRAMS.values():
        wanted.add(g["query"])
        wanted.update(g["panel"])
        wanted.update(g["readout"])
    out = defaultdict(list)
    with open(namespace_csv, newline="") as fh:
        for row in csv.DictReader(fh):
            sym = row["symbol"]
            if sym in wanted:
                out[sym].append({
                    "address_index": int(row["molecular_address_index"]),
                    "address_id": row["molecular_address_id"],
                    "identity_class": row["identity_class"],
                    "biotype": row["biotype"],
                })
    return {k: out[k] for k in sorted(out)}, sorted(wanted)


def microglial_matrices(db_path: str) -> dict:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        where = " or ".join(
            f"(source='{s}' and native_class='{n}')" for s, n in CANDIDATE_LABELS)
        rows = con.execute(
            f"select source, native_class, matrix_id, count(*), "
            f"count(distinct donor_id) from cells "
            f"where partition='{FIT_PARTITION}' and ({where}) "
            f"group by 1,2,3 order by 1,2,3").fetchall()
    finally:
        con.close()
    out = []
    for s, nc, m, n, d in rows:
        out.append({"source": s, "native_class": nc, "matrix_id": m,
                    "cells": n, "donors": d})
    return out


def load_support(support_gz: str, addresses: set, matrices: set) -> dict:
    """(matrix_id, address_index) -> measured_address bool, for wanted rows."""
    sup = {}
    seen_matrices = set()
    with gzip.open(support_gz, "rt", newline="") as fh:
        for row in csv.DictReader(fh):
            m = row["matrix_id"]
            seen_matrices.add(m)
            if m not in matrices:
                continue
            ai = int(row["molecular_address_index"])
            if ai not in addresses:
                continue
            sup[(m, ai)] = {
                "measured": row["measured_address"].strip().lower() == "true",
                "status": row["measurement_status"],
                "zero_distinct_from_unmeasured":
                    row["measured_zero_distinct_from_unmeasured"].strip().lower() == "true",
            }
    return sup, seen_matrices


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle-root", required=True,
                    help="foundation_calibration_bundle_20260824 directory")
    ap.add_argument("--metadata-sqlite", required=True)
    ap.add_argument("--r8-probe", required=True,
                    help="JEPA_R8_STRUCTURED_TARGET_PROBE_20260926.py, digested "
                         "so the transcribed panels are attributable")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    ns = os.path.join(a.bundle_root, "contracts", "address_namespace.csv")
    sup_gz = os.path.join(a.bundle_root, "contracts",
                          "address_measurement_support.csv.gz")
    for p in (ns, sup_gz, a.metadata_sqlite, a.r8_probe):
        if not os.path.exists(p):
            raise SystemExit(f"REFUSED_MISSING_INPUT {p}")

    sym2addr, wanted = load_symbol_addresses(ns)

    absent_symbols = [s for s in wanted if s not in sym2addr]
    ambiguous = {s: v for s, v in sym2addr.items() if len(v) > 1}

    mats = microglial_matrices(a.metadata_sqlite)
    matrix_ids = {m["matrix_id"] for m in mats}
    addr_idx = {v["address_index"] for vs in sym2addr.values() for v in vs}

    sup, seen_matrices = load_support(sup_gz, addr_idx, matrix_ids)

    matrices_absent_from_support = sorted(matrix_ids - seen_matrices)

    # per matrix x program
    per = []
    for m in mats:
        mid = m["matrix_id"]
        entry = {**m, "programs": {}}
        for prog, g in R8_PROGRAMS.items():
            genes = {}
            for role, syms in (("query", [g["query"]]), ("panel", g["panel"]),
                               ("readout", g["readout"])):
                for s in syms:
                    recs = sym2addr.get(s, [])
                    if not recs:
                        genes[s] = {"role": role, "state": "SYMBOL_NOT_IN_ADDRESS_NAMESPACE"}
                        continue
                    # state is recorded PER ADDRESS, keyed by address index, so
                    # nothing depends on row order. A previous version reported
                    # states[0] for the unambiguous case, which is correct only
                    # because all states agreed there - but it made the
                    # ambiguous case unreadable.
                    by_addr = {}
                    for r in recs:
                        k = (mid, r["address_index"])
                        by_addr[r["address_index"]] = (
                            "NO_SUPPORT_ROW" if k not in sup
                            else ("MEASURED" if sup[k]["measured"]
                                  else "DECLARED_UNMEASURED"))
                    uniq = set(by_addr.values())
                    genes[s] = {
                        "role": role,
                        "state_by_address": by_addr,
                        "state": (next(iter(uniq)) if len(uniq) == 1
                                  else "AMBIGUOUS_SYMBOL_MIXED_SUPPORT"),
                    }

            # Two readings, reported side by side and never merged.
            #   symbol_only  - what a symbol lookup alone can conclude; an
            #                  ambiguous symbol is NOT resolvable here.
            #   r8_resolved  - the state at the exact addresses R8 recorded.
            rec = R8_RECORDED_ADDRESSES[prog]

            def _state_at(addr):
                k = (mid, addr)
                if k not in sup:
                    return "NO_SUPPORT_ROW"
                return "MEASURED" if sup[k]["measured"] else "DECLARED_UNMEASURED"

            r8_q = _state_at(rec["query"])
            r8_panel = [_state_at(x) for x in rec["panel"]]
            r8_read = [_state_at(x) for x in rec["readout"]]
            q_ok = genes[g["query"]]["state"] == "MEASURED"
            panel_ok = sum(1 for s in g["panel"] if genes[s]["state"] == "MEASURED")
            read_ok = sum(1 for s in g["readout"] if genes[s]["state"] == "MEASURED")
            # R8's contract requires ALL FOUR partners. Three of four is not a
            # degraded version of the target, it is a DIFFERENT target.
            entry["programs"][prog] = {
                "genes": genes,
                "symbol_only": {
                    "query_measured": q_ok,
                    "partners_measured": panel_ok,
                    "partners_required": 4,
                    "readouts_measured": read_ok,
                    "satisfiable": bool(q_ok and panel_ok == 4),
                    "blocked_by_symbol_ambiguity": sorted(
                        s for s in [g["query"]] + g["panel"]
                        if genes[s]["state"] == "AMBIGUOUS_SYMBOL_MIXED_SUPPORT"),
                },
                "r8_resolved": {
                    "addresses": rec,
                    "query_state": r8_q,
                    "panel_states": r8_panel,
                    "readout_states": r8_read,
                    "satisfiable": bool(r8_q == "MEASURED"
                                        and all(x == "MEASURED" for x in r8_panel)),
                },
                "r8_contract_satisfiable": bool(r8_q == "MEASURED"
                                                and all(x == "MEASURED"
                                                        for x in r8_panel)),
                "note_if_partial": None if all(x == "MEASURED" for x in r8_panel) else (
                    "fewer than four supported partners at R8's own addresses; "
                    "R8's construct_measured_anchor raises on any panel length "
                    "other than 4, so this is not a weakened R8 target but a "
                    "different target requiring its own prospective definition"),
            }
        per.append(entry)

    # source-level roll-up, sources kept apart
    rollup = defaultdict(lambda: defaultdict(lambda: {
        "matrices_total": 0, "cells_total": 0,
        "matrices_satisfiable_r8_resolved": 0, "cells_satisfiable_r8_resolved": 0,
        "matrices_satisfiable_symbol_only": 0, "cells_satisfiable_symbol_only": 0}))
    for e in per:
        key = (e["source"], e["native_class"])
        for prog, r in e["programs"].items():
            d = rollup[key][prog]
            d["matrices_total"] += 1
            d["cells_total"] += e["cells"]
            if r["r8_resolved"]["satisfiable"]:
                d["matrices_satisfiable_r8_resolved"] += 1
                d["cells_satisfiable_r8_resolved"] += e["cells"]
            if r["symbol_only"]["satisfiable"]:
                d["matrices_satisfiable_symbol_only"] += 1
                d["cells_satisfiable_symbol_only"] += e["cells"]

    receipt = {
        "schema": "V5_R8_PANEL_SUPPORT_IN_FULL104_MICROGLIA_V1",
        "status": "CONTRACT_ONLY__NO_EXPRESSION_OPENED__NO_TRAINING",
        "question": ("is every R8 panel gene DECLARED MEASURED in each matrix "
                     "that contains candidate myeloid nuclei?"),
        "why_it_is_not_a_zero_question": (
            "an address absent from a matrix's measured set is UNMEASURED, not "
            "zero. The support ledger exists precisely so those two are never "
            "averaged together."),
        "input_digests": {
            "address_namespace.csv": sha_file(ns),
            "address_measurement_support.csv.gz": sha_file(sup_gz),
            "foundation_metadata_rows.sqlite": sha_file(a.metadata_sqlite),
            "JEPA_R8_STRUCTURED_TARGET_PROBE_20260926.py": sha_file(a.r8_probe),
        },
        "r8_programs_transcribed": R8_PROGRAMS,
        "symbol_resolution": {
            "symbols_required": wanted,
            "symbols_absent_from_address_namespace": absent_symbols,
            "symbols_with_multiple_addresses": ambiguous,
            "ambiguity_policy": "reported, never silently resolved to the first hit",
        },
        "matrices_absent_from_support_contract": matrices_absent_from_support,
        "per_matrix": per,
        "per_source_label_rollup": {
            f"{s}::{nc}": {k: dict(v) for k, v in progs.items()}
            for (s, nc), progs in sorted(rollup.items())
        },
        "SOURCES_NOT_HARMONIZED": (
            "each (source, native_class) is reported on its own. No panel result "
            "is pooled across sources, because the labels do not denote the same "
            "population."),
        "training_authorized": False,
        "expression_opened": False,
        "protected_outcomes_opened": False,
    }
    receipt["producer_sha256"] = sha_file(os.path.abspath(__file__))

    p = os.path.join(a.out_dir, "R8_PANEL_SUPPORT_IN_FULL104_MICROGLIA_V1.json")
    with open(p, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("R8 panel measurability in FULL104 myeloid matrices "
          "(contracts only, no counts opened)\n")
    if absent_symbols:
        print(f"  symbols not in the address namespace at all: {absent_symbols}")
    if ambiguous:
        print(f"  symbols with >1 address: {sorted(ambiguous)}")
    if matrices_absent_from_support:
        print(f"  matrices with NO support rows: {matrices_absent_from_support}")
    print()
    print("  'r8-resolved' = state at the exact addresses R8 recorded.")
    print("  'symbol-only' = what a symbol lookup alone can conclude; an "
          "ambiguous symbol is unresolvable there.\n")
    for (s, nc), progs in sorted(rollup.items()):
        print(f"  {s} :: {nc}")
        for prog, d in progs.items():
            print(f"      {prog:20s} r8-resolved "
                  f"{d['matrices_satisfiable_r8_resolved']}/{d['matrices_total']} mat "
                  f"({d['cells_satisfiable_r8_resolved']:,}/{d['cells_total']:,} cells)"
                  f"   symbol-only "
                  f"{d['matrices_satisfiable_symbol_only']}/{d['matrices_total']}")
    print(f"\nwrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
