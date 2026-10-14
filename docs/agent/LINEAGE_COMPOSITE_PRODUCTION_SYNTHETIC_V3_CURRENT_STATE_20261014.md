# Synthetic production design current state — 2026-10-14

PR #344 is now controlled by:

1. historical base design: `docs/superpowers/specs/2026-10-13-lineage-composite-production-synthetic-design-v2.md`;
2. controlling prospective amendment: `docs/superpowers/specs/2026-10-14-lineage-composite-production-synthetic-design-v3-amendment.md`;
3. preserved review/audit chain:
   - `docs/agent/LINEAGE_COMPOSITE_PRODUCTION_SYNTHETIC_V2_REVIEW_DELTA_20261014.md`;
   - `docs/agent/LINEAGE_COMPOSITE_PRODUCTION_SYNTHETIC_V3_SELF_AUDIT_R1_20261014.md`;
   - `docs/agent/LINEAGE_COMPOSITE_PRODUCTION_SYNTHETIC_V3_SELF_AUDIT_R2_20261014.md`;
   - `docs/agent/LINEAGE_COMPOSITE_PRODUCTION_SYNTHETIC_V3_SELF_AUDIT_R3_20261014.md`;
   - `docs/agent/LINEAGE_COMPOSITE_PRODUCTION_SYNTHETIC_V3_SELF_AUDIT_R4_20261014.md`.

Current V3 spec blob:
`9792acfb9b2fab8ad2a20717566c95ac5ed506d1`

Current design-review verdict:
`PASS_DESIGN_SCOPE_AND_INTERNAL_CONSISTENCY__USER_REVIEW_REQUIRED__IMPLEMENTATION_OFF`

Major V3 additions:
- explicit V79 + V80 production challenge inheritance without copying frozen benchmark bytes/thresholds;
- authenticated real-distribution calibration provenance and anti-circularity law;
- explicit V72-V75 96-anonymous-feature non-authority for canonical addresses;
- fixed-bundle biological-evidence response separated from measurement-depth response;
- held-out measurement-domain transfer separated from biological novelty;
- fail-closed 41,238 canonical address binding with no 4,096 fallback;
- new hostile tests for all of the above.

Historical boundaries remain unchanged:
- V79 permanently `NOT_QUALIFIED`;
- V80 benchmark/package frozen and qualified;
- successor estimator unqualified;
- PR #328 fixture-only;
- no target/representation/TD60/Stage4/training authority.

Next action is user review of V3. Implementation planning remains off until approval.

Terminal:
`LINEAGE_COMPOSITE_PRODUCTION_SYNTHETIC_DESIGN_V3__SELF_AUDIT_PASS__USER_REVIEW_REQUIRED__IMPLEMENTATION_OFF__TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
