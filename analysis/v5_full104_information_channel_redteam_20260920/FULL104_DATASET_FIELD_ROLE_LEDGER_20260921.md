# FULL104 dataset field-role ledger — 2026-09-21

Status: **design / qualification support; no production authority changed**

Scope class: `CURRENT_FULL104_RECONNAISSANCE` for the authenticated FULL104
metadata geometry; historical 50K examples remain `HISTORICAL_SUPPORTING_ONLY`.

## Why this ledger exists

The anti-shortcut pipeline needs to understand the dataset without exposing
pathology to the model. A recurring risk is to label a column "technical" merely
because it is called an operator, batch, depth, or support field. In FULL104 that
is not safe: several such fields encode biological organization as well.

This ledger separates fields by allowed diagnostic role. It does **not** authorize
any field as a model input.

## Authenticated FULL104 geometry

The current fit population is:

- 4,553,407 cells
- 104 fit donors
- 42 operators
- HVS: 198,718 cells
- NPH52: 236,476 cells
- SEA_AD: 4,118,213 cells

The uploaded calibration bundle has SHA-256:

`07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`

and reproduces the same metadata atlas.

Operator composition is source-specific:

- SEA_AD: 11 matrices whose IDs encode brain regions
  (PFC A9, MTG, caudate, MEC, V1C, STG, ITG, FI, ANG, HIP, LEC).
- NPH52: 7 matrices whose IDs encode cell classes
  (Oligo, ExN, InN, Astro, MG, OPC, Endo).
- HVS: 24 UUID-named matrices. Their exact semantics are not declared by the
  current FULL104 bundle. In the historical 50K discovery sample, each HVS
  operator is concentrated in one native cell class; that observation is
  supporting-only but is enough to forbid assuming HVS operator is pure batch.

Therefore `operator_index` / `matrix_id` is **not** a generic technical covariate.

## Current diagnostic roles

| field | role | allowed as exact G4 nuisance-decoy stratum? | note |
|---|---|---:|---|
| `source` | `DOMAIN_NUISANCE` | yes | cohort/domain label; deliberately not called exogenous technical |
| `matrix_id` / `operator_index` | `MIXED_BIO_TECH` | **no** | SEA_AD region; NPH52 cell class; HVS semantics unresolved/mixed |
| `native_class` | `BIOLOGICAL` | **no** | biological cell-state/class information |
| `broad_class` | `BIOLOGICAL` | **no** | biological class information |
| `source_library` | `MIXED_BIO_TECH` | **no** | sequencing depth plus biological transcript mass; Audit A shows denominator biology enters normalized values |
| `support_fingerprint` | `DOMAIN_NUISANCE` | yes, for measurement-domain controls | assay/support geometry, not a biological target |
| `donor_id` | `GROUPING_ONLY` | **no** | legal grouping/split key, never a model feature or exact nuisance stratum |
| `cell_id` | `GROUPING_ONLY` | **no** | provenance/identity only |
| `stable_key` | `GROUPING_ONLY` | **no** | deterministic row key only; may seed replay but not explain biology |

Depth-, sparsity-, or QC-derived summaries are **not automatically exogenous
technical variables**. Because they depend on biological RNA content as well as
measurement mechanics, they require an explicit role decision before use.

## Consequence for G4

The required G4 decoy should be interpreted as a **nuisance-preserving
falsification control**, not proof that preserved components are biologically
empty.

Exact stratum preservation is limited to fields explicitly classified as:

- `DOMAIN_NUISANCE`
- `EXOGENOUS_TECHNICAL`

Fields classified as:

- `MIXED_BIO_TECH`
- `BIOLOGICAL`
- `GROUPING_ONLY`
- `UNKNOWN`

fail closed in the exact-decoy builder.

If a future design wants to preserve a mixed variable such as depth or region,
that must be a separately named mixed-nuisance diagnostic with a correspondingly
weaker interpretation. It must not be laundered into the "technical-only" gate.

## Pathology firewall

Understanding source study, region, cell class, support, and assay geometry is
allowed and necessary for pipeline design.

Pathology variables remain excluded from model-facing inputs and from selection of
masking policy, thresholds, margins, target universe, or repairs unless separately
authorized prospectively.

```
TERMINAL_MASKING_OUTCOMES = UNOPENED
D_SHARED                  = SEALED
PATHOLOGY                  = SEALED
DEV / SEALED              = SEALED
MASKING_POLICY_SELECTED    = NO
G5_MARGIN_SELECTED         = NO
TRAINING_OFF
```
