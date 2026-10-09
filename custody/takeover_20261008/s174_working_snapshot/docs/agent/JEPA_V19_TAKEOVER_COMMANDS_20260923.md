# V19 takeover commands — next JEPA chat and Claude GPU/Windows (2026-09-23)

## A. Read authority and fetch LIVE heads BEFORE changes
```powershell
git fetch origin --prune
git show origin/handoff/jepa-v5-source-repair-raretail-20260923-v19:START_HERE.md
git show origin/handoff/jepa-v5-source-repair-raretail-20260923-v19:docs/agent/JEPA_LATEST_HANDOFF_POINTER.json
git show origin/handoff/jepa-v5-source-repair-raretail-20260923-v19:docs/agent/JEPA_NEW_CHAT_HANDOFF_20260923_V19_SOURCE_REPAIR_RARETAIL.md
git show origin/handoff/jepa-v5-source-repair-raretail-20260923-v19:docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260923_V19.json
git show origin/handoff/jepa-v5-source-repair-raretail-20260923-v19:docs/agent/JEPA_V19_DATA_RESULTS_SCRIPTS_MANIFEST_20260923.json
gh pr view 63 --json headRefOid,baseRefName,state,isDraft
gh pr view 64 --json headRefOid,baseRefName,state,isDraft
gh pr view 65 --json headRefOid,baseRefName,state,isDraft
gh pr view 66 --json headRefOid,baseRefName,state,isDraft
gh pr view 67 --json headRefOid,baseRefName,state,isDraft
```
These names and hashes were current 2026-09-23. Stop if moved and re-audit the diff. Current repo `main` still had 2026-09-15 governance when verified; do not mistake `main` for V19. V18 is an older docs-only handoff and V19 supersedes its current action list.

## B. N1 ORIGINAL physical metadata diagnostic only — expected quarantine
Use a clean worktree at exact PR #67 SHA `c4a893cbc98bfa736f3d44a2fe9a9ebe31dec6fa` or its verified live reviewed descendant. The ORIGINAL heavy file SHA MUST equal `f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae` and the Level-4 manifest `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`. Resolve machine paths physically; placeholders below are NOT real paths. Do not copy/rename an unrelated old NPZ.
```powershell
git switch --detach c4a893cbc98bfa736f3d44a2fe9a9ebe31dec6fa
$env:PYTHONPATH = 'src;.'
python -m pytest -q -p no:randomly --strict-markers tests/test_v5_audit_b_n1_source_lineage_v1.py tests/test_v5_audit_b_n1_physical_binding_v1.py
python scripts/agent/audit_full104_n1_source_lineage_v1_20260922.py --help
# After resolving the three ACTUAL physically authenticated paths:
python scripts/agent/audit_full104_n1_source_lineage_v1_20260922.py --heavy-artifact '<ORIGINAL_GPU_HEAVY_NPZ>' --level4-root '<GPU_LEVEL4_ROOT>' --out '<NEW_IMMUTABLE_AUDIT_RECEIPT>.json'
```
Expected original result: `QUARANTINED_SOURCE_ENCODING__N1_STOP`, CLI exit code 2, new receipt physically present. Any metadata/donor failure earlier than the known label transposition is a NEW blocker, not something to patch around. Capture file SHA, canonical receipt SHA, mismatch counts, metadata coverage, 10 original controls, test counts/zero skips. No Level-4 count blocks are opened by this diagnostic.

## C. Canonical-source DERIVATIVE — separate successor and independent review
1. Never mutate or overwrite original heavy NPZ, original producer, frozen original qualification or split receipts. Use separate new output path and explicit code/contract version. Generate **both** corrected `source_names=['HVS','NPH52','SEA_AD']` and `src_of_cell` from independently SHA-checked Level-4 metadata donor/source map. Do NOT merely swap names at a binder call site.
2. Authenticate all 8,915 metadata SHA records, exactly-once coverage of 4,553,407 selection rows, exact source donor counts [41,17,46] and cell counts [198718,236476,4118213], donor_src identity to frozen split and qualified sample; check every cell's `src_of_cell == donor_src[cell_donor]` under canonical source names.
3. Independently compare EVERY other original and derivative NPZ array by role, dtype, shape and canonical endian-contiguous value SHA (and ideally each unchanged `.npy` member's payload hash). Do not assume a metadata-only correction is safe for source-dependent numeric pools; enumerate their uses. Any changed numerical array needs independent lineage and likely reaggregation, not automatic transport.
4. Issue new SHA-256 for full new 242MB-class file and full per-array manifest. Write successor six-donor UMI/nnz qualification with the real original PR #59 sampled donor IDs and verified original numeric arrays, explicitly correct old NPH52/SEA_AD text labels; if any sample or numeric binding differs, re-run the raw six-donor comparison from Level-4 counts. State SIX-DONOR qualification scope, never 104-donor raw proof. Reissue physical N1 binder pinned to new NPZ/qualifier/split source, then run it on Windows CPU/read-only. Test original bytes rejected, substituted name rejected, tampered source values, metadata histogram-preserving permutations, overflow and non-int dtype.
5. STOP with reviewed new physical preflight receipt; **do not start N1 burden, masks, 256 target selection or precision**.

## D. Rare-tail Windows-only synthetic verification — PARALLEL
Use PR #66 exact head `f13c8364fe997d800cb84ad5370da43e75e17d3e`, which is on parallel target lineage (PR #65 reviewed V2).
```powershell
git switch --detach f13c8364fe997d800cb84ad5370da43e75e17d3e
$env:PYTHONPATH = 'src;.'
python -m pytest -q -p no:randomly --strict-markers -rs tests/ -k rare_tail
python -m pytest -q -p no:randomly --strict-markers -rs tests/test_v5_full104_rare_tail_molecular_guarded_v1.py
```
Run synthetic-only normal/abort/corruption/restart cases with zero skips. The previous Windows result BEFORE fix was 71 passed, 1 failed at `fsync(rb)`. Do not conflate #66 hosted Linux 441/441 with native Windows PASS. Recompute and independently approve NEW gateway normalized-text SHA: the old source hash is invalidated by `rb+`. Revalidate the V2 preflight file SHA `feac846b76b39f6c07b93ef3f78adeb7539b3b0a3b7933a7ec677cf003774ade` on real read-only root. The older frozen molecular runner remains directly callable: require governance-level prohibition/binding before any real expression-opening run.

## E. AFTER independently reviewed new N1 physical preflight only
Integrate synthetic-only PR #63 crash-safe runtime `59e16ab6edf3979d5cfc6d18c2f7ac2add6bb159` on a NEW successor, not blind merge into #67. Bind exact new physical source SHA, six-donor qualifier, split, exact 256 strict-core target addresses, B4 N1-only authority, V3 mask params, fixed RNG seed `1267387626254385975` as exact int, source hashes, four policies, 4 folds and 6 rungs. Full geometry 256×4×6=6144 resumable units. Add run-level source-anchored journal digest, single-writer lock and receipt contract alignment; simulate restarts, coordinated reseal and corruption/duplicate/missing/temp failures. Do not open actual N1 or any downstream protected result without separate explicit authority.

## F. Required reporting
Report exact GitHub heads, native machine/OS and dependency versions, actual physical input full SHA and sizes, first failure/exit, diagnostic/preflight receipt full canonical AND file hashes, per-array digests, 0 skipped and full test counts, all adversarial controls, changed files, open PR URLs, remaining blockers and the OFF/UNOPENED terminal state. Keep heavy dataset on GPU disk; GitHub receives scripts/small receipts/reviewed audit logs and a manifest, NOT 30GB+ counts. Any unexpected discrepancy => STOP and report.

Required terminal: `AUDIT_B_N1=UNOPENED | RARE_TAIL_MOLECULAR=UNOPENED | TD60=UNEXECUTED | PATHOLOGY_DEV_SEALED=UNOPENED | D_SHARED_G5=UNOPENED | TRAINING=OFF`.