# V79 V2_CORE qualification contract V2: DRAFT candidate (pending controller acceptance)

Date: 2026-10-11

Status: `PENDING_CONTROLLER_ACCEPTANCE__NO_WORLD_GENERATION`, with `launch_authority=false`. This becomes launch authority only after the controller accepts both the masked exact-S174 replay and this amendment. Until then there is no world generation, truth table, benchmark or qualification fit.

| item | value |
|---|---|
| draft JSON | `results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2_DRAFT.json` |
| provisional SHA-256 | `cbfa332b419f12205d26b7f1ebd645299acb9ecc7f1ed8cdccc526ebf88477b3` (`.sha256` beside it) |
| builder | `scripts/v79/build_v79_v2_core_contract.py`; `--check` rebuilds the JSON byte for byte |
| supersedes | `V79_V2_CORE_QUALIFICATION_CONTRACT_V1.json` `70edabb8…`, kept unchanged at its path as `HISTORICAL_PRE_CONTROLLER_DRAFT__NOT_LAUNCH_AUTHORITY` |

## Amendments (PR #286 controller ruling 6113874774)

| ruling | encoded as |
|---|---|
| A: continue after a scientific FAIL, with a terminal lock | The first FAIL-class gate failure irreversibly locks the combined terminal to `V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED`. Later results are labelled `POST_TERMINAL_DIAGNOSTIC__CANNOT_RESCUE_QUALIFICATION` and cannot change the FAIL, select a variant, relax a gate or authorize anything. Infrastructure, custody, poison-read and hash failures STOP immediately. |
| B: LIMIT gates | LIMIT is exactly four donor-SD **bias** gates: Q01 detection, Q01 positive, Q08 positive and Q09 positive. Their coverage gates stay hard. **Every Q11 gate is hard FAIL-class: fixed, donor and PPC.** |
| C: conventions | 0.5-SD materiality, the [0.80, 1.25] population donor-SD ratio, the Q07 donor-absent floor and the Q11 operator SD of 0.5 × donor SD are ratified for this generation only, with their scope recorded. Q11 is a **mild** omitted-operator stress: a PASS does not show robustness to larger operator effects. |
| structural support | Each world's support mask is hash-bound world truth, and unmeasured entries carry a poison sentinel. Five support-mask tests are required before generation. |
| masked calibration | Usable only because its join reproduces. The committed builder mask, the development mask and the calibration mask are all `12ad275e…`, and the builder fails closed otherwise. |

## Rebuilt gate counts and derived quantities

| quantity | V1 (pre-controller) | V2 draft |
|---|---|---|
| gates, total | 292 | 292 |
| hard statistical | 252 (264 STAT, 12 LIMIT) | **260** |
| hard rule | 28 | **28** |
| LIMIT statistical | 12 | **4** |
| Bonferroni family | all 264 statistical gates | the 260 hard statistical gates |
| α per gate | 1.894×10⁻⁴ | **1.923×10⁻⁴** |
| genes per world (smallest G with power ≥ 0.80 to detect a 0.75-SD bias) | 45 (power 0.816) | **44** (power 0.8003; t_crit 4.08; minimum significant bias 0.61 SD) |
| structural-absence genes per world | 5 | 5 |
| fits | 1,080 | **1,056** (about 13.6 h estimated before retries; still to be replaced by the engineering benchmark) |

Why G moved: the multiplicity rule now counts only hard gates. That makes α slightly larger, and the frozen precision rule then needs one gene fewer. No threshold, prior, world or model term was changed.

The V2_CORE term set is unchanged. Whether it stays frozen is the controller's decision after reviewing `docs/agent/V79_S174_STRUCTURE_REPLAY_V4_MASKED_RESULT_20261011.md`.
