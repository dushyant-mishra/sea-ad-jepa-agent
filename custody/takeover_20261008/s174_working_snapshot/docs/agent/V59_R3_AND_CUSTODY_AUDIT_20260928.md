# V59 — audit of the V58 R3 ledger, custody and anchor probe

**Date 2026-09-28. Branch `claude/v59-r3-audit-and-external-cis-20260928`,
created from PR #195 head `7b5860b33e5afb6b3fd30387a07e3e268d76afcf` (verified
live against GitHub before any work). `TRAINING=OFF`. `TD60=BLOCKED`.
**No molecular biological outcome was opened. No protected pathology field was
opened.**

## Verdict

The R3 ledger is **sound and should be preserved as the starting implementation.**
Its semantics are correct and its tests genuinely pass. Three custody defects sit
around it, one of which is mine and is retracted below.

---

## RETRACTION — a claim I made and then disproved

I first reported that the R3 snapshot's SHA-256 did not match the stated
`03dbe2ed966e353aa750c336e7670ee63058c8acba23dd3c381a98521596ea4f`, and treated
that as a provenance defect.

**That was wrong, and the error was mine.** `03dbe2ed…` is the value of the
`ledger_sha256` **field inside** the snapshot, not the digest **of** the snapshot
file. Read correctly, it matches exactly. I compared the wrong object, then
spent a line-ending investigation on a discrepancy that did not exist.

Recording this rather than quietly correcting it, because "the digest does not
match" is precisely the kind of alarm that damages a record if issued carelessly.

---

## F1 — the ledger source files are byte-exact. Custody of CODE is clean.

| file | manifest digest | committed | |
|---|---|---|---|
| `src/sea_ad_jepa/regulatory/regulatory_exposure_ledger_v1.py` | `c2c8afa217df62fe…` | `c2c8afa217df62fe…` | **MATCH** |
| `tests/test_regulatory_exposure_ledger_v1.py` | `dab1c6ecef0808f4…` | `dab1c6ecef0808f4…` | **MATCH** |
| `scripts/regulatory/v53_external_anchor_benchmark.py` | `90b8154327b0467c…` | `90b8154327b0467c…` | **MATCH** |

The `/mnt/data/v58_r3/…` paths named in the handoff **do not exist on this
machine** — they are the other environment's filesystem. But the same files were
committed to the branch, and those committed bytes verify. The audit was
performed against git objects, not against a copy.

## F2 — the external-anchor RESULT digest genuinely does not match

`V58_REGULATORY_INDEPENDENCE_MANIFEST_20260928.json` pins

```
external_anchor_probe.local_result_sha256 = 79c07b9f7f699e5e1bfffea3eda32ae8…
```

explicitly as a **file** digest. The committed
`results/v58/V53_EXTERNAL_ANCHOR_SYNTHETIC_IDENTIFIABILITY_V1.json` hashes to

```
73ea945b122da4a39785cc87069a9920930e0853e7b642700532417ec54d3a8e
```

Not a line-ending artifact: the file contains **no CR bytes**, and none of
as-stored, LF-normalised, CRLF, trailing-newline-stripped or
trailing-newline-added variants reproduce the pinned value. The file carries no
self-digest field, so — unlike the R3 case — there is no alternative reading
that rescues it.

**Most likely cause, from the manifest's own words:** reconciliation used
`"exact_file_content_copy_forward__not_merge_commit"` because the connector
"exposes file writes but no branch merge action". Writing a JSON through a
file-write API re-serialises it. That would change bytes while preserving
content. **Plausible, and not verified** — I cannot confirm content equivalence
against an original I do not have.

**Consequence:** the anchor result is **not currently byte-attested**. Its
numbers may be correct; its custody is not closed. It must not be cited as a
pinned artifact until either the original bytes are produced or the manifest is
re-pinned to what is actually committed.

## F3 — `snapshot.ledger_sha256` is a dangling pointer

`03dbe2ed…` equals neither the committed ledger source (`c2c8afa2…`) nor any of
**12 canonicalisations** I tried of the snapshot's own content (`outcomes`,
`cross_source_rules`, `governance`, and the whole document minus the field
itself; each in compact, sorted-indent and unsorted-indent form).

So the snapshot pins a ledger digest that **cannot be reconstructed from
anything committed**. It is not wrong so much as unverifiable here. It should
either be re-pointed at the committed source digest or documented as referring
to an object held elsewhere.

## F4 — the R3 suite passes 7/7, but only under `PYTHONPATH=src`

```
$ pytest tests/test_regulatory_exposure_ledger_v1.py
ModuleNotFoundError: No module named 'sea_ad_jepa.regulatory'
Interrupted: 1 error during collection

$ PYTHONPATH=src pytest tests/test_regulatory_exposure_ledger_v1.py
7 passed
```

**A collection error runs ZERO tests.** On a runner that does not treat the exit
code as fatal, or in any summary that counts only failures, that reads as "no
failures" while nothing was checked. The stated "7 passed" is true and is an
**environment property, not a repository property**.

This is the **third instance of this exact failure class** in this project: the
V29 census tests were listed as CI path triggers with no step executing them,
and the conditional-composition portable bundle's collection error made four
test files run nothing.

**Fixed here** by a repository-level `conftest.py` that puts `src/` on
`sys.path`, so the bare command is correct. Verified: bare `pytest` now reports
**7 passed**.

---

## What the R3 ledger gets right, and should be preserved

Audited against the required semantics, by reading the committed source and
running its tests:

- exposure is keyed by exact **(source, modality, outcome_family)** — never
  dataset-wide. `GSE174367_MORABITO / ATAC / MARGINAL_ACCESSIBILITY_AND_COVERAGE`
  is `INSPECTED` while `… / ATAC / TARGET_STATE_CIS_CORRESPONDENCE` is still
  `UNKNOWN`. That distinction is the whole point and it is implemented, not
  merely documented.
- `UNKNOWN` does not mean pristine and never self-authorises confirmation.
- exposure state cannot regress.
- a construction source cannot confirm its own regulatory object.
- the UCI cross-source rule is present, carrying donors **1224 / 1230 / 1238**
  and `UNDETERMINED_POSSIBLE_UCI_DONOR_OVERLAP`.
- the ledger is deliberately non-authorising.

**This is finer-grained than the ledger I built earlier** on
`claude/regulatory-ledger-20260928` (`f1a68f38`), which keyed exposure by
*dataset*. Dataset-level keying would have wrongly blocked Morabito ATAC
target-state work merely because marginal accessibility had been inspected.
**The V58 implementation is better and mine should be superseded, not merged.**

One gap: the snapshot does not contain the literal string `NON_AUTHORIZING`,
though the handoff describes the ledger that way. The property is carried in
prose rather than as a machine-checkable field. Worth adding, since every other
guarantee here is enforced in code.

---

## Self-audit

**Starting SHA** `7b5860b33e5afb6b3fd30387a07e3e268d76afcf` (PR #195 head,
verified live). **Ending SHA** in the commit. **Branch/worktree**
`claude/v59-r3-audit-and-external-cis-20260928` in `D:/jepa_wt_v59_20260928`.

**Changed files:** `conftest.py` (**source**), this document (**docs**). No
result file, no test file, no historical file modified.

**Artifacts read, with digests:** committed ledger source `c2c8afa2…`, ledger
test `dab1c6ec…`, anchor script `90b81543…`, R3 snapshot `b8d993a2…` (file),
anchor result `73ea945b…` (file), plus the V58 manifest and handoff. The four
`/mnt/data/…` paths named in the brief are **ABSENT on this machine** and were
audited via their committed equivalents instead.

**External sources consulted:** none this turn.

**Molecular biological outcome opened: NO. Protected pathology field opened: NO.**
No Morabito, SEA-AD, GSE214979 or GSE272082 target-state regulatory outcome was
touched.

**Tests run locally:** `tests/test_regulatory_exposure_ledger_v1.py` — 7 passed
with `PYTHONPATH=src`; collection error bare; **7 passed bare after the conftest
fix**. **Tests run on hosted GitHub: none.** I did not trigger CI and make no
hosted-provenance claim.

**Skips/timeouts:** none in the R3 suite. Not re-run: R2, R4, V53–V57 — per
instruction, and I found no contradiction requiring it.

**Failed experiments, including RED:** my own initial digest-mismatch claim,
disproved and retracted above. Also carried forward and still RED: my
cross-modal cis probe on `claude/laneB-crossmodal-20260928` @ `671ccb3b`, whose
positive control cancels — it is not evidence for the cis strategy I argued for
in the V50 red-team.

**Strongest alternative explanation for F2:** the anchor result is content-identical
and only re-serialised, making the mismatch a pure custody-hygiene issue with no
scientific consequence. I consider this the most likely explanation and I cannot
confirm it without the original bytes.

**Strongest criticism of the external-map strategy I am about to recommend:**
every candidate class named in the brief — Nott, ABC, Corces, scE2G — is built
from bulk or sorted-population human brain data with donor counts in the tens or
fewer, and none was constructed to be independent of the cohorts we would confirm
in. "Externally defined" removes the circularity of learning cis weights from our
own confirmation cohort; it does **not** remove shared-population, shared-protocol
or shared-reference-annotation structure. A frozen external map could still
encode the same nuisance geometry and would then hand us a confident, wrong
answer with better provenance. The provenance-only selection criteria must
therefore be frozen before any overlap with our target genes is computed —
otherwise we spend the target to pick the answer key.

**What remains unknown:** whether any external cis map is genuinely independent
of all four confirmation cohorts; whether the anchor probe's nuisance class
corresponds to a defensible physical restriction; and whether a new synthetic
gate can pass at n=18 at all, given V54's `-0.0143`, V57's 192-seed `-0.0287`,
and the relational variants at `-0.176` and `-0.233`.
