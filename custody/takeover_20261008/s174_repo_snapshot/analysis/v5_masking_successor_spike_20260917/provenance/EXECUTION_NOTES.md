# Execution notes — masking successor spike 2026-09-17

- All material in this package is **exploratory successor evidence**, not production masking authority and not training authority.
- The repository authority lane closed V2 at `authority/v5-masking-shortcut-predictability-v2-20260916@8abd3fd6f7036fdea2a00682b1e0059c449c60f6` with disposition `V2_PRIMARY_QUALIFICATION_METRIC_NOT_INTERPRETABLE__NO_MASKING_AUTHORITY`.
- The local spike used the frozen 50k discovery expression sample, not FULL104.
- Common-random base masks were used so untreated U/V2 cases cancel exactly by construction.
- The bounded evaluation score is source-balanced mean of donor-centered prediction correlation-squared; lower is better and the score is in [0,1].
- The initial 800-address spike favored PREFIX3 for selectivity, but the 800→2,000→6,000 scale stress demoted PREFIX3 and moved RIDGE8 to the lead exploratory candidate.
- Exact ridge scale stress used **8 distinct targets x 4 donor-held-out folds** at 800, 2,000 and 6,000 addresses. Do not restate those 32 target-fold rows as 32 independent targets.
- A broader 32-target correlation-based scale screen also remained positive through 6,000 addresses, but it is not the exact RIDGE8 result.
- `ridge8_6000_32_fold.py` is preserved inside `SCRIPTS_BUNDLE_20260917.txt` as the prepared exact 32-target expansion script. The 32-target exact 6,000-address run was **not completed in this session**; no corresponding result CSV exists. This is a high-priority next step before FULL104 qualification.
- Planted positive control at 6,000 addresses: planted source ranked #1 in 4/4 folds; mean bounded attack-score drop 0.3633.
- Within-donor shuffled negative control at 6,000 addresses: mean paired delta -0.000240, median -0.000221; no positive effect manufactured.
- All 16 preserved Python scripts compiled successfully in a fresh verification pass before GitHub handoff publication.
