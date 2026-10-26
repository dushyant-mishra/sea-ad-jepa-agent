"""Task8 exact-consumption rehearsal for first-class NONE (no target).

This is *not* a full DOWNSTREAM_CERTIFIED receipt; Task8 selected-target and
human execution cannot be certified until real Task7 verified target objects,
Task4 custody and exact Task5 same-code-path evidence exist.
"""
from __future__ import annotations
from scripts.v5.td_unified.canonical_v1 import canonical_sha256
from scripts.v5.td_unified.target_bundle_v1 import (
    TargetBundleError, verify_target_none_fixture
)


class DownstreamContractError(ValueError):
    pass


def certify_downstream_abstention(
    bundle, *, resolver,
    teacher_executed=False, student_executed=False,
    optimizer_steps=0, ema_updates=0, selected_candidate=None,
    downstream_obligation_receipts=None
):
    """Prove a fixture correctly *abstained*, never that biology qualified."""
    if (type(teacher_executed) is not bool or teacher_executed
        or type(student_executed) is not bool or student_executed
        or type(optimizer_steps) is not int or optimizer_steps != 0
        or type(ema_updates) is not int or ema_updates != 0
        or selected_candidate is not None
        or downstream_obligation_receipts is not None):
        raise DownstreamContractError("TARGET NONE refuses downstream execution, forged tests or optimization")
    try:
        checked=verify_target_none_fixture(bundle,resolver)
    except TargetBundleError as exc:
        raise DownstreamContractError("unverified exact target bundle refused") from exc
    body={
        "schema":"DOWNSTREAM_CERTIFICATION_RECEIPT_V1",
        "status":"NO_TARGET__DOWNSTREAM_ABSTAIN",
        "target_bundle_sha256":checked["target_bundle_sha256"],
        "manifest_sha256":checked["manifest_sha256"],
        "registry_sha256":checked["registry_sha256"],
        "negative_evidence_sha256":checked["negative_evidence_sha256"],
        "inherited_negative_obligations":checked["negative_obligations"],
        "selected_target":None,
        "teacher_constructed":False,
        "student_constructed":False,
        "teacher_executed":False,
        "student_executed":False,
        "optimizer_steps":0,
        "ema_updates":0,
        "downstream_certified":False,
        "real_data_authorized":False,
        "training_authorized":False,
        "authority_effect":"NONE",
    }
    body["receipt_sha256"]=canonical_sha256(body)
    return body


def certify_downstream_consumption(*args, **kwargs):
    """Production-selected target remains completely fail-closed."""
    raise DownstreamContractError(
        "selected downstream consumption cannot be certified without a verified "
        "independently issued real Task7 bundle, active Task4/5 execution custody "
        "and complete inherited obligation receipts"
    )
