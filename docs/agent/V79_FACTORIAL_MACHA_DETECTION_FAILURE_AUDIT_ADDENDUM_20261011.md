# V79 factorial audit addendum — Macha detection-family failure

Date: 2026-10-11

This audit is limited to the synthetic/factorial lane. It does not perform target discovery.

## Audited upstream state

Live Macha source branch `analysis/v79-bayesian-synthetic-geometry-20261009` reached snapshot `d9d8cac6fa65463529374c50a9c309e7eb7e5405`.

Detection/Bernoulli V2 was the final precommitted parameterization. In S4, after the allowed retry and one extension, the limiting effective sample size was `362`, below the frozen minimum `400`. Under the preregistered recovery contract, that is a terminal family failure.

Audit ruling:

`DETECTION_V2_FAILED_S4__DETECTION_FAMILY_NOT_QUALIFIED__NO_V3_ALLOWED`

No threshold change, sampler rescue, or parameterization search is permitted. Completion of S0/S1 may preserve evidence but cannot reverse the S4 family failure.

## Downstream acceptance boundary

The factorial lane must reject all detection/Bernoulli-derived Macha quantities as qualified H2/H3 observation authority.

Gaussian, log-normal and ZTNB remain separate families and may continue qualification. If they pass, only the geometry they independently and lawfully identify may enter a future successor authority.

A future successor observation authority must carry the detection component explicitly as `UNQUALIFIED` unless it retains the already frozen pre-Macha observation authority unchanged. It must not substitute a provisional Macha detection fit or invent a V3.

Any material H1/H2 successor still requires:
1. prospective freeze before any factorial outcome;
2. exact byte bindings for all authority inputs;
3. fresh preexecution-only replay;
4. independent final gate audit.

## Unchanged factorial state

No H0/H1/H2/H3/C_OBS/C_BIO scientific arm has been executed. No arm is promoted. No JEPA training or checkpoint generation is authorized.

Current terminal:

`FACTORIAL_INTERNAL_ENGINEERING_CLOSED__DETECTION_FAMILY_NOT_QUALIFIED__OTHER_MACHA_FAMILIES_PENDING__FINAL_AUTHORITY_AND_BYTE_CUSTODY_GATES_PENDING__SCIENTIFIC_TOURNAMENT_NOT_RUN__TRAINING_OFF`
