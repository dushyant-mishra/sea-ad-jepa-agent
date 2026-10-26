"""Fixture-only bridge: prospective Unified Task5 -> existing JEPA post-TD harness.

Reuses the post-TD target-portfolio / teacher-evidence / architecture code from
PR #351, not a replacement downstream pipeline. No human Target Qualification
Bundle exists here. Caller-supplied fixture qualifications are *never* evidence
of biological qualification; this bridge cannot select a production target or
enable training. Task7/8 need independent exact-bundle verification later.
"""
from __future__ import annotations

from scripts.v5.td_unified.casebundle_v1 import validate_casebundle
from scripts.v5.td_unified.mode_equivalence_v1 import (
    FixtureStage, trace_scientific_path, certify_mode_path_equivalence,
)
from scripts.v5 import jepa_post_td_harness_contract_v1 as H


class FixtureBridgeError(ValueError):
    pass


_CANDIDATE_ROSTER = frozenset({"C1","C2","C3","C4","C5","C6"})
_FIXTURE_STATUSES = frozenset({"PASS","FAIL","NOT_ESTIMABLE"})
FIXTURE_LABEL_RECEIPT_CLASS = "TASK5_PLANTED_FIXTURE_LABEL"


def _closed_fixture_statuses(qualifications) -> dict[str, str]:
    # Exact builtins only; keys must name roster candidates, not claims.
    if type(qualifications) is not dict or not qualifications:
        raise FixtureBridgeError("fixture portfolio inputs must be explicit closed statuses")
    out = {}
    for k, v in dict.items(qualifications):
        if (type(k) is not str or k not in _CANDIDATE_ROSTER
                or type(v) is not str or v not in _FIXTURE_STATUSES):
            raise FixtureBridgeError("fixture portfolio inputs must be explicit closed statuses")
        out[k] = v
    return out


def _fixture_label_receipt(status: str, casebundle_sha256: str) -> dict[str, object]:
    # The harness reads only "status"; the rest keeps the fixture provenance
    # inside the TargetPortfolio itself, so an extracted portfolio still says
    # where its PASS came from.
    return {
        "status": status,
        "receipt_class": FIXTURE_LABEL_RECEIPT_CLASS,
        "biological_qualification": False,
        "casebundle_sha256": casebundle_sha256,
    }


def stage_fixture_downstream(
    *, case_payload: dict[str, object], stages: tuple[FixtureStage, ...],
    fixture_candidate: str | None = None,
    fixture_qualifications: dict[str, str] | None = None,
    ema_half_life_presentations: int = 256,
) -> dict[str, object]:
    """Exercise the *existing* legacy control plane using Task5 fixtures.

    `TARGET_NONE` is a real first-class non-authorizing output. For a
    non-NONE selection, PASS labels are explicit planted fixture inputs, not
    verified biological qualifications; they only test existing portfolio
    policy. Architecture is a plan, not an optimizer execution or EMA update.
    """
    case=validate_casebundle(case_payload)
    if case["authority_effect"]!="NONE" or case["externally_authenticated"] is not False:
        raise FixtureBridgeError("non-fixture case bundle refused")
    known=trace_scientific_path(mode="KNOWN_TRUTH",case_payload=case_payload,stages=stages)
    human=trace_scientific_path(mode="HUMAN_SEALED",case_payload=case_payload,stages=stages)
    parity=certify_mode_path_equivalence(known,human)
    if parity["authority_effect"]!="NONE" or parity["same_code_path_authorized"] is not False:
        raise FixtureBridgeError("fixture path cannot issue scientific authority")
    # Both traces run the same in-process stages on the same payload, so the
    # Task5 parity receipt only shows the stage roster matched. Do not forward
    # its equivalence claim.
    mode_check={
        "schema":"UNIFIED_TASK5_BRIDGE_STAGE_ROSTER_CHECK_V1",
        "status":"SAME_PROCESS_SELF_COMPARISON__NOT_MODE_EQUIVALENCE_EVIDENCE",
        "stage_roster_validated":True,
        "scientific_output_equivalence":None,
        "independent_human_sealed_execution":False,
        "observable_payload_digest":parity["observable_payload_digest"],
        "known_truth_execution_trace_digest":parity["known_truth_execution_trace_digest"],
        "human_mode_execution_trace_digest":parity["human_mode_execution_trace_digest"],
        "same_code_path_authorized":False,
        "authority_effect":"NONE",
    }
    if type(ema_half_life_presentations) is not int or ema_half_life_presentations <= 0:
        raise FixtureBridgeError("EMA half-life must be a positive exact int of presentations")
    none_evidence=None
    if fixture_candidate is None:
        empty = type(fixture_qualifications) is dict and dict.__len__(fixture_qualifications) == 0
        if fixture_qualifications is not None and not empty:
            # TARGET_NONE may carry the closed evidence behind it, never a PASS:
            # NONE despite a qualifying candidate is a false abstention.
            none_evidence=_closed_fixture_statuses(fixture_qualifications)
            if "PASS" in none_evidence.values():
                raise FixtureBridgeError("TARGET_NONE cannot smuggle fixture PASS claims")
            none_evidence={k:none_evidence[k] for k in sorted(none_evidence)}
        portfolio=None
        architecture=None
        target="NONE"
    else:
        if type(fixture_candidate) is not str or fixture_candidate not in {"C1","C2","C3","C4","C6"}:
            raise FixtureBridgeError("fixture portfolio inputs must be explicit closed statuses")
        statuses=_closed_fixture_statuses(fixture_qualifications)
        labelled={
            k:_fixture_label_receipt(v, case["observable_sha256"])
            for k,v in statuses.items()
        }
        # Existing PR351 enforces C4 requires independently PASS C6 among the
        # supplied fixture labels, while the bridge never authenticates them.
        try:
            portfolio=H.build_target_portfolio(
                selected_candidate=fixture_candidate,
                qualifications=labelled,
            )
            architecture=H.build_architecture_plan(
                portfolio=portfolio,
                ema_half_life_presentations=ema_half_life_presentations,
            )
        except H.PostTDContractError as exc:
            raise FixtureBridgeError("existing post-TD portfolio/architecture policy refused fixture") from exc
        target=fixture_candidate
        if (any(x is not False for x in portfolio["authority"].values())
                or any(x is not False for x in architecture["authority"].values())):
            raise FixtureBridgeError("post-TD control plane unexpectedly promoted fixture")
    return {
        "schema":"UNIFIED_TASK5_POST_TD_FIXTURE_BRIDGE_V1",
        "status":"FIXTURE_ONLY__NOT_TARGET_QUALIFIED",
        "target_candidate_fixture":target,
        "target_none_fixture_evidence":none_evidence,
        "casebundle_sha256":case["observable_sha256"],
        "mode_path_receipt":mode_check,
        "post_td_portfolio":portfolio,
        "post_td_architecture_plan":architecture,
        "authenticated_target_bundle_consumed":False,
        "same_code_path_authorized":False,
        "human_execution_authorized":False,
        "real_training_authorized":False,
        "stage4_authorized":False,
        "authority_effect":"NONE",
    }
