# V2B student-facing validation boundary after Macha #507 — October 29, 2026

**State:** NEW VERSIONED **FIXTURE-ONLY** public student gate; #502 old teacher-aware validator remains rejected for student-facing use. No externally authenticated source rights, no real training or G7.

## Independent RED, preserved without modifying original tests

Macha #507 exact head `a4894f366b9d73df03a675d0b70383dea6a36454`, original review test blob `d59814301715bbffe3e07501fe7be305358140cc`; its targeted CI `40908327307` reports 4 RED/19 PASS on original #502 head `0789247cdbbdfca671613b020865aba958dfd699`. Two RED classes:

- **Public teacher issuance oracle.** The #502 shared validator checks whether an arbitrary teacher candidate digest is in `_VIEW_BINDINGS`. An adversary with only the student view can enumerate 1024 possible teacher values; exactly one candidate validates and reveals hidden q values (7,23). This is NOT a teacher-hash disclosure; no teacher digest needs to be published.
- **Uncommitted source rights and query.** The producer accepts an arbitrary caller-supplied rights ladder. A swapped base right or a decoy query can expose hidden biological evidence while a student-view receipt still claims the same semantic status. No independently pinned source policy exists. Removing the digest allowlist alone does not authenticate a policy.

The original #507 tests and PR #502 source remain unchanged. Existing ChatGPT #503/#508 passes refer to historical **fixture mechanics**, NOT student-facing security qualification.

## Separate V2B public API — what changes

New `observation_v2b_public_student_gate_v1.py::validate_public_student_v2b(student_view, expected_policy)`:

- Checks **only** `STUDENT_BASE_RIGHTS` before digest, content or issuer lookup. Every constructed/issued/forged teacher view has the same role refusal regardless of hidden teacher data.
- **Never reads** `B._VIEW_BINDINGS` or a teacher digest. The result contains a public **policy-only** hash over query ID/base rights/address→right mapping, no source-cell roster, private physical total, teacher commitment, per-cell count or source hash.
- Reuses original exact-type snapshot and V2 shape checks, requires distinct bound-content input schema and exact student visible digest. Independently supplied expected policy must include query ID, frozen address/right universe, base rights, complete cell/source/donor/operator roster and per-operator physical measurement state (as a fixture claim).
- Refuses student leakage into non-base scalar states, query relabels, missing source cell/address coverage, donor/source/operator substitutions, incompatible physical state masks and D1 sum/count inconsistencies **against that separately supplied policy**. The #507 1024-teacher-candidate attack is re-executed against the new API, and every teacher candidate yields the identical refusal. Both student output and every student-constructible candidate response stay invariant under altered hidden q.
- Does **not** establish the policy is external/authenticated. A hostile caller supplying *its own forged policy* can produce a consistent view. Every acceptance receipt sets source-rights/feature/donor/physical/QC/teacher/real-training authentication flags FALSE. This is a material source-custody limitation, not merely a missing test.

## Unchanged risks/decisions

The older #502 public validator is **unsafe for student use** and remains RED under original Macha #507 tests. It must not be deployed, imported at a student boundary or used as a public teacher-candidate oracle. #503's private pair intentionally relies on privileged process-local teacher issuance and must execute only in a separate private actor. Python module naming does not enforce operating-system isolation; real student and issuer must run in disjoint trust/OS process contexts and private issuer data must not be imported by student code.

Macha #509 exact head `3e5694e2c1b959c8e21f9fc6dd50cbf694ac4013` corrects #492 final mapping table custody and identifies 18 legacy/current alias pairs, 11 candidate query addresses at D1 risk, NPH52 symbol-only/off-ledger identities and inherited selection. **Decision:** NPH52 symbol-only *negative clearance is prohibited*; real NPH52 query issuance blocked until independently reviewed exact alias/identifier and QC contract. Quarantined reader-fit NPH52 expression is **not authorized** without separate access approval. Metadata-only selection/QC crosswalk may proceed. SEA-AD regional observations are nested within donors; donor between-person inference must account for repeated within-donor specimens, not treat matrices as independent donors.

**Stop state:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
