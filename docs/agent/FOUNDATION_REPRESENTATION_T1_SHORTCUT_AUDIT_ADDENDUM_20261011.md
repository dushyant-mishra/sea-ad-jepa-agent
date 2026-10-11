# Foundation Representation V4 — Learned T1 Shortcut Audit Addendum

Date: 2026-10-11

## Custody

This addendum uses the authenticated project-mounted calibration bundle only as preserved diagnostic evidence. It does not read TEST/Morabito, pathology, target-discovery values, or held-out protected expression.

- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` SHA-256: `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
- embedded metadata SQLite SHA-256: `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`

The calibration bundle contains `FOUNDATION_TEACHER_SHORTCUT_ATLAS.csv`, a held-out-TRAIN-donor descriptive probe surface. The probe was fit on 104 encoder-fit TRAIN donors and evaluated on 45 held-out TRAIN donors. It is a diagnostic of representation content, not an intervention proving causal technical contamination.

## Learned T1 shortcut evidence

At checkpoint `u205`, the rich representation retains strong provenance/measurement predictability on held-out TRAIN donors:

- rich_H source balanced accuracy: `1.000000`
- rich_H operator balanced accuracy: `0.7632058297`
- rich_H measured-support-count R²: `0.9998000749`
- rich_H broad-annotation balanced accuracy: `0.4950178189`
- partial_H source balanced accuracy: `1.000000`
- partial_H operator balanced accuracy: `0.5213534553`
- partial_H measured-support-count R²: `0.9908710155`
- rich_CELL source balanced accuracy: `1.000000`
- rich_CELL operator balanced accuracy: `0.4839259268`
- rich_CELL measured-support-count R²: `0.9995202679`
- partial_CELL source balanced accuracy: `0.9047619`
- partial_CELL operator balanced accuracy: `0.1915752`
- partial_CELL measured-support-count R²: `0.9696955`

The associated diagnostic narrative records median `u0 -> u205` change of zero for source/operator/support targets: training did not measurably remove those shortcut signals under these probes.

The H address/operator decomposition is also highly address-dominated at `u205`:

- rich_H address-only explained variance: `0.998224`
- rich_H operator incremental explained variance: `0.001321`
- rich_H total explained variance: `0.999545`
- rich_H residual: `0.000455`
- partial_H address-only explained variance: `0.999493`
- partial_H operator incremental explained variance: `0.000365`
- partial_H total explained variance: `0.999858`

This decomposition does not neutralize the shortcut finding: near-perfect source/support decoding can coexist with small incremental operator variance because source, operator, donor, biological composition, support and acquisition geometry are not orthogonal in the corpus.

## Scientific interpretation

This evidence is a stronger and more directly learned-representation warning than the older Stage81A3 pre-learning basis diagnostics.

It supports the following current ruling:

`LEARNED_REPRESENTATION_TECHNOLOGY_INVARIANCE_NOT_QUALIFIED__SOURCE_OPERATOR_SUPPORT_HIGHLY_DECODABLE_ON_HELDOUT_TRAIN_DONORS__CAUSAL_TECHNICAL_LABEL_NOT_IDENTIFIED__CONDITIONAL_INVARIANCE_GATE_REQUIRED`

Important nuance: source/operator predictability is **not** labeled proof of a purely technical failure. Source and operator are partly aliased with donor, biological composition and measurement support. Therefore the next lawful test is conditional technology-imprint/invariance analysis that asks whether measurement identity remains recoverable after conditioning on defensible biological state/support variables.

## Consequences

- no production representation freeze;
- no claim that the current learned representation is technology invariant;
- no coordinate-specific certainty; retain subspace/block uncertainty;
- require a conditional technology-imprint gate on the final learned representation;
- retain separate biological-support and measurement-domain OOD axes;
- do not feed donor/dataset/matrix identity directly as observation descriptors;
- no training authorization is created by this audit.

`training_authorized=false`
