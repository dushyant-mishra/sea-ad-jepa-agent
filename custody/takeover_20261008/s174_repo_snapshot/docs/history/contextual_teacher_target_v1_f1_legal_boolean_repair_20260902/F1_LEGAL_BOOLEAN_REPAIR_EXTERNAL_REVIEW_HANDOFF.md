# F1 strict legal/provenance Boolean repair — external review handoff

Terminal sought: `PASS_F1_LEGAL_BOOLEAN_REPAIR_AWAITING_EXTERNAL_REVIEW`.

The pre-edit v4 source reproduced the fail-open: truthy strings, integer `1`, and `[1]` could satisfy legal provenance. The repaired decision boundary requires `type(payload["legal"]) is bool` and passes the gate only for `payload["legal"] is True`. Integration independently requires the same exact built-in type and forwards the value without coercion.

Built-in `True` remains the sole passing value. Built-in `False` remains a valid value that fails the legal gate. Strings, integers, containers, `None`, and both NumPy Boolean scalars reject before decision arithmetic.

The truth-table SHA and all fourteen prior decision fixtures are unchanged; regenerated regression artifacts are byte-identical. Population omission/relabel and QID-domain attacks remain passing. Forward and nuisance authority roots remain unset. No expression, candidate outcomes, training, or EMA were accessed.

The prior truth-table package is historical and intentionally retains its pre-repair source hashes. This new package—not the old root—binds the repaired sources.
