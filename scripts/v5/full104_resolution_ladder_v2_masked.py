#!/usr/bin/env python3
"""The resolution ladder v2: acts on the availability mask, does not trust it.

WHAT CHANGED FROM v1

  v1 read a counts array in which a gene the source never measured was written
  as 0, indistinguishable from a measured zero. It happened not to be misled -
  every query and panel address is available in every matrix - but "happened
  not to be misled" is not a property you can rely on, and the same code
  pointed at a cohort missing a panel gene would have produced a number rather
  than a refusal.

  v2 requires `address_available` in the input and REFUSES an artifact without
  it, because an artifact predating the mask cannot distinguish the two cases
  at all. For every cohort and program it then checks that all four partner
  addresses are available for EVERY nucleus it is about to use, and marks the
  program VOID rather than computing on placeholder zeros.

  The housekeeping-reference diagnostic is also fixed. v1 summed all eight
  genes, counting an unmeasured PGK1 as zero for all eleven SEA-AD matrices -
  170,528 of 187,909 nuclei - and so understated that reference. v2 sums only
  the available ones and reports how many there were.

The resolution ladder: single nuclei -> within-donor aggregates.

THE POINT OF THE LADDER IS TO SEPARATE TWO ESTIMANDS THAT LOOK ALIKE

  A per-nucleus target asks: what is the state of THIS nucleus?
  A neighbourhood target asks: what is the state of this donor's myeloid
  population, estimated from k nuclei?

  They are not the same quantity and a reliability number quoted for one is
  not evidence for the other. Worse, the SIGN of the interpretation flips
  between them. Disagreement between two disjoint sets of nuclei from one donor
  is measurement noise for the neighbourhood target, and is the signal itself
  for the per-nucleus target.

TWO DESIGNS, RUN AT EVERY RUNG, AND THE GAP BETWEEN THEM IS THE ANSWER

  MOLECULE SPLIT at rung k
      take 2k nuclei from one donor, pool them, then split the POOLED
      MOLECULES by a fair coin. Each half has the expected depth of k nuclei.
      Because the nuclei are held fixed, this varies only molecule sampling.
      It is the ceiling: no estimator can do better than this at this depth.
      This is R8's design, lifted to depth k.

  DISJOINT NUCLEI at rung k
      take 2k nuclei from one donor and split them into two disjoint sets of k.
      Each set has the expected depth of k nuclei, the SAME as above. But the
      two sets contain different cells, so this varies molecule sampling AND
      nucleus-to-nucleus heterogeneity within the donor.

  Matched depth is what makes the comparison mean anything, and it is why both
  designs start from 2k nuclei rather than k.

      disjoint(k) / molecule(k)  ~ 1   the nuclei within a donor are
                                       interchangeable at this resolution;
                                       there is no per-nucleus state to learn,
                                       only a donor-level one.
      disjoint(k) / molecule(k)  << 1  nuclei within a donor genuinely differ.
                                       That difference is what a per-nucleus
                                       teacher target would have to predict.

  Neither design is independent biological replication. Two disjoint sets of
  nuclei from one donor still share the donor, the dissection, the library prep
  and the sequencing run. The ladder bounds what one donor-level experiment can
  say; it cannot exceed it.

CONTROLS THAT CAN FAIL

  DONOR SCRAMBLE   rebuild the disjoint-nuclei design after permuting nuclei
                   across donors within a source. The pairing then shares no
                   donor, so its correlation must COLLAPSE. If it does not, the
                   ladder is not measuring anything donor-specific and every
                   number here is void.

  SOURCES APART    every source and label is computed on its own. No rung is
                   ever pooled across sources.

REFERENCE DENOMINATOR

  R8's headline activity used the full observed count excluding the 29 program
  and housekeeping addresses, not the eight housekeeping genes. That choice is
  kept, and for good reason: in the FULL104 myeloid nuclei those eight genes
  sum to ZERO in 15-27% of nuclei, because ribosomal and translation-factor
  mRNAs are cytoplasmic and depleted in single nuclei. A denominator that
  vanishes in a quarter of cells is not a size factor. Both are computed and
  reported so the choice is visible rather than assumed.

Randomness is seeded from scientific identity - donor, program, rung - never
from storage order.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys


import numpy as np

R8_ADDR = {
    "APOE_LIPID": {"query": 6186, "panel": [6188, 11425, 7194, 2044]},
    "P2RY12_HOMEOSTATIC": {"query": 12469, "panel": [15109, 12239, 12995, 13365]},
    "HLA_DRA_ANTIGEN": {"query": 18511, "panel": [392, 23673, 18500, 20496]},
}
HOUSE_ADDR = [1817, 9924, 2628, 11587, 16586, 8192, 12595, 1225]
LADDER_K = (1, 2, 5, 10, 25, 50, 100)
MIN_PAIRS = 12          # below this a correlation is not worth reporting
MYELOID_PREFIX = "Micro-PVM"


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def seed_for(donor: str, program: str, k: int, arm: str) -> int:
    """Deterministic, from scientific identity - not from row or block order."""
    s = f"{donor}|{program}|k={k}|{arm}".encode()
    return int.from_bytes(hashlib.sha256(s).digest()[:8], "big") % (2 ** 63)


def activity(part, ref):
    ref = np.maximum(ref, 1)
    return np.log1p(10000.0 * part / ref)


def paired_corr(xa, xb):
    if xa.size < MIN_PAIRS:
        return None, int(xa.size)
    if xa.std() == 0 or xb.std() == 0:
        return None, int(xa.size)
    return float(np.corrcoef(xa, xb)[0, 1]), int(xa.size)


def build_rung(part, ref, donors, k, program, scramble_rng=None):
    """Return (molecule-split pairs, disjoint-nuclei pairs) at rung k.

    Pairs are pooled across donors, and a donor with many nuclei contributes
    many pairs. Those pairs are NOT independent: they share the donor, so
    between-donor variance enters the pooled correlation repeatedly. That is
    the right behaviour for the quantity being estimated - how well a k-nucleus
    aggregate recovers a donor's level - but it means n_pairs is a count of
    comparisons, not an independent sample size. The independent unit is the
    donor-by-operator stratum, which is reported alongside as
    n_strata_contributing. No p-value is computed here, and none should be
    computed from n_pairs.
    """
    ma, mb, da, db = [], [], [], []
    strata_used = set()
    don = np.asarray(donors)
    if scramble_rng is not None:
        # permute the donor labels, keeping group sizes identical. This breaks
        # the donor link without changing anything else about the design.
        don = don[scramble_rng.permutation(don.size)]
    for d in np.unique(don):
        idx = np.flatnonzero(don == d)
        if idx.size < 2 * k:
            continue
        strata_used.add(str(d))
        rng = np.random.default_rng(seed_for(str(d), program, k, "shuffle"))
        idx = idx[rng.permutation(idx.size)]
        n_groups = idx.size // k
        n_pairs = n_groups // 2
        for g in range(n_pairs):
            ga = idx[(2 * g) * k:(2 * g + 1) * k]
            gb = idx[(2 * g + 1) * k:(2 * g + 2) * k]
            # ---- disjoint nuclei: two different sets of cells
            da.append(activity(part[ga].sum(), ref[ga].sum()))
            db.append(activity(part[gb].sum(), ref[gb].sum()))
            # ---- molecule split: ONE pooled set of the same 2k nuclei,
            #      molecules divided by a fair coin. Same expected depth.
            both = np.concatenate([ga, gb])
            p_tot = int(part[both].sum()); r_tot = int(ref[both].sum())
            srng = np.random.default_rng(
                seed_for(f"{d}|{g}", program, k, "molsplit"))
            pa = int(srng.binomial(p_tot, 0.5)); pb = p_tot - pa
            ra = int(srng.binomial(r_tot, 0.5)); rb = r_tot - ra
            ma.append(activity(pa, max(ra, 1)))
            mb.append(activity(pb, max(rb, 1)))
    return ((np.asarray(ma), np.asarray(mb)), (np.asarray(da), np.asarray(db)),
            len(strata_used))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--counts-npz", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    z = np.load(a.counts_npz, allow_pickle=True)
    if "address_available" not in z.files:
        raise SystemExit(
            "REFUSED_NO_AVAILABILITY_MASK: this artifact writes unmeasured "
            "addresses as zeros indistinguishable from measured zeros. Re-extract "
            "with full104_myeloid_panel_extraction_v3_masked.py.")
    avail = z["address_available"].astype(bool)
    addr = z["address_columns"]
    col = {int(x): i for i, x in enumerate(addr)}
    cnt = z["counts"]
    source = z["source"].astype(str)
    native = z["native_class"].astype(str)
    supert = z["supertype"].astype(str)
    donor = z["donor_id"].astype(str)
    oper = z["operator_index"]
    ref_full = z["total_excluding_29"].astype(np.int64)
    house_idx = [col[h] for h in HOUSE_ADDR]
    house_avail = avail[:, house_idx]
    # an unmeasured housekeeping gene is not a zero; sum only what was measured
    ref_house = (cnt[:, house_idx] * house_avail).sum(1).astype(np.int64)
    house_n_avail = house_avail.sum(1)

    # Cohorts, kept strictly apart. SEA_AD 'Immune' appears twice: as the raw
    # class-level label, and as the myeloid-restricted subset defined by the
    # consortium's own supertype. They are different populations and are never
    # merged.
    cohorts = {}
    for s, nc in sorted(set(zip(source, native))):
        m = (source == s) & (native == nc)
        cohorts[f"{s}::{nc}"] = m
        if s == "SEA_AD" and nc == "Immune":
            cohorts[f"{s}::{nc}::MYELOID_RESTRICTED"] = m & np.char.startswith(
                supert, MYELOID_PREFIX)

    out = {}
    for cname, mask in cohorts.items():
        d_c = donor[mask]
        op_c = oper[mask]
        rf = ref_full[mask]; rh = ref_house[mask]
        # a donor is stratified by operator: for SEA-AD one donor spans ten
        # brain regions, and pooling nuclei across regions would aggregate
        # across anatomy, not within a neighbourhood.
        strat = np.asarray([f"{d}|op{o}" for d, o in zip(d_c, op_c)])
        entry = {"n_nuclei": int(mask.sum()),
                 "n_donors": int(np.unique(d_c).size),
                 "n_donor_by_operator_strata": int(np.unique(strat).size),
                 "reference_house_zero_fraction": float(np.mean(rh == 0)),
                 "reference_house_genes_available_median":
                     float(np.median(house_n_avail[mask])),
                 "reference_house_genes_declared": len(HOUSE_ADDR),
                 "reference_full_median": float(np.median(rf)),
                 "reference_is_source_specific": True,
                 "programs": {}}
        for prog, g in R8_ADDR.items():
            pidx = [col[x] for x in g["panel"]]
            pav = avail[mask][:, pidx]
            if not pav.all():
                missing = [int(g["panel"][k]) for k in range(len(pidx))
                           if not pav[:, k].all()]
                entry["programs"][prog] = {
                    "status": "VOID_PANEL_ADDRESSES_UNAVAILABLE",
                    "unavailable_addresses": missing,
                    "why": ("R8's contract requires exactly four partners and "
                            "raises on any other length, so a panel missing one "
                            "is a different target, not a weaker one"),
                }
                continue
            part = cnt[mask][:, pidx].sum(1).astype(np.int64)
            pe = {"partner_umi_median": float(np.median(part)),
                  "partner_umi_zero_fraction": float(np.mean(part == 0)),
                  "rungs": {}}
            scr_rng = np.random.default_rng(
                seed_for(cname, prog, 0, "donor_scramble"))
            for k in LADDER_K:
                (ma, mb), (da, db), n_strata = build_rung(part, rf, strat, k, prog)
                mc, mn = paired_corr(ma, mb)
                dc, dn = paired_corr(da, db)
                _, (sa, sb), _ = build_rung(part, rf, strat, k, prog,
                                            scramble_rng=scr_rng)
                sc, sn = paired_corr(sa, sb)
                ratio = (dc / mc) if (mc not in (None, 0.0) and dc is not None
                                      and mc > 0) else None
                pe["rungs"][str(k)] = {
                    "n_pairs": dn,
                    "n_strata_contributing": n_strata,
                    "n_pairs_is_not_an_independent_sample_size": True,
                    "molecule_split_corr": mc,
                    "disjoint_nuclei_corr": dc,
                    "donor_scrambled_corr": sc,
                    "disjoint_over_molecule": ratio,
                    "reportable": bool(dn >= MIN_PAIRS and mc is not None
                                       and dc is not None),
                }
            # the scramble control must collapse, else the ladder is void here
            usable = [r for r in pe["rungs"].values() if r["reportable"]
                      and r["donor_scrambled_corr"] is not None]
            if usable:
                worst = max(abs(r["donor_scrambled_corr"]) for r in usable)
                best_real = max(r["disjoint_nuclei_corr"] for r in usable)
                pe["donor_scramble_control"] = {
                    "max_abs_scrambled_corr": worst,
                    "max_disjoint_corr": best_real,
                    "control_collapsed": bool(worst < 0.5 * max(best_real, 1e-9)),
                    "if_not_collapsed": ("the design reproduces itself without a "
                                         "shared donor, so it is not measuring a "
                                         "donor-anchored quantity and the rungs "
                                         "for this program are VOID"),
                }
            entry["programs"][prog] = pe
        out[cname] = entry

    receipt = {
        "schema": "V5_FULL104_RESOLUTION_LADDER_V1",
        "status": "MEASUREMENT_ONLY__NO_TEACHER_FITTED__NO_TRAINING",
        "counts_npz_sha256": sha_file(a.counts_npz),
        "rungs": list(LADDER_K),
        "min_pairs_to_report": MIN_PAIRS,
        "estimand_separation": {
            "k=1": "the per-nucleus objective, preserved as the reference rung",
            "k>1": "a SEPARATELY LABELLED neighbourhood-level target",
            "molecule_split": "ceiling at matched depth; nuclei held fixed",
            "disjoint_nuclei": "adds within-donor nucleus heterogeneity",
            "ratio": "fraction of the achievable reliability that survives "
                     "swapping which nuclei you drew",
        },
        "stratification": "donor x operator, because one SEA-AD donor spans ten "
                          "brain regions and pooling across them is anatomy, not "
                          "a neighbourhood",
        "sources_not_harmonized": True,
        "availability_mask_required_and_enforced": True,
        "reference_caveat": (
            "total_excluding_29 subtracts only the ban-set addresses each "
            "matrix actually measures, so the subtracted set differs between "
            "sources. It is a SOURCE-SPECIFIC reference: usable within a "
            "source, and requiring an explicit comparability check before any "
            "cross-source transport claim."),
        "reserved_readouts_untouched": True,
        "training_authorized": False,
        "protected_outcomes_opened": False,
        "cohorts": out,
    }
    receipt["producer_sha256"] = sha_file(os.path.abspath(__file__))
    p = os.path.join(a.out_dir, "FULL104_RESOLUTION_LADDER_V1.json")
    with open(p, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print("Resolution ladder - sources NOT harmonized\n")
    for cname, e in out.items():
        print(f"  {cname}   n={e['n_nuclei']:,}  donors={e['n_donors']}  "
              f"strata={e['n_donor_by_operator_strata']}  "
              f"8-gene-ref zero in {100*e['reference_house_zero_fraction']:.1f}% "
              f"(median full ref {e['reference_full_median']:.0f})")
        for prog, pe in e["programs"].items():
            ctl = pe.get("donor_scramble_control", {})
            flag = "" if ctl.get("control_collapsed", True) else "   <-- CONTROL FAILED, VOID"
            print(f"      {prog:20s} partner median {pe['partner_umi_median']:5.1f} "
                  f"zero {100*pe['partner_umi_zero_fraction']:5.1f}%{flag}")
            hdr = "         k:"
            rows = {"molecule": "         mol:", "disjoint": "         dis:",
                    "scram": "         scr:", "ratio": "         d/m:"}
            for k in LADDER_K:
                r = pe["rungs"][str(k)]
                hdr += f"{k:>8d}"
                rows["molecule"] += (f"{r['molecule_split_corr']:>8.3f}"
                                     if r["molecule_split_corr"] is not None else "       -")
                rows["disjoint"] += (f"{r['disjoint_nuclei_corr']:>8.3f}"
                                     if r["disjoint_nuclei_corr"] is not None else "       -")
                rows["scram"] += (f"{r['donor_scrambled_corr']:>8.3f}"
                                  if r["donor_scrambled_corr"] is not None else "       -")
                rows["ratio"] += (f"{r['disjoint_over_molecule']:>8.3f}"
                                  if r["disjoint_over_molecule"] is not None else "       -")
            print(hdr)
            for v in rows.values():
                print(v)
        print()
    print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
