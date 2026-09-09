# T0 V20 Stage 3 independent review — 2026-09-09

Status: `T0_STAGE3_TERMINAL_OBSERVED__INTERNAL_SUPPORT_RECORDED__FULL_EVIDENCE_BYTE_REVIEW_PENDING`

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

## Review caveat 2 — final evidence bytes are not committed on the T0 branch

The terminal commit records the following artifact identities:

- adjudication decision SHA-256: `a36081705ed17f3f4656f742ea1e65d8e955a05eaf13cb7a607af01938a36a03`;
- Stage 3 run summary SHA-256: `9aa4abbf0e213464d207533e2412d74177b3cc1712a77e6a0aad71bbce1b9ed4`;
- confirmation access manifest SHA-256: `af884f3de7e37d8eba89139cc2ffdd48a664faf92d6b0738cf6ebac9807012ac`;
- tail package root: `c84a76b02d2a29cfc070b04161800d2b7c9b503321b9258bc5c256b55a1597bc`;
- pretarget authority root: `3b0b16a364ff1430e28d496ea5586ff1aaf1b2fce58bbe5367c26678b6c6e618`;
- preadjudication authority root: `ba87764fa7419eda1119744f206242d0440dc8f41772e3259b87f75f61611f8c`;
- confirmation matrix SHA-256: `4246b93be338ca935f13666f1be490b541c7f410f7301bf4a1536399af81ba10`;
- confirmation endpoint-values SHA-256: `3098f7e289d4c14b5c0f57ef98c76004dd92c36d38f0d306881a7779e402a8a7`.

However, the result commit itself is empty and the Stage 3 decision/run-summary/access-manifest bytes are not present in the current Git tree. Their exact-byte replay therefore cannot yet be independently repeated from GitHub alone.

## Review caveat 3 — frozen adjudicator reporting omission

The `qc_ok=False` return path of the frozen adjudicator omits `state_composition` and `state_measurements` from the emitted decision object even though those sensitivities are computed and are required for `SUPPORTED_INTERNAL`.

The result commit states that both sensitivities cleared their frozen directional 0.05 criteria. Because the returned decision omits those fields, the exact supporting statistics must be reviewed from the Stage 3 execution evidence once those bytes are available. This is a reporting defect, not evidence here of a changed decision rule.

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

Obtain or commit the exact Stage 3 run-summary, decision, access-manifest, and sensitivity-supporting evidence bytes under their recorded SHA-256 identities, then perform exact-byte independent replay/readback. Until then, the scientific terminal is recorded as internally supported with the caveats above.
