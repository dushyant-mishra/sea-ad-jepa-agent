# V79 V2_CORE qualification contract V2: FINAL (launch authority)

Date: 2026-10-11

| item | value |
|---|---|
| contract | `results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json` |
| SHA-256 | `57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26` (`.sha256` beside it; pinned in `scripts/v79/v79_v2_core_launch.py`) |
| status | `FROZEN_PROSPECTIVE_LAUNCH_AUTHORITY__NO_QUALIFICATION_FIT_RUN`, `launch_authority=true`, scope `WORLD_GENERATION_GATE` |
| controller | PR #288 ruling `6114753697`; model decision `FROZEN_UNCHANGED_AFTER_MASK_CORRECTED_S174_REPLAY` |
| builder | `scripts/v79/build_v79_v2_core_contract.py --check` regenerates this file **and** the accepted draft byte for byte |
| gate | every world generator, benchmark and runner must call `v79_v2_core_launch.require_launch_authority()` |

## What the final is

The final is exactly the accepted V2 draft (`cbfa332b…`) with finalization fields added; a test proves every other key is identical.

Added:
- `launch_authority_scope`;
- `controller_ruling` and `controller_model_decision`;
- `source_term_interpretation`;
- `accepted_evidence`;
- `qualification_worlds_generated = 0` and `qualification_fits_run = 0`;
- `finalization`.

Changed:
- `status` and `launch_authority`;
- the development finding's controller decision, now recorded as decided.

Removed:
- `launch_condition`, which has been met.

Unchanged:
- the model terms, priors, parameterization, worlds, gates, sampler and resource rules, and conventions.

## Source term

Source stays **IN** as *predictive/acquisition-source structure among estimable measured comparisons*. That is reproducible acquisition- or source-associated structure, under the existing donor/source confounding limitations.

It is **not** claimed as:
- universal source biology;
- a causal source effect;
- a biological mechanism.

The masked replay kept the structural decision but changed the magnitude. The detection source increment, read from the masking audit, fell:
- median: +0.00148 → +0.00091;
- mean: +0.0226 → +0.0090.

For a gene measured in one source only, the cross-source estimand is **UNDEFINED/UNEVALUABLE**. Such a gene is never zero-effect or positive-effect evidence for source.

## Accepted arithmetic (reproduced by the builder, and refused if it differs)

| quantity | value |
|---|---|
| worlds | 12 |
| genes per world | 44 |
| planned fits | 1,056 |
| gates | 260 hard statistical, 28 hard rule, 4 LIMIT statistical (292 total) |
| family-wise false-fail rate | 0.05 |
| α per gate | 0.05/260 = 1.923076923076923×10⁻⁴ |

LIMIT applies only to the donor-SD **bias** gates in four places: Q01 detection, Q01 positive, Q08 positive and Q09 positive. Every Q11 gate is hard FAIL. The first scientific FAIL irreversibly locks `V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED`, and every result after that point is `POST_TERMINAL_DIAGNOSTIC__CANNOT_RESCUE_QUALIFICATION`. Q11 remains a mild stress at 0.5 × donor SD.

## History (never launch authority)

- V1, `70edabb8…`: `HISTORICAL_PRE_CONTROLLER_DRAFT__NOT_LAUNCH_AUTHORITY`.
- V2 draft, `cbfa332b…`: `PENDING_CONTROLLER_ACCEPTANCE__NO_WORLD_GENERATION`.

Both are refused by the launch gate by name, by hash and by content.

No qualification world, truth table, world manifest, benchmark or fit exists.
