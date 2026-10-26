"""Task7 fixture-only TARGET=NONE artifact; production issuance deliberately closed.

Task3 has no active same-code-path/known-truth producer qualification. This
module cannot sign an authenticated target, issue a selected TargetPortfolio or
prove independent parent issuer custody. It is a content-addressed DEVELOPMENT
fixture demonstrating fail-closed NONE handling, nothing more.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Callable
from scripts.v5.td_unified.canonical_v1 import canonical_sha256, CanonicalError


class TargetBundleError(ValueError):
    pass


_ROLES = {
    "manifest_sha256": ("FIXTURE_MANIFEST", "reader_partition", "reader_fit"),
    "registry_sha256": ("FIXTURE_REGISTRY", "status", "NO_QUALIFIED_TARGETS"),
    "controller_sha256": ("FIXTURE_CONTROLLER", "status", "NO_DECISION_PROMOTION"),
    "negative_evidence_sha256": ("FIXTURE_FALSIFIER", "failed_or_unresolved", None),
}
_OBLIGATIONS = [
    "NORMALIZATION_QUERY_HIDDEN_TOTAL_LEAKAGE",
    "DONOR_SOURCE_OPERATOR_LEAKAGE",
    "WRONG_CELL_PAIRING",
    "FAKE_RICH_TEACHER",
    "TEACHER_STUDENT_ORACLE_CONFUSION",
    "EVIDENCE_STARVATION_OR_THINNING",
    "TARGET_SEMANTICS_AND_SUPPORT_DRIFT",
    "SUBSPACE_VS_AXIS_STABILITY",
    "UNAUTHORIZED_SUPPORT_WIDENING",
    "BAYESIAN_RBB_GRADIENT_INTERFERENCE_PRIOR",
]
_BUNDLE_KEYS = frozenset({
    "schema","target_selection","scope","qualification_stage",
    "manifest_sha256","registry_sha256","controller_sha256",
    "negative_evidence_sha256","negative_obligations",
    "failure_semantics","target_semantics","selected_support",
    "externally_authenticated","real_reference_ready",
    "same_code_path_qualified","training_authorized",
    "authority_effect","target_bundle_sha256",
})


def _sha(value):
    return type(value) is str and len(value)==64 and all(c in "0123456789abcdef" for c in value)


def _resolve_parents(claims: dict[str, str], resolver: Callable):
    if not callable(resolver):
        raise TargetBundleError("fixture parent resolver is mandatory")
    for field,(role,property_name,expected) in _ROLES.items():
        digest=claims[field]
        if not _sha(digest):
            raise TargetBundleError("invalid exact parent digest for "+field)
        try:
            resolved=resolver(digest)
        except Exception as exc:
            raise TargetBundleError("failed to resolve exact "+field+" parent") from exc
        if type(resolved) is not dict or type(resolved.get("object_role")) is not str:
            raise TargetBundleError("parent must be a precisely typed fixture object")
        try:
            if canonical_sha256(resolved)!=digest:
                raise TargetBundleError("resolved parent bytes differ from pinned digest")
        except (CanonicalError,ValueError,TypeError) as exc:
            raise TargetBundleError("cannot verify parent canonical identity") from exc
        if resolved.get("object_role")!=role or property_name not in resolved:
            raise TargetBundleError("parent role/content does not match closed fixture contract")
        if expected is not None and (
            type(resolved[property_name]) is not str or resolved[property_name]!=expected
        ):
            raise TargetBundleError("parent holds unsupported role-specific fixture claim")
        if field=="negative_evidence_sha256":
            unresolved=resolved[property_name]
            if (type(unresolved) is not list or not unresolved
                or any(type(x) is not str or not x for x in unresolved)
                or len(set(unresolved))!=len(unresolved)):
                raise TargetBundleError("NONE requires explicit unresolved/failed falsifier evidence")


def issue_target_none_fixture(*, manifest_sha256: str, registry_sha256: str,
                              controller_sha256: str, falsifier_sha256: str,
                              resolver: Callable) -> dict:
    """Issue only non-authorizing NONE; never allow caller-defined PASS."""
    claims={
        "manifest_sha256":manifest_sha256,
        "registry_sha256":registry_sha256,
        "controller_sha256":controller_sha256,
        "negative_evidence_sha256":falsifier_sha256,
    }
    _resolve_parents(claims,resolver)
    body={
        "schema":"TARGET_QUALIFICATION_BUNDLE_V1",
        "target_selection":"NONE",
        "scope":"DEVELOPMENT_FIXTURE_ONLY",
        "qualification_stage":"SEMANTICS_ONLY",
        **claims,
        "negative_obligations":list(_OBLIGATIONS),
        "failure_semantics":"NO_BIOLOGICALLY_QUALIFIED_TARGET",
        "target_semantics":None,
        "selected_support":None,
        "externally_authenticated":False,
        "real_reference_ready":False,
        "same_code_path_qualified":False,
        "training_authorized":False,
        "authority_effect":"NONE",
    }
    body["target_bundle_sha256"]=canonical_sha256(body)
    return deepcopy(body)


def verify_target_none_fixture(bundle: dict, resolver: Callable) -> dict:
    """Revalidate full content and parent bytes on every consumption."""
    if type(bundle) is not dict or set(bundle)!=_BUNDLE_KEYS:
        raise TargetBundleError("TARGET NONE bundle is not an exact canonical fixture object")
    expected={
        "schema":"TARGET_QUALIFICATION_BUNDLE_V1",
        "target_selection":"NONE",
        "scope":"DEVELOPMENT_FIXTURE_ONLY",
        "qualification_stage":"SEMANTICS_ONLY",
        "negative_obligations":_OBLIGATIONS,
        "failure_semantics":"NO_BIOLOGICALLY_QUALIFIED_TARGET",
        "target_semantics":None,
        "selected_support":None,
        "externally_authenticated":False,
        "real_reference_ready":False,
        "same_code_path_qualified":False,
        "training_authorized":False,
        "authority_effect":"NONE",
    }
    for k,value in expected.items():
        if type(bundle[k]) is not type(value) or bundle[k]!=value:
            raise TargetBundleError("fixture NONE assertion moved or claimed authority: "+k)
    claims={k:bundle[k] for k in _ROLES}
    _resolve_parents(claims,resolver)
    sha=bundle["target_bundle_sha256"]
    if not _sha(sha):
        raise TargetBundleError("bundle digest malformed")
    try:
        observed=canonical_sha256({k:v for k,v in bundle.items() if k!="target_bundle_sha256"})
    except (CanonicalError,TypeError,ValueError) as exc:
        raise TargetBundleError("noncanonical bundle input") from exc
    if observed!=sha:
        raise TargetBundleError("bundle changed after issuance or digest forged")
    return deepcopy(bundle)


def issue_selected_target_bundle(**kwargs):
    """Explicit STOP: Stage7 selected target authority needs independent inputs.

    Do not build a simulated 'selected' bundle with caller-declared PASS,
    purported independent human credentials, or fixture-only G7 scores.
    """
    raise TargetBundleError(
        "selected target issuance unavailable until accepted Task4 custody, "
        "Task5 genuine A7, independently qualified gates, source/actor "
        "identity resolver and target selection receipts are integrated"
    )
