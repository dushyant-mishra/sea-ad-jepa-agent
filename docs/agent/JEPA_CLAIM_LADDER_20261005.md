# JEPA CLAIM LADDER — 2026-10-05

Status: `PROSPECTIVE_PROMOTION_FIREWALL__TRAINING_OFF`
Machine state: `docs/agent/JEPA_CLAIM_LADDER_20261005.json`

The project uses four distinct claim levels:

1. `RNA_REPRESENTATION`
2. `TRANSFERABLE_BIOLOGICAL_STATE`
3. `REGULATORY_SUPPORT`
4. `CAUSAL_PERTURBATIONAL_PREDICTION`

No level automatically promotes to the next, and no transitive promotion is allowed.

## Level 1 -> Level 2

A lawful recoverable RNA representation becomes a transferable biological-state claim only with **new independent semantic evidence**, relevant donor/operator/study/technology transfer evidence, and biological-unit-aware uncertainty.

Stage A and RNA self-supervision alone are insufficient.

## Level 2 -> Level 3

Transferable biological-state evidence becomes regulatory support only with independent chromatin/regulatory evidence under a prospective support rule and appropriate negatives/nulls. RNA-derived edges or same-RNA associations are insufficient.

## Level 3 -> Level 4

Regulatory support becomes causal/perturbational prediction only with intervention or perturbation evidence, experimental-unit-aware uncertainty, and a prospective causal verdict rule. Observational association and masking never identify an intervention effect by themselves.

## Explicitly forbidden inferences

- masked-RNA success -> biological validity;
- RNA/ATAC association -> regulatory qualification;
- observational prediction -> intervention effect;
- large cell count -> large biological-unit count;
- synthetic success -> real biological validation;
- donor transfer -> study/technology transfer;
- pathology-label blindness -> pathology information absent from RNA.

**Stage-A maximum claim: `RNA_REPRESENTATION`.**

Support remains support unless a prospectively frozen qualification rule says otherwise.

`TRAINING=OFF`
