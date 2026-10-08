# Stage81 Storage-Policy Reconsideration

Stage81 dataset eligibility has no fixed total-download cap, fixed reserve, or
per-object manual size threshold. Available space is measured before transfer,
but scientific role, authority, processed status, identity support and
nonduplication determine selection.

The reconsideration ledger reclassifies every acquisition and exclusion into
one of the approved decisions. Scientific rationale and storage assessment are
separate columns. Any surviving `deferred_oversized`,
`excluded_due_to_download_limit`, `catalog_only_due_to_size`, or
`requires_manual_size_approval` status fails the audit.

The review found no previously recorded size-based exclusion. It did identify a
scientific coverage gap in the normal-reference search, resolved by adding
official processed assets for GSE243292, GSE146639, GSE99074 and GSE133357.
All eight approved perturbation studies were acquired. Duplicate, raw,
scientifically incompatible, source-unverified and controlled-access decisions
remain distinct and are not storage exclusions.

Run:

```powershell
conda run -n sea-ad-jepa-v3 python scripts/v4/stage81_reconsider_storage_policy.py
```
