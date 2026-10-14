# Lineage-composite production synthetic V3 self-audit — Round 1

Date: 2026-10-14
Reviewed object: `docs/superpowers/specs/2026-10-14-lineage-composite-production-synthetic-design-v3-amendment.md`
Reviewed branch head before repair: `283e305eb55eae95ca334091389c74222ae6af20`

Verdict: `FAIL_WITH_CORRECTABLE_AMBIGUITY__IMPLEMENTATION_OFF`

## Audit method

Hostile review against:
- PR #324 cold-start operator checklist;
- PR #324 next-action queue;
- PR #325 successor guardrails;
- V2 design and review delta;
- frozen V79/V80 non-rescue law;
- the architecture requirement to separate biological evidence from measurement depth.

## Passed checks

V3 correctly:
- preserves V79 historical failure and V80 frozen-package independence;
- imports V80-style estimability/abstention principles without copying seeds or thresholds;
- keeps `NUMERICAL_FAILURE` out of controller biological truth;
- binds real-distribution calibration to provenance and non-authority;
- separates measurement-domain OOD from biological novelty;
- preserves observation-operator causal ordering;
- retains 41,238-address binding and authority-off boundaries.

## Defect found

### R1-D1 — biological-evidence response can be misread as measurement thinning

The draft says the biological-evidence curve may use evidence subsets derived from one full observation. Without a stronger constraint, an implementation could generate the 20/40/60/80/100% evidence levels by thinning counts or capture depth. That would make the biological-evidence curve mathematically overlap the measurement-depth curve and defeat the purpose of the distinction.

Required repair:
- biological-evidence levels must change the *set or scope of biologically relevant evidence* available to the student while holding measurement quality for retained evidence fixed as closely as the interface permits;
- examples include additional lawful features, genes, modalities, context or measured channels, not count-depth thinning;
- sequencing-depth/count thinning belongs only to measurement-depth response;
- where a design cannot vary evidence independently of depth, that case is ineligible for the biological-evidence curve rather than silently confounded.

## Secondary tightening required

1. Transfer classes should be mandatory for every supported measurement-domain axis represented in the final sealed package, rather than optional under a broad `where feasible` escape hatch.
2. Empirical calibration summaries that include biological composition must be explicitly excluded from defining latent program prevalence unless a separate biological authority exists.

No implementation or planning authority is granted by this audit.
