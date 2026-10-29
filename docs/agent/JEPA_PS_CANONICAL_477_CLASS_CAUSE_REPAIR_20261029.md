# Production-synthetic canonical #477 class/cause boundary repair — 2026-10-29

**Scope:** synthetic encoding mechanics only. No external T2-D scan issuer or authenticated data.

Original code: PR #477 `c83088de090bc4f2fc6bbee353c46070bcca7be5`.
Independent review: Macha #483 `48ec018735a095571a0bfaa25b33f9b9deb40b39`.
Reviewer test file preserved without edits, Git blob `f2d10a8c4ea3620c3f46f7d6b208c07279027d56`.

Changes:
- `semantic_sha256` uses exact `type(x) is ...` membership for byte-like rejection, not `isinstance` that may read an adversarial payload `__class__`.
- `_iter_rows` checks `type(rows)` and rejects list/tuple subclasses without invoking the payload instance's `__class__`; ordinary non-container iterables remain permitted for this *existing* interface.
- Caught `TypeError` from obtaining a row iterator is raised as a static `CanonicalError` `from None`, suppressing payload `__cause__` formatting.

Unresolved: the existing live-generator interface deliberately invokes producer code during iteration, and non-TypeError exceptions during later iteration can still escape. This repair **does not** declare generator-supplied observations secure from hostile code. Decide a separately versioned immutable row-snapshot boundary if adversarial/production custody is required; do not silently reject existing legitimate producer streams.

Original Macha #483 suite remains unchanged; new hosted workflow evaluates it against NumPy 1.26 and 2.x on Linux and Windows. Earlier platform fixes remain subject to independent review. T2-D external scan issuer stays RED and outside this patch.

**Authority:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
