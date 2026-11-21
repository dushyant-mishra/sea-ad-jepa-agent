# Macha V2C review delta — 2026-11-02 (append-only)

**Status:** `REVIEW_EVIDENCE_ONLY__NO_AUTHORITY_CHANGE`.

**Scope.** This is the independent tests-only review of ChatGPT #514 (standalone V2C) and #515 (D1 → V2C). It modifies no implementation file and no historical RED test. It rewrites no October 28 frozen document. It supersedes the line "No submitted independent PR review as of inspection" in `JEPA_20261102_QUALIFICATION_HANDOFF_RECONCILIATION.md` by appending, not by editing that file.

**Machine record:** `results/target_discovery/unified_qualification_v1/JEPA_MACHA_V2C_514_515_REVIEW_DELTA_20261102.json`.

## Frozen references (no drift when the review started)
| PR | Role | Head |
|---|---|---|
| #514 | reviewed: standalone V2C | `63099f6b17b14bcfcfd92b0334bf564e9cf8376d` (V2C blob `360d3bcc54142deb32f17d3dee44cfb902d62fe6`) |
| #515 | reviewed: D1 → V2C | `fa06d486d5f8a130ff545690a8f0b12773c4f85d` (producer blob `edee1b8adc1b5c7ca660d52d3667d2020abdb417`) |
| #507 | historical RED | `a4894f366b9d73df03a675d0b70383dea6a36454` (test blob `d59814301715bbffe3e07501fe7be305358140cc`) |
| #512 | historical RED | `16b5bc6c050222c592f88c35dc65b0a256d65402` (test blob `1a915431f871520841de551bae85729695433639`) |

The legacy #502 module (`02c703d0`) and #510 module (`6955bb8e`) are byte-identical at #510, #514 and #515.

## Review PRs
| Review PR | Base | Head | Files |
|---|---|---|---|
| [#516](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/516) | #514 branch | `881194aec9d99a9d42cbf206ffcb779429c4e768` | new `test_v2c_standalone_student_gate_514_macha_review_red.py` (blob `8647c07a`); #507 and #512 files carried byte-identical; `macha_514_515_mutation_audit.py` (blob `b57d03a0`); workflow `td-v2c-macha514-review-red.yml` |
| [#518](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/518) | #515 branch | `32c0a22b9ae6220ed03fe7d6e944da753c0e4a0c` | new `test_d1_v2c_composed_515_macha_review_red.py` (blob `2a63a753`); workflow `td-d1-v2c-macha515-review.yml` |

## Verdicts
| Question | #514 (V2C) | #515 (D1 → V2C) |
|---|---|---|
| Fixture consistency | **`REPAIR_REQUIRED`** | **`ACCEPT_SCOPED`** for the composition delta only. The head inherits #514's `REPAIR_REQUIRED`, and must be rebased and rechecked. |
| Student runtime isolation | **`NOT_TESTED`**: `STUDENT_PROCESS_ISOLATION_NOT_YET_DEMONSTRATED` | **`NOT_TESTED`**: same |
| Source-rights authentication | **`NOT_AUTHENTICATED`** | **`NOT_AUTHENTICATED`** |
| Real human-source issuance | **`BLOCKED`** | **`BLOCKED`** |

## Contradicted by a reproducible attack (#514)
Both defects are in V2C's entry guard: `dict.get(student_view, "view_kind")` is read twice on the caller's live dict, before `_snap`, and the role is never re-checked on the snapshot.
1. **Attacker code runs before the snapshot.** A top-level key whose hash equals `hash("view_kind")` makes the lookup call the key's own `__eq__`. `RuntimeError`, `LookupError` or `ZeroDivisionError` escapes in place of `StudentV2CRefusal`. This contradicts the module's own "strict snapshot before any potentially attacker-controlled dispatch" and the author's hostile-value test. Nested positions are safe.
2. **The receipted snapshot's role is never checked.** A key that swaps the value between the two reads, plus a value whose `__ne__` restores `TEACHER_RICHER_RIGHTS`, yields a `STUDENT_ONLY_CONTENT_POLICY_CONSISTENT_NO_AUTHORITY` receipt for a **teacher-labelled** snapshot. No withheld value is exposed, but "accepts STUDENT_BASE_RIGHTS only" is false for the receipted bytes.

**Suggested repair (ChatGPT implements on a new head):**
1. Refuse unless every top-level key is an exact `str`, checked without dispatch.
2. Read the role once.
3. Re-require `view["view_kind"] == "STUDENT_BASE_RIGHTS"` on the snapshot.

In the local mutation audit this repair gives 58/58, and no GREEN test regresses.

## Mechanically demonstrated (fixture scope)
**#514 (V2C, 54 GREEN):**
- **Oracle closed.** I submitted 2,049 candidates in each of 4 worlds that differ only in hidden query counts:
  - 1,024 teacher-labelled guesses;
  - 1,024 guesses relabelled as student;
  - each world's true teacher view.

  Responses are identical across worlds, and each family gets one constant refusal.
- **Runtime purity.** Validation raises zero audit events; a positive control confirms the hook works. The module holds no mutable state.
- **Binding.** Eleven policy substitutions and fourteen view-content changes each either move the commitment or are refused.
- **D1 rule.** Depths that include query, collision, off-ledger or whole-library mass are refused.
- **Hostile objects.** 29 unsupported objects at 10 positions, and hostile keys at 5 nested positions, are refused without dispatch.
- **Canonical collision.** The encoder's CR/CRLF→LF fold cannot be reached by accepted input.

**#515 (D1 → V2C, 28 GREEN):**
- **D1 rule.** D1 equals the measured base-right sum in 300 random worlds (129 accepted, 171 D1=0 refusals), and never the physical total.
- **Hidden-mass invariance.** 120 worlds × 6 hidden-mass variations give identical bytes.
- **Injection.** Injected query, withheld, collision, structural and off-ledger counts at 1,027 values get one refusal. The only change is at the canonical 2^53 edge. Extra quantity fields are refused.
- **Import graph.** At runtime the composed path loads exactly the two new modules; it loads no legacy or teacher-aware module and raises zero audit events.
- **States.** The four observation states stay distinct.
- **Forgeries.** Seven forgeries move the commitment and never yield a `True` authentication flag.
- **Entry guard.** The #514 entry defect cannot be reached through the producer.

## Unqualified: external source or execution authority does not exist
These are synthetic counterexamples, and they pass while the boundary is open.
- **Self-supplied policies.** A coherent self-supplied policy and view pass. Receipts are unkeyed digests and can be minted for views V2C refuses.
- **Alias classes.** The policy cannot express alias classes. The #513 provisional table is **not enforced**:
  - MIR4307HG (`ENSG00000257612`) is accepted as a query;
  - with UBE2R2-AS1 (`ENSG00000235481`) as the query and legacy holder `ENSG00000233776` in base, the student recovers the hidden query exactly from D1.
- **Query-dependent roster selection.** A genes-detected floor that counts the query changes the roster, so the student learns the query was detected.
- **Pseudo-address.** A self-declared pseudo-address makes D1 equal the physical total.
- **Support matrix.** A wrong support state turns structural absence into a measured zero.
- **Execution.** No deployment artifact exists, so `STUDENT_PROCESS_ISOLATION_NOT_YET_DEMONSTRATED`.
  - **Search:** the #515 tree, and every remote branch updated since 2026-10-30, were searched for consumers of V2C. Only the module, its tests, the two author workflows and the author doc reference it. The only container files are `docker/scenicplus/*`, which are unrelated. `src/sea_ad_jepa/v4/teacher_student_runtime.py` (last changed 2026-09-08) does not reference V2C.
  - **Launch:** under the author's own `python -I -S -B` verifier-only launch, student code imports the #502 teacher-aware module and the producer from the readable tree, and reads a teacher-private file written by another process.

## CI receipts (GitHub Actions)
| Review head | Run | Matrix | Result |
|---|---|---|---|
| #516 `881194ae` | 41497294200 `inherited-514-unchanged` | ubuntu/windows × numpy 1.26.4/2.2.6 | 145 pass ×4 |
| #516 `881194ae` | 41497294200 `macha514-review` | same | preserved #507 + #512 at 14 RED / 40 ×4; new file at **4 RED / 54** ×4 |
| #516 `881194ae` | 41497293990 Task 2 / 41497293798 Task 3 sweeps | ubuntu | 18 failed / 739 passed; the failures are exactly these 18 RED tests |
| #518 `32c0a22b` | 41497402803 `inherited-515-unchanged` | ubuntu/windows × numpy 1.26.4/2.2.6 | 220 pass ×4 |
| #518 `32c0a22b` | 41497402803 `macha515-review` | same | **28 pass** ×4 |
| #518 `32c0a22b` | 41497402680 Task 2 / 41497402649 Task 3 sweeps | ubuntu | 748 passed |

**Local results:** identical counts on Windows (numpy 2.4.6 and 1.26.4) and WSL Linux (numpy 1.26.4). The mutation self-audit is local evidence only.

## Governance boundaries preserved
These are unchanged by this review:
- D1 selected and D2 excluded;
- UBE2R2-AS1 shares a provisional rights class with its legacy predecessor;
- MIR4307HG and LINC02588 blocked for affected query issuance;
- NPH52 quarantined expression not opened;
- SEA-AD `sample_id` is nucleus-level;
- `JEPA_SOURCE_RIGHTS_ISSUER` has no signing identity, and none was invented;
- the 322-artifact ETL audit and physical source data were not reopened.

## Next
1. **ChatGPT:** repair the V2C entry guard on a new head, rebase #515 onto it, and do not edit #516/#518 or any historical RED file.
2. **Macha:** independently recheck the repaired head with #516 unchanged, then the rebased #515 with #518 unchanged.
3. **External:** a student deployment artifact with an enforced filesystem and process boundary, and a provisioned source-rights issuer. Neither may be self-generated.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
