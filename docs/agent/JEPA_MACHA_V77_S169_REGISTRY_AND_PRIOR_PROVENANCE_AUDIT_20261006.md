# JEPA Macha/V77 — S169 registry custody and synthetic-prior provenance audit

Date: 2026-10-06
Parent audit head before write: `647526a1da38709ea78f44d501c68714a4eb6bc8`
Macha head audited: `b1d8ca9fb0f1d03102c8e117e2792b0e3b100326`
Status: `DOCUMENTATION_ONLY__TRAINING_OFF`

## 1. S169 classification

The canonical 41,238-address registry is not present in the current tree. `v77_address_universe.py` searches repository-relative candidates and a machine-specific fallback path.

However, every candidate registry is SHA-256 checked against the frozen digest:

`7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`

A wrong registry version therefore fails rather than silently relabelling addresses.

Correct classification:

`S169 = CUSTODY_AND_CLEAN_CHECKOUT_REPRODUCIBILITY_DEFECT__NOT_SILENT_IDENTITY_DRIFT`

The focused GitHub Actions run independently verified during this audit restored the registry from historical commit `95d2cafe...`, checked its digest, and passed the 55-test plumbing suite. That is a valid recovery route, but the normal local code still depends on finding external bytes.

## 2. Biological meaning

The registry is the dictionary that says which molecular address corresponds to which gene and which source families measured it. Hash checking protects identity. Missing custody in the current tree mainly means another machine cannot reproduce the world without knowing the recovery path.

## 3. Synthetic abundance/detectability provenance is partly assumed, not purely registry-derived

The module docstring says the background is `not invented` and emphasizes registry-derived realism. This requires qualification.

The registry directly supplies:

- gene/address identity and order;
- biotype;
- number of contributing source features;
- which source families measured each address.

But the mapping from those facts to synthetic abundance and detection is manually specified in code. Examples include biotype-family parameters such as `mu`, `sd` and `det`, plus the breadth coefficient `1.6` and random detectability coefficient `0.7`.

The code itself correctly calls these values an external choice and states they were not tuned against an outcome.

Therefore the accurate provenance statement is:

`STRUCTURAL_CATEGORIES_AND_COVERAGE_ARE_REGISTRY_DERIVED__ABUNDANCE_AND_DETECTABILITY_MAPPING_IS_A_PROSPECTIVE_MODELING_ASSUMPTION`

This is not a defect by itself. Synthetic worlds require assumptions. But these priors must not be described as empirically measured real-RNA distributions unless separately calibrated and qualified.

## 4. Why this matters after S149

Because detection and coverage can manufacture correlation topology, hand-specified detectability priors are scientifically load-bearing. They can be used for controlled synthetic challenges, but agreement with a downstream graph statistic cannot validate the biological mechanism if the observation prior itself has not been independently qualified.

## Authority unchanged

TRAINING=OFF; Stage A OFF; Stage 4 NOT AUTHORIZED; TEST sealed; Morabito protected; no target, representation, evidence-object or estimand winner.
