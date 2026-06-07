# v2.1 Named Biological Programs

This interpretation layer groups the v2.1 Graph-JEPA outputs into readable biological programs. It combines latent-axis decoding, cross-checks against the `fine_bridge_06` AT8-sensitive checkpoint, Jacobian sensitivity, and multi-target counterfactual stability.

These are model-implied programs, not validated disease mechanisms.

## Program 1: Lysosome / Phagocytosis Routing Axis

Evidence:

- The top predictor-Jacobian edges in both `upgrade_fine_08` and `fine_bridge_06` are annotated as lysosome/phagocytosis-linked latent factors.
- The module counterfactual is one of the strongest multi-target effects.
- It increases predicted GFAP, Iba1, and NeuN while lowering predicted A beta/6e10.

Interpretation:

This appears to be a core microglial state-routing axis in the Graph-JEPA predictor. It may encode phagocytic/lysosomal remodeling rather than a simple “bad disease” direction. Its opposite signs across targets are important: the model treats this program as protective or amyloid-clearing for A beta/6e10, but aligned with gliosis/Iba1 and higher NeuN prediction.

Representative genes/modules:

- `CTSD`, `CTSB`, `CTSS`, `CD68`, `LAMP1`, `LAMP2`, `MERTK`, `NPC2`

## Program 2: Antigen Presentation / Immune Recognition Axis

Evidence:

- Antigen presentation is the strongest AT8-lowering and A beta/6e10-lowering module perturbation.
- It increases predicted NeuN and weakly increases GFAP/Iba1.
- `CD74` appears in the bridge model and candidate gene screens.

Interpretation:

This is one of the most intervention-like axes in the current model because it lowers both tau and amyloid predictions at module level while improving NeuN prediction. It should be prioritized for external validation, not because it is “causal” yet, but because the sign pattern is unusually coherent.

Representative genes/modules:

- `B2M`, `CD74`, `HLA-DPA1`, `HLA-DPB1`, `HLA-DQA1`, `HLA-DQB1`, `HLA-DRA`, `HLA-DRB1`, `TAP1`, `TAP2`

## Program 3: Vascular / Barrier Myeloid Axis

Evidence:

- Vascular/barrier myeloid perturbation lowers predicted AT8 and A beta/6e10.
- It increases predicted NeuN and has smaller positive effects on GFAP/Iba1.
- Earlier v1 analyses also repeatedly surfaced vascular/barrier markers.

Interpretation:

This looks like a disease-context or tissue-interface axis rather than a pure microglial activation axis. Its strongest value is as a bridge between neuropathology burden and tissue-state context.

Representative genes/modules:

- `F13A1`, `CD163`, `LYVE1`, `MARCO`, `MERTK`, `MRC1`, `MSR1`, `C1QA`, `C1QB`, `C1QC`

## Program 4: Lipid / Plaque Response / DAM Axis

Evidence:

- Plaque-response and DAM modules strongly lower A beta/6e10 and increase NeuN.
- Lipid metabolism increases AT8, GFAP, Iba1, and NeuN while weakly lowering A beta/6e10.
- `APOE`, `TREM2`, `LPL`, `PLCG2`, and `CTSD` appear across modules and decoded axes.

Interpretation:

This is a mixed disease-response axis. It likely captures plaque-associated microglial remodeling rather than a unidirectional therapeutic lever. The model sees it as amyloid-lowering but gliosis/activation-associated.

Representative genes/modules:

- `APOE`, `TREM2`, `LPL`, `PLCG2`, `CTSD`, `AXL`, `GPNMB`, `SPP1`, `TYROBP`

## Program 5: Homeostatic Surveillance Axis

Evidence:

- Homeostatic microglia perturbation increases AT8, GFAP, Iba1, and NeuN while lowering A beta/6e10.
- `P2RY12`, `CX3CR1`, and `CSF1R` remain highly interpretable candidates across outputs.

Interpretation:

This axis should not be read as “homeostasis is harmful.” It likely reflects the model moving cells toward a reference-like surveillance state, which has different predicted relationships with amyloid, tau, gliosis, and neuronal density. It is important for anchoring disease deviations and for interpreting state transitions.

Representative genes/modules:

- `P2RY12`, `P2RY13`, `CX3CR1`, `CSF1R`, `TMEM119`, `SALL1`, `GPR34`, `HEXB`

## Program 6: Stress / STAT3 / APP / BCL2 Tissue-Reactivity Axis

Evidence:

- `STAT3` and `APP` are among the strongest gene-level multi-target effects.
- `BCL2`, `HSP90AA1`, `HIF1A`, `MAPK1`, and `GRB2` repeatedly appear in decoded axes and counterfactuals.
- This program tends to move GFAP, Iba1, and NeuN upward and often moves AT8 upward.

Interpretation:

This appears to be a broad tissue-reactivity or stress-survival axis. It is not microglia-specific enough to claim a clean therapeutic mechanism, but it is important for explaining why the model links microglial expression states to tissue-level GFAP and NeuN readouts.

Representative genes/modules:

- `STAT3`, `APP`, `BCL2`, `HSP90AA1`, `HIF1A`, `MAPK1`, `GRB2`, `RHOA`

## Practical Prioritization

Near-term validation should focus on two categories:

1. Coherent pathology-lowering module hypotheses:
   - antigen presentation
   - vascular/barrier myeloid
   - complement
   - inflammatory signaling

2. Stable high-effect, interpretable genes:
   - `APP`
   - `STAT3`
   - `BCL2`
   - `TLR2`
   - `CD4`
   - `APOE`
   - `CX3CR1`
   - `CSF1R`
   - `CTSD`
   - `HSP90AA1`

## Recommendation

Stop broad tuning for now. The v2.1 model is biologically coherent enough to support a validation phase. The next strongest scientific step is frozen-encoder external validation, followed by spatial/IHC validation of the named programs.
