# Response to the PR #118 independent audit

Branch `repair/pr118-audit-fixes-20260925` at `c02d47a7b60a`, from PR #118 head
`d719ce1619f8` (verified ancestor). Nothing unpushed, tree clean.

Live heads at close: `main c49b13bd75c2` · PR#77 `9a2a30e4c4c9` ·
PR#118 `d719ce1619f8` · PR#117 `9c524f49dd14` (moved from `0a72e6eb` during the
work). No competing PR merged.

---

## Status

| item | status |
|---|---|
| **P0-1** adversarial testing | **FIXED_AND_PHYSICALLY_TESTED** — 53 adversaries, 4 producers, 0 undeclared skips |
| **P0-2** inventory fail-open + unbound assertions | **FIXED_AND_PHYSICALLY_TESTED** |
| **P0-3** independent recompute of GSE301119 | **FIXED_AND_PHYSICALLY_TESTED**, with one caveat — see §3 |
| **P0-4** harden the GSE301119 producer | **FIXED_AND_PHYSICALLY_TESTED** |
| **P0-5** stale matrix status / leakage | **FIXED_AND_PHYSICALLY_TESTED** |
| **P1-6** independent bulk recompute | **PARTIAL** — GSE254205 done; GSE241858 and GSE240609 `NOT_DONE` |
| **P1-7** BIN1 physical V2 | **FIXED_AND_PHYSICALLY_TESTED** |
| **P1-8** guide-target / assay scope | **PARTIAL** — ARID5B held `TARGET_IDENTITY_PENDING`; HGNC crosswalk `NOT_DONE` |
| **P2-9** external data | **BLOCKED**, correctly and unchanged |

Step 2 of the execution order was honoured: the qualification contract
(`PR118_REPAIR_QUALIFICATION_CONTRACT_20260925.md`, commit `2c07fd90`) was
published **before** any expensive run, fixing the frozen 16-asset manifest, the
20-adversary matrix, the reproduction algorithm, a 1e-9 tolerance and the
exposure freeze.

---

## 1. Both new findings were confirmed against our own code before being fixed

**P0-2 fail-open, demonstrated on one fixture** — byte-correct asset, `.sha256`
sidecar removed:

```
physical_source_inventory_vnext.py   printed "NO DIGEST GSEAAA/a.gz"   exit 0
physical_source_inventory_v2.py      printed "NO_SIDECAR_DIGEST ..."   exit 1
```

**P0-2 staleness was worse than "out of date."** The readiness JSON contradicted
commits in the *same PR*: GSE240609 marked `UNOPENED_RESERVED` after 38,090
contrast rows had been physically produced; GSE311359 marked author-blocked
after the deposit was shown to resolve it.

**P0-5 confirmed**: the matrix hard-coded that same `UNOPENED_RESERVED`.

## 2. What is now enforced

* Inventory binds to `FROZEN_EXPECTED_16_ASSET_MANIFEST_V1.json` and fails
  nonzero on missing, extra, size-, digest-, format- or role-mismatched or
  sidecar-less assets, and on any study lacking a registered assertion.
  Real store: **PASS, 16/16, 4,450,940,052 bytes**.
* Exposure lives only in `CURATOR_ASSERTION_REGISTRY_V2.json`; the matrix reads
  it and cannot drift. GSE335887 age recorded as
  `SOURCE_CONFLICT_PENDING_RUN_LEVEL_AUTHORITY`, not chosen.
* Both superseded producers are fail-closed; CI asserts they stay that way.
* **P1-7**: V1 held **14** rows claiming cells with zero counts, all BIN1. V2:
  **0**. All **2,434** non-BIN1 units reproduce exactly — zero mismatches in
  cells or counts, none unique to either side — closing the condition PR #92
  left open. The three BIN1 cis elements are kept separate.

## 3. P0-3 — and the caveat that matters more than the number

```
CRISPRi D1  max|delta| 1.776e-15  over 7,503,205 cells   0 mask mismatches
CRISPRi D2  max|delta| 1.776e-15  over 7,466,604 cells   0 mask mismatches
CRISPRa D1  max|delta| 1.776e-15  over 3,947,372 cells   0 mask mismatches
CRISPRa D2  max|delta| 1.776e-15  over 3,794,076 cells   0 mask mismatches
cross-donor mean       8.882e-16                          0 mask mismatches
```

~22.7M cells, six orders inside the declared 1e-9, target order, feature order
and donor masks all matching. The comparator was proven able to detect a sign
error **before** being trusted, via a planted fixture matching a hand
computation at delta 0.0 and a swapped-contrast control that must negate
exactly. CRISPRi-down/CRISPRa-up was explicitly **not** used, since a
direction error flips both together.

**Caveat (our self-audit S4, not raised by the audit):** we authored the R
producer, the Python reproducer **and** the specification both follow. This
rules out transcription, indexing, layout and one-sided normalisation errors. It
does **not** establish that the specified estimand is right — a wrong spec would
be reproduced faithfully by both. **Read the receipt's
`INDEPENDENT_REPRODUCED` as `IMPLEMENTATION_REPRODUCED`.** Closing this needs a
different author deriving the estimand afresh; it is not closable by more work
from this lane.

## 4. What failed during red-team

**A declared tolerance genuinely failed, and was not widened.** P1-6 came back
at `max|delta| = 5.000e-07` — exactly half of 1e-6, the signature of 6-decimal
storage, so 1e-9 was never testable against that CSV. The replacement is
*stricter*, not looser: `round(independent_value, 6)` must equal the stored
value for **every** row. It does, **108,351 / 108,351**. Verdict recorded as
`IMPLEMENTATION_REPRODUCED_TO_STORED_PRECISION`, and verifying at 1e-9 requires
the producer to emit unrounded values.

**Three defects were found in our own test code**, each of which would have
produced a false green:

1. the comparability positive control **failed** when P0-5's externalisation
   added a required argument — the suite caught our own breaking change;
2. the donor-aware positive control **failed** on an over-escaped regex that
   left `donor` holding the whole key. Without it, all 13 mutation rejections
   would have been untrustworthy, since they could have been failing for an
   unrelated reason;
3. `rowname_drift` was a **silent no-op** — it changed rownames while `features`
   was *derived from* rownames, so nothing drifted;
4. in P1-6, the rounding checker miscounted decimals for scientific notation
   (`-3.9e-05` → 5 not 6) and manufactured false violations. The producer was
   right; our test was wrong.

**Skips are bounded, not forbidden.** CI parses JUnit and fails on any skip
outside a named allowlist, on any synthetic test failing to run, and on a
shrunken suite. The allowlist and must-run set are written out, so a reader sees
which tests may be absent and why rather than inferring it from a green check.

## 5. Software correctness vs scientific uncertainty

**Software correctness — materially stronger.** 53 adversaries across four
producers; both fail-open paths closed; identity (not shape) validated; atomic
publish; inputs digested before opening and re-verified after; two effect
computations independently reproduced.

**Scientific uncertainty — unchanged by any of it.** GSE301119 still has **n=2
donors** and licenses no population claim. GSE178317's four wells are capture
wells from **one pooled preparation** and create no replicate. GSE311359's V2
proves feature identity, **not** protospacer sequence, perturbation efficiency
or cis causality — `BIN1` remains the depositors' nominated label.
GSE335887's library is **30 targets × 2 guides + 5 NTC**, and **ARID5B has no
authenticated guide** in the deposit. No ETL pass here authorises a predictor or
training.

## 6. Self-audit — five findings the audit did not raise

`SELF_AUDIT_20260925.md`, commit `cc077f5e`.

| | finding | status |
|---|---|---|
| S1 | frozen manifest generated from our own inventory run | fixed — three-way agreement now explicit, 16/16 |
| S2 | R locale collation vs Python codepoint ordering | fixed — `method="radix"` |
| S3 | P0-5 relocated assertions rather than externalising them | fixed — external digested contract, output byte-identical |
| S4 | reproduction not independently **authored** | **open, not closable here** |
| S5 | outputs manifest currency | no defect (re-verified, 14 files) |
| S6 | 33-target comparison rested on an unverified PR #102 upstream | fixed — 39/39 reproduce |
| S7 | donor-aware producer had no suite | fixed — 17 adversaries |

## 7. Not done

GSE241858 and GSE240609 independent recompute (P1-6); the HGNC 13,373/116
crosswalk (P1-8); GSE254205's snRNA, ATAC and LD-sort assets (untouched,
`UNOPENED_RESERVED`); GSE335887 preparation census and run-level chemistry;
GSE175721 (author-blocked, re-searched and confirmed).

No promotion is claimed. Acceptance criteria are **not** met: P1-6 is partial,
and S4 means the GSE301119 reproduction is implementation-level only.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
```
