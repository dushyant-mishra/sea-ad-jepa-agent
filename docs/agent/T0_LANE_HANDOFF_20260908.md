# T0 lane handoff — 2026-09-08

Standalone context for a fresh session. Everything here is verifiable from the
branch and the digests below.

---

## 1. What the project is

A JEPA-based agentic framework for **gene-network discovery** across scRNA-seq,
immunohistochemistry and imaging. Founding intent 2026-05-27. The frozen model
sequence is five stages, `v4A` through `v4E`, where `v4A` is the
`required_parent_baseline` every later branch must beat.

Intent lives in the Codex history (`~/.codex/state_5.sqlite`, sessions under
`~/.codex/sessions/`), `docs/scientific_pitch.md`,
`configs/v4/stage81a0_v4_design_contract.yaml` and
`docs/v4/STAGE81A0_V4_FAILURE_REGISTRY_AND_DESIGN_CONTRACT.md`. Repository
contracts describe gates, not goals.

"Pathology-blind" is a **staging rule for v4A**, not the objective. AT8, 6e10,
GFAP, Iba1 and NeuN are the eventual validation targets.

---

## 2. Where the work is

| | |
|---|---|
| canonical repo | `D:\Jepa project` (`/mnt/d/Jepa project` in WSL, same files) |
| lane worktree | `D:\jepa_t0_mat_20260908` |
| lane branch | `t0/v20-pathology-blind-materialization-20260908` |
| sealed base | `21ec629667eeda5a7d37d3f1d822fbf93b213325` (`coordination/project-consolidation-20260907`) — must stay unchanged |
| environment | `conda run -n sea-ad-jepa-v3` (Python 3.11.15, numpy 2.4.6, pandas 2.2.3, pytest 9.1.1) |
| suites | `tests/test_work_checkpoint_v1.py`, `tests/v4/test_t0_at8_availability_authority_v1.py`, `tests/v4/test_t0_v20_feature_projection_authority_v1.py` — **98 cases** |

Run the three suites **explicitly**. `pytest tests/v4/` aborts at collection
because three unrelated files from commit `2d929e41` do file I/O at import time
and fail with `FileNotFoundError` in any worktree lacking their data. That is
pre-existing and outside this lane's authorization.

`git worktree add -b` sets the new branch's upstream to the branch it was
created from. Push with an explicit refspec
(`git push origin refs/heads/<b>:refs/heads/<b>`) and verify the sealed ref
before and after, or a bare `git push` can target the sealed base.

---

## 3. What T0 is

T0 is the project's first real biological claim. From the frozen V18 contract:

> Can a fixed, expression-only broad-IMMUNE molecular score learned on SEA-AD MTG
> discovery donors show a donor-disjoint positive association with quantitative
> MTG AT8 pathology, after predeclared nuisance, broad-IMMUNE composition, and
> measurement/technical sensitivities?

Plus a nested question about a donor-recurrent extreme-cell tail.

**T0 does not use the JEPA.** `t0_target_learner_v1.py` is a donor-pseudobulk
nuisance-partialled dual-ridge learner — no torch, no checkpoint, no teacher. T0
is therefore the only lane not blocked behind the healthy-trained-teacher gate.

- **V18** freezes the science: 18 discovery / 18 confirmation donors, α 0.025
  state-positive, 0.02 tail-positive, 0.005 negative, q=0.95 tail,
  `HC3_T_RESIDUAL_DF`, 9,999 permutations, 17-point ridge grid, tail n ∈ {17,18}.
- **V19/V20** change no science. They add execution-input binding: the canonical
  entrypoints refuse to conclude unless a prospectively built authority attests
  the exact input bytes with a chronology stamp.
- **V20** repaired two V19 defects: malformed input absorbed as `NOT_ESTIMABLE`,
  and a superseded V1 API map left active. Independently reviewed: `PASS`.

---

## 4. Accepted V20 package (immutable)

Recovered by SHA, not by path. Local copy:
`C:\Users\dushy\Downloads\JEPA_T0_V20_EXECUTION_AUTHORITY_REVIEW_PACKAGE_20260907.zip`

| artifact | SHA-256 |
|---|---|
| ZIP | `a069cad258d278bf8d97e20ba1317ccc62b93265e7f93208a2ae1a4848561947` |
| package root (154 members) | `896dce257b8ed7330cfe9ac9a561e6d87090903485236dbf37f389d6432cb9e7` |
| V20 contract | `b8e5a38f9a158d0436d38e6846a51692f9a949580c899768c7d7507ab8646f62` |
| implementation manifest | `1f55741e83bf1b504c052975649ec3a8978428b311251c9b0bd5271cf20c6b9d` |
| active-test manifest | `99b9aeacea525ff06d6ab6d64aaed2fd74167795c2da21c02ef912f867fb0d6b` |
| API map V3 | `4aa3a3d11d7f851b106b8a2f33e1b4b345eddbcdd1f2baaab9f30b0aff1bec2c` |
| superseded registry | `ef54a8d0cc2f2e9c160e459bd8e239c20c10a0e052a369cc2ec3688096de909c` |
| V20 constants | `d15a1773469f67140de199ddcaf784b3c811c92ae7ed3f8bc4d6ab9f90252833` |
| V18 scientific contract | `0851b47d2351ded1be35a772bb9d7c05ed57d4bbbe551d81c7845a87ace85050` |
| V18 frozen constants | `e255bf4ad878e3277dcdd573dbf17a10b7cd34eb78be64c78435ffa4f38971ec` |
| preserved failed V19 ZIP | `4ba8d3362ee05efe363e254f11a45db468a3e44d234ddd4dd58091640ba7a52e` |
| preserved V18/V4 ZIP | `f25806dd68c576832d51ef998712f56b4add4481388852e4b22636fbc1624fa9` |

Independent review terminal, meaning **only** this:
`T0_V18_SCIENTIFIC_SPECIFICATION_PRESERVED__V20_EXECUTION_BINDING_AND_INVALID_PRECEDENCE_ACCEPTED__REAL_T0_STILL_UNAUTHORIZED`

Verified: 154/154 members, root reproduced, 22/22 static audit, 11/11 STOP-A,
6/6 STOP-B, 18/18 execution-binding, **224/224 full suite**, 5/5 canonical chain.

---

## 5. External data — five of six V18 blockers are materialized

| requirement | resolution |
|---|---|
| AT8 endpoint | `data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv`, sha `ebbe9bc0c623c663331425794bd8fb1b4c4f3657455cf55d806cc383ea6d8e3a`, 21,982 bytes, 84 donors. V18 names exactly `percent AT8 positive area_Grey matter` |
| nuisance | age `int64`, sex Female/Male, complete for all 46 |
| canonical counts | `outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/` — 41,238 addresses, 4,553,407 cells, 104 donors, 42 operators, **raw integer counts plus per-cell `source_library`**, `log1p(raw*10000/library)` deferred |
| membership | 20,804 cells / 46 donors, all operator 31 — **100% present** in the store |
| matrix semantics | `results/v4/stage81a2_matrix_semantics_contract.csv` — `matrix_slot=layers/UMIs`, `raw_integer_counts`, `normalization_already_applied=False` |
| MTG h5ad | `data/external/v4/sea_ad/mtg/SEAAD_MTG_RNAseq_final-nuclei.2026-06-22.h5ad`, sha `e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79` |

### Traps that cost real time — do not repeat

1. **`X` is normalized.** Only `layers['UMIs']` holds integer counts.
2. **`source_feature_index`** in the provenance table is **not** an h5ad column
   index. Address `ENSG00000207751` → index 32126 → `CEACAM5` in the h5ad. Four
   of four spot checks landed on unrelated genes.
3. **Two contradictory matrix-semantics files.** `pre_stage81a2_matrix_semantics_registry.csv`
   says `integer_count_layer_available=False`; the `stage81a2_matrix_semantics_contract.csv`
   says True. Bind the **contract**, never the pre-stage registry.
4. **CRLF.** `core.autocrlf=true`. Declared authority digests are **Git blob**
   digests. `PHASE2_EXPRESSION_BLOCK_MANIFEST.csv` is `66f589e5…` as a blob and
   `e482d9da…` on disk. Hash tracked authorities with
   `git cat-file blob <pin>:<path>`.
5. **Stage81A2R authorities are absent at the sealed base** `21ec629…` and exist
   only at pin `95d2cafe5cde68773f81c4aa64afc5788ae1d73b`. A naive hash of a
   missing path digests empty bytes as `e3b0c442…`.
6. **`BLOCK_MANIFEST.partial.csv` needs no repair** — byte-identical to
   `PHASE2_EXPRESSION_BLOCK_MANIFEST.csv`; the filename is stale.

---

## 6. Lane state

### Lane A — AT8 availability-only authority

Owner-authorized to derive **only** whether the frozen AT8 field is present and
non-missing. Never parses, retains, emits or models a numeric value.

```
source            ebbe9bc0c623c663331425794bd8fb1b4c4f3657455cf55d806cc383ea6d8e3a
availability root e49c4e9365513d88d3afb687e452bc126dc3d39722384bc262557f84ee43523b
package root      5ed35e084f888c688bc77edcda542c0a2c7f56d3f24b7cf8689aa07733bb2fdc
derivation code   a78f58709418c1b341a0570d657a44ece706861fbebeb5ecedd2307053841b3e
membership set    f89838342622348f126217686084bf69901b1a50aca97ce94b176b779e294d64
donors            84/84 available (0 blank, 0 in the missingness vocabulary)
membership        46/46 accepted-V20 donors resolve and are available
location          outputs/t0_at8_availability_20260908  (untracked, no CRLF filter)
```

**Two-root design.** `availability_root` covers the derived predicate alone and
is invariant to every numeric value, proven metamorphically; it has reproduced
across **six** builds. `package_root` binds the source digest and derivation
code and is expected to move.

Value handling is stated precisely: `raw_at8_token_read_for_missingness=true`,
`numeric_at8_value_parsed/_retained/_emitted=false`. A measured **zero counts as
available**.

Review package: `C:\Users\dushy\Downloads\T0_AT8_AVAILABILITY_REVIEW_PACKAGE_V3_20260908.zip`
sha `01ce9b37e592ee694c0cb6edc2b1095908943997216bd70e8f792416a78a70a2`,
repository-relative layout, 26 cases pass from the extraction root, includes
`membership/ACCEPTED_V20_DONOR_SET_WITNESS.csv` and the accepted-V20 member
digest `d471499836118ddaf963ae9241f612d2e9a78bff4add62834347fc0ca06a3529`.

Status: `NOT_YET_INDEPENDENTLY_VERIFIED` — awaiting re-review of V3.

### Lane B1 — S2 feature projection authority

```
accepted split   current/authority/T0_MTG_FEATURE_ROLE_SPLIT_V2.csv
                 29116c16e9002329090a5054b6c4bdae1cbff28917cbee85f03b4633b0b29369
projection root  0a0739ec30c758a53070f76989cd4964d7d37224fd20890951b63aacf66e8002
authority root   81b570abb46d4406b746478c48c121ae3e9b524b8736b6548488e264d4bcb1cf
features         35,076   SCORING 28,061   COHERENCE_HOLDOUT 7,015
pin              95d2cafe5cde68773f81c4aa64afc5788ae1d73b
registry blob    7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd
support gzip     ee5d12c144536efdacb983f6b9aa2acb46d47d395b2aa9c556ad10b191f3cdaa
support plain    5b641c5a8f2386720c58c4512ec89879a43985a01995e2ada70e941b017dee03
```

`projection_root` binds ordered rows only. `feature_authority_root` additionally
binds schema, namespace, split member and digest, feature count, role counts,
matrix id, address-space size, registry and both support digests, the pin, the
ordering contract, `source_feature_index_used` and `real_execution_ready`.
Demonstrated on production data: a `matrix_id` mutation leaves `projection_root`
identical and moves `feature_authority_root`.

**An independent agreement with the contract:** V18 §3 declares SCORING =
28,061 and the projection observes exactly 28,061.

**An honest limit:** the accepted split is itself strictly increasing in
`molecular_address_index` (0 → 41,194), so split order and address order coincide
and the ordering guarantee is vacuous for this split. Retained because it is not
vacuous for a future split; exercised only by synthetic fixtures.

### Lane B2 — row/count authority (NEXT, not started)

Must consume `81b570ab…`, not only `0a0739ec…`. Three separate roots:

- `population_closure_root` — exhaustive operator-31 scan
- `logical_row_authority_root` — all 20,804 rows in frozen membership order
- `physical_read_plan_root` — may sort by block/row for I/O but must carry
  `logical_index` so physical ordering can never redefine the population

Reproduced expectations: **1,247 blocks, 638,150 metadata rows, 20,804/20,804
unique targets, zero missing, zero duplicates, 46 donors**, against a complete
manifest of 8,915 blocks over 42 operators
(`66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`, pinnable at
`21ec629…` under `docs/history/…/expression_level4/`).

`source_library` is an **integer sum of the full raw source row, computed before
projection**. Never recompute it from the 41,238-address row or the 35,076
projection; neither sum need equal it. Bind all six Phase2 metadata fields
(`selection_row, canonical_cell_id, donor_id, expression_row,
primary_row_weight, source_library`) and mark which V20 consumes versus
audit-only.

### Lane C — promotion-only successor (authorized, design only)

**V20 cannot be promoted by flipping a flag.** Its verifiers raise unless
`real_execution_ready is not False`, so they accept only `False`; its production
entrypoints raise unless it `is not True`, so they proceed only on `True`. The
two are mutually exclusive by construction, and `True` is assigned nowhere in the
codebase. The successor needs its own **schema + verifier + entrypoint triple**
wrapping accepted V20, binding V20 identity, the S2 roots, the donor-role
authority and a future owner pathology-authorization artifact, failing closed on
any absence. Synthetic fixtures only; no real activation.

---

## 7. The blocking scientific gate

`STOP_T0_DONOR_ROLE_AT8_AVAILABILITY_AUTHORITY_UNBOUND` — **active**.

Donor roles need a genuine `bool AT8_available` column. The availability
authority now provides it but is not yet independently accepted, and per the
owner authorization the STOP lifts only after that acceptance. Without roles
there is no discovery/confirmation split, so nothing downstream can run.

Recovered V18 framing, not invented: `split_hash = _digest(donor_id)` from
`t0_discovery_confirmation_split_v2`, order by `(split_hash, donor_id)`, first
`N_CONFIRM`=18 are CONFIRMATION, namespace `T0-DISCOVERY-CONFIRM-V2`,
completeness `= AT8_available & technical_complete & isfinite(age) & non-empty
sex`. With 46 eligible that gives 18 CONFIRMATION + 28 DISCOVERY, against a
floor of 18. 45 of 46 donors clear the 80-cell tail minimum.

`technical_complete` is **not** a second blocker: V18 §7 grounds it in `Q_DEPTH`
(donor mean `log1p(source_library)`) and `Q_DETECT` (donor mean nonzero fraction
over the 35,076 addresses), both derivable pathology-blind inside S2.

**Remaining after that:** owner pathology authorization (S6), then the promotion
successor, then V18's serial chain — DISCOVERY 28 → freeze target → freeze
tail/technical/family/preadjudication → CONFIRMATION 18 → three-valued decision.

---

## 8. Parallel lane, not mine: target discovery

Peer-led. State as of 2026-09-08:

- Cross-source **gene loadings** do not replicate; support mismatch does not
  explain it (TD16).
- Within-source gene-gene **dependency** does not replicate cross-source in OPC,
  though that stratum is underpowered and reproducibility tracks cell count
  (HVS 5,734→0.078–0.107; NPH52 8,825→0.066–0.069; SEA_AD 80,758→0.213–0.304).
- **Relational geometry between annotated cell states does replicate**
  (r ≈ 0.88–0.98, TD17/TD18) — but used labels, so it cannot qualify a target.
- **TD41**: within-cell pairwise address-ordering features give GLUT cross-source
  state geometry ≈ 0.80–0.92 residualized. Note pairwise signs are a function of
  ranks, so this is a **metric** change (Kendall-like) rather than new
  information.
- **TD43**: ~99% directional fidelity at half depth versus 87–91% matched
  wrong-cell — so most of the signal is a global gene-abundance prior, and any
  training target must be scored as **excess over the matched null**.
- Structural facts: 42 operators perfectly nested within source; only 17,346 of
  41,238 addresses measured by all three families, 17,186 scalar in all 42
  operators; SEA_AD is 90.4% of pooled cells; HVS↔SEA_AD share the three
  `broad_class` labels and 87 of 104 donors.

---

## 9. Process rules that are not negotiable

- **Audit your own work continuously**, not at the end. Reproduce a suspected
  defect before repairing it, so the repair is known to discriminate.
- **Treat your own passing tests as claims to attack.** A test that ratifies
  current behaviour instead of the intended contract certifies a hole forever.
  This happened here: a test asserted there should be *no* complaint when a later
  commit replaced a declared authority.
- **Verify edits by diff and by counting what should exist.** A truncating
  rewrite silently deleted seven regression cases; the suite count falling from
  30 to 24 was the only signal.
- Never fabricate a threshold. Measure, then state the measurement.
- `NOT_MEASURABLE` is not `PASS`. A test that can skip is not a test that ran.
- Fail closed. Never "make the pipeline work" by weakening a gate.
- Prose in a docstring or contract is not an implementation.
- **Keep proof-of-concept detail in the repository**, referenced by path and
  digest; use neutral engineering vocabulary. See
  `docs/agent/T0_LANE_SECURITY_SCOPE.md`.

---

## 10. Forbidden

`RUN_REAL_T0`, `OPEN_AT8_PATHOLOGY_VALUES`,
`SET_OR_BYPASS_REAL_EXECUTION_READY_TRUE`, `MODIFY_V18_OR_V20_SCIENCE`,
`CREATE_NULLABLE_DONOR_ROLE_SUBSTITUTE`,
`HASH_WORKING_TREE_CRLF_AS_SOURCE_AUTHORITY`,
`BIND_PRE_STAGE81A2_MATRIX_SEMANTICS_REGISTRY_AS_T0_AUTHORITY`,
`BUILD_T0_AGGREGATE_AUTHORITY_WITHOUT_LAWFUL_DONOR_ROLES`, plus the standing
closures on DEV, SEALED, reader-validation, reader-oracle, real F1 and fresh
production training.

Do not touch the sealed coordination base, the sealed-holdout registry branch or
the frozen F1-B attack authority.

---

## 11. Immediate next actions

1. Await independent re-review of availability ZIP V3 `01ce9b37…` and of the S2
   feature authority `81b570ab…`.
2. **Lane B2**: adversarial cases first, then the row/count authority with the
   three roots, consuming `81b570ab…`.
3. **Lane C**: promotion successor schema/verifier/entrypoint, synthetic only.
4. Ledger: `ledger/t0-v20-binding-20260907` holds DEC-016 and the peer's
   secondary verification `2faaa6cf…`. This lane carries DEC-016 (ported),
   DEC-017 (lane opened) and DEC-018 (the two parallel authorizations).
