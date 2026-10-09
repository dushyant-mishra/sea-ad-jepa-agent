# JEPA target-discovery new-agent takeover — 2026-10-09

Status: `CANONICAL_TAKEOVER__AUDIT_AND_CUSTODY_CONSOLIDATED__NO_TARGET_WINNER__NO_REPRESENTATION_WINNER__TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

This is the canonical first read for a new agent taking over the current target-discovery / biological-objective authority lane. It is designed to prevent redoing archaeology already completed on PR #237.

## 1. Repository and active custody surfaces

Repository: `dushyant-mishra/sea-ad-jepa-agent`

Primary handoff branch:
`handoff/jepa-20261008-complete-runtime-s174-takeover`

Primary PR: `#237`

Successor audit snapshot branch:
`audit/jepa-target-discovery-handoff-snapshot-20261009`

The audit snapshot must point at the same final commit as the handoff branch. Verify both heads before doing new work.

Canonical read order:
1. `docs/agent/JEPA_TARGET_DISCOVERY_NEW_AGENT_TAKEOVER_20261009.md` — this file.
2. `docs/agent/TARGET_DISCOVERY_AUTHORITY_RECONCILIATION_20261009.md` — current authority classification.
3. `docs/agent/JEPA_TARGET_DISCOVERY_FULL_AUDIT_HANDOFF_20261009.md` — detailed archaeology/history.
4. `custody/target_discovery_20260907_recovered/README.md`
5. `custody/target_discovery_20260907_recovered/TD34_EXACT_PANEL_BINDING_RECEIPT_20261009.md`
6. `custody/handoff_20261009/HANDOFF_CUSTODY_AUDIT_RESULT.json`
7. `custody/handoff_20261009/LOCAL_ASSET_CUSTODY_MANIFEST.csv`
8. `scripts/audit/verify_handoff_custody_20261009.py`

## 2. Governing scientific boundary

Do not infer authority from engineering qualification.

Current terminal:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Also binding:
- real biological correspondence: **UNOPENED**
- production EMA: **NOT SELECTED**
- protected TEST / Morabito / DEV / SEALED: **CLOSED**
- no production target freeze
- no representation freeze
- no multimodal training

A bounded synthetic/runtime PASS is not biological target authority.

## 3. What is already audited — do not redo without contradictory primary evidence

### S174 feature axis
The HVS/SEA-AD physical feature-axis defect is repaired/replayed in the S174 lane. Do not reopen “is S174 fixed?” as a generic blocker. The remaining historical question is narrower: whether specific decision-bearing TD56 / TD57B / TD59 products were explicitly rematerialized on corrected substrate.

### TD34 genealogy — CLOSED
TD34 exact panel genealogy is no longer open.

Recovered authentic producer:
`custody/target_discovery_20260907_recovered/td_iteration34_state_geometry_globalrow.py`

Producer SHA-256:
`1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`

Canonical upstream archive currently mounted:
- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
- bytes `410278055`
- SHA-256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`

Exact observation-state member:
`FOUNDATION_CALIBRATION_BUNDLE_20260824/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz`
- bytes `227532`
- SHA-256 `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`
- `states` shape `(42, 41238)`

Authentic TD34 rule:
1. select addresses whose observation state is `MEASURED_SCALAR` (`state == 1`) for all 42 operators;
2. obtain 17,186 common-support addresses;
3. order by `sha256("TD25|<address>")`;
4. slice first 2,048 into four ordered 512-address panels.

Exact vector hashes:
- sorted common support: `a4095c0e70141cacbcb940a2455480e9666452de4d41875360e9b4573c05a4f4`
- TD25-hash-ordered 17,186: `48b311c8abe1c25912277c2c4aaafb595035649ab7e3929bed5655167bd8a310`
- first 2,048: `13616d28a3e0c1e517b8b465e19e4ce7d209fc9e796391c041519fdcf1542b12`

Panel hashes:
- P0 `45414005bf84af3d85a2bdd5062f8c00b0163872a2f95848efaa8a55d89f4976`
- P1 `c34ec8a677c688501a5b5a4a1ab2d2d02c06610fe9f42e4c94ea973acbe2ce44`
- P2 `b7b863962dda2d68ef9c66b0b88d2ad7a0ea1578241b40dc25a3bfc2cf9b7e56`
- P3 `df5aa4d410d6f51fbcf7796ced7093d2ad807cca398ce36d9e6512651ef6a0d5`

Current classification:
`TD34_EXACT_PANEL_MEMBERSHIP_REPRODUCED__CANONICAL_UPSTREAM_SUPPORT_BOUND__SELECTION_RULE_HASH_BOUND__NO_TARGET_AUTHORITY`

**Do not spend another cycle rediscovering TD34 membership.**

### TD41–TD43
Forensic reconstruction remains a strong measurement/concordance result:
- all-42 common-scalar support = 17,186
- every TD41 panel gene and retained pair endpoint lies inside support
- support violations = 0
- TD43 reconstruction = 24/24
- terminal = `NO_TARGET_AUTHORITY`

### TD56
`HISTORICAL_RELATIONAL_EVIDENCE__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY`

### TD57B
`HISTORICAL_PROSPECTIVE_SUCCESS__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY`

### TD57C
Frozen failure remains binding:
`NO_THREE_VIEW_FINE_LOCAL_RELATIONAL_RECURRENCE__TD57C_FAIL`

HVS Panel 0 passed 2/4 frozen cases. The sequential firewall prevented NPH52, SEA_AD and Panel1 opening. Later unrestricted same-X/Y 4/4 diagnostic is post-failure and cannot rescue the frozen claim.

### TD58
`FALSIFICATION_ONLY__NO_TARGET_AUTHORITY` because the object lineage reuses quarantined TD57A material.

### TD59
Independent reconstruction reproduced all 24/24 committed rows and the recorded statistic:
`PASS_TD59_REPLAY_CLOSURE_BY_INDEPENDENT_RECONSTRUCTION__ORIGINAL_EXECUTOR_BYTES_NOT_RECOVERED`

Current authority:
`TD59_STATISTIC_REPRODUCED__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_PRODUCTION_LOCALITY_OR_TRAINING_AUTHORITY`

### TD60
Prospectively frozen, never qualifyingly executed. Do not call it failed and do not call it a winner.
`PROSPECTIVELY_FROZEN__NEVER_QUALIFYINGLY_EXECUTED__SUPERSEDED_AS_CURRENT_NEXT_ACTION_BY_LATER_TARGET_PREMISE_AUTHORITY`

### G2 / PIPELINE_ARTEFACT_m
False-alarm half was exercisable; positive-control detection sensitivity was not qualified because deciding margin was unset and no planted CONTROL_A-vs-CONTROL_B asymmetry was found.
`G2_NOT_IN_FORCE__PIPELINE_ARTEFACT_M_DETECTION_HALF_UNQUALIFIED__STAGE4_REMAINS_BLOCKED`

### Nott / liftover
Authenticated external-substrate execution exists; valid negative cohorts were produced, but `E2_NOTT_CANDIDATE = NOT INSTANTIATED`.
`EXTERNAL_SUBSTRATE_QUALIFICATION_EXECUTED__E2_CANDIDATE_NOT_INSTANTIATED__NO_TARGET_AUTHORITY`

### SCENIC+ / cisTarget
Substrate and engineering/QC exist; no completed decision-bearing regulatory network exists.
`SUBSTRATE_AND_ENGINEERING_QUALIFIED__REGULATORY_NETWORK_NOT_GENERATED__NO_DECISION_BEARING_EXTERNAL_NETWORK__NO_TARGET_AUTHORITY`

### NIH-CARD
Design/control/executor engineering exists. Real biological correspondence was not lawfully opened.
`DESIGN_CONTROL_AND_EXECUTOR_ENGINEERING_PRESENT__REAL_BIOLOGICAL_CORRESPONDENCE_UNOPENED__STAGE4_NOT_AUTHORIZED`

### Later target-premise authority
Commit `a9146d930c132978b6297722314e7af9f8507338` records V76 STOP: the synthetic state-qualification ladder has no defined objective.
Important measurements include:
- complete-H mean R² deltas T0/T1/TCTX ≈ `-0.07663 / -0.09387 / -0.09432`
- production forward gate T1 conditional row R² `0.9114` vs identity-only `0.9105`
- TCTX `0.9595` vs `0.9591`
- critics `STOP / STOP / STOP`

The runtime T1-family teacher default is not a biologically selected target.

## 4. Current chat-local custody, now recorded on GitHub

Large binary assets are not duplicated into ordinary Git history. Their fresh byte identities and replay checks are preserved in:
- `custody/handoff_20261009/LOCAL_ASSET_CUSTODY_MANIFEST.csv`
- `custody/handoff_20261009/HANDOFF_CUSTODY_AUDIT_RESULT.json`
- `scripts/audit/verify_handoff_custody_20261009.py`

The currently mounted 41K split is:
- part001: 303,979,881 bytes, SHA-256 `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`
- part002: 303,979,880 bytes, SHA-256 `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`
- streamed reassembly: 607,959,761 bytes, SHA-256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

Those values match the freshly mounted split ledger. Concatenated ZIP opening and CRC testing pass. An earlier transient inventory suggesting a 536,870,912 + 71,088,849 split is superseded for the current mounted files and must not be treated as a defect.

The two current chat-local text notes are hash-bound and interpreted in:
`docs/agent/S174_SOURCE_NOTE_RECONCILIATION_20261009.md`

Despite its filename, the current `WSL execution issue.txt` is a conceptual observation-operator / axis-stability discussion, not an S174 repair log. Do not cite it as S174 repair evidence.

## 5. What the next agent should do

Only three residual custody/provenance tasks remain worth pursuing in this lane unless new contradictory primary evidence appears:

1. **Corrected-S174 rematerialization receipts:** locate and bind explicit post-repair substrate receipts for TD56, TD57B and TD59. Do not infer these from the global S174 repair.
2. **TD59 original first-run bytes:** recover original executor/result bytes if they exist. This is provenance improvement only; successor replay already reproduces the statistic.
3. **Keep the current local-asset manifest current:** if physical files are replaced/remounted, re-run `scripts/audit/verify_handoff_custody_20261009.py` and record the new byte identities rather than silently relying on an older inventory.

Do not redo broad target archaeology. Do not redo TD34. Do not reopen Nott/SCENIC+/NIH-CARD as if their current authority classifications were unknown.

## 6. Reproduction

From a machine holding the current custody assets:

```bash
python scripts/audit/verify_handoff_custody_20261009.py /path/to/assets --json-out /tmp/handoff_audit.json
```

The verifier:
- hashes physical custody assets;
- validates both 41K parts and the streamed reassembly against the split ledger;
- binds the canonical calibration archive and observation-state member;
- reconstructs the TD34 common-support universe and all four ordered panel hashes;
- emits machine-readable PASS/FAIL;
- never confers biological/training authority.

## 7. Scientific rules for takeover

- A historical PASS is not automatically current authority.
- An engineering PASS is not a biological PASS.
- A repaired infrastructure defect does not silently repair every historical downstream result.
- A later diagnostic does not rescue a frozen prospective failure.
- Candidate evidence is not target authority.
- External substrate qualification is not target instantiation.
- Infrastructure for SCENIC+ is not a generated regulatory network.
- NIH-CARD executor engineering is not opened biological correspondence.
- Runtime mutation safety is not target validity.
- Never open protected data or real-data training from this handoff.

If future evidence changes a classification, record the primary bytes/hash, defect→repair→verification chain, supersession statement, and authority consequence explicitly.
