# T0 Donor Metadata Authority Specification V1

Status: **EXTERNAL INTERFACE FREEZE — 2026-09-08**

Purpose: provide the exact age/sex inputs consumed by frozen T0 code without carrying numeric AT8 magnitude into pathology-blind stages.

Frozen source:
`data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv`

Expected source SHA-256:
`ebbe9bc0c623c663331425794bd8fb1b4c4f3657455cf55d806cc383ea6d8e3a`

Required fields:
- `Donor ID`
- `Age at Death`
- `Sex`

Production constructor must authenticate the pathology-metadata source and the accepted T0 membership before parsing; derive the exact candidate donor set from membership; extract only donor identity, age text, and sex text; and emit exactly one row per candidate donor in deterministic UTF-8 donor order.

No numeric AT8 value may be parsed, retained, emitted, summarized, ranked, or used.

Acceptance:
- 46 candidate donors before eligibility;
- exact membership donor-set equality;
- no blank/duplicate donor identity;
- age preserved for frozen `pd.to_numeric(..., errors='coerce')` semantics;
- sex preserved as source text;
- `real_execution_ready=False`.

Missing/non-numeric age and blank sex are later eligibility failures if faithfully represented. Source digest/schema/identity mismatches are global STOPs.
