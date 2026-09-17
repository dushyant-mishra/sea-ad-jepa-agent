# JEPA masking exploratory spike — 2026-09-17

**Status: EXPLORATORY_THROWAWAY_MASKING_SPIKE_NOT_AUTHORITY.** No production masking authority, mask fraction, or training authority is created by this experiment.

## Data and design

- Frozen 50,000-cell discovery expression sample, 104 donors, HVS/NPH52/SEA_AD.
- Deterministic 800-address common-core subset; 32 targets; 4 source-stratified donor-held-out folds.
- Every targeted strategy starts from the *same* random base mask and performs burden-preserving swaps.
- Score: source-balanced mean of per-donor, donor-centered prediction correlation squared; bounded [0,1], lower is better.
- Fresh ridge attacker after masking. Positive planted-shortcut and within-donor shuffled negative controls included.

## Matched-burden results (cap 8)

| burden | strategy | U mean | mean drop | relative drop | median paired drop | win rate | treated cases | treated mean drop | treated win rate |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 10% | TOP8 | 0.0689 | 0.0088 | 12.7% | 0.0039 | 82.8% | 128 | 0.0088 | 82.8% |
| 10% | RIDGE8 | 0.0689 | 0.0099 | 14.4% | 0.0061 | 84.4% | 128 | 0.0099 | 84.4% |
| 10% | PREFIX3 | 0.0689 | 0.0080 | 11.6% | 0.0000 | 46.1% | 60 | 0.0170 | 98.3% |
| 15% | TOP8 | 0.0686 | 0.0087 | 12.7% | 0.0045 | 87.5% | 128 | 0.0087 | 87.5% |
| 15% | RIDGE8 | 0.0686 | 0.0094 | 13.7% | 0.0058 | 82.8% | 128 | 0.0094 | 82.8% |
| 15% | PREFIX3 | 0.0686 | 0.0075 | 11.0% | 0.0000 | 46.1% | 60 | 0.0161 | 98.3% |
| 20% | TOP8 | 0.0678 | 0.0084 | 12.4% | 0.0034 | 82.0% | 128 | 0.0084 | 82.0% |
| 20% | RIDGE8 | 0.0678 | 0.0091 | 13.4% | 0.0058 | 81.2% | 128 | 0.0091 | 81.2% |
| 20% | PREFIX3 | 0.0678 | 0.0077 | 11.3% | 0.0000 | 43.8% | 60 | 0.0164 | 93.3% |
| 30% | TOP8 | 0.0659 | 0.0076 | 11.5% | 0.0031 | 79.7% | 128 | 0.0076 | 79.7% |
| 30% | RIDGE8 | 0.0659 | 0.0078 | 11.8% | 0.0043 | 85.2% | 128 | 0.0078 | 85.2% |
| 30% | PREFIX3 | 0.0659 | 0.0066 | 10.1% | 0.0000 | 41.4% | 60 | 0.0142 | 88.3% |

## Cap efficiency at 15% burden

| cap | strategy | mean drop | relative drop | treated mean drop |
|---:|---|---:|---:|---:|
| 8 | TOP8 | 0.0087 | 12.7% | 0.0087 |
| 8 | RIDGE8 | 0.0094 | 13.7% | 0.0094 |
| 8 | PREFIX3 | 0.0075 | 11.0% | 0.0161 |
| 4 | TOP8 | 0.0056 | 8.2% | 0.0056 |
| 4 | RIDGE8 | 0.0059 | 8.6% | 0.0059 |
| 4 | PREFIX3 | 0.0048 | 7.0% | 0.0102 |

## Controls

At 15% burden, the planted shortcut is suppressed strongly by all targeted strategies (paired score drop about 0.837–0.839), while the shuffled negative-control deltas are approximately zero (within about ±0.0001). PREFIX3 masks the planted partner in every fold and does nothing on the negative control.

## Interpretation

The most promising successor candidate is **PREFIX3 with a common random base mask and cap 8**. It is selective: it acts only when three-way cross-fitted discovery finds evidence. Across cap-8 burden settings it acted on 60/128 target-fold cases and, where it acted, reduced held-out shortcut predictability by about 0.014–0.017 absolute with an 88–98% win rate. Overall mean improvement was smaller because untreated cases cancel exactly, which is desirable.

**RIDGE8 is the strongest simple fallback**: it produced the largest overall mean improvement at 10–20% burden (about 13–14% relative) and was positive in roughly 81–84% of target-fold comparisons, but it always spends all 8 targeted slots even when evidence is weak. TOP8 was close but slightly weaker.

Cap 4 retained only about two-thirds of cap-8 benefit, so cap 8 appears useful in this exploratory slice. The effect was slightly stronger at 10–20% burden than at 30%, suggesting there is no reason from this spike to prefer a heavy base mask. Production burden remains a separate authority question.

## Limits

This is not FULL104: it uses the frozen 50k discovery sample and an 800-address common-core universe. It does not cover native/non-common-core support, production geometry, a nonlinear JEPA-capacity attacker, or the full 41,238-address search space. Results should be used only to choose what to preregister and test next on FULL104.
