# Part 3 prerequisite: authenticating the historical Layer-2 linear LODO baseline

**Date:** 2026-09-25
**Branch:** `part3/layer2-lodo-baseline-authentication-20260925`
**Executed from:** commit `e63b426116c7fcb5fc155c6f42c99b24a3c3b175`, clean worktree
**Receipt:** `results/PART3_LAYER2_LODO_BASELINE_AUTHENTICATION_RECEIPT.json`

---

## The verdict, in plain language

**Did it authenticate?  No.**
**`PENDING_PHYSICAL_INPUT_AUTHENTICATION`. The baseline was not replayed, and
no replayed number exists.**

This is a mixed result, and the mix matters.

**The bad news is narrow but real.** The three data files that the original
analysis actually read are gone. Not corrupted, not altered — simply not on this
machine, anywhere. Because they are gone, the historical LODO numbers cannot be
re-run today, and nothing can be verified about how they were computed beyond
what the recorded code says. They remain a *record* of a computation rather than
a *reproducible* computation.

**What this costs the project.** The Part 3 plan was to compare a trained JEPA
against a real, verified baseline rather than against numbers quoted from a
document. Right now that is not possible: the baseline is still only a quoted
number. It is a well-documented, internally consistent, cryptographically
sealed quoted number — but a quoted number nonetheless. Treating it as a
verified baseline would be exactly the substitution this exercise was designed
to prevent.

**And the news is worse than "the files were deleted":** the code that made those
files is also gone. `screen.py` and `rebuild.py`, named in the historical
`aud_hashes.json` as the producers of two of the three inputs, exist in neither
git history nor on disk. So the inputs cannot be rebuilt either. Recovering this
baseline means *finding the original files*, not re-deriving them.

**What is still fine — and it is a lot.**

- **The recorded numbers are authentic.** The committed `z_lodo.json` hashes
  byte-for-byte to the digest the historical closeout recorded for it. Nobody has
  edited the results after the fact. The three headline values in the task brief
  match the committed file exactly, to all 16 digits.
- **The code is authentic.** `z5_lodo.py` hashes to its recorded digest exactly.
  The script that is described is the script that is committed.
- **The branch is where it was said to be.** The live head of
  `analysis/v5-layer2-cross-view-shortcut-claude-20260915` is
  `219831b899b914984369c7a41828bf750554d1d9`, identical to the recorded head. No
  drift.
- **The upstream substrate survives intact.** All three large substrate files
  (`V0_full.npy`, `V1_full.npy`, `ASSEMBLY_SEEN_V5.npy`, 18.7 GB together) hash
  to their recorded digests exactly. The raw material is not lost.
- **Pathology-blindness held, then and now.** The historical analysis declared
  `NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`, `PROTECTED_DATA_CLOSED` and
  `TRAINING_OFF`; a scan of the replayed script finds no reference to
  `reader_validation`, `reader_oracle`, sealed holdout, Siletti, pathology,
  `D_shared`, AT8, Braak or CERAD. Nothing protected was opened in this
  work either.

**This was caught before any comparison was published, not after.** No result
rests on the assumption that this baseline was verified. The cost is schedule,
not retraction.

---

## What these numbers are — and what they are not

This framing is load-bearing. The three values are easy to misread as "how well
the project can predict disease," and they are nothing of the kind.

| source | donors | pooled LODO R² (full precision) |
|---|---|---|
| SEA-AD | 36 | 0.2410121580995348 |
| HVS | 41 | 0.04508741749145817 |
| NPH52 | 17 | 0.05462934735003744 |
| (pooled ALL) | 94 | 0.0687231474121911 |

**36 + 41 + 17 = 94, not 104.** This is a *selected* 94-donor population — the
`BASE_MECHANICS` stratum, 196,817 cells across 42 operators. It is not FULL104.

**The model is a straight line, not a JEPA.** The estimator is ridge regression
— a linear map with a small penalty, solved in closed form. There is no neural
network, no training, no representation learning. It is a deliberately simple
probe.

**The thing being predicted is not pathology.** The target is `p100_v1`: the
256-number "view 1" vector of the *same cell*, where the genes have been split
into two disjoint halves and each half summarised into 256 numbers. The model is
asked: *given half of this cell's molecular profile, can you reconstruct the
other half?* It is not asked anything about the donor's disease state. There is
no AT8, no Braak stage, no clinical outcome anywhere in this computation.

**The score is per-cell, not per-donor.** R² is pooled across all 256 output
numbers and all held-out *cells*. "Leave-one-donor-out" describes only how the
training set was built — every cell of one donor is withheld, and the whole
pipeline is refit from scratch. The quantity scored is still cell-level
reconstruction. The project's standing rule applies with full force here: many
cells sharpen the measurement of a donor, they do not multiply the donor sample
size.

**The numbers are unweighted, on a sample that is not uniform.** Cells entered by
an operator-stratified whole-block hash-rank sample, with per-cell inclusion
probability `q_i = min(12, B_o)/B_o` ranging from 0.0084 to 1.0 (median 0.41).
`z5_lodo.py` applies no weights. So these are *unweighted sample* quantities, not
FULL104 population quantities. This is known to matter on exactly this substrate:
the historical audits index records the molecular increment over context moving
from **+0.0311 unweighted to +0.1207 under empirical FULL104 weighting**. Reading
these R² values as population figures would be a real error, not a pedantic one.

**Do not pool.** SEA-AD alone is 0.2410; all 94 donors pooled is 0.0687. Pooling
across sources mixes in between-source mean structure. A single pooled headline
would misrepresent both.

**What the historical closeout actually concluded:** donor-generalisable linear
cross-view signal is *demonstrated* in SEA-AD at this model class, and *not
demonstrated* in HVS or NPH52. Not demonstrated is not the same as absent — a
simple probe failing shows only that this model class cannot reach the signal.

---

## Two identity rules that could not be checked

The project's hardest-won rule is that a cell's identity is `selection_row` and a
donor's is the donor ID string — never a storage position. `z5_lodo.py` takes
donor identity from `donor_code` inside `bind_population.npz` and cell selection
from `base_index` in the same file.

**That file is absent, so neither could be verified.** It is recorded in the
receipt as `UNVERIFIED`, not as assumed correct. Specifically unchecked:

1. whether `donor_code` is a one-to-one encoding of the donor ID *string* rather
   than a block or shard position;
2. whether `base_index` resolves cells by `selection_row` rather than block order.

If `donor_code` were not faithful to donor identity, leave-one-donor-out would
not actually hold a donor out, and the SEA-AD figure would be inflated — the
failure mode would make results look *better*, never worse, so nothing
downstream would flag it. Order-invariant summaries cannot detect it; only
checking the mapping against the physical source can. That check is waiting on
the same absent file.

---

## Why the inputs are gone: a structural finding

The original analysis read all of its inputs from a session scratchpad:

```
C:\Users\dushy\AppData\Local\Temp\claude\d--Jepa-project\cdf819f6-...\scratchpad
```

That is a temporary directory. The analysis was conducted carefully — the spec
was frozen before computation, a defective estimator was withdrawn and retained,
a null fixture validated the estimator, an independent reproduction agreed to
1e-14 — and then its inputs were left in a folder whose contents are not
preserved.

The project already has the rule that covers this: *nothing produced in a
scratchpad may be cited as evidence; if a number is going to be reported, its
producer belongs in the repository.* The consequence of the exception is now
concrete and measurable — a careful, well-sealed analysis that cannot be re-run.

The `LARGE_ARTIFACT_REFERENCES.json` policy statement says: *"Every committed
result is reproducible from these inputs using the committed scripts."* That
claim does not hold. The inputs are not committed and not preserved, and for two
of them the producing scripts are not committed either. A related claim — that
`bind_population.npz` is *"deterministically regenerable from
final_manifest.csv"* — is **undischarged**: no committed code anywhere writes
that file. Six committed scripts reference it across seven lines — `z1_repro.py`,
`z2_estimand.py`, `z3_donorrec.py`, `z5_lodo.py`, `z6_closeout.py` and
`z7_stage.py` — and every one of those references is a read. None creates it.

---

## Evidence

### Authenticated (digest matches the historical record exactly)

| artifact | SHA-256 | status |
|---|---|---|
| `scripts/z5_lodo.py` | `8b343279447d4c6d4122c7435bd808939e1a0f8bd11649f0f32e78599707ba7d` | MATCH |
| `results/z_lodo.json` | `277eab6e11fefa25d52cdb72522dbd8e29e3cc1602c4f1e3a85b117947f63fdb` | MATCH |
| `results/y_source.json` | `cfa899100411582db93a2586cfecb089c5852242c4abbb7203aad486b2a836d7` | MATCH |
| `V0_full.npy` (9,325,377,664 B) | `3b3f102c6767727ca4ab56832f8e70baf203676d6b65973c42903b22b6d56ada` | MATCH |
| `V1_full.npy` (9,325,377,664 B) | `c41df46d842d643f04566b8523a8aa711fa54bec1c836e0b394c0146017f231c` | MATCH |
| `ASSEMBLY_SEEN_V5.npy` | `0339d2e79599419f369d78cddf14448019f89476eb674000437b72a1b4fb640e` | MATCH |

Historical branch live head `219831b899b914984369c7a41828bf750554d1d9` — identical
to the recorded head.

### Not authenticated (absent — no digest could be computed)

| input | expected SHA-256 | expected size | found |
|---|---|---|---|
| `bind_population.npz` | `4488bcc0226826de332c0ee5c3504dfe6a2c22853de17dce7b366397c56c99be` | 5,118,788 B | **ABSENT** |
| `screen_out.npz` | `0fc144a82a6b1bd6d8bcf41c7a2443601203307535fdffd6f882a59343289ffa` | 1,403,900,426 B | **ABSENT** |
| `final_manifest.csv` | `c409cdf3b5579022936c52e3ba9aee0144a9a3a663588545607684301d517726` | 22,860,892 B | **ABSENT** |
| `y_source.json` (comparison print only) | `cfa899100411582db93a2586cfecb089c5852242c4abbb7203aad486b2a836d7` | — | **ABSENT** at the declared path |

Searches performed, and their exact scope:

| search | scope | result |
|---|---|---|
| all four input filenames | `D:\` and the full Claude temp tree, depth ≤ 6 | only `y_source.json`, inside the `/d/jepa_layer2_20260915` worktree |
| `bind_population*`, `screen_out*`, `final_manifest*` | `D:\`, depth ≤ 10 | no hits |
| `screen.py`, `rebuild.py` | `D:\` and Claude temp tree, depth ≤ 8 | no hits |
| producer filenames | entire git history, all refs | no hits |
| `bind_population*`, `screen_out*`, `final_manifest*` | unbounded full-depth scan of **all of `D:\` and `C:\Users`** (9.5 TB + 1.86 TB used) | **completed, exit 0, zero hits** |

The single hit anywhere was a committed copy of `y_source.json` — a *result*
file, not one of the three binary inputs — inside the `/d/jepa_layer2_20260915`
worktree. The declared scratchpad directory itself still exists and holds 146
entries from adjacent sessions; the four inputs are specifically not among them,
which is consistent with routine temp-directory cleanup of large files rather
than loss of the whole folder.

The unbounded scan has now completed with zero hits, so the absence is
established across both drives in their entirety rather than only within a
bounded search depth. The three inputs are not on this machine. That does not
close the recovery routes below — the files may exist on another machine, a
backup or a cloud volume — and the authenticator can be re-run against any
candidate with `--search-root`.

### Producers of the absent inputs

| script | recorded SHA-256 | produces | status |
|---|---|---|---|
| `screen.py` | `d0fe0ab135585586b27c2c23af0cacc0ea3380ccf3eb270a3c640f4c41976fd6` | `screen_out.npz` | **not in git, not on disk** |
| `rebuild.py` | `abe8ecff642af47e07e9657835a88d4ca0c90a0fe97de111f353ea4cf7e8297b` | `final_manifest.csv` | **not in git, not on disk** |

### Replayed values

`UNMEASURED`. The replay was refused, so there is no replayed R², and therefore
no delta against the historical values. The receipt records `UNMEASURED` rather
than an estimate; the deltas are unavailable, not zero.

---

## Environment

Python 3.9.7, numpy 1.24.2, pandas 1.5.3, Windows-10-10.0.26200-SP0.
Executor head `e63b426116c7fcb5fc155c6f42c99b24a3c3b175`, worktree clean at
execution time (`executor_status_clean: true` in the receipt).
Authenticator digest at execution:
`79cd45da435765958b33054bfdabfff04dd3b641529f70173aade1be6f56109d`.

---

## What a valid future comparison against a trained JEPA requires

So that the later comparison cannot be made against an incompatible baseline by
accident, all five must hold. These are also recorded machine-readably under
`valid_future_comparison_requirements` in the receipt.

1. **Same population.** The same 94 donors and the same 196,817 `BASE_MECHANICS`
   cells, keyed by donor ID string and `selection_row`. A JEPA evaluated on all
   104 donors is a different population. If the JEPA's population differs, the
   *baseline must be recomputed on the JEPA's population* — the existing number
   must not be quoted across.

2. **Same target.** Predict the 256-dimensional VALUE_ONLY view-1 vector of the
   same cell from view-0, operator-mean-centred, scored as pooled
   total-variance-explained R² over cells. A JEPA scored on a donor-level
   pathology outcome, on a `reader_fit` target, or at a different embedding
   dimensionality is measuring a different quantity and must not share a column
   with these values.

3. **Same held-out split.** Leave-one-donor-out with complete refit per held-out
   donor, *including* the operator means and the standardisation. A 5-fold donor
   split is not comparable. Normalisation statistics fitted across all donors are
   not comparable. Any JEPA whose pretraining saw cells from the held-out donor
   voids the comparison outright.

4. **Same weighting.** These are unweighted estimates on a probability sample
   with unequal inclusion probabilities. A population-weighted JEPA number is not
   comparable to them. Pick one convention and apply it to both sides.

5. **Report per source.** SEA-AD, HVS and NPH52 separately. Never a single pooled
   headline.

---

## What would unblock this

In order of preference:

1. **Locate the original three files** on another machine, backup or cloud
   volume, and re-run the authenticator with `--search-root` pointed at them. If
   any file's digest matches, it is the real artifact and the replay proceeds
   automatically. This is the only path that yields a replay of *the historical
   baseline itself*.

2. **Recover `screen.py` and `rebuild.py`** — from another machine or an agent
   transcript — and rebuild the frozen screen from the surviving, authenticated
   substrate. The rebuilt artifacts would then have to hash to the recorded
   digests to count; if they do not, the rebuild is a *new* baseline, not this
   one, and must be labelled as such.

3. **Accept that this baseline is unrecoverable and build a fresh one** from the
   authenticated substrate, prospectively, with its inputs committed or stored
   under a permanent path. This is honest and buildable, but it produces a new
   baseline that cannot inherit the historical numbers' authority — and the new
   one must be constructed before any JEPA result is seen, not after.

**Until one of these completes, the historical R² values should be cited as a
documented prior result with the population and target caveats attached — never
presented as a verified baseline a trained JEPA has been measured against.**

---

## Classification against the historical audits index

Per `START_HERE.md`, work is classified before computing.

- The **scientific result** — full-refit source-specific LODO, SEA-AD ≈ 0.241,
  HVS ≈ 0.045, NPH52 ≈ 0.055 — is `ALREADY_AUDITED`
  (`JEPA_HISTORICAL_AUDITS_INDEX_20260915.md`, line 66). It was not recomputed,
  and this document does not compete with it.
- The **physical-input authentication and replay** of that result is `OPEN`. It
  had never been attempted, and it is the only new computation performed here.

---

## A note on the test suite

`tests/test_auth_z5_lodo.py` (19 tests, all passing) is adversarial rather than
confirmatory. A refusal is easy to produce by accident — a typo in a path would
produce one — so each test drives a mechanism to the outcome *opposite* to the
one observed: a decoy file of exactly the declared byte length must still be
rejected, a file whose bytes genuinely match must report MATCH, a planted
protected-artifact name must fire the pathology-blindness scanner, and the
producer search must find `z5_lodo.py` in git history and a decoy on disk. Only
because those positive controls fire does "ABSENT" and
"NOT_IN_GIT_AND_NOT_ON_DISK" count as measurements rather than stuck outputs.

The suite earned its keep immediately: it caught a real defect in the replay
path. `repoint()` passed the new input directory to `re.subn` as a string
replacement, where backslashes are read as regex escapes. Since the scratchpad
path is a Windows path, every realistic replay would have failed on
`bad escape \s`, or silently rewritten the path at a `\U` segment. A confirmatory
suite run against the current absent inputs would never have reached that code
path, and the bug would have surfaced only once the files were finally recovered
and the replay mattered most.
