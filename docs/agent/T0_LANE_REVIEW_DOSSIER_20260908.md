# T0 lane — review dossier, 2026-09-08

For a reviewer who has not seen this work. It lists every defect found so far,
who found it, what was done, and — importantly — exactly which commits and
artifacts have **not** been independently reviewed yet.

Branch `t0/v20-pathology-blind-materialization-20260908`, head
`e4187f25127fe9c442d4a22314cfef2db6ad5f30`, 17 commits on sealed base
`21ec629667eeda5a7d37d3f1d822fbf93b213325`.

Ten files changed across the whole branch. Nothing else.

---

## 1. How to verify independently

```
git log --reverse --format="%h  %s" 21ec629667eeda5a7d37d3f1d822fbf93b213325..HEAD
git diff --name-only 21ec629667eeda5a7d37d3f1d822fbf93b213325..HEAD
git rev-parse origin/coordination/project-consolidation-20260907   # must be 21ec6296...

conda run -n sea-ad-jepa-v3 python -m pytest -q \
  tests/test_work_checkpoint_v1.py \
  tests/v4/test_t0_at8_availability_authority_v1.py \
  tests/v4/test_t0_v20_feature_projection_authority_v1.py
# expected: 98 passed   (86 test functions + 12 parametrized cases)

conda run -n sea-ad-jepa-v3 python scripts/agent/work_checkpoint.py validate \
  --worktree "D:/jepa_t0_mat_20260908" \
  --checkpoint docs/agent/CURRENT_WORK_CHECKPOINT.json
# expected: {"status": "PASS"}
```

Do **not** run `pytest tests/v4/` — see §6.

---

## 2. Commit-by-commit review status

| commit | subject | independently reviewed? |
|---|---|---|
| `ba83e4a4` | validate tracked authorities from Git blob bytes | **yes** — source review passed |
| `bce0fd4b` | open the lane (DEC-016 ported, DEC-017) | **yes** |
| `1396a483` | clear the in-flight modification declaration | **yes** |
| `8a4ac967` | canonical authority path identities | **yes** — the two defects it fixed were reviewer-found |
| `6ebab737` | correct rendered gate, blockers, pins | **yes** |
| `58c9c21c` | availability adversarial cases (red) | **yes** |
| `55f262cb` | availability authority implementation | **yes** — V1 archive attacked in depth |
| `45151ec8` | keep availability package out of CRLF-filtered text | **yes** |
| `e01d1b8d` | close two self-audit defects | **yes** — confirmed grounded in the pushed branch |
| `95c5bb95` | close reviewer-found TOCTOU + index protection | **yes** — and the review of it produced three more findings |
| `49611d2e` | S2 projection adversarial cases (red) | **partly** — the primitive was reviewed, not the commit |
| `e4c0f4da` | S2 projection implementation | **partly** — "math is good, authority binding is not finished" |
| `e5bdd4fa` | index-mode fail-open + stronger TOCTOU regression | **NO** |
| `3733c6c9` | record S2 projection, membership provenance, stale-field removal | **partly** — reviewed, but reviewer read a pre-fix state |
| `f6a63ae4` | close the frozen-package loader member TOCTOU | **NO** |
| `2e48f365` | bind the S2 feature authority, not only its rows | **NO** |
| `e4187f25` | scope statement, vocabulary, handoff | **NO** |

**Four commits have never been reviewed: `e5bdd4fa`, `f6a63ae4`, `2e48f365`,
`e4187f25`.** Those four contain the index-mode fix, the loader TOCTOU fix, the
S2 authority binding and the documentation pass.

One coordination note worth knowing: the reviewer twice reviewed a commit that
predated the relevant fix and reported a defect as still open. Check the head
SHA before concluding something is unfixed.

---

## 3. Defect ledger

### 3.1 Found by independent review

| # | defect | reproduced? | repair | commit |
|---|---|---|---|---|
| R1 | authority path treated as a Git **pathspec**, so `:authority.txt`, `:(literal)authority.txt` and `./authority.txt` all resolved to the same blob; returned path never compared to the declared one | yes, locally before repair | one canonical spelling only; `--literal-pathspecs`; returned path must equal the declaration | `8a4ac967` |
| R2 | disk fallback had no containment or declaration requirement, so `../outside_authority.txt` validated with `allowed_untracked_files=[]` | yes — `validate` returned `[]` | local authority must be declared, in the untracked inventory, inside the worktree, not a symlink | `8a4ac967` |
| R3 | availability **source** check-then-use: the file was hashed by path, reopened for parsing, and `stat`ed again for the byte count | by inspection | read once, authenticate those bytes, parse from memory, `source_bytes = len(authenticated)` | `95c5bb95` |
| R4 | checkpoint validator **index protection** regressed: a staged replacement with the worktree restored validated clean | yes — index `1ac17412…` vs bound `2412992050dc…`, `validate` returned `[]` | compare bound entry against **both** index and worktree | `95c5bb95` |
| R5 | loader accepted a **self-consistent replacement** package, because the manifest was only compared with the root beside it | yes | both expected roots are now **required keyword arguments** | `95c5bb95` |
| R6 | loader ignored **unmanifested extra files** | yes | directory must hold exactly the four known files | `95c5bb95` |
| R7 | `membership_donor_count` alone does not identify a set; with all donors available any 46 of 84 satisfied the same counts | n/a | canonical `membership_donor_set_sha256` + a donor-identity-only witness + the accepted-V20 member digest | `3733c6c9` |
| R8 | index **mode** fail-open: `--chmod` preserves the blob, so comparing object ids alone missed a staged `100644`→`100755` flip | yes — ids equal, modes differ, gate reported clean | bound mode passed in and compared | `e5bdd4fa` |
| R9 | my TOCTOU regression contained `assert ... or True`, which proves nothing, and never exercised the full builder | n/a | wrapped reader authenticates A, replaces the file with B, returns A; registry, digest and byte count must all come from A | `e5bdd4fa` |
| R10 | stale `outcome_values_read` / `outcome_values_emitted` contradicted the corrected `value_handling` block | n/a | deleted | `3733c6c9` |
| R11 | frozen-**package** loader check-then-use: members authenticated by path then reopened for parsing | yes — a same-length metadata substitution was returned with `membership_donor_set_sha256` all zeros while both external roots still verified | capture every member once; all digests, both roots and all parsing from captured bytes; regression asserts **no member is opened twice** | `f6a63ae4` |
| R12 | review archive could not run its own tests as extracted (tests at `tests/`, code at `code/`, but tests resolve `parents[2]/scripts/v4`) | yes | repository-relative layout + `RUN_REVIEW.md`; verified by extracting to a clean directory and running 26 cases from there | `f6a63ae4` |
| R13 | `projection_root` bound only the ordered rows, so the same root verified after altering `matrix_id`, `address_space_size`, split/registry/support digests, schema, namespace, role counts or `real_execution_ready` | yes, on production data | added `feature_authority_root` binding all of it; verifier requires both roots externally | `2e48f365` |
| R14 | the split's own `molecular_address_index` column and the support table's were read and silently ignored; a disagreement let the registry quietly win | n/a | both cross-checked against the frozen registry; disagreement is a STOP | `2e48f365` |
| R15 | `source_feature_index` guarded by a **static substring test** — the fail-open class already condemned in F1B, and it broke the moment an unrelated field mentioned the token | n/a | behavioural: every fixture row carries `source_feature_index = 999999`, out of range, and emitted indices must still come only from the registry | `2e48f365` |
| R16 | governance inconsistencies: `donor_roles.reason` contradicted its own note; `owner_authorization` described only S2; `gates.current` was stale; pins abbreviated to 7 characters; three verified Phase2 authorities unrecorded; reader-validation/oracle closures not machine-readable | n/a | all corrected; DEC-018 added | `6ebab737`, `3733c6c9` |

### 3.2 Found by my own audit of my own work

| # | defect | how it surfaced | commit |
|---|---|---|---|
| S1 | the checkpoint validator hashed **worktree** bytes while declaring **Git blob** digests, so it could not validate its own four declared authorities on any Windows checkout | attempting to satisfy the mandated startup gate | `ba83e4a4` |
| S2 | dirtiness measured against **current** HEAD rather than the checkpoint-bound commit — a later commit could replace a declared authority with no authority-level complaint | self-audit | `e01d1b8d` |
| S3 | **a test of mine ratified S2 as correct behaviour**, asserting there should be no complaint in exactly that scenario | self-audit | `e01d1b8d` |
| S4 | a truncating file rewrite silently deleted **seven** regression cases; noticed only because the suite count fell 30 → 24, not by reading the diff | self-audit | `e01d1b8d` |
| S5 | availability builder crashed with an unhandled `FileExistsError` on an existing but empty output directory | self-audit | `e01d1b8d` |
| S6 | I committed the frozen availability package as tracked text, so a fresh checkout produced `a4424482…` instead of the declared `e49c4e93…`, and the loader could not verify its own package after a clone | self-audit | `45151ec8` |
| S7 | availability metadata recorded an absolute `D:/Jepa project/…` source path — environment noise that would change the package root on another machine | self-audit | `55f262cb` |
| S8 | single-root design could not express value-blindness, because binding the source digest meant the root moved whenever values moved | my own metamorphic case failed | `55f262cb` |
| S9 | I reintroduced `or True is False` while writing the replacement for R9, and removed it before applying | reading my own patch | `e5bdd4fa` |
| S10 | my synthetic projection fixture was internally inconsistent — enumerated indices contradicting the registry it shipped | exposed the moment R14's cross-check was added; four cases failed | `2e48f365` |
| S11 | I reported an **aggregate suite count before observing it**; the individual figures were real, the combined one was not yet | the aggregate run then aborted at collection | corrected in conversation |
| S12 | my first leak audit flagged 84 "decimals" in the registry; they were donor identifiers like `H19.33.004` matched by a crude regex — my audit was wrong, not the artifact | re-reading the output | n/a |
| S13 | my first reproduction probe for R11 fired at the hashing open, not between hash and parse, and was refused; I had to correct the probe before the defect appeared | re-reading the probe | n/a |
| S14 | I reported "68 of 35,076 frozen feature-split addresses are missing" as a hard blocker. It was **false** — I had joined against raw h5ad `var/gene_ids` instead of the canonical materialized store. All 35,076 are `measured_address=True` | prompted to search the project's own registries | corrected in conversation |
| S15 | I claimed HVS and SEA_AD share no `broad_class` labels. False — they share all three; my query had printed only the first 5 of 20 labels | peer correction | corrected in conversation |

**S3 is the one I would most want a reviewer to weigh.** A wrong assertion is
worse than no assertion: it certifies the hole and a green suite hides it.

---

## 4. What I claim is verified, and the evidence

| claim | evidence |
|---|---|
| accepted V20 package intact | recovered **by SHA, not by path** (size-filtered candidates, each hashed, exactly one match); 154/154 members; root `896dce25…`; all nine named digests; 224/224 suite; 22/22 static audit; 18/18 execution-binding |
| availability derivation correct | 84/84 available, 0 blank, 0 in the missingness vocabulary; derived not assumed (a fixture with known missingness must not report full availability); measured zero counts as available |
| availability is value-blind | metamorphic: values all replaced, `availability_root` byte-identical; paired discriminator: blank one value, root changes; AST test forbids `float`/`int`/`to_numeric`/`read_csv`/`astype`/`mean`/`sum` and any pandas/numpy import |
| `availability_root` is stable | `e49c4e93…` reproduced across **six** builds, through a label change, added metadata, a relocation, a code fix and the loader rewrite |
| no member is read twice | open counts measured per member: manifest 1, metadata 1, root 1, registry 1 |
| membership set is the accepted-V20 set | recomputed from member `d4714998…`; witness `6f8e20d3…`; digest `f8983834…` |
| S2 projection correct | 35,076 features, all `measured_address=True`; **V18 §3 independently declares SCORING = 28,061 and the projection observes exactly 28,061** |
| authority root binds meaning | on production data, a `matrix_id` mutation leaves `projection_root` identical and moves `feature_authority_root` |
| real T0 cannot run | `real_execution_ready` is assigned `False` in exactly two places and `True` **nowhere**; V20's verifiers accept only `False` while its production gate proceeds only on `True` |

---

## 5. Honest limitations — please attack these

1. **The ordering guarantee is vacuous for the accepted split.** That split is
   itself strictly increasing in `molecular_address_index` (0 → 41,194), so
   split-order and address-order roots are identical. Only synthetic fixtures
   exercise the guarantee.
2. **`_donor_set_digest` proves a set, not a provenance chain.** The witness and
   member digest close the current claim, but nothing prevents a future caller
   passing a different 46-donor list; only the recorded digests catch that.
3. **The availability package is self-describing.** An adversary who rewrites all
   four members *and* the externally recorded roots in governance would pass. The
   external roots are the only anchor.
4. **`source_library` is bound as declared, not as loaded.** Nothing yet proves
   the Phase2 blocks are the counts the frozen reader would load for these exact
   rows. Same defect class recorded against F1's `VerifiedSourceValues`. This is
   Lane B2's job.
5. **The AST value-blindness test is a whitelist of names.** A numeric conversion
   by another route — say `decimal.Decimal` or `array` — would not be caught. The
   metamorphic case is the real defence; the AST test is supporting.
6. **No CI.** Every figure here is a local run on one machine.
7. **The missingness vocabulary is a frozen list** (`""`, `na`, `n/a`, `nan`,
   `none`, `null`, `.`). A token outside it, e.g. `-` or `unknown`, would be read
   as available. All 84 real values are non-missing so it does not bite today,
   but I have **not** proven every real value is numeric-shaped.

---

## 6. Pre-existing defects flagged, not fixed

- **`pytest tests/v4/` aborts at collection.** Three files from commit
  `2d929e41` perform file I/O at *import* time and raise `FileNotFoundError` in
  any worktree lacking their data, which takes unrelated passing tests down with
  them. Fails identically at the sealed base. Same fail-open family: a test that
  cannot be collected reports nothing. Outside this lane's authorization.
- **The T0 lane has no versioned source in the repository.** DEC-016 binds
  digests of a 154-member package that survives only as loose local copies.
- **`core.autocrlf=true` plus blob-digest declarations** is a repository-wide
  trap, not a lane-local one.

---

## 7. Suggested review targets, in the order I would attack them

1. `f6a63ae4` — the loader rewrite. Try substituting a member between capture and
   use by a route other than `Path.open`; try a hard link; try a directory
   junction pointing at a valid package.
2. `2e48f365` — the authority binding. Look for a field the authority root should
   cover and does not. `role_counts` and `authority_binding` are dicts; check
   ordering assumptions in the digest.
3. `e5bdd4fa` — index mode. Try a stage-1/2/3 index entry rather than stage 0,
   and an intent-to-add entry.
4. `01ce9b37…` (availability ZIP V3) — the re-review that was requested.
5. The `_donor_set_digest` framing: `"T0_DONOR_IDENTITY_SET_V1"` then `|`-joined
   sorted ids. Check for a separator-injection collision via a donor id
   containing `|`.
6. `feature_authority_root` field framing: `name=value` joined by `|`. Same
   question.

---

## 8. What has not been built

- **Lane B2**, the row/count authority with `population_closure_root`,
  `logical_row_authority_root` and `physical_read_plan_root`. Not started. Must
  consume `81b570ab…`, not only `0a0739ec…`.
- **Lane C**, the promotion-only successor. Authorized, design not started.
- Donor roles. Blocked by
  `STOP_T0_DONOR_ROLE_AT8_AVAILABILITY_AUTHORITY_UNBOUND`, which lifts only when
  the availability authority is independently accepted.

Nothing in this lane authorizes real T0 execution. `real_execution_ready` is
false, pathology values are closed, and DEV, SEALED, reader-validation and
reader-oracle remain unauthorized.
