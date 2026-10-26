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
    if fixture_candidate is None:
        if fixture_qualifications not in (None, {}):
            raise FixtureBridgeError("TARGET_NONE cannot smuggle fixture PASS claims")
        portfolio=None
        architecture=None
        target="NONE"
    else:
        if (
            type(fixture_candidate) is not str
            or fixture_candidate not in {"C1","C2","C3","C4","C6"}
            or type(fixture_qualifications) is not dict
            or not fixture_qualifications
            or any(type(k) is not str or type(v) is not str
                   or v not in {"PASS","FAIL","NOT_ESTIMABLE"}
                   for k,v in fixture_qualifications.items())
        ):
            raise FixtureBridgeError("fixture portfolio inputs must be explicit closed statuses")
        # Existing PR351 enforces C4 requires independently PASS C6 among the
        # supplied fixture labels, while the bridge never authenticates them.
        try:
            portfolio=H.build_target_portfolio(
                selected_candidate=fixture_candidate,
                qualifications=fixture_qualifications,
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
        "casebundle_sha256":case["observable_sha256"],
        "mode_path_receipt":parity,
        "post_td_portfolio":portfolio,
        "post_td_architecture_plan":architecture,
        "authenticated_target_bundle_consumed":False,
        "same_code_path_authorized":False,
        "human_execution_authorized":False,
        "real_training_authorized":False,
        "stage4_authorized":False,
        "authority_effect":"NONE",
    }
