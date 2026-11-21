# Event105 — Independent consolidated #590 implementation review: original V5 initialized U0 durable V2-journal quarantine, direct-writer RED→GREEN (NO TRAINING)

**Date:** 2026-11-06 (UTC). **Reviewer:** new independent takeover agent (not Sol or Macha). **Scope:** specific confirmed implementation defect and bounded repair, **not** an independent comprehensive endorsement of #590 and **not** production qualification. Prior original scientific chronology Events1–104, including complete Event90 source/data/results inventory and Event104 current first-read, remains unchanged. No historical experiments rerun.

**Absolute boundary:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`. No new optimizer, backward, EMA, model forward, GPU, restricted human RNA, V80 sealed controller, Stage4, RT1–RT8, production promotion or PR merge. Only original initialized CPU U0 model capture and synthetic fake-bytes journal tests ran.

## 1. Exact source positions, confirmed new defect

Source of the consolidated candidate: [draft #590](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/590), exact pre-review head `a3a59eb934186a8ab329eb2b0b4385b3948d1f0a`, based on Macha #588's sole canonical 35-import-source + PR547 artificial FIT contract. In `scripts/v5/jepa_v5_structured_journal_preflight_v1.py`, `_ORIGINAL_V5_U0_ONLY` was a **process-local** set. `commit_synthetic_preflight` tested this set and refused fake U1 on real V5 U0 **only through this wrapper in its opening process**. The underlying `scripts/v5/jepa_synth2048_attempt_journal_v2.py` exposed `begin_attempt` and `commit_reported_update` without reading any persistent real-V5 classification. Its `run.lock.json` held no original-V5 U0-only field. A lower-level caller in the opening process could bypass the wrapper and begin a purported update. The generic V2 writer validates a caller-reported state-bound probe but does **not** itself attest a physical optimizer/EMA step or neural model; therefore fake bytes could otherwise be committed by the lower-level path. This is a dev-journal contamination defect, **not** proof that an unauthorized real training step occurred.

## 2. Independently preserved exact-hosted RED

[draft repair PR #591](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/591), RED test-only head `1b27037aede64e8834b67a2591aa7993691fbc0a`. Original `tests/test_jepa_v5_live_model_u0_journal_connector_v1.py` has three append-only regression cases: (i) direct V2 `begin_attempt` on verified genuine original V5 initialized U0; (ii) direct lower-level fake-U1 commit refusal distinguished from merely missing a BEGIN record; (iii) a separate fresh Python interpreter checking durable U0 classification rather than unrelated process-session denial.

[Exact RED Actions run 42239689452](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/42239689452): **Python 3.11.9: 3 failed, 67 passed; Python 3.12.7: 3 failed, 67 passed.** In particular `begin_attempt` unexpectedly **did not raise**; the standalone commit without an earlier BEGIN refused merely `OUTCOME_REQUIRES_MATCHING_BEGIN`; the second process refused with `WRITER_IS_NOT_THE_OPENING_PROCESS__RESUME_NOT_AUTHORIZED`, which did not establish durable U0-only policy. The RED tests did **not** execute a neural optimizer, forward, backward, EMA or create a trained U1 checkpoint. Original failures remain in Actions history.

## 3. Minimum GREEN repair

[draft #591](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/591) exact GREEN head `ff1141fefa1377ac394be530c1236b682805e5e4`, unmerged. The V2 journal's mirrored `run.lock.json` now has **`original_v5_u0_only: true` ONLY** when strict `require_original_v5=True` validation has succeeded. This field is included in the run-lock hash used by journal records, checked in both ordinary and forensic binding readers, and cannot be lost merely because the Python process dies. The generic legacy fabricated-state journal's lock bytes are unchanged when the optional flag defaults false.

Direct `journal.begin_attempt` and `journal.commit_reported_update` now refuse this durable original-U0-only classification, including when called without the structured bridge. `_check_structure` also refuses attempted `ATTEMPT_BEGIN` or `UPDATE_COMMITTED` records for flagged runs when reviewing their hash-linked history, rather than relying only on the immediate writer API. The structured bridge persists this flag when opening genuine initialized U0. The historical in-memory gate remains defense in depth, not sole authority.

Source changes (Git blob identities at exact GREEN head):
- `scripts/v5/jepa_synth2048_attempt_journal_v2.py`: `b10dbf5a983794b79ad08b4344661d1b176a169f`.
- `scripts/v5/jepa_v5_structured_journal_preflight_v1.py`: `b348d8561414842897cd9114e4727293dc5f97fb`.
- `scripts/v5/jepa_v5_pipeline_identity_contract_v1.py`: `902bd98119f9bdce22fe20354982fffe7ac3df0f`.
- `tests/test_jepa_v5_live_model_u0_journal_connector_v1.py`: `6424095acaffc0bdb4f99e688c02dde71b42ab69`.
- `results/target_discovery/unified_qualification_v1/JEPA_V5_DEV2048_PIPELINE_IDENTITY_CONTRACT_V1.json`: `d5734123c54706a751c59c921479e600dd1a5513`.

The canonical development identity was **repinned, not bypassed**: source-manifest SHA-256 `5b03b91643cd654c7469d6af82c457f541d8029c7c0a8ab66385b3d52a0b4ec1`; canonical nonauthorizing contract SHA-256 `e3ccfa164f06ff7fd22b4d292365a12442d9fcde898f1cc8497f5d5339c8914a`. The original 35-file V5 executed closure, 2,048-gene PR547 1,440-cell/36-donor synthetic source, 48-dimensional gene identity, frozen teacher, genuine U0 initialized tensor bytes and empty AdamW slots remain as in #590.

**Exact-head GREEN:** [#591 Actions](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions?query=branch%3Areview%2Fv5-u0-durable-journal-quarantine-20261106): 13/13 workflows and **26/26 hosted jobs SUCCESS** on `ff1141fefa1377ac394be530c1236b682805e5e4`, including the 3 original hostile regressions and inherited full V2 synthetic journal and canonical source/data identity suites. They are **non-stepping**, with explicit allowlisted suites and no new real-data permission.

## 4. Exact limits and handoff

**REPAIR_AUTHOR_GREEN__INDEPENDENT_RECIPROCAL_REVIEW_PENDING.** This verifies a bounded logical separation of original initialized U0 journals from unqualified lower-level fake U1 commits, including observation of the policy from a fresh Python process. It is **not** a proof of process-crash recovery into an authorized restart path, a signed D1 external custody authority, or protection against wholesale malicious replacement of both unsigned local/external stores. A separate newly created *generic fake* journal can still hold arbitrary synthetic bytes but must not be called original V5 or production. No actual U1 training occurred or is authorized. Do not infer a qualified external teacher, true frozen physical probes, issued patient RNA rights, biology, bitwise resume or Stage4 from this fix.

The earlier #590 branch itself remains draft and unchanged; #591 is a stacked independent review/repair on it, still requiring cross-review (including the previously outstanding Macha review of #590 and reciprocal review of #591). Old #585/#589 remain precursor historical artifacts, not alternative current production identity. Original Event102 safety incident disclosure and Event95 resolved private V80 owner backup stay unchanged. The next agent should inspect any later comments/CI and record genuinely new RED→GREEN results as Event106+, preserving this Event105's exact historical receipts. Do not rerun completed source/history and do not start training.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
