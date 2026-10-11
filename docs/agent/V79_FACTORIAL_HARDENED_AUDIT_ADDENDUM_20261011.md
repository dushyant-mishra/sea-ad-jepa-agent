# V79 Factorial Hardened Audit Addendum — 2026-10-11

## Why this addendum exists

PR #262 advanced after the original hardened audit snapshot. The hardened implementation head is now:

`6692886231a54d75a5a9a09b94946b91d5a37961`

This addendum updates verification without rewriting the older audit record.

## New verification

GitHub Actions run `38116853466` completed successfully on the PR #262 merge test for the new head.

Focused result:

`90 passed in 0.96 s`

The new 90th test closes the main remaining equivalence gap. It compares the hardened sparse scoring path directly against the frozen pre-hardening scoring authorities on the same deterministic count matrix:

- frozen V77 legacy scorer versus `_sparse_legacy_score`;
- original V79 `build_l0_l2` versus `_sparse_l0_l2`;
- selected genes;
- V77 detection/expression/topology/abundance outputs;
- L0 pooled detection correlation and summary;
- L1 class-conditioned localization;
- L2 detected-feature and library-size localization.

Nested numerical outputs are required to agree under zero relative tolerance and absolute tolerance `1e-12`; discrete fields and arrays must agree exactly where applicable.

The workflow also continues to compare untouched PR #253 against hardened PR #262 under the same runtime. Latent/count/capture behavior remains equivalent on the frozen fixture and the integer count hash remains unchanged.

## Audit ruling

Engineering/scoring equivalence is now stronger than in the 2026-10-10 hardened audit:

- latent biology equivalence: PASS;
- observation equivalence: PASS;
- frozen HVG selection equivalence: PASS;
- frozen V77 endpoint equivalence: PASS;
- V79 L0/L1/L2 localization equivalence: PASS;
- focused CI: 90/90 PASS.

No H0/H1/H2/H3 scientific outcome was generated or read by this verification.

## Remaining preexecution custody point

A fully fresh byte-authenticated preexecution replay on head `6692886...` still requires access to the external registry and repaired-marginal authority bytes. These large custody inputs are hash-bound but are not duplicated on PR #262. The previously authenticated READY gate receipt remains preserved in PR #256 and must not be silently relabeled as a fresh receipt for the newer implementation head.

Therefore the lawful state is:

`HARDENED_IMPLEMENTATION_EQUIVALENCE_GREEN__EXTERNAL_CUSTODY_REPLAY_STILL_REQUIRED_BEFORE_DEFINITIVE_EXECUTION__SCIENTIFIC_TOURNAMENT_NOT_RUN__TRAINING_OFF`

## Macha integration policy

Macha supervision is controlled by PR #261. The controller must read Macha's live committed state first and issue only the instructions needed for the next unmet gate. Provisional Bayesian estimates remain forbidden as synthetic authority.

Once independently qualified, use the richest defensible posterior-generative geometry from corrected TRAIN. Preserve posterior distributions and uncertainty where useful. Map qualified biological geometry prospectively into H1 and qualified observation geometry prospectively into H2 while randomizing identities needed to preserve planted causal truth.

If this materially changes H1/H2, freeze a successor authority/manifest and rerun the full preexecution gate before any factorial scientific outcomes are generated.

## Canonical lane entry points

- hardened factorial implementation: PR #262
- hardened factorial audit: PR #264
- hardened factorial handoff: PR #265
- immutable earlier frozen artifact store: PR #256
- Macha Bayesian supervision: PR #261

PR #265 supersedes PR #257 as the factorial execution-review handoff.