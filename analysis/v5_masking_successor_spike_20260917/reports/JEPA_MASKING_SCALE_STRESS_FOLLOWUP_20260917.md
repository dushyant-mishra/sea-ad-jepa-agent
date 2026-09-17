# JEPA masking scale-stress follow-up — 2026-09-17
Exploratory spike only; not production masking authority.
## Main finding
The strict PREFIX3 candidate loses action/effect as the address universe grows, but RIDGE8 remains positive at 800, 2,000, and 6,000 addresses under paired common-random masks and a bounded held-out donor score.
## Strict PREFIX3 scale stress
- 800 addresses: action rows 43/128, action targets 16/32, overall delta 0.0129, acted delta 0.0385, acted win 97.7%.
- 2,000 addresses: action rows 31/128, action targets 12/32, overall delta 0.0103, acted delta 0.0427, acted win 90.3%.
- 6,000 addresses: action rows 15/128, action targets 10/32, overall delta 0.0019, acted delta 0.0158, acted win 73.3%.

## RIDGE8 exact ridge-attacker scale stress
- 800 addresses: mean bounded-score drop 0.0108 (target-cluster bootstrap 95% CI 0.0059 to 0.0169); relative 13.5%; target win 100.0%; row win 90.6%.
- 2,000 addresses: mean bounded-score drop 0.0069 (target-cluster bootstrap 95% CI 0.0030 to 0.0116); relative 8.1%; target win 87.5%; row win 87.5%.
- 6,000 addresses: mean bounded-score drop 0.0064 (target-cluster bootstrap 95% CI 0.0039 to 0.0089); relative 6.9%; target win 100.0%; row win 93.8%.

These exact ridge stress runs use 8 targets x 4 donor folds; the broader correlation-based scale screen used 32 targets and also remained positive through 6,000 addresses.

## Controls at 6,000 addresses
- Planted shortcut: source ranked #1 in 4/4 folds; mean attack-score drop 0.3633.
- Within-donor shuffled negative: mean delta -0.000240, median -0.000221; no positive masking effect is manufactured.

## Candidate decision
Carry RIDGE8 forward as the lead exploratory candidate, with TOP8 as a simple comparator and U as the paired control. Do not promote PREFIX3 as lead: under the strict floor/reduction rule its action rate collapses from 43/128 at 800 to 15/128 at 6,000 and its overall effect shrinks accordingly.

RIDGE8 definition in this spike: donor/source-balanced correlation screening to 64 candidates on training donors, ridge fit on lawful molecular values, choose the 8 largest absolute ridge coefficients, then deterministically swap those addresses into the same random base mask at matched burden. Outer held-out donors are used only for evaluation.

## Caveat
This establishes a locally credible candidate, not FULL104 production authority. The exact ridge 6,000-address stress has only 8 distinct targets; FULL104 qualification should prospectively expand target count and address universe before any production decision.
