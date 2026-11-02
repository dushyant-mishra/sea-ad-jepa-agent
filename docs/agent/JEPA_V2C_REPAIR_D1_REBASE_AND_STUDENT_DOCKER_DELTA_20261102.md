# JEPA V2C entry-guard repair, D1 rebase and restricted student runtime — 2026-11-02

**Disposition:** `IMPLEMENTATION_AUTHOR_GREEN_WITH_PENDING_INDEPENDENT_MACHA_RECHECK__NO_SOURCE_AUTHORITY`. New forward engineering work; preserve historical experimental and source custody. This record supplements Macha's independently reviewed and merged [#519 audit](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/519) and [#520 handoff](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/520), not a reclassification of their scope.

## Independent review incorporated

- Macha [#516](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/516) immutable head `881194aec9d99a9d42cbf206ffcb779429c4e768` reviewed old #514 `63099f6b17b14bcfcfd92b0334bf564e9cf8376d`: **REPAIR_REQUIRED**; four entry-guard RED from hostile top-level dictionary keys and receipting teacher-labelled snapshots. Original #507/#512 14 RED remain valid for legacy #502/#510. No evidence that teacher-hidden values leaked via V2C itself.
- Macha [#518](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/518) immutable head `32c0a22b9ae6220ed03fe7d6e944da753c0e4a0c` reviewed old #515 `fa06d486d5f8a130ff545690a8f0b12773c4f85d`: **ACCEPT_SCOPED** for D1→V2C composition only, conditional on repairing inherited V2C and independent recheck. Neither review authorized OS deployment or source-rights issuance.
- Macha's exact test blobs: V2C #516 `8647c07a893d932ffa5f05a79be50c89c3c28b53` and D1 #518 `2a63a753081012e10a9c6cb39b80e79d16848ebe`. Immutable review branch sources must be replayed without modifying tests or coercing a pass.

## New GPT implementation

| Branch/PR | Exact source head | New delta |
|---|---|---|
| [#514 V2C](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/514) | `df83525b25ac1278fcb331b078f8c59e84097404` | Before dict.get, require all top-level keys are exact strings. Read role once. Recheck `view_kind` on private snapshot before validation. New V2C blob `46b813fcbf598e12a2a9f209ca254d01aaeba784`. No other verifier logic changed. |
| [#515 D1 composition](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/515) | `6c74ba41ef4537dc4474d36fd966538976451089` | Exact-tree git rebase, parent is repaired #514 `df83525b`, preserving producer `edee1b8a` and old review commit via #518 branch. The inherited V2C blob matches repaired #514 byte-for-byte. |
| [#521 student runtime](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/521) | `09a5fc58f3690bef7a8a317d92d0f4b97a267a03` | New V2C-only minimal Docker image builder/entrypoint and restricted Linux execution. Rebased onto repaired #515. Versioned 1 MiB JSON protocol, non-root uid, read-only root, no network, no capabilities, no-new-privileges, pids-limit 1, 256 MiB and isolated Python. No #502, teacher/private registry or producer in image. New image input pins repaired #514 V2C Git blob. |

**Source/CI evidence.** On old #521 initial unpatched source, dedicated [run 41504771526](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41504771526) passed nine Linux Docker checks. After repair/rebase, [run 41505425630](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41505425630) and [run 41505630513](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41505630513) also reported Docker SUCCESS on repaired source; these establish only the documented CI runner restrictions. #514 exact head author CI 6/6 SUCCESS, #515 exact rebased head author CI 6/6 SUCCESS.

**Frozen reviewer replay.** New author CI fetches the #516/#518 files by exact immutable commit and verifies their raw Git blob SHA-1 before running them against the *repaired* source. An initial sparse review workspace omitted the legacy #502 import that Macha's **limitation** tests deliberately exercise; the remedy restored the old module in the **test workspace only**, never in the student image. Subsequently all 86 unchanged reviewer assertions passed on Linux, but that attempt's workflow failed at a YAML echo note containing an unescaped '#' comment. The note was corrected **without modifying reviewer tests, science source or Docker restrictions**; final exact-head replay [run 41505805055](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41505805055) must be checked for its final conclusion. No independent Macha acceptance is claimed from author replay.

## Remaining unresolved science/security

- **Issuer:** a consistent self-supplied policy and public receipt remain forgeable. Source-rights signer/trust identity is not provisioned. A consumer must not promote a V2C receipt into Task7 source authority.
- **Alias:** current expected-policy schema lacks canonical alias-class/right restrictions; synthetic UBE2R2-AS1/legacy address coexposure leaks hidden query count through base D1, and MIR4307HG query issuance is accepted without source-level block.
- **Selection:** q-dependent depositor detection/QC gates can change the cell roster, leaking q detection even if values are redacted. No independently authenticated source roster, feature map or specimen/region/technology identity exists.
- **Deployment:** Docker fixture proves no-network/no-fork/no-root-write and code exclusion for a restricted **hosted Linux fixture**, not malicious daemon/kernel breakout, side-channels, host flag immutability, real Windows/WSL/GPU isolation, signed image provenance or physical issuer authority. Python base image tag remains mutable and is **not digest-pinned**. Macha's older finding about `python -I -S` launch with readable host legacy source remains valid **for the old unisolated launch**; Docker isolation evidence is a distinct new deployment setup.
- **Scientific:** selected targets, C1/C2/C3/C6 biological qualification, full Task4/5, Tasks6–8 real authority, training, Stage4 remain OFF.
- **Reviewer:** Macha independent recheck requested against repaired exact #514, rebased #515 and then #521 Docker security tests. No GPT self-acceptance.

## Permanent continuity

Each future substantial engineering or science delta requires: owner/reviewer PR exact SHAs and test evidence → **audit #322** append-only source-pinned note and chronological JSON event, verified GitHub Actions → **handoff #460** latest top-of-file exact audit pointer, current owner/reviewer separation and next legal action, verified handoff Actions. Macha-authored #519/#520 were merged into these canonical branches; their records remain immutable and must be cited by successors. Preserve original negative scientific results and #507/#512/#516/#518 reviewer evidence; no duplicate historical crawl.

**Standing:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
