# Event96 — resolve Event68/90 canonical V5 runtime source-locator mismatch against original PR224 (NO EXECUTION)

**2026-11-05; independent original-source audit, not a new runtime implementation, executed experiment, training authorization, numerical reproducibility proof or modification to older events.**

## Reason for this narrow follow-up

Event68's source table listed `src/sea_ad_jepa/v5/canonical_runtime.py` as the V5 canonical runtime at original PR224 `9d00684e08ba34ef8d7b04e478b9c380cd36d537`. Event90 independently fetched that exact path and correctly reported HTTP 404, then marked the **runtime locator** unresolved. That last status does **not** imply the original guarded V5 runtime was absent: the source file was misnamed in the Event68 table.

## Exact original PR224 source and supported role

Read the actual original PR224 source at commit **`9d00684e08ba34ef8d7b04e478b9c380cd36d537`** (not a guessed replacement):

| Role | Exact original source file | Git blob SHA-1 |
|---|---|---|
| **Canonical guarded one-update entrypoint** | `src/sea_ad_jepa/v5/inactive_guarded_update_v1.py` | `59647eb0122dfd98068844f68b6d48c2c33d67ca` |
| Bounded model/EMA-mechanics consumer; accepts caller-provided mutation callbacks | `src/sea_ad_jepa/v5/inactive_update_reference.py` | `ab266faa31ac7d3e51acf695a7deff1702368cde` |
| Guarded optimizer authority contract | `src/sea_ad_jepa/v5/prefreeze_runtime_authority.py` | `41a6ebde613ee3ec5c898fa39e5a212c14eaac66` |
| Encoder reference with keyed dropout and packed evidence | `src/sea_ad_jepa/v5/keyed_dropout_prototype_v2.py` | `0fd06ae0891625924761ef097b20ba6e11495cb3` |
| **Original explicit canonical-runtime convergence tests** | `tests/test_v5_canonical_runtime_convergence_red.py` | `33d62e1a96e44b375467da3d88ee49f8430fc2fd` |

The wrapper's original module docstring identifies it as `Canonical guarded wrapper for the inactive V5 one-update mechanics harness`. The function `run_guarded_inactive_reference_update` requires `PrefreezeMechanicalAuthorityV1`, binds `PrefreezeOptimizerGuardV1`, delegates loss computation to `run_inactive_reference_update`, and owns guarded backward, optimizer completion and EMA callbacks; its output explicitly says `training_authorized=False` and `execution_authorized=False`. This is **narrow, nonauthorizing rehearsal mechanics**, not a production multiple-update trainer, physical RNA-based qualification or full restart proof.

The original convergence test points `RUNTIME = Path("src/sea_ad_jepa/v5/inactive_update_reference.py")`, prohibits direct teacher EMA mutation in that consumer and rejects a duplicate generic rehearsal runtime; it **does not refer to or require `canonical_runtime.py`**. The separate guarded wrapper is the original entrypoint.

**Independent cross-ref equality:** read all five source/test paths at PR224, PR525 head `b493efc35af20bcf2adee29c47376e1dbf4b6dcd`, and V5 guarded U0 PR548 head `cde03f738c758694aa66211b5021603af943675b`; each has the **same exact corresponding Git blob SHA-1** across all three heads. These are the same original implementation, not three distinct rewrites. In particular, PR548 already documented this at `docs/agent/JEPA_20261104_SYNTH2048_EXACT_LATEST_MODEL_RUNTIME_AUDIT.md` (Git blob `6aed686ba7b942862f68cc603c537251cd9b21ac`); the novel correction is **reconciling the Event68/90 bad path**, not rediscovering or rebuilding PR548.

**Critical old-main trap:** on checked default `main`, `src/sea_ad_jepa/v5/inactive_update_reference.py` is older blob `3dc61b629c1d4723e7df058f72c1497c4b4c6c20`, which still contains directly reachable `optimizer.step()` and teacher-EMA mutation, while `inactive_guarded_update_v1.py` is absent. Do **not** substitute main simply because the file name matches. Use exact original source head and accepted guarded successor, without inferring authorization.

The file `src/sea_ad_jepa/v5/canonical_runtime.py` is **confirmed not found** at original PR224 exact head; it must remain marked `LEGACY_PATH_INVALID`, not renamed to exist or falsely claimed as a real tracked file.

## Supersession and practical implications

- **Event68, lines 101/167**: the literal canonical-runtime file path is incorrect. The correct source role resolves to **guarded wrapper + separated V5 consumer + authority**, pinned above; the historic 40-step statement does not give new execution rights.
- **Event90 source-localizer row**: its 404 finding remains true, but `ERRATUM_OPEN__LOCATE_ORIGINAL_OWNER_PR` is **closed by this exact PR224 source inspection**, not by treating the nonexistent path as present.
- **No-repeat:** do not build another EMA/trainer, recrawl PR224/525/548, or have Macha rediscover this already-source-pinned runtime. The genuine new tasks are its integration with #575/#576/#577/#579/#578 and reciprocal exact-head adversarial review, with no actual optimizer step absent separate owner approval.
- V80 backup remains `OWNER_CONFIRMED_PERSONAL_DOWNLOAD_COMPLETE__V80_BACKUP_RESOLVED` per Event95; original sealed controller remains private, unopened and outside public Git.
- No original historical Event68/90 row is changed, no original test is modified, no source code is changed; this is additive exact-source correction. Static source and Git SHA verification only; no tests or model executions were launched.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
