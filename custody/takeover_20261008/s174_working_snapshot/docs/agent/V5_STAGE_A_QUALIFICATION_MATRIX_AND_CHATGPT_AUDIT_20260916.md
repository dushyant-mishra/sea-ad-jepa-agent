# V5 Stage-A qualification matrix + independent audit of the spillover-firewall work — 2026-09-16

Auditor lane: Claude, adversarial/independent.
Audited work: ChatGPT's `audit/v5-stage-a-spillover-firewall-20260916`.
No training. No `D_shared`. No protected outcomes. FULL104 read-only.

---

## 1. Live repository state (independently resolved, not quoted)

| ref | expected | resolved | verdict |
|---|---|---|---|
| `impl/v5-current-target-authority-successors-20260915` | `812352a70ce1322f1a7d35a3fa9feeda4e4148c3` | same | MATCH |
| ↳ tree | `497fd3021c82aae05f0b36c8f4567674ebcd9f40` | same | MATCH |
| `audit/v5-stage-a-spillover-firewall-20260916` | `d0909dec25224909e940019262257273c3ef3b8c` | same | MATCH |
| PR #17 | open | OPEN, **draft**, MERGEABLE, head `d0909dec`, base `impl/…20260915` | MATCH |

CI: two `spillover-firewall` check runs SUCCESS at `d0909dec`; two earlier runs FAILURE at the
pre-fix commits. The failures are load-bearing evidence that the defect was real.

Sept-16 authority (`JEPA_NEW_CHAT_HANDOFF_STATE_20260916_V5_CURRENT.json`) lives on
`handoff/jepa-v5-new-chat-20260916` (`42cd1dec`) and is **not present on the audit branch**.

---

## 2. Diff audit — every changed path, `812352a7 → d0909dec`

| path | classification | verdict |
|---|---|---|
| `src/sea_ad_jepa/v5/__init__.py` | necessary | the fix itself |
| `tests/test_v5_current_stage_a_spillover_firewall_v1.py` | test-only | added |
| `.github/workflows/v5-stage-a-spillover-firewall.yml` | CI | added |

3 files, +214/−13. **No unrelated scientific or runtime change.** Every authority module source
is byte-identical to base. No module hashes `__init__.py` or walks the package directory, so the
change provably cannot perturb authority hashing, receipts, or serialization.

---

## 3. Defect reproduction at base

At `812352a7`, `import sea_ad_jepa.v5.current_authority_roots_v1` **raises
`ModuleNotFoundError: No module named 'torch'`**, via the eager
`from .data_first_geometry import …` in the package `__init__`.

The spillover was therefore not cosmetic: it made the entire current V5 authority path
hard-dependent on torch through a quarantined prospective module. At `d0909dec` the same import
succeeds and loads zero quarantined modules.

---

## 4. Independent spillover verification (stronger than the committed test)

| probe | committed test | this audit | result |
|---|---|---|---|
| modules imported in a clean interpreter | 1 | **all 17** Stage-A modules | all clean |
| quarantined modules inspected | 2 | **all 13** | none loaded |
| import depth | 1 file | **full transitive closure** | no reachability |
| import ordering | fixed | 12 permutations | no leak |
| bare `import sea_ad_jepa.v5` | not asserted | asserted | **0** submodules loaded |

Semantic scan over the Stage-A authority modules for `0.996`, `TD57/59/60`, six-block geometry,
`128 x 8`, `proposal_polic*`, `data_first_geometry`, ontology, coordinate, neighborhood:
**0 hits each**.

`from sea_ad_jepa.v5 import *` still loads `data_first_geometry` — that is the deliberately
preserved compatibility surface, not a regression, but it means the firewall is bypassable by
wildcard import. Noted, not corrected.

---

## 5. Defect found in ChatGPT's own test

`_local_imports()` recognised only **one of four** import forms that can reach a quarantined
module:

| form | detected by v1 |
|---|---|
| `from .data_first_geometry import X` | yes |
| `from . import data_first_geometry` | **no** |
| `from sea_ad_jepa.v5 import proposal_policy_v1` | **no** |
| `import_module(".data_first_geometry", __package__)` | **no** |

The third matters most: the new `__getattr__` makes that form *resolve successfully*, so
spillover could be reintroduced in a shape the firewall silently ignores.

**Corrected** (TDD): 3 tests written red against `d0909dec`, `_local_imports` extended to all
four forms plus `import sea_ad_jepa.v5.X`, tests green. Re-running the strengthened static check
over **every** non-quarantined v5 module finds **no** real contamination — so this was a
test-strength defect, not a hidden live one.

---

## 6. Claims audit

| ChatGPT claim | evidence | finding | verdict |
|---|---|---|---|
| spillover defect existed | base import dies on torch via `data_first_geometry`; 2 CI failures pre-fix | confirmed, and worse than described | **AGREES** |
| caused by eager package imports | `__init__` eagerly imported both modules | confirmed | **AGREES** |
| fix isolates current authority imports | 17/17 modules, 13/13 quarantined, transitive + order-permuted: clean | confirmed by stronger probes | **AGREES** |
| legacy helpers no longer auto-loaded | bare package import loads 0 submodules | confirmed | **AGREES** |
| current provider remains unselected | `current_provider_choice_status: OPEN`; no provider in tree; `address_registry_authority_sha256` populated nowhere | confirmed | **AGREES** |
| historical provider semantics not inherited | semantic scan 0 hits; authority container carries no defaults | confirmed | **AGREES** |
| Stage-A remains open | Sept-16 state: blocker `TARGET_ADDRESS_STAGE_A_STRUCTURAL_QUALIFICATION` | confirmed | **AGREES** |
| training remains off | `training_authorized: false`, `training_state: OFF`; authority raises if `training_authorized` is not `False` | confirmed | **AGREES** |
| firewall test proves the invariant | only 1 of 4 import forms detected; 1 module; 2 of 13 quarantined; no transitivity | **test was materially weaker than its claim** | **PARTIAL** |

Claims A–E from the task all verify: Layer-2 is `ALREADY_AUDITED_SUPPORTING_ONLY` with
`production_geometry_authority: false`; Stage-A is the current blocker; the provider is OPEN;
authority containers select no defaults; training is off.

---

## 7. Stage-A 11-check matrix

Criteria quoted verbatim from `JEPA_NEW_CHAT_HANDOFF_STATE_20260916_V5_CURRENT.json →
current_blocker.required_checks`.

| # | criterion (verbatim) | current authority | required runtime evidence | provable now? | provider-dependent? | verdict | evidence |
|---|---|---|---|---|---|---|---|
| 1 | shared trainable target/address mechanism; no per-target memorization | `TargetAddressQueryAuthorityV1.parameter_sharing_policy_id` | instantiated provider with shared params | no | **yes** | **UNPROVEN** | no provider exists; field is a free string |
| 2 | context/evidence gradient path into shared target/address mechanism | `gradient_policy_id` | nonzero grad at provider params from context→target loss | no | **yes** | **UNPROVEN** | requires a provider and a loss path |
| 3 | correct teacher/EMA reachability | `ema_presentation_v1`, `ema_timescale_authority_v1` | provider params inside teacher/EMA set | no | **yes** | **UNPROVEN** | EMA authority present; no provider to enrol |
| 4 | checkpoint/restart and deterministic replay binding | `current_atomic_checkpoint_guard_v1`, `replay_policy_id` | reload reproduces identical address→query | no | **yes** | **UNPROVEN** | guard exists; nothing to serialize |
| 5 | eligibility independent of hidden target value | `support_estimability_authority_v1` | eligibility invariant under target permutation | **partial** | yes | **UNPROVEN** | registry is value-independent (`expression_values_accessed: false`), but eligibility path unbuilt |
| 6 | no post-hoc/value-derived QC eligibility | `masking_authority_v1`, `anti_cheat_authority_bundle_v1` | QC perturbation leaves query identity fixed | no | **yes** | **UNPROVEN** | no query to perturb |
| 7 | no unauthorized target-specific lookup/coordinate/ontology/graph leakage | `target_identity_shortcut_gate_authority_v1` | provider input restricted to lawful identity | **partial** | yes | **UNPROVEN** | classification done (2 of 15 columns lawful); not enforced by code |
| 8 | provider source/provenance bound | `address_registry_authority_sha256`, `query_artifact_sha256` | registry hash bound + mismatch fails closed | **no** | yes | **FAIL** | field populated **nowhere**; see REG-1/REG-2 |
| 9 | no unauthorized historical carryover | spillover firewall | no import/semantic inheritance | **yes** | no | **PASS** | §4, §5: 0 import hits, 0 semantic hits |
| 10 | no visibility/QC re-entry to primary molecular path | `primary_representation_authority_v1` | primary path excludes visibility/QC channels | **partial** | yes | **UNPROVEN** | V0/V1 address lists frozen; no runtime path to test |
| 11 | no historical experiment result promoted by naming similarity | `NAMES_DO_NOT_CREATE_CAUSAL_OR_BIOLOGICAL_AUTHORITY` | no TD57/59/60-named selection | **yes** | no | **PASS** | 0 hits for `TD5[79]`/`TD60` in Stage-A modules |

**2 PASS · 1 FAIL · 8 UNPROVEN.** Checks 10 and 11 are kept distinct, as required.

Check 8 is FAIL rather than UNPROVEN because the authority *requires* a field that no artifact
supplies — that is a determinable present-state failure, not an absence of evidence.

---

## 8. Registry provenance (Phase 1 result)

Fully recovered and lineage-proven — see
`V5_STAGE_A_REGISTRY_BINDING_FAIL_CLOSED_CONTRACT_20260916.json`. Headlines:

- registry `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`, 41,238 rows,
  contiguous deterministic index, unique IDs, sufficient to replay an address exactly
- FULL104 block manifest SHA `66f589e5…` **verified on disk**; 8,915 blocks; 4,553,407 cells;
  104 donors; 42 operators; HVS 198,718 / NPH52 236,476 / SEA_AD 4,118,213
- six real Level-4 blocks read: declared hashes 6/6 MATCH, observed address indices within
  `[0, 41236]` → the blocks index into exactly this address universe
- common core **17,186**, derived as addresses in `MEASURED_SCALAR` across all 42 operators
- registry is **not** value-derived: `expression_values_accessed: false`,
  `dataset_or_source_family_used_in_address_id: false`, `deterministic_ordering: true`

**Blocked anyway**, on five items (REG-1…REG-5). The decisive one: the same artifact is bound by
three current authorities under three *different* role names, one of which
(`registry_observation_state_binding_sha256`) is actively misleading because the observation-state
NPZ has a different hash (`852cb3ec…`). Binding a provider by field name could bind the wrong
artifact. **No provider implemented.**

---

## 9. Test accounting

| category | count | detail |
|---|---|---|
| PASSED | 27 | 22 v2 adversarial + 2 v1 + 3 v1-regression after fix |
| FAILED | 0 | — |
| ENVIRONMENT BLOCKED | 1 | `test_compatibility_helpers_are_lazy_not_eager` — needs torch; fails identically at unmodified `d0909dec`; passes in CI (py3.12 + torch) |
| SKIPPED | 0 | — |
| DESELECTED | 0 | — |
| NOT EXECUTED | — | broader V5 CPU suite not run locally (torch absent); heavy/data-dependent not run |

No green-suite claim is made.

---

## 10. Residual risk

1. Local environment has no torch, so only the import-isolation surface was executed here.
2. `from sea_ad_jepa.v5 import *` still loads quarantined modules by design.
3. The `__getattr__` compatibility path caches into `globals()`; harmless, but it means the
   package acquires attributes after first access.
4. Checks 1–7 and 10 cannot advance without a provider, which cannot be built until REG-1…REG-5
   are resolved by current authority.
5. The workflow triggers `push` only on the audit branch; it will not run on push elsewhere.

---

## 11. Final audit disposition

`CHATGPT_WORK_AUDIT_PASS_WITH_RESIDUALS`

The runtime fix is correct, minimally scoped, and verified far beyond its own tests. Its test was
materially weaker than its claim; that has been corrected additively on the same branch. This
disposition covers only the reviewed work. It does not authorize training and does not close
Stage-A.

`STAGE-A_REMAINS_OPEN`
