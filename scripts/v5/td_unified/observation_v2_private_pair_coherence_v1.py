"""Private actor-only V2 student/teacher coherence preflight (fixture mechanics).

A bounded snapshot of two separately issued V2 D1 content views is checked for
one frozen query/rights roster and compatible physical observation states.
The result contains NO teacher bytes, digest, query count, row count or
per-cell fields. A private reviewer may use the function, but its receipt
must not be mistaken for source attestation, real G7 E3, or training authority.

This is NOT a G7 content law. In particular V1/G7 physical `library_size`
cannot be replaced with D1 `base_rights_normalization_depth`.
"""
from __future__ import annotations

from scripts.v5.td_unified import observation_normalization_view_v2_fixture as LEGACY
from scripts.v5.td_unified import observation_normalization_view_v2_bound_content_v1 as BOUND
from scripts.v5.td_unified.q_excluded_depth_v1 import (
    MEASURED_SCALAR, WITHHELD_BY_EVIDENCE_RIGHTS, QExcludedObservationError,
)

_STATE_WITHOUT_SCALAR = frozenset({
    "STRUCTURALLY_UNMEASURED", "MEASURED_COLLISION_UNRESOLVED",
})


def validate_private_v2_pair_coherence(*, student_view, teacher_view):
    """Compare only views already issued by the same cooperative fixture scope.

    A malicious same-process actor can alter the in-memory rights registry.
    Matching views cannot prove one physical nucleus, source feature mapping,
    donor independence, operator/QC noninterference, or a trusted external
    issuer. Do not expose the teacher view/digest even if this check passes.
    """
    # Snapshot BOTH before validation; caller mutations after this point do
    # not affect this transaction. Exact built-ins prevent payload dispatch.
    student, teacher = LEGACY._view_snapshot([student_view, teacher_view])
    if type(student) is not dict or type(teacher) is not dict:
        raise QExcludedObservationError("private V2 pair requires two exact views")
    if (student.get("view_kind") != LEGACY._STUDENT or
            teacher.get("view_kind") != LEGACY._TEACHER):
        raise QExcludedObservationError("private V2 pair role routing differs")
    student_receipt = BOUND.validate_fixture_observation_view_v2_bound(student)
    teacher_receipt = BOUND.validate_fixture_observation_view_v2_bound(teacher)
    if (student_receipt["status"] != BOUND._STATUS or
            teacher_receipt["status"] != BOUND._STATUS):
        raise QExcludedObservationError("private V2 pair lacks bound content")
    # Policy is private to cooperative issuer: neither the student nor its
    # consumer receives the teacher's digest or a source/teacher commitment.
    with BOUND._VIEW_BINDINGS_LOCK:
        student_binding = BOUND._VIEW_BINDINGS.get(student["observable_sha256"])
        teacher_binding = BOUND._VIEW_BINDINGS.get(teacher["observable_sha256"])
    if student_binding is None or teacher_binding is None:
        raise QExcludedObservationError("private pair source binding is absent")
    (sq, sr, srights, sbase, sselected) = student_binding
    (tq, tr, trights, tbase, tselected) = teacher_binding
    if (sq != tq or sq != student["query_address_id"] or
            tq != teacher["query_address_id"] or
            sr != LEGACY._STUDENT or tr != LEGACY._TEACHER or
            srights != trights or sbase != tbase or
            frozenset(sselected) != frozenset(sbase) or
            not frozenset(tselected).issuperset(dict(srights).values())):
        raise QExcludedObservationError("private pair frozen rights/query differs")
    def roster(rows):
        result = {}
        for row in rows:
            key = (row["cell_id"], row["address_id"])
            if key in result:
                raise QExcludedObservationError("private pair duplicate cell/address")
            result[key] = row
        return result

    left, right = roster(student["rows"]), roster(teacher["rows"])
    if set(left) != set(right):
        raise QExcludedObservationError("private pair cell/address coverage differs")
    for key in left:
        s, t = left[key], right[key]
        for name in ("cell_id", "donor_id", "source_id", "operator_id",
                     "address_id", "evidence_right"):
            if s[name] != t[name]:
                raise QExcludedObservationError("private pair immutable row identity differs")
        if s["state"] == MEASURED_SCALAR:
            if (t["state"] != MEASURED_SCALAR or t["count"] != s["count"] or
                    t["base_rights_normalization_depth"] != s["base_rights_normalization_depth"]):
                raise QExcludedObservationError("private pair base scalar or D1 differs")
        elif s["state"] == WITHHELD_BY_EVIDENCE_RIGHTS:
            if (t["state"] != MEASURED_SCALAR or
                    s["count"] is not None or
                    s["base_rights_normalization_depth"] is not None):
                raise QExcludedObservationError("private pair non-base scalar states differ")
        elif s["state"] in _STATE_WITHOUT_SCALAR:
            if (t["state"] != s["state"] or t["count"] is not None or
                    t["base_rights_normalization_depth"] is not None):
                raise QExcludedObservationError("private pair structural states differ")
        else:
            raise QExcludedObservationError("private pair state is outside frozen contract")
    # The receipt intentionally has no student digest either: a constant
    # result must be invariant when only the teacher's withheld values move.
    return {
        "schema": "JEPA_TD_V2_PRIVATE_PAIR_COHERENCE_FIXTURE_V1",
        "status": "PAIR_COHERENCE_VERIFIED_FIXTURE_ONLY",
        "external_source_authenticated": False,
        "physical_measurement_identity_authenticated": False,
        "donor_specimen_identity_authenticated": False,
        "feature_alias_closure_authenticated": False,
        "q_independent_qc_selection_authenticated": False,
        "q_rights_issuer_authenticated": False,
        "reference_truth_authenticated": False,
        "g7_content_v2_authorized": False,
        "same_code_path_authorized": False,
        "real_training_authorized": False,
        "authority_effect": "NONE",
    }
