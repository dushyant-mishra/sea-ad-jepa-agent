# GPT independent review of Macha PR #523 and flat main landing — 2026-11-02

**Classification:** `ACCEPT_SCOPED__STUDENT_FIXTURE_HARDENING_AND_MAIN_HOSTILE_REGRESSION__NO_RUNTIME_OR_SOURCE_ATTESTATION`. **No biological/scientific authority changed.** This is a new engineering/reviewer chronology event, not a rerun or replacement of #516, #518, #507, #512 or older history.

## Exact custody and acts

- Previous consolidated main: `e4925cffc9a9da2e4c05e79f000c1233e63ff4bf` (squash #522).
- Macha original independent hostile review: PR [#523](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/523) review branch `review/macha-main-e4925cff-security-20261102`. Tests-only initial commit `6f825acd07e18a51e08b54a3c85351367c5f8497`, 12 expected RED witnesses; repair head `bce3a35a9cd8ec364906798738c14ab3236cc583`.
- Macha report and machine receipt already appended to #322: `docs/agent/JEPA_MACHA_MAIN_E4925CFF_INDEPENDENT_REVIEW_20261102.md`, `results/target_discovery/unified_qualification_v1/JEPA_MACHA_MAIN_E4925CFF_INDEPENDENT_REVIEW_20261102.json`. Previous chronology event 17 preserves independent verdicts.
- **Independent GPT reviewer decision:** [review comment on #523](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/523#issuecomment-6589689736), after source/patch/test/workflow inspection; **no independent physical Docker or Windows/WSL run by GPT**.
- **Accepted and merged:** PR #523 was marked ready and merged by **squash**, main exact integration commit `971ec6a14a9435ffc9fe03b1373c3ec3f5a30687`. Main had not drifted before this merge. The V2C verifier remains original repaired Git blob `46b813fcbf598e12a2a9f209ca254d01aaeba784`. Merged entrypoint Git blob `ceb7d25ec0501b66a791463372aa2e363449bb39`; merged Dockerfile Git blob `1414d02c14a62f658e82a03b962448e35bd03ecc`.
- **PR #523 repair-head CI:** [41517891013](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41517891013) SUCCESS, reviewer container test 21/21; [41517891053](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41517891053) SUCCESS, inherited author Docker 9/9. **Original RED-first run** [41517539396](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41517539396) has expected container job FAILURE with 12 RED before repair. Macha's original #516/#518 suites are Git-blob-checked in the new main workflow and archived at original PR heads. These are hosted engineering receipts, not a real-data test.
- **Postmerge main push workflows:** inspect on the exact `971ec6a14a9435ffc9fe03b1373c3ec3f5a30687` when queued/completed. At first postmerge query, zero workflow runs were returned; **no postmerge success claimed** by this report.

## Scoped verdict, independent source reasoning

1. **Root-owned package:** Replacing three `COPY --chown=65534:65534` lines with `COPY` creates root-owned verifier/entrypoint/manifest while the image continues to run as uid/gid 65534; this closes the documented ability of the runtime user to rewrite its packaged verifier if the readonly-root flag was omitted.
2. **Fail-closed default entrypoint:** `_runtime_restricted()` now runs before reading stdin or loading V2C. It checks effective uid/gid/groups, five capability sets, `NoNewPrivs=1`, seccomp filter mode, loopback-only interfaces, one visible PID, read-only allowed mounts, `pids.max=1`, and cgroup memory at most 256 MiB. The 11 original weakened-launch RED variants (including `/dev` submount and teacher mount) are reported GREEN after the repair. The original V2C acceptance scope and D1 equation are unchanged.
3. **Durable regression:** The flat main CI carries original Macha #516/#518 hostile tests, SHA-checked, plus main-native launch/container tests, catching the original role/snapshot regression that the former author D1 suite did not catch. Two original legacy-#502 same-user launch witnesses are deselected because their legacy module no longer exists in main; these still apply unchanged to the historical heads. No old RED was erased or reinterpreted as a passing old revision.

## Explicit unqualified gaps — do not turn into a security or biology PASS

- **Execution-origin and mount provenance are not attested.** The guard inspects mount target/options/filesystem rather than authenticating origin. A source-level ambiguity remains at whitelisted default mount targets, e.g. `/etc/hosts` permits any read-only mount with that target and `/dev/shm` permits allowed fs types. This is a **logical guard limitation, not a physically reproduced Docker bypass**. Require external trusted launcher/engine configuration and independent verification before any stronger deployment claim.
- A hostile operator can override `--entrypoint`; the Docker daemon/VM/kernel is outside this trust boundary. Desktop's outer seccomp can mask `seccomp=unconfined`; `--ipc host`, hostile binds at allowlisted points, side channels, GPU isolation, process kill/cancellation and reproducible base-image identity are not qualified. A mandatory launcher, content-pinned base/image, CPU+wall-clock bounds, `--ipc` policy and native-Linux versus Desktop security decision remain open.
- The V2C consistency receipt is unsigned and forgeable by a party that knows the public algorithm. `expected_policy` and source measurements are self-supplied. External source-rights issuer/trust root, alias-class closure (UBE2R2-AS1, MIR4307HG/LINC02588), query-independent roster/depositor QC, donor/specimen/physical identity, NPH52 expression and C1/C2/C3/C6 source evidence-right bindings remain blocked. A fixture receipt cannot be used to authorize Task7/8 or training.
- Downstream post-TD #351/#517 five REDs, Task4 cumulative qualification, production-synthetic V3.1.1 genuine Task4, teacher target and independent biology are separate work with prior source-specific limits; do not redo settled historical ETL or experiments.

## Next lawful action and successor routing

1. Recognize **main `971ec6a14a...`** as the active code landing; #523 is merged provenance, not another implementation branch. Publish current exact-main postmerge workflow states without anticipating results.
2. Refresh the `main` startup router at the next appropriately reviewed flat governance/integration increment: any older wording that says Macha's exact-main review is pending is now historical. Active #460 top pointer controls immediate navigation meanwhile.
3. Advance a **small, independent** trusted-launcher/engine-attestation architecture decision and upstream source-rights/alias/roster evidence; do not call the self-check attestation.
4. Keep appending evidence to #322 and update #460 at each meaningful implementation, negative result and acceptance. Do not create parallel historical audit or stack implementation PRs.

**Terminal:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
