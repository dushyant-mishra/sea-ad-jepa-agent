#!/usr/bin/env python3
"""FULL104 microglial eligibility census - per source, NOT harmonized.

WHY THIS EXISTS

  Four native-class labels in the FULL104 reader-fit partition look microglial:

      HVS    'Microglia-PVM'          2,117 cells
      NPH52  'MG'                    15,264 cells
      SEA_AD 'Immune'               138,242 cells   (10 cortical/HIP matrices)
      SEA_AD 'Microglia-PVMSubclass'  32,286 cells   (caudate matrix only)

  They are NOT the same population and must not be summed. Specifically:

    * SEA_AD 'Immune' is a CLASS-level label. In the SEA-AD taxonomy the
      Immune subclass contains Micro-PVM supertypes AND Lymphocyte AND
      Monocyte. Treating it as microglia silently admits lymphocytes.
    * The caudate matrix uses a DIFFERENT label column: every one of its 17
      labels carries a 'Subclass' suffix and its broad_class column is a COPY
      of the subclass label rather than a broad class. It is also striatum,
      not cortex.
    * HVS 'Microglia-PVM' and SEA_AD 'Microglia-PVM*' pool microglia with
      perivascular macrophages. PVM is a distinct, non-parenchymal myeloid
      population; it is not microglia.
    * NPH52 'MG' has NO broad_class at all (missing for all 236,476 reader-fit
      cells) and no cross-reference to either other vocabulary.

  So this script produces a census that keeps every source in its own
  vocabulary and refuses to emit a single pooled 'microglia' number.

THE ONE RESOLUTION THAT IS NOT MINE TO INVENT

  SEA-AD publishes its own 10-region immune object
  (SEAAD_Immune_10-region_RNAseq_final-nuclei), in which the same nuclei -
  joined by exact experiment-component barcode - carry a Supertype label that
  separates Micro-PVM from Lymphocyte and Monocyte. Using the consortium's own
  supertype assignment is a lookup, not a harmonization: no label of mine is
  mapped onto another source's label.

  That still leaves microglia pooled with perivascular macrophages. This script
  says so and does not pretend otherwise.

PROTECTED-OUTCOME DISCIPLINE

  The immune object carries donor pathology columns (Braak, CERAD, Thal,
  'Overall AD neuropathological Change', 'Cognitive Status', LATE, ...). Under
  the standing governance PROTECTED_FULL104_OUTCOMES=UNOPENED those columns are
  NOT read. The script reads a fixed whitelist and asserts that the whitelist
  and the protected list are disjoint before opening the file.

NOTHING IS TRAINED AND NO EXPRESSION IS OPENED. This is a metadata census.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from collections import defaultdict

import numpy as np

# ---------------------------------------------------------------- constants

FIT_PARTITION = "reader_fit"  # this partition IS the FULL104 corpus

# The four candidate labels, each pinned to the source whose vocabulary it
# belongs to. A (source, native_class) pair - never a bare label.
CANDIDATE_LABELS = (
    ("HVS", "Microglia-PVM"),
    ("NPH52", "MG"),
    ("SEA_AD", "Immune"),
    ("SEA_AD", "Microglia-PVMSubclass"),
)

# Consortium supertypes that are myeloid-parenchymal-or-perivascular. Anything
# not on this list is excluded, including anything NEW that appears in a future
# release: the check is allow-list, not deny-list, so an unrecognised supertype
# fails closed rather than being admitted by default.
MYELOID_SUPERTYPE_PREFIX = "Micro-PVM"
KNOWN_NON_MYELOID_SUPERTYPES = ("Lymphocyte", "Monocyte")

# PROSPECTIVE THRESHOLD, declared before the join is executed.
#
# Honest disclosure: the object-level supertype marginals over all 240,651
# nuclei were inspected before this floor was written (Micro-PVM 98.07%,
# Lymphocyte 1.91%, Monocyte 0.02%). What was NOT inspected, and what this
# floor governs, is the coverage of the join restricted to the 138,242 FULL104
# reader-fit SEA_AD 'Immune' cells.
#
# Rationale for 0.95: an unresolved remainder is not missing-at-random. If a
# whole region or donor failed to join, the surviving set would be a silent
# subset of unknown composition while still looking like "the microglia". Five
# percent is roughly one of the ten regions; below that a single missing region
# cannot hide.
JOIN_COVERAGE_FLOOR = 0.95

# obs columns this script is permitted to read.
OBS_WHITELIST = ("Supertype", "Subclass", "Class", "Brain Region", "Donor ID")

# obs columns that are protected donor outcomes and must never be read here.
OBS_PROTECTED = (
    "Braak", "CERAD score", "Thal", "Overall AD neuropathological Change",
    "Cognitive Status", "LATE", "Highest Lewy Body Disease", "Overall CAA Score",
    "Arteriolosclerosis", "Atherosclerosis", "Last CASI Score", "Last MMSE Score",
    "Last MOCA Score", "Total Microinfarcts (not observed grossly)",
    "Total microinfarcts in screening sections",
)

# Metacell sizes for the resolution ladder. k=1 is the per-nucleus objective,
# kept as the reference rung and never replaced.
LADDER_K = (1, 5, 10, 25, 50, 100)


def sha_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------ census, step 1

def census_per_source(db_path: str) -> dict:
    """Per source x matrix x native_class x donor counts. No pooling."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        where = " or ".join(
            f"(source='{s}' and native_class='{n}')" for s, n in CANDIDATE_LABELS)
        rows = con.execute(
            f"select source, matrix_id, native_class, donor_id, count(*) "
            f"from cells where partition='{FIT_PARTITION}' and ({where}) "
            f"group by 1,2,3,4").fetchall()
        # denominators: total FULL104 cells and donors per source
        totals = dict()
        for s, n, d in con.execute(
                f"select source, count(*), count(distinct donor_id) from cells "
                f"where partition='{FIT_PARTITION}' group by 1"):
            totals[s] = {"source_cells": n, "source_donors": d}
    finally:
        con.close()

    out = defaultdict(lambda: {"matrices": defaultdict(int), "donors": {}})
    for s, m, nc, don, n in rows:
        e = out[(s, nc)]
        e["matrices"][m] += n
        e["donors"][don] = e["donors"].get(don, 0) + n

    blocks = []
    for (s, nc), e in sorted(out.items()):
        counts = sorted(e["donors"].values())
        blocks.append({
            "source": s,
            "native_class": nc,
            "vocabulary_owner": s,   # the label means what THIS source means by it
            "matrices": dict(sorted(e["matrices"].items())),
            "n_matrices": len(e["matrices"]),
            "cells": int(sum(counts)),
            "donors": len(counts),
            "source_total_cells": totals[s]["source_cells"],
            "source_total_donors": totals[s]["source_donors"],
            "cells_per_donor": {
                "min": int(counts[0]), "max": int(counts[-1]),
                "median": float(np.median(counts)),
                "q25": float(np.percentile(counts, 25)),
                "q75": float(np.percentile(counts, 75)),
            },
            "per_donor_counts": {k: int(v) for k, v in sorted(e["donors"].items())},
        })
    return {"blocks": blocks}


# --------------------------------------------- step 2: consortium supertypes

def _read_cat(obs, name):
    g = obs[name]
    import h5py
    if isinstance(g, h5py.Group) and "categories" in g:
        cats = [x.decode() if isinstance(x, bytes) else str(x)
                for x in g["categories"][:]]
        return np.asarray(cats, dtype=object), g["codes"][:]
    vals = g[:]
    if vals.dtype.kind == "S":
        vals = np.asarray([v.decode() for v in vals], dtype=object)
    cats, codes = np.unique(vals, return_inverse=True)
    return cats, codes


def resolve_seaad_immune(h5_path: str, db_path: str) -> dict:
    """Resolve SEA_AD 'Immune' to consortium Supertype by exact barcode join."""
    import h5py

    overlap = set(OBS_WHITELIST) & set(OBS_PROTECTED)
    if overlap:
        raise SystemExit(f"REFUSED: whitelist touches protected columns {overlap}")

    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        fit = con.execute(
            f"select cell_id, donor_id, matrix_id from cells "
            f"where partition='{FIT_PARTITION}' and source='SEA_AD' "
            f"and native_class='Immune'").fetchall()
    finally:
        con.close()
    fit_ids = {r[0]: (r[1], r[2]) for r in fit}
    if len(fit_ids) != len(fit):
        raise SystemExit("REFUSED: SEA_AD Immune cell_id is not unique in reader_fit")

    with h5py.File(h5_path, "r") as f:
        obs = f["obs"]
        present = set(obs.keys())
        missing = [c for c in OBS_WHITELIST if c not in present]
        if missing:
            raise SystemExit(f"REFUSED: immune object lacks columns {missing}")
        idx_name = obs.attrs["_index"]
        idx_name = idx_name.decode() if isinstance(idx_name, bytes) else str(idx_name)
        idx_cats, idx_codes = _read_cat(obs, idx_name)
        barcodes = idx_cats[idx_codes]
        st_cats, st_codes = _read_cat(obs, "Supertype")
        sc_cats, sc_codes = _read_cat(obs, "Subclass")
        rg_cats, rg_codes = _read_cat(obs, "Brain Region")
        dn_cats, dn_codes = _read_cat(obs, "Donor ID")

    # every nucleus in this object must be Subclass == Immune; otherwise the
    # object is not what its name says and the lookup is not valid.
    sc_vals = set(sc_cats[np.unique(sc_codes)])
    if sc_vals != {"Immune"}:
        raise SystemExit(f"REFUSED: immune object Subclass vocabulary is {sc_vals}")

    # allow-list: anything not Micro-PVM* and not a KNOWN non-myeloid supertype
    # is UNRECOGNISED and fails the resolution closed.
    unrecognised = [c for c in st_cats
                    if not c.startswith(MYELOID_SUPERTYPE_PREFIX)
                    and c not in KNOWN_NON_MYELOID_SUPERTYPES]
    if unrecognised:
        raise SystemExit(
            f"REFUSED: unrecognised Supertype(s) {unrecognised}; the allow-list "
            "must be extended deliberately, not bypassed")

    lut = {}
    for i, bc in enumerate(barcodes):
        lut[bc] = i

    joined = 0
    per_supertype = defaultdict(int)
    joined_by_region = defaultdict(int)
    myeloid_by_donor = defaultdict(int)
    nonmyeloid_by_donor = defaultdict(int)
    unjoined_by_matrix = defaultdict(int)
    donor_id_agreement = {"checked": 0, "agree": 0, "disagree_examples": []}

    for cid, (don, mat) in fit_ids.items():
        j = lut.get(cid)
        if j is None:
            unjoined_by_matrix[mat] += 1
            continue
        joined += 1
        st = st_cats[st_codes[j]]
        per_supertype[st] += 1
        # independent cross-check: the object's own Donor ID must agree with
        # the FULL104 donor_id. A join that lands on the wrong donor is worse
        # than no join.
        donor_id_agreement["checked"] += 1
        if str(dn_cats[dn_codes[j]]) == str(don):
            donor_id_agreement["agree"] += 1
        elif len(donor_id_agreement["disagree_examples"]) < 5:
            donor_id_agreement["disagree_examples"].append(
                {"cell_id": cid, "full104_donor": don,
                 "immune_object_donor": str(dn_cats[dn_codes[j]])})
        if st.startswith(MYELOID_SUPERTYPE_PREFIX):
            myeloid_by_donor[don] += 1
        else:
            nonmyeloid_by_donor[don] += 1
        joined_by_region[str(rg_cats[rg_codes[j]])] += 1

    n_fit = len(fit_ids)
    coverage = joined / n_fit if n_fit else 0.0
    myeloid = sum(v for k, v in per_supertype.items()
                  if k.startswith(MYELOID_SUPERTYPE_PREFIX))
    nonmyeloid = sum(v for k, v in per_supertype.items()
                     if not k.startswith(MYELOID_SUPERTYPE_PREFIX))

    verdict = "RESOLVED" if coverage >= JOIN_COVERAGE_FLOOR else "REFUSED_INCOMPLETE_JOIN"
    if donor_id_agreement["checked"] and \
            donor_id_agreement["agree"] != donor_id_agreement["checked"]:
        verdict = "REFUSED_DONOR_ID_DISAGREEMENT"

    return {
        "verdict": verdict,
        "join_key": "exact string equality on FULL104 cells.cell_id == immune "
                    "object obs index (exp_component_name)",
        "join_coverage_floor_declared_before_join": JOIN_COVERAGE_FLOOR,
        "full104_seaad_immune_cells": n_fit,
        "joined": joined,
        "join_coverage": coverage,
        "unjoined": n_fit - joined,
        "unjoined_by_matrix": dict(sorted(unjoined_by_matrix.items())),
        "joined_by_region": dict(sorted(joined_by_region.items())),
        "donor_id_cross_check": donor_id_agreement,
        "supertype_counts": dict(sorted(per_supertype.items())),
        "myeloid_micro_pvm_cells": myeloid,
        "non_myeloid_cells": nonmyeloid,
        "non_myeloid_fraction_of_joined": (nonmyeloid / joined) if joined else None,
        "myeloid_donors": len(myeloid_by_donor),
        "myeloid_per_donor": {k: int(v) for k, v in sorted(myeloid_by_donor.items())},
        "WHAT_THIS_DOES_NOT_ESTABLISH": (
            "Micro-PVM pools microglia with perivascular macrophages. Removing "
            "Lymphocyte and Monocyte makes the set myeloid-restricted; it does "
            "NOT make it microglia. No PVM/microglia separation is performed "
            "here and none is claimed."),
    }


# ----------------------------------------------------- step 3: ladder rungs

def ladder_feasibility(per_donor: dict, k_values=LADDER_K) -> dict:
    """How many within-donor aggregates of size k each source-label supports.

    The split-half requirement is the binding one: to split independent nuclei
    WITHIN a neighbourhood at resolution k you need at least 2 full aggregates
    from the same donor, i.e. n_donor >= 2*k.
    """
    counts = np.asarray(sorted(per_donor.values()), dtype=np.int64)
    out = {}
    for k in k_values:
        full = counts // k
        out[str(k)] = {
            "donors_with_ge_1_aggregate": int((full >= 1).sum()),
            "donors_with_ge_2_aggregates": int((full >= 2).sum()),
            "donors_with_ge_4_aggregates": int((full >= 4).sum()),
            "total_aggregates": int(full.sum()),
            "median_aggregates_per_donor": float(np.median(full)),
        }
    return out


# ---------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata-sqlite", required=True)
    ap.add_argument("--immune-h5ad", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--input-digests", default=None,
                    help="precomputed 'sha256  path' lines for the two inputs")
    a = ap.parse_args()

    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    digests = {}
    if a.input_digests and os.path.exists(a.input_digests):
        for line in open(a.input_digests):
            line = line.strip()
            if not line:
                continue
            sha, path = line.split(None, 1)
            digests[os.path.basename(path.strip())] = sha
    else:
        digests[os.path.basename(a.metadata_sqlite)] = sha_file(a.metadata_sqlite)
        digests[os.path.basename(a.immune_h5ad)] = sha_file(a.immune_h5ad)

    cen = census_per_source(a.metadata_sqlite)
    res = resolve_seaad_immune(a.immune_h5ad, a.metadata_sqlite)

    # attach ladder feasibility per source-label, and for the RESOLVED
    # myeloid-restricted SEA_AD set separately (it is a different population
    # from the unresolved 'Immune' label and gets its own rung table).
    for b in cen["blocks"]:
        b["ladder"] = ladder_feasibility(b["per_donor_counts"])
        b["purity_status"] = {
            ("HVS", "Microglia-PVM"): "MYELOID_POOLED_MICROGLIA_AND_PVM",
            ("NPH52", "MG"): "VOCABULARY_UNVERIFIED_NO_BROAD_CLASS",
            ("SEA_AD", "Immune"): "NOT_MYELOID_RESTRICTED__CLASS_LEVEL_LABEL",
            ("SEA_AD", "Microglia-PVMSubclass"):
                "MYELOID_POOLED_MICROGLIA_AND_PVM__STRIATUM__DIFFERENT_LABEL_COLUMN",
        }[(b["source"], b["native_class"])]

    resolved_block = None
    if res["verdict"] == "RESOLVED":
        resolved_block = {
            "source": "SEA_AD",
            "native_class": "Immune -> Supertype Micro-PVM* (consortium lookup)",
            "purity_status": "MYELOID_RESTRICTED_MICROGLIA_AND_PVM",
            "cells": res["myeloid_micro_pvm_cells"],
            "donors": res["myeloid_donors"],
            "ladder": ladder_feasibility(res["myeloid_per_donor"]),
        }

    receipt = {
        "schema": "V5_FULL104_MICROGLIAL_ELIGIBILITY_CENSUS_V1",
        "status": "METADATA_CENSUS__NO_EXPRESSION_OPENED__NO_TRAINING",
        "governance": {
            "TRAINING": "OFF",
            "PROTECTED_FULL104_OUTCOMES": "UNOPENED",
            "obs_columns_read": list(OBS_WHITELIST),
            "obs_columns_refused": list(OBS_PROTECTED),
            "whitelist_protected_disjoint": True,
        },
        "input_digests": digests,
        "full104_partition": FIT_PARTITION,
        "REFUSES_TO_EMIT_A_POOLED_MICROGLIA_COUNT": (
            "The four labels belong to three incompatible vocabularies and two "
            "label columns. A single total would be a harmonization this script "
            "is not authorised to perform and could not defend."),
        "per_source_census": cen["blocks"],
        "seaad_immune_supertype_resolution": res,
        "seaad_myeloid_restricted_block": resolved_block,
        "ladder_semantics": {
            "k=1": "the per-nucleus objective; the reference rung, never replaced",
            "k>1": "a SEPARATELY LABELLED aggregate target; a neighbourhood-level "
                   "estimand, not an individual-nucleus estimand",
            "binding_constraint": "within-donor split-half at resolution k needs "
                                  "n_donor >= 2k, hence donors_with_ge_2_aggregates",
        },
        "training_authorized": False,
        "expression_opened": False,
    }
    receipt["producer_sha256"] = sha_file(os.path.abspath(__file__))

    p = os.path.join(a.out_dir, "FULL104_MICROGLIAL_ELIGIBILITY_CENSUS_V1.json")
    with open(p, "w") as fh:
        json.dump(receipt, fh, indent=2)

    # ---- console summary
    print("FULL104 microglial eligibility census - sources NOT harmonized\n")
    for b in cen["blocks"]:
        cpd = b["cells_per_donor"]
        print(f"  {b['source']:7s} {b['native_class']:24s} "
              f"cells={b['cells']:7,d} donors={b['donors']:3d}/{b['source_total_donors']:3d} "
              f"matrices={b['n_matrices']:2d}  med/donor={cpd['median']:7.0f}")
        print(f"          status: {b['purity_status']}")
        l = b["ladder"]
        print(f"          donors supporting >=2 aggregates: "
              + "  ".join(f"k={k}:{l[k]['donors_with_ge_2_aggregates']}" for k in map(str, LADDER_K)))
    print()
    print(f"  SEA_AD 'Immune' -> consortium Supertype : {res['verdict']}")
    print(f"      join coverage {res['join_coverage']:.4f} "
          f"(floor {JOIN_COVERAGE_FLOOR} declared before the join)")
    print(f"      donor-ID cross-check  {res['donor_id_cross_check']['agree']}"
          f"/{res['donor_id_cross_check']['checked']} agree")
    for k, v in res["supertype_counts"].items():
        print(f"      {k:24s} {v:8,d}")
    print(f"      myeloid Micro-PVM* {res['myeloid_micro_pvm_cells']:,} across "
          f"{res['myeloid_donors']} donors; non-myeloid removed "
          f"{res['non_myeloid_cells']:,}")
    if resolved_block:
        l = resolved_block["ladder"]
        print("      ladder (myeloid-restricted): "
              + "  ".join(f"k={k}:{l[k]['donors_with_ge_2_aggregates']}d"
                          for k in map(str, LADDER_K)))
    print(f"\nwrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
