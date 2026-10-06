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

## Next gate

1. Re-fetch live main before any readiness/merge claim.
2. Independent whole-branch scientific/governance review.
3. Keep PR #220 draft until that review is clean and owner direction is explicit.

Do not duplicate the runtime optimizer/EMA/checkpoint lane or Macha V77 simulator lane.
