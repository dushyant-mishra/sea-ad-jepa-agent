#!/usr/bin/env python3
"""T0 V20 replay-equivalence policy V2 — one field moved, nothing else.

Frozen by the owner in `T0_V20_REPLAY_EQUIVALENCE_POLICY_V2.md` as a correction
to an internally inconsistent classification, not as permission to tune
tolerances until a replay passes. The single change from V1:

    final_trace_scale:  exact scalar  ->  at most 1 float64 ULP

The basis is algebraic rather than empirical. Frozen
`t0_target_learner_v1.py:68-71` computes `s = trace(gram)/n` and
`lam = 10**exponent * s`, serialised as `final_trace_scale` and `final_lambda`.
V1 already permits its derived child one ULP while requiring the parent be
exact, and under the frozen exponent 2.0 the child is just the parent times
100.0 — so no drifting stack could ever satisfy both. V2 assigns the parent the
same one-ULP class its child already had. It does not widen that class, and it
introduces no caller-configurable or result-dependent tolerance.

V1 is not edited, superseded in place, or imported for its constants alone. It
remains the default policy everywhere, its STOP artifact stands, and this module
is a second identity that a caller must ask for by name.

How the comparison logic is shared. V1's comparison functions read their policy
from module-level constants, so rather than retype them here — which would put a
transcription risk inside the thing being versioned — their sources are exec'd
verbatim into a namespace where only those four constants differ. That is the
same technique the R8 verifiers and the state-adjudicator repair already use.
Nothing on V1 is rebound.

`verify_single_policy_change` is the part worth reading. It proves the derivation
is the one change the owner authorized: every other policy element identical,
the field present in exactly one class before and after, and the set of
classified fields unchanged, so the field was moved rather than dropped,
duplicated, or quietly given a second rule.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import t0_replay_equivalence_v1 as v1

# Re-exported so callers catching the V1 error type still catch these.
ReplayEquivalenceError = v1.ReplayEquivalenceError

POLICY_IDENTITY = "JEPA_T0_V20_REPLAY_EQUIVALENCE_POLICY_V2"
POLICY_DOCUMENT = "docs/agent/T0_V20_REPLAY_EQUIVALENCE_POLICY_V2.md"

# The one authorized change, named so the verification can check it by name
# rather than by trusting the constants below.
MOVED_FIELD = "final_trace_scale"
MOVED_TO_MAX_ULP = 1

# --- the V2 policy, derived from V1 ---------------------------------------
FLOAT_POLICY = {field: dict(policy) for field, policy in v1.FLOAT_POLICY.items()}
ULP_POLICY = {**v1.ULP_POLICY, MOVED_FIELD: MOVED_TO_MAX_ULP}
EXACT_ARRAY_FIELDS = tuple(v1.EXACT_ARRAY_FIELDS)
EXACT_SCALAR_FIELDS = tuple(f for f in v1.EXACT_SCALAR_FIELDS
                            if f != MOVED_FIELD)

# Inherited from V1 unchanged; named here so the report can state them.
REQUIRED_FLOAT_DTYPE = v1.REQUIRED_FLOAT_DTYPE
STATE_PRIMARY_FLOAT_RTOL = v1.STATE_PRIMARY_FLOAT_RTOL
STATE_PRIMARY_FLOAT_ATOL = v1.STATE_PRIMARY_FLOAT_ATOL
STATE_PRIMARY_FLOAT_FIELDS = tuple(v1.STATE_PRIMARY_FLOAT_FIELDS)
STATE_PRIMARY_EXACT_FIELDS = tuple(v1.STATE_PRIMARY_EXACT_FIELDS)


def _classified(float_policy: Any, ulp_policy: Any, exact_arrays: Any,
                exact_scalars: Any) -> dict[str, str]:
    """Which rule class each field sits in, so a move can be checked."""
    classes: dict[str, str] = {}
    duplicated: list[str] = []
    for name, fields in (("tolerant_array", float_policy),
                         ("at_most_n_ulp", ulp_policy),
                         ("exact_array", exact_arrays),
                         ("exact_scalar", exact_scalars)):
        for field in fields:
            if field in classes:
                duplicated.append(field)
            classes[field] = name
    if duplicated:
        raise ReplayEquivalenceError(
            "T0 replay-equivalence policy V2: field in more than one rule "
            "class: %r" % sorted(set(duplicated)))
    return classes


def policy_digest() -> str:
    """A digest over the V2 policy, so a run record can bind its tolerances."""
    canonical = json.dumps({
        "identity": POLICY_IDENTITY,
        "float_policy": FLOAT_POLICY,
        "ulp_policy": ULP_POLICY,
        "exact_array_fields": list(EXACT_ARRAY_FIELDS),
        "exact_scalar_fields": list(EXACT_SCALAR_FIELDS),
        "required_float_dtype": str(REQUIRED_FLOAT_DTYPE),
        "state_primary_float_rtol": STATE_PRIMARY_FLOAT_RTOL,
        "state_primary_float_atol": STATE_PRIMARY_FLOAT_ATOL,
        "state_primary_float_fields": list(STATE_PRIMARY_FLOAT_FIELDS),
        "state_primary_exact_fields": list(STATE_PRIMARY_EXACT_FIELDS),
    }, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def verify_single_policy_change() -> dict[str, Any]:
    """Prove V2 differs from V1 by exactly the authorized move.

    Checked rather than asserted in prose, because a policy module that had
    quietly acquired a second change would still run and would still produce a
    report that looked like an authorized one.
    """
    problems: list[str] = []

    if FLOAT_POLICY != v1.FLOAT_POLICY:
        problems.append("float policy changed")
    if tuple(EXACT_ARRAY_FIELDS) != tuple(v1.EXACT_ARRAY_FIELDS):
        problems.append("exact array fields changed")
    for name, mine, theirs in (
            ("required_float_dtype", REQUIRED_FLOAT_DTYPE,
             v1.REQUIRED_FLOAT_DTYPE),
            ("state_primary_float_rtol", STATE_PRIMARY_FLOAT_RTOL,
             v1.STATE_PRIMARY_FLOAT_RTOL),
            ("state_primary_float_atol", STATE_PRIMARY_FLOAT_ATOL,
             v1.STATE_PRIMARY_FLOAT_ATOL),
            ("state_primary_float_fields", tuple(STATE_PRIMARY_FLOAT_FIELDS),
             tuple(v1.STATE_PRIMARY_FLOAT_FIELDS)),
            ("state_primary_exact_fields", tuple(STATE_PRIMARY_EXACT_FIELDS),
             tuple(v1.STATE_PRIMARY_EXACT_FIELDS))):
        if mine != theirs:
            problems.append("%s changed" % name)

    # The move itself: out of exact-scalar, into the one-ULP class, at 1.
    if MOVED_FIELD not in v1.EXACT_SCALAR_FIELDS:
        problems.append("%s was not an exact scalar in V1" % MOVED_FIELD)
    if MOVED_FIELD in v1.ULP_POLICY:
        problems.append("%s already had a ULP budget in V1" % MOVED_FIELD)
    if MOVED_FIELD in EXACT_SCALAR_FIELDS:
        problems.append("%s is still an exact scalar in V2" % MOVED_FIELD)
    if ULP_POLICY.get(MOVED_FIELD) != MOVED_TO_MAX_ULP:
        problems.append("%s does not carry max_ulp %d in V2"
                        % (MOVED_FIELD, MOVED_TO_MAX_ULP))

    # Nothing else moved between the two mutable classes.
    if set(ULP_POLICY) - set(v1.ULP_POLICY) != {MOVED_FIELD}:
        problems.append("more than one field gained a ULP budget")
    if set(v1.ULP_POLICY) - set(ULP_POLICY):
        problems.append("a field lost its ULP budget")
    if set(v1.EXACT_SCALAR_FIELDS) - set(EXACT_SCALAR_FIELDS) != {MOVED_FIELD}:
        problems.append("more than one field left the exact-scalar class")
    if set(EXACT_SCALAR_FIELDS) - set(v1.EXACT_SCALAR_FIELDS):
        problems.append("a field entered the exact-scalar class")
    for field, budget in v1.ULP_POLICY.items():
        if ULP_POLICY[field] != budget:
            problems.append("the ULP budget for %s changed" % field)

    # Moved, not dropped: every field the V1 policy covered is still covered.
    before = _classified(v1.FLOAT_POLICY, v1.ULP_POLICY,
                         v1.EXACT_ARRAY_FIELDS, v1.EXACT_SCALAR_FIELDS)
    after = _classified(FLOAT_POLICY, ULP_POLICY, EXACT_ARRAY_FIELDS,
                        EXACT_SCALAR_FIELDS)
    if set(before) != set(after):
        problems.append("the set of classified fields changed")
    reclassified = sorted(f for f in before
                          if f in after and before[f] != after[f])
    if reclassified != [MOVED_FIELD]:
        problems.append("reclassified fields are %r, expected exactly [%r]"
                        % (reclassified, MOVED_FIELD))

    if problems:
        raise ReplayEquivalenceError(
            "T0 replay-equivalence policy V2 is not the authorized single "
            "change: " + "; ".join(problems))

    return {
        "policy_identity": POLICY_IDENTITY,
        "policy_document": POLICY_DOCUMENT,
        "parent_policy": "JEPA_T0_V20_TARGET_REPLAY_EQUIVALENCE_V1",
        "authorized_change_count": 1,
        "authorized_change": {
            "field": MOVED_FIELD,
            "from": "exact_scalar",
            "to": "at_most_n_ulp",
            "max_ulp": MOVED_TO_MAX_ULP,
        },
        "reclassified_fields": reclassified,
        "every_other_policy_element_identical_to_v1": True,
        "classified_field_set_unchanged": True,
        "policy_sha256": policy_digest(),
    }


# --- V1's comparison logic, under the V2 policy ----------------------------
# Sources are exec'd verbatim into a namespace where only the four policy
# constants differ, so the logic is not retyped and V1 is not rebound.
_SHARED = ("compare_fit_equivalence", "full_fit_equivalence_report",
           "verify_target_v2_replay_equivalent", "compare_decision_equivalence")

_NAMESPACE: dict[str, Any] = dict(v1.__dict__)
_NAMESPACE.update(
    FLOAT_POLICY=FLOAT_POLICY,
    ULP_POLICY=ULP_POLICY,
    EXACT_ARRAY_FIELDS=EXACT_ARRAY_FIELDS,
    EXACT_SCALAR_FIELDS=EXACT_SCALAR_FIELDS,
)


def _install_shared_logic() -> None:
    verify_single_policy_change()
    for name in _SHARED:
        source = inspect.getsource(getattr(v1, name))
        exec(compile(source, "<replay-equivalence-v2:%s>" % name, "exec"),
             _NAMESPACE)
        globals()[name] = _NAMESPACE[name]


_install_shared_logic()
