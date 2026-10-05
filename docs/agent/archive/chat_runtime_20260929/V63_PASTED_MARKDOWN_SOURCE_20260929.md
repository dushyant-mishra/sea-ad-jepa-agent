PR retargeted and Task 3 landed. Remote head `97dab7fa`.

## PR governance — fixed

`gh pr edit 198 --base chatgpt/v62-target-backbone-authority-successors-20260928`. Now **6 commits / 24 files**, exactly as you measured.

## Task 3 — the receipt, and the repair earning its keep

**Exact shared barcodes: zero.** The cause is concrete — the ATAC index *repeats the sample suffix*:

```
RNA   AAACAGCCACGTGCTG-1_HBCC-1193
ATAC  CCTATAGCAATATAGG-1_HBCC-1193_HBCC-1193

```

The `(sample, raw_barcode)` composite matches **1,501,089 — all of them, 1:1 with no residual**. So pairing is almost certainly real, and the probe still refuses to assert it. That is the repair working on real data: **v1.0 would have reported 0 paired microglia for NIH-CARD**, which would have read as "this cohort has no paired microglia."

Two things I'd flag as traps:

- **`.X` holds the counts (uint16); `raw/X` is log-like float32.** The convention is *reversed* from the usual AnnData layout. A pipeline assuming the norm would silently analyse log values as counts.
- **RNA `var` mixes symbols and Ensembl IDs in one index** — `OR4F5` sitting beside `ENSG00000290826`. Feature identity has to resolve on stable IDs.

**Microglia: 87,384 across 357 donors, median 217.** But the binding constraint is per-donor depth, not the headline: **167 of 357 donors have fewer than 200**, 45 below 50. And cohort is confounded with depth — HBCC median 157 vs NABEC 256.5 — which is a second, independent reason the PMI diagnostic must run *within* cohort.

Covariates are all present on the RNA side (Age, Sex, PMI, cohort, batch, Brain_bank, Race, Ancestry); ATAC carries only cohort.

## Integrity binding is now in the receipt, not a warning

Per your contract change: authoritative content-length (matches what the reader observed for both files), Zenodo's published md5, **`md5_verified: False` stated plainly** because verifying it means reading the 33 GB the range design avoids, last-modified, and the request/byte counts (36 requests / 3.2% for RNA; 21 / 2.4% for ATAC). I've saved the general rule — that a receipt must bind the identity of the bytes it read, because opening a file successfully is not evidence it is complete — so it carries into future sessions rather than living only in this receipt.

## Task 8 v2 — your design, and it already changed the answer

Rebuilt as a tournament with the three classes, per-family margins, one-sided LCB over seeds, donor-held-out folds, and all four anti-false-green controls. Smoke run (donors=8, seeds=4):

**TECH FAILS** — margin +0.0115, LCB95 **+0.0069 < M_MIN 0.010** — while NULL, GEO, ACC, ANCHOR and DONOR all pass. My v1 pooled ceiling would have shown this as healthy. `gate_may_proceed: false`.

The held-out ambient-cross-talk family *did* generalise. Twin identical to POS-BIO-1 (`NON_IDENTIFIABLE_BY_DESIGN`, not a failure). CRN verified. Detectability and the POS1 > POS2 > negatives ordering both hold.

One thing you should know: adding anchor frequency as a matching variable — needed to make NEG-ANCHOR-1 a fair test rather than a free win — pushed common support down to **15.4%** from v1's 41%. The full run with the selection-stress panel (standardised mean differences on retained vs discarded linked pairs) is executing now; that's your question about whether the attrition is statistical cost or a changed estimand.

**Bash** Read the full tournament and mutation results

IN

```
cat "C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/tasks/bazlox26i.output" 2>/dev/null
```

OUT

```
######## PRIMARY donors=18 seeds=24

arm                        median
POS_BIO_1                +0.22976
POS_BIO_2                +0.03223
NEG_NULL_0               +0.00010
NEG_TECH_1               +0.00048
NEG_TECH_2               +0.02314
NEG_GEO_1                +0.01829
NEG_ACC_1                +0.00501
NEG_ANCHOR_1             +0.01143
NEG_DONOR_1              +0.00076
NEG_HELDOUT_1            +0.00037
NEG_SEMANTIC_TWIN        +0.22976  <- NON_IDENTIFIABLE_BY_DESIGN

A. REPRESENTED_NUISANCE_SPECIFICITY   (M_MIN=0.01, one-sided LCB95)
   family         margin      LCB95   pass
   NULL         +0.03230   +0.03184   PASS
   TECH         +0.00932   +0.00768   FAIL
   GEO          +0.01482   +0.01349   PASS
   ACC          +0.02638   +0.02418   PASS
   ANCHOR       +0.01960   +0.01852   PASS
   DONOR        +0.03176   +0.03098   PASS
   HELDOUT_NOT_USED_IN_DESIGN   +0.03145   +0.02987   generalises (held out)

B. IDENTIFIABILITY_BOUNDARY: NEG_SEMANTIC_TWIN median +0.22976 vs POS_BIO_1 +0.22976 -> identical=True

detectability LCB95 +0.03184  ordering_ok=True
VERDICT: {"A_represented_nuisance_specificity": "FAIL__TECH", "detectability": "PASS", "B_identifiability_boundary": "NON_IDENTIFIABLE_BY_DESIGN (not a failure)", "gate_may_proceed": false}

######## MUTATION: no_qc_residualization
   NULL         +0.02805   +0.02740   PASS
   TECH         +0.00635   +0.00490   FAIL
   GEO          +0.01457   +0.01294   PASS
   ACC          +0.02392   +0.02116   PASS
   ANCHOR       +0.01786   +0.01628   PASS
   DONOR        +0.02801   +0.02692   PASS
   HELDOUT_NOT_USED_IN_DESIGN   +0.02837   +0.02665   generalises (held out)
detectability LCB95 +0.02740  ordering_ok=True
VERDICT: {"A_represented_nuisance_specificity": "FAIL__TECH", "detectability": "PASS", "B_identifiability_boundary": "NON_IDENTIFIABLE_BY_DESIGN (not a failure)", "gate_may_proceed": false}

######## MUTATION: no_control_matching
   NULL         +0.03256   +0.03193   PASS
   TECH         -0.20110   -0.20532   FAIL
   GEO          -0.14928   -0.15565   FAIL
   ACC          -0.08564   -0.09004   FAIL
   ANCHOR       +0.01290   +0.00910   FAIL
   DONOR        -0.32820   -0.33329   FAIL
   HELDOUT_NOT_USED_IN_DESIGN   +0.03407   +0.03268   generalises (held out)
detectability LCB95 +0.03193  ordering_ok=False
VERDICT: {"A_represented_nuisance_specificity": "FAIL__TECH,GEO,ACC,ANCHOR,DONOR", "detectability": "FAIL", "B_identifiability_boundary": "NON_IDENTIFIABLE_BY_DESIGN (not a failure)", "gate_may_proceed": false}

######## MUTATION: pooled_scoring
   NULL         +0.02901   +0.02840   PASS
   TECH         +0.00725   +0.00573   FAIL
   GEO          +0.01549   +0.01385   PASS
   ACC          +0.02493   +0.02204   PASS
   ANCHOR       +0.01875   +0.01730   PASS
   DONOR        +0.02920   +0.02799   PASS
   HELDOUT_NOT_USED_IN_DESIGN   +0.02947   +0.02551   generalises (held out)
detectability LCB95 +0.02840  ordering_ok=True
VERDICT: {"A_represented_nuisance_specificity": "FAIL__TECH", "detectability": "PASS", "B_identifiability_boundary": "NON_IDENTIFIABLE_BY_DESIGN (not a failure)", "gate_may_proceed": false}

[exited with code 0]
```

Full run is in, and it's a **stop**.

**Bash** Extract sensitivity arms and the common-support selection stress

IN

```
PY=/c/Users/dushy/anaconda3/envs/sea-ad-jepa-v3/python.exe
"$PY" - <<'PY'
import json
d=json.load(open("D:/jepa_v5_outputs_20260925/v63_t2/primary/V63_E2_TOURNAMENT_V2.json"))
A=d["A_REPRESENTED_NUISANCE_SPECIFICITY"]
print("VERDICT:", json.dumps(d["VERDICT"]))
print("\nper-family with sensitivity arms:")
for f,v in A["families"].items():
    print(f"  {f:8s} LCB95 {v['lcb95']:+.5f}  M_MIN(0.010)={'PASS' if v['passes_M_MIN'] else 'FAIL'}"
          f"   0.005={'PASS' if v['passes_sensitivity']['0.005'] else 'FAIL'}"
          f"   0.020={'PASS' if v['passes_sensitivity']['0.02'] else 'FAIL'}")
cs=d["common_support"]; ss=cs["SELECTION_STRESS"]
print(f"\nCOMMON SUPPORT: {cs['linked_after_trim']}/{cs['linked_before_trim']} retained "
      f"({100*(1-cs['trim_fraction']):.1f}%), strata {cs['strata_with_common_support']}/{cs['strata_total']}")
print(f"  retained {ss['n_retained_linked']}  discarded {ss['n_discarded_linked']}")
print("  standardised mean differences (retained - discarded):")
for k,v in sorted(ss['standardised_mean_differences'].items(), key=lambda x:-abs(x[1]['standardised_mean_difference'])):
    smd=v['standardised_mean_difference']
    tag = "MATERIAL" if abs(smd)>0.25 else ("modest" if abs(smd)>0.10 else "negligible")
    print(f"    {k:22s} SMD {smd:+.3f}   retained {v['retained_mean']:+8.3f}  discarded {v['discarded_mean']:+8.3f}   {tag}")
print(f"  worst |SMD| = {ss['worst_abs_smd']} on {ss['worst_variable']}")
PY
```

OUT

```
VERDICT: {"A_represented_nuisance_specificity": "FAIL__TECH", "detectability": "PASS", "B_identifiability_boundary": "NON_IDENTIFIABLE_BY_DESIGN (not a failure)", "gate_may_proceed": false}

per-family with sensitivity arms:
  NULL     LCB95 +0.03184  M_MIN(0.010)=PASS   0.005=PASS   0.020=PASS
  TECH     LCB95 +0.00768  M_MIN(0.010)=FAIL   0.005=PASS   0.020=FAIL
  GEO      LCB95 +0.01349  M_MIN(0.010)=PASS   0.005=PASS   0.020=FAIL
  ACC      LCB95 +0.02418   M_MIN(0.010)=PASS   0.005=PASS   0.020=PASS
  ANCHOR   LCB95 +0.01852   M_MIN(0.010)=PASS   0.005=PASS   0.020=FAIL
  DONOR    LCB95 +0.03098   M_MIN(0.010)=PASS   0.005=PASS   0.020=PASS

COMMON SUPPORT: 146/960 retained (15.2%), strata 145/4704
  retained 146  discarded 814
  standardised mean differences (retained - discarded):
    log10_distance         SMD +0.346   retained   +4.448  discarded   +4.341   MATERIAL
    distal_accessibility   SMD -0.229   retained   +0.243  discarded   +0.459   modest
    promoter_degree        SMD +0.142   retained   +7.014  discarded   +6.629   modest
    re_density             SMD +0.119   retained   +2.106  discarded   +1.932   modest
    anchor_frequency       SMD -0.119   retained   +1.906  discarded   +2.095   modest
    promoter_activity      SMD -0.017   retained   +0.128  discarded   +0.146   negligible
  worst |SMD| = 0.3461 on log10_distance
```

Decisive, and it answers your attrition question in the direction you were worried about. Writing it up.
