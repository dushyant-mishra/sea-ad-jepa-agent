# D1 base-only source → standalone V2C fixture composition — 2026-11-02

**Scope:** `IMPLEMENTED_FIXTURE_ONLY__AUTHOR_CI_NOT_INDEPENDENT_ACCEPTANCE__NO_REAL_SOURCE_ISSUANCE`. New versioned implementation branch stacked **on unchanged #514 exact head** `63099f6b17b14bcfcfd92b0334bf564e9cf8376d`, which itself is stacked on #511. Original #502, #507, #510, #511, #512, #514 and the original review tests remain untouched. This is a **new implementation increment**, not a claim that Macha's independent #514 review has already happened.

## New composed interface

- `scripts/v5/td_unified/observation_d1_base_only_student_v2c_fixture_v1.py`: `produce_d1_base_only_student_v2c_fixture(*, base_observations, expected_policy)`. It receives **previously redacted base-rights raw integer observations** and a **self-supplied, unauthenticated** exact policy. It rejects nonbase and hidden-query counts, structurally unmeasured or collision-ambiguous base scalars, invalid donor/source/operator roster rows, and zero D1. It emits a STUDENT-only complete-address fixture view containing exact D1 = sum of measured base-right counts; physical source library, off-ledger residual, teacher query count and teacher digest are absent by signature and output contract.
- This version imports **only** `observation_v2c_standalone_student_gate_v1`. It no longer references the old V2B gate, V2 bounded-content module or issuer registry. The new composed path calls `C.validate_student_v2c` internally and requires its nonauthorizing status; V2C binds its final receipt to both the **complete expected policy** and **exact view contents**.
- `tests/v5/td_unified/test_observation_d1_v2c_composed_fixture_v1.py`: source/operator and measured-zero examples, hidden-q and off-ledger/collision redaction metamorphisms, schema/rights/roster forgery tests, signed-looking-but-unauthenticated view/content warnings, malformed domain refusals, duplicate or absent cells, exact preservation of current #511 and #514 source, forbidden legacy-import source inspection and a limited standalone `python -I -S` verifier-only launch from a temporary directory.
- `.github/workflows/td-d1-v2c-composed-fixture-chatgpt-20261102.yml`: Ubuntu/Windows × NumPy 1.26.4/2.2.6; invokes new tests, inherited #514, #511, #510 author's tests on unchanged earlier code. Reviewer #507/#512 original RED remains on their own PR heads, **not overwritten or reclassified as green**.

## Security and scientific boundaries

**Not established by this implementation:** an OS-enforced student-only identity with a restricted filesystem/network, independent student/teacher service separation, inaccessible #502 source tree and teacher registry *in production*, a physically authenticated source redactor, a q-independent selected cell roster, source alias closure, donor/specimen/nucleus identity, depositor selection/QC, an independently signed source-rights issuer or actual G7 real content V2 authorization. A subprocess launched with a single module copy and Python isolated mode demonstrates that the **verifier code alone** can run without legacy modules; it does not enforce access controls in a deployed service.

**Known positive counterexamples remain:** a source-side base feature contaminated by hidden-q alias molecules, an upstream roster selected as a function of hidden q, and a caller forging counts together with a consistent `expected_policy` can yield internally consistent V2C receipts while violating true source policy. The synthetic test fixture cannot resolve these issues. Source issuers are still **UNPROVISIONED**, Macha's #512 V2B review is still **REPAIR_REQUIRED**, and #514 still requires an independently executed test-only hostile review plus actual deployed isolation. V2C remains a **consistency checker, not an authentication service**.

**Rights:** D1 selected and D2 excluded. No NPH52 quarantined expression or new nonallowlisted metadata may be read. Only three alias-query rights constraints currently bind provisionally. SEA-AD `sample_id` is nucleus-level, HVS depositor UMIs differ from deposited counts. Historical G7 V1 physical `library_size` is not D1, and #500 G7 remains fixture-only. No current target winner, representation winner, Stage4 or real training.

## Follow-up / external ownership

1. **Macha or an independent tests-only reviewer** must attack #514 V2C at unchanged head, preserve #507/#512 RED and challenge this new composition separately. An author CI PASS does not settle deployment/security authority.
2. **Student runtime security owner** must produce a real restricted executable or service artifact with verified absence of teacher-bearing #502 code, restricted runtime filesystem/capabilities and independent adversarial proof, rather than conflating a pure-import test with process isolation.
3. **External source governance** must provision an authenticated issuer and prove allowed data identities, rights, alias closure, QC, selection and donor/specimen evidence. No self-signed key is authority.
4. **Custody owner** appends this change and its exact CI results to audit PR #322, then synchronizes active PR #460 with the audited head. Avoid modifying Oct28 frozen snapshots or reopening already accepted historical work.

**Standing terminal:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
