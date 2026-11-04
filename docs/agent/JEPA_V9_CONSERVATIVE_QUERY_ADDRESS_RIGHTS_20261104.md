# JEPA V9 — conservative original-source query-address restriction (2026-11-04)

**Status:** author-proposed code repair; independent Macha exact-head review required. No authenticated real issuer, biological target, deployment authority, production fit, pathology, or Stage4 permission.

## Why this is a separate small change

Original Macha source PR #513 at `0b1af4f06ba423753899e7c564d3b16ce609ac6a` generated the read-free alias adjudication:
`results/target_discovery/unified_qualification_v1/JEPA_MACHA_ALIAS_CLASS_ADJUDICATION_20261030.json`.
Its exact data-support judgment is conservative. Same-strand overlap **does not prove gene-feature identity**. The original #514/#515 Macha hostile witnesses (preserved Git blobs
`8647c07a893d932ffa5f05a79be50c89c3c28b53` and `2a63a753081012e10a9c6cb39b80e79d16848ebe`) demonstrated untrusted self-supplied policies and a specific query/D1 alias leak; these original tests remain byte-identical.

## Narrow fixed query constraints

At existing `observation_d1_base_only_student_v2c_fixture_v1.py` **producer** and independent `observation_v2c_standalone_student_gate_v1.py` **student verifier**, refuse the following queried Ensembl addresses:

| Original #513 constrained object | Address(es) | Current action |
|---|---|---|
| UBE2R2-AS1 vs historical LINC01251 / RP11-384P7.6 source holder | `ENSG00000235481`, `ENSG00000233776` | **Reject either query** until a trusted source policy can jointly withhold/resolve the class |
| MIR4307HG | `ENSG00000257612` | **Reject query**, any operator; ambiguous historical replacement |
| LINC02588 / NOVA1-DT | `ENSG00000257842` | **Reject query**, any operator; ambiguous historical replacement |
| Shared unresolved chr14 legacy holder | `ENSG00000258081` | **Reject query** as a conservative closure of the MIR4307HG/LINC02588 ambiguity |

Version-suffixed Ensembl query tokens receive the same refusal. The check is source-read-free, uses only frozen identifiers, does not change the on-disk source feature mapping, does not edit physical totals, and does not infer equivalent count features from genomic overlap. It blocks a **query address in an operator**, not every unrelated feature in the entire operator.

## Exact limits still open

1. Original source alias/feature identity, operator support, donor/specimen lineage, depositor QC and query-independent cell selection remain issuer-dependent. A self-supplied manifest or the hardcoded negative list cannot authenticate the source.
2. Other pairs in #513's 18-pair adjudication are not thereby resolved. NPH52 remains quarantined by its existing rights decision; HVS/SEA-AD D1 source eligibility is not a real G7 admission.
3. A source with an unrecognized alias or false query identifier can still make a self-consistent forged view, because no independent issuer is present. The negative list is a local conservative eligibility gate, not a complete cryptographically authenticated rights closure.
4. The historical #514/#515 tests asserting **acceptance** of the two now-repaired alias classes are retained byte-for-byte at their original blob SHAs and historic PR refs. They are explicitly deselected *only on the current source head* as superseded limit characterizations; the new positive-refusal regressions must pass instead. Every other original applicable Macha hostile test remains active.
5. Real target C2/C3 and source-to-CaseBundle bindings still require prospective evidence under the existing PR338 gates. No extra Level4 count reads, ETL, synthetic world, model or GPU campaign was initiated.

## Red-to-green / independent review contract

The original #514/#515 alias limit witnesses are positive evidence that, at main `28cbe3b23cfcbd4365b2b7cf19f7b7ea8c0fd1bb`, both dangerous queries were accepted. The new
`tests/v5/td_unified/test_conservative_query_address_rights_20261104.py` requires rejection at both entrypoints **even for a self-consistent, rehashed counterfeit student view**, across all five exact addresses and versioned forms, plus a lawful unrelated-query control.

Run with the existing matrix/hostile CI and preserve the two original reviewer-test Git object SHAs. Report the exact new PR head, workflow/job status and any tests intentionally deselected. Macha independently attempts address substitutions, operator overrides, default-argument side doors, version/symbol alias bypasses and q-dependent source cell-selection leaks; the last class cannot be honestly closed by the current synthetic APIs alone.

**Scientific/training lock:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
