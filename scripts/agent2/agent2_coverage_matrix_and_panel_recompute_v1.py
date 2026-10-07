#!/usr/bin/env python
"""AGENT 2 - coverage matrix and query-panel recompute.

Reads the one-row-per-address crosswalk and emits:

  agent2_coverage_matrix_v1.csv
      Machine-readable state x stratum counts. Strata: ALL (genome-wide),
      MICROGLIA_DETECTABLE, STAGE75F_REGULATOR, STAGE75F_TARGET, QUERY_PANEL.

  agent2_query_panel_coverage_v1.csv
      One row per panel gene with its observation states.

Because the crosswalk is one row per canonical address, coverage for ANY new
target panel is recomputed by re-running this script with --panel pointing at
the new gene list. No re-derivation of the crosswalk is required.

A panel gene that does not resolve to a canonical address is reported as
ABSENT_FROM_CANONICAL_REGISTRY. It is never silently dropped and never counted
as covered.

Governance: TRAINING=OFF | AUDIT_B_N1=UNOPENED |
PROTECTED_FULL104_OUTCOMES=UNOPENED | D_SHARED_G5=UNOPENED |
RARE_TAIL_MOLECULAR=UNOPENED | THERAPEUTIC_RANKING=OFF
"""
import argparse
import collections
import csv
import hashlib
import json
import os
from datetime import datetime, timezone

STATE_COLUMNS = [
    "rna_state",
    "rna_microglia_state",
    "annotation_regulatory_state",
    "atac_accessibility_state",
    "atac_microglia_accessibility_state",
    "regulatory_evidence_state",
    "matched_rna_atac_state",
]

ABSENT = "ABSENT_FROM_CANONICAL_REGISTRY"


def sha256_of(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def receipt(path):
    return {"path": os.path.abspath(path).replace("\\", "/"),
            "bytes": os.path.getsize(path), "sha256": sha256_of(path)}


def norm(s):
    return (s or "").strip().upper()


def load_panel(path, field="gene"):
    out = []
    groups = {}
    with open(path, newline="", encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        f = field if field in (rd.fieldnames or []) else rd.fieldnames[0]
        for row in rd:
            g = norm(row.get(f))
            if g:
                out.append(g)
                groups[g] = row.get("audit_groups", "")
    return out, groups


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crosswalk", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--panel", default=None)
    ap.add_argument("--panel-field", default="gene")
    ap.add_argument("--panel-name", default="QUERY_PANEL")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)

    rows = []
    with open(a.crosswalk, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append(r)
    n_total = len(rows)

    by_symbol = collections.defaultdict(list)
    for r in rows:
        by_symbol[norm(r["symbol"])].append(r)

    panel_syms, panel_groups = ([], {})
    if a.panel and os.path.exists(a.panel):
        panel_syms, panel_groups = load_panel(a.panel, a.panel_field)
    panel_set = set(panel_syms)

    strata = {
        "ALL": rows,
        "MICROGLIA_DETECTABLE": [r for r in rows
                                 if r["rna_microglia_state"]
                                 == "MEASURED_DETECTED"],
        "STAGE75F_REGULATOR": [r for r in rows
                               if r["stage75f_role"] in
                               ("REGULATOR", "REGULATOR_AND_TARGET")],
        "STAGE75F_TARGET": [r for r in rows
                            if r["stage75f_role"] in
                            ("TARGET", "REGULATOR_AND_TARGET")],
        a.panel_name: [r for r in rows if norm(r["symbol"]) in panel_set],
    }

    mat = os.path.join(a.out_dir, "agent2_coverage_matrix_v1.csv")
    with open(mat, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["stratum", "stratum_n_addresses", "state_column", "state",
                    "n_addresses", "fraction_of_stratum"])
        for sname, srows in strata.items():
            n = len(srows)
            for col in STATE_COLUMNS:
                ctr = collections.Counter(r[col] for r in srows)
                tot = sum(ctr.values())
                if tot != n:
                    raise SystemExit(
                        "FAIL-CLOSED: %s/%s states sum to %d, not %d"
                        % (sname, col, tot, n))
                for st in sorted(ctr, key=lambda x: (-ctr[x], x)):
                    w.writerow([sname, n, col, st, ctr[st],
                                ("%.6f" % (ctr[st] / n)) if n else ""])

    # Per-panel-gene coverage, including genes with no canonical address.
    pan = os.path.join(a.out_dir, "agent2_query_panel_coverage_v1.csv")
    n_absent = 0
    absent_syms = []
    n_multi = 0
    with open(pan, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["panel_gene", "panel_groups", "n_canonical_addresses",
                    "molecular_address_index", "molecular_address_id"]
                   + STATE_COLUMNS)
        for g in sorted(panel_set):
            hits = by_symbol.get(g, [])
            if not hits:
                n_absent += 1
                absent_syms.append(g)
                w.writerow([g, panel_groups.get(g, ""), 0, "", ""]
                           + [ABSENT] * len(STATE_COLUMNS))
                continue
            if len(hits) > 1:
                n_multi += 1
            for r in hits:
                w.writerow([g, panel_groups.get(g, ""), len(hits),
                            r["molecular_address_index"],
                            r["molecular_address_id"]]
                           + [r[c] for c in STATE_COLUMNS])

    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "crosswalk": receipt(a.crosswalk),
        "n_canonical_addresses": n_total,
        "strata_sizes": {k: len(v) for k, v in strata.items()},
        "panel_name": a.panel_name,
        "panel_genes_declared": len(panel_syms),
        "panel_genes_unique": len(panel_set),
        "panel_genes_absent_from_registry": n_absent,
        "panel_absent_symbols": absent_syms,
        "panel_genes_multi_address": n_multi,
        "outputs": {os.path.basename(mat): receipt(mat),
                    os.path.basename(pan): receipt(pan)},
        "governance": ("TRAINING=OFF | AUDIT_B_N1=UNOPENED | "
                       "PROTECTED_FULL104_OUTCOMES=UNOPENED | "
                       "D_SHARED_G5=UNOPENED | RARE_TAIL_MOLECULAR=UNOPENED | "
                       "THERAPEUTIC_RANKING=OFF"),
    }
    sp = os.path.join(a.out_dir, "agent2_coverage_matrix_summary_v1.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
