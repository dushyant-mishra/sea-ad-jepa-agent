# JEPA independent audit — 26 September 2026

**Scope:** Live GitHub `main`, the V42 custody/handoff stack and related recent authorization, source-parity, masking and critical-test PRs (#144, #149, #156, #161, #165–#174); V42 portable manifest; physical hashes of mounted originals; selected source and workflow logs. This is an extensive *current critical-path* audit, **not** a claim to have reviewed every historical commit, every branch or all ~30 GB GPU-only scientific files. No protected outcomes or unclassified NPZ internals were read. No repository files were changed.

## Executive conclusion

- No FULL104 production training authority. Current recorded closure remains 0/33 full current V5 roots; `TRAINING=OFF`, Audit-B N1 and protected outcomes unopened.
- Engineering repairs and provenance experiments have genuinely passed scoped hosted CI; none demonstrate the original/current 33-root physical science+runtime closure.
- V42 is good custody documentation but contains at least one stale machine-readable field and omits newer parallel PR #169/#170 results. `main` still points to V25; all reviewed PRs unmerged.
- Live `main` at `c49b13bd75c2d23716c777336db8fbfc78c09cd0` reports `protected:false`; GitHub `GET /rulesets` returned `[]`. The direct branch-protection endpoint returned 403, so do not assert all admin settings were audited.

## Audited evidence

| Area | Result | Scope/limitation |
|---|---|---|
| PR #165 guard | Five successful workflows at `25447126...`; original V36 job log 20/20 exact tests. Guard source requires live closure, preexecution, critical and runtime inputs at install, arm and pre-step. | Upstream critical-test provenance still forgeable as shown in #168. Mocked mechanical positives are not real B2. |
| PR #168 critical evidence | Seven red-team tests demonstrate caller-declared `EXECUTED_PASS` and unverified source hashes in V1 authority. | No complete 33-root forgery shown. |
| PR #172 V40 | Hosted run `36252237835` has 17/17 exact synthetic preflight tests, original JUnit artifact `10909547327`. | Origin was expressly unverified by V40 itself. |
| PR #173 V41 | Independent CI run `36252411024` succeeded; source checks exact original V40 commit/run/job/artifact, SHA-256 and 17 JUnit identities. | Authenticates the original synthetic V40 run, not real full V5 critical tests. |
| PR #166 source lineage | Frozen old planner and opt-in G3 planner source digests differ; six other binding inputs identical. | Original freeze must remain unchanged. |
| PR #170 further parity | Hosted `36250218148`: seven passing physical source-identity/default-parity tests over limited synthetic fixture (including 24-row wrapper). | No real FULL104 data or new approved scientific freeze. |
| PR #169 successor | Hosted masking run `36249786388`: 924 passed in primary invocation, 918 passed in separate skip-check invocation; all four workflows successful at `e14c4003...`. | Different invocation lists: the separate fail-on-skips pass omits six tests included in the primary; fix list parity as hardening. A versioned binding repair is not permission for N1. |
| PR #174 custody | Hosted `36254314731` printed 11/11 SHA256/Git-blob matches and seven manifest-only binaries. | Checked-in manifest and checked-in bytes form one trust domain; externally pinned original portable manifest is needed for an independent custody anchor. |

## Physical local inventory audit

The supplied portable manifest has exactly 18 unique entries: 11 marked uploaded and seven manifest-only. Of those, ten original files are mounted in this current execution environment and **all ten** match the manifest's exact byte counts and SHA-256: the seven untransferred binaries, split-archive checksum CSV, `Status and Repair Plan.txt` and `WSL execution issue.txt`. The remaining eight original items are not individually mounted here; GitHub currently carries their recorded bytes or custody metadata. This does not contradict the previously recorded V42 originating-chat inventory.

The two physical discovery ZIP parts independently match their individual digests; concatenation yields exactly **607,959,761 bytes**, SHA-256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`, matching V42. Four mounted ZIPs were structurally opened for metadata only; their compressed payload CRCs and internal biological evidence were **not** reread in this audit. The opaque NPZ contents were not inspected.

## Findings, ordered by decision impact

**F01 — CRITICAL, OPEN: Current teacher-target biological identifiability.** The documented previous scalar construction can expose the answer through target count or its normalization descendants; non-query pre-normalization C/T disjoint construction remains research-only. Current raw FULL104 source replay, invariance over *every encoder-visible tensor*, q-agnostic and shared-cell-state controls, donor/source/operator robustness, zero-view estimability and independently qualified q-safe global comparator are still prerequisites. Historical ~4k cell pilot R² must not become a FULL104 qualification threshold.

**F02 — CRITICAL, OPEN: Real critical-test source and execution provenance.** #168 exposes upstream caller-declared statuses. #172/#173 prove an approach on **17 synthetic tests**, not on a scientist-approved exact real-V5 required test manifest and source/runner/environment roots. Migrate to a versioned, outside-pinned, original-provider-verified real suite before any B2 authority.

**F03 — HIGH, OPEN: Source-to-optimizer assurance remains compositionally incomplete.** #165 guard-side repairs are real, but original underlying upstream parents must each authenticate original bytes and actual execution, including the critical parent. A digest envelope or green subset must not authorize training.

**F04 — HIGH, OPEN: Prospective Phase-IV scientific decision.** #166 identifies the planner-only source move; #169 has a tested narrow successor binding; #170 independently tests bounded opt-in-off parity. Reconcile their separate implementations and choose/approve an exact prospective versioned freeze *before* N1. Retain immutable old freeze and all seven exact parent bindings. Synthetic parity alone is not G3 biological fitness.

**F05 — HIGH, OPEN: FULL104 physical qualification.** Complete audited present-day data-source hashes, all-104 raw count and donor/feature support, 41,238-address crosswalk, Morabito original RNA/ATAC H5 and native feature identities on the external GPU host. Do not infer this from old 4k research, 42-pair TRAIN cache or ZIP presence.

**F06 — HIGH, OPEN: Governance enforcement.** Live `main` has `protected:false` and repository rulesets API returned an empty array. Protected branch settings may be inaccessible under current GitHub integration (403). Review branch protection, required independent status checks and review requirements before integration; keep all drafts separate in the meantime.

**F07 — MEDIUM, CONFIRMED: V42 machine state stale.** `open_blockers` still says `missing_eight_original_binaries_remote_custody` although top-level custody and portable manifest say **seven** and the successful V42 CI confirms eleven on GitHub. Correct machine state and add cross-field consistency regression.

**F08 — MEDIUM, CONFIRMED: V42 transfer is not a complete latest-PR index.** #169 (new successor, 924/924 primary) and #170 (independent seven-test parity) are omitted. V42 represents #166 as if a successor is wholly unimplemented; now distinguish *engineering successor implemented* from *scientific approval outstanding*. Regenerate live PR/CI crosswalk rather than using snapshot heads as current without refresh.

**F09 — MEDIUM, CONFIRMED: PR #169 two test selectors differ.** Original full test invocation shows 924 pass; dedicated skip-check shows 918 pass. No observed skipped tests in either log, but the separate protective invocation should dynamically reuse the *same collection* or verify manifest identity to prevent future omissions.

**F10 — MEDIUM, HARDENING: V42 custody CI is not an external anchor on its own.** Script compares recorded hashes and Git blob SHA inside one checkout; matching both is a genuine integrity test of that version, but a coordinated rewrite of files and manifest would not be detected without a separately held signed/pinned manifest or comparing current original mounted bytes. This audit independently verified ten presently mounted originals against the separately uploaded portable manifest.

**F11 — MEDIUM, UNCLOSED: External biological validation remains scoped.** Historical Stage75 pilot is motif/proximity hypothesis, not proven eRegulons. HLA-DPA1/HLA-DPB1 crosswalk ambiguity, current V5 target-registry mapping, original Morabito gene/peak and sample pairing remain unresolved. GSE178317 development comparison with CRISPRbrain is same-study and four wells are not biological replicates; the INPP5D reuse in GSE289721 is not independent validation.

**F12 — MEDIUM, DOCUMENTARY: V42 asset language requires precise scope.** Eleven originals are in GitHub; seven are not. Several individual originals referenced by V42 are absent from *this* mounted environment while remaining retrievable from GitHub. The portable ZIP's separately described thirteen-file payload was not independently re-opened in this audit, so no fresh claim about its internal membership is made.

## Ordered repair and acceptance plan

1. **No protected scientific data or training.** Maintain `TRAINING=OFF`, Audit-B N1 unopened and 0/33 independently complete as the controlling status.
2. **Repair handoff consistency first:** correct stale `eight` field, include #169/#170 and new exact CI, and enforce internal JSON↔prose↔GitHub-branch consistency. Do not move main's pointer merely to advertise a draft.
3. **Independently review branch compositions:** #149→#156→#161→#165→#168→(#171 or #172→#173) are engineering/provenance stack alternatives; #144→#166→#170 and #144→#169 are parallel source-evidence and successor lanes. Avoid accidental combination or wholesale merge. #167→#174 is documentation/custody.
4. **Approve real critical suite prospectively, then execute and authenticate it** using source/runner/environment SHA anchors, GitHub original run/job/artifact identities and an independent reviewer. Follow with a versioned critical execution authority and integration test against live issuer and optimizer guard.
5. **Resolve teacher target and masking science before training:** physically re-derive lawful non-q raw views from current FULL104 originals, run leakage invariants and q-specific vs generic-state controls, approve q-safe normalization/globals and document masking-policy choice before protected terminal data.
6. **Prospectively sign the new Phase-IV scientific freeze** after cross-branch parity reconciliation; preserve original frozen parent, exact seven-role fingerprints and fail-closed regression behavior.
7. **Physical GPU and biological source qualification** on the other machine: SHA and source-native annotation, real original 104-donor support, raw-count crosswalk, Morabito original H5 and protected-exposure firewall. Only transfer missing assets with appropriate public-data review and channels.
8. **Independent 33-root closure and real runtime proof** only when all scientific and physical prerequisites are satisfied. Full approved GPU proof must test actual gradient/Adam movement, EMA post-step chronology, single-use cursor and crash-safe checkpoint, not old synthetic or TRAIN-cache results.

## Direct evidence links

- Live governance: https://github.com/dushyant-mishra/sea-ad-jepa-agent/blob/main/START_HERE.md
- V42 handoff: https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/174
- V42 exact asset CI: https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/36254314731
- V41 provider replay: https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/36252411024
- V36 guard tests: https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/36231569310
- V40 original 17: https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/36252237835
- Masking 924 primary: https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/36249786388
- Independent G3 parity: https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/36250218148

**No changes were pushed or merged as part of this audit.**
