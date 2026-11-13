# JEPA V8d — current successor first-session checklist, no-repeat (2026-10-27)

**Operational:** PR #460, this branch. **Historical audit:** PR #322, qualified exact head `a4c86fa83adf0cd718105807e9d254e09c989610`. **Historical-only handoff:** PR #323. No target/representation winner or Stage4/real-training authorization.

**Controlling invariant:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

## First read without re-auditing

1. This file; then PR #322 `docs/agent/JEPA_POST_V8C_DELTA_V8D_20261027.md` + machine JSON. The V8d [audit run 40539643680](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40539643680) passed **20 static hostile tests**; all 14 inherited workflows at that exact audit head succeeded.
2. The prior `JEPA_SUCCESSOR_FIRST_SESSION_V8C_20261027.md` is preserved for historical state; prior V8/V8a/V8b/V8c audit deltas and complete V8a file index remain intact.
3. Re-fetch exact heads of PRs #457–#464; PR titles and this dated snapshot cannot establish live heads after another commit. Only create V8e or later **append-only** if a changed head or new independently evidenced status matters.

## Current source and repair status (exact snapshot)

| PR | Frozen-as-of-this-handoff head | Control |
|---|---|---|
| #457 | `2fa7a4621c00e27e41c1c52afe122599d0114ae0` | Public E2G latest workflows [40538117453](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40538117453) / [40538117363](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40538117363) GREEN; fine-grain Stage75 file-upload and overlap findings **source-reported**, not independently authenticated genome build, gene IDs, direct TF binding or target validity |
| #458 | `3b08081d7fb3fa99cf1459b13cbe47d5b0962547` | Unchanged original 13 hostile PS Tasks1–2 RED |
| #459 | `57e707149b46ca011eee096f01dc08b64aeb8f9f` | Macha X1 author CI previously GREEN but independent #462 X1-S1/S2 **RED**; new author repair required |
| #461 | `495350d477a0b7ba65c13dcab5032d443f939cd5` | Eight Unified Task1 historical-canonical RED |
| #462 | `67d2336155624a8657d2ef3320c9bfff175951ee` | Two reviewer-authored Task4 short-I/O RED reproduced Linux and Windows |
| #463 | `84b05952112ca405436ee3ccf35cc1c0df53c14d` | ChatGPT candidate Unified Task1: 35 author-side tests GREEN, awaiting Macha independent assessment |
| #464 | `f6ee226c146c4c31d88ce5b845449ce21758cdeb` | ChatGPT PS Task1/2 mechanic repair: 12 scoped hostile tests GREEN and inherited compatibility; **T2-D still the sole RED across full hostile CI**; awaiting Macha incremental review |

### New external E2G evidence must stay nonauthorizing

The latest #457 report **claims** 319 Stage75 motif evidence rows from a new upstream uploaded bundle, 149 distinct TF–gene–query-peak hypotheses over 56 unique physical query peaks, and 26/149 source-reported recurrent overlaps using only 12 physical peaks. These are not 149 independent assays. The original Stage75 source upload was **not independently read in the V8d audit**; direct TF binding/causality, original genomic build and 0-based coordinate attestation, source-native external Ensembl IDs, assay independence and nonpromoter specificity remain missing. No real G7 E3, Stage75 biology gate or target authorization results.

### Reviewer/owner split

- **Macha authors #459 repair, ChatGPT independently reviews its exact new head against unchanged #462.**
- **ChatGPT authors #463 and #464; Macha independently reviews those changes** (new tests-only RED if needed, no author-test acceptance shortcut).
- Since Macha authored original PS Tasks1–2 and Task4, and ChatGPT authored subsequent repairs, neither may automatically grant cumulative non-author acceptance to those modules. Require claim-specific non-author whole-lineage review.
- **T2-D** does *not* become GREEN by replacing a handwritten attestation with a process-local Python token, self-signed key supplied by the candidate, or a strict xfail. Genuine independent immutable-tree scan issuer/trace provenance and externally anchored trust are unavailable. T2-D remains RED; no PS Task4.
- **G7** physical provenance, evidence rights, q-excluded depth and actual deciding-row digest linkage still unavailable. Previous local expression/calibration metadata probe does not prove or replace authenticated molecular observations.
- **Downstream Task5:** #451 bridge increment accepted narrowly only; #326/#332/#351 JEPA harness already exists. Tasks6–8 remain fixture-only NONE/abstain. No extra JEPA trainer, Stage4, real training, protected experiments or reopening negative Bayesian/RBB-JEPA.

## Integrity commands (run on appropriate branch)

On PR #322:
```sh
python scripts/v5/verify_jepa_lane_audit_v8.py
python scripts/v5/verify_jepa_lane_audit_v8a.py
python scripts/v5/verify_jepa_lane_audit_v8b.py
python scripts/v5/verify_jepa_lane_audit_v8c.py
python scripts/v5/verify_jepa_lane_audit_v8d.py
python -m pytest -q tests/v5/test_verify_jepa_lane_audit_v8d.py
```

On PR #460:
```sh
python scripts/v5/verify_jepa_lane_handoff_v8.py
python -m pytest -q tests/v5/test_verify_jepa_lane_handoff_v8.py
```

Do not reread/checkpoint-unpickle untrusted external binaries, copy 41K or protected artifacts into Git, mistake Windows and WSL locks for the same OS lock domain, or treat static CI as independent issuer/scientific authentication.

**Stopping rule:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
