Ruling recorded and pushed. Census is at 5,500 of 8,915 blocks.

## What I've written into the record

**All six retired as strict endpoints**, with your three-tier status: CSF1R value-exposed (secondary/sensitivity only), SALL1/CTSD/CTSS/HLA-DMB computation-exposed (prespecified secondary, never "previously unseen confirmation"), LPL both.

**No replacement set**, with your reasoning preserved — because the tempting repair is the wrong one. A hold-out is worth something only because it was fixed *before* anyone saw how the analysis behaves. Six genes chosen now would be picked by people who just learned which genes were awkward, and that contamination leaves no written trace, whereas the spent set carries a full exposure history.

**The consequence stated in the same breath**, per your framing: with every internal reserved readout downgraded, this study has **no strictly independent internal confirmation left**. The ledger now says that explicitly rather than leaving a reader to infer it, and names the donor-level ATAC evaluation as where genuine confirmation now has to come from.

## Your terminology correction — accepted, and it was a real overstatement

I withdrew it rather than softening it. Thinning tests **post-capture measurement robustness** and can expose differential sensitivity to *additional* sampling loss. It cannot establish exchangeability with respect to the original hidden biochemical capture process — that ran at the bench, before any count existed, and nothing done to the counts afterwards reaches back to it. The quantity v7 actually named, partial correlation with latent capture given `log D`, is **not recovered by thinning and remains unobserved**. Section 6 is retitled to "a robustness check, NOT an identification strategy," with the correction stated inline rather than edited away.

One process note: both of those edits first went through a scripted string replace that **silently matched nothing**. I caught it by grepping for the new text instead of trusting the edit — the same silent no-op that cost a 35-minute extraction earlier in this project.

## Sequence from here

Corrected numbers land → I audit whether the revised exact Hall capacities change any **wording** in the v7 closeout, explicitly not whether they rescue the retired matching strategy → freeze the count-route closeout → conditional composition proceeds as a new developmental strategy with the differential-capture negative control mandatory from the start, since your 119/120 and 80/80 results already showed observed-depth adjustment doesn't protect it.

I'd expect the combined figures to *fall* under the per-source intersection and NPH52 pools to *rise* under the authenticated axis — offsetting effects that could move P2RY12's combined number in either direction. HLA-DRA's ceiling was already below 199 at every tier, so I don't expect that verdict to move, but I'll check rather than assume.

`TRAINING=OFF`, reserved outcomes closed.

Census done. Verifying the firewall actually worked, then the audit.

**Bash&#xA0;**&#x56;erify firewall and NPH52 axis in new census

IN

```
cd /d/jepa_v5_wt_20260925
PY=/c/Users/dushy/anaconda3/envs/sea-ad-jepa-v3/python.exe
"$PY" - <<'PY'
import numpy as np, json
z=np.load("D:/jepa_v5_outputs_20260925/pool_census_v3/FULL104_CANDIDATE_POOL_CENSUS_V1.npz",allow_pickle=True)
r=json.load(open("D:/jepa_v5_outputs_20260925/pool_census_v3/FULL104_CANDIDATE_POOL_CENSUS_V1.json"))
RES=[2810,4748,10846,13734,14980,26659]
srcs=[str(s) for s in z["sources"]]
fin=0; tot=0; sent=0
for s in srcs:
    for f in ("mean","detect","fano","depth","hk"):
        v=z[f"{s}__{f}"][RES]; tot+=len(v); fin+=int(np.isfinite(v).sum())
    sent+=int((z[f"{s}__n_available"][RES]==-1).sum())
print(f"FIREWALL: reserved statistic slots={tot}, finite(computed)={fin}  <-- must be 0")
print(f"          n_available sentinel -1 slots={sent} of {len(RES)*len(srcs)}  <-- must be all")
print(f"          protected entries dropped before accumulation: {r['protected_entries_dropped_before_accumulation']:,}")
print(f"\nNPH52 axis: {json.dumps(r['nph52_axis'], indent=1)[:400]}")
print(f"available addresses per source: {r['per_source_available_addresses']}")
print(f"blocks read {r['blocks_read']}  entries {r['nonzero_entries_folded']:,}  "
      f"fitting nuclei folded exactly once: {r['fitting_nuclei_folded_exactly_once']:,}")
PY
```

OUT

```
FIREWALL: reserved statistic slots=90, finite(computed)=0  <-- must be 0
          n_available sentinel -1 slots=18 of 18  <-- must be all
          protected entries dropped before accumulation: 261,461

NPH52 axis: {
 "NPH52::matrix::MG_data_arranged_updatedId_final_batches.qs": {
  "provenance_rows": 32176,
  "authenticated_addresses": 31621,
  "observed_nonzero_union": 28099,
  "measured_but_never_nonzero": 3522
 }
}
available addresses per source: {'HVS': 18731, 'SEA_AD': 34236, 'NPH52': 31616}
blocks read 5211  entries 303,849,232  fitting nuclei folded exactly once: 114,041
Shell cwd was reset to d:\Jepa project
```

Firewall verified: **0 of 90 reserved statistic slots computed**, all 18 carry the `-1` sentinel, 261,461 protected entries dropped before accumulation. NPH52 now uses its authenticated 31,621-address axis. Running audit and analysis.

**Bash&#xA0;**&#x41;udit and analyse corrected census

IN

```
cd /d/jepa_v5_wt_20260925
PY=/c/Users/dushy/anaconda3/envs/sea-ad-jepa-v3/python.exe
rm -rf /d/jepa_v5_outputs_20260925/pool_census_audit_v3 /d/jepa_v5_outputs_20260925/pool_analysis_v3
"$PY" scripts/v5/audit_candidate_pool_census_v1.py \
  --census /d/jepa_v5_outputs_20260925/pool_census_v3/FULL104_CANDIDATE_POOL_CENSUS_V1.npz \
  --receipt /d/jepa_v5_outputs_20260925/pool_census_v3/FULL104_CANDIDATE_POOL_CENSUS_V1.json \
  --artifact "D:/jepa_v5_outputs_20260925/myeloid_panel_masked_full/FULL104_MYELOID_R8_PANEL_COUNTS_V1.npz" \
  --out-dir /d/jepa_v5_outputs_20260925/pool_census_audit_v3 2>&1 | tail -14
echo "================= ANALYSIS ================="
"$PY" scripts/v5/candidate_pool_analysis_v1.py \
  --census /d/jepa_v5_outputs_20260925/pool_census_v3/FULL104_CANDIDATE_POOL_CENSUS_V1.npz \
  --out-dir /d/jepa_v5_outputs_20260925/pool_analysis_v3 2>&1 | tail -30
```

OUT

```
  FAIL  cross_path_agreement
  PASS  reserved_readouts_not_compared
  PASS  forbidden_count
  PASS  donor_arms_disjoint
  PASS  fitting_nuclei_match
  PASS  availability_is_source_specific
  PASS  marginals_in_range

  FAILURES:
      NPH52|23673 AVAILABILITY DISAGREEMENT: artifact n=9391 vs census n=0

  ALL_CHECKS_PASS: False
wrote D:/jepa_v5_outputs_20260925/pool_census_audit_v3\AUDIT_CANDIDATE_POOL_CENSUS_V1.json
================= ANALYSIS =================
    T4_plus_depth          slots [1245, 290, 625, 613]        exact   258 (greedy  258)
    T5_all_five            slots [1239, 281, 145, 14]         exact    14 (greedy   14)
  HLA_DRA_ANTIGEN
    T1_mean                slots [174, 950, 1247, 1601]       exact   174 (greedy  174)
    T2_mean_detect         slots [157, 901, 1148, 1599]       exact   157 (greedy  157)
    T3_mean_detect_fano    slots [128, 773, 858, 1370]        exact   128 (greedy  128)
    T4_plus_depth          slots [117, 773, 858, 1370]        exact   117 (greedy  117)
    T5_all_five            slots [0, 42, 773, 1076]           exact     0 (greedy    0) EMPTY:CD74

=== COMBINED_ALL_SOURCES   eligible universe 16718
  APOE_LIPID
    T1_mean                slots [14, 1, 19, 6]               exact     1 (greedy    1)
    T2_mean_detect         slots [12, 1, 9, 6]                exact     1 (greedy    1)
    T3_mean_detect_fano    slots [0, 0, 0, 5]                 exact     0 (greedy    0) EMPTY:APOC1,ABCA1,GPNMB
    T4_plus_depth          slots [0, 0, 0, 5]                 exact     0 (greedy    0) EMPTY:APOC1,ABCA1,GPNMB
    T5_all_five            slots [0, 0, 0, 1]                 exact     0 (greedy    0) EMPTY:APOC1,ABCA1,GPNMB
  P2RY12_HOMEOSTATIC
    T1_mean                slots [32, 0, 3, 67]               exact     0 (greedy    0) EMPTY:CX3CR1
    T2_mean_detect         slots [32, 0, 1, 64]               exact     0 (greedy    0) EMPTY:CX3CR1
    T3_mean_detect_fano    slots [30, 0, 0, 48]               exact     0 (greedy    0) EMPTY:CX3CR1,GPR34
    T4_plus_depth          slots [30, 0, 0, 16]               exact     0 (greedy    0) EMPTY:CX3CR1,GPR34
    T5_all_five            slots [29, 0, 0, 1]                exact     0 (greedy    0) EMPTY:CX3CR1,GPR34
  HLA_DRA_ANTIGEN
    T1_mean                slots [0, 0, 140, 107]             exact     0 (greedy    0) EMPTY:CD74,HLA-DPA1
    T2_mean_detect         slots [0, 0, 139, 107]             exact     0 (greedy    0) EMPTY:CD74,HLA-DPA1
    T3_mean_detect_fano    slots [0, 0, 113, 1]               exact     0 (greedy    0) EMPTY:CD74,HLA-DPA1
    T4_plus_depth          slots [0, 0, 113, 1]               exact     0 (greedy    0) EMPTY:CD74,HLA-DPA1
    T5_all_five            slots [0, 0, 98, 0]                exact     0 (greedy    0) EMPTY:CD74,HLA-DPA1,IFI30

wrote D:/jepa_v5_outputs_20260925/pool_analysis_v3\CANDIDATE_POOL_ANALYSIS_V1.json
Shell cwd was reset to d:\Jepa project
```

Dramatic change. The per-source intersection collapses the combined population — your P1 was not a minor correction. Pulling the complete table.

**Bash&#xA0;**&#x46;ull corrected capacity table

IN

```
cd /d/jepa_v5_wt_20260925
PY=/c/Users/dushy/anaconda3/envs/sea-ad-jepa-v3/python.exe
"$PY" - <<'PY'
import json
d=json.load(open('D:/jepa_v5_outputs_20260925/pool_analysis_v3/CANDIDATE_POOL_ANALYSIS_V1.json'))
T=["T1_mean","T2_mean_detect","T3_mean_detect_fano","T4_plus_depth","T5_all_five"]
print("EXACT Hall max gene-disjoint panels (target 199)\n")
print(f"{'population':22s} {'program':20s} " + " ".join(f"{t.split('_')[0]:>6s}" for t in T) + "   empty slots at T1")
for pop,rec in d["populations"].items():
    for prog,p in rec["programs"].items():
        v=[p["panels"][t]["exact_hall_max_disjoint_panels"] for t in T]
        e=",".join(p["panels"]["T1_mean"]["empty_slots"]) or "-"
        print(f"{pop:22s} {prog:20s} " + " ".join(f"{x:6d}" for x in v) + f"   {e}")
print("\neligible universes:", {p:r["eligible_universe"] for p,r in d["populations"].items()})
print("\nREACHES 199 WITHOUT REUSE:")
any_ok=False
for pop,rec in d["populations"].items():
    for prog,p in rec["programs"].items():
        ok=[t.split('_')[0] for t in T if p["panels"][t]["reaches_199_without_reuse"]]
        if ok: print(f"  {pop:22s} {prog:20s} {', '.join(ok)}"); any_ok=True
if not any_ok: print("  NONE anywhere")
PY
```

OUT

```
EXACT Hall max gene-disjoint panels (target 199)

population             program                  T1     T2     T3     T4     T5   empty slots at T1
HVS                    APOE_LIPID              293    219    115    111    102   -
HVS                    P2RY12_HOMEOSTATIC      423    320    226    149    148   -
HVS                    HLA_DRA_ANTIGEN          64     48     37     13      4   -
NPH52                  APOE_LIPID              877    855     13     13     13   -
NPH52                  P2RY12_HOMEOSTATIC       64     62     59     59     59   -
NPH52                  HLA_DRA_ANTIGEN           0      0      0      0      0   HLA-DPA1
SEA_AD                 APOE_LIPID              630    318     57     57     36   -
SEA_AD                 P2RY12_HOMEOSTATIC      340    278    258    258     14   -
SEA_AD                 HLA_DRA_ANTIGEN         174    157    128    117      0   -
COMBINED_ALL_SOURCES   APOE_LIPID                1      1      0      0      0   -
COMBINED_ALL_SOURCES   P2RY12_HOMEOSTATIC        0      0      0      0      0   CX3CR1
COMBINED_ALL_SOURCES   HLA_DRA_ANTIGEN           0      0      0      0      0   CD74,HLA-DPA1

eligible universes: {'HVS': 18692, 'NPH52': 31575, 'SEA_AD': 34195, 'COMBINED_ALL_SOURCES': 16718}

REACHES 199 WITHOUT REUSE:
  HVS                    APOE_LIPID           T1, T2
  HVS                    P2RY12_HOMEOSTATIC   T1, T2, T3
  NPH52                  APOE_LIPID           T1, T2
  SEA_AD                 APOE_LIPID           T1, T2
  SEA_AD                 P2RY12_HOMEOSTATIC   T1, T2, T3, T4
Shell cwd was reset to d:\Jepa project
```

**Bash&#xA0;**&#x51;uantify cross-source expression spread

IN

```
cd /d/jepa_v5_wt_20260925
PY=/c/Users/dushy/anaconda3/envs/sea-ad-jepa-v3/python.exe
"$PY" - <<'PY'
import numpy as np
z=np.load("D:/jepa_v5_outputs_20260925/pool_census_v3/FULL104_CANDIDATE_POOL_CENSUS_V1.npz",allow_pickle=True)
NAMES={6188:"APOC1",11425:"ABCA1",7194:"GPNMB",2044:"TREM2",15109:"TMEM119",
       12239:"CX3CR1",12995:"GPR34",13365:"C1QA",392:"CD74",23673:"HLA-DPA1",
       18500:"HLA-DMA",20496:"IFI30"}
print("WHY THE COMBINED POOLS COLLAPSE: each partner's mean differs across sources,")
print("so a candidate must sit inside 0.80-1.25x of it in ALL THREE simultaneously.\n")
print(f"{'partner':10s} {'HVS':>8s} {'NPH52':>8s} {'SEA_AD':>8s} {'max/min':>9s}")
sp=[]
for a,nm in NAMES.items():
    v=[z[f"{s}__mean"][a] for s in ("HVS","NPH52","SEA_AD")]
    fin=[x for x in v if np.isfinite(x) and x>0]
    r=max(fin)/min(fin) if len(fin)>1 else float('nan')
    sp.append(r)
    print(f"{nm:10s} " + " ".join(f"{x:8.3f}" if np.isfinite(x) else f"{'n/a':>8s}" for x in v) + f" {r:9.2f}x")
print(f"\nmedian cross-source spread across the 12 partners: {np.nanmedian(sp):.2f}x")
print("The matching band is 1.25/0.80 = 1.56x wide. A partner whose own mean moves")
print("more than that between sources cannot be matched by one gene everywhere.")
print(f"partners whose spread exceeds the band: "
      f"{int(np.nansum(np.array(sp) > 1.25/0.80))} of 12")
PY
```

OUT

```
WHY THE COMBINED POOLS COLLAPSE: each partner's mean differs across sources,
so a candidate must sit inside 0.80-1.25x of it in ALL THREE simultaneously.

partner         HVS    NPH52   SEA_AD   max/min
APOC1         0.323    0.183    0.610      3.34x
ABCA1         1.441    0.284    1.298      5.07x
GPNMB         0.192    0.140    0.396      2.83x
TREM2         0.152    0.640    0.309      4.21x
TMEM119       0.122    0.350    0.232      2.88x
CX3CR1        0.651    4.691    1.207      7.21x
GPR34         1.095    1.807    1.033      1.75x
C1QA          0.534    1.055    1.019      1.97x
CD74          3.777    6.169    3.477      1.77x
HLA-DPA1      0.541      n/a    0.643      1.19x
HLA-DMA       0.336    0.389    0.437      1.30x
IFI30         0.173    0.169    0.192      1.14x

median cross-source spread across the 12 partners: 2.40x
The matching band is 1.25/0.80 = 1.56x wide. A partner whose own mean moves
more than that between sources cannot be matched by one gene everywhere.
partners whose spread exceeds the band: 9 of 12
Shell cwd was reset to d:\Jepa project
```

**9 of 12 partners vary across sources by more than the matching band itself.** That's the mechanism. Rewriting the closeout with corrected numbers.

**Write** D:\jepa_v5_wt_20260925\docs\agent\V29_FULL104_CANDIDATE_POOL_CENSUS_RESULTS_20260928.md

238 lines

````
# FULL104 candidate-pool census — results and feasibility decision

**Date 2026-09-28, revised the same day after three independent-review repairs.
Branch `review/v27-authority-root-inventory-20260925`. `TRAINING=OFF`. Real
teacher-fidelity evaluation CLOSED. No reserved readout opened; from this run
none was even computed on.**

> **This supersedes the first version of this report.** Three defects were
> repaired between them — protected readouts were being accumulated before
> exclusion, NPH52 availability was taken from observed nonzeros rather than its
> authenticated axis, and the combined population was a pooled average rather
> than a per-source intersection. The third changes the headline numbers
> drastically. §6 records what moved and why.

## Decision

| program | verdict in the combined population |
|---|---|
| **APOE_LIPID** | **INFEASIBLE.** Exactly **1** gene-disjoint panel at the loosest tier, 0 from the dispersion tier onward. |
| **P2RY12_HOMEOSTATIC** | **INFEASIBLE.** **0** at every tier; CX3CR1 has no eligible candidate even on mean alone. |
| **HLA_DRA_ANTIGEN** | **INFEASIBLE.** **0** at every tier; CD74 and HLA-DPA1 both empty. |

**No program reaches 199 gene-disjoint panels in the combined population at any
tier.** The first version of this report said HLA_DRA was infeasible and the
other two were feasible at loose tiers. That was an artefact of pooling sources;
corrected, **all three are infeasible**.

This is a statement about **sham construction**. The count-based null could not
be assembled, so it was never run and did not fail.

---

## 1. What was run

All 8,915 Level-4 manifest blocks streamed; **5,211 count blocks** contained
fitting nuclei and were read; **303,849,232 nonzero entries** folded.
**114,041 fitting nuclei** from **60 fitting donors**, each folded exactly once
and asserted so. 32 evaluation donors and their 73,868 nuclei never touched.

Structurally measurable addresses, from authenticated axes:

| source | measurable | eligible after exclusions | fitting nuclei |
|---|---:|---:|---:|
| HVS | 18,731 | 18,692 | 1,415 |
| NPH52 | 31,616 | 31,575 | 9,391 |
| SEA_AD | 34,236 | 34,195 | 103,235 |
| **intersection** | — | **16,718** | — |

---

## 2. Exact Hall capacity against the frozen target of 199

Gene-disjoint means no gene reused in any panel. Computed with the independent
workstream's exact Hall/bipartite tool, not a greedy construction. **Disjointness
is a conservative feasibility criterion and does not by itself establish
statistical independence of the sham draws.**

| population | program | T1 mean | T2 +detect | T3 +Fano | T4 +depth | T5 all five |
|---|---|---:|---:|---:|---:|---:|
| HVS | APOE_LIPID | 293 | 219 | 115 | 111 | 102 |
| HVS | P2RY12 | 423 | 320 | 226 | 149 | 148 |
| HVS | HLA_DRA | 64 | 48 | 37 | 13 | 4 |
| NPH52 | APOE_LIPID | 877 | 855 | 13 | 13 | 13 |
| NPH52 | P2RY12 | 64 | 62 | 59 | 59 | 59 |
| NPH52 | HLA_DRA | **0** | 0 | 0 | 0 | 0 |
| SEA_AD | APOE_LIPID | 630 | 318 | 57 | 57 | 36 |
| SEA_AD | P2RY12 | 340 | 278 | 258 | 258 | 14 |
| SEA_AD | HLA_DRA | 174 | 157 | 128 | 117 | **0** |
| **COMBINED** | **APOE_LIPID** | **1** | **1** | **0** | **0** | **0** |
| **COMBINED** | **P2RY12** | **0** | **0** | **0** | **0** | **0** |
| **COMBINED** | **HLA_DRA** | **0** | **0** | **0** | **0** | **0** |

Reaches 199 without reuse: HVS APOE (T1–T2), HVS P2RY12 (T1–T3), NPH52 APOE
(T1–T2), SEA_AD APOE (T1–T2), SEA_AD P2RY12 (T1–T4). **Never in the combined
population, for any program, at any tier.**

---

## 3. Why the combined pools collapse — and it is not small-sample noise

A combined-eligible gene must satisfy the matching band **separately in every
source**. The band is 1.25 / 0.80 = **1.56× wide**. But each partner's own mean
moves between sources by more than that:

| partner | HVS | NPH52 | SEA_AD | max/min |
|---|---:|---:|---:|---:|
| APOC1 | 0.323 | 0.183 | 0.610 | 3.34× |
| ABCA1 | 1.441 | 0.284 | 1.298 | 5.07× |
| GPNMB | 0.192 | 0.140 | 0.396 | 2.83× |
| TREM2 | 0.152 | 0.640 | 0.309 | 4.21× |
| TMEM119 | 0.122 | 0.350 | 0.232 | 2.88× |
| **CX3CR1** | 0.651 | **4.691** | 1.207 | **7.21×** |
| GPR34 | 1.095 | 1.807 | 1.033 | 1.75× |
| C1QA | 0.534 | 1.055 | 1.019 | 1.97× |
| CD74 | 3.777 | 6.169 | 3.477 | 1.77× |
| HLA-DPA1 | 0.541 | *not measured* | 0.643 | 1.19× |
| HLA-DMA | 0.336 | 0.389 | 0.437 | 1.30× |
| IFI30 | 0.173 | 0.169 | 0.192 | 1.14× |

Median cross-source spread **2.40×**, and **9 of 12 partners exceed the matching
band itself**. To match such a partner everywhere, a candidate would have to
reproduce not just its level but its *cross-source pattern* — rising 7-fold into
NPH52 for CX3CR1, falling 5-fold for ABCA1. Almost nothing does.

**This is the real finding, and it is more general than pool size.** The three
sources do not place these genes on a common scale. Whether that reflects
protocol, dissection, nuclear isolation or cohort composition is not resolved
here, and it is an outcome-blind, structural fact about the corpus rather than
anything about the shams.

### An interpretive question this raises, which I am not resolving alone

v7 says donors are split "by hash of the source-specific donor identity. Sources
never pooled." If that means a single frozen sham roster must serve all three
sources, the combined row governs and **all three programs are infeasible**. If
per-source rosters are admissible, the per-source rows govern and APOE and
P2RY12 remain feasible **only at T1/T2** — tiers the counterexample already
proves insufficient for latent capture.

**The count-route verdict is the same either way**, which is why this is
reported rather than treated as a blocker. But the two readings license
different sentences about *why*, and the distinction should be settled before
the closeout is frozen.

---

## 4. HLA_DRA: the two reasons, now both structural

**CD74 is unmatchable** at the strictest tier: 99.6th abundance percentile in HVS
and 99.85th in NPH52; nothing in 34,195 eligible SEA-AD addresses falls inside
its bands at T5, and nothing in the combined population at any tier.

**HLA-DPA1 is not in NPH52's authenticated feature axis.** Now established from
the stage81a2r provenance table filtered to the MG object — 32,176 rows, 31,621
distinct addresses — rather than inferred from observed zeros. CD74, PGK1, LPL
and APOE are in that axis; address 23673 is not.

The MHC class II locus caveat stands: HLA-DRA, HLA-DPA1, HLA-DMA and HLA-DMB are
physically linked and CIITA-co-regulated, so a random-gene null lacks coherence
the real panel has by construction. Even a feasible pool would have been an
unfair comparison here.

---

## 5. A defect in the corrected artifact, now doubly confirmed

The audit **fails on exactly one disagreement**, deliberately:

```
NPH52 | address 23673 (HLA-DPA1): artifact n=9391 available, census n=0
```

| source | nuclei | artifact says available | nonzero counts |
|---|---:|---|---:|
| HVS | 2,117 | True | 777 (36.7%) |
| **NPH52** | **15,264** | **True** | **0 (0.0%)** |
| SEA_AD | 170,528 | True | 64,642 (37.9%) |

Two independent routes agree it is absent: the authenticated provenance axis,
and the NPH52 pilot's reading of the historical archive. **Root cause:** the
extractor treats NPH52 as identity-verified and returns every requested address
as reachable *without checking its feature axis per address*. HVS and SEA-AD
availability came from a verified decoder; NPH52's was assumed.

**Blast radius stays small.** `total_excluding_29` subtracted address 23673 for
NPH52 nuclei and it contributed exactly 0, so no denominator is numerically
wrong, and no analysis has read those 15,264 zeros as measurement. Address 40452
is **not** substituted: same symbol, different address, unverified identity.

---

## 6. What the three repairs moved

| repair | effect on the numbers |
|---|---|
| Protected readouts excluded **before** accumulation | No effect on any pool. Restores blindness; the exposure is recorded in the ledger as Correction 4. |
| NPH52 availability from the **authenticated axis** | **Raised** NPH52 eligibility from 28,053 to 31,575 addresses — 3,522 genes were measured but zero in every myeloid nucleus and had been wrongly treated as unmeasured. NPH52 APOE T1 rose from ≥398 to 877. |
| Combined = **per-source intersection**, not pooled average | **Collapsed** every combined figure. APOE T5 28 → 0; P2RY12 T4 203 → 0; HLA_DRA T1 139 → 0. The pooled average had been hiding source-specific matching failure exactly as the review predicted. |
| Exact Hall capacity replacing greedy | Agreed with greedy in every cell checked. Greedy was a valid constructive lower bound; the numbers are now exact rather than merely sufficient. |

---

## 7. What this does and does not license

**No exchangeability claim.** The 2026-09-28 counterexample matched two panels to
within 0.003 on mean, detection and depth correlation and 0.0005 on within-panel
covariance, and they still differed +0.809 versus +0.002 on residual capture
coupling. Every tier here is built from those same observables.

**Disjointness ≠ independence.** No cross-panel gene reuse is a conservative
feasibility criterion. It does not establish that the sham statistics are
statistically independent.

**The type-I figures remain scenario calculations**, from an assumed correlation
rule applied to the pilot's measured reuse — not a qualified pipeline error rate.

**No candidate list is emitted**, no tier is preferred, no gene selected.
Selection used fitting donors only.

---

## 8. Decision under frozen protocol v7

**`SHAM_CONSTRUCTION_INFEASIBLE`** for all three programs in the combined
population, at every matching tier. Where per-source construction is feasible it
is feasible only at tiers already shown insufficient.

**The count-based teacher-fidelity procedure is recorded as
`INSUFFICIENTLY_IDENTIFIABLE_UNDER_TESTED_NUISANCE`** per the v7 stopping rule.
Bands, thresholds and pools are not to be retuned to induce a pass.

That verdict is about the **validation strategy**. It is not evidence that the
per-nucleus biological state is absent, and must never be reported as such.

**Next, in order:**

1. Repair the NPH52 availability flag in the artifact itself, deriving it from
   the provenance axis rather than assuming it, and re-audit. One flag is wrong
   today; the method that produced it would produce more.
2. Freeze the v7 count-route closeout, with §3's interpretive question settled.
3. **Conditional composition as a new developmental validation strategy**, with a
   **differential-capture negative control mandatory from the start**. The
   independent CPU work already showed why: 5/120 positives under uniform
   capture but **119/120 under gene-specific differential capture with no
   biological association**, and a per-donor conditional binomial GLM at
   **0/80 uniform versus 80/80 false positives under differential capture**.
   Supplying the true hidden capture factor — unavailable in real data — cut
   those to 2/80. Observed depth does not control gene-specific capture.
4. Same-nucleus thinning may contribute a **post-capture measurement-robustness
   diagnostic** only. It cannot establish equivalence with respect to the
   original hidden biochemical capture process.

**With every internal reserved readout downgraded to secondary evidence (see the
exposure ledger's owner ruling), this study has no strictly independent internal
confirmation left.** The donor-level ATAC evaluation becomes the genuine
confirmation layer, and that shift should be stated wherever these results are
reported.

````

if we dont have a qualified target yet will finding these controls sham or poritive/negative controls be ineffective?

**Bash&#xA0;**&#x43;ommit corrected census results

IN

```
cd /d/jepa_v5_wt_20260925
cp /d/jepa_v5_outputs_20260925/pool_census_v3/FULL104_CANDIDATE_POOL_CENSUS_V1.json results/v29/
cp /d/jepa_v5_outputs_20260925/pool_analysis_v3/CANDIDATE_POOL_ANALYSIS_V1.json results/v29/
cp /d/jepa_v5_outputs_20260925/pool_census_audit_v3/AUDIT_CANDIDATE_POOL_CENSUS_V1.json results/v29/
git add -f results/v29/FULL104_CANDIDATE_POOL_CENSUS_V1.json results/v29/CANDIDATE_POOL_ANALYSIS_V1.json results/v29/AUDIT_CANDIDATE_POOL_CENSUS_V1.json
git add docs/agent/V29_FULL104_CANDIDATE_POOL_CENSUS_RESULTS_20260928.md
git commit -q -F- <<'MSG'
Corrected census: all three programs infeasible; sources are not on a common scale

The per-source intersection changes the headline. Pooling sources had been
hiding source-specific matching failure exactly as the review predicted.

EXACT Hall capacity, combined population, against the target of 199:

  APOE_LIPID    1  1  0  0  0
  P2RY12        0  0  0  0  0    CX3CR1 empty even on mean alone
  HLA_DRA       0  0  0  0  0    CD74 and HLA-DPA1 both empty

No program reaches 199 in the combined population at any tier. The first
version of this report said HLA_DRA was infeasible and the other two feasible
at loose tiers; that was an artefact of pooling.

THE MECHANISM, which is a more general finding than pool size. A combined
candidate must sit inside the matching band in every source. The band is
1.25/0.80 = 1.56x wide. But the partners' own means move between sources by
more than that: median spread 2.40x and NINE OF TWELVE partners exceed the
band. CX3CR1 runs 0.651 in HVS, 4.691 in NPH52, 1.207 in SEA-AD - 7.21x. To
match such a partner everywhere a candidate would have to reproduce not just
its level but its cross-source pattern. Almost nothing does. The three sources
do not place these genes on a common scale.

An interpretive question is recorded rather than decided: v7 says sources are
never pooled for the donor split. If one frozen roster must serve all sources,
the combined row governs and all three are infeasible; if per-source rosters
are admissible, APOE and P2RY12 are feasible only at T1/T2, which the
counterexample already proves insufficient. The verdict is identical either
way, which is why it is reported and not treated as a blocker - but the two
readings license different sentences about WHY.

WHAT THE THREE REPAIRS MOVED:

  protected-before-accumulation  no pool changed; blindness restored. From this
                                 run zero of 90 reserved statistic slots were
                                 computed, all carry the -1 sentinel, 261,461
                                 protected entries dropped before any
                                 accumulator saw them.
  authenticated NPH52 axis       RAISED NPH52 eligibility 28,053 -> 31,575.
                                 3,522 genes are measured but zero in every
                                 myeloid nucleus and had been wrongly treated
                                 as unmeasured. NPH52 APOE T1 rose to 877.
  per-source intersection        COLLAPSED every combined figure. APOE T5
                                 28 -> 0, P2RY12 T4 203 -> 0, HLA_DRA T1
                                 139 -> 0.
  exact Hall vs greedy           agreed in every cell; numbers now exact rather
                                 than merely sufficient.

5,211 count blocks read of 8,915 manifest blocks, 303,849,232 entries folded,
114,041 fitting nuclei each folded exactly once and asserted so.

The audit still FAILS on one disagreement, deliberately: NPH52 HLA-DPA1,
artifact n=9391 available versus census n=0. Now confirmed structurally from
the provenance axis rather than inferred from observed zeros, and independently
by the NPH52 pilot. No denominator is numerically wrong - the address
contributed exactly zero to total_excluding_29.

Count route stands closed as INSUFFICIENTLY_IDENTIFIABLE_UNDER_TESTED_NUISANCE.
A statement about the validation strategy, not about APOE, P2RY12 or HLA-DRA
biology.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
git push -q origin review/v27-authority-root-inventory-20260925 && echo PUSHED
```

OUT

```
PUSHED
Shell cwd was reset to d:\Jepa project
```

Corrected census pushed. Now your question — and I think you've caught a real ordering error in how I've been working.

## Short answer: partly yes, and the distinction matters

**Negative controls (shams) are premature without a qualified target. Positive controls are not.**

A sham exists to answer "could this signal have arisen by chance?" That question only means something if there *is* a signal to interrogate. If the per-nucleus program score is mostly measurement noise, then the real program and a well-matched sham will look alike — and the test returns null. Not wrong, just **uninformative**. You'd have spent enormous effort building a null for a statistic that was never measuring anything.

A positive control is different. Planting a known effect and asking whether the pipeline recovers it tests *sensitivity*, and that's meaningful whether or not the real biology is there. That's why the synthetic gate work still stands: it established the machinery can detect a planted effect at a tested strength.

## The sharper version: these are the same problem

The sham question and the target question both reduce to **gene-specific capture**.

- The target is a ratio of counts at 1–4 molecules per gene, so its variation is part biology and part capture.
- The sham has to match on capture — the counterexample proved observables can't pin that down.
- The composition fallback fails on capture too — 119/120 and 80/80 false positives under differential capture.

So capture sits upstream of all three. I've been attacking it from the null side, which is the hardest side, when the cheaper and more fundamental question is whether the target carries measurable signal at all.

## What we actually don't know

**The reliability of the four-partner program score has never been measured on authenticated coordinates.** R7 reported a thinning-repeatability proxy of 0.659 for APOE and 0.364 for P2RY12 — but that was on the scrambled columns, so those numbers describe random gene sets, not the real programs.

That is a genuine gap, it sits upstream of everything I've spent this session on, and it's answerable with data already on disk.

## What is not wasted

- **The cross-source scale finding.** Nine of twelve partners vary more between sources than the matching band is wide; CX3CR1 runs 7.2× from HVS to NPH52. That's a structural fact about the corpus that will constrain *any* cross-source analysis, target or no target.
- **The NPH52 artifact defect.** Real, must be fixed regardless.
- **The methodological result** that observable matching can't establish exchangeability — permanent.
- **The gate executor and validator hardening** — infrastructure that outlives any particular target.
- **The exposure ledger** — governance that had to happen.

## What I'd do instead, and it's cheap

Measure the target's reliability before building any more controls:

1. **Split-half over partners** — score each nucleus from 2 of the 4 partners, twice, correlate within donor×operator stratum.
2. **Binomial thinning repeatability** — split each nucleus's counts and score both halves. This is exactly what thinning legitimately supports: post-capture measurement robustness.
3. Report per source, since §3 shows they're not on a common scale.

Uses only the program genes, which are already exposed by design. No reserved readout, no evaluation donor, no new extraction.

If reliability is near zero at these counts, **that is the finding** — the per-nucleus target is not measurable, and it explains the sham difficulty rather than being explained by it. If it's substantial, then the capture problem is worth the fight and the composition route has something to aim at.

Either way it's a better next step than more control design. Want me to run it?

how is our target discovery situation

Let me ground this in the actual record rather than my session memory — I read the audits index and protocol v7 earlier but never opened the target-discovery history.

**Bash&#xA0;**&#x52;ead target discovery history

IN

```
cd /d/jepa_v5_wt_20260925
cat docs/agent/V5_FULL104_TARGET_DISCOVERY_HISTORY_TO_TD60_SUCCESSOR_20260921.md
```

OUT

```
# V5 FULL104 target-discovery history -> learned-teacher relational successor

Date: 2026-09-21  
Status: `PROSPECTIVE_TARGET_QUALIFICATION_DESIGN__NO_TRAINING_AUTHORITY`

## Bottom line

The project has already searched many candidate targets. The surviving lesson is not
"pick another gene/module/PCA coordinate." The strongest replicated biological
object is **relational cell-state geometry**.

The current target hypothesis is therefore:

> the EMA teacher's direct biological cell-state representation may become the
> JEPA target only if it preserves already-qualified donor-recurrent molecular
> relational structure.

This is a qualification of a learned state, not another target-discovery search.

## Historical decisions that remain binding

### Pathology-prediction era (Stage27C/41C/53-62)

These stages showed that donor/cell-state features can carry disease-associated
signal, but pathology prediction was the optimization criterion.

**Carry forward:** biological heterogeneity matters.  
**Do not carry forward:** pathology performance as target authority.

### Rare-microglia era (Stage64-71)

Rare/high-tail microglial programs were biologically coherent and sometimes
improved internal donor-held-out prediction. Stage68 showed strong recurrent
high-tail expression contrasts. But Stage70/71 did not earn the final
representation/prediction lock.

**Carry forward:** rare biology can be diluted by averaging and must be protected.  
**Do not carry forward:** old rare-cell labels/modules as supervised JEPA targets.

### Stage81 representation era

Balanced PCA/REP work showed stable subspace structure, but axes rotated and
cross-donor/matrix behavior was weaker. Historical 160/224-D states explicitly
did not establish complete biological sufficiency.

**Carry forward:** state may be stable as geometry/subspace rather than exact axes.  
**Do not carry forward:** historical PCA/REP coordinates or dimensions as final target authority.

### TD13-TD36 falsification era

Gene loadings, dependency graphs, source-global subspaces, class-conditioned
subspaces, and generic label-free clustering repeatedly failed cross-source or
donor recurrence. Several apparent positives were later invalidated by reset-row
aliasing. Corrected annotated state geometry remained validation-only.

**Carry forward:** row identity, donor recurrence, technical nulls and cross-source
replication are mandatory.  
**Do not repeat:** coordinate/loadings/dependency/global-subspace target searches
without a materially new hypothesis.

### TD37-TD55 coordinate/predictability era

A source-internal linear object existed, but its coefficients did not transfer.
Pair-order geometry and uncertainty-aware pair direction were reliable, but
attempts to infer exact pair inversions, query-local ordinal coordinates,
reference contexts, nonlinear contexts and stable visible proxies generally
failed donor recurrence or independent-source replication.

**Carry forward:** exact coordinates are fragile; relational order is more stable.

### TD56-TD59 surviving relational evidence

The strongest surviving evidence is:

- TD56: disjoint-gene within-donor relational geometry survived HVS, NPH52 and SEA_AD;
- TD57A/B: scale-free triplet relational order survived donor blocks and independent
  panels; TD57B closed 24/24;
- TD58: partial molecular evidence (60%) still reproduced the relational target 24/24;
- TD57C: nearest-third fine locality failed;
- TD59: nearest-half mesoscale relational recurrence survived 24/24.

No production target or training authority was granted by those screens.

### TD60 unfinished bridge

TD60 was prospectively designed to ask whether a lawful learned EMA teacher
preserves the already-qualified global TD57B and mesoscale TD59 relations.

It has no result and remains the correct conceptual bridge.

## FULL104 / ETL changes that must now modify TD60

The lawful reader-fit population is:

- 4,553,407 cells;
- 104 donors;
- 42 operators;
- HVS: 41 donors / 198,718 cells;
- NPH52: 17 donors / 236,476 cells;
- SEA_AD: 46 donors / 4,118,213 cells.

SEA_AD contains ~90% of cells. Therefore raw cell-uniform evaluation would let one
source dominate the target decision.

The current scientific mass remains:

`DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1`

Source is a robustness/domain stratum, not automatic scientific mass. HVS, NPH52
and SEA_AD must remain separately visible to the qualification decision.

Operator cannot be treated as one common biological/technical axis because:
- HVS operators are native-class-pure;
- NPH52 operators are class-pure;
- SEA_AD operators are region matrices.

Native cell-class labels are also not a lawful universal target ontology because
the three source schemas are not harmonized and NPH52 broad-class is absent.

## Current prospective target qualification

Implemented in:

`src/sea_ad_jepa/v5/full104_teacher_relational_target_qualification_authority_v1.py`

The prospective target remains:

`BIOLOGICAL_CELLULAR_LATENT_STATE_V1`

Teacher representation:

`EMA_DIRECT_CELL_STATE__NO_PROJECTION_HEAD_V1`

The teacher state cannot be promoted solely because JEPA loss decreases or because
its embedding looks structured.

It must first preserve:

1. TD57B-style global relational order; and
2. TD59 nearest-half mesoscale relational order.

No new gene-panel search and no new locality search are allowed in this authority.

## Rare biology policy

Rare disease-associated biology is **not** converted into a supervised target label.

The protection strategy is:

1. donor-uniform scientific mass prevents huge donors/cell populations from setting
   the objective by cell count;
2. every source remains visible separately, so NPH52/HVS cannot disappear behind
   SEA_AD;
3. rare-state, disease, pathology and native-class labels are forbidden in target
   construction;
4. rare biology must earn representation authority through donor recurrence and
   preservation, not rarity alone.

Important limitation:

This authority does **not yet claim that a learned teacher preserves rare-state
tails**. A separate outcome-blind rare/heterogeneity preservation diagnostic must
be prospectively defined before such a claim is made. It must not reuse pathology
outcomes or tune a rare-state threshold after viewing teacher latents.

## Current stop boundary

This work does not authorize:

- teacher/student training;
- successor u40 production;
- TD60 outcome inspection;
- pathology access;
- DEV/SEALED expression;
- new gene-panel selection;
- new locality-fraction tuning;
- rare-state label supervision;
- terminal masking adaptation.

Current state:

`FULL104_LEARNED_TEACHER_RELATIONAL_TARGET_QUALIFICATION_PROSPECTIVELY_DEFINED__WAITING_FOR_LAWFUL_TEACHER__TRAINING_OFF`
Shell cwd was reset to d:\Jepa project
```

This reframes things — and I should have read it earlier. Checking how the three-program work relates to the TD60 line.

**Bash&#xA0;**&#x52;ead R7 next-target decision contract

IN

```
cd /d/jepa_v5_wt_20260925
PY=/c/Users/dushy/anaconda3/envs/sea-ad-jepa-v3/python.exe
"$PY" -c "
import json
d=json.load(open('D:/jepa_v5_outputs_20260925/r7_r8_packages/R7/JEPA_R7_NEXT_TARGET_DECISION_CONTRACT_20260926.json'))
print(json.dumps(d, indent=1))" | head -70
```

OUT

```
{
 "schema": "JEPA_R7_CANDIDATE_QUERY_LOCAL_TARGET_NONAUTHORIZING_V1",
 "date": "2026-09-26",
 "status": "THREE_PREDECLARED_RNA_PROGRAM_ANCHORS_FALSIFIED_AS_SUFFICIENT_BIOLOGY_TARGETS_NOT_REJECTED_AS_POSSIBLE_COMPONENTS",
 "governance": {
  "training_authorized": false,
  "audit_b_n1_opened": false,
  "protected_full104_outcomes_opened": false,
  "teacher_target_scientifically_selected": false,
  "architecture_selected": false,
  "historical_data_reused": true,
  "current_full104_population_used": false
 },
 "scientific_objective": "For cell c and query q, a rich teacher constructs a multidimensional, same-cell, biologically falsifiable molecular state from explicitly documented evidence. A student predicts only the component recoverable from lawful complementary RNA. Non-causal gene associations and measured-cell state must not be conflated with perturbation effects.",
 "status_of_existing_target": "R5/R6 data-derived eight-gene contextual panel is a developmental measurable prediction anchor only; it is not a biological world-state target. R7 separately tests three prior-named marker program anchors and finds insufficient same-assay heldout-gene generalization in historical microglia.",
 "candidate_target_object": {
  "name": "STRUCTURED_QUERY_PROGRAM_STATE_CANDIDATE_V1",
  "identity": [
   "original_same_cell_key",
   "canonical_query_address",
   "ordered_component_gene_addresses",
   "source_artifact_sha256",
   "teacher_input_policy_sha256"
  ],
  "measured_anchor": "Actual same-cell, original-count evidence in a prospectively named nonquery program panel; carry measured zero distinctly from structurally unavailable assays and no-support abstention.",
  "count_scale_and_composition": "Store absolute count information and separately labeled q-independent compositional coordinates. Normalizing a panel by its own sum removes its total activation amplitude; raw log counts retain amplitude but are depth/confounding sensitive. Neither is approved as the full state alone.",
  "teacher_query_value_policy": "COMPARE_RICH_Q_VISIBLE_VS_Q_EXCLUDED_NO_DECISION_YET",
  "teacher_latent": "Learned contextual program embedding only after its independent biological meaning has a declared falsifier; no scalar-only reconstruction objective.",
  "student_input": "Mask and normalize only complementary observed RNA, excluding the queried value, all target-program measurements and any derived full-library or QC feature carrying those forbidden counts.",
  "optional_core_fine_rare": "Keep head coordinates, measurement eligibility, donor recurrence, uncertainty, q identity and same-cell provenance distinct; unsupported specialists abstain rather than emit fake zeros.",
  "output": "One or more measured anchor vectors plus scientifically qualified predictable latent-state coordinates and support/uncertainty metadata; do not confuse arbitrary embedding coordinates with biological targets."
 },
 "remaining_scientific_decisions": [
  "Select original, authenticated, outcome-safe development population with sufficient microglia and independent donors",
  "Predeclare actual biological target and independently measured falsifier for each query/head, preferably assays not used to construct or select the teacher",
  "Require teacher-only biological relevance, count-thinning stability, donor/study transport and additional signal beyond technical and generic-cell comparators",
  "Compare rich q-visible and q-excluded teachers on a fixed measured biological target before selecting teacher input semantics",
  "Separate generic state predictability from true cell-by-query interaction and compare against a rich capacity/compute-matched reference",
  "Only after target fidelity and predictability are qualified, compare single rich, shared multi-head and complementary teachers under the same support and donor budgets",
  "Review versioned target-construction authority and branch-aware optimizer/EMA/checkpoint integration without modifying original V5 frozen contracts"
 ],
 "forbidden_shortcuts": [
  "Claiming same-assay held-out RNA constitutes independent biological validation",
  "Using HLA symbol-only aliases rather than exact current Ensembl address mapping",
  "Treating structurally unmeasured genes as measured zero",
  "Treating within-panel composition as total activation",
  "Using query value in the student or its input denominators",
  "Using one program success to claim the target works for all query identities",
  "Using historical 5-fold diagnostic geometry to authorize current 4-fold production masking",
  "Unlocking FULL104 training from synthetic, historical or source-contract tests"
 ]
}
Shell cwd was reset to d:\Jepa project
```

Now I can answer properly — and the first thing to say is that I should have read this document at the start of the session.

## Where target discovery actually stands: no target has been selected

R7's own decision contract records `teacher_target_scientifically_selected: false`. There are **two parallel lines**, and I've spent this entire session on the weaker one.

## Line A — relational cell-state geometry (the strong line)

This is the project's best-replicated biological object, and it's largely intact:

| screen  | result                                                                                                    |
| ------- | --------------------------------------------------------------------------------------------------------- |
| TD56    | disjoint-gene within-donor relational geometry survived HVS, NPH52 **and** SEA-AD                         |
| TD57A/B | scale-free triplet relational order survived donor blocks and independent panels — **TD57B closed 24/24** |
| TD58    | only 60% of molecular evidence still reproduced the relational target **24/24**                           |
| TD59    | nearest-half mesoscale relational recurrence **24/24**                                                    |
| TD57C   | nearest-*third* fine locality **failed** — so the scale is real, not arbitrary                            |

**TD60 is the unfinished bridge**: does a lawfully learned EMA teacher preserve TD57B global order and TD59 mesoscale order? It was prospectively designed and **has no result**.

**The blocker is circular.** TD60 needs a *learned* teacher. A learned teacher needs training. Training is off until a target is qualified. Target qualification *is* TD60. That's a governance knot, not a measurement problem, and only you can cut it — most cleanly by authorizing a bounded qualification-only run whose sole output is a teacher state for TD60, granting no production authority.

## Line B — the gene-panel program state (what I've been working on)

R7 already classified this on 2026-09-26, before this session:

> `THREE_PREDECLARED_RNA_PROGRAM_ANCHORS_FALSIFIED_AS_SUFFICIENT_BIOLOGY_TARGETS_NOT_REJECTED_AS_POSSIBLE_COMPONENTS`

and the R5/R6 eight-gene panel is "a developmental measurable prediction anchor only; **it is not a biological world-state target**."

So the three programs were *already* downgraded to possible components. This session closed their count-based fidelity route. **That closure costs Line A nothing** — Line A never depended on it.

## The one place this session does touch target discovery

My census found that **9 of 12 partner genes vary more between sources than the matching band is wide** — median 2.40×, CX3CR1 7.21× from HVS to NPH52.

Your own history says: *"exact coordinates are fragile; relational order is more stable"* (TD37–TD55), and every surviving screen (TD56–TD59) is **ordinal**, not level-based.

Those are plausibly the same fact. If sources preserve *ordering* while disagreeing on *level*, then relational statistics transfer and level-based ones don't — which is exactly the pattern TD13–TD55 kept hitting. And the count-based teacher target is level-based by construction (`log1p(10000·partner_sum/reference)`), placing it squarely in the fragile family.

I offer that as a mechanistic hypothesis consistent with both records, not as a proven link.

## Honest summary

- **Target selected:** none.
- **Strongest object:** relational cell-state geometry, replicated 24/24 across three independent screens.
- **Blocking step:** TD60, designed, never run, blocked by a training/qualification circularity.
- **Line B:** closed as a sufficient target in September, and its measurement route closed this session.
- **Internal confirmation:** all six reserved readouts now downgraded to secondary — so external ATAC carries the confirmation load.
- **My error:** I worked a full session on Line B without reading the history that says gene-panel targets are not the path. The work stands on its own terms — the census, the artifact defect, the exposure ledger — but I should have known where it sat.

The decision in front of you is whether to unblock TD60, not whether to keep repairing Line B.