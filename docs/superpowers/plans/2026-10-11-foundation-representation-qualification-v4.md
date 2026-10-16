# Foundation Representation Qualification V4 — Implementation Plan

1. Add RED tests for historical requalification, transfer blocking, subspace-only uncertainty, observation-ID firewall, hierarchical sampling, and dense-memory guard.
2. Implement `foundation_qualification_v4.py` as a pure fail-closed adjudicator of preserved Stage81A3 reports.
3. Implement `foundation_sampling.py` with explicit sublinear dataset/donor weighting and per-cell conditional masses.
4. Implement `foundation_resource_guard.py` with dense-byte estimation and compact-cache planning.
5. Add a small CLI that authenticates an input report hash when supplied, emits an atomic bounded JSON receipt, and never creates training authority.
6. Add focused GitHub Actions CI including the existing relevant stability/uncertainty/domain/observation tests and all new V4 tests.
7. Run independent audit against the preserved Stage81A3 report and tables; record evidence-versus-current-authority distinctions.
8. Update target-discovery audit/handoff PRs only with cross-lane references and unchanged hard authority boundaries.
9. Audit the separate FULL104 dimension lane and add only missing prospective statistical/code authority; do not fabricate physical FULL104 completion.
