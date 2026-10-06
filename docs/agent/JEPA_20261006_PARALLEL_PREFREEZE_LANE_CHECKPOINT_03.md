# JEPA parallel premise-prefreeze lane checkpoint 03 — 2026-10-06

Takeover record only. No Stage-A or training authority.

Working branch:

`design/premise-qualification-contract-v3-20261006`

New progress since checkpoint 02:

- `7018edea1ca58e9cfd42a5e83b625fddb5b15ad1` — draft external-validation asset matrix using existing audited evidence rather than redoing PRs #188-#199.
- `9713231e4c71c11535182ae98ec2f49d2c4636dc` — foundation-population estimand prefreeze; candidates defined but `selected_estimand=UNSET_REQUIRES_APPROVAL`.

External-asset matrix preserves these distinctions:

- external != independent;
- access != exposure;
- same-nucleus pairing != separate-nucleus donor-level evidence;
- cell count cannot rescue small donor n;
- observational multimodal support cannot establish causality;
- Morabito remains protected and unavailable for target selection;
- unresolved facts stay `UNKNOWN_REQUIRES_AUDIT`, `ARTIFACT_UNLOCATED`, `NEEDS_AUTHENTICATION`, or embargoed rather than being guessed.

Estimand candidates now explicitly include:

- `CELL_WEIGHTED_EMPIRICAL`
- `DONOR_WEIGHTED`
- `SOURCE_BALANCED_DONOR_WEIGHTED`
- `HIERARCHICAL_TEMPERED`

No candidate is selected or defaulted. Any later hierarchical tempering exponent is a scientific estimand parameter and may not be tuned post hoc on biological outcomes.

Current V3 branch progression:

1. `b149de6e...` — V3 premise design
2. `47739d86...` — representation-family tournament
3. `b17f5016...` — observation-operator contract
4. `7018edea...` — external-validation asset matrix
5. `9713231e...` — foundation-population estimand choices

Next work:

1. freeze basis/subspace stability execution protocol;
2. freeze biological-evidence vs measurement-depth convergence protocol;
3. produce machine-readable contracts only after the human-readable semantics are stable;
4. add fail-closed governance tests/validator without granting execution authority.

Parallel-lane boundaries unchanged: do not duplicate runtime optimizer/EMA/checkpoint reconciliation or Macha V77 generator work.
