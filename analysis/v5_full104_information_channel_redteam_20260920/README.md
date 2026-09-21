# FULL104 information-channel red-team — 2026-09-20

Reconnaissance and qualification audits of information channels exposed by the
actual FULL104 code and history.

**No current authority is modified by anything in this directory.** Not pass1,
not Census Authority V2, not the target eligibility set, not the masking burden
ladder, not the masking policy, not G5, G4, G3, and not any terminal run
contract. Where an audit finds a real mismatch it is recorded as an open design
issue with a repair *plan*; discovery and policy choice are kept separable.

```
TERMINAL_MASKING_OUTCOMES   = UNOPENED
D_SHARED                    = SEALED
PATHOLOGY / DEV / SEALED    = SEALED
TERMINAL_BURDEN_SELECTED    = NO
MASKING_POLICY_SELECTED     = NO
TRAINING_OFF
```

The corrected census value `core_measured_zero_frequency = 0.8329826626244999`
remains authoritative. This phase does not attempt to repair it and does not
depend on repairing it.

---

## Audits

| | audit | question | report |
|---|---|---|---|
| **A** | normalization denominator | `source_library` is computed from raw source expression *before* ledger mapping, so RNA outside the 41,238-address ledger divides every visible feature | `NORMALIZATION_DENOMINATOR_AUDIT_REPORT.md` |
| **B** | effective mask burden | does exact address-count parity imply equal evidence burden? | `MASK_EFFECTIVE_BURDEN_AUDIT_REPORT.md` |
| **C** | target source estimability | is every globally eligible target actually estimable within each source, and how often is the target unvarying within a donor? | `TARGET_SOURCE_ESTIMABILITY_AUDIT_REPORT.md` |
| **D** | attacker standardization | what estimand does held-out-donor standardization define? | `ATTACKER_STANDARDIZATION_ESTIMAND_AUDIT.md` |
| **E** | co-detection vs co-expression | are screening-selected partners *detected together* or *quantitatively covarying*? | `PARTNER_CODETECTION_DECOMPOSITION_REPORT.md` |
| **F** | target identity × target-zero | on target-zero cells, how much of the target representation is identity and context? | `TARGET_IDENTITY_ZERO_STRATIFIED_DESIGN.md` |
| **G** | calibration-cache coverage | does the cache cover the real support extremes? | `CALIBRATION_CACHE_COVERAGE_AUDIT.md` |

`CROSS_AUDIT_INTERACTIONS.md` carries the required status table across all of
them.

## Evidence layout

```
scripts/     every producing script, committed
evidence/    compact JSON and CSV, committed
EVIDENCE_SHA256.csv      byte size + SHA-256 of every committed file here
EXTERNAL_ARTIFACTS.json  large artifacts NOT committed, content-addressed
```

Large row-level artifacts stay on the GPU machine. Each is recorded with its
absolute path, byte size, SHA-256, producer Git SHA, producer script SHA-256,
schema/role, whether it contains cell-level material, and
`GPU_MACHINE_NOT_COMMITTED`. A reviewer cannot recompute those from GitHub, but
can verify byte-identity against the artifact the reported numbers came from —
and every aggregate needed to challenge a conclusion is committed alongside.

Donor identity is carried as canonical donor codes and IDs already present in
the authenticated pass1 registry. No raw cell identifiers are committed.

## Verification protocol

Each audit follows the same sequence, and the status is derived from the
evidence rather than declared by the caller:

1. implement;
2. unit-test;
3. synthetic **positive** control, where the answer is known by construction;
4. **negative** control capable of falsifying the test — an audit that cannot
   fail is not evidence;
5. real FULL104 safe-lane execution;
6. invariant inspection, fail-closed;
7. independent recomputation of headline totals **by a second route**, not by
   calling the same helper twice;
8. red-team the interpretation;
9. only then commit.

Where a quantity could not be measured it is reported `NOT_MEASURABLE` with a
reason, never as a zero and never silently omitted.

## Reproduction

All scripts take explicit paths and run from the repository root with
`PYTHONPATH=src`. The environment must have its native DLL directory on `PATH`;
see `analysis/v5_full104_pass1_rebuild_20260920/SOLVER_ENVIRONMENT_DIAGNOSIS_CORRECTION_20260920.md`
for why that is a hard precondition rather than a convenience.
