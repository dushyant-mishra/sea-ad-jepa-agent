# V74 Macha full audit final — 2026-10-03

## Purpose

This document finishes the audit of the live Macha lanes named in the V74 audit-takeover handoff. It is a documentation-only audit result. It does not modify scientific code, tests, thresholds, contracts, protected data, training state, or scientific result bytes.

The audit distinguishes five evidence classes:

1. **Git-resident implementation evidence** — source/tests/contracts actually committed at the exact head.
2. **Git-resident result/receipt evidence** — machine results or receipts actually committed at the exact head.
3. **local transcript evidence** — execution reported in the supplied Macha transcript but not preserved as a Git result/receipt.
4. **historical/superseded evidence** — preserved but not current authority.
5. **open/unqualified** — missing, contradictory, or not yet reconciled.

## Exact live heads audited

- Route-B custody: `claude/v74-routeb-custody-20261002` @ `32dfcbfdcfced5683d9646e10a7db679ea9ba323`
- Lane E blacklist/scaling: `claude/v74-blacklist-and-512pilot-20261002` @ `60b0971086bc414dc14e65da59818316450a0a16`
- G2 continuous successor: `claude/v74-g2-continuous-successor-20261002` @ `03c0c48612860e4bd2f094ce54fdef9cde274490`
- stale-claim audit: `claude/v74-stale-claim-audit-20261002` @ `14326480882f5bc4618634ba7f95c94f4924437d`
- exact-sampler / ACTIVE_STATE lineage: `claude/v64-exact-sampler-successor-20260930` @ `78f13e71db968ad42486fdecb718dacd48704a5a`

The heads above were re-queried during this audit. Lane E remains exactly at `60b09710...`; no quiet-512 result commit landed after the producer commit.

## Exact-head hosted-CI audit

No GitHub Actions workflow run is attached to any of the five exact heads above.

Consequences:

- statements such as “50 tests passing; 13 mutations all proven capable of failing” are **local-execution evidence**, not exact-head hosted-CI evidence;
- the audit does not downgrade the code because hosted CI is absent, but it refuses to upgrade local handback claims into provider-backed qualification;
- a final reconciliation successor must run an exact-head hosted or otherwise independently captured suite if provider-backed execution provenance is required.

## Branch topology audit

The Macha work is not cumulative on one branch.

### Route-B vs Lane E

`32dfcbfd...` and `60b09710...` diverge from common ancestor `d5b76230c1d2837dfbf643e205c5b2780831d8f9`.

- Route-B has 9 commits on its side.
- Lane E has 13 commits on its side.
- neither contains the other's later repairs.

### G2 vs stale-claim lane

`03c0c486...` and `14326480...` diverge from `498f56a365f16ff7e8da5446e09175ceebce874f`.

Therefore there is currently **no single exact Macha head** containing Route-B custody repair, Lane-E blacklist/scaling work, G2 successor design, stale-claim repair, and the ACTIVE_STATE update.

This remains the central repository-level blocker.

---

# Audit findings

## M-A1 — Route-B code repair is real, but the expensive real rerun is not a committed result

At `32dfcbfd...`, Git contains substantive changes to:

- `routeb_extract_pseudobulk_fragments_v1.py`
- `routeb_call_peaks_and_consensus_v1.py`
- `v69_barcode_identity.py`
- new `v69_custody.py`
- new mutation driver
- new replay verifier
- `tests/test_v74_routeb_custody_v1.py`

The extractor now:

- hashes the compressed fragment bytes as they are consumed;
- stages outputs until the authenticated digest matches;
- audits barcode authority rows **before** dictionary collapse;
- binds authority files by content;
- distinguishes absent QC from measured QC failure;
- re-counts fragments per cohort barcode during the verified pass.

This materially repairs V69's circular digest linkage and post-collapse duplicate checking.

However the Git diff for the Route-B lane contains scripts/tests, not a new V74 machine result/receipt binding the reported 63.6 GB rerun. The supplied transcript reports that the real stream matched `b7c5aa2d...` and that 2,534 barcodes reconciled at 23,522,438 fragments, but that expensive execution is **transcript/local evidence**, not a committed V74 result artifact on this branch.

### Verdict

- **implementation repair:** QUALIFIED FOR REVIEW
- **real-byte rerun claim:** LOCAL-ONLY / NOT GIT-RECEIPTED
- **biological implication:** NONE

Required reconciliation action: preserve the real-run receipt or replay artifact with exact fragment digest, source SHA, per-barcode reconciliation and execution code binding before treating the real rerun as repository authority.

## M-A2 — Route-B mutation discipline is materially improved but not provider-backed

The committed test suite is behavioural rather than source-inspection-only. It includes:

- same-size/different-byte gzip mutation;
- truncation/corruption paths;
- missing digest;
- QC bound to the wrong fragment file;
- partial-scan non-authority;
- content binding checks;
- duplicate/conflict controls;
- positive controls proving clean fixtures can pass.

This is a meaningful improvement over checks that could not fail.

But no exact-head GitHub Actions run exists at `32dfcbfd...`.

### Verdict

**LOCAL TEST EVIDENCE ONLY** until independently executed/captured at the reconciled head.

## M-A3 — Route-A still has the same pre-collapse identity bug

At both `60b09710...` and `32dfcbfd...`, `scripts/v69/build_routea_cistopic_object_v1.py` still executes:

```python
guard_evidence = assert_donor_map_is_not_suffix_derived(
    dict(zip(bc["barcode"].astype(str), bc["donor"].astype(str))))
```

A conflicting duplicate barcode can therefore be collapsed before the guard sees the raw rows.

This is precisely the bug class fixed on Route B.

### Verdict

**OPEN — P0 Route-A integrity blocker.**

Required repair:

1. audit raw barcode/donor/subcluster rows first;
2. fail closed on conflicting duplicates;
3. only then build maps;
4. add behavioural duplicate/conflict tests;
5. add a mutation proving a post-`dict(zip(...))` implementation is detected;
6. produce a structured failure receipt.

No Route-A cisTopic object should be called fully guarded until this is closed.

## M-A4 — blacklist-before-consensus semantics are correct

The Route-B custody branch implements a hard blacklist-policy gate because blacklist handling occurs inside consensus construction. A no-blacklist consensus followed by filtering is not equivalent to the blacklist-on consensus universe.

The supplied transcript correctly refused to run consensus before blacklist authentication.

### Verdict

**SEMANTICS CORRECT.**

No no-blacklist consensus should be treated as a substitute for the decided blacklist-ON route.

## M-A5 — blacklist authentication code is committed, but the authentication receipt is not

Lane E contains `laneE_write_blacklist_acquisition_receipt_v1.py`. The producer recomputes local hashes and checks:

- HTTP content length;
- ENCODE metadata file size;
- S3 ETag/local gz MD5;
- ENCODE published gz MD5;
- ENCODE content MD5 of the uncompressed BED;
- GRCh38 assembly;
- exclusion-list output type;
- released status.

That is a reasonable authentication design.

But `results/v74` does not exist at exact Lane-E head `60b09710...`, and the Lane-E compare contains the producer but no committed acquisition receipt.

### Verdict

- **authentication producer:** PRESENT
- **authenticated blacklist result as Git evidence:** ABSENT

The blacklist should remain required, but its actual authenticated receipt must be preserved on the reconciliation successor before consensus runs.

## M-A6 — the random-128 motif-composition finding is important but is not a machine-result commit

Lane E commits the analysis document stating that earlier cisTarget benchmarks used an alphabetical motif prefix with unusually short PWMs.

The supplied transcript reports a matched random-128 run:

- prefix 128: 11.56 s/motif;
- random 128: 18.45 s/motif;
- mean PWM positions 9.19 vs 17.30;
- whole collection mean 21.57, max 1,480.

This invalidates the 33.5 h whole-collection projection as representative.

However the actual `RANDOM128_t8.bench.json` shown in the transcript is not committed at `60b09710...`; the branch contains the prose finding and producers/scripts, not a result/receipt tree under `results/v74`.

### Verdict

- **scientific/engineering interpretation:** credible supporting evidence
- **machine result in Git:** absent
- **old 33.5 h estimate:** should remain retired
- **54–65 h estimate:** planning/supporting only, not a precise production measurement

## M-A7 — quiet-512 is incomplete in repository evidence

The transcript shows a `QUIET512_t8` run launched after thresholds were prospectively declared. The transcript ends while it is still running.

The live branch has not advanced past `60b09710...`, the commit made before the quiet run landed.

Therefore the following are not qualified repository evidence:

- final quiet-512 wall time;
- final quiet-machine classification;
- final 512 contended-vs-quiet bitwise equality;
- final decision-rule branch;
- final shard-size recommendation from the quiet run;
- generated successor scaling-authority receipt.

### Verdict

**INCOMPLETE / LOCAL-ONLY.**

## M-A8 — Lane-E scaling authority producer is fail-open with respect to missing evidence

This is a new audit finding.

At `60b09710...`, `laneE_write_scaling_authority_successor_v2.py` behaves as follows:

- if the quiet-512 receipt is missing, `run_row()` returns `RECEIPT_ABSENT`;
- if one 512 run is missing, the digest comparison becomes `UNMEASURED__ONE_RUN_ABSENT`;
- nevertheless the top-level receipt status is assigned unconditionally as:

`COMPLETE__WORKERS_AND_SHARD_SIZE_MEASURED__BUILD_INFRASTRUCTURE_MAY_RUN__RUNTIME_PROJECTION_REVISED_UPWARD`

There is no prerequisite asserting that all mandatory run rows are present and PASS before that status is emitted.

This means the producer can produce a “COMPLETE” authority artifact while its own payload states that one deciding comparison is unmeasured.

### Verdict

**OPEN — P0 authority-producer fail-open.**

The producer must refuse output or emit a non-authorizing status unless every mandatory evidence item is present and validated.

## M-A9 — Lane-E scaling authority producer accepts caller assertions without independently binding them

The same producer accepts from CLI:

- `--recommended-shard-size`
- `--shard-size-changed`
- `--decision-branch`
- `--restart-evidence`

and records them into an authority receipt.

It does not, in this producer:

- recompute the frozen shard-size rule;
- validate that the declared decision branch is the branch actually implied by the measurements;
- validate the restart-evidence artifact contents/digest;
- bind the frozen decision-rule file by digest;
- independently execute/verify the shard plan before writing `plan_proven`;
- independently load and verify the claimed shard-size invariance artifact before writing `outputs_proven_invariant_to_shard_size`.

Several authority statements are therefore caller-supplied or hard-coded prose rather than derived checks.

### Verdict

**OPEN — P0/P1 authority forgery risk.**

Required repair: make the producer derive every deciding field from content-bound evidence and fail closed on missing/mismatched evidence. Add mutations for falsified CLI branch, falsified shard size, missing restart evidence, wrong restart digest, missing invariance result and altered decision-rule bytes.

## M-A10 — worker-count wording is overstated in ACTIVE_STATE

`ACTIVE_STATE.md` at `78f13e71...` says “cisTarget scaling measured: 8 workers optimal.”

Lane E's later scaling-authority producer explicitly narrows that claim:

- 8 workers was selected from a 16-motif curve;
- 512-motif runs show 8 workers **works** at production shard size;
- no other worker count was run at 512;
- optimality at production shard size is not demonstrated.

### Verdict

`ACTIVE_STATE.md` is **stale/overbroad on this point** and must be corrected in the reconciliation successor.

Correct wording: 8 workers is the measured optimum on the 16-motif benchmark and a demonstrated workable configuration at 512 motifs; production-shard optimality is unproven.

## M-A11 — ACTIVE_STATE is not the current global Macha state despite being a stale-state repair

The `78f13e71...` update correctly repaired a four-week gap and records:

- Stage 4 NOT AUTHORIZED;
- correspondence UNOPENED;
- training OFF;
- S102 OPEN;
- the V1 K-curve retraction;
- the repaired K curve's non-monotone result;
- no SCENIC+ network on either route.

But it predates the later parallel Route-B and Lane-E work and is on a separate lineage.

Therefore it is no longer sufficient as a complete current-state pointer.

### Verdict

**NEEDS RECONCILIATION**, not because its protected-boundary statements are wrong, but because it omits/overstates later lane-specific evidence.

## M-A12 — G2 successor contract is appropriately fail-closed and remains NOT_IN_FORCE

The committed G2 successor contract at `03c0c486...` has status:

`FROZEN__NOT_IN_FORCE__DECIDING_MARGIN_UNSET`

It fixes:

- the estimand;
- donor-cluster bootstrap structure;
- C∩P support alignment;
- three weightings;
- sign invariance;
- three-valued substantive decision structure;
- explicit refusal states;
- forbidden margin sources.

It also explicitly records:

- `m_abs` unset/not derivable from current evidence;
- relative `f=1` as the only derivable logical boundary, with smaller values requiring labelled convention;
- confidence level, `D_min`, and `E_min` unset;
- discriminating PIPELINE_ARTEFACT_m experiment specified but not run;
- no real substrate read;
- no real correspondence values computed;
- Stage 4 NOT AUTHORIZED.

### Verdict

**GOOD FAIL-CLOSED DESIGN ARTIFACT; NOT EXECUTION AUTHORITY.**

S102 remains OPEN/NARROWED.

## M-A13 — existing synthetic corpus does not test the detection half of G2

The G2 contract correctly states that existing planted worlds put signal on linked intervals only and do not plant CONTROL_A-vs-CONTROL_B asymmetry.

Therefore existing synthetic worlds can measure the false-alarm half of G2 but cannot measure whether a proposed G2 rule detects the artifact it is intended to police.

### Verdict

No G2 safeguard should be called qualified until the prospectively specified discriminating experiment is run under frozen margins/rules.

## M-A14 — stale-claim audit found real propagation failures

The stale-claim lane classifies:

- 12 false stale claims;
- 7 superseded claims;
- 5 structural-argument-only statements;
- 3 historical-retain-for-record statements;
- 9 current groups.

It correctly identifies that the withdrawn V1 K-curve conclusion remained in both the V1 artifact and the Stage-4 closeout, including machine-readable convergence/monotonicity fields.

No executable gate was found to consume the stale V1 conclusion.

### Verdict

**VALID GOVERNANCE FINDING; NO COMPUTATION INVALIDATED BY PROPAGATION.**

## M-A15 — stale-claim repair strategy is not byte-preserving history

The stale-claim lane modifies historical V1 and closeout artifacts in place by adding supersession headers / regenerating the closeout while preserving measured fields and recording prior hashes.

This is more transparent than silent rewriting, but it is not byte-preserving historical custody.

Other project lanes use the stricter pattern “preserve historical artifact byte-for-byte; create a successor artifact that supersedes it.”

### Verdict

**GOVERNANCE CONCERN, not a scientific-result defect.**

The reconciliation successor should choose one policy explicitly. Preferred: leave original historical bytes immutable and place supersession in a separate successor/index artifact, unless there is a documented reason to retain the in-place annotation convention.

## M-A16 — stale-claim S112 remains open

The stale-claim lane itself says S112 is not closable there: the repaired V2 artifact still carries a bare convergence flag beside inherited contract text asserting a monotone rise.

### Verdict

**OPEN.**

A runner/artifact successor must remove or scope that contradiction without rewriting SHA-frozen execution evidence.

## M-A17 — exact-sampler governance remains appropriately fail-closed

The ACTIVE_STATE record describes the Stage-4 executor as implemented/qualified but containing no authorized real-execution path, even with a correctly formed authorization object present.

It also records that no real correspondence value has been computed.

Nothing found in the later Macha lane diffs contradicts the protected boundary.

### Verdict

Protected execution remains closed.

## M-A18 — protected-data audit

Across the inspected exact branch diffs:

- Route-B adds/modifies scripts and tests, not protected correspondence outputs;
- Lane E adds docs/scripts and no committed `results/v74` output tree;
- G2 adds design/contract/test artifacts and declares `real_substrate_read=false`;
- stale-claim work modifies historical Stage-4 documentation/result metadata, not protected outcomes;
- ACTIVE_STATE is documentation only.

No evidence was found that any audited Macha lane opened Morabito, recoverability TEST, real correspondence, or training.

### Verdict

- Stage 4: NOT AUTHORIZED
- correspondence: UNOPENED
- training: OFF
- multimodal training: OFF
- Morabito: PROTECTED
- recoverability TEST: SEALED

## M-A19 — no SCENIC+ network exists

The ACTIVE_STATE update explicitly says no regulatory network exists on either route. Nothing in Route-B or Lane-E diffs adds a final network artifact.

### Verdict

**NO NETWORK / NO BIOLOGICAL eREGULON CLAIM.**

## M-A20 — no Macha 100K synthetic qualification exists

The audited Macha lanes address Stage-4/G2/SCENIC+ infrastructure and do not produce the Sol V73/V74 synthetic-stress promotion authority.

### Verdict

No 100K foundation synthetic qualification may be inferred from Macha work.

---

# Final disposition matrix

| Area | Final audit state |
|---|---|
| Route-B custody code | materially repaired |
| Route-B real 63.6GB rerun | local transcript only; no committed V74 receipt |
| Route-B mutations/tests | meaningful local evidence; no exact-head hosted CI |
| Route-A barcode guard | OPEN P0 |
| blacklist policy semantics | correct |
| blacklist authentication producer | present |
| committed blacklist authentication receipt | absent |
| random-128 timing finding | credible supporting evidence; machine result not committed |
| historical 33.5h projection | superseded |
| quiet-512 | incomplete/uncommitted |
| scaling-authority producer | OPEN P0 fail-open + caller-assertion defects |
| 8-worker production optimality | NOT demonstrated |
| G2 successor contract | frozen, fail-closed, NOT_IN_FORCE |
| S102 | OPEN / narrowed |
| G2 detection operating characteristic | NOT RUN |
| stale V1 K-curve propagation | found and documented |
| S112 | OPEN |
| ACTIVE_STATE | partially stale relative to later parallel lanes |
| exact-head hosted CI on Macha heads | absent |
| one reconciled Macha head | does not exist |
| Stage 4 | NOT AUTHORIZED |
| real correspondence | UNOPENED |
| training | OFF |
| Morabito | PROTECTED |
| recoverability TEST | SEALED |
| SCENIC+ network | does not exist |

# Required reconciliation gate

Before any Macha work is called “current” or “closed,” create a new reconciliation successor from an explicitly selected audited base and require all of the following:

1. integrate Route-B custody code from `32dfcbfd...`;
2. fix Route-A duplicate/conflict validation before dictionary construction;
3. bring Lane-E work from `60b09710...` only as committed evidence;
4. preserve/commit the blacklist authentication receipt before consensus;
5. preserve/commit random-128 and, if completed, quiet-512 machine receipts with exact code/data digests;
6. repair the scaling-authority producer so missing evidence cannot yield COMPLETE;
7. remove caller-controlled authority assertions by deriving shard decision, decision branch, restart evidence, invariance and planner status from content-bound artifacts;
8. add adversarial mutations for every scaling-authority prerequisite;
9. bring in G2 successor semantics from `03c0c486...` without setting an unearned margin;
10. preserve S102 as OPEN until the owner fixes conventions/margins and the discriminating experiment is prospectively run;
11. reconcile stale-claim corrections from `14326480...` using an explicitly chosen historical-custody policy;
12. close S112 with a versioned successor rather than rewriting frozen execution evidence;
13. update ACTIVE_STATE to remove the overbroad “8 workers optimal” production interpretation and include all later lane status;
14. run the complete exact-head behavioural/mutation suite;
15. obtain provider-backed execution evidence if that is required for final engineering qualification;
16. emit one machine-readable reconciliation receipt containing source SHAs, conflict resolutions, test/mutation evidence, result/receipt digests, protected-data state and all remaining blockers.

# Final audit verdict

The Macha work contains several **real and valuable repairs**, especially Route-B custody logic, blacklist semantics, G2 fail-closed redesign and stale-claim discovery.

But the full audit does **not** support the statement “Macha is finished” or “Macha V74 is one qualified implementation.” The work is split across divergent heads; key expensive executions are transcript-only; Route-A retains a known integrity bug; Lane-E's scaling-authority producer can issue COMPLETE with missing evidence and accepts caller assertions; S102/S112 remain open; and there is no final network or Stage-4 authorization.

The correct narrow statement is:

> **All currently visible Macha lanes have now been audited. The remaining defects and evidence gaps are explicitly enumerated. No further hidden Macha audit task is known from the supplied handoff/transcript/GitHub heads; the next step is implementation reconciliation and re-qualification, not more audit discovery.**
