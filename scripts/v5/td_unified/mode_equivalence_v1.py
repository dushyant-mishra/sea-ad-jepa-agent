"""A7 Task5 *fixture-only* executable scientific-path comparison.

A strict, deliberately non-authorizing rehearsal of the science-side sequence.
It compares measured path execution and actual handler outputs; it does NOT
establish independently signed code identities, Task4 custody, real-data
reference readiness, or genuine cross-process same-code-path certification.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import marshal
import types
from typing import Callable

from scripts.v5.td_unified.canonical_v1 import canonical_sha256, CanonicalError
from scripts.v5.td_unified.casebundle_v1 import validate_casebundle, CaseBundleError

SCIENTIFIC_ROLES = (
    "SCHEMA_VALIDATOR",
    "POPULATION_ACCESS",
    "PRODUCER",
    "ARTIFACT_SERIALIZER",
    "RECEIPT_VALIDATOR",
    "EXECUTOR",
    "METRIC",
    "SUPPORT",
    "REFERENCE",
    "STATUS",
)
_ALLOWED_MODES=frozenset({"KNOWN_TRUTH","HUMAN_SEALED"})
_FORBIDDEN_SCIENCE_KEYS=frozenset({
    "truth", "latent_truth","expected_outcome","expected_verdict",
    "planted_mechanisms","controller_nonce","oracle","gate_verdict",
})


class PathEquivalenceError(ValueError):
    """Missing, moved or untrustworthy fixture scientific execution path."""


@dataclass(frozen=True)
class FixtureStage:
    role: str
    handler: Callable[[object], object]


def _guard_tree(value: object) -> None:
    if type(value) is dict:
        for k,v in value.items():
            if type(k) is not str or k.lower() in _FORBIDDEN_SCIENCE_KEYS:
                raise PathEquivalenceError("truth/controller value entered scientific execution")
            _guard_tree(v)
    elif type(value) in (list,tuple):
        for item in value:
            _guard_tree(item)


def _code_identity(handler: object) -> str:
    """Diagnostic same-run Python handler fingerprint, NOT external trust."""
    if type(handler) is not types.FunctionType:
        raise PathEquivalenceError("only exact fixture Python functions are accepted")
    closure=[]
    if handler.__closure__:
        for cell in handler.__closure__:
            try:
                item=cell.cell_contents
            except ValueError as exc:
                raise PathEquivalenceError("unbound closure rejected") from exc
            if type(item) not in (str,int,float,bool,type(None)):
                raise PathEquivalenceError("fixture closure cannot depend on complex mutable values")
            closure.append(item)
    try:
        return canonical_sha256({
            "schema":"TASK5_FIXTURE_PYTHON_HANDLER_IDENTITY_V1",
            "module":handler.__module__,
            "qualname":handler.__qualname__,
            "marshal_code_sha256":hashlib.sha256(marshal.dumps(handler.__code__)).hexdigest(),
            "closure":closure,
        })
    except (CanonicalError,ValueError,TypeError) as exc:
        raise PathEquivalenceError("fixture handler source identity malformed") from exc


def _digest(value: object) -> str:
    try:
        return canonical_sha256(value)
    except (CanonicalError,ValueError,TypeError) as exc:
        raise PathEquivalenceError("noncanonical fixture scientific value") from exc


def trace_scientific_path(
    *, mode: str, case_payload: dict[str,object],
    stages: tuple[FixtureStage,...],
) -> dict[str,object]:
    """Execute the ordered common science-side fixture path.

    Neither the function signature of a handler nor its payload contains
    the outer known-truth versus human-sealed mode. Caller-level mode
    independence is not general proof for arbitrary untrusted code: the
    returned receipt is *never* authoritative.
    """
    if type(mode) is not str or mode not in _ALLOWED_MODES:
        raise PathEquivalenceError("unknown wrapper mode")
    if type(stages) is not tuple or len(stages)!=len(SCIENTIFIC_ROLES):
        raise PathEquivalenceError("scientific stage roster is incomplete")
    if any(type(step) is not FixtureStage or type(step.role) is not str
           or step.role!=expected for step,expected in zip(stages,SCIENTIFIC_ROLES)):
        raise PathEquivalenceError("scientific stage order or identities differ from contract")
    try:
        validated=validate_casebundle(case_payload)
    except CaseBundleError as exc:
        raise PathEquivalenceError("fixture failed CaseBundle preflight") from exc
    observable_sha=validated["observable_sha256"]
    current={
        "schema":"TASK5_SCIENTIFIC_OBSERVABLE_INPUT_V1",
        "case_id":validated["case_id"],
        "observable_sha256":observable_sha,
        "manifest_sha256":validated["manifest_sha256"],
        "population_access_policy_sha256":validated["population_access_policy_sha256"],
    }
    trace=[]
    for stage in stages:
        _guard_tree(current)
        name=_code_identity(stage.handler)
        prev=_digest(current)
        try:
            output=stage.handler(current)
        except Exception as exc:
            raise PathEquivalenceError("fixture science-side stage execution failed") from exc
        _guard_tree(output)
        digest=_digest(output)
        trace.append({
            "role":stage.role,
            "code_identity":name,
            "input_sha256":prev,
            "output_sha256":digest,
        })
        current=output
    trace_sha=_digest(trace)
    return {
        "schema":"SCIENTIFIC_EXECUTION_TRACE_FIXTURE_V1",
        "mode":mode,
        "observable_payload_sha256":observable_sha,
        "scientific_trace":trace,
        "scientific_trace_sha256":trace_sha,
        "scientific_output_sha256":_digest(current),
        "issuer_authenticated":False,
        "authority_effect":"NONE",
    }


def _verify_trace(report: object, mode: str) -> None:
    if type(report) is not dict or set(report)!={
        "schema","mode","observable_payload_sha256","scientific_trace",
        "scientific_trace_sha256","scientific_output_sha256",
        "issuer_authenticated","authority_effect",
    }:
        raise PathEquivalenceError("mode trace has wrong receipt structure")
    if (report["schema"]!="SCIENTIFIC_EXECUTION_TRACE_FIXTURE_V1"
        or report["mode"]!=mode or type(report["mode"]) is not str
        or report["issuer_authenticated"] is not False
        or report["authority_effect"]!="NONE"):
        raise PathEquivalenceError("fixture trace attempts external authority or mode substitution")
    trace=report["scientific_trace"]
    if type(trace) is not list or len(trace)!=len(SCIENTIFIC_ROLES):
        raise PathEquivalenceError("stage trace incomplete")
    for step, role in zip(trace,SCIENTIFIC_ROLES):
        if type(step) is not dict or set(step)!={
            "role","code_identity","input_sha256","output_sha256"
        } or step["role"]!=role:
            raise PathEquivalenceError("unexpected or missing science stage")
        for key in ("code_identity","input_sha256","output_sha256"):
            x=step[key]
            if type(x) is not str or len(x)!=64 or any(c not in "0123456789abcdef" for c in x):
                raise PathEquivalenceError("stage lacks exact content identity")
    if report["scientific_trace_sha256"]!=_digest(trace):
        raise PathEquivalenceError("science trace digest does not recompute")
    for key in ("observable_payload_sha256","scientific_output_sha256"):
        x=report[key]
        if type(x) is not str or len(x)!=64 or any(c not in "0123456789abcdef" for c in x):
            raise PathEquivalenceError("observable or output identity malformed")


def certify_mode_path_equivalence(known_truth: dict, human_sealed: dict) -> dict[str,object]:
    """Compare two executed *fixture* traces and refuse scientific divergence.

    Proof is limited to these fixture invocations: no same-code-path authority
    because external producer identity, mandatory case population-access
    policy, Task4 authenticated lineage and truth controller are absent.
    """
    _verify_trace(known_truth,"KNOWN_TRUTH")
    _verify_trace(human_sealed,"HUMAN_SEALED")
    for key in ("observable_payload_sha256","scientific_trace_sha256","scientific_output_sha256"):
        if known_truth[key]!=human_sealed[key]:
            raise PathEquivalenceError("known-truth and human-mode science-side path diverged")
    if known_truth["scientific_trace"]!=human_sealed["scientific_trace"]:
        raise PathEquivalenceError("known-truth and human-mode stage roster or semantics diverged")
    return {
        "schema":"MODE_PATH_EQUIVALENCE_RECEIPT_FIXTURE_V1",
        "status":"MODE_PATH_EQUIVALENCE_FIXTURE_ONLY_NO_AUTHORITY",
        "observable_payload_digest":known_truth["observable_payload_sha256"],
        "known_truth_execution_trace_digest":known_truth["scientific_trace_sha256"],
        "human_mode_execution_trace_digest":human_sealed["scientific_trace_sha256"],
        "scientific_output_equivalence":True,
        "producer_identity_set":[known_truth["scientific_trace"][2]["code_identity"]],
        "executor_identity_set":[known_truth["scientific_trace"][5]["code_identity"]],
        "validator_identity_set":[
            known_truth["scientific_trace"][i]["code_identity"] for i in (0,1,4)
        ],
        "branch_condition_audit_digest":None,
        "independent_issuer_authenticated":False,
        "same_code_path_authorized":False,
        "known_truth_qualified":False,
        "real_reference_ready":False,
        "training_authorized":False,
        "authority_effect":"NONE",
    }
