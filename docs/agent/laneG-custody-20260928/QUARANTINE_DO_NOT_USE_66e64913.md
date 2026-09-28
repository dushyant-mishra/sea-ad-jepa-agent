# QUARANTINE — DO NOT USE — `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`

```
  ####################################################################
  #                                                                  #
  #   STATUS: PROVENANCE_MISMATCH_DO_NOT_USE                         #
  #   ROLE:   QUARANTINED_PROVENANCE_MISMATCH                        #
  #           NEVER_CURRENT_AUTHORITY                                #
  #                                                                  #
  #   THIS FILE MUST NEVER BE USED SCIENTIFICALLY.                   #
  #                                                                  #
  ####################################################################
```

**Recognition key — this identifies the quarantined object under ANY filename:**

```
sha256 = 001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70
bytes  = 1531109
```

If you hash an `.npz` and get that digest, stop. It does not matter what directory it came
from, what it has been renamed to, or which handoff archive delivered it.

---

## Why it is quarantined

The bytes on hand do not match the identity the project history expects for this name.

| | size (bytes) | sha256 |
|---|---|---|
| **observed** | 1 531 109 | `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70` |
| **historical expected** | 4 985 | `1473430393179ce8242c9b5ce24d7b84c39d9289492b5a96332eb81436ae68a6` |

The observed object is about 307 times the expected size. Two different objects have carried
this filename. `hash_verified: false`. Until someone reconciles the provenance — documents what
the 1 531 109-byte object actually is and who produced it — **anything computed from it cannot
be attributed to a known artifact**, so it cannot support or refute any scientific claim.

You may not lift this quarantine by opening the file and inferring its role from its contents.
From `JEPA_HEAVY_ASSET_REFERENCE_20260909_FINAL_R4.md`:

> semantic role must be recovered from project provenance before use; do not infer it from the filename.

## Allowed

- Recording its size and SHA-256 for custody accounting.
- Hashing the raw bytes to confirm identity (what this lane did).

## Forbidden

- `numpy.load`, or any pickle / object-array deserialization.
- Using it as the historical operator-address authority.
- Relabelling it as an authenticated FULL104 operator-address artifact.
- Deriving, supporting, checking or refuting **any** scientific result from its contents.
- Admitting it into any training, evaluation, calibration, census or qualification input set.

## Where it is reachable on this machine (verified 2026-09-28)

No loose extracted copy exists, but the quarantined object is inside **four** local archives.
Extracting any of them yields the file under its bare name, carrying no warning of its own:

| archive | member |
|---|---|
| `C:/Users/dushy/Downloads/JEPA_V46_CHAT_EXCLUSIVE_SMALL_PORTABLE_20260927.zip` | `originals/66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` |
| `C:/Users/dushy/Downloads/JEPA_HANDOFF_VOLUME_00_SMALL_MEDIUM.zip` | `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` |
| `C:/Users/dushy/Downloads/JEPA_COMPREHENSIVE_HANDOFF_20260905.zip` | `JEPA_COMPREHENSIVE_HANDOFF_20260905/runtime_archive_small_medium/66e64913-...npz` |
| `C:/Users/dushy/Downloads/JEPA_FINAL_HANDOFF_20260905.zip` | `04_LOCAL_WORK/all_small_runtime_artifacts/66e64913-...npz` |

All four members were read as raw bytes and hashed on 2026-09-28. Every one is 1 531 109 bytes
with sha256 `001375ec...ff70` — the quarantined object, not the 4 985-byte historical one. None
was deserialized.

**Rule for future agents:** hash every `.npz` recovered from a project handoff archive before
using it.

## The prior records this preserves (verbatim)

- `docs/agent/JEPA_RUNTIME_ASSET_STATUS_20260910_CURRENT.json`, key `operator_address_state_npz`
  — `"status": "PROVENANCE_MISMATCH_DO_NOT_USE"`;
  *"Do not use this runtime NPZ as the historical operator-address authority unless its provenance is separately reconciled."*;
  and the smoke policy *"use only assets whose expected identity is hash-verified; exclude operator_address_state_npz while mismatch remains"*.
- `analysis/v5_full104_dataset_etl_20260921/environment/JEPA_ENVIRONMENT_ARTIFACT_ROLES_20260921.csv`
  — `66e64913-...npz,1531109,001375ec...,QUARANTINED_PROVENANCE_MISMATCH,NEVER_CURRENT_AUTHORITY`.
- `analysis/v5_full104_dataset_etl_20260921/supporting/JEPA_LOCAL_PARALLEL_AUDIT_20260920.md`,
  section *"Quarantined / never current authority"* — *"…says never current authority. It is not used below to establish a current result."*
- `docs/agent/JEPA_V26_CURRENT_V5_EXECUTION_SEAM_AUDIT_20260925.md` — *"Quarantine remains… Do not relabel this NPZ as an authenticated FULL104 operator-address artifact."*
- `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260910_FINAL_CURRENT.md` — *"Do NOT use this object as the historical operator-address authority without reconciliation."*
- `docs/agent/PROJECT_SESSION_ARTIFACT_INVENTORY_20260907.csv` — role `ROLE_REQUIRES_AUTHORITY_TRACE_BEFORE_USE`.

None of those files was modified. This notice adds to them.

---

Full machine-readable record:
`docs/agent/laneG-custody-20260928/JEPA_CUSTODY_MANIFEST_SUCCESSOR_20260928_LANEG.json`
(key `READ_THIS_FIRST__QUARANTINE`).
