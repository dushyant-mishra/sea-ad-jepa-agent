# T0 V20 Stage 3 independent review — 2026-09-09

Status: `T0_STAGE3_EVIDENCE_BYTES_PUBLISHED_AND_HASH_BOUND__PRIMARY_INTERNAL_SUPPORT_RETAINED__SENSITIVITY_REPORTING_GAP_AND_REMOTE_CI_REPLAY_PENDING`

## Reviewed live branch state

Active T0 branch:
`t0/v20-pathology-blind-materialization-20260908`

Observed terminal commit:
`e7a16eae2d60faf9a5aa82d8a966f9b8c676ccc9`

Recorded terminal:
`PASS_T0_V20_STAGE3_CONFIRMATION_AND_ADJUDICATION_REPLAYED`

No downstream gate is opened by this review.

## Primary state result

Recorded decision:
`BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL`

Recorded statistics:

- permutation upper-tail p = 0.021 against frozen alpha = 0.025;
- t = 1.9078694125102356;
- beta = 124.94507515835764;
- HC3 SE = 65.48932245523241;
- n = 18 confirmation donors;
- residual df = 13;
- 9,999 permutations;
- estimable = true.

The terminal is correctly interpreted as marginal internal support, not a strong effect.

The pre-confirmation ridge-CV prediction that maximal shrinkage implied a likely null confirmation was conceptually wrong. Ridge shrinkage magnitude does not imply loss of significance for a scale-invariant t statistic: positive rescaling of the predictor inversely rescales coefficient and standard error together.

## Rare-tail result

Recorded terminal:
`RARE_TAIL_UNDERDETERMINED_MEASUREMENT`

- support gate: PASS;
- coherence gate: PASS;
- mean pairwise cosine = 0.1042159853231405;
- exact coherence p = 7.62939453125e-06;
- pathology-blind QC gate: FAIL/VETO;
- QC p_upper = 0.018;
- max mean absolute standardized contrast = 0.2946862124155104;
- 999 QC replicates over 2 decision QC metrics and 18 donors;
- tail disease test was not run.

Therefore the tail is neither supported nor rejected biologically. It is measurement-underdetermined.

## Review caveat 1 — first Stage 3 attempt stopped after confirmation AT8 was read

The first Stage 3 attempt reached the confirmation numeric AT8 reader and loaded the 18 confirmation values into process memory, then stopped because the donor-set digest was computed under the hardcoded role label `DISCOVERY` instead of `CONFIRMATION`.

The repair at:
`f98c1f8cbc1345b7a8cf0d643addd1a9bd494bc1`

made the role an explicit required keyword and changed the digest label accordingly. The failure exposed only the role-tagged donor-set digest mismatch; no confirmation decision statistic or decision artifact was produced before the STOP.

Review judgment: this is a post-access implementation/provenance repair and must remain disclosed. I do not see evidence that the repair was outcome-responsive: the fix is structurally forced by the wrong role label and does not alter endpoint, donor membership, nuisance design, ridge grid, thresholds, permutation rule, or adjudication logic. It therefore does not by itself invalidate the internal result, but it is a procedural caveat for any stronger confirmatory interpretation.

## Evidence-byte publication review — limitation closed at 2e6d8d1e

The evidence publication head is:

`2e6d8d1e33867fa90032492894c92ea4849e3e4a`

It adds 84 tracked evidence files (3,621,018 bytes) across the decision chain plus standing tests and raw-byte Git attributes. The previously published identities now resolve to committed bytes, including:

- adjudication decision SHA-256: `a36081705ed17f3f4656f742ea1e65d8e955a05eaf13cb7a607af01938a36a03`;
- Stage 3 run summary SHA-256: `9aa4abbf0e213464d207533e2412d74177b3cc1712a77e6a0aad71bbce1b9ed4`;
- confirmation access manifest SHA-256: `af884f3de7e37d8eba89139cc2ffdd48a664faf92d6b0738cf6ebac9807012ac`;
- tail package root: `c84a76b02d2a29cfc070b04161800d2b7c9b503321b9258bc5c256b55a1597bc`;
- pretarget authority root: `3b0b16a364ff1430e28d496ea5586ff1aaf1b2fce58bbe5367c26678b6c6e618`;
- preadjudication authority root: `ba87764fa7419eda1119744f206242d0440dc8f41772e3259b87f75f61611f8c`;
- discovery target root: `b29429021b551f3b26dadbc5ee20f57cec4e84cccc483943b73602f5bcfad8fe`;
- discovery authority root: `9806de382c75f7a7a12bb952631ed0b6c9b458250e8161a876b470c48898f6f7`;
- donor-role root: `db8680e6cef3e0d26ee117a2acbd10ba1f681a53401008128a9bb7a2e6c478e0`.

The committed decision bytes reproduce the primary statistics and the tail QC veto exactly. The evidence manifest records 84/84 blob-to-disk byte equality and excludes only the two reproducible matrix NPZ caches, whose matrix identities remain digest-bound in the run summaries. The branch also applies `-text` to all thirteen evidence directories and tests committed blob bytes rather than merely re-hashing the producer worktree. That is the correct defense against the earlier CRLF digest failure.

This closes the prior missing-evidence-byte limitation. There is no GitHub Actions run attached to the publication head, however, so the producer-suite claim remains local until an independent checkout/CI replay executes the standing tests.

## Remaining review caveat — frozen adjudicator sensitivity-reporting omission

The `qc_ok=False` return path of the frozen adjudicator omits `state_composition` and `state_measurements` from the emitted decision object even though those sensitivities are computed and are required for `SUPPORTED_INTERNAL`.

The result commit states that both sensitivities cleared their frozen directional 0.05 criteria. Because the returned decision omits those fields, the exact supporting statistics must be reviewed from the Stage 3 execution evidence once those bytes are available. This is a reporting defect, not evidence here of a changed decision rule.

## Remaining review caveat — clean-clone computation replay is not self-contained

The 84-file evidence publication is byte-complete for the emitted evidence chain, but the Stage 3 runner is not yet self-contained from a clean GitHub clone. The committed runner reaches frozen V20 conclusion modules through the external scratch authority path used by `_frozen(...)`. At publication head `2e6d8d1e...`, the branch tree does not contain at least:

- `t0_adjudicator_v1.py` / `t0_adjudicator_v2.py`;
- `t0_canonical_freeze_v1.py`;
- `t0_target_v2.py`;
- `t0_donor_role_authority_v2.py`.

Therefore an independent reviewer can verify the exact emitted decision/evidence bytes and their roots, but cannot yet recompute the entire Stage 3 scientific decision from committed code and committed evidence alone.

Required closure is provenance-only: publish the exact frozen V20 code bundle used by Stage 3, with byte identities/root and an import/replay harness that resolves only to that committed bundle. Do not modify, modernize or repair the scientific code while publishing it.

## Authority effect

Accepted now:

`T0_PRIMARY_INTERNAL_RESULT = BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL`

`T0_RARE_TAIL_RESULT = RARE_TAIL_UNDERDETERMINED_MEASUREMENT`

Still closed:

- V5 training;
- successor-u0;
- TD60;
- D1 real execution;
- DEV/SEALED;
- reader_validation / reader_oracle;
- protected populations;
- biological sweeps.

The T0 primary result may inform future evaluation priorities after governance review, but it is not a teacher/student training target and does not authorize pathology-conditioned optimization.

## Next T0 review action

Run the committed evidence-byte standing tests from a clean independent checkout/CI environment. Then publish and bind the exact frozen V20 computation modules so the scientific adjudication itself can be replayed from a clean clone. Separately preserve the frozen reporting defect: the committed decision still omits the numerical `state_composition` and `state_measurements` result objects even though `SUPPORTED_INTERNAL` depends on them. The terminal and primary/tail statistics are now byte-verifiable; the omitted sensitivity numerics are not recoverable as standalone result objects from the committed decision.

Do not rerun, retune, or widen the T0 V20 scientific procedure. The remaining work is evidence/replay hygiene only.
