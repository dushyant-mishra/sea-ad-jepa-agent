# JEPA V5 masking successor exploratory package — 2026-09-17

**Status: EXPLORATORY_SUCCESSOR_EVIDENCE_NOT_AUTHORITY. TRAINING OFF.**

This package preserves the ChatGPT-side masking candidate search performed after the corrected V2 FULL104 lane closed with a non-interpretable primary qualification metric.

## Authority context

Current corrected V2 authority lane:

`authority/v5-masking-shortcut-predictability-v2-20260916 @ 8abd3fd6f7036fdea2a00682b1e0059c449c60f6`

Disposition:

`V2_PRIMARY_QUALIFICATION_METRIC_NOT_INTERPRETABLE__NO_MASKING_AUTHORITY`

That lane found a small correctly signed treated-subset signal but could not create masking authority because the frozen mean of unclipped partial R² was pathologically dominated by its unbounded negative tail and discovery remained below minimum-n requirements.

## What this successor spike changed

The exploratory successor tests fixed the two measurement-design problems exposed by V2:

1. **Common random base masks**: U and targeted conditions start from the same random mask; targeted conditions only perform deterministic burden-preserving swaps.
2. **Bounded paired score**: source-balanced mean of held-out, donor-centered prediction correlation², in [0,1], lower is better.

## Current lead candidate: RIDGE8

RIDGE8 in this spike:

1. donor/source-balanced molecular screening on outer-training donors;
2. keep 64 screening candidates;
3. fit ridge (`alpha=0.01`) on lawful molecular values;
4. select 8 largest absolute ridge coefficients;
5. deterministically swap those 8 addresses into the same random base mask at matched burden;
6. evaluate a freshly fit held-out donor attacker using only visible addresses.

Exact 8-target x 4-fold scale stress:

| address universe | mean bounded-score drop | target-cluster bootstrap 95% CI | relative drop | target win | row win |
|---:|---:|---:|---:|---:|---:|
| 800 | 0.01076 | [0.00594, 0.01692] | 13.53% | 100% | 90.6% |
| 2,000 | 0.00692 | [0.00299, 0.01162] | 8.06% | 87.5% | 87.5% |
| 6,000 | 0.00636 | [0.00390, 0.00885] | 6.88% | 100% | 93.8% |

Controls at 6,000 addresses:

- planted shortcut: source rank #1 in 4/4 folds; mean score drop 0.3633;
- within-donor shuffled negative: mean delta -0.000240, median -0.000221.

## PREFIX3 status

PREFIX3 looked attractive at 800 addresses because it was selective, but the strict floor/reduction version loses action and effect with address-universe scale:

- 800: 43/128 action rows, overall drop 0.01293;
- 2,000: 31/128, drop 0.01034;
- 6,000: 15/128, drop 0.00185.

Therefore PREFIX3 is **not** the lead candidate.

## Immediate next work

1. Run the prepared exact **32-target** RIDGE8/TOP8 comparison at 6,000 addresses; cluster uncertainty by target.
2. If it remains positive, freeze a prospective FULL104 successor contract **before** inspecting FULL104 successor outcomes.
3. FULL104 successor should compare paired U vs RIDGE8 vs TOP8, use common random masks, bounded paired scoring, target-clustered uncertainty, and an address-universe ladder. Include planted positive and shuffled negative controls.
4. Do not promote 10–15% mask burden, cap 8, RIDGE8, or any spike threshold to production authority merely because this exploratory sample is positive.
5. Keep training off and protected/D_shared outcomes sealed while masking and other V5 authorities remain open.

## Directory map

- `analysis/v5_masking_successor_spike_20260917/reports/` — human-readable initial spike and scale-stress reports.
- `analysis/v5_masking_successor_spike_20260917/RESULTS_BUNDLE_20260917.txt` — complete text bundle of exploratory result CSVs.
- `analysis/v5_masking_successor_spike_20260917/SCRIPTS_BUNDLE_20260917.txt` — complete text bundle of exact exploratory scripts used/prepared in the ChatGPT environment. Paths point to `/mnt/data/jepa_spike_work`; adapt paths when rerunning elsewhere.
- `analysis/v5_masking_successor_spike_20260917/provenance/` — heavy-input hashes, omitted heavy derived assets, and execution caveats.

The package manifest provides integrity hashes for preserved artifacts.
