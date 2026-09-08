# Teacher/Student V4 Governance Repair — 2026-09-08

Status: `SOURCE_FROZEN__EXTERNAL_REVIEW_REQUIRED__TRAINING_UNAUTHORIZED`

V3 package identity remains immutable evidence. Independent local clean extraction replayed 87/87, but adversarial source review found governance fail-open conditions before execution binding. V4 is a narrow successor.

## Defects closed

1. **Independent-review PASS-prefix spoofing.** V3 used `startswith(...)` on attacker-supplied review terminals in the execution-binding overlay and u40 continuation authority. V4 requires exact canonical terminals.
2. **Checkpoint phase fail-open.** V3 capture rejected unknown phases, but restore/header validation did not. V4 rejects any phase outside `U0`, `QUALIFICATION`, `CONTINUATION` and allows runners to require an exact expected phase. Qualification requires `U0`; continuation requires `QUALIFICATION`.
3. **Overlay-consumption hardening.** Qualification/continuation consume the validator-generated overlay PASS by exact equality rather than a generic `PASS_` prefix.

## Explicit non-changes

No change to 41,238-address / 160-D / 6-block / 4-head geometry, teacher EMA semantics, predictor 15-tensor registry, 40% hidden masking, loss, AMP ordering, mandatory gradient gates, Adam-state proof, movement adjudication, schedule/population, biology firewall, or prospective relational mechanics.

## Frozen source identity

- integrated source commit: `739b6495f9c102a6d6d68f64beb37c68c42e676d`
- source manifest root: `2637fe1a4954cb26edde4f6cf79993dff4dbeb1662885bac70b150b9eb654870`
- predecessor V3 source root: `cd7faf6dd48f58387597b05f2e143ac629e1b74418d9720c4acdc9fcf4dfb584`

Training remains unauthorized.
