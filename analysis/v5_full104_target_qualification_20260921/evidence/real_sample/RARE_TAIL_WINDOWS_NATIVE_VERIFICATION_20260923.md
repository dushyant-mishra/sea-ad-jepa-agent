# PR #66 — native Windows verification

Date: 2026-09-23
Branch: `verify/v5-rare-tail-windows-native-20260923-claude`
Parent: `f13c8364fe997d800cb84ad5370da43e75e17d3e` (PR #66 head, verified unmoved)

Clean detached worktree at the exact head. **No real molecular RNA was executed.**

## Environment

```
os      Windows-10-10.0.26200-SP0   (AMD64)
python  3.9.7
numpy   1.24.2
scipy   1.10.1
```

## The change under test

```python
# Windows rejects fsync on a read-only descriptor (EBADF). Open the staged
# result read-write solely for durability; do not modify its validated bytes.
with stage.open("rb+") as f:
    os.fsync(f.fileno())
```

This is exactly the defect reported in PR #65 and the minimal fix suggested there.

## Result — the Windows defect is closed

| suite | before (#61 head) | after (#66 head) |
|---|---|---|
| `tests/ -k rare_tail` | 71 passed, **1 failed** | **72 passed, 0 failed** |
| `tests/test_v5_full104_rare_tail_molecular_guarded_v1.py` | — | **6 passed** |

Both suites run **twice**, **zero skipped** in every run.

The previously failing
`test_atomic_synthetic_success_creates_one_result_one_receipt_and_intent`
now passes natively on Windows. Hosted Linux CI could not have caught this: on
Linux `fsync` on a read-only descriptor succeeds, so the defect was invisible
there by construction. Linux green was correct and simply not a Windows
qualification.

Four pre-existing V4 collection errors (`results/v4/` artifacts absent) are
unrelated to this lane and were excluded by path; they reproduce on a pristine
worktree.

## Recomputed gateway source SHA

The old externally-approved gateway SHA is **invalid** — #66 changed code bytes.

```
new gateway normalized_text_sha256
0f9689c513eb391c803f875fb9b7c804a8a14a3b0286a812de08d37478cd6cbd
```

(The file has no CR bytes, so its raw file SHA is the same value.)

Any prior approval must be reissued against this digest.

## Controls covered by the passing suites

Verified by the guarded-gateway suite executing on this host, not by inspection
alone: successful atomic result commit; successful receipt commit; exclusive
intent created before execution; subprocess failure leaving the intent and
refusing silent relaunch; staged-result `fsync` working on Windows; corruption
rejected; wrong reviewed-preflight SHA rejected; wrong gateway-source SHA
rejected; duplicate/restart behaviour fail-closed.

## Governance note

The older frozen molecular runner remains **directly callable** — nothing in the
filesystem prevents invoking it and bypassing the guarded gateway. The protection
here is governance, not a technical interlock. That bypass remains forbidden, and
the gateway is the only approved path to molecular execution. Worth restating
plainly because a reviewer reading only the gateway's guards could reasonably
assume the bypass is closed in code. It is not.

```
RARE_TAIL_MOLECULAR = UNOPENED
REAL MOLECULAR RNA  = NOT EXECUTED
TRAINING            = OFF
```
