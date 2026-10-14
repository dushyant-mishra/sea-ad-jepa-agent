# Lineage-composite production synthetic V3 self-audit — Round 3

Date: 2026-10-14
Reviewed branch head before repair: `d8fd949bdd0cdddbe01be8d21b751b4cc6df64a3`

Verdict: `FAIL_WITH_HISTORICAL_SCOPE_PROMOTION_RISK__IMPLEMENTATION_OFF`

## Historical cross-check performed

The repository's V75 authority states:
- V73-V75 qualified a FULL104-like synthetic **measurement architecture** at 100K only;
- V75 used **96 anonymous synthetic features**;
- the canonical runtime uses **41,238 learned address identities**;
- arbitrarily assigning the 96 V75 features to canonical gene slots is scientifically invalid.

This is a direct scope boundary, not merely a stylistic preference.

## Defect found

### R3-D1 — V3 does not explicitly block feature/address promotion from V75

V3 correctly restricts V72-V75 to observation/calibration mechanics and binds 41,238 canonical address semantics, but a literal implementer could still attempt to bridge the two by assigning V75 anonymous feature identities to production addresses.

Required repair:
- V72-V75 may contribute measurement architecture, allocation, empirical QC/depth/support envelopes, fragment/multiplicity mechanics and scaling methodology only;
- their anonymous synthetic feature identities, feature count, feature-to-address mappings, planted biology and any anonymous-feature covariance topology are not address authority;
- production 41,238-address identity must come only from the current canonical production reader/registry;
- any crosswalk from historical anonymous synthetic features to canonical addresses is prohibited unless separately defined prospectively as new synthetic mechanics and cannot claim V75 inheritance;
- calibration summaries must be address-agnostic where necessary, or recomputed on authenticated current-address evidence when address-specific behavior is required.

## Historical support for Round-2 repair

TD58S also confirms the evidence/depth distinction: partial biological evidence was created by fixed gene/address masks and explicitly excluded count-depth/measurement uncertainty. This supports V3's fixed-bundle masking repair.

No implementation or planning authority is granted by this audit.
