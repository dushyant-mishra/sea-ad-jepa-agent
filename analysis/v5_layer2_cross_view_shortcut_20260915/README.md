# V5 Layer-2 cross-view shortcut audit — 2026-09-15

Full report: [`docs/agent/V5_LAYER2_CROSS_VIEW_SHORTCUT_CLOSEOUT_20260915.md`](../../docs/agent/V5_LAYER2_CROSS_VIEW_SHORTCUT_CLOSEOUT_20260915.md)

Machine-readable closeout: `V5_LAYER2_CROSS_VIEW_SHORTCUT_CLOSEOUT.json`
(sha256 `105092b41cd132a6134d548bbba26de05204e04a9af5139aae913d50122741f3`, 35 artifacts bound)

## Question

Does the V0↔V1 cross-view training objective gain predictive advantage from shared
measurement state or from coarse context, rather than from cell-level molecular structure?

## Headline

| finding | value |
|---|---|
| matched measurement-state synergy above the attenuation null | ≤ **1.09%** of full-depth cross-view R² |
| within-donor cell-level cross-view R² (molecular) | **0.185 – 0.265**, all three sources |
| same, reachable from measured QC alone | 0.021 – 0.069 |
| QC increment once V0 is present | **+0.003** |
| donor-generalisable signal (LODO, full refit) | SEA_AD **0.241**; HVS 0.045; NPH52 0.055 |
| independent reproduction, worst disagreement | **1.0e-14** |

The measurement shortcut we set out to test is ~1%. The exposure that matters is **pooling** —
across sources, and across donors in HVS and NPH52.

## Layout

```
X_CROSS_VIEW_SHORTCUT_AUDIT_SPEC.json        spec frozen BEFORE any computation (b280a1ed…)
Z_RESIDUAL_OVER_CONTEXT_SPECIFICATION.md     anti-shortcut construction — SPECIFICATION ONLY
V5_LAYER2_CROSS_VIEW_SHORTCUT_CLOSEOUT.json  machine-readable closeout
V5_VALUE_ONLY_SAME_CELL_MEASUREMENT_PREFLIGHT_RECEIPT.json   Layer-1 screen receipt (5ed97a43…)
LARGE_ARTIFACT_REFERENCES.json               big inputs by path / size / sha256, not committed
scripts/                                     every script that produced a reported number
results/                                     every reported result, as written by those scripts
withdrawn/                                   a defective implementation, retained for audit
```

## Reproduction order

Layer-1 measurement closeout: `qc_replay.py` → `w1_design.py` → `w2_audit.py` →
`g1_geo.py` → `g2_stress.py` → `g3_spec.py` → `g4_qc.py` → `g5_verify.py` → `g6_receipt.py` →
`g7_weighted.py`

Layer-2 audit: `x1_spec.py` (freeze spec first) → `x2_audit.py` → `x3_nuis.py` →
`x6_fixture.py` (**validate before use**) → `x5_within.py` → `y1_source.py` → `y2_donor.py` →
`y3_qc.py` → `y4_ln.py` → `z1_repro.py` → `z2_estimand.py` → `z3_donorrec.py` → `z5_lodo.py` →
`z6_closeout.py`

Scripts read from a session scratchpad path recorded in `LARGE_ARTIFACT_REFERENCES.json`;
repoint `S` to relocate the inputs.

## Constraints in force throughout

`TRAINING_OFF` · `NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION` · `PROTECTED_DATA_CLOSED`
No production training. No representation modification. No operator/source residualization.
No new thinning realization — `qc_post.npz` is a bit-identical deterministic replay of the
frozen screen (total deviation 0.000e+00).

## Two things a reviewer should check first

1. **`scripts/x6_fixture.py`.** Any estimator reporting signal remaining after removing group
   structure can manufacture it from nothing through inconsistent centring. The null fixture
   (operator structure, zero cell-level signal) must return ~0; ours returns −0.0068. A first
   implementation failed exactly this and is kept in `withdrawn/`.
2. **§10 of the report.** Three earlier claims are corrected there, including a headline that
   conflated pooling inflation with donor-generalisation failure.
