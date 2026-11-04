# JEPA parallel premise-prefreeze lane checkpoint 03 — 2026-10-06

Takeover record only. No Stage-A or training authority.

Working branch: `design/premise-qualification-contract-v3-20261006`
Draft PR: `#220 — Premise qualification V3: stability, observation operator, and uncertainty prefreeze`
Current scientific branch head: `1ab08f8aab796fd9e779a66e0ac7afee42fabdb3`

## Durable package

- V3 premise design on current-main baseline.
- Neutral four-family representation tournament.
- Observation-operator contract.
- External-validation asset matrix reusing prior audits.
- Foundation-population estimand choices; none selected.
- Representation-stability protocol.
- Biological-evidence vs measurement-depth convergence protocol.
- Standalone V3 claim ladder.
- Standalone Stage-A real-RNA target/representation gate, explicitly prefreeze-only.
- Machine-readable V3 state.
- Fail-closed validator + adversarial governance tests + focused PR CI.
- `JEPA_PREMISE_V3_SELF_REVIEW_20261006.md`, explicitly self-review and not independent merge authority.

## TDD / CI history

Observed RED→GREEN cycles:

1. Initial workflow harness lacked pytest. Classified as harness defect, not scientific RED; fixed first.
2. RED: validator absent — 1 passed / 7 failed. Minimal validator -> GREEN.
3. RED: eight new scientific invariants — 8 passed / 8 failed. Targeted validator extension -> GREEN.
4. Whole-branch audit found four stale machine source-document paths. RED: 16 passed / 1 failed naming exactly four stale paths. Path-only repair -> GREEN.
5. RED: donor-ID shortcut, blanket technology invariance, estimand roster, post-hoc tempering, external-vs-independent, access-vs-exposure, pairing-class distinction, unknown-field fail-closed — 17 passed / 8 failed. Targeted extension at `660af814...` -> GREEN, run `37500945561`, job `112397471487`.
6. RED: CLI accepted a supplied corrupted state because it ignored the supplied path — 26 passed / 1 failed. CLI repaired at `223217754f16c187541278ef32eac8ca911807de`; GREEN run `37501457583`.
7. Standalone claim ladder + Stage-A contracts added. RED machine binding: 27 passed / 3 failed because verdict roster, diagnostic firewall and source bindings were absent. Machine state repaired at `8ec1a20c3b14da1d96223821aae3f62d59c2d940`; GREEN run `37501974100`.

## Frozen scientific distinctions

- `TRAINING=OFF`; Stage A execution not authorized.
- No target, representation, dimension, estimand or deciding numeric margin selected.
- Four representation families remain neutral: global, query-local, program, structured-combined.
- Technology/assay is a constrained observation operator; donor ID, unrestricted dataset ID and arbitrary matrix ID are forbidden free shortcuts.
- Universal technology unpredictability is not itself a qualification rule.
- Stable subspace != stable coordinates; coordinate semantics require axis stability after lawful alignment.
- Biological-evidence uncertainty != measurement-depth uncertainty.
- Biological-support OOD != measurement-regime OOD.
- Donor/operator/study/technology transfer remain separate.
- Target-object recoverability != biological-truth recoverability.
- Claim ladder: RNA representation -> transferable biological state -> regulatory support -> causal perturbational prediction; no automatic promotion.
- Stage A maximum claim = `RNA_REPRESENTATION`.
- Stage-A verdict roster is frozen to seven statuses.
- Fitted diagnostic readouts = inner-TRAIN only, frozen before held-donor evaluation; held-out units cannot influence fit; diagnostic fitting does not authorize JEPA training.
- External != independent; access != exposure; same-nucleus != separate-nucleus evidence; cells cannot substitute for donors; unknowns fail closed; observational multimodal support is not causal.
- Morabito protected and unavailable for target selection; TEST sealed.
- Estimand candidates remain cell-weighted, donor-weighted, source-balanced donor-weighted and hierarchical-tempered; none selected; tempering cannot be tuned on biological outcomes.

## Self-review result

Self-review found and repaired two concrete defects:

- SR-1 stale machine-readable source-document filenames;
- SR-2 CLI ignored a supplied state path.

No additional Critical/Important self-review finding remained after those repairs. This is **not** independent review.

## Independent PR #220 freeze audit — additional required changes before sign-off

Do **not** merge #220 yet, but do not reopen the entire design. Independent review has bounded the remaining work to five concrete items:

1. **Bind Stage-A verdicts + diagnostic firewall into `validate_state()`**, including adversarial supplied-file tests. Existing JSON/tests are not sufficient if the validator itself can ignore those fields.
2. **Define whole-JSON fail-closed behavior.** Prefer rejecting missing required contract fields and unrecognized contract fields instead of silently ignoring them.
3. **Expand CI path coverage** so every binding V3 governance source triggers the guard.
4. **Operationally distinguish biological-evidence removal from count-depth thinning.** `U_bio` and `U_measurement` must use demonstrably different perturbation operators.
5. **Require inner-fit/frozen alignment for held-donor coordinate-stability evaluation.** Alignment/canonical maps must fit on lawful inner TRAIN, freeze, then evaluate held donors.

Current PR #220 status should therefore be described as:

`SCIENTIFICALLY_WELL_DESIGNED_PREFREEZE_DRAFT__ADDITIONAL_BOUNDED_FIXES_REQUIRED`

Only after those five items are closed should it become:

`CANDIDATE_FOR_INDEPENDENT_WHOLE_BRANCH_PREFREEZE_APPROVAL`

Neither status is Stage-A execution authority or training authority.

## Macha / V77 update — `d76631b6d5f2f6cbf9ae57e202d9b38c4c400b32`

Branch: `claude/v77-synthetic-premise-custody-20261005`
Decision: `SUPPORTED_FOR_NEXT_STAGE__WITH_TWO_NAMED_UNRESOLVED_ISSUES`

### A_REPLICA control

A_REPLICA was frozen before the new family was built. It uses an unsupervised 50-component PCA readout that does not require planted module support.

Frozen thresholds before the reader ran:
- recoverable floor = `0.30`;
- null band = `0.05`.

First run:
- recoverable mean = `0.9821`;
- non-recoverable mean = `-0.0012`;
- DETECT = true;
- REJECT = true;
- SEPARATED = true.

This is a control/readability result, not a biological ceiling.

### Major corrected diagnosis

The synthetic-lane bottleneck was primarily the **observation model**, not the latent generator family.

The discrete block-switching family generated near-perfect latent cliques immediately (`latent transitivity 0.9649–0.9999`), but the observation layer capped observed transitivity around the same range that had limited the old factor family.

The specific culprit was the **exact per-cell detected-count constraint**. Previous variants forced each cell to detect exactly `k` genes. In real data, detected-gene count is an outcome of the cell's state and measurement process, not a hard constraint.

Removing exact top-k detection materially changed observed topology:

- previous exact-top-k: median `0.1430`, frac>|0.3| `0.0623`, transitivity `0.6885`, degree `186.9`;
- free threshold + noise: median `0.2677`, frac>|0.3| `0.4140`, transitivity `0.7590`, degree `1241.7`, largest community `0.7727`;
- free threshold/no noise: median `0.3243`, frac>|0.3| `0.5504`, transitivity `0.7990`, degree `1650.6`;
- real binarized: median `0.3770`, frac>|0.3| `0.6148`, transitivity `0.8871`, degree `1843.8`, largest community `0.7630`.

Best current setting entered the frozen transitivity envelope:
- transitivity `0.8844` vs real `0.8871`, envelope `[0.8752, 0.8928]`;
- degree `1855.9` vs real `1843.8`;
- frac>|0.3| `0.6188` vs real `0.6148`;
- T5 `0.9957` vs real `1.012`.

This means the earlier 37-candidate search over generator space was partly diagnosing an observer defect. Do not send Macha back into blind generator-only sweeps.

### Unresolved issue 1 — HIGH

A genuine abundance/topology conflict remains.

The abundance scaling that produces realistic dependence topology destroys the previously matched abundance marginal:

- max/median abundance: real `6685`; scale 1.0 `1889`; scale 0.3 `10`;
- top-1% count share: real `0.322`; scale 1.0 `0.307`; scale 0.3 `0.038`.

One scalar cannot satisfy both marginal and topology constraints.

Recommended scientific direction: **decouple gene-specific detection thresholds/capture efficiency from transcript-abundance scale**. This is biologically reasonable because capture/detection efficiency and underlying transcript abundance are distinct processes.

Resolve this before expensive world regeneration.

### Unresolved issue 2 — MEDIUM

The current two giant single-signed modules produce:
- effectively unbounded positive/negative correlation ratio vs real `1.669`;
- largest-community fraction `0.921` vs real `0.763`.

Known levers exist, but must be calibrated jointly:
- module count/sign structure affects sign balance;
- independent-gene fraction affects community size;
- more modules may lower transitivity.

Do not tune these sequentially and declare victory on one metric while breaking another.

### T5 anti-cheat guard

T5 held `0.9926–1.1128`, best `0.9957` vs real `1.012`.

This is structurally meaningful because hidden substates were drawn independently of annotated cell class, so the family cannot obtain the topology merely by separating known classes.

### Authority boundary remains unchanged

At `d76631b6`:
- no 100K rebuild authorized;
- no production-world regeneration;
- no target-selection claim;
- no generator frozen as production winner;
- no model training.

Recommended next V77 step: fix Issue 1 first by decoupling detection thresholds from abundance, then jointly calibrate module count, sign balance, and independent-gene fraction while retaining T5 and all already-frozen topology targets.

## Next gate for this premise lane

1. Close the five bounded independent-review findings on PR #220 through RED→GREEN tests where machine-enforceable.
2. Re-fetch live main before any readiness/merge claim.
3. Re-run independent whole-branch scientific/governance review after those fixes.
4. Keep PR #220 draft until review is clean and owner direction is explicit.

Do not duplicate the runtime optimizer/EMA/checkpoint lane or Macha V77 simulator lane.
