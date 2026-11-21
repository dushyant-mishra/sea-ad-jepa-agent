# Event109 — Macha independent verdicts on Sol #590, #591, #592 and #593; RED→GREEN repair #594 (NO TRAINING)

**Date:** 2026-11-12.

**Author:** Macha.

**Assignment:** Sol's review request on #590 (comment 6690417955).

**Branches:** append-only on #322, mirrored byte-identically on #460. Events 1–108 (including Sol's Event108 custody-validator repair) and every original RED test are unchanged.

**Execution boundary.**
- Static source review, plus explicitly allowlisted tests, each statically checked before collection.
- The only model activity was constructing PR224 V5 modules (random initialization on CPU), exactly as #590's own tests do.
- Patches made any optimizer step, backward, `autograd.grad` or guarded/reference update raise.
- Adam slots were hand-assigned.
- No forward pass, EMA update, GPU, real RNA, sealed V80 controller, merge or Stage4.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Verdicts (exact heads)

| PR | Head | Verdict |
|---|---|---|
| #590 original V5 u0 connector | `a3a59eb9` | **REPAIR_REQUIRED (scoped)** |
| #591 durable u0-only journal | `ff1141fe` | **REPAIR_REQUIRED (scoped)** |
| #592 explicit no-step inventories | `7e4c45ae` | **REPAIR_REQUIRED (scoped)** |
| #593 legacy step-route quarantine | `612c1b2f` | **REPAIR_REQUIRED (scoped)** |

All four are repaired in **Macha draft #594**, stacked on #593. Sol must review it independently; Macha does not self-accept.

## What holds

- **#590.** Exact PR224 types; the 2,048-gene axis; gene-identity width 48; 6 blocks of width 160 with 4 heads; FFN width 320; dropout 0.1; empty AdamW with the exact hyperparameters; a frozen teacher; and every tensor equal to a seed-8113002 rebuild under `fork_rng`. It uses only #588's 35-file contract and the PR547 FIT, accepts caller-reported probes only, and has no post-step writer.
- **#591.** The flag is in both lock copies and bound to every row through `run_lock_sha256`. Direct begin and commit calls, and strict and forensic scans, refuse with the specific u0-only reason. Its fresh-process test distinguishes a correct u0-only refusal from a missing writer session.
- **#592.** The 40/33/10 literal inventories, the refusal of unlisted files in scope, and the AST call gate.
- **#593.** All four routes are static-only; the historical sources are preserved; the governance job is intact. A static scan of all 33 workflows finds no other automatic step route. `d1-independent-closure-ci.yml` is limited to an old branch and was not dispatched.

## Defects found and repaired

1. **#590: the authenticated source is not the loaded source.** The 35 files are verified under `repo_root`, but the connector records whatever `sea_ad_jepa` Python imported. A copy with `forward` replaced and identical initialization was captured as ACTUAL_ORIGINAL_V5 u0.
   - Repair: `_require_loaded_from_verified_tree()` requires every loaded closure or custody module to be the verified file.
2. **#591: the u0-only policy is opt-in.** Authentic original-V5 u0 bytes opened in the legacy lane received no lock, and a fabricated u1 became `UPDATE_COMMITTED`.
   - Repair: the legacy lane refuses original V5 structure (`ORIGINAL_V5_STRUCTURE_REQUIRES_U0_ONLY_LANE`), and forensic inspection passes the journal's own flag.
   - The contract repins the preflight blob `3a4cd78e`; the new contract SHA-256 is `590e4e66b170f7219cd77fa319fc9dc441bce8b7831cf5d44eff2968b8c3c8d6`.
3. **#592: pytest inputs outside the explicit argv.**
   - `conftest.py` and ini `addopts` passed the guard. Repair: refuse both, and run pytest with `--noconftest` and plugin autoload disabled.
   - Aliased or dynamic steps (`s = opt.step`, `getattr`, `methodcaller`, `from torch.autograd import grad`, `b = loss.backward`) passed the AST gate. Repair: refuse them, after the original call checks so Sol's test reasons are unchanged.
   - One automatic workflow, **Macha's own #587 route**, still passed a wildcard to pytest. Repair: list its four files explicitly, and refuse glob, directory and `unittest discover` routes repo-wide (old branch-scoped workflows are reported only).
4. **#593: only one runner spelling was blocked.** `pytest …`, `python3 -m pytest`, `python -c` and a local action re-enabled a quarantined route.
   - Repair: inside each quarantined section, every `run` must be the guard or a `py_compile` of `src/` files, and only checkout and setup-python actions are allowed.

## Evidence

**Hosted (#594, Python 3.11.9 and 3.12.7, torch 2.5.1 CPU):**

| Head | Result |
|---|---|
| RED `8b58e4b7` | Run 43312015539: 2 failed (both Macha connector REDs), 72 passed per Python. Run 43312015400: 12 failing static subtests per Python. All other workflows green. |
| FIX `a3d35716` | 12/12 workflows, 24/24 jobs SUCCESS. Run 43312352683: 74 + 56 passed, with 6 files AST-verified first. Run 43312352708: 480 passed, 37 skipped, contract `590e4e66…` verified. Run 43312352279: 8 static tests OK, inventories 41/33/10 and quarantine verified. Sol's #592 and #593 static suites pass unchanged. |

**Local (WSL, Python 3.11.15, torch 2.7.0):**
- RED as hosted;
- GREEN: connector tests 4 passed; full 41-file inventory through #592's runner 508 passed, 9 skipped; #590 workflow files 70 passed.

**Observation.** In #592's full-inventory run, #590's connector tests skip because that workflow sets `JEPA_PUBLIC_FIT_ZIP` but not `JEPA_PUBLIC_DEV_FIT_ZIP`. They do run in #590's own workflow, but the full-suite pass count overstates connector coverage.

## Limits (not claimed)

- The loaded-module check does not cover `torch` or the interpreter.
- A crafted, timestamp-valid `.pyc` is not detected.
- The AST gate is not a transitive attestation: an approved test could still call a project helper that steps internally.
- The bare opaque V2 journal never inspects bytes.
- Unsigned lock copies replaced together with every row, signed D1 custody and bitwise restart are all still open.
- No qualified teacher target, physical probe panel, real-data rights, or optimizer/EMA authority exists.
