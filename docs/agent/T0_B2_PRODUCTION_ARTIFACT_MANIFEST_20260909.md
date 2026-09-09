# T0 production B2 — artifact manifest and hash report

The production B2 substrate run and the population raw-source closure, executed
from committed code and replayed from disk.

## Why the artifacts are referenced rather than committed

`outputs/` is gitignored deliberately, and this is the reason: committing a
package member as tracked text lets the platform line-ending filter rewrite its
bytes on checkout, which changes its SHA-256 and therefore breaks the package
root the member is bound by. That failure already happened once in this lane — a
frozen availability package committed as tracked text produced `a4424482…` on a
fresh checkout instead of `e49c4e93…`.

So the artifacts are named here by exact path, size and SHA-256, with the package
root, and a reviewer reproduces them by running the committed runner.

## Reproducing

    python scripts/v4/t0_b2_production_run_v1.py \
        --outdir outputs/t0_b2_production_20260909 \
        --store "<phase2>/expression_level4" \
        --membership "<accepted membership csv>" \
        --source "<SEAAD_MTG_RNAseq_final-nuclei.2026-06-22.h5ad>"

    python scripts/v4/t0_b2_production_replay_v1.py \
        --pkgdir outputs/t0_b2_production_20260909 \
        --store "<phase2>/expression_level4" \
        --membership "<accepted membership csv>" \
        --rebuild-substrate

## Code identities the run recorded

    runner            736a31c1c317c37163dee2dc52a7fcf98e15000ddc217e8df235da991e0ad798
    raw-source module 25744294ca6eb6ef66786422f70519a6e469b12a0c86dbd11d38b08ff0b4ee5b
    row-count module  253bf3d747f877790294e2046dfb66596fcd2cc9910f33193779728b3806ca5f

Git blob content digests (LF bytes), so they are reproducible from the branch
rather than from a checkout's worktree bytes.

## Inputs

    accepted immune membership  d471499836118ddaf963ae9241f612d2e9a78bff4add62834347fc0ca06a3529
    complete Phase2 manifest    66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29
    MTG H5AD source             e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79
    source bytes                32,978,570,763   (all hashed; digest_bytes_read matches)
    B1 feature authority root   538b73b8414f47c70507cb0c8b46a6d4787e019c49056e07d6b0238382cf99b8

Every one of the 1,247 operator-31 block metadata members was authenticated
against the digest the complete manifest declares for it, in a preflight and
again inside the closure.

## Roots produced

    population closure       ec350b8d9a30a8a08573f055b9a0c103d0f6805014998ac9975d94585421d397
    logical row authority    64ea880ff6cf19aca48e0f2e77edfa6d37fc4f5e20022011131c496173896fc3
    physical read plan       cc75cef0ebb9a05e6699546e18ae45b3555f488dc2e46db4c845370c5be23519
    population raw-source    0b3e44897f0a5af1951677af95110e16d46f9a285fe227c31e34f45137b98f1b
    authority package root   98eac4a68df7960e79739d236cf0febacdec52a33de76144b146dc29a5a64436

## Geometry, as measured

    complete manifest blocks   8,915
    operators                     42
    operator-31 blocks         1,247
    operator-31 metadata rows 638,150
    accepted logical rows     20,804
    donors                        46
    rows proven               20,804   of 20,804
    elapsed                    536.8 s

    source_library  min 1,221   median 5,733   max 66,590   total 139,196,165

## Artifacts

Directory `D:\jepa_t0_mat_20260908\outputs\t0_b2_production_20260909`
(gitignored).

| file | bytes | sha256 |
|---|---|---|
| `T0_RAW_SOURCE_POPULATION_REGISTRY.csv` | 1,677,306 | `4812f01a9596119d83f3821556c6599a696c79735961d1b1ad756994fda85f4c` |
| `T0_RAW_SOURCE_POPULATION_METADATA.json` | 1,905 | `7e660e149863348b74f43ba4cc4e5f2345054df1d087efadb1443edba0312fe5` |
| `T0_RAW_SOURCE_POPULATION_MANIFEST.csv` | 242 | `85a350220d39c78a87fad77d66709965412171861e01024680f87ec2eb7dedd9` |
| `T0_RAW_SOURCE_POPULATION_PACKAGE_ROOT_SHA256.txt` | 65 | `9cee84207a684128eb37da8ca35aca7f6a9c7000025bb9713a43fee6218a0983` |
| `T0_B2_PRODUCTION_RUN_SUMMARY.json` | 1,807 | `149684cfb831f1deef33207abb9fe89703f6420a6349c21a985f3fdaec4d86eb` |

The package root `98eac4a6…` is computed over the first three members only; the
run summary and the root file are run records, not package members.

Registry schema: `logical_index, expression_row, canonical_cell_id, donor_id,
source_library, stored_values_in_row`. No pathology field appears, and the
replay asserts that.

## What the run checked, per the required list

| required | how |
|---|---|
| exact expected row count 20,804 | `expected_row_count` on the proof; closure also asserts `target_cells` |
| source SHA `e06000cb…` | whole asset hashed, compared before opening |
| source byte count recorded | `source_bytes` and `digest_bytes_read`, both 32,978,570,763 |
| every logical index proven exactly once | package writer refuses gaps or repeats; replay re-checks |
| every `expression_row` matched to the source row | the proof reads at the bound row and compares identity there |
| every source row matched to `canonical_cell_id` | `obs['exp_component_name']` at that row |
| every source row matched to `donor_id` | `obs['Donor ID']` categorical at that row |
| every `source_library` recomputed | summed from `layers/UMIs` at that row and compared |
| no pathology fields read | `obs` reads confined to two fields; `assert_no_pathology_read` guards the set |
| no skipped rows | 20,804 of 20,804, cardinality asserted |
| no duplicate rows | index uniqueness asserted at write and at replay |
| no mismatches | any mismatch raises; the run completed without one |

## Replay result

    all three substrate roots reproduced from the frozen inputs
    population root recomputed from the reloaded registry and equal to stored
    stored == recomputed == externally expected
    20,804 rows replayed
    no pathology field in the emitted schema
    REPLAY PASS

## Reproducibility note worth stating

An earlier attempt at this run was driven from a temporary script with an
unpushed local edit. Its numbers were real but not reproducible from committed
code, so they were not claimable, and an external review said so. The committed
runner produced **the same** closure, logical, physical-plan and population roots
as that attempt, which is a useful independent check on both — but the claim rests
only on the committed run.

## Terminals

`PRODUCTION_B2_NOT_RUN` no longer holds: the production B2 substrate run has been
executed and replayed. It was pathology-blind, and these remain in force:

    DONOR_ROLE_GATE_SHUT
    NUMERIC_CONFIRMATION_AT8_NOT_ACCESSED
    real_execution_ready=False
    NO_ELIGIBLE_DONOR_CONSTRUCTION

No authority is self-promoted to PASS. The next step is the technical-completeness
production run consuming this population authority together with the authenticated
closure, physical plan, B1 projection and counts payloads; eligible-donor
construction stays closed until that also replays cleanly.
