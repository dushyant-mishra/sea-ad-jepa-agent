# TD G6/G7 full custody successor: implementation and canonical qualification record

Date: 2026-10-11

Status: `QUALIFIED_FOR_OWNER_DECISION__NO_VALUE_READ`

Hard terminal: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## What this record is

This branch repairs the G6/G7 V2 custody code before any owner decision. It is a code and test record only:

- no real owner-decision record was created;
- no runtime value authorization was created;
- G6 and G7 were never run on real data;
- no corrected expression or count array was read.

The only real files any test read are the three PR #259 value-blind artifacts: the driver receipt, the mapping receipt and the replay manifest.

## Heads

| | commit |
|---|---|
| Inherited base (PR #268 head) | `d8fa3024e06e265b77353c8382453e7ccbf2350f` |
| Implementation head (qualified) | `43cac77da52446f6391874eb8f5be7ce3ed4e0f7` |
| Branch | `fix/td-g6g7-full-custody-successor-20261011` |

Commits after the implementation head add only this record, its evidence and the qualification runner (`docs/agent/TD_G6G7_FULL_CUSTODY_SUCCESSOR_20261011/`).

## Inherited baseline: three failures, not one

At `d8fa3024` the focused suite had three failures (`evidence/RED_00_inherited_baseline_d8fa3024.txt`).

PR #268 described only the first one.

1. `test_g7_attempt_concurrent_start_has_exactly_one_winner`. This is the intended RED: two concurrent G7 starters both won.
2. `test_g7_requires_same_authority_g6_pass_receipt`. It has failed since `c5d9c64c`, which is the failure PR #266 recorded. The test looks for "g6 pass", but the message said "G6 V2 PASS".
3. `test_no_overlap_control_flow_precedes_s174_count_open...`. It broke at `16f05bd3` (PR #267). That commit moved the S174 count load into `open_authenticated_overlap_count_sources`, so the source-text anchor no longer exists. The protection itself still held.

All three pass at the implementation head. How each was resolved is described under items 4, 5 and 9 below.

## Repairs: RED first, then GREEN

Each repair has a failing test committed first, with its log, followed by the fix commit with its passing log. Every log is in `evidence/`. A RED marked "semantic" fails because the inherited code accepts the defect. A RED marked "parameter" fails because the inherited gate had no way to take the new input.

### Item 1: owner-decision binding

RED: `RED_01`, with the semantic demonstration `demo_gate_without_owner_decision.py`. The inherited gate accepted an authorization bound to no owner-decision record.

GREEN: `GREEN_01`.

`load_runtime_authorization` now requires `owner_decision_path`. `common.load_owner_decision` verifies the record. Its contract is:

| field | required value |
|---|---|
| `schema` | `JEPA_TD_RELATIONAL_G6_G7_OWNER_DECISION_V1` |
| `decision` | exactly `AUTHORIZE_G6_G7_INTEGRITY_ONLY` |
| `authorized_pr259_preflight_driver_sha256` | `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae` |
| `authorized_pr259_mapping_receipt_sha256` | `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0` |
| `qualified_implementation_commit_sha` | the commit G6/G7 execute from (checked against `code_identity`) |
| `biological_replay_authorized`, `target_selection_authorized`, `td60_authorized`, `training_authorized` | JSON `false` (missing, `"false"` or `0` is refused) |
| any other `*_authorized` key | refused unless `false` |

The runtime authorization must also bind `owner_decision_sha256`, which is the physical SHA-256 of the record file. A record edited after authorization is refused, even if its JSON content is unchanged. G6 and G7 take `--owner-decision` and write its SHA into the authority trace, so G6 and G7 are bound to the same owner decision. Tests use synthetic records only.

### Item 2: exact PR #259 physical bytes

RED: `RED_02`, with the semantic demonstration `demo_inherited_gate_semantics.py`. The inherited gate accepted a reformatted driver receipt and a reformatted mapping receipt, each with an authorization built around the altered bytes.

GREEN: `GREEN_02`.

`common.require_pr259_physical_bytes` accepts only these exact bytes:
- the driver receipt `62f2af4a…`;
- the mapping receipt `6a97cb30…`;
- the replay manifest `4bde5f80…`.

The authorization must also bind `replay_manifest_sha256`. The existing gate tests were moved to a shared synthetic fixture: only the call sites changed, and every assertion is unchanged. `GREEN_02` notes one caveat: its old-signature demonstration refuses for an unrelated reason and is not evidence for item 1.

### Item 3: G6 attempt spending

RED: `RED_03`. With two simultaneous starters, a new directory produced zero winners (a `mkdir` race), and an existing empty directory produced two winners. A spent namespace was not reported as "already spent".

GREEN: `GREEN_03`.

`begin_namespace` now creates the marker with `O_CREAT|O_EXCL` through `common.exclusive_create_json`, followed by an fsync. The marker is never removed, and a foreign file appearing before the marker is refused. The new tests force both starters to reach the creation call at the same moment. Results were stable over three runs.

### Item 4: G7 attempt spending

RED: `RED_04`. The inherited PR #268 test, kept unchanged, and a new forced-race test both showed two winners.

GREEN: `GREEN_04`. The same exclusive-create mechanism is used, and the losing starter gets "already spent". The immutable pre-check is kept.

### Item 5: G6→G7 prerequisite

RED: `RED_05`. The positive control is a real G6 run on the synthetic world. Its recorded trace equals the trace G7 computes itself. The inherited validator caught only a changed trace or a true flag, and accepted 27 corruptions.

GREEN: `GREEN_05`.

`load_g6_pass_receipt` now requires the exact G6 PASS namespace, and nothing else in it:
- the start marker;
- the receipt;
- the manifest;
- the values file;
- the metadata file.

It also requires:
- values and metadata SHAs equal to what the receipt and manifest bind;
- the same authority trace on the receipt, the manifest and the start marker;
- the exact G6 input-authority hashes, including the historical CSR and TD50 member hashes;
- the frozen Sample-A coverage;
- no claim that all rows were reread;
- the four `false` flags.

G7 records the SHA of every verified G6 file. The G6 output names, schemas and historical pins now live once in the common module, so the writer and the validator cannot drift apart.

The inherited test that accepted a bare minimal PASS receipt as its positive case now asserts that the receipt is refused. Its two negative cases are unchanged. The "g6 pass" assertion now holds because the message reads "G7 requires G6 PASS (V2 receipt)".

### Item 6: NPH52 duplicate CSR indices

RED: `RED_06`. A duplicate address index was silently resolved last-wins, whether inside or outside the replay set.

GREEN: `GREEN_06`. The check runs on the row slice before the dictionary is built. Historical values and hashes are untouched, and a passthrough test proves the values are unmodified.

### Item 7: G6 receipt semantics

RED: `RED_07`, run through the real G6 entrypoint on the synthetic world.

GREEN: `GREEN_07`.

`source_library_exact_rows` (25000) is removed. The receipt now reports three separate counts:
- `hvs_sea_physically_reread_source_library_verified_rows`: 23690 in production;
- `nph52_authenticated_historical_passthrough_rows`: 1310;
- `total_sample_a_rows`: 25000.

These are counted from the rows actually processed, checked against the frozen geometry, and accompanied by an explicit verification-scope sentence.

### Item 8: strict raw counts

`RED_08` and `GREEN_08`.

Preservation, which already passed on the inherited code:
- the G6/G7 physical decoders and the S174 rows and payload reject fractional, negative, NaN and ±inf counts;
- an AST scan finds no `round`, `around`, `rint`, `floor`, `ceil`, `trunc` or `fix` call in the three V2 scripts.

The scanner has a planted-`round` positive control. Its only exemption is the exact integrality comparator `np.equal(x, np.floor(x))`.

RED found: G6 `sentinel_maps` truncated fractional or non-finite TD50 `source_library`, `detected` and `global_row` values with `astype`. It now uses `common.strict_integer_array`.

### Item 9: PR #267 protections

`PRESERVE_09`. No production change was made for this item. New behavioural tests run the real G7 entrypoint on synthetic S174 shards after a genuine synthetic G6 PASS:

| case | expected outcome |
|---|---|
| exact natural overlap | PASS (exit 0); every replay address checked, including implicit zeros; immediate-use hashes recorded |
| one mismatch | non-success (exit 2) |
| zero overlap | NOT_ESTIMABLE (exit 3); S174 counts and physical values are never opened |
| a zero-overlap matrix among overlapping ones | never count-loaded |
| a repeated attempt | refused as already spent |
| a changed G1b shard | refused |

These tests were mutation-checked against three mutations: zero overlap reported as PASS, implicit zeros skipped, and a mismatch counted as success. Each mutation is caught. The stale source-inspection test is re-anchored on `open_authenticated_overlap_count_sources`. It also asserts that the helper authenticates the physical H5AD before loading S174 counts.

The inherited unit tests still cover the rest of the PR #267 protections:
- G1b result and freeze validation;
- immediate S174 meta and count re-hashing;
- duplicate cell ID and duplicate CSR address rejection;
- 41,238-column geometry;
- counterpart authentication.

## Additional fail-closed findings (beyond the nine items; flagged for the owner)

These go beyond the nine listed items. Each only refuses input that is malformed or misread, and none changes a value on well-formed input. The owner may veto any of them.

- **X1: Sample-A text sort.** G6/G7 read the Sample-A freeze with `dtype=str` and sorted `sample_row` as text. Any Sample A with 11 or more rows, including the real 25,000, would fail the frozen order check. On real data, the first authorized G6 run would have stopped after spending its immutable attempt. Rows are now ordered numerically, and a genuinely missing row is still refused. Evidence: `RED_X1` and `GREEN_X1`.
- **X2: duplicate physical H5AD column index.** G6/G7 `corrected_row` silently double-counted a duplicated unmapped column into the library total. Such a row is now refused. Evidence: `RED_06` and `GREEN_06`.
- **X3: TD50 sentinel truncation.** This is the defect described under item 8.

## Residual risks, stated plainly

- **No real data was examined.** The NPH52 duplicate-index check and the physical duplicate-column check have never run on real data, because reading those arrays is outside this assignment. If real data violates either check, G6 will stop, and that stop must be preserved.
- **Code identity is synthetic in every test.** Every synthetic test replaces `code_identity` (git cleanliness and commit identity) with a fixed fake. The real function is exercised only at real execution time.
- **G1b authority is synthetic in end-to-end tests.** The production G1b authority is read from git at `4ab8e210`. The G7 end-to-end tests replace it with a synthetic freeze. The G1b result and freeze validators keep their inherited unit tests.
- **Gate fixtures redirect the pins.** The synthetic gate fixtures point the PR #259 pins at synthetic receipts. Only `QUAL_02` checks the real pins against the real files.

## Canonical qualification

Run: `qualification_runner.sh` (in this folder), from a fresh, clean, detached worktree created at the implementation head (`/d/jepa_wt_td_g6g7_qual_20261011`). All logs are written outside that worktree, to `qualification_43cac77d/`. The qualification worktree was never edited, and nothing was rerun.

| check | result | log |
|---|---|---|
| initial and final exact head | `43cac77da52446f6391874eb8f5be7ce3ed4e0f7` both | `QUAL_00`, `QUAL_05` |
| tracked status before and after; untracked files | clean; none | `QUAL_00`, `QUAL_05` |
| versions | Python 3.9.7, numpy 1.24.2, pandas 1.5.3, scipy 1.10.1, h5py 3.2.1, pytest 6.2.4 | `QUAL_00` |
| complete focused suite (11 files: common, G6, G7, custody including the inherited PR #268 race, G6 race, owner decision, PR #259 pins, strict counts, row order, G6 end to end, G7 prerequisite, G7 end to end) | **166 passed, 0 failed, 0 skipped** | `QUAL_01` |
| `python -m pytest -q tests/v5/test_td_relational_pr259_real_receipt_compat.py -rs` against the original physical PR #259 files (from PASS record `a075b472`) | **1 passed / 0 skipped / 0 failed** | `QUAL_02` |
| real driver, mapping and replay-manifest SHAs | `62f2af4a...`, `6a97cb30...`, `4bde5f80...`, equal to the pins; replay-manifest pin MATCH | `QUAL_02` |
| changed-file inventory from `d8fa3024` | 40 files: 3 production scripts, 14 test files, evidence | `QUAL_03` |
| production script SHA-256 (raw = LF-canonical = git blob) | common `383104c358d5b190d7a65f73d6c143f67e737379d43589d25cdcb1c940ba110f`; G6 `6e35c4c89fbc6772eb16e9dd44259e71590f2e15ec0215d25914121adbcbac63`; G7 `6250f3a87abfb1bd8625a19c6ab9a69ff8e5e43ee1ddae30ddc659a3d3fe5220` | `QUAL_03` |
| no real owner decision, authorization or G6/G7 output | the owner-decision schema appears only in code, tests and pytest output inside evidence logs; no tracked G6/G7 output file | `QUAL_04` |

These results are local execution evidence on the canonical Windows machine; CI did not run them. The compatibility test depends on the PR #259 files outside this branch (paths in `QUAL_02`). Every other test is synthetic and self-contained.

## Next owner decision

The first owner decision after this record is the explicit value-integrity authorization `AUTHORIZE_G6_G7_INTEGRITY_ONLY`, written as an immutable record to the contract under item 1. It must name the qualified implementation commit `43cac77da52446f6391874eb8f5be7ce3ed4e0f7`.

Until then, the following remain unauthorized:
- G6/G7 on real values;
- corrected TD56/TD57B/TD57C/TD59;
- TD60;
- target selection;
- representation selection;
- Stage 4;
- training.
