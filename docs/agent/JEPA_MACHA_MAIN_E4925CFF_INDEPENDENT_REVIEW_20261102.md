# Macha independent review of consolidated main `e4925cff` (2026-11-02, append-only)

**Status:** `INDEPENDENT_HOSTILE_REVIEW__NO_AUTHORITY_PROMOTED`. This records Macha's verdict on the consolidated main implementation. It adds one flat proposal PR against main ([#523](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/523)), which GPT must review; Macha does not accept its own repair. Only synthetic canaries were used. No protected expression, NPH52 quarantined cells, DEV/SEALED, pathology or source credentials were touched, and no issuer identity was created.

## 0. Custody

| Surface | Identity |
|---|---|
| Main under review | `e4925cffc9a9da2e4c05e79f000c1233e63ff4bf` (tree `c13c5a01`, identical to the #522 head `5f6e81aa` tree); unchanged throughout the review |
| V2C verifier | blob `46b813fcbf598e12a2a9f209ca254d01aaeba784`; the diff from the reviewed `360d3bcc` is exactly the #516 three-line entry repair |
| D1 producer | blob `edee1b8adc1b5c7ca660d52d3667d2020abdb417`, unchanged since #518 |
| Immutable reviewer evidence | #516 `881194aec9d99a9d42cbf206ffcb779429c4e768` (file blob `8647c07a`); #518 `32c0a22b9ae6220ed03fe7d6e944da753c0e4a0c` (file blob `2a63a753`); #507/#512 files `d5981430` / `1a915431` |
| Pinned audit / handoff at assignment | #322 `40aed21385e8a3171b9cb333abef4de2250a4c69`; #460 `6855dea510e2396b8566df870c90defa93a1d2f1`. Both moved during the review (GPT historical-recovery commits); this delta is appended on the live heads. |
| Proposal PR | [#523](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/523): `6f825acd07e18a51e08b54a3c85351367c5f8497` (tests only, RED), then `bce3a35a9cd8ec364906798738c14ab3236cc583` (proposed repair) |
| CI, RED commit | [41517539396](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41517539396): regression jobs Ubuntu + Windows SUCCESS (84 passed, 2 deselected; main-native 2/2); container job FAILURE as designed, 12 RED / 9 passed; the author's 9 container tests passed in the same job |
| CI, repair commit | [41517891013](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41517891013): all SUCCESS (container job 21/21, so all 12 RED turned green; regression jobs Ubuntu + Windows 84 passed, 2 deselected, plus main-native 2/2; author 9/9 in the same job). The author's own container workflow [41517891053](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41517891053) also passed 9/9. Repaired image in CI: `sha256:b7e5ea46937cd146f3d6b756d773a965aa57a406f345ba24d4c678fbe573dc0c`. Local Windows: 21/21, author 9/9, immutable suites 84 passed with 2 deselected, author D1 75/75. WSL client: 20 passed, 1 skipped (the git-tree test, because the Windows worktree's `.git` pointer does not resolve under WSL). |
| CI engine | Ubuntu 24.04.5, kernel 7.0.0-1017-azure, Docker 28.0.4, cgroup v2, AppArmor + seccomp; image `sha256:b02c589654d9341b7277c9b7c6d8d1a95429fb84cff81b04d44f2a90426325f4` |
| Local engine | Docker Desktop 4.44.2, engine 28.3.2, WSL2 kernel 5.15.167.4, cgroup v1, seccomp only (no AppArmor). Windows and WSL clients reach the same engine (ID `6f2f1271`). |
| Local images | Windows-built `sha256:46589029dd20…`; WSL-built `sha256:462a9911e010…`. Build-context file modes differ (755 vs 644), so the image ID depends on the build host. |
| Base image | `python:3.11-slim-bookworm@sha256:94a8fee35252d06ab75856f15f12c7bae67b10e8a6da93c7fded82b2610926cd`, identical in CI and locally. The author CI step that should record the base printed "No such image", so the author run recorded no base identity. |

## 1. Verdict matrix

| Area | Verdict |
|---|---|
| Repaired V2C verifier `46b813fc` | **`ACCEPT_SCOPED`**: fixture consistency of an unauthenticated, self-supplied view and policy |
| D1 base-only composition `edee1b8a` | **D1 computation law `ACCEPT_SCOPED`**; upstream source authenticity **`NOT_AUTHENTICATED`** |
| Student container isolation | **Demonstrated under the documented flags only.** 2 defects: **`REPAIR_REQUIRED`**, with a repair proposed in #523. Host and kernel isolation **`NOT_TESTED`**. |
| Source-rights authentication | **`NOT_AUTHENTICATED`**. Real human-source issuance **`BLOCKED`**. |
| Main regression CI | **Insufficient.** Main's CI passes 75/75 against the unrepaired V2C `360d3bcc`. #523 proposes the fix. |
| Downstream scientific authority | **Blocked.** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED` |

## 2. V2C verifier: `ACCEPT_SCOPED`

**Original #516 cases, replayed unchanged:**
- The 4 original RED cases now pass on main: `test_red_role_check_runs_attacker_equality_before_the_snapshot[poisoned_truth|raising_eq|str_subclass]` and `test_red_receipt_is_issued_for_a_snapshot_whose_role_was_never_checked`.
- **Pure main, #516 and #518 files together:** 84 passed. The 2 failures are the launch witnesses (one per file) that import legacy #502, which main no longer has. #516 alone gives 57/58.
- **Ephemeral workspace** (main plus the legacy `td_unified` closure from `63099f6b`, in a scratch directory and never committed): 86/86.
- **Platforms:** identical on Windows numpy 2.4.6, Windows numpy 1.26.4 and WSL numpy 1.26.4.

**Historical failures preserved on the old heads:** #507/#512 give 14 RED / 40 against the legacy #502/#510 modules, and #516 gives 4 RED / 54 against the old V2C `360d3bcc`.

**Properties now demonstrated:**
- No caller code runs before the snapshot. Only exact `str` top-level keys are iterated, with no lookup dispatch.
- A teacher-labelled snapshot cannot get a receipt, because the role is re-checked on the snapshot.
- Hostile values give a constant refusal: 29 hostile kinds × 10 positions.
- There is no membership oracle. Teacher candidates get one world-independent response across 2,049 candidates × 4 worlds, and the verifier has zero audit events and no module state.
- The receipt binds the complete view, roster, operator states, rights and policy (11 policy and 14 content variants).
- Fresh read: every post-snapshot operation acts only on exact built-ins. For accepted inputs the CR-folding encoder is injective, because tokens exclude control characters.

**Scope exclusions:** none of these were tested.
- Concurrent mutation by another thread in the caller's own process. The caller has that authority anyway; my probe had no positive control and is not evidence.
- Authenticity of the self-supplied policy.

## 3. D1 → V2C: the law is accepted, the source is not authenticated

**Accepted, as the D1 computation law.** The #518 file runs unchanged: 27/28 on pure main, where the one legacy-#502 launch witness cannot import #502, and 28/28 in the ephemeral workspace.
- D1 equals the sum of the permitted measured base counts across 300 random worlds. It is never the physical total.
- Query, collision and off-ledger counts cannot enter. Injecting them gives one value-independent refusal (5 kinds × 1,027 values).
- Hidden-value changes leave acceptance, refusal and visible output unchanged (120 worlds × 6 hidden variants).
- The four observation states stay distinct.
- Forgeries gain no authentication flag.
- No V2B or teacher-aware module is imported.

**Not authenticated: these limits still reproduce on main.**
- **Alias leak:** the UBE2R2-AS1 alias recovers the hidden query count exactly through D1, and MIR4307HG is accepted as a query. The policy has no field for alias classes.
- **Roster leak:** a depositor detected-genes cutoff that counts the query changes the roster, and so leaks detection.
- **Self-supplied policy:** a pseudo-address makes D1 equal the physical total, and a wrong support state turns structural absence into measured zero.
- **Receipts:** they are unkeyed and mintable without running V2C, and the producer returns only the view.

A matching fixture comparison is not authenticated source rights.

## 4. Student container: what is demonstrated, broken and untested

**Demonstrated** locally and in CI, but only when the launcher supplies all documented flags:
- **Identity and privilege:** uid/gid 65534, all capability sets empty, `NoNewPrivs=1`, seccomp in filter mode.
- **Network and processes:** loopback only, no route, no host-canary connection; fork and thread creation denied; one visible PID.
- **Filesystem:** read-only root and engine files.
- **Imports:** `sys.path` is stdlib-only, and `scripts`, `pip` and `deployment` are not importable.
- **Code excluded from the image:** a filename scan finds only public CA bundles and stdlib `secrets.py`. The build context is exactly the 4 declared files with no credentials. The image environment has no secrets and no RUN, ADD or ARG layers.
- **Receipts:** byte-equal to host V2C.

**Broken** (`REPAIR_REQUIRED`; see §7):
- **D-1:** the runtime user owns its verifier files.
- **D-2:** the shipped entrypoint serves receipts under any launch.

**Gaps and limitations**, characterized by `test_limit_*` tests:
- **Launcher-dependent mounts:** teacher files are absent only because nobody mounted them. One `-v` reads the canary under every documented flag. On Windows, Docker Desktop file sharing exposed it under default temp-folder permissions; from WSL only host mode 0700 blocked it, and mode 755 exposed it.
- **Default launch:** reaches the host's loopback services through `host.docker.internal` (canary connected from both clients). It also allows fork, gives a writable root and sets `NoNewPrivs=0`.
- **`--pid host`:** shows VM processes.
- **No CPU quota or engine-side deadline:** CPU-bound code survives a killed client (measured at about 100% CPU after 39 s). The shipped entrypoint exits once a killed client closes stdin.
- **Extra writable paths:** `/dev/shm` (64 MiB) and `/dev/mqueue`, which the README does not mention.
- **Setuid binaries:** 11 setuid/setgid root binaries are present, neutralized only by `no-new-privileges`.
- **Unpinned identity:** the base tag is mutable; `build_context_v1.py` pins only the V2C blob, not the entrypoint or Dockerfile; and image identity differs between Windows and Linux builds.

**Engine-dependent:**
- **Local engine weaker than CI:** Docker Desktop has no AppArmor, unlike the CI runners.
- **Seccomp unobservable on Desktop:** its outer seccomp filter reports `Seccomp: 2` even under `seccomp=unconfined` or `--privileged`.

**Not tested:**
- container breakout;
- kernel, VM or Docker Desktop compromise;
- side channels;
- GPU passthrough;
- a hostile Docker operator.

Membership in the `docker` group is root on the VM.

**A receipt attests nothing about the runtime.** Every protection is a launch flag, not an image property.

## 5. Main regression CI: insufficient, specific missing coverage

- **Revert undetected:** main's `jepa-student-v2c-d1-fixture.yml` runs only the author D1 test, which passes 75/75 with the unrepaired V2C `360d3bcc` restored, so it cannot detect a revert of the #516 repair.
- **Docker coverage:** the container workflow runs only on `pull_request` and `workflow_dispatch`, not on pushes to main. Main's own Docker evidence is the #522 pre-merge run 41509613313 on an identical tree.
- **#523 proposes:**
  - the byte-identical #516/#518 suites, blob-checked, with the two legacy-#502 witnesses deselected and replaced by main-native equivalents;
  - one container job on pushes to main and on pull requests.

## 6. Issuer and scientific boundary (unchanged; dependencies remain unresolved)

**Sources:** #513 `0b1af4f06ba423753899e7c564d3b16ce609ac6a` (open, metadata only) and this audit.
1. **Signing and trust:** no authenticated external signing authority or consumer trust root exists. `JEPA_SOURCE_RIGHTS_ISSUER` has no signing identity, and none was created.
2. **Alias closure:** canonical source-feature and alias closure is open.
   - 18 legacy/current pairs over 11 query addresses were adjudicated in #513.
   - UBE2R2-AS1 has a provisional shared restriction.
   - MIR4307HG and LINC02588 are blocked.
   - V2C cannot express alias classes.
3. **Query-independent selection:** query-independent cell selection and QC evidence are absent.
   - The depositor filters for NPH52 are contradicted, because the selection was imported.
   - A query-dependent roster is demonstrated synthetically.
4. **Identity:**
   - Donor, specimen and physical measurement identity are unauthenticated.
   - The SEA-AD `sample_id` is nucleus-level, not a specimen key.
   - NPH52 and SEA-AD tissue-block specimen keys are unavailable.
5. **NPH52:** expression issuance is blocked, and the 22,715 quarantined reader-fit cells stay unopened. The #513 §4 protocol was neither approved nor run.
6. **Downstream:** Task4–8 qualification, the post-TD #517 REDs, and trainer and Stage 4 authorization all remain blocked. D1 is selected and D2 excluded.

## 7. Defects

| ID | Source path | Reproducing test (#523) | Expected | Observed on main | Severity | Smallest repair (#523 `bce3a35a`) |
|---|---|---|---|---|---|---|
| D-1 | `deployment/student_v2c/Dockerfile.v1` | `test_red_the_runtime_user_owns_and_can_rewrite_its_own_verifier` | The packaged verifier, entrypoint and manifest are root-owned and not writable by uid 65534, even without `--read-only` | Owned by 65534 (`COPY --chown`). With `--read-only` omitted, all three can be opened for writing. | Low–medium (defence in depth; needs a weakened launch or code execution) | Drop `--chown=65534:65534` from the three COPY lines |
| D-2 | `deployment/student_v2c/entrypoint_v1.py` | `test_red_default_entrypoint_serves_receipts_when_a_mandated_restriction_is_weakened[11 cases]` | The shipped entrypoint refuses unless the documented restrictions are observable | Serves a receipt with no flags at all, and under each of: writable root, default network, kept capabilities, new privileges allowed, no PID or memory limit, root user, host PID namespace, a teacher bind mount, a host tmpfs bound under `/dev` | Medium (the boundary rests on every launcher remembering every flag; the README presents the flags as the fixture) | A fail-closed self-check before stdin, using the existing constant refusal. It is not an attestation. |

**Mutation audit** (author self-audit, scratch mirror, local engine):
- The proposed repair turns 12/12 RED green with no guard or limit regression.
- R1 and R2 each fix only their own REDs.
- Each guard is killed by its planted defect: a baked teacher file, a missing `USER`, a tampered receipt, changed refusal bytes, and five mandated flags each removed.

**Self-audit rounds:**
- **Round 1** added an image `USER`/`ENTRYPOINT` guard. Without it, dropping `USER` would go undetected because the flags override it.
- **Round 2** removed an unsatisfiable `seccomp_unconfined` RED, because Docker Desktop's outer filter makes it invisible.
- **Round 3** found that a prefix mount rule in R2 admitted a host tmpfs bound under `/dev`. R2 now uses exact engine mount points, and a RED case covers it.

## 8. Next

1. GPT independently reviews #523. Macha does not merge or accept it.
2. If GPT accepts it, main gains continuous #516/#518 and container regression coverage.
3. The remaining isolation decisions need an owner:
   - a deployment launcher with fixed flags, an image-digest pin and `--cpus`/`--ulimit cpu`;
   - an `--ipc` policy;
   - a decision on Docker Desktop versus native Linux;
   - GPU passthrough.
4. The issuer, alias, roster and identity dependencies in §6 stay external; see GPT's correction memo items 2–5.

**Terminal:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
