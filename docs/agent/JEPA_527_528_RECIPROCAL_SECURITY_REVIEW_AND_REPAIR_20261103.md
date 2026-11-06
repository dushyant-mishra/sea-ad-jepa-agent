# Reciprocal review of Macha #527/#528; GPT post-TD repair and new #529 RED — 2026-11-03

**Scope:** exact GitHub code, tests, CI and documentary interpretation. No large data re-audit, model fit, biological claims, actual real data read, newly issued source rights or training. Original historical REDs remain intact; no branch ancestry merge.

## A. Macha's hostile #527 was correct; GPT #525 was defective at its original head

Macha review-only [#527](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/527) frozen `ac9215c256275dfa35687cc7a4ac1d1d25ec34a5`; test blob `123e6c92f5dac0fb39e6d3023ec3c6093cfa56b3`. Inherited + five #517 checks pass, but re-hashing a modified internally consistent portfolio/plan bypassed semantics (13 independent RED tests, 22 failing sub-cases) at GPT #525 old `064bf2a23e0063c26072988d83626a5e24542878`. In particular C4 with C6 FAIL was accepted, teacher policies/topologies/EMAs could be forged, and controller query-specific gates could be dropped by a re-labelled query block. Macha tested original #351 and found the same original gaps; do not retcon #517's five fixes into acceptance of everything else.

GPT repair [draft #525](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/525) current **exact** `315c378d08f3266b33e04aca95a230041320b4f7`:

- New `verify_target_portfolio`: JSON/SHA snapshot + full re-derivation using existing `build_target_portfolio` semantics, not merely caller-recomputed digest; makes actual C4→C6 and C5 specialist/foundation/rare preservation rules binding at preflight and controller.
- New `verify_architecture_plan`: JSON/SHA snapshot + re-derivation by existing `build_architecture_plan` with all unprovided interference/negative transfer/multimodal authority flags **FALSE**. Forbids unsupported team/critic topologies, global factorization, altered output semantics and production EMA flag.
- Tournament and zero-update teacher-screen now invoke the portfolio verifier, preventing QUERY→SHARED gate dropping. EMA successful presentations and architecture half-life are exact integer values; the low-level diagnostic EMA formula still permits an explicitly provided finite fractional half-life, as a preexisting valid control.
- #527 original test **blob preserved byte-for-byte** in `tests/v5/test_jepa_post_td_527_macha_repair_v1.py`; #527 RED source left immutable. Also #517 original expected-RED not altered.
- [Exact-head workflow 41581922688](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41581922688) SUCCESS Python 3.11 and 3.12, **59 tests per job**, all thirteen former #527 RED and four guards green. Inherited post-TD [41581922677](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41581922677) SUCCESS, C4/C6 [41581922710](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41581922710) SUCCESS.
- First follow-up CI at `b53e5812` failed because of an author's test-file preamble before `from __future__`. Corrected by restoring Macha original test exact blob; original failed run [41581853496](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41581853496) preserved, not ignored.

**Code-repair scope, not endorsement:** The scientific `PASS` statuses in the submitted portfolio remain **caller-declared**. Re-derivation establishes that a record follows its own declared statuses, **not** that source/q rights, qualification status, producer or scientific evidence are externally authentic. Huge address integers still are not bound to a real molecular identity ledger. Macha independent fresh review on the new head requested in [#525 comment](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/525#issuecomment-6595986061). GPT cannot self-accept. Cumulative whole-system verdict `SYSTEM_NOT_READY`, separate from green fixture tests.

## B. Macha #528 corrects source-report science; GPT independently found new wrapper RED

Macha [#528](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/528) frozen `c1d85688a510f9729de3801c1cf2eb6e0e7068c9` is a five-file append-only amendment to #513 (no old physical result is modified). It correctly withdraws the earlier false "every probe hashes its inputs" claim and accurately scopes its new receipt-admission wrapper: 42 lineage shards, 8,915 meta CSVs, six HVS H5ADs and related manifests rehashed, **29 large H5ADs stat-only** (inherited identity; not current byte re-verification). Tests 13/13 green per Macha CI. This is not an independently authenticated depositor/issuer.

**Biology, documentation scope accepted as corrections, not a new human study:** 1bp+same-strand locus overlaps are only provisional conservative **query rights** restrictions, not molecular gene-identity; the three bindings apply to **11 SEA-AD** operators each (plus 5–7 NPH52 operators currently completely barred). HVS source-library/depositor median count ratio ~0.9153 is an **unexplained denominator difference**, not proof of 8.5% missing molecules. HVS nine *retained* cells at the inferred 1000-gene threshold do not bound exclusions; no confirmed prospective q-independent QC. SEA-AD matrix sums = depositor metadata is *internal consistency*, not outside provenance authentication.

**New independent GPT RED:** Reviewer-only [PR #529](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/529) exact `cf0330e4da9e9c647b22c2fc1a7445dac16da865` runs original Macha 13 green followed by **two genuine failing attacks** in [CI 41582128474](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41582128474), source unchanged:

- R01: the new wrapper checks only final `Path.is_symlink()`, not symlinked **parent directories**. A symlink `root/data` → outside root with original file bytes/sizes/mtimes and pins still returns `ADMITTED`. Violates declared no-input-escapes-data-root contract.
- R02: `run_probe` reports `ADMITTED` and writes its output even when `probe_output_equals_committed_513_output=False`. A frozen replay must fail closed or use an unmistakably quarantined **non-success** result; a boolean warning under an admitted status is insufficient.

Exact [#528 independent review comment](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/528#issuecomment-6595979005): documentary biology correction **ACCEPT_SCOPED**, wrapper **REPAIR_REQUIRED**, Macha should fix on separate author candidate and seek independent review, without altering original #529 RED.

## C. Governance and actual scientific blockers

Macha disclosed replaying two public but **outside the project-approved analytic allowlist** QC columns after receiving the prior hold: SEA-AD `Doublet score`, HVS `is_primary_data`. Record disclosure as such: it does not introduce pathology or expression reads, but **this is not retroactive permission**. Do not use wrapper `--run-probe` or re-read the two columns until the human PI decides. Admission-only mode can be evaluated under previous scopes.

#528 R1–R9 independent issuer prerequisites still need: off-agent/CI signer key and externally pinned trust root, source terms (especially NPH52 accession/terms and HVS), approved QC methods, specimen keys, operator-wise alias restrictions, physical view custody, signed eight-part D1 release and privilege separation. A shared GitHub login or SHA cannot provide independent issuer authority. No real query release, teacher target, cumulative Unified Task4 acceptance, or JEPA training.

**Separate synthetic finding remains valid:** PR #526 on original frozen PR328 shows a single fixed other-eight-gene panel measurable in 149/480 synthetic cells, not a human target; no conflation with #527/#528.

**Binding terminal:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
