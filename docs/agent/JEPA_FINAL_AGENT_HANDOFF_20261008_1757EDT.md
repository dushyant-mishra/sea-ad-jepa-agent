# JEPA final new-agent handoff — 2026-10-08 17:57 EDT

## Status and scope

This is a **non-authorizing, cold-start takeover checkpoint** for the next agent. It supersedes the earlier same-day conversational checkpoint as the first general state document a new agent should read, but it does **not** delete or replace the older custody documents.

**Critical target-discovery custody update:** PR #237 does not physically mirror every historical target-discovery primary artifact. Before searching for TD34/Nott/SCENIC+/NIH-CARD files, read:

`docs/agent/TARGET_DISCOVERY_PRIMARY_ARTIFACT_LOCATOR_20261008.md`

and:

`docs/agent/TARGET_DISCOVERY_CUSTODY_UPDATE_20261008.md`

The historical `JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.zip` has now been physically recovered in the current chat environment and authenticated against its historical SHA-256. The original TD34 producer bytes were recovered from that package and match the historical recorded producer digest exactly. Authority-critical recovered text bytes and a 97-file checksum inventory are now copied into:

`custody/target_discovery_20260907_recovered/`

The remaining TD34 custody question is no longer “where is the producer?” It is the narrower upstream binding problem: recover/hash-bind `FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz` or an authenticated equivalent common-support vector so the four exact 512-address panel memberships can be independently reconstructed and hashed.

Read this together with:

- `docs/agent/TARGET_DISCOVERY_PRIMARY_ARTIFACT_LOCATOR_20261008.md`
- `docs/agent/TARGET_DISCOVERY_CUSTODY_UPDATE_20261008.md`
- `docs/agent/JEPA_COMPLETE_TAKEOVER_20261008.md`
- `docs/agent/JEPA_NEW_AGENT_HANDOFF_20261008_1518EDT.md`
- `docs/agent/V77_BOUNDED_SYNTHETIC_MUTATION_REHEARSAL_CONTRACT_20261007.md`
- `docs/agent/V77_BOUNDED_SYNTHETIC_MUTATION_REHEARSAL_AUDIT_20261008.md`
- `custody/takeover_20261008/MANIFEST.json`
- `custody/takeover_20261008/PR230_PRIOR_HANDOFF.md`
- `custody/takeover_20261008/s174_working_snapshot/`
- `custody/target_discovery_20260907_recovered/README.md`

Immediately before the original version of this file was written, PR #237 was open, draft, mergeable at head `438640ee91de310768d02b5f5e342696e166445e`. It has since advanced through documentation/custody commits. Re-read PR #237 before relying on any recorded “latest” SHA.

PR #237 branch:

`handoff/jepa-20261008-complete-runtime-s174-takeover`

Base:

`impl/v77-bounded-synthetic-mutation-20261007`

Base SHA:

`8495c9f0a753dbb25c90bc27e65f28c4ee2e471e`

This checkpoint and its custody successors are documentation/custody-only. They do not modify runtime code, tests, workflows, scientific outputs, or scientific authorization state.

---

# 1. Executive takeover state

There are **three distinct lanes**. Do not collapse them.

1. **Runtime/provenance lane.** The project has one audited, preregistered, synthetic-only guarded optimizer update with post-step EMA and deterministic fresh-module restore. That is a bounded runtime proof, not real-data training authority.
2. **Synthetic-science/S174 lane.** The HVS/SEA-AD feature-axis defect was prospectively repaired and replayed. The current live S174 branch is newer than the snapshot carried in PR #237; consult the artifact locator before judging any old RED state as current.
3. **Target-discovery lane.** Historical target work is substantially more mature than “find a target tensor,” but exact TD34→TD60 and multimodal genealogy must be reconstructed from primary artifacts. The Sept. 7 primary custody package and authentic TD34 producer are now recovered; several later artifacts still live only on historical branches, and some upstream/external execution assets remain to be located.

The next agent must use a **defect → repair/recovery → verification → supersession** method. Do not treat an old audit finding as current merely because it is well documented, and do not treat a later prose handoff as a repair without primary evidence.

---

# 2. Canonical runtime lineage and current authority

Known canonical chain:

- PR #224 runtime head: `9d00684e08ba34ef8d7b04e478b9c380cd36d537`
- PR #226 shared qualification interface: `e83bb8d90bbabefdfe6bfa7c5dfff994d7a41005`
- PR #228 joined V77 ZERO_UPDATE: `6282b59c7bd961c0dfb99d3cb24bdd55fe2526f7`
- PR #232 physical provenance successor: `d3430ce6c0e878272e92b61e01822334e088d8c8`
- PR #233 2K operator-smoke CI successor: `c919d957de79a3866fdaeab3ae2ae5a0891d4859`
- PR #234 pre-rehearsal freeze: initially `0ec385889630b3a7f02caa489d95d988304ad9dd`
- PR #235 preregistered bounded-mutation design: `71a3d6d84a36e1812ffd776153d48948bd8b945c`
- PR #236 audit-record head: `8495c9f0a753dbb25c90bc27e65f28c4ee2e471e`

The bounded synthetic rehearsal contract is:

`docs/agent/V77_BOUNDED_SYNTHETIC_MUTATION_REHEARSAL_CONTRACT_20261007.md`

Contract head:

`71a3d6d84a36e1812ffd776153d48948bd8b945c`

The durable post-execution audit is:

`docs/agent/V77_BOUNDED_SYNTHETIC_MUTATION_REHEARSAL_AUDIT_20261008.md`

Audit-record commit:

`8495c9f0a753dbb25c90bc27e65f28c4ee2e471e`

Final implementation/test head:

`8dabe9ef9ed87b4beaf00acefda1a3073ed751de`

Successful workflow:

- `v77-qualified-zero-update-join` run `37712331165` — SUCCESS
- job `113100879103`
- focused suite: **51 passed in 9.87s**
- independent successful rehearsal custody rerun: **1 passed in 3.41s**
- `shared-qualification-interface-v1` run `37712331253` — SUCCESS

Final verdict:

`PASS__ONE_SYNTHETIC_GUARDED_UPDATE_PHYSICALLY_BOUND__NON_PRODUCTION`

Observed state transition:

- optimizer step `0 -> 1`
- teacher presentations `0 -> 2`
- online/student parameters changed
- predictor parameters changed
- teacher parameters changed only through the permitted post-completion EMA route
- optimizer state changed
- typed continuation persisted
- checkpoint restored into fresh modules and exact restored state was verified
- `execution_authorized=false`
- `training_authorized=false`
- `production_promotable=false`

Test-only EMA half-life is **1000 successful base-cell presentations**. This is not a production EMA choice.

---

# 3. Runtime audit performed in this chat: RED → GREEN

The earlier implementation at `c59db70046c5dcc7c6c8be6e30bebb745604cad5` was not accepted merely because its first tests looked green. The audit found material contract gaps: no true restored-state proof in fresh modules, incomplete failure custody, replayable run identity under a new output path, and incomplete bounded adversary coverage.

RED tests at `f0de464fcf921c14a96ef75df806075cc5b69da2` produced expected CI `37711581663`: **45 passed / 5 failed**.

Minimal repair `6f9f51704431825c4d95649944c7613a77c4dcf6` added stable run identity, durable failure receipts, cleanup of partial continuation, true checkpoint restoration into fresh modules, exact state digest comparison, and restored-module EMA authority. CI `37712004919` then passed 50 tests.

Final bounded physical-proof adversary at `8dabe9ef9ed87b4beaf00acefda1a3073ed751de` yielded **51 passed**. No model architecture or update mathematics was changed by the audit repair.

---

# 4. PR #232 physical payload/provenance repair

PR #232 head: `d3430ce6c0e878272e92b61e01822334e088d8c8`.

`PhysicalRowValueBindingV2` binds exact batch coverage, physical row, observation/donor identity, feature digest, actual executed student-expression values and aggregate physical-binding digest. CI `37693805825`: **29 passed**.

This proves fail-closed enforcement of a supplied proof. It does **not** independently prove protected production bytes are authentic.

---

# 5. PR #233 2K operator-smoke regression

Historical regression: stress-twin 2K preserved 42/42 operators; calibration-closure 2K silently dropped six. The repaired/current sampler was missing a CI execution guard.

PR #233 head `c919d957de79a3866fdaeab3ae2ae5a0891d4859`; CI run `37695987219`, job `113047706088`: **128 passed**, including real 2K smoke proving 42/42 with minimum >=1.

---

# 6. Corrected S174 scientific state

The critical correction is that the old HVS/SEA-AD feature-axis defect is **not an unresolved blocker**.

Prospective rebuild freeze:

`cf4d4708af68d32c8c1ec73b1a4b09294b2df6ef`

primary receipt:

`results/v77/S174_REBUILD_FREEZE_V1.json`

Corrected replay commit:

`46d8eaa8fa23cd60762a8a90c55b84e8d86364b2`

CI `37693603160`: **146 passed, zero skipped**.

The live S174 branch has advanced beyond the older snapshot embedded in PR #237. At the later locator audit it was:

`claude/s174-train-cache-rebuild-20261007@f88338713b173edb3acbc90662e607ce45b5878b`

Therefore use the live branch plus `TARGET_DISCOVERY_PRIMARY_ARTIFACT_LOCATOR_20261008.md` for defect→repair→verification chains; do not freeze the snapshot head as the current S174 truth.

Corrected real references remain descriptive pending S159; pooled p05–p95 envelopes are not qualification thresholds.

No synthetic mechanism is currently qualified.

---

# 7. Target-discovery archaeology: updated primary custody

The target-discovery lane is where the largest handoff risk remains. Historical target work had reportedly pivoted into relational-objective qualification after TD56/TD57B, with later TD59/TD60 work, but stage shorthand is not enough.

Use first:

`docs/agent/TARGET_DISCOVERY_PRIMARY_ARTIFACT_LOCATOR_20261008.md`

and:

`docs/agent/TARGET_DISCOVERY_CUSTODY_UPDATE_20261008.md`

### Sept. 7 package and TD34 producer

The historical ZIP is now recovered:

`JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.zip`

- bytes: `1664383`
- SHA-256: `d0b883ff798e94933b5e8aade3845551fad0b23d51451b01a59230476a7c59e4`
- historical expected SHA-256: same
- verdict: `EXACT_MATCH`

Embedded handoff SHA-256:

`5f49bf4072b44c8f1a269be86d299fb0157a6cf2a923040d2dbe348126af09b1`

Historical expected embedded handoff SHA-256: same.

Recovered authentic TD34 producer:

`scripts/td_iteration34_state_geometry_globalrow.py`

SHA-256:

`1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`

This exactly matches the historical digest preserved by the TD34/S149 audit. Durable takeover copy:

`custody/target_discovery_20260907_recovered/td_iteration34_state_geometry_globalrow.py`

The recovered producer establishes that TD34's four panels were constructed from the all-state common-support address universe, deterministically ordered by `SHA256("TD25|<address>")`, then split into four consecutive 512-address blocks. The old claim that original producer bytes were unavailable is superseded.

The remaining TD34 question is narrower: the upstream support NPZ `FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz` is not present in the recovered ZIP, and standalone exact panel membership manifests have not yet been located. Current classification:

`PRIMARY_PRODUCER_RECOVERED_AND_HASH_VERIFIED__SELECTION_RULE_RECOVERED__UPSTREAM_SUPPORT_ARRAY_BINDING_PENDING`

Durable package checksum inventory:

`custody/target_discovery_20260907_recovered/RECOVERED_PACKAGE_SHA256_MANIFEST.csv`

### Other established historical starting points

- TD34/S149 genealogy audit: `audit/td34-genealogy-s149-20261006@efa5c21db479f2feb78892356af3eef42c2886d2`
- historical TD34 closure: `ff85f5bb18dc7d438113c3a5662856a360d2cd8f`
- Nott/V64 successor: `chatgpt/v64-e2-single-source-successor-20260929@23255baaf81381d5c22c655a605642db27f2a173`
- Nott substrate-fit contract: `chatgpt/v64-nott-substrate-fit-contract-20260929@a6ecae6c31ba2083de72566fd336b187f7d59bfc`
- SCENIC+ recovery: `agent-4/scenicplus-recovery-expansion-20260926@5e3d1197749c6d2ac0b4015edea5c042b681af91`
- SCENIC+/cisTarget external-network: `claude/v69-scenicplus-external-network-20261001@d5b76230c1d2837dfbf643e205c5b2780831d8f9`
- NIH-CARD design: `claude/v64-nihcard-e2-design-20260929@6d08386f9f996c8db6224a959ca93745669b27ee`
- NIH-CARD realism lane: `claude/v64-nihcard-realism-design-20260929`

Do not carry an old RED finding forward until checking for a repair successor. Conversely, do not call it fixed unless exact repair and verification artifacts are found.

---

# 8. Local binary custody

The current environment contains the previously recorded hash-bound `/mnt/data` runtime/scientific assets **plus** the now-recovered Sept. 7 target-discovery ZIP.

Recovered target-discovery ZIP:

- `/mnt/data/JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.zip`
- bytes `1664383`
- SHA-256 `d0b883ff798e94933b5e8aade3845551fad0b23d51451b01a59230476a7c59e4`

The two 41K expression parts concatenate to complete archive SHA-256:

`63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

The binary Sept. 7 ZIP itself is not committed because the connected GitHub write interface is text-only; its exact identity and the authority-critical recovered text files are durably recorded under `custody/target_discovery_20260907_recovered/`.

---

# 9. Ordered continuation plan

1. Cold-start verify current PR/branch heads rather than trusting recorded “latest” SHAs.
2. Use `TARGET_DISCOVERY_PRIMARY_ARTIFACT_LOCATOR_20261008.md` and `TARGET_DISCOVERY_CUSTODY_UPDATE_20261008.md` to reconstruct TD34→TD60 as exact `defect/finding → repair/recovery → verification → supersession` chains.
3. For TD34, stop searching for the producer. Recover/hash-bind `FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz` or an authenticated equivalent common-support vector, reconstruct the four exact 512-address memberships, hash them, and compare them with downstream TD41 panel/pair artifacts.
4. Recheck G2 / `PIPELINE_ARTEFACT_m` successor history before carrying the Oct. 6 RED state forward.
5. Reconstruct Nott/liftover/V64 provenance from the historical V64 successor/contract branches, not from PR #237 alone.
6. Reconstruct SCENIC+/cisTarget producer/input/region-universe/exposure chains from the two SCENIC+ historical branches.
7. Reconstruct NIH-CARD design/audit versus actual Stage 3/4 execution outputs; do not confuse a design receipt with an execution result.
8. Re-adjudicate TD41→TD60 against current substrate/provenance status only after those upstream chains are exact.
9. Separately, the S174 synthetic agent owns prospective synthetic-biological redesign; do not merge that work into target-discovery archaeology.
10. No additional runtime mutation is the default next step.

---

# 10. Hard boundaries

Nothing in this handoff authorizes:

- real-data training;
- protected TEST execution;
- Morabito as pristine/unseen validation;
- 500K;
- Stage 4;
- production EMA selection;
- target freeze;
- representation freeze;
- threshold selection from corrected S174 outcomes;
- multimodal training.

If an answer rests on “a prior agent said so” rather than an exact producer, receipt, manifest, file, commit or authenticated local artifact, the takeover audit is not complete.