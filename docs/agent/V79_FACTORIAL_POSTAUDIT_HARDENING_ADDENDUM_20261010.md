# V79 Factorial Post-Audit Hardening Addendum — 2026-10-10

## Purpose

This addendum preserves the original audited preexecution evidence in PR #256 while recording a later, still pre-outcome engineering review that found three registry-scale memory defects in the implementation branch. The original audit remains valid for the code it verified; this addendum does **not** retroactively claim that the hardening patch has passed the same verification.

## Hardening branch

- PR: #262
- branch: `fix/v79-factorial-memory-hardening-20261010`
- head at this addendum: `3419dfc9bbc0410298b21b55e2caddd07ed82a27`
- base: PR #253 head `1a0ab6e1108af924ca13e81caa3c70f3101d251c`
- scientific H0/H1/H2/H3 outcomes observed before patch: **no**
- Macha Bayesian outputs consumed by patch: **no**
- target-discovery data consumed by patch: **no**

## Defects found

Independent preexecution review identified three implementation-scale memory defects:

1. `v79_hierarchical_biology.py` accumulated full float64 cell×gene intermediates before final float32 storage.
2. `v79_observation_operator.py` materialized full dense support/base/rate/int64 count matrices at registry scale.
3. `score_v79_factorial_worlds.py` densified the complete 41,238-address count matrix for the legacy V77 endpoint and densified the full evaluation universe before HVG selection.

These are engineering defects, not scientific reasons to alter the factorial hypothesis.

## What PR #262 changes

The patch:

- generates latent abundance in cell blocks while retaining final float32 latent truth;
- samples explicit-observer counts in blocks and converts blocks immediately to CSR;
- keeps the legacy/V79 scoring path sparse through CPM-log1p variance selection and materializes only selected genes;
- preserves the frozen arm manifest, seeds, threshold family, biological/observation separation, and non-training boundary;
- is intended to preserve RNG draw order and float64 rate arithmetic where relevant.

Changed files are limited to:

- `scripts/v79/v79_hierarchical_biology.py`
- `scripts/v79/v79_observation_operator.py`
- `scripts/v79/score_v79_factorial_worlds.py`

## Verification status

The previously recorded `84 passed` and READY preexecution replay in PR #256 apply to the pre-hardening implementation.

For PR #262 at head `3419dfc9bbc0410298b21b55e2caddd07ed82a27`:

- GitHub PR exists and is draft;
- no pull-request-triggered GitHub Actions workflow runs were returned for the head at review time;
- no claim is made here that the full 84-test suite has been rerun on the hardening head;
- no claim is made here that byte-for-byte or statistic-for-statistic equivalence has been proven for all three rewritten paths;
- therefore PR #262 is **prospective candidate execution code, pending explicit equivalence and focused-test verification**.

The next agent must not silently treat the old `84 passed` receipt as applying to PR #262.

## Required verification before scientific execution

Before adopting #262 as the scientific execution substrate:

1. run the five focused V79 test files on the exact #262 head;
2. add explicit small-fixture equivalence tests comparing old vs hardened latent generation, observation sampling, HVG selection, legacy endpoint summaries, and localization summaries for the same seeds;
3. verify no full registry-scale dense materialization remains in the real execution path;
4. rerun the preexecution-only gate with the exact authority/manifest/custody files;
5. record exact head SHA, test counts, gate receipt hashes, and any changed script hashes in a successor audit receipt;
6. do **not** execute scientific H0/H1/H2/H3 outcomes until this verification closes and the Macha-integration decision below is resolved.

## Macha integration boundary

Macha's Bayesian dataset-geometry lane is separately preserved in PR #260/#261. Its current audited terminal is `SIMULATION_QUALIFICATION_INCOMPLETE`; no qualified posterior-generative authority has yet been consumed by the factorial generator.

Project direction has been clarified: when Macha's lane becomes qualified, the factorial generator should consume as much defensible identity-scrubbed posterior generative geometry as possible, rather than only a few scalar summaries. This must be frozen **before** the definitive scientific tournament. No post-outcome rescue/retuning is allowed.

## Authorization state

- scientific factorial tournament executed: **false**
- JEPA training/checkpoint generation authorized: **false**
- V78 retuning authorized: **false**
- TEST/Morabito accessed: **false**
- pathology accessed: **false**
- target discovery modified: **false**
- PR #262 verified as execution substrate: **false / pending**

This addendum is the controlling statement for work performed after the original PR #256 audit snapshot.