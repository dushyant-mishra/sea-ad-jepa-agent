# F1-A Data-Only Closure Design — 2026-09-07

Status: `DESIGN_ONLY__NOT_EXECUTED__REAL_F1_STILL_UNAUTHORIZED`

## The problem this exists to prevent

The producer and replay must be byte-frozen *before* any real output exists,
otherwise their source could be adjusted after seeing outcomes. But the frozen
result package must eventually name the real capture, replay and effect-row
roots — values that cannot be known until the sweep has run.

Editing the producer afterwards to paste those hashes in would destroy the
freeze. The whole point of freezing source before results is lost the moment the
source is touched once results exist.

So the binding has to happen in **data**, never in source.

## Rule

After the sweep, no `.py` file under `scripts/v4/` that participated in
producing or verifying the result may change. Not a docstring, not a constant,
not a comment. The frozen digests in the pre-freeze manifest must still verify
byte-for-byte against the same files after closure as before it.

Closure adds files. It never edits them.

## Mechanism

Closure writes exactly one new artifact:

```
outputs/f1_real_producer_replay_closure_<date>/F1_REAL_CLOSURE_BINDING.json
```

containing, and containing only, values that were unknowable before execution:

- `capture_root_sha256`
- `shard_set_root_sha256`
- `effect_row_root_sha256`
- the ordered shard id list and its root
- the ordered forward identity list root
- the ordered effect-row id list root
- the environment record actually observed
- the pre-freeze manifest root it closes over

Plus a back-reference to the frozen source digests, restated so that any later
drift is detectable from the closure file alone.

The producer reads this file at run time when authorized. It does not embed the
values. `FROZEN_REAL_CAPTURE_ROOT_SHA256` and its two siblings stay `None` in
source permanently; the authorized path resolves them from the closure artifact
and fails closed if the artifact is absent, malformed, or closes over a
different pre-freeze manifest root.

## Ordering, which is the part that is easy to get wrong

1. Freeze producer, replay and tests. Record their digests. **This step is
   complete and is the present commit.**
2. Obtain explicit real-execution authorization. Not granted.
3. Run the sweep. Source is now immutable.
4. Compute the three roots from the produced bytes.
5. Write the closure artifact. Source still untouched.
6. Re-verify every pre-freeze source digest. If any changed, the result is
   invalid regardless of its content.
7. Package result plus closure plus the unchanged pre-freeze manifest, and
   submit for external review.

Step 6 is the load-bearing one. It is what makes step 3 trustworthy in
retrospect, and it must be run by the reviewer rather than reported by the
producing lane.

## Why the roots are not simply appended to the existing manifest

The pre-freeze manifest is an authority about source. Adding result values to it
would make it change after outcomes exist, and a reviewer could no longer
distinguish "this manifest described the frozen source" from "this manifest was
rewritten once the answer was known". Two artifacts with one directional
reference is the only arrangement where staleness is visible.

This project has already rejected two packages for a related failure — a
manifest describing bytes it no longer matched, and a document embedding its own
package root so that stating the root changed the root. The same shape applies
here: a closure artifact must never be a member of the manifest it closes over.

## Interrupted execution

Resume is by physical shard existence, already exercised in the frozen suite. A
resumed run reuses committed shards rather than rewriting them, and the ordered
payload digests and identity root must be identical to an uninterrupted run.
Closure therefore does not care whether the sweep was interrupted, only that the
final shard set verifies. That property is tested before freeze, not asserted
after capture.

## What closure explicitly may not do

Populate a root that was not computed from produced bytes. Bind a result to a
different pre-freeze manifest root than the one the source was frozen under.
Relax the execution gate. Change the accepted mechanics, the geometry, the
authority set, or any F1-A scientific rule. Grant access to
reader-validation, reader-oracle, DEV, SEALED, foundation sealed-holdout or
pathology.

A closure step that needed any of those would be evidence that the freeze was
premature, and the correct response is a new prospective pre-freeze generation,
not an edit.
