# Rare-tail V2 safeguards — independent review

Date: 2026-09-22
Branch: `gpu/v5-rare-tail-v2-review-20260922-claude`
Parent: `bf248a97f6e5249dc7922e4499fc18128cc89fc5` (PR #61 head, verified unmoved)

**No expression opened. No count matrix opened. No molecular outcome opened. The
gateway's expression-opening option was NOT used.** The older frozen molecular
runner was not called directly.

---

## V2 read-only preflight — PASS

```
state    READY_FOR_INDEPENDENT_REVIEW__NO_RNA_OPENED
receipt  RARE_TAIL_MOLECULAR_READONLY_PREFLIGHT_V2.json
canonical sha256  84e6f716fec00fd660f67dc18bd468759c47a7cc935e9a359c4c4bebabb8efa7
file sha256       feac846b76b39f6c07b93ef3f78adeb7539b3b0a3b7933a7ec677cf003774ade
bytes             3,093
```

Run against the real authenticated sample and the real Level-4 manifest
(`66f589e5…`). Written to a new path; nothing was overwritten.

**No count matrix was opened.** Verified the strong way, not by reading the flag:
the preflight completes against a Level-4 root containing **only** the manifest,
with zero `.npz` blocks on disk.

## What V2 adds over V1

V2's substantive addition is **physical** structural-receipt authentication: it
binds the structural receipt's *file* SHA and its *canonical* SHA, cross-checks
the provenance against it, and requires the provenance's safety flags. It then
**re-runs V1 in process** rather than trusting a stored V1 receipt.

That last point is worth stating because it defeated one of my own controls (see
below) — it is a stronger design than binding a stored receipt.

## Rejection controls

| control | result |
|---|---|
| modified structural receipt | **REJECTED** — `physical structural receipt file SHA-256 mismatch` |
| forged provenance (terminal flipped to STOP) | **REJECTED** — `physical structural provenance file SHA-256 mismatch` |
| changed pair-address hash (strict-core reorder) | **REJECTED** — `target-eligibility file hash mismatch` |
| provenance claims `expression_opened=true` | **REJECTED** — `physical structural provenance file SHA-256 mismatch` |
| gateway: wrong externally-approved V2 SHA | **REJECTED** — `V2 preflight file differs from externally reviewed immutable SHA` |
| gateway: safe mode (no execution flag) | **PASS** — `GATE_VERIFIED__EXPRESSION_NOT_OPENED` |

### One control of mine was invalid, not a finding

"Altered V1 preflight receipt" appeared to be accepted. It is not a gap: **V2
never reads a stored V1 receipt.** It calls `run_preflight(...)` and uses the live
result, so mutating a stored V1 receipt file changes nothing by construction. My
control was pointed at a file the code does not consult.

### "Unapproved source" — recorded at preflight, enforced at the gateway

Editing a bound source (the V1 preflight or the structural validator) does **not**
make V2 exit non-zero. It is not a hole:

```
v1_preflight_source_normalized_sha256   16e972ba… -> f18874c0…   (moves)
receipt_sha256                          84e6f716… -> (moves)
```

The edited hash propagates into `receipt_sha256`, and the gateway requires
`--externally-approved-v2-file-sha256` to match exactly. Any source edit therefore
invalidates the approval. **Record at preflight, enforce at the gate** — verified
end to end: the gateway rejects a mismatched approved SHA.

The gateway's execution path additionally requires an exact
`--externally-approved-gateway-source-sha256` compared against
`normalized_text_sha256(Path(__file__))`, and refuses without it. I verified that
by source inspection and by the ordering of the checks; **I did not pass the
execution flag**, so this one is reported as read, not as run.

---

## Defect found: the gateway cannot commit a result on Windows

`tests/test_v5_full104_rare_tail_molecular_guarded_v1.py::test_atomic_synthetic_success_creates_one_result_one_receipt_and_intent`
**FAILS on this machine** with:

```
OSError: [Errno 9] Bad file descriptor
  run_full104_rare_tail_molecular_guarded_v1_20260922.py:173
```

The cause, at lines 172–173:

```python
with stage.open("rb") as f:     # read-only handle
    os.fsync(f.fileno())        # Windows: EBADF
```

Minimally reproduced on this host:

```
platform: win32
fsync on a READ-ONLY handle   -> OSError errno=9: Bad file descriptor
fsync on a READ-WRITE handle  -> OK
```

**This is not a CI problem and PR #61's green CI is not wrong.** The suites are
genuinely executed, not excluded — 71 of 72 rare-tail tests pass here too. Hosted
CI runs Linux, where `fsync` on a read-only descriptor succeeds, so the defect is
invisible there by construction.

**Why it matters for this project specifically:** the GPU machine holding the
authenticated FULL104 data is Windows. On it, the guarded gateway would execute
the molecular runner, stage a result, and then **crash at the atomic-commit step**
— after the compute, before the receipt.

The failure is *safe* — it matches the code's own comment that an interruption
between the two commits yields no admissible receipt and the exclusive intent
prevents automatic retry — but the path is **unusable on this host**, and the
crash happens only after the expensive and boundary-sensitive work has run.

**I have not patched it.** It is frozen science-adjacent code on another lane, and
the fix is a design choice (fsync the stage at write time, or open `"rb+"`, or
fsync the containing directory) that belongs to PR #61's owner. Suggested minimal
change, for that owner to accept or reject:

```diff
-    with stage.open("rb") as f:
+    with stage.open("rb+") as f:
         os.fsync(f.fileno())
```

## Tests

```
pytest -q -p no:randomly --strict-markers -rs tests/ -k rare_tail
  -> 71 passed, 1 failed, 0 skipped
```

The single failure is the Windows `fsync` defect above. Zero skips.

```
EXPRESSION OPENED            = FALSE
COUNT MATRICES OPENED        = FALSE
MOLECULAR OUTCOME            = UNOPENED
GATEWAY EXPRESSION OPTION    = NOT USED
FROZEN MOLECULAR RUNNER      = NOT CALLED DIRECTLY
TRAINING                     = OFF
```
