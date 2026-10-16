# FULL104 donor-transport factorial preflight — September 25, 2026

**Development metadata only. No outcome inspection, FULL104 LODO refit, N1 execution, D_shared opening, or training authority.** Based on two physically SHA-256-authenticated Aug 24 local archives: `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` (`07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`) and `expression.zip` (`1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`), with embedded `FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv` SHA-256 `79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`. Local program and six locally authored fail-closed CPU checks passed; original heavyweight ZIPs and local code are **not** committed by this GitHub text-documentation PR. Obtain the companion local handoff package and verify its contents rather than inferring repo publication.

## Independently recovered structural results

| Source | donors represented in frozen 50k sample | operators | distinct exact support fingerprints | scalar addresses in every source operator |
| --- | ---: | ---: | ---: | ---: |
| HVS | 41 | 24 | 1 | 18,736 |
| NPH52 | 17 | 7 | 7 | 29,136 |
| SEA-AD | 46 | 11 | 1 | 35,076 |

Exact all-operator scalar intersection **HVS ∩ SEA-AD = 17,757**; HVS-only versus SEA-AD **979**; SEA-AD-only versus HVS **17,319**; three-source strict common core **17,186**. Nine exact observed operator-support fingerprints belong to distinct source families: source is identifiable directly from structural masks on these sampled operators. This is a structural diagnostic, NOT evidence that the eventual learned `z_bio` encodes source. The previous suggestion to restrict SEA-AD to HVS's entire 18,736-gene set would incorrectly treat 979 unmeasured SEA-AD genes as measured. Use the real 17,757-gene intersection or separately the strict 17,186 common core, without zero filling.

## Region support recovered WITHOUT expression inspection

| SEA-AD region | donors in frozen discovery sample | sampled cells | per-donor minimum | per-donor median |
| --- | ---: | ---: | ---: | ---: |
| MTG | 46 | 5,946 | 49 | 122 |
| MEC | 44 | 4,622 | 24 | 99 |
| PFC | 42 | 6,559 | 89 | 154 |

All **40** donors shared by MTG, MEC and PFC are eligible for a prospective *same-donor-population* region contrast. MTG covers all 46 SEA-AD donors and is the prespecified primary single-region candidate. The 50k discovery sample combines non-proportional A/B designs; its row counts are feasibility diagnostics only and **cannot be substituted for original FULL104 source-specific LODO inputs**.

## Predeclared prospective investigation, after historical evaluator recovery

1. Recover and independently reproduce the historical source-specific full-refit LODO evaluator, source population, weights, target, folds and scoring. Historic SEA-AD ~0.241/HVS ~0.045/NPH52 ~0.055 are **prior reported outcomes**, not results of any new experiment here. If historical details cannot be recovered, mark the new score as a different estimand, never claim direct numeric reproduction.
2. Single-region: retain the *same* evaluator on SEA-AD MTG only, with 46 donor-held-out folds. Repeat on MEC (44) and PFC (42) descriptively. Within the same **40-donor** intersection, refit separately by region and compare as a paired donor-population diagnostic, excluding the held-out donor from **every** region-specific train input.
3. Feature support: rerun both HVS and SEA-AD on the exact 17,757 jointly measured scalar genes in frozen molecular-address order. Repeat on the 17,186 strict three-source common core for a separate support comparison. Never import genes structurally absent from a cohort as observed zeros.
4. Precision: construct a fixed-seed, expression-blind HVS-versus-SEA-AD matched per-donor **full-data cell-budget** design. Choose SEA-AD donor subsets and hash-selected cell downsampling before reading any evaluation outcomes; maintain the original full 46-donor reference separately. Do not conflate the 50k sample's cell counts with full donor budgets.
5. Evaluate the combined MTG + shared-gene + matched-cell-budget contrast; explicitly record changes in target/evaluation universe and do not compare R² from different universes without a separately reported estimand difference.

A persistent SEA-AD MTG signal argues against requiring its 11-region mixture but does not establish causation. A drop after gene or cell balancing suggests support or precision sensitivity, not a biological absence in HVS. Structural-mask source separability must be measured alongside within-source biological preservation once a diagnostic representation is authorized.

## Local machine-verifiable preflight

The separately exported conversation artifact `JEPA_FULL104_TRANSPORT_PREFLIGHT_20260925.zip` contains `qualify_lodo_region_support_v1.py`, `test_lodo_region_support_v1.py`, `FULL104_LODO_REGION_SUPPORT_PREFLIGHT_V1.json`, `SEA_AD_REGION_LODO_FOLD_PLAN_V1.csv` and a detailed scientific design document. Package SHA-256 `037d9b2270720d34067ffad0b9c74596b355e154eb766ffbb60ce2cc284dab08`. Generated receipt SHA-256 `50a482c5e0410301d6a4c4a2c6bb2cb8f652d2c473ab66d14a0e85161a334ad0`; 86 metadata fold rows (46 MTG + 40 paired-region); fold CSV SHA-256 `c6349af6d64abcf013d85d3d0bfb2c31b80f2cc5c9c9b0d90e9d4a1aea65cf80`. Six CPU tests pass, including wrong archive digest, altered ZIP, no-overwrite and donor-fold identity. This PR records **derived metadata and design only**; it does not transfer physical archive bytes, authorize expression evaluation, or certify current V5 model generalization.

Historical authority: `START_HERE.md`, `JEPA_HISTORICAL_AUDITS_INDEX_20260915.md`, existing V25 handoff and current unmerged PR #123. Never revive Stage81A3 historical small-run inputs as FULL104.
