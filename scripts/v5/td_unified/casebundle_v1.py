"""Task 5 prospective fixture-only CaseBundle / TruthBundle boundary.

Implements a deliberately limited scientific-shape preflight under the Task3
freeze. This is *not* Task4-sealed custody, a protected-data reader, human
population authority, or authenticated truth issuance. A full Task5
implementation must later bind Task2 population raw bytes and Task4 challenge
commitments. No real or sealed case is admitted here.
"""
from __future__ import annotations
from copy import deepcopy
from collections.abc import Mapping

from scripts.v5.td_unified.canonical_v1 import canonical_sha256, CanonicalError


class CaseBundleError(ValueError):
    """Fixture is malformed or attempts to cross the truth/access boundary."""


_SCHEMA = "KNOWN_TRUTH_CASEBUNDLE_V1"
_TRUTH_SCHEMA = "TRUTH_BUNDLE_V1"
_FIELDS = frozenset({
    "schema", "case_id", "authority_scope", "manifest_sha256",
    "population_access_policy_sha256", "address_universe_sha256",
    "reader_partition", "observations",
})
_ROW_FIELDS = frozenset({
    "cell_id","donor_id","source_id","operator_id","address_id",
    "state","count","library_size","evidence_right",
})
_STATES = frozenset({
    "MEASURED_SCALAR", "STRUCTURALLY_UNMEASURED",
    "MEASURED_COLLISION_UNRESOLVED", "WITHHELD_BY_EVIDENCE_RIGHTS",
})
_FORBIDDEN_TREE_KEYS = frozenset({
    "expected_outcome", "target_truth", "verdict", "controller_nonce",
    "planted_mechanisms", "truth_bundle", "latent_truth", "expected_state",
    "controller_truth", "expected_class", "oracle", "gate_verdict",
    "qualification_pass", "truth_label", "known_truth",
})


def _string(value: object) -> bool:
    return type(value) is str and bool(value) and value == value.strip()


def _sha(value: object) -> bool:
    return (
        type(value) is str and len(value) == 64
        and all(ch in "0123456789abcdef" for ch in value)
    )


def _exclude_truth_tree(value: object) -> None:
    # Unlike a keyword scan of serialized values, reject forbidden *keys*
    # recursively (including nested payloads and cells). Strict schema checks
    # below independently prohibit unknown fields, even innocuous ones.
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str or key.lower() in _FORBIDDEN_TREE_KEYS:
                raise CaseBundleError("truth or noncanonical key entered scientific observable tree")
            _exclude_truth_tree(item)
    elif type(value) is list:
        for item in value:
            _exclude_truth_tree(item)


def validate_casebundle(payload: dict[str, object]) -> dict[str, object]:
    """Validate a *synthetic fixture* observable and snapshot its exact content.

    Caller-controlled SHA strings and fixture labels are consistency claims,
    never real source authentication. Only reader_fit-shaped fixture data can
    pass; full Task2 manifest/population-access attestation is NOT performed.
    """
    if type(payload) is not dict:
        raise CaseBundleError("casebundle must be an exact canonical mapping")
    _exclude_truth_tree(payload)
    if set(payload) != _FIELDS:
        raise CaseBundleError("casebundle schema is not exact")
    if (
        payload["schema"] != _SCHEMA or type(payload["schema"]) is not str
        or payload["authority_scope"] != "FIXTURE_ONLY"
        or type(payload["authority_scope"]) is not str
        or not _string(payload["case_id"])
        or payload["reader_partition"] != "reader_fit"
        or type(payload["reader_partition"]) is not str
    ):
        raise CaseBundleError("only same-contract reader-fit-shaped fixtures accepted")
    for key in ("manifest_sha256","population_access_policy_sha256","address_universe_sha256"):
        if not _sha(payload[key]):
            raise CaseBundleError("fixture digest claim is malformed")
    rows=payload["observations"]
    if type(rows) is not list or not rows:
        raise CaseBundleError("at least one explicit physical observation required")
    seen=set()
    cell_library={}
    cell_hierarchy={}
    counted_mass={}
    for row in rows:
        if type(row) is not dict or set(row) != _ROW_FIELDS:
            raise CaseBundleError("observation row must have exact fields")
        for key in ("cell_id","donor_id","source_id","operator_id","address_id","state","evidence_right"):
            if not _string(row[key]):
                raise CaseBundleError("row contains noncanonical scientific identity")
        if row["state"] not in _STATES:
            raise CaseBundleError("unknown biological-measurement support state")
        hierarchy=(row["donor_id"],row["source_id"],row["operator_id"])
        before=cell_hierarchy.setdefault(row["cell_id"],hierarchy)
        if before!=hierarchy:
            raise CaseBundleError("one scientific cell cannot switch donor, source or operator")
        atom=(row["cell_id"],row["address_id"])
        if atom in seen:
            raise CaseBundleError("duplicate cell/address evidence atom")
        seen.add(atom)
        if row["state"]=="MEASURED_SCALAR":
            if (
                type(row["count"]) is not int or row["count"] < 0
                or type(row["library_size"]) is not int
                or row["library_size"] < 1
                or row["count"] > row["library_size"]
            ):
                raise CaseBundleError("scalar requires observed nonnegative integer and positive library mass")
            # Library is cell/observation realization property, not an arbitrary
            # gene-by-gene number. Enforce consistency when two scalar rows
            # share a cell. Full total library auditing needs external producer.
            prev=cell_library.setdefault(row["cell_id"],row["library_size"])
            if prev!=row["library_size"]:
                raise CaseBundleError("inconsistent measured normalization library within cell")
            counted_mass[row["cell_id"]]=counted_mass.get(row["cell_id"],0)+row["count"]
            if counted_mass[row["cell_id"]]>prev:
                raise CaseBundleError("sum of measured address counts exceeds physical library mass")
        elif row["count"] is not None or row["library_size"] is not None:
            raise CaseBundleError("non-scalar state cannot supply hidden count or library mass")
    try:
        content_sha=canonical_sha256(payload)
    except (CanonicalError,ValueError,TypeError) as exc:
        raise CaseBundleError("cannot compute exact canonical case content identity") from exc
    snap=deepcopy(payload)
    return {
        "schema":"CASEBUNDLE_FIXTURE_VALIDATION_RECEIPT_V1",
        "status":"CASEBUNDLE_FIXTURE_VALIDATED_NO_AUTHORITY",
        "case_id":payload["case_id"],
        "observable_sha256":content_sha,
        "observations":snap["observations"],
        "manifest_sha256":payload["manifest_sha256"],
        "population_access_policy_sha256":payload["population_access_policy_sha256"],
        "same_code_path_authorized":False,
        "externally_authenticated":False,
        "authority_effect":"NONE",
    }


def freeze_fixture_td_output(payload: dict[str, object]) -> dict[str, object]:
    """Freeze a caller-produced *fixture* TD output, never issue authority."""
    if type(payload) is not dict or set(payload)!={"status","outcome"}:
        raise CaseBundleError("fixture TD output has wrong schema")
    if type(payload["status"]) is not str or payload["status"] not in {
        "COMPLETE","FAIL","NOT_ESTIMABLE","NUMERICAL_FAILURE"
    }:
        raise CaseBundleError("unrecognized fixture-only TD status")
    if payload["outcome"] is not None and type(payload["outcome"]) not in (str,int,float):
        raise CaseBundleError("fixture outcome must be canonical scalar")
    try:
        digest=canonical_sha256(payload)
    except (CanonicalError,TypeError,ValueError) as exc:
        raise CaseBundleError("invalid frozen output content") from exc
    return {
        "schema":"FIXTURE_TD_OUTPUT_FREEZE_V1",
        "frozen_output_sha256":digest,
        "frozen_status":payload["status"],
        "authority_effect":"NONE",
    }


def validate_truth_separation(
    case_payload: dict[str, object],
    truth_payload: dict[str, object],
    *,
    td_output_frozen: object,
) -> dict[str, object]:
    """Fixture-only external truth separation, callable only after output freeze.

    This does not enforce a genuine external adjudicator, signed commitment or
    inaccessible secret. Truth is never forwarded into the science trace.
    """
    checked=validate_casebundle(case_payload)
    if (
        type(td_output_frozen) is not dict
        or set(td_output_frozen)!={"schema","frozen_output_sha256","frozen_status","authority_effect"}
        or td_output_frozen["schema"]!="FIXTURE_TD_OUTPUT_FREEZE_V1"
        or not _sha(td_output_frozen["frozen_output_sha256"])
        or td_output_frozen["authority_effect"]!="NONE"
    ):
        raise CaseBundleError("scientific output was not frozen before external truth read")
    if (
        type(truth_payload) is not dict
        or set(truth_payload)!={"schema","case_id","authority_scope","expected_outcome","latent_truth"}
        or truth_payload["schema"]!=_TRUTH_SCHEMA
        or truth_payload["authority_scope"]!="CONTROLLER_FIXTURE_ONLY"
        or type(truth_payload["case_id"]) is not str
        or truth_payload["case_id"]!=checked["case_id"]
        or type(truth_payload["expected_outcome"]) is not str
        or type(truth_payload["latent_truth"]) is not dict
    ):
        raise CaseBundleError("truth bundle must be separate, exact and controller fixture only")
    # Do not export any truth values. Digest confirms bytes only, not issuer.
    try:
        digest=canonical_sha256(truth_payload)
    except (CanonicalError,TypeError,ValueError) as exc:
        raise CaseBundleError("uncanonical external truth bundle") from exc
    return {
        "schema":"TASK5_FIXTURE_TRUTH_SEPARATION_RECEIPT_V1",
        "status":"EXTERNAL_FIXTURE_TRUTH_SEPARATED_NO_AUTHORITY",
        "casebundle_sha256":checked["observable_sha256"],
        "fixture_truth_sha256":digest,
        "frozen_td_output_sha256":td_output_frozen["frozen_output_sha256"],
        "adjudicator_authenticated":False,
        "authority_effect":"NONE",
    }
