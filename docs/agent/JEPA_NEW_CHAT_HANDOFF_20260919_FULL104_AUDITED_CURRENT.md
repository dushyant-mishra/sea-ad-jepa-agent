# JEPA V5 FULL104 — audited new-chat handoff — 2026-09-19

Status: `FULL104_PRETERMINAL_PROVENANCE_REPAIR_ACTIVE__OLD_PASS1_INVALID__H3_G5_TERMINAL_LOCKED__TRAINING_OFF`

## 0. Read this first

This handoff supersedes the September 17/18 startup pointers for current work.

**Scientific implementation branch (do not move while physical execution is bound):**

`impl/v5-full104-provenance-spillover-repair-20260919`

**Exact audited scientific head:**

`a51cdbe8bbfac1c77980711cca13df8bc58caa1d`

**Docs/evidence handoff branch:**

`handoff/jepa-v5-full104-audited-20260919`

The handoff branch is documentation/evidence only and must not be used as the GPU scientific execution worktree. Runtime-envelope execution must remain bound to the clean scientific branch/head above.

Permanent boundaries:

`TRAINING_OFF`

`NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`

`NO_TERMINAL_MASKING_OUTCOME_ACCESS`

`IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`

Permanent scientific ordering:

`DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> TARGET SEMANTICS -> PRODUCTION GEOMETRY -> MODEL`

The foundation task is **cellular/query-local state inference from partial RNA conditioned on a canonical molecular address**. It is **not hidden-gene scalar reconstruction**.

---

## 1. Exact current FULL104 substrate

Current immutable FULL104 facts:

- cells: `4,553,407`
- donors: `104`
- operators: `42`
- canonical molecular addresses: `41,238`
- strict common-core addresses: `17,186`
- Level-4 blocks: `8,915`
- sources: `HVS`, `NPH52`, `SEA_AD`
- Level-4 block-manifest SHA-256: `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`
- canonical registry SHA-256: `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`
- observation-state SHA-256: `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`
- current support semantic authority canonical JSON SHA-256: `cab2cecdd5ff31c2fbcaff408e1b1b7548eb2f72c1d3213931f1ce39188b6e08`
- canonical address-registry authority semantic digest: `28b20a457c44ac864c375492c8875e865ed6fe6d2000338d5fd46d9557a25676`

Canonical GPU paths reported from the physical machine:

- Level-4 root: `D:\Jepa project\outputs\full104_v014_20260826\03_phase2_state_derivation_v1\expression_level4`
- canonical registry: `D:\Jepa project\exports\foundation_calibration_bundle_20260824\contracts\address_namespace.csv`
- the Stage81A2R-named registry is a byte-identical upstream source copy, not the preferred runtime path.

### Normalization

Every real expression value is normalized exactly once as:

\[
\boxed{x' = \log(1 + x \cdot 10000/L_s)}
\]

where `x` is the raw count and `L_s` is the source-library quantity bound to the physical cell/source metadata.

The FULL104 physical shakedown applies this exact sparse transform to every stored nonzero; no monolithic 4.55M x 17,186 dense matrix is required or allowed.

---

## 2. Scientific identity and support semantics

### Cell identity

The authoritative global cell key is:

`selection_row`

Never block iteration position, file order, or append order.

For any per-cell derived artifact:

```text
cell_quantity[selection_row] = quantity_for_that_exact_physical_cell
```

A complete FULL104 pass must prove:

- every `selection_row` is in `[0, 4_553_407)`;
- no duplicate `selection_row`;
- every global row appears exactly once.

### Donor identity

Donor identity must be derived from physical donor IDs by a deterministic storage-independent rule. The historical September-17 census code used `sorted(donor IDs)`, which is deterministic, but the replacement producer must prove this again from physical metadata before reusing donor codes/folds.

### Observation state

The operator x address observation state is ternary:

- `0 = STRUCTURALLY_UNMEASURED`
- `1 = MEASURED_SCALAR`
- `2 = MEASURED_COLLISION_UNRESOLVED`

Strict common core:

\[
C = \{j: S_{o,j}=1\;\forall o\in\{1,\dots,42\}\}
\]

with `|C| = 17,186`.

Permanent interpretation:

- measured zero = a measured observation in which transcript was not detected;
- structurally unmeasured != zero;
- collision unresolved != scalar zero;
- common core = comparability support, not biological truth;
- native support = evidence, not automatically private biology.

---

## 3. September-17 pass1 defect — current stop state

Claude's physical requalification of the September-17 `pass1.npz` failed at the current independent verifier:

`ValueError: pass1 cell_donor does not rederive from physical metadata`

Root cause is confirmed in the committed historical producer:

`analysis/v5_full104_census_20260917/full104_readonly_census_pass1.py`

It stored per-cell vectors by sequential block traversal:

```text
cell_donor[pos:pos+n] = ...
cell_nnz_core[pos:pos+n] = ...
pos += n
```

instead of indexing by `selection_row`.

Claude's diagnostic sample:

- indexed by physical `selection_row`: `0/12` matched;
- indexed by sequential block position: `12/12` matched;
- the first block begins with selection rows such as `140, 219, 248, 272, 281, 345`, proving physical storage order is not global row identity.

### Classification

`SEPT17_PASS1 = INVALID_FOR_CURRENT_ROLE__ROW_IDENTITY_KEYED_TO_BLOCK_ITERATION_ORDER`

Do **not** reorder/permute the old NPZ and call it repaired. Build a new pass1 from authenticated physical bytes.

Historical order-invariant aggregates may be used only as cross-checks until independently reproduced.

### Replacement pass1 requirements

Recompute physically:

- `cell_donor`
- `cell_nnz_core`
- `donor_addr_nnz`
- `donor_src`
- `duniq`
- `core`

The new builder must be committed/reproducible and independently verified. Tests must scramble block order and row order within blocks and prove the semantic output is unchanged when keyed by `selection_row`. A test reproducing the old sequential-position bug must fail verification.

---

## 4. Separate historical census bug found in audit

The old September-17 `full104_readonly_census_pass2.py` treated `core_nonzero < B` as inability to supply `B` measured masking units. That is scientifically wrong because **measured zeros remain measured addresses and are maskable**.

This defect is **historical and repaired in the current live semantics**.

The current evidence-budget template explicitly uses:

`MASK_FRACTION_OF_STRICT_MEASURED_NON_TARGET_ADDRESSES_V1`

and:

`VALUE_INDEPENDENT_ELIGIBILITY__MEASURED_ZERO_IS_MEASURED_EVIDENCE_V1`

Do not revive the old nonzero-based feasibility interpretation.

---

## 5. Base scientific estimand

The recovered/frozen base-training scientific estimand is:

`DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1`

For donor `d` with `n_d` eligible cells and `D=104` donors:

\[
\boxed{p_i = \frac{1}{D\,n_d}}
\]

The objective is mean-over-donors, mean-over-eligible-cells-within-donor.

Proposal sampling `q`, physical packing and scientific mass `p` are separate. If proposal mass differs, exact `p/q` correction is required.

Source is a domain/robustness stratum and does **not** automatically set base training mass. Operator does not set base scientific mass.

### Kish ESS correction

The historical census computed the descriptive weight-imbalance statistic:

\[
N_{Kish}=\frac{(\sum_d n_d)^2}{\sum_d n_d^2}
\]

which is about 42 for raw donor cell counts.

**This is not the number of independent biological donors.** Current inference has `104` independent donor units. Kish ESS here describes imbalance in cell-count weights only; it must not replace donor N in donor-level power or confirmation statements.

Any older note saying “104 donors statistically behave like 42 donors” is superseded.

---

## 6. Primary molecular representation

Frozen channel-role decision:

`PRIMARY_MOLECULAR_EVIDENCE = VALUE_ONLY_256`

`VISIBILITY_CHANNELS = OBSERVATION_QC_CONTROL_ONLY__NOT_PRIMARY_MOLECULAR_INPUT`

Authenticated V0/V1 parent roots:

- V0 FULL parent: `3b3f102c6767727ca4ab56832f8e70baf203676d6b65973c42903b22b6d56ada`
- V1 FULL parent: `c41df46d842d643f04566b8523a8aa711fa54bec1c836e0b394c0146017f231c`
- expected shape for each: `[4_553_407, 512]`, float32
- molecular value channels: `[0:256)`
- visibility/QC channels: `[256:512)`

Current routing implementation:

`src/sea_ad_jepa/v5/primary_representation_routing_v1.py`

It authenticates physical parent bytes when available, but deliberately records that the production consumer is not yet bound.

### F13 status

`F13_OPEN__PRODUCTION_MODEL_CONSUMER_NOT_BOUND`

Claude's inventory found the physical V0/V1 parents absent on that GPU machine. Do not rebuild/substitute them. Locate by exact SHA on available storage later.

### Important unresolved leakage question

The query scalar is supposed to be withheld before contextual mixing. However, the lawful global V0/V1 context is precomputed. Before F13/F15 closure, explicitly test whether changing only the queried address scalar can change a supposedly query-scalar-withheld global-context route. A semantic label is not proof of query exclusion.

Required metamorphic idea:

```text
hold all non-query RNA fixed
change only x_q
recompute student-visible/global-context path
prove the route that claims to withhold q has the required invariance
```

If V0/V1 legitimately carries indirect information about q, that must be scientifically stated and the identity/global-no-RNA controls must demonstrate it cannot solve the task by itself.

---

## 7. Target semantics

Intended target:

`QUERY_LOCAL_STATE_CONDITIONED_ON_CANONICAL_ADDRESS_V1`

Hidden-gene scalar reconstruction is explicitly forbidden as the JEPA objective.

The target-construction/teacher semantics require:

- canonical query identity may be supplied;
- queried scalar withheld before the relevant context-mixing boundary;
- lawful non-query RNA may be visible;
- lawful global context may be used;
- teacher is stop-gradient;
- target is query-local state, not expression scalar.

The enum `BIOLOGICAL_CELLULAR_LATENT_STATE_V1` is **design intent**, not empirical proof that the state is biological. Names do not create biological authority.

### Remaining-RNA necessity test

Full remaining-RNA state evidence must beat both:

1. query identity only;
2. query identity + lawful global context with remaining RNA ablated.

For cosine-similarity score `s`, per-unit advantages are conceptually:

\[
\Delta_{id}=s_{full}-s_{identity},\qquad
\Delta_{global}=s_{full}-s_{global,noRNA}
\]

and both need prospectively frozen median/win-fraction rules plus adequate precision.

No healthy current-V5 teacher execution has yet closed this scientifically.

---

## 8. Masking: current safe design and hard locks

Historical masked-gene correlation/RIDGE work is **supporting discovery evidence only**. Historical parameters may motivate a prospective confirmation candidate when explicitly rebound to current FULL104 roots, but cannot provide current targets, folds, burdens, seeds, row caps, PASS states or selected policies.

Current conditional confirmation attacker remains a 32-feature class. This does **not** close the capacity-matching problem.

### Current decision concept

Let `m` be a prospectively justified residual-shortcut equivalence margin.

A terminal negative control should have its 95% interval inside:

\[
[-m,m]
\]

The shortcut excess upper bound should satisfy, globally and per fixed source:

\[
U_{shortcut}\le m
\]

A targeted policy should show improvement over uniform with lower confidence bound:

\[
L_{\Delta}>0
\]

and no negative per-source lower-bound improvement.

Worst-target degradation is currently bounded relative to `-m`, and the nonlinear challenge must also remain inside the shortcut-equivalence bar.

These are **qualification mechanics**, not proof that biological state signal remains usable.

### Hard locks

Do not run target-panel sizing:

`STOP_H3_EQUIVALENCE_POWER_OPEN`

Do not enter a convenient equivalence margin:

`STOP_G5_NULL_EQUIVALENCE_MARGIN_BASIS_OPEN`

Do not build terminal run contract:

`STOP_H3_G5_TERMINAL_RUN_CONTRACT_UNAUTHORIZED`

Do not execute a terminal rung:

`STOP_H3_G5_TERMINAL_MASKING_UNAUTHORIZED`

No terminal 5%, no higher rungs, no policy selection.

### Open masking science

- **G5** — scientifically justify the largest residual shortcut advantage considered negligible. Historical `1/1000` is not authority.
- **H3** — after G5, prospectively size the target panel for equivalence precision/power, not merely planted-shortcut detectability.
- **H4** — preregister interpretations of all-rung failure so failure distinguishes ineffective masking, overly strict margin, irreducible depth/detection structure, or inadequate estimator precision.
- **G2** — current targeting-complexity materiality is one total targeted event on the target x fold grid. This changes relative meaning with grid size and needs scientific justification/scale normalization.
- **G3** — 32-feature attacker is much weaker than the eventual JEPA context; add stronger/capacity-matched/objective-aligned attack layers before training.
- **G4** — add prospective state-signal preservation. A shortcut can be suppressed by destroying useful molecular evidence; masking PASS must not equal biology-preserved.

The burden ladder `5/10/15/20/30/50%` is a prospectively fixed stress/search grid, not a biological statement that any rung preserves state.

---

## 9. Masking population versus base-training estimand

Precision V4 conditions on the three observed sources and aggregates them equally while reporting source-specific guardrails.

Base training is donor-uniform/cell-uniform-within-donor.

These are different estimands and must remain explicitly distinct:

- **training estimand:** what population receives scientific objective mass;
- **masking source-equal aggregation:** a robustness/safety gate intended to prevent a large source from hiding failure in another source.

Do not silently convert the source-equal masking gate into the base training estimand.

---

## 10. Target estimability

Historical/current eligibility construction has used thresholds including:

- donor has at least 30 cells with a nonzero value at an address;
- per outer fold: at least 20 supporting training donors and 5 supporting validation donors.

Historical result was `17,053 / 17,186` addresses estimable in all four folds, with per-fold counts around `17,070 / 17,071 / 17,072 / 17,060`.

These numbers must be regenerated from the corrected physical pass1 before current authority.

The 30/20/5 thresholds are statistical estimability choices, not definitions of biological importance. Their scientific/statistical justification and nearby-threshold sensitivity should be documented before final target-panel authority.

---

## 11. F14/F15 and model/training status

### F14 — production dimension/rank/subspace

`OPEN`

Do not inspect protected `D_shared` outcomes while upstream design remains open.

Historical dimension relation remains:

\[
\boxed{D_{total}=D_{shared}+D_{private}}
\]

with `D_obs` separate.

Historical ranks/widths are not current production geometry.

### F15 — production teacher/student/training mechanics

`OPEN`

Claude's inventory found no executable current V5 production training path. Historical V4/inactive/prototype mechanics are not production authority.

EMA mechanics concept retained:

\[
\boxed{m_u = \exp(\log(0.5)\,p_u/H)}
\]

where `p_u` is the authorized number of scientific presentations in an update and `H` is a prospectively chosen half-life in presentation units. Historical `.996` is not current authority.

EMA must advance only after a proved optimizer step; skipped step => no EMA update.

---

## 12. New audit findings on downstream authority

### A1 — current final authority closure is stale relative to the live masking chain — HIGH OPEN

`src/sea_ad_jepa/v5/current_authority_closure_v2.py` still imports older masking types such as Design V1, Parameters V1, RunContract V1, Execution V2, Precision V1, TargetPanel V1 and RNG V1.

The actual hardened lane now contains newer V2/V3/V4 authorities and physical pass1 provenance.

Therefore final training closure does **not yet prove it consumed the current FULL104 masking chain**.

Do not issue training authority until this closure is rebuilt against the actual final schemas.

### A2 — several “execution authorities” can still trust declared PASS states — HIGH OPEN

Examples include the current schemas for:

- critical-test execution;
- remaining-RNA execution;
- measurement robustness;
- geometry memorization;
- runtime source/environment.

Several validate caller-supplied hashes/status strings without independently reopening/recomputing the bytes that justify `EXECUTED_PASS`.

Permanent repair rule:

`NO_CALLER_SUPPLIED_DERIVABLE_RECEIPT_FIELDS_V1`

Every final PASS/hash/status must be recomputed from bound evidence or cross-bound to a separately validated physical artifact/log.

The newer masking ExecutionAuthority V4 is closer to the desired pattern because it has explicit raw-artifact/decision-receipt binding methods; extend that standard globally.

### A3 — startup/governance docs were stale — repaired by this handoff

At scientific head `a51cdbe8...`, `START_HERE.md` and the latest pointer still referenced September-17 work, the active execution plan referenced a September-18 branch, and the command file carried an older source anchor.

This handoff branch replaces the startup pointers. Do not treat old startup docs as current.

---

## 13. Current exact-head verification

Exact scientific head:

`a51cdbe8bbfac1c77980711cca13df8bc58caa1d`

GitHub Actions at that exact head:

- FULL104 masking runner — run `35451597882`, job `105919598903`: `342 passed`, then `342 passed` again under skip-fail; zero skips.
- Stage-A spillover firewall — run `35451597886`, job `105919598957`: `159 passed`, then `159 passed`; zero skips.
- remaining-RNA and target-semantics successor — run `35451597885`, job `105919598853`: `314 passed`, then `314 passed`; zero skips.
- runtime closure — run `35451597891`, job `105919598836`: `40 passed`, then `40 passed`; zero skips.

These prove current mechanical/regression health, not biological validity.

Claude's canonical-GPU-environment preflight additionally reported:

- environment: `sea-ad-jepa`
- Python 3.11
- PyTorch 2.7.0+cu128
- CUDA 12.8
- RTX 3080
- numpy 1.26.4
- scipy 1.15.3
- sklearn 1.5.2
- pandas 2.2.3
- only pytest and its required dependencies were added;
- 76 passed, 0 skipped across the ten physical-lane safety files.

The exact full environment artifact hashes were reported by prefix as BEFORE `01bc18ab…` and CANONICAL `dba5f169…`; preserve the complete files when Claude returns the evidence package rather than inventing missing suffixes.

---

## 14. Claude physical lane — current handoff state

Last user-supplied status:

1. canonical environment frozen successfully;
2. clean execution worktree at exact scientific head `a51cdbe8...`;
3. old September-17 pass1 failed physical identity requalification and is now invalid for current role;
4. no pass1 binding/census/split/eligibility/census authority was produced from the bad artifact;
5. calibration cache correctly remained gated;
6. runtime envelope correctly rejected output placed inside the scientific worktree and later rejected execution without a sentinel — record these as expected fail-closed guard evidence;
7. Claude relocated outputs to a sibling path and prepared a proper runtime envelope;
8. the independent full physical shakedown was still running when this handoff was prepared;
9. no terminal outcome was opened and training remained off.

Do not claim the shakedown passed until the actual receipt/log arrives.

After shakedown, Claude was instructed to verify canonical donor ordering and build a **new physical pass1** rather than patch the old one.

---

## 15. Safe work allowed now

Without terminal/protected outcomes, safe work includes:

- physical Level-4/registry/observation-state authentication;
- full streaming I/O and exact normalization shakedown;
- canonical donor-order audit;
- corrected selection-row-keyed pass1 producer + permutation tests;
- physical pass1 independent binding;
- regenerated census/split/target eligibility;
- authenticated calibration-only cache;
- runtime/memory/throughput instrumentation;
- current V0/V1 parent byte location/authentication when exact files are found;
- static/unit/provenance repair of final authority schemas;
- prospective scientific design for G5/H3/H4/G2/G3/G4;
- query-scalar/global-context leakage metamorphic tests;
- documentation/governance repair.

### Not allowed

- target-panel sizing while H3 open;
- choosing/typing G5 margin from convenience or history;
- terminal RunContract;
- terminal 5%;
- higher terminal burdens;
- policy selection;
- D_shared/protected/pathology outcomes;
- current training;
- historical teacher checkpoint promoted as current healthy teacher;
- historical/smaller pass1/cache/target/fold/burden/seed imported by coincidence.

---

## 16. Historical findings — keep in perspective

Historical findings remain valuable only in their proper role:

- prior JEPA repeatedly learned shortcuts -> motivates anti-cheat testing;
- visibility strongly tracks depth/detection -> visibility stays QC-only in primary molecular path;
- random masking can leave correlated partners visible -> motivates dependency-aware masking candidates;
- prior T0/T1/C2/QID failures -> regression/authority guardrails;
- historical same-cell thinning and linear/ridge attacks -> model-class-limited supporting evidence;
- Stage81 corrected TRAIN cache -> historical mechanic scope only, never FULL104;
- historical T1 checkpoints -> adversarial/diagnostic fixtures only;
- discovery 50k expression -> algorithm discovery/supporting evidence only;
- historical D_shared/private scaffolding -> formula/design context only until current protected outcomes lawfully open.

Historical results may motivate a prospective test. They may not silently supply current FULL104 data roots, row identities, targets, folds, thresholds, geometry or PASS states.

---

## 17. Local files available in this chat environment

A machine-readable exact manifest is included at:

`docs/agent/handoff_artifacts/20260919/JEPA_LOCAL_ENVIRONMENT_ASSET_MANIFEST_20260919.json`

Key immutable/heavy assets available here and therefore recorded by size/SHA rather than copied into Git history:

- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` — 410,278,055 bytes — SHA `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
- discovery expression archive expected whole — 607,959,761 bytes — SHA `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- discovery part001 — 303,979,881 bytes — SHA `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`
- discovery part002 — 303,979,880 bytes — SHA `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`
- `checkpoints.zip` — 71,356,460 bytes — SHA `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`
- `t1_checkpoint_u0200.zip` — 233,729,581 bytes — SHA `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`
- historical `expression.zip` — 3,599,456 bytes — SHA `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`
- `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` — 1,531,109 bytes — SHA `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`; historical supporting result with prior provenance-mismatch warning; never current authority.

The exact local asset manifest is copied to the handoff branch. The downloadable handoff ZIP supplied with this chat additionally packages the small textual manifests/audit notes with explicit supporting-only classification.

Large binary files are **not** duplicated into ordinary Git history. Exact filename/size/SHA and semantic role are preserved instead.

---

## 18. Corrected external/Claude evidence notes

Claude inventory underlying report final corrected SHA as reported in its transcript:

`3aaa1509bf6c9987fd93677c9f53e3191d6def63ea8cb7e0e5132126bee7412d`

The file copied into this handoff is the conversation transcript, not byte-identical report content; transcript SHA is separately recorded in the local asset manifest.

The masking/scientific audit transcript copied into this handoff is supporting evidence and contains statements superseded by later repairs. In particular:

- its G1 ceiling-binding defect was later repaired by exact binding to PrecisionAuthority V4;
- prior-rung provenance was subsequently strengthened;
- F16/F17 mechanics are closed;
- G2/G3/G4/G5/H3/H4 remain scientifically relevant/open as described above;
- its “Kish ESS ≈42 means donor n≈42” interpretation is superseded by the corrected donor-sampling semantics: independent donor N is 104.

Never promote the raw transcript itself to current authority.

---

## 19. Priority sequence for the next chat

### Immediate

1. Re-fetch `impl/v5-full104-provenance-spillover-repair-20260919` and verify it still equals `a51cdbe8...`. If it moved, compare the delta before acting.
2. Read this handoff, machine state, current audit and local asset manifest.
3. Ingest Claude's physical shakedown/evidence package if it has returned. Verify hashes/logs independently.
4. If the shakedown passed, preserve receipt as `NEW_CURRENT_FULL104_EVIDENCE`; if not, diagnose without weakening envelope guards.
5. Finish/verify canonical donor ordering and the new selection-row-keyed pass1 builder.
6. Run unchanged independent physical verifier; only after PASS regenerate census/split/eligibility/authority.
7. Compare new aggregate census values to historical values; label each `REPRODUCED_EXACTLY` or `CHANGED_AFTER_IDENTITY_CORRECTION`.
8. Build authenticated calibration-only cache only after the physical pass1 chain closes.

### Then scientific design

9. G5 first: derive/freeze a scientifically meaningful residual-shortcut equivalence margin.
10. H3 second: design target-panel equivalence precision/power against that margin using outcome-blind controls/simulation.
11. H4: preregister all-rung failure interpretation/diagnostics.
12. G2: justify targeting-complexity materiality in a scale-stable way.
13. G4: define state-signal preservation before terminal masking.
14. G3: define stronger/capacity-matched/objective-aligned shortcut attacks.
15. Resolve query-scalar/global-context leakage contract.

### Production closure after those

16. F13 current representation consumer binding.
17. F14 protected dimension/rank/subspace qualification only when lawful to open.
18. F15 current teacher/student/runtime implementation.
19. Rebuild final authority closure to the actual final schemas.
20. Replace caller-declared execution PASS/hash fields with physical/result-log derivation.
21. Only then consider explicit final training authority.

---

## 20. Current project classification

Use:

`FULL104_PRETERMINAL_PROVENANCE_REPAIR_ACTIVE__OLD_PASS1_INVALID__H3_G5_TERMINAL_LOCKED__NO_TERMINAL_OUTCOMES_OPENED__TRAINING_OFF`

Do not claim:

- current pass1/census closure;
- current target panel selected;
- scientifically justified null-equivalence margin;
- terminal masking PASS;
- selected production masking policy;
- biological-state preservation demonstrated;
- F13/F14/F15 closed;
- D_shared opened;
- training authorized.